"""Validation package for SQL and request validators."""

from .query_validator import is_safe_select_query, sanitize_sql_output

__all__ = ["is_safe_select_query", "sanitize_sql_output"]
