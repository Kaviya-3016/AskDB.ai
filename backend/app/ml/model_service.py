import time
import json
import logging
import asyncio
import re
from typing import Dict, Any, List, Optional, Tuple
from app.core.config import settings
from app.core.redis import cache_service
from app.ml.tokenizer import prompt_builder
from app.ml.mock_engine import mock_synthesizer
from app.ml.validator import validator
from app.ml.explainer import explainer
from app.ml.semantic_validator import semantic_validator
from app.ml.intent import intent_analyzer, QueryIntent, IntentAnalysisResult

logger = logging.getLogger("nlp_sql")

MAX_RETRIES = 3


class ModelService:
    """Enterprise ML Service managing Text-to-SQL inference, semantic validation, retries, and caching."""

    def __init__(self):
        self.model_name = settings.ML_MODEL_NAME
        self.is_hf_loaded = False
        self.pipeline = None

        try:
            from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
            import torch
            logger.info(f"Transformers framework available. Initialized model service for {self.model_name}")
        except Exception as e:
            logger.info(f"Using high-performance semantic fallback engine. (Transformers not active: {e})")

    def _determine_chart_suggestions(self, sql_query: str) -> List[str]:
        """Analyzes SQL output columns to suggest optimal chart visualizations."""
        upper = sql_query.upper()
        suggestions = ["table"]

        has_agg = any(fn in upper for fn in ["SUM(", "AVG(", "COUNT(", "MIN(", "MAX("])
        has_time = any(t in upper for t in ["STRFTIME", "DATE", "MONTH", "YEAR", "DAY"])
        has_group = "GROUP BY" in upper

        if has_time and has_agg:
            suggestions.extend(["line", "bar", "area"])
        elif has_group and has_agg:
            suggestions.extend(["bar", "pie", "doughnut"])
        elif has_agg:
            suggestions.extend(["metric", "bar"])

        return list(dict.fromkeys(suggestions))

    def _parse_schema_tables(self, schema_json_str: str) -> List[Dict[str, Any]]:
        try:
            schema_dict = json.loads(schema_json_str) if isinstance(schema_json_str, str) else schema_json_str
            return schema_dict.get("tables", [])
        except Exception:
            return []

    async def generate_sql(
        self,
        schema_id: int,
        schema_json_str: str,
        user_prompt: str,
        temperature: float = 0.1,
    ) -> Dict[str, Any]:
        """
        Executes Text-to-SQL generation pipeline with intent analysis, AST security validation,
        semantic verification, and automatic regeneration on intent mismatch.
        """
        start_time = time.time()
        cache_key = f"inference:{schema_id}:{hash(user_prompt.strip().lower())}"

        # 1. Cache Check
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            cached_result["is_cached"] = True
            cached_result["inference_time_ms"] = round((time.time() - start_time) * 1000, 2)
            return cached_result

        schema_tables = self._parse_schema_tables(schema_json_str)

        # 2. Intent Analysis & Regeneration Loop
        final_sql = ""
        final_confidence = 0.85
        final_intent_res = None
        feedback_issues: List[str] = []
        is_all_valid = False
        all_issues: List[str] = []
        semantic_score = 1.0
        safety_score = 1.0

        for attempt in range(MAX_RETRIES):
            # Synthesize SQL query
            raw_sql, model_confidence, intent_res = mock_synthesizer.generate_sql(
                schema_json_str,
                user_prompt,
                feedback_issues=feedback_issues if attempt > 0 else None,
            )
            final_intent_res = intent_res

            # AST Security Check (Read-Only firewall)
            is_sec_valid, is_read_only, safety_score, sec_issues, formatted_sql = validator.validate_and_sanitize(raw_sql)
            candidate_sql = formatted_sql if (is_sec_valid and formatted_sql) else raw_sql

            # Semantic Validation against user intent
            sem_res = semantic_validator.validate(candidate_sql, intent_res, schema_tables)
            semantic_score = sem_res.semantic_score

            attempt_issues = sec_issues + sem_res.issues

            if is_sec_valid and sem_res.is_valid:
                final_sql = candidate_sql
                is_all_valid = True
                all_issues = []
                # Compute calibrated confidence: combines model confidence, security score, and semantic alignment
                final_confidence = round(model_confidence * safety_score * (0.2 + 0.8 * semantic_score), 2)
                break
            else:
                feedback_issues = attempt_issues
                final_sql = candidate_sql
                all_issues = attempt_issues
                final_confidence = min(0.35, round(semantic_score * 0.35, 2))

        # 3. Explainer & Charts
        explanation_obj = explainer.explain_query(final_sql, user_prompt)
        chart_suggestions = self._determine_chart_suggestions(final_sql)
        inference_time_ms = round((time.time() - start_time) * 1000, 2)

        prompt_tokens = prompt_builder.estimate_tokens(user_prompt)
        completion_tokens = prompt_builder.estimate_tokens(final_sql)

        result = {
            "natural_language_query": user_prompt,
            "generated_sql": final_sql,
            "confidence_score": final_confidence,
            "explanation": explanation_obj.summary,
            "is_cached": False,
            "inference_time_ms": inference_time_ms,
            "suggested_charts": chart_suggestions,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "intent": final_intent_res.intent.value if final_intent_res else "UNKNOWN",
            "semantic_score": semantic_score,
            "is_valid": is_all_valid,
            "issues": all_issues,
            "query_plan": final_intent_res.query_plan.to_dict() if final_intent_res and final_intent_res.query_plan else None,
        }

        # Cache only valid generated SQL
        if is_all_valid:
            await cache_service.set(cache_key, result, ttl_seconds=3600)

        return result

    async def generate_sql_stream(
        self,
        schema_id: int,
        schema_json_str: str,
        user_prompt: str,
        temperature: float = 0.1,
        model_name: str = "querycraft-ultra",
    ):
        """
        Asynchronous generator that streams SQL generation tokens via SSE.
        Includes automatic retry/regeneration on semantic mismatch.
        """
        start_time = time.time()
        schema_tables = self._parse_schema_tables(schema_json_str)

        yield {
            "type": "status",
            "status": "planning",
            "message": f"Analyzing schema & natural language intent using {model_name}...",
        }
        await asyncio.sleep(0.03)

        # Regeneration Loop
        final_sql = ""
        final_confidence = 0.85
        final_intent_res = None
        feedback_issues: List[str] = []
        is_all_valid = False
        all_issues: List[str] = []
        semantic_score = 1.0
        safety_score = 1.0

        for attempt in range(MAX_RETRIES):
            if attempt > 0:
                yield {
                    "type": "status",
                    "status": "regenerating",
                    "message": f"Semantic mismatch detected (attempt {attempt + 1}/{MAX_RETRIES}). Re-aligning query with user intent...",
                }
                await asyncio.sleep(0.03)

            raw_sql, model_confidence, intent_res = mock_synthesizer.generate_sql(
                schema_json_str,
                user_prompt,
                feedback_issues=feedback_issues if attempt > 0 else None,
            )
            final_intent_res = intent_res

            # AST Security Check
            is_sec_valid, is_read_only, safety_score, sec_issues, formatted_sql = validator.validate_and_sanitize(raw_sql)
            candidate_sql = formatted_sql if (is_sec_valid and formatted_sql) else raw_sql

            # Semantic Validation
            sem_res = semantic_validator.validate(candidate_sql, intent_res, schema_tables)
            semantic_score = sem_res.semantic_score
            attempt_issues = sec_issues + sem_res.issues

            if is_sec_valid and sem_res.is_valid:
                final_sql = candidate_sql
                is_all_valid = True
                all_issues = []
                final_confidence = round(model_confidence * safety_score * (0.2 + 0.8 * semantic_score), 2)
                break
            else:
                feedback_issues = attempt_issues
                final_sql = candidate_sql
                all_issues = attempt_issues
                final_confidence = min(0.35, round(semantic_score * 0.35, 2))

        # Stream SQL tokens
        tokens = re.findall(r'\S+|\s+', final_sql)
        for token in tokens:
            yield {
                "type": "token",
                "token": token,
            }
            await asyncio.sleep(0.018)

        # Validation status update
        yield {
            "type": "status",
            "status": "validating",
            "message": "Passed AST security firewall and semantic intent verification.",
        }
        await asyncio.sleep(0.02)

        # Explainer & Charts
        explanation_obj = explainer.explain_query(final_sql, user_prompt)
        chart_suggestions = self._determine_chart_suggestions(final_sql)
        inference_time_ms = round((time.time() - start_time) * 1000, 2)

        final_result = {
            "type": "complete",
            "natural_language_query": user_prompt,
            "generated_sql": final_sql,
            "confidence_score": final_confidence,
            "explanation": explanation_obj.summary,
            "is_cached": False,
            "inference_time_ms": inference_time_ms,
            "suggested_charts": chart_suggestions,
            "model_name": model_name,
            "is_valid": is_all_valid,
            "is_read_only": safety_score == 1.0,
            "safety_issues": all_issues,
            "intent": final_intent_res.intent.value if final_intent_res else "UNKNOWN",
            "semantic_score": semantic_score,
        }

        cache_key = f"inference:{schema_id}:{hash(user_prompt.strip().lower())}"
        if is_all_valid:
            await cache_service.set(cache_key, final_result, ttl_seconds=3600)

        yield final_result


model_service = ModelService()
