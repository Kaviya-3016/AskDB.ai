import re
from typing import Tuple, List, Dict, Any, Optional
import sqlparse
from sqlparse.sql import Statement, IdentifierList, Identifier, Where, Comparison
from sqlparse.tokens import Keyword, DML, DDL


DISALLOWED_KEYWORDS = {
    "DROP",
    "DELETE",
    "TRUNCATE",
    "ALTER",
    "INSERT",
    "UPDATE",
    "CREATE",
    "RENAME",
    "REPLACE",
    "MERGE",
    "GRANT",
    "REVOKE",
    "EXEC",
    "EXECUTE",
    "CALL",
    "KILL",
    "SHUTDOWN",
}

SUSPICIOUS_PATTERNS = [
    r"--",                     # SQL comment injection
    r"/\*.*?\*/",             # Block comment
    r";\s*\w+",               # Multi-statement injection (e.g. SELECT 1; DROP TABLE)
    r"xp_cmdshell",           # Command execution
    r"into\s+outfile",        # File dumping
    r"load_file",             # Local file read
    r"information_schema",    # Metadata discovery attempts (if untrusted)
    r"pg_shadow",
    r"pg_authid",
]


class SQLSecurityValidator:
    """Enterprise AST-level SQL Injection & Safety Validator."""

    @staticmethod
    def validate_and_sanitize(sql_query: str) -> Tuple[bool, bool, float, List[str], Optional[str]]:
        """
        Validates the SQL query against injection attacks, destructive mutations, and syntax abnormalities.
        Returns: (is_valid, is_read_only, safety_score, issues_list, formatted_sql)
        """
        issues: List[str] = []
        clean_sql = sql_query.strip().rstrip(";")

        if not clean_sql:
            return False, False, 0.0, ["Query is empty."], None

        # 1. Multi-statement check
        parsed_statements = sqlparse.parse(clean_sql)
        if len(parsed_statements) > 1:
            issues.append("Multiple SQL statements detected in a single request. Only single queries are permitted.")

        # 2. Regex pattern checks
        for pattern in SUSPICIOUS_PATTERNS:
            if re.search(pattern, clean_sql, re.IGNORECASE):
                issues.append(f"Suspicious SQL pattern detected matching security rule '{pattern}'.")

        # 3. Keyword / DDL / DML Mutation check
        is_read_only = True
        for statement in parsed_statements:
            first_token = statement.get_type()
            if first_token not in ("SELECT", "UNKNOWN"):
                if first_token in DISALLOWED_KEYWORDS:
                    issues.append(f"Non-SELECT statement type '{first_token}' is strictly forbidden.")
                    is_read_only = False

            for token in statement.flatten():
                token_val = token.value.upper()
                if token_val in DISALLOWED_KEYWORDS:
                    issues.append(f"Disallowed mutation keyword '{token_val}' detected.")
                    is_read_only = False

        # 4. Enforce starting with SELECT or WITH
        clean_upper = clean_sql.lstrip().upper()
        if not (clean_upper.startswith("SELECT") or clean_upper.startswith("WITH")):
            issues.append("Query must begin with SELECT or a common table expression (WITH).")
            is_read_only = False

        # Format SQL nicely
        formatted_sql = sqlparse.format(
            clean_sql,
            reindent=True,
            keyword_case="upper",
            identifier_case="lower",
        )

        is_valid = len(issues) == 0 and is_read_only
        safety_score = 1.0 if is_valid else max(0.0, 1.0 - (len(issues) * 0.35))

        return is_valid, is_read_only, safety_score, issues, formatted_sql

    @staticmethod
    def extract_ast_summary(sql_query: str) -> Dict[str, Any]:
        """Extract table names, columns, and operations using AST inspection."""
        parsed = sqlparse.parse(sql_query)
        if not parsed:
            return {"tables": [], "columns": [], "statement_type": "UNKNOWN"}

        stmt = parsed[0]
        tables = set()
        
        # Regex fallback for tables after FROM and JOIN
        from_matches = re.findall(r"\bFROM\s+([a-zA-Z0-9_]+)", sql_query, re.IGNORECASE)
        join_matches = re.findall(r"\bJOIN\s+([a-zA-Z0-9_]+)", sql_query, re.IGNORECASE)
        
        tables.update(from_matches)
        tables.update(join_matches)

        return {
            "tables": list(tables),
            "statement_type": stmt.get_type(),
            "has_where": "WHERE" in sql_query.upper(),
            "has_group_by": "GROUP BY" in sql_query.upper(),
            "has_order_by": "ORDER BY" in sql_query.upper(),
            "has_limit": "LIMIT" in sql_query.upper(),
        }


validator = SQLSecurityValidator()
