import re
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple


class QueryIntent(str, Enum):
    DIRECT_LOOKUP = "DIRECT_LOOKUP"                    # Exact single-entity/date lookup (WHERE, no agg, no group by)
    FILTER = "FILTER"                                  # Filtered list of rows
    FILTER_LIST = "FILTER"                            # Backward-compatible alias
    AGGREGATION = "AGGREGATION"                        # Dataset-wide aggregation (AVG, SUM, COUNT, MIN, MAX) without GROUP BY
    GROUPED_AGGREGATION = "GROUPED_AGGREGATION"        # Aggregation with explicit GROUP BY ("by ...", "for each ...")
    GROUPING = "GROUPED_AGGREGATION"                  # Backward-compatible alias
    COMPARATIVE_AGGREGATION = "COMPARATIVE_AGGREGATION"# Compare groups, rank them, and pick winner ("Which ... had highest/lowest ...")
    TOP_N = "TOP_N"                                    # Ranked ordering with LIMIT ("top 10", "hottest day", "highest precipitation")
    TOP_N_WITH_FILTER = "TOP_N_WITH_FILTER"            # Top-N ranked ordering combined with explicit WHERE filter(s)
    NESTED_ANALYTICAL = "NESTED_ANALYTICAL"            # Multi-stage query with dependent subqueries or CTEs
    SORTING = "SORTING"                                # Explicit ordering ("sort by temperature asc")
    DATE_RANGE = "DATE_RANGE"                          # Date interval (BETWEEN or >= AND <=)
    MULTI_CONDITION = "MULTI_CONDITION"                # Multiple WHERE filters combined with AND
    INJECTION_ATTEMPT = "INJECTION_ATTEMPT"            # Suspicious or malicious intent
    UNSUPPORTED_QUERY = "UNSUPPORTED_QUERY"            # Unrelated question not answerable by database schema
    UNSUPPORTED = "UNSUPPORTED_QUERY"                  # Backward-compatible alias


MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7, "aug": 8, "sep": 9, "sept": 9,
    "oct": 10, "nov": 11, "dec": 12,
}


class StructuredQueryPlan:
    """Explicit intermediate structured representation of a user query plan."""

    def __init__(
        self,
        intent: str,
        table: str,
        select: List[str],
        filters: List[Dict[str, Any]],
        group_by: Optional[List[str]] = None,
        sort: Optional[Dict[str, str]] = None,
        limit: Optional[int] = None,
        aggregations: Optional[List[Dict[str, Any]]] = None,
        stages: Optional[List[Dict[str, Any]]] = None,
        dependency: Optional[Dict[str, Any]] = None,
    ):
        self.intent = intent
        self.table = table
        self.select = select
        self.filters = filters
        self.group_by = group_by or []
        self.sort = sort
        self.limit = limit
        self.aggregations = aggregations or []
        self.stages = stages
        self.dependency = dependency

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "intent": self.intent,
            "table": self.table,
            "select": self.select,
            "filters": self.filters,
            "group_by": self.group_by,
            "sort": self.sort,
            "limit": self.limit,
            "aggregations": self.aggregations,
        }
        if self.stages:
            data["stages"] = self.stages
        if self.dependency:
            data["dependency"] = self.dependency
        return data


class IntentAnalysisResult:
    """Structured semantic representation of the user request."""

    def __init__(
        self,
        intent: QueryIntent,
        confidence: float,
        target_columns: List[str],
        date_filters: List[Dict[str, Any]],
        numeric_filters: List[Dict[str, Any]],
        equality_filters: List[Dict[str, Any]],
        group_by_columns: List[str],
        aggregations: List[str],
        dimension: Optional[str] = None,
        metric: Optional[str] = None,
        aggregation: Optional[str] = None,
        comparison: Optional[str] = None,
        ordering_col: Optional[str] = None,
        ordering_dir: Optional[str] = None,
        limit_val: Optional[int] = None,
        raw_prompt: str = "",
        is_read_only_safe: bool = True,
        explanation: str = "",
        query_plan: Optional[StructuredQueryPlan] = None,
        stages: Optional[List[Dict[str, Any]]] = None,
        dependency: Optional[Dict[str, Any]] = None,
    ):
        self.intent = intent
        self.confidence = confidence
        self.target_columns = target_columns
        self.date_filters = date_filters
        self.numeric_filters = numeric_filters
        self.equality_filters = equality_filters
        self.group_by_columns = group_by_columns
        self.aggregations = aggregations
        self.dimension = dimension
        self.metric = metric
        self.aggregation = aggregation
        self.comparison = comparison
        self.ordering_col = ordering_col
        self.ordering_dir = ordering_dir
        self.limit_val = limit_val
        self.raw_prompt = raw_prompt
        self.is_read_only_safe = is_read_only_safe
        self.explanation = explanation
        self.query_plan = query_plan
        self.stages = stages
        self.dependency = dependency

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "intent": self.intent.value,
            "confidence": self.confidence,
            "dimension": self.dimension,
            "metric": self.metric,
            "aggregation": self.aggregation,
            "comparison": self.comparison,
            "limit": self.limit_val,
            "target_columns": self.target_columns,
            "date_filters": self.date_filters,
            "numeric_filters": self.numeric_filters,
            "equality_filters": self.equality_filters,
            "group_by_columns": self.group_by_columns,
            "aggregations": self.aggregations,
            "ordering_col": self.ordering_col,
            "ordering_dir": self.ordering_dir,
            "is_read_only_safe": self.is_read_only_safe,
            "explanation": self.explanation,
            "query_plan": self.query_plan.to_dict() if self.query_plan else None,
        }
        if self.stages:
            data["stages"] = self.stages
        if self.dependency:
            data["dependency"] = self.dependency
        return data


