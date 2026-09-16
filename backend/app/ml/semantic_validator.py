import re
from typing import Dict, Any, List, Tuple, Optional
import sqlparse
from sqlparse.sql import IdentifierList, Identifier, Where, Comparison
from sqlparse.tokens import Keyword, DML
from app.ml.intent import QueryIntent, IntentAnalysisResult


class SemanticValidationResult:
    def __init__(
        self,
        is_valid: bool,
        semantic_score: float,
        issues: List[str],
        recommendations: List[str],
        ast_summary: Dict[str, Any],
    ):
        self.is_valid = is_valid
        self.semantic_score = semantic_score
        self.issues = issues
        self.recommendations = recommendations
        self.ast_summary = ast_summary

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "semantic_score": self.semantic_score,
            "issues": self.issues,
            "recommendations": self.recommendations,
            "ast_summary": self.ast_summary,
        }


class SemanticValidator:
    """
    Validates that a generated SQL query aligns with the user's natural language intent,
    schema constraints, requested filters, aggregations, and grouping expectations.
    """

    @staticmethod
    def extract_ast_details(sql_query: str) -> Dict[str, Any]:
        clean = sql_query.strip()
        upper = clean.upper()

        # Tables
        from_matches = re.findall(r"\bFROM\s+([a-zA-Z0-9_]+)", clean, re.IGNORECASE)
        join_matches = re.findall(r"\bJOIN\s+([a-zA-Z0-9_]+)", clean, re.IGNORECASE)
        tables = list(dict.fromkeys(from_matches + join_matches))

        # Has clauses
        has_where = "WHERE" in upper
        has_group_by = "GROUP BY" in upper
        has_order_by = "ORDER BY" in upper
        has_limit = "LIMIT" in upper

        # Aggregations
        agg_matches = re.findall(r"\b(COUNT|AVG|SUM|MIN|MAX)\s*\(", upper)
        aggregations = [a.upper() for a in agg_matches]

        # Group by columns
        group_by_cols = []
        if has_group_by:
            gb_match = re.search(r"\bGROUP BY\s+(.*?)(?=\bORDER BY\b|\bLIMIT\b|;|$)", clean, re.IGNORECASE | re.DOTALL)
            if gb_match:
                cols_str = gb_match.group(1).strip()
                group_by_cols = [c.strip() for c in cols_str.split(",") if c.strip()]

        # Order by columns
        order_by_cols = []
        if has_order_by:
            ob_match = re.search(r"\bORDER BY\s+(.*?)(?=\bLIMIT\b|;|$)", clean, re.IGNORECASE | re.DOTALL)
            if ob_match:
                cols_str = ob_match.group(1).strip()
                order_by_cols = [c.strip() for c in cols_str.split(",") if c.strip()]

        # Limit value
        limit_val = None
        if has_limit:
            lim_m = re.search(r"\bLIMIT\s+(\d+)", clean, re.IGNORECASE)
            if lim_m:
                limit_val = int(lim_m.group(1))

        # Where clause content
        where_clause_str = ""
        where_columns = []
        if has_where:
            wm = re.search(r"\bWHERE\s+(.*?)(?=\bGROUP BY\b|\bORDER BY\b|\bLIMIT\b|;|$)", clean, re.IGNORECASE | re.DOTALL)
            if wm:
                where_clause_str = wm.group(1).strip()
                # Find column candidates before operators =, >, <, LIKE, BETWEEN, IN
                col_candidates = re.findall(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\s*(?:=|!=|<>|>|<|>=|<=|\bLIKE\b|\bBETWEEN\b|\bIN\b)", where_clause_str, re.IGNORECASE)
                where_columns = [c.lower() for c in col_candidates if c.upper() not in ["AND", "OR", "NOT"]]

        # Select columns/expressions
        select_match = re.search(r"\bSELECT\s+(.*?)\s+\bFROM\b", clean, re.IGNORECASE | re.DOTALL)
        select_clause = select_match.group(1).strip() if select_match else ""

        return {
            "tables": tables,
            "has_where": has_where,
            "where_clause": where_clause_str,
            "where_columns": where_columns,
            "has_group_by": has_group_by,
            "group_by_columns": group_by_cols,
            "has_order_by": has_order_by,
            "order_by_columns": order_by_cols,
            "has_limit": has_limit,
            "limit_value": limit_val,
            "aggregations": aggregations,
            "select_clause": select_clause,
        }

    def validate(
        self,
        sql_query: str,
        intent_res: IntentAnalysisResult,
        schema_tables: List[Dict[str, Any]],
    ) -> SemanticValidationResult:
        """
        Performs semantic validation of SQL against the user's intent and schema.
        Returns SemanticValidationResult with is_valid, semantic_score, and issues.
        """
        issues: List[str] = []
        recommendations: List[str] = []
        score = 1.0

        if not sql_query or not sql_query.strip():
            return SemanticValidationResult(
                is_valid=False,
                semantic_score=0.0,
                issues=["SQL query is empty."],
                recommendations=["Generate a valid SQL query."],
                ast_summary={},
            )

        ast = self.extract_ast_details(sql_query)

        # 1. Schema Validation (Tables & Columns exist)
        valid_table_names = [t.get("name", "").lower() for t in schema_tables]
        valid_cols_by_table = {}
        for t in schema_tables:
            t_name = t.get("name", "").lower()
            valid_cols_by_table[t_name] = [c.get("name", "").lower() for c in t.get("columns", [])]

        for tbl in ast["tables"]:
            if tbl.lower() not in valid_table_names and valid_table_names:
                issues.append(f"Table '{tbl}' does not exist in schema (available: {', '.join(valid_table_names)}).")
                score -= 0.4

        # 2. Intent Alignment Checks

        # Intent A: DIRECT_LOOKUP
        if intent_res.intent == QueryIntent.DIRECT_LOOKUP:
            # Rule: Must not have GROUP BY
            if ast["has_group_by"]:
                issues.append("Unexpected GROUP BY clause in direct lookup query. Direct lookup questions require a direct WHERE filter without grouping.")
                recommendations.append("Remove the GROUP BY clause.")
                score -= 0.45

            # Rule: Must not have dataset aggregations (COUNT, SUM, AVG) unless requested
            if ast["aggregations"] and not any(a in intent_res.aggregations for a in ["AVG", "SUM", "COUNT"]):
                issues.append(f"Unexpected aggregations {ast['aggregations']} in direct lookup query. Direct lookup requires retrieving raw records.")
                recommendations.append("Remove aggregate functions (COUNT, SUM, AVG).")
                score -= 0.45

            # Rule: Must have required date or equality filter
            if intent_res.date_filters:
                expected_date_col = intent_res.date_filters[0]["col"].lower()
                if not ast["has_where"] or expected_date_col not in ast["where_columns"]:
                    issues.append(f"Missing required date filter on '{expected_date_col}'. The user specified an exact date.")
                    recommendations.append(f"Add WHERE {expected_date_col} = '{intent_res.date_filters[0].get('val')}'.")
                    score -= 0.40

            # Rule: Arbitrary LIMIT > 1 is discouraged on direct lookup
            if ast["has_limit"] and ast["limit_value"] and ast["limit_value"] > 10:
                issues.append(f"Unnecessary LIMIT {ast['limit_value']} on single-record lookup query.")
                recommendations.append("Remove arbitrary LIMIT.")
                score -= 0.10

        # Intent B: AGGREGATION
        elif intent_res.intent == QueryIntent.AGGREGATION:
            # Rule: Should have aggregate function
            if not ast["aggregations"]:
                issues.append("Expected an aggregate function (e.g. AVG, COUNT, SUM, MAX, MIN) in the SELECT clause.")
                recommendations.append("Add the appropriate aggregate function answering the question.")
                score -= 0.40

            # Rule: Should NOT have GROUP BY unless grouping was explicitly requested
            if ast["has_group_by"] and not intent_res.group_by_columns:
                issues.append("Unexpected GROUP BY in overall dataset aggregation query.")
                recommendations.append("Remove GROUP BY to compute the metric across the entire dataset.")
                score -= 0.35

            # Check equality filters (e.g. "rainy days" -> weather = 'rain')
            if intent_res.equality_filters:
                expected_col = intent_res.equality_filters[0]["col"].lower()
                if not ast["has_where"] or expected_col not in ast["where_columns"]:
                    issues.append(f"Missing expected filter condition on '{expected_col}' (e.g. {expected_col} = '{intent_res.equality_filters[0]['val']}').")
                    recommendations.append(f"Add WHERE {expected_col} = '{intent_res.equality_filters[0]['val']}'.")
                    score -= 0.30

        # Intent C: GROUPING
        elif intent_res.intent == QueryIntent.GROUPING:
            if not ast["has_group_by"]:
                issues.append("Missing GROUP BY clause. The question explicitly asks for a breakdown / grouping by category or period.")
                recommendations.append("Add GROUP BY with the requested dimension column.")
                score -= 0.50

        # Intent D: TOP_N
        elif intent_res.intent == QueryIntent.TOP_N:
            if not ast["has_order_by"]:
                issues.append("Missing ORDER BY clause for ranked / Top-N question.")
                recommendations.append("Add ORDER BY to sort records by the target ranking metric.")
                score -= 0.35

            if not ast["has_limit"] and intent_res.limit_val:
                issues.append(f"Missing LIMIT {intent_res.limit_val} clause for Top-N query.")
                recommendations.append(f"Add LIMIT {intent_res.limit_val}.")
                score -= 0.25

        # Intent D2: TOP_N_WITH_FILTER
        elif intent_res.intent == QueryIntent.TOP_N_WITH_FILTER:
            if not ast["has_where"]:
                issues.append("Constraint completeness failed: Missing WHERE clause filter conditions.")
                recommendations.append("Add WHERE clause with required filters.")
                score -= 0.45

            if not ast["has_order_by"]:
                issues.append("Missing ORDER BY clause for Top-N query.")
                recommendations.append("Add ORDER BY to sort records by the target ranking metric.")
                score -= 0.35

            if not ast["has_limit"] and intent_res.limit_val:
                issues.append(f"Missing LIMIT {intent_res.limit_val} clause for Top-N query.")
                recommendations.append(f"Add LIMIT {intent_res.limit_val}.")
                score -= 0.25

        # Intent E: DATE_RANGE
        elif intent_res.intent == QueryIntent.DATE_RANGE:
            if not ast["has_where"]:
                issues.append("Missing date range filter in WHERE clause.")
                recommendations.append("Add WHERE date BETWEEN 'start' AND 'end' (or >= start AND <= end).")
                score -= 0.45

        # Intent F: FILTER_LIST
        elif intent_res.intent == QueryIntent.FILTER_LIST:
            # Check numeric filter (e.g. precipitation > 20)
            if intent_res.numeric_filters:
                nf = intent_res.numeric_filters[0]
                expected_col = nf["col"].lower()
                if not ast["has_where"] or expected_col not in ast["where_columns"]:
                    issues.append(f"Missing numeric filter on '{expected_col}' ({nf['op']} {nf['val']}).")
                    recommendations.append(f"Add WHERE {expected_col} {nf['op']} {nf['val']}.")
                    score -= 0.35

        # Intent: COMPARATIVE_AGGREGATION
        elif intent_res.intent == QueryIntent.COMPARATIVE_AGGREGATION:
            if not ast["has_group_by"]:
                issues.append("Missing GROUP BY clause. Comparative aggregation questions require grouping by the requested dimension.")
                recommendations.append("Add GROUP BY with the dimension column.")
                score -= 0.40

            if not ast["has_order_by"]:
                issues.append("Missing ORDER BY clause. Comparative aggregation requires sorting to select the winning record.")
                recommendations.append("Add ORDER BY with the calculated metric.")
                score -= 0.35

            if not ast["has_limit"]:
                issues.append("Missing LIMIT clause. Comparative question asks for the winning condition (LIMIT 1).")
                recommendations.append("Add LIMIT 1.")
                score -= 0.20

            if intent_res.dimension:
                dim_low = intent_res.dimension.lower()
                all_sql_text = (ast.get("select_clause", "") + " " + " ".join(ast.get("group_by_columns", []))).lower()
                if dim_low not in all_sql_text and not (dim_low in ["month", "months"] and any(k in all_sql_text for k in ["month", "date", "%m", "%y"])):
                    issues.append(f"Missing dimension column '{intent_res.dimension}' in SELECT or GROUP BY.")
                    recommendations.append(f"Include {intent_res.dimension} in SELECT and GROUP BY.")
                    score -= 0.25

        # Intent: SORTING
        elif intent_res.intent == QueryIntent.SORTING:
            if not ast["has_order_by"]:
                issues.append("Missing ORDER BY clause for sorting request.")
                recommendations.append("Add ORDER BY to sort records.")
                score -= 0.40

        # Intent: MULTI_CONDITION
        elif intent_res.intent == QueryIntent.MULTI_CONDITION:
            if not ast["has_where"]:
                issues.append("Missing WHERE clause for multi-condition query.")
                recommendations.append("Add WHERE clause with conditions combined by AND.")
                score -= 0.45

        # Intent G: UNSUPPORTED / INJECTION
        elif intent_res.intent == QueryIntent.INJECTION_ATTEMPT:
            issues.append("Security violation: Potential SQL injection or prohibited mutation.")
            score = 0.0

        elif intent_res.intent == QueryIntent.UNSUPPORTED:
            issues.append("Query intent is unsupported or unrelated to available database schema.")
            score = 0.20

        # =========================================================================
        # 3. UNIVERSAL CONSTRAINT COMPLETENESS VERIFICATION
        # Verify that all explicit user constraints survived into generated SQL
        # =========================================================================

        # 3a. Date Constraints
        for df in intent_res.date_filters:
            col = df["col"].lower()
            where_clause_str = ast.get("where_clause", "")
            where_cols = [c.lower() for c in ast.get("where_columns", [])]
            date_in_where = col in where_cols or col in where_clause_str.lower() or "strftime" in sql_query.lower()

            val_present = False
            if df.get("op") == "BETWEEN":
                val1 = str(df.get("val1", ""))
                val2 = str(df.get("val2", ""))
                val_present = val1 in sql_query and val2 in sql_query
            else:
                val = str(df.get("val", ""))
                val_present = val in sql_query or val[:4] in sql_query

            if not ast["has_where"] or not (date_in_where and val_present):
                issues.append(f"Constraint completeness failed: Missing date filter on '{col}' ({df.get('op', '=')} {df.get('val', df.get('val1', ''))}).")
                recommendations.append(f"Add required date filter on '{col}' to the WHERE clause.")
                score -= 0.50

        # 3b. Equality Constraints (e.g. weather = 'rain')
        for ef in intent_res.equality_filters:
            col = ef["col"].lower()
            val = str(ef["val"]).lower()
            where_clause_str = ast.get("where_clause", "").lower()
            where_cols = [c.lower() for c in ast.get("where_columns", [])]

            if not ast["has_where"] or col not in where_cols or val not in where_clause_str:
                issues.append(f"Constraint completeness failed: Missing expected equality filter '{col} = {ef['val']}'.")
                recommendations.append(f"Add WHERE {col} = '{ef['val']}'.")
                score -= 0.40

        # 3c. Numeric Constraints (e.g. precipitation > 10)
        for nf in intent_res.numeric_filters:
            col = nf["col"].lower()
            val_str = str(nf["val"])
            where_clause_str = ast.get("where_clause", "")
            where_cols = [c.lower() for c in ast.get("where_columns", [])]

            if not ast["has_where"] or col not in where_cols or val_str not in where_clause_str:
                issues.append(f"Constraint completeness failed: Missing numeric filter '{col} {nf['op']} {nf['val']}'.")
                recommendations.append(f"Add WHERE {col} {nf['op']} {nf['val']}.")
                score -= 0.40

        # 3d. Limit Constraint if explicitly requested
        if intent_res.limit_val is not None and not ast["has_limit"]:
            issues.append(f"Constraint completeness failed: Missing LIMIT {intent_res.limit_val} clause.")
            recommendations.append(f"Add LIMIT {intent_res.limit_val}.")
            score -= 0.30

        has_constraint_failure = any("Constraint completeness failed" in i for i in issues)
        if has_constraint_failure:
            score = min(score, 0.30)

        # Ensure score bounds
        semantic_score = max(0.0, min(1.0, round(score, 2)))
        is_valid = len(issues) == 0 or (
            semantic_score >= 0.75
            and not has_constraint_failure
            and not any(
                "Unexpected GROUP BY" in i
                or "Unexpected aggregations" in i
                or "Security violation" in i
                or "Missing GROUP BY" in i
                or "Comparative aggregation" in i
                for i in issues
            )
        )

        return SemanticValidationResult(
            is_valid=is_valid,
            semantic_score=semantic_score,
            issues=issues,
            recommendations=recommendations,
            ast_summary=ast,
        )


semantic_validator = SemanticValidator()
