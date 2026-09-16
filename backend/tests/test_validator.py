import pytest
from app.ml.validator import validator


def test_valid_select_query():
    sql = "SELECT customer_id, first_name, last_name FROM customers WHERE country = 'USA';"
    is_valid, is_read_only, score, issues, formatted = validator.validate_and_sanitize(sql)
    assert is_valid is True
    assert is_read_only is True
    assert score == 1.0
    assert len(issues) == 0
    assert "SELECT" in formatted


def test_block_destructive_drop_table():
    sql = "DROP TABLE customers;"
    is_valid, is_read_only, score, issues, _ = validator.validate_and_sanitize(sql)
    assert is_valid is False
    assert is_read_only is False
    assert any("DROP" in issue or "Non-SELECT" in issue for issue in issues)


def test_block_destructive_delete():
    sql = "DELETE FROM orders WHERE order_id = 1;"
    is_valid, is_read_only, score, issues, _ = validator.validate_and_sanitize(sql)
    assert is_valid is False
    assert is_read_only is False


def test_block_multi_statement_injection():
    sql = "SELECT * FROM products; DROP TABLE customers;"
    is_valid, is_read_only, score, issues, _ = validator.validate_and_sanitize(sql)
    assert is_valid is False
    assert any("Multiple SQL statements" in issue or "DROP" in issue for issue in issues)


def test_block_alter_table():
    sql = "ALTER TABLE users ADD COLUMN is_hacked BOOLEAN;"
    is_valid, is_read_only, score, issues, _ = validator.validate_and_sanitize(sql)
    assert is_valid is False
    assert is_read_only is False