class IntentAnalyzer:
    """Enterprise NLP Intent & Constraint Extraction Engine."""

    @staticmethod
    def parse_natural_date(date_str: str) -> Optional[str]:
        """Convert 'January 1, 2012', '2012-01-01', 'March 15 2015' into ISO 'YYYY-MM-DD'."""
        clean = date_str.strip().strip(",").strip(".")
        iso_match = re.search(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b", clean)
        if iso_match:
            y, m, d = int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3))
            return f"{y:04d}-{m:02d}-{d:02d}"

        m_d_y = re.search(r"\b([A-Za-z]+)\s+(\d{1,2})(?:st|nd|rd|th)?(?:,)?\s+(\d{4})\b", clean)
        if m_d_y:
            m_str, d_str, y_str = m_d_y.group(1).lower(), m_d_y.group(2), m_d_y.group(3)
            if m_str in MONTHS:
                return f"{int(y_str):04d}-{MONTHS[m_str]:02d}-{int(d_str):02d}"

        d_m_y = re.search(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]+)(?:,)?\s+(\d{4})\b", clean)
        if d_m_y:
            d_str, m_str, y_str = d_m_y.group(1), d_m_y.group(2).lower(), d_m_y.group(3)
            if m_str in MONTHS:
                return f"{int(y_str):04d}-{MONTHS[m_str]:02d}-{int(d_str):02d}"

        return None

    def _decompose_nested_query(
        self,
        p: str,
        prompt: str,
        schema_tables: List[Dict[str, Any]],
        all_cols_map: Dict[str, str],
        is_weather_schema: bool,
        target_table_name: str,
    ) -> Optional[Tuple[Dict[str, Any], str]]:
        """
        Decomposes nested analytical questions into Stage 1 (subquery/CTE) and Stage 2 (clean prompt).
        Examples:
          'Which weather condition had the highest average maximum temperature during the year with the most precipitation?'
          -> Stage 1: find wettest year (GROUP BY year ORDER BY SUM(precipitation) DESC LIMIT 1)
          -> Clean Stage 2: 'Which weather condition had the highest average maximum temperature?'
        """
        # Pattern 1: 'during/in the [year/month/period] with the [most/least/highest/lowest] [metric]'
        p1 = re.compile(
            r"\b(during|in|for|throughout)\s+(?:the\s+)?(year|month|day|period|category)\s+(?:with|having|that had|of)\s+(?:the\s+)?(most|least|highest|lowest|greatest|smallest|maximum|minimum|max|min|peak)\s+([a-zA-Z_ ]+?)(?:\.|\?|$|\s+and|\s+where)",
            re.IGNORECASE,
        )
        # Pattern 2: 'during/in the [wettest/driest/hottest/coldest/windiest] [year/month]'
        p2 = re.compile(
            r"\b(during|in|for|throughout)\s+(?:the\s+)?(wettest|driest|hottest|coldest|windiest)\s+(year|month|day|period)\b(?:\.|\?|$)?",
            re.IGNORECASE,
        )

        m1 = p1.search(prompt)
        m2 = p2.search(prompt)

        raw_dim = None
        superlative = None
        metric_phrase = ""
        matched_span = None

        if m1:
            raw_dim = m1.group(2).lower()
            superlative = m1.group(3).lower()
            metric_phrase = m1.group(4).lower().strip()
            matched_span = m1.span()
        elif m2:
            superlative = m2.group(2).lower()
            raw_dim = m2.group(3).lower()
            matched_span = m2.span()
            if superlative in ["wettest", "driest"]:
                metric_phrase = "precipitation"
            elif superlative in ["hottest", "coldest"]:
                metric_phrase = "temperature"
            elif superlative in ["windiest"]:
                metric_phrase = "wind"

        if not raw_dim or not superlative:
            return None

        # Determine metric, aggregation and ranking direction
        ranking = "DESC" if superlative in ["most", "highest", "greatest", "peak", "maximum", "max", "wettest", "hottest", "windiest"] else "ASC"

        agg = "SUM"
        metric = "precipitation"

        if "wind" in metric_phrase:
            metric = all_cols_map.get("wind", "wind")
            agg = "AVG" if any(w in metric_phrase for w in ["average", "avg", "mean"]) else "MAX"
        elif any(w in metric_phrase for w in ["precipitation", "rainfall", "rain"]):
            metric = all_cols_map.get("precipitation", "precipitation")
            agg = "AVG" if any(w in metric_phrase for w in ["average", "avg", "mean"]) else "SUM"
        elif any(w in metric_phrase for w in ["temperature", "temp", "maximum temperature", "max temp"]):
            metric = all_cols_map.get("temp_max", "temp_max") if superlative != "coldest" else all_cols_map.get("temp_min", "temp_min")
            agg = "AVG"
        elif any(w in metric_phrase for w in ["sales", "revenue", "amount", "spend"]):
            metric = "total_amount" if "total_amount" in all_cols_map else ("sales" if "sales" in all_cols_map else "amount")
            agg = "SUM"
        else:
            for c_low, c_orig in all_cols_map.items():
                if c_low in metric_phrase:
                    metric = c_orig
                    break
            agg = "AVG" if any(w in metric_phrase for w in ["average", "avg", "mean"]) else "SUM"

        date_col = all_cols_map.get("date", "date")
        if raw_dim == "year":
            dim_col_expr = f"STRFTIME('%Y', {date_col})"
            dim_alias = "year"
            cte_name = "target_year"
        elif raw_dim == "month":
            dim_col_expr = f"STRFTIME('%Y-%m', {date_col})"
            dim_alias = "month"
            cte_name = "target_month"
        else:
            dim_col = all_cols_map.get(raw_dim, raw_dim)
            dim_col_expr = dim_col
            dim_alias = raw_dim
            cte_name = f"target_{raw_dim}"

        stage_1_plan = {
            "stage_id": "stage_1",
            "operation": "GROUP_AND_RANK",
            "table": target_table_name,
            "dimension": f"{raw_dim}(date)" if raw_dim in ["year", "month"] else raw_dim,
            "dimension_expression": dim_col_expr,
            "dimension_alias": dim_alias,
            "metric": metric,
            "aggregation": agg,
            "ranking": ranking,
            "limit": 1,
            "cte_name": cte_name,
        }

        # Build clean Stage 2 prompt by removing the dependent clause
        start, end = matched_span
        clean_prompt = (prompt[:start] + " " + prompt[end:]).strip()
        clean_prompt = re.sub(r"\s+", " ", clean_prompt)
        if not clean_prompt.endswith("?") and prompt.strip().endswith("?"):
            clean_prompt += "?"

        return stage_1_plan, clean_prompt

    def analyze(self, prompt: str, schema_tables: List[Dict[str, Any]], is_nested_child: bool = False) -> IntentAnalysisResult:
        p = prompt.strip().lower()

        # 1. Security / Malicious Check
        malicious_keywords = ["drop table", "delete from", "truncate table", "alter table", "update ", "insert into", "exec ", "execute "]
        if any(mk in p for mk in malicious_keywords) or re.search(r";\s*(?:drop|delete|truncate|alter)", p):
            return IntentAnalysisResult(
                intent=QueryIntent.INJECTION_ATTEMPT,
                confidence=0.0,
                target_columns=[],
                date_filters=[],
                numeric_filters=[],
                equality_filters=[],
                group_by_columns=[],
                aggregations=[],
                is_read_only_safe=False,
                raw_prompt=prompt,
                explanation="Malicious or destructive SQL pattern detected in query.",
            )

        # 2. Gather available columns & table contexts from schema
        all_cols_map = {}
        all_col_types = {}
        target_table_name = None

        if schema_tables:
            for tbl in schema_tables:
                t_name = tbl.get("name", "")
                if t_name.lower() in p or t_name.lower().rstrip("s") in p:
                    target_table_name = t_name
                    break
            if not target_table_name:
                target_table_name = schema_tables[0].get("name", "")

            target_table_obj = next((t for t in schema_tables if t.get("name", "").lower() == target_table_name.lower()), schema_tables[0])
            for col in target_table_obj.get("columns", []):
                cn = col.get("name", "")
                all_cols_map[cn.lower()] = cn
                all_col_types[cn.lower()] = str(col.get("type", "")).upper()

        is_weather_schema = "weather" in all_cols_map and "precipitation" in all_cols_map

        # Check for completely unrelated / unsupported questions
        unsupported_keywords = [
            "president", "poem", "joke", "recipe", "capital of", "bake", "cake",
            "france", "prime minister", "who is", "who was", "write a", "how to cook"
        ]
        if any(uk in p for uk in unsupported_keywords):
            return IntentAnalysisResult(
                intent=QueryIntent.UNSUPPORTED_QUERY,
                confidence=0.20,
                target_columns=[],
                date_filters=[],
                numeric_filters=[],
                equality_filters=[],
                group_by_columns=[],
                aggregations=[],
                raw_prompt=prompt,
                explanation="Question is unrelated to the active database schema.",
            )

        # 2b. Multi-Stage Query Decomposition & Dependency Extraction
        if not is_nested_child:
            decomp = self._decompose_nested_query(p, prompt, schema_tables, all_cols_map, is_weather_schema, target_table_name)
            if decomp:
                stage_1_dict, clean_stage_2_prompt = decomp
                stage_2_res = self.analyze(clean_stage_2_prompt, schema_tables, is_nested_child=True)

                stages = [
                    stage_1_dict,
                    stage_2_res.query_plan.to_dict() if stage_2_res.query_plan else {
                        "operation": stage_2_res.intent.value,
                        "dimension": stage_2_res.dimension,
                        "metric": stage_2_res.metric,
                        "aggregation": stage_2_res.aggregation,
                        "ranking": stage_2_res.ordering_dir,
                        "limit": stage_2_res.limit_val,
                    }
                ]
                dependency = {
                    "type": "CTE_FILTER",
                    "target_cte": stage_1_dict.get("cte_name", "target_year"),
                    "column_expression": stage_1_dict.get("dimension_expression", "STRFTIME('%Y', date)"),
                    "operator": "=",
                    "subquery_column": stage_1_dict.get("dimension_alias", "year"),
                }

                nested_plan = StructuredQueryPlan(
                    intent=QueryIntent.NESTED_ANALYTICAL.value,
                    table=target_table_name or "dataset",
                    select=stage_2_res.query_plan.select if stage_2_res.query_plan else (stage_2_res.target_columns or ["weather"]),
                    filters=stage_2_res.query_plan.filters if stage_2_res.query_plan else [],
                    group_by=stage_2_res.query_plan.group_by if stage_2_res.query_plan else [],
                    sort=stage_2_res.query_plan.sort if stage_2_res.query_plan else None,
                    limit=stage_2_res.query_plan.limit if stage_2_res.query_plan else None,
                    aggregations=stage_2_res.query_plan.aggregations if stage_2_res.query_plan else [],
                    stages=stages,
                    dependency=dependency,
                )

                return IntentAnalysisResult(
                    intent=QueryIntent.NESTED_ANALYTICAL,
                    confidence=0.98,
                    target_columns=stage_2_res.target_columns,
                    date_filters=stage_2_res.date_filters,
                    numeric_filters=stage_2_res.numeric_filters,
                    equality_filters=stage_2_res.equality_filters,
                    group_by_columns=stage_2_res.group_by_columns,
                    aggregations=stage_2_res.aggregations,
                    dimension=stage_2_res.dimension,
                    metric=stage_2_res.metric,
                    aggregation=stage_2_res.aggregation,
                    comparison=stage_2_res.comparison,
                    ordering_col=stage_2_res.ordering_col,
                    ordering_dir=stage_2_res.ordering_dir,
                    limit_val=stage_2_res.limit_val,
                    raw_prompt=prompt,
                    is_read_only_safe=True,
                    explanation=f"Detected multi-stage nested analytical query: Stage 1 finds '{stage_1_dict.get('cte_name')}' based on {stage_1_dict.get('aggregation')}({stage_1_dict.get('metric')}) {stage_1_dict.get('ranking')}, Stage 2 executes '{stage_2_res.intent.value}' filtered by Stage 1.",
                    query_plan=nested_plan,
                    stages=stages,
                    dependency=dependency,
                )

        # 3. Extract Date Information
        date_filters = []

        # 3a. Between month X and month Y of year Z: "between January and March 2012"
        month_range_match = re.search(
            r"\bbetween\s+([A-Za-z]+)\s+and\s+([A-Za-z]+)(?:,)?\s+(\d{4})\b",
            prompt,
            re.IGNORECASE,
        )
        if month_range_match and month_range_match.group(1).lower() in MONTHS and month_range_match.group(2).lower() in MONTHS:
            m1 = MONTHS[month_range_match.group(1).lower()]
            m2 = MONTHS[month_range_match.group(2).lower()]
            y = int(month_range_match.group(3))
            next_m = m2 + 1
            next_y = y
            if next_m > 12:
                next_m = 1
                next_y += 1
            date_col = all_cols_map.get("date", "date")
            date_filters.append({"col": date_col, "op": ">=", "val": f"{y:04d}-{m1:02d}-01"})
            date_filters.append({"col": date_col, "op": "<", "val": f"{next_y:04d}-{next_m:02d}-01"})

        # 3b. Between full dates
        if not date_filters:
            between_match = re.search(
                r"\bbetween\s+([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?(?:,)?\s+\d{4}|\d{4}-\d{2}-\d{2})\s+and\s+([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?(?:,)?\s+\d{4}|\d{4}-\d{2}-\d{2})\b",
                prompt,
                re.IGNORECASE,
            )
            if between_match:
                d1 = self.parse_natural_date(between_match.group(1))
                d2 = self.parse_natural_date(between_match.group(2))
                if d1 and d2:
                    date_filters.append({"col": all_cols_map.get("date", "date"), "op": "BETWEEN", "val1": d1, "val2": d2})
            else:
                split_range_match = re.search(
                    r"\bbetween\s+([A-Za-z]+)\s+(\d{1,2})(?:st|nd|rd|th)?\s+and\s+(?:([A-Za-z]+)\s+)?(\d{1,2})(?:st|nd|rd|th)?(?:,)?\s+(\d{4})\b",
                    prompt,
                    re.IGNORECASE,
                )
                if split_range_match:
                    m1_name = split_range_match.group(1).lower()
                    d1_num = split_range_match.group(2)
                    m2_name = (split_range_match.group(3) or m1_name).lower()
                    d2_num = split_range_match.group(4)
                    y_num = split_range_match.group(5)
                    if m1_name in MONTHS and m2_name in MONTHS:
                        d1 = f"{int(y_num):04d}-{MONTHS[m1_name]:02d}-{int(d1_num):02d}"
                        d2 = f"{int(y_num):04d}-{MONTHS[m2_name]:02d}-{int(d2_num):02d}"
                        date_filters.append({"col": all_cols_map.get("date", "date"), "op": "BETWEEN", "val1": d1, "val2": d2})

        # 3c. Relational dates: "after January 1, 2012", "before January 1, 2013", "since ...", "until ..."
        if not date_filters:
            after_match = re.search(r"\b(?:after|since|from)\s+([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?(?:,)?\s+\d{4}|\d{4}-\d{2}-\d{2})\b", prompt, re.IGNORECASE)
            if after_match:
                d_after = self.parse_natural_date(after_match.group(1))
                if d_after:
                    op = ">=" if any(w in p for w in ["from", "since", "on or after"]) else ">"
                    date_filters.append({"col": all_cols_map.get("date", "date"), "op": op, "val": d_after})

            before_match = re.search(r"\b(?:before|until|prior to)\s+([A-Za-z]+\s+\d{1,2}(?:st|nd|rd|th)?(?:,)?\s+\d{4}|\d{4}-\d{2}-\d{2})\b", prompt, re.IGNORECASE)
            if before_match:
                d_before = self.parse_natural_date(before_match.group(1))
                if d_before:
                    op = "<=" if any(w in p for w in ["until", "on or before"]) else "<"
                    date_filters.append({"col": all_cols_map.get("date", "date"), "op": op, "val": d_before})

        # 3d. Exact single date: "on January 1, 2012", "January 1, 2012", "2014-06-20", "March 15, 2015"
        if not date_filters:
            single_date = self.parse_natural_date(prompt)
            if single_date:
                date_filters.append({"col": all_cols_map.get("date", "date"), "op": "=", "val": single_date})

        # 3e. Month + Year: "in November 2013", "during March 2012", "for November 2013"
        if not date_filters:
            month_year_match = re.search(r"\b(?:in|for|during)\s+([A-Za-z]+)\s+(\d{4})\b", prompt, re.IGNORECASE)
            if month_year_match and month_year_match.group(1).lower() in MONTHS:
                m_val = MONTHS[month_year_match.group(1).lower()]
                y_val = int(month_year_match.group(2))
                date_col = all_cols_map.get("date", "date")
                next_y = y_val if m_val < 12 else y_val + 1
                next_m = m_val + 1 if m_val < 12 else 1
                date_filters.append({"col": date_col, "op": ">=", "val": f"{y_val:04d}-{m_val:02d}-01"})
                date_filters.append({"col": date_col, "op": "<", "val": f"{next_y:04d}-{next_m:02d}-01"})

        # 3f. Year only: "during 2012", "in 2012", "throughout 2012", "in 2015", "in 2013", "in 2014", "year 2012", or year in query
        if not date_filters:
            year_match = re.search(r"\b(?:during|in|throughout|for(?:\s+the)?(?:\s+year)?)\s+(?:the\s+year\s+)?(\d{4})\b", prompt, re.IGNORECASE)
            if not year_match:
                # Check for calendar year (e.g., 2012-2015) in weather context if not preceded by non-date words
                year_match = re.search(r"\b(201[0-9]|202[0-9])\b", prompt)
            if year_match and not any(w in p for w in ["president", "war"]):
                y_val = int(year_match.group(1))
                date_col = all_cols_map.get("date", "date")
                date_filters.append({"col": date_col, "op": ">=", "val": f"{y_val:04d}-01-01"})
                date_filters.append({"col": date_col, "op": "<", "val": f"{y_val+1:04d}-01-01"})

        # 4. Extract Numeric Filters
        numeric_filters = []
        num_word_patterns = [
            (r"(?:precipitation|rainfall)\s+(?:was\s+)?(?:greater than|more than|higher than|above|exceeded|>)\s*(\d+(?:\.\d+)?)", "precipitation", ">"),
            (r"(?:precipitation|rainfall)\s+(?:was\s+)?(?:less than|under|below|<)\s*(\d+(?:\.\d+)?)", "precipitation", "<"),
            (r"(?:temp_max|maximum temp(?:erature)?|max temp)\s+(?:was\s+)?(?:greater than|above|>)\s*(\d+(?:\.\d+)?)", "temp_max", ">"),
            (r"(?:temp_min|minimum temp(?:erature)?|min temp)\s+(?:was\s+)?(?:less than|under|below|<)\s*(\d+(?:\.\d+)?)", "temp_min", "<"),
            (r"(?:wind|wind speed)\s+(?:was\s+)?(?:greater than|more than|higher than|above|exceeded|>)\s*(\d+(?:\.\d+)?)", "wind", ">"),
            (r"(?:wind|wind speed)\s+(?:was\s+)?(?:less than|under|below|<)\s*(\d+(?:\.\d+)?)", "wind", "<"),
            (r"(?:price|cost)\s*([><]=?|=)\s*(\d+(?:\.\d+)?)", "price", None),
        ]
        for pat, col, forced_op in num_word_patterns:
            m = re.search(pat, p)
            if m:
                actual_col = all_cols_map.get(col, col)
                if forced_op:
                    val = float(m.group(1)) if "." in m.group(1) else int(m.group(1))
                    numeric_filters.append({"col": actual_col, "op": forced_op, "val": val})
                else:
                    op = m.group(1)
                    val = float(m.group(2)) if "." in m.group(2) else int(m.group(2))
                    numeric_filters.append({"col": actual_col, "op": op, "val": val})

        # 5. Extract Categorical Equality Filters (e.g., "rainy days", "during rainy days" -> weather = 'rain')
        equality_filters = []
        if is_weather_schema:
            weather_conditions = ["rain", "sun", "drizzle", "fog", "snow"]
            for cond in weather_conditions:
                if cond in p or (cond == "rain" and "rainy" in p) or (cond == "sun" and "sunny" in p) or (cond == "fog" and "foggy" in p) or (cond == "snow" and "snowy" in p):
                    # Ensure it's a filter, not asking for "which weather condition" or "for each weather condition"
                    if not any(phrase in p for phrase in ["which weather", "what weather", "each weather", "by weather", "per weather", "across weather"]):
                        # "rainiest" is an ordering requirement unless "rainy" is also an explicit condition
                        if cond == "rain" and "rainiest" in p and not any(phrase in p for phrase in ["rainy", "rain day", "rain condition", "days with rain", "with rain"]):
                            pass
                        else:
                            equality_filters.append({"col": all_cols_map.get("weather", "weather"), "op": "=", "val": cond})
                            break

        # 6. Detect COMPARATIVE AGGREGATION
        # Questions such as: "Which weather condition had the highest average maximum temperature?"
        # Pattern: Which/What <dimension> had the highest/lowest/most/least <metric/agg>
        dimension = None
        metric = None
        comp_agg = None
        comparison = None
        limit_val = None
        ordering_col = None
        ordering_dir = None

        comp_pattern = re.search(
            r"\b(?:which|what)\s+(?!is\b|was\b|are\b|were\b)(?:type of\s+|kind of\s+)?([a-zA-Z0-9_ ]+?)\s+(?:(?:had|has|have|with|showed|recorded|experienced|saw|is|was|occurred)\s+)?(?:the\s+)?(highest|lowest|most|least|greatest|smallest|best|worst|peak|max|maximum|min|minimum)\b",
            p
        )
        if comp_pattern:
            raw_dim = comp_pattern.group(1).lower().strip()
            comp_word = comp_pattern.group(2).lower()

            # Map raw dimension
            dim_candidate = None
            if raw_dim in ["weather condition", "weather conditions", "weather", "condition", "conditions"]:
                dim_candidate = all_cols_map.get("weather", "weather")
            elif raw_dim in ["month", "months"]:
                dim_candidate = "month"
            elif raw_dim in ["year", "years"]:
                dim_candidate = "year"
            elif raw_dim in ["day", "days", "date", "dates"]:
                dim_candidate = all_cols_map.get("date", "date")
            elif raw_dim in all_cols_map:
                dim_candidate = all_cols_map[raw_dim]
            elif raw_dim.rstrip("s") in all_cols_map:
                dim_candidate = all_cols_map[raw_dim.rstrip("s")]
            elif raw_dim in ["category", "categories"]:
                dim_candidate = all_cols_map.get("category", "category")
            elif raw_dim in ["country", "nation"]:
                dim_candidate = all_cols_map.get("country", "country")
            else:
                for c_low, c_orig in all_cols_map.items():
                    if c_low in raw_dim or raw_dim in c_low:
                        dim_candidate = c_orig
                        break

            if dim_candidate:
                dimension = dim_candidate
                comparison = "MAX" if comp_word in ["highest", "most", "greatest", "best", "peak", "max", "maximum"] else "MIN"
                ordering_dir = "DESC" if comparison == "MAX" else "ASC"
                limit_val = 1

                # Determine metric and aggregation
                if any(w in p for w in ["occurred most often", "occurred least often", "most often", "least often", "most common", "most frequent", "occurred most"]):
                    metric = None
                    comp_agg = "COUNT"
                elif any(w in p for w in ["average maximum temperature", "avg maximum temp", "average max temp"]):
                    metric = all_cols_map.get("temp_max", "temp_max")
                    comp_agg = "AVG"
                elif any(w in p for w in ["average minimum temperature", "avg min temp"]):
                    metric = all_cols_map.get("temp_min", "temp_min")
                    comp_agg = "AVG"
                elif any(w in p for w in ["average temperature", "avg temp", "average temp"]):
                    metric = all_cols_map.get("temp_max", "temp_max")
                    comp_agg = "AVG"
                elif any(w in p for w in ["average wind", "avg wind"]):
                    metric = all_cols_map.get("wind", "wind")
                    comp_agg = "AVG"
                elif any(w in p for w in ["wind speed", "wind", "windiest"]):
                    metric = all_cols_map.get("wind", "wind")
                    comp_agg = "MAX" if comparison == "MAX" else "MIN"
                elif any(w in p for w in ["rainy days", "days of rain", "days with rain", "rainy day"]):
                    metric = all_cols_map.get("date", "date")
                    comp_agg = "COUNT"
                    if not equality_filters and is_weather_schema:
                        equality_filters.append({"col": all_cols_map.get("weather", "weather"), "op": "=", "val": "rain"})
                elif any(w in p for w in ["precipitation", "rainfall", "rain"]):
                    metric = all_cols_map.get("precipitation", "precipitation")
                    comp_agg = "SUM" if "total" in p else ("MAX" if comparison == "MAX" else "MIN")
                elif any(w in p for w in ["maximum temperature", "max temp", "temperature", "temp", "hottest"]):
                    metric = all_cols_map.get("temp_max", "temp_max")
                    comp_agg = "MAX" if comparison == "MAX" else "MIN"
                elif any(w in p for w in ["minimum temperature", "min temp", "coldest"]):
                    metric = all_cols_map.get("temp_min", "temp_min")
                    comp_agg = "MIN" if comparison == "MIN" else "MAX"
                else:
                    if any(w in p for w in ["average", "avg", "mean"]):
                        comp_agg = "AVG"
                    elif any(w in p for w in ["total", "sum of", "sum"]):
                        comp_agg = "SUM"
                    elif any(w in p for w in ["count", "number of"]):
                        comp_agg = "COUNT"
                    else:
                        comp_agg = "MAX" if comparison == "MAX" else "MIN"

                    for c_low, c_orig in all_cols_map.items():
                        if c_orig != dimension and (c_low in p or any(w in p for w in c_low.split("_"))):
                            metric = c_orig
                            break

        # 7. Extract Group By Intent for Non-Comparative Grouped Aggregations
        group_by_columns = []
        if dimension:
            group_by_columns.append(dimension)
        else:
            group_phrases = [
                r"\bfor each\s+([a-zA-Z_]+(?:\s+[a-zA-Z_]+)?)\b",
                r"\bby\s+([a-zA-Z_]+(?:\s+[a-zA-Z_]+)?)\b",
                r"\bper\s+([a-zA-Z_]+(?:\s+[a-zA-Z_]+)?)\b",
                r"\bacross\s+([a-zA-Z_]+(?:\s+[a-zA-Z_]+)?)\b",
                r"\bbreakdown by\s+([a-zA-Z_]+(?:\s+[a-zA-Z_]+)?)\b",
                r"\bgrouped by\s+([a-zA-Z_]+(?:\s+[a-zA-Z_]+)?)\b",
            ]
            for gp in group_phrases:
                gm = re.search(gp, p)
                if gm:
                    phrase_col = gm.group(1).lower().strip()
                    if phrase_col in ["weather", "condition", "conditions", "weather condition", "weather conditions"]:
                        phrase_col = "weather"
                    elif phrase_col in ["month", "months"]:
                        phrase_col = "month"
                    elif phrase_col in ["year", "years"]:
                        phrase_col = "year"
                    elif phrase_col in ["country", "nation"]:
                        phrase_col = "country"
                    elif phrase_col in ["category"]:
                        phrase_col = "category"

                    if phrase_col in all_cols_map:
                        group_by_columns.append(all_cols_map[phrase_col])
                    elif phrase_col in ["month", "year"]:
                        group_by_columns.append(phrase_col)
                    break

        # 8. Extract General Aggregation Intent
        aggregations = []
        if comp_agg:
            aggregations.append(comp_agg)
        else:
            if any(w in p for w in ["average", "avg", "mean"]):
                aggregations.append("AVG")
            if any(w in p for w in ["how many", "count", "number of", "total days", "total records"]):
                aggregations.append("COUNT")
            if any(w in p for w in ["total precipitation", "total rainfall", "sum of", "total amount", "total spend"]):
                aggregations.append("SUM")
            if any(w in p for w in ["highest", "maximum", "max", "peak", "most"]) and not any(w in p for w in ["average maximum", "avg max", "average"]):
                aggregations.append("MAX")
            if any(w in p for w in ["lowest", "minimum", "min", "least", "coldest"]) and not any(w in p for w in ["average minimum", "avg min", "average"]):
                aggregations.append("MIN")

        # 9. Extract Ordering and Top-N
        top_n_match = re.search(r"\b(?:top|first|limit)\s+(\d+)\b", p)
        if not top_n_match:
            top_n_match = re.search(r"\b(\d+)\s+days\b", p)
        if not top_n_match:
            top_n_match = re.search(r"\b(\d+)\s+(?:rainiest|coldest|hottest|windiest|highest|lowest)\b", p)
        if top_n_match and not limit_val:
            limit_val = int(top_n_match.group(1))

        # Explicit sorting
        sort_match = re.search(r"\b(?:sort|order)\s+(?:days|records|rows)?\s*(?:by\s+)?([a-zA-Z_]+)\s+(ascending|descending|asc|desc)\b", p)
        if sort_match:
            s_col = sort_match.group(1).lower()
            s_dir = "ASC" if "asc" in sort_match.group(2).lower() else "DESC"
            if s_col in ["temperature", "temp"]:
                s_col = "temp_max"
            if s_col in all_cols_map:
                ordering_col = all_cols_map[s_col]
                ordering_dir = s_dir

        if not ordering_col and not dimension:
            if any(w in p for w in ["hottest", "highest", "most", "peak", "maximum", "rainiest"]):
                ordering_dir = "DESC"
                if is_weather_schema:
                    if any(w in p for w in ["hottest", "maximum temperature", "highest temperature"]):
                        ordering_col = all_cols_map.get("temp_max", "temp_max")
                    elif any(w in p for w in ["rainiest", "precipitation", "rainfall", "rain"]):
                        ordering_col = all_cols_map.get("precipitation", "precipitation")
                    elif any(w in p for w in ["wind", "wind speed", "windiest"]):
                        ordering_col = all_cols_map.get("wind", "wind")
                if not limit_val and any(w in p for w in ["hottest day", "highest day", "the most rainy", "highest precipitation day"]):
                    limit_val = 1
            elif any(w in p for w in ["coldest", "lowest", "least", "minimum"]):
                ordering_dir = "ASC"
                if is_weather_schema:
                    if any(w in p for w in ["coldest", "minimum temperature", "lowest temperature"]):
                        ordering_col = all_cols_map.get("temp_min", "temp_min")
                    elif any(w in p for w in ["precipitation", "rainfall"]):
                        ordering_col = all_cols_map.get("precipitation", "precipitation")
                    elif any(w in p for w in ["wind", "wind speed"]):
                        ordering_col = all_cols_map.get("wind", "wind")
                if not limit_val and any(w in p for w in ["coldest day", "lowest day", "lowest wind speed"]):
                    limit_val = 1

        # 10. Target Columns for Output Display
        target_columns = []
        if is_weather_schema:
            if "weather" in p:
                target_columns.append(all_cols_map.get("weather", "weather"))
            if any(w in p for w in ["maximum temperature", "max temp", "hottest", "temperature", "temp"]):
                target_columns.append(all_cols_map.get("temp_max", "temp_max"))
            if any(w in p for w in ["minimum temperature", "min temp", "coldest"]):
                target_columns.append(all_cols_map.get("temp_min", "temp_min"))
            if any(w in p for w in ["precipitation", "rainfall", "rainiest", "rain"]):
                target_columns.append(all_cols_map.get("precipitation", "precipitation"))
            if any(w in p for w in ["wind", "wind speed"]):
                target_columns.append(all_cols_map.get("wind", "wind"))
            if any(w in p for w in ["day", "days", "date", "when"]):
                target_columns.append(all_cols_map.get("date", "date"))
        else:
            for c_low, c_orig in all_cols_map.items():
                if re.search(r"\b" + re.escape(c_low) + r"\b", p):
                    target_columns.append(c_orig)

        # Build unified filter list
        all_plan_filters: List[Dict[str, Any]] = []
        for df in date_filters:
            if df.get("op") == "BETWEEN":
                all_plan_filters.append({"column": df["col"], "operator": "BETWEEN", "val1": df["val1"], "val2": df["val2"]})
            else:
                all_plan_filters.append({"column": df["col"], "operator": df["op"], "value": df["val"]})
        for ef in equality_filters:
            all_plan_filters.append({"column": ef["col"], "operator": ef["op"], "value": ef["val"]})
        for nf in numeric_filters:
            all_plan_filters.append({"column": nf["col"], "operator": nf["op"], "value": nf["val"]})

        has_filters = len(all_plan_filters) > 0

        # =========================================================================
        # 11. INTENT CLASSIFICATION HIERARCHY
        # =========================================================================

        # Priority 1: Comparative Aggregation ("Which weather condition had the highest average maximum temperature?")
        if dimension and comparison:
            intent = QueryIntent.COMPARATIVE_AGGREGATION
            confidence = 0.98

        # Priority 2: Top-N with Filter (e.g. "Show the 5 days with the highest precipitation during 2012.")
        elif (ordering_col and limit_val and not group_by_columns and has_filters) or (limit_val and any(w in p for w in ["top", "highest precipitation", "lowest precipitation", "rainiest", "coldest", "hottest"]) and has_filters):
            intent = QueryIntent.TOP_N_WITH_FILTER
            confidence = 0.98

        # Priority 3: Pure Top-N / Extreme ranking across records (e.g. "What was the hottest day?", "Show 10 days with highest precipitation")
        elif (ordering_col and limit_val and not group_by_columns) or (limit_val and any(w in p for w in ["top", "highest precipitation", "lowest precipitation", "rainiest", "coldest", "hottest"])):
            intent = QueryIntent.TOP_N
            confidence = 0.97

        # Priority 4: Date Range
        elif date_filters and date_filters[0].get("op") == "BETWEEN":
            intent = QueryIntent.DATE_RANGE
            confidence = 0.98

        # Priority 5: Direct Lookup on exact single date
        elif date_filters and date_filters[0].get("op") == "=" and not group_by_columns and not any(a in aggregations for a in ["AVG", "SUM", "COUNT"]):
            intent = QueryIntent.DIRECT_LOOKUP
            confidence = 0.99

        # Priority 6: Explicit Sorting Query
        elif sort_match:
            intent = QueryIntent.SORTING
            confidence = 0.97

        # Priority 7: Grouped Aggregation ("for each weather condition", "breakdown by category")
        elif group_by_columns:
            intent = QueryIntent.GROUPED_AGGREGATION
            confidence = 0.97

        # Priority 8: Multi-Condition Filtering
        elif len(numeric_filters) + len(equality_filters) > 1:
            intent = QueryIntent.MULTI_CONDITION
            confidence = 0.96

        # Priority 9: Overall Dataset Aggregation (e.g. "What is the average maximum temperature?", "What is the highest temperature?")
        elif aggregations and not group_by_columns:
            intent = QueryIntent.AGGREGATION
            confidence = 0.97

        # Priority 10: Single Filtered List (e.g. "Show days when precipitation was greater than 20")
        elif numeric_filters or equality_filters:
            intent = QueryIntent.FILTER
            confidence = 0.96

        elif date_filters:
            intent = QueryIntent.DIRECT_LOOKUP
            confidence = 0.92
        else:
            intent = QueryIntent.FILTER
            confidence = 0.90

        # Construct Structured Query Plan
        plan_select = []
        if target_columns:
            plan_select = target_columns[:]
        elif is_weather_schema:
            plan_select = ["date", "precipitation", "weather"]
        else:
            plan_select = list(all_cols_map.values())[:4]

        query_plan = StructuredQueryPlan(
            intent=intent.value,
            table=target_table_name or (schema_tables[0].get("name", "dataset") if schema_tables else "dataset"),
            select=plan_select,
            filters=all_plan_filters,
            group_by=group_by_columns,
            sort={"column": ordering_col, "direction": ordering_dir} if ordering_col and ordering_dir else None,
            limit=limit_val,
            aggregations=[{"func": a, "column": metric or ordering_col} for a in aggregations],
        )

        return IntentAnalysisResult(
            intent=intent,
            confidence=confidence,
            target_columns=target_columns,
            date_filters=date_filters,
            numeric_filters=numeric_filters,
            equality_filters=equality_filters,
            group_by_columns=group_by_columns,
            aggregations=aggregations,
            dimension=dimension,
            metric=metric,
            aggregation=comp_agg or (aggregations[0] if aggregations else None),
            comparison=comparison,
            ordering_col=ordering_col,
            ordering_dir=ordering_dir,
            limit_val=limit_val,
            raw_prompt=prompt,
            explanation=f"Detected intent '{intent.value}' with dimension={dimension}, metric={metric}, agg={comp_agg or (aggregations[0] if aggregations else None)}, comparison={comparison}.",
            query_plan=query_plan,
        )


intent_analyzer = IntentAnalyzer()
