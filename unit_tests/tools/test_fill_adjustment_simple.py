#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fill_adjustment_simple 工具脚本适配测试。"""

import sys
from pathlib import Path

import duckdb
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from tools import fill_adjustment_simple


@pytest.fixture
def new_schema_conn():
    """提供包含新版 stock_daily 表的内存 DuckDB。"""
    conn = duckdb.connect(':memory:')
    conn.execute("""
        CREATE TABLE stock_daily (
            stock_code VARCHAR,
            symbol_type VARCHAR DEFAULT 'stock',
            date DATE,
            period VARCHAR DEFAULT '1d',
            open DOUBLE,
            high DOUBLE,
            low DOUBLE,
            close DOUBLE,
            volume BIGINT,
            amount DOUBLE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (stock_code, date, period)
        )
    """)
    yield conn
    conn.close()


@pytest.fixture
def old_schema_conn():
    """提供包含旧版 stock_daily 表的内存 DuckDB。"""
    conn = duckdb.connect(':memory:')
    conn.execute("""
        CREATE TABLE stock_daily (
            stock_code VARCHAR,
            symbol_type VARCHAR DEFAULT 'stock',
            date DATE,
            period VARCHAR DEFAULT '1d',
            adjust_type VARCHAR DEFAULT 'none',
            open DOUBLE,
            high DOUBLE,
            low DOUBLE,
            close DOUBLE,
            volume BIGINT,
            amount DOUBLE,
            open_front DOUBLE,
            high_front DOUBLE,
            low_front DOUBLE,
            close_front DOUBLE,
            open_back DOUBLE,
            high_back DOUBLE,
            low_back DOUBLE,
            close_back DOUBLE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (stock_code, date, period, adjust_type)
        )
    """)
    yield conn
    conn.close()


class TestSchemaDetection:
    """测试 schema 检测辅助函数。"""

    def test_detects_new_schema_without_adjust_type(self, new_schema_conn):
        """新版 schema 应被识别为不需要复权填充。"""
        assert fill_adjustment_simple._is_old_schema(new_schema_conn) is False

    def test_detects_old_schema_with_adjust_type(self, old_schema_conn):
        """旧版 schema 应被识别为需要复权填充。"""
        assert fill_adjustment_simple._is_old_schema(old_schema_conn) is True


class TestStockListQuery:
    """测试获取股票列表的 SQL 兼容性。"""

    def test_stock_list_query_runs_on_new_schema(self, new_schema_conn):
        """不含 adjust_type 的查询应能在新版 schema 上运行。"""
        conn = new_schema_conn
        conn.execute("""
            INSERT INTO stock_daily (stock_code, date, period, open, high, low, close, volume, amount)
            VALUES ('000001.SZ', '2024-01-01', '1d', 10.0, 11.0, 9.0, 10.5, 1000, 10500.0)
        """)

        stocks = conn.execute("""
            SELECT DISTINCT stock_code
            FROM stock_daily
            ORDER BY stock_code
        """).fetchdf()['stock_code'].tolist()

        assert stocks == ['000001.SZ']

    def test_old_stock_list_query_fails_on_new_schema(self, new_schema_conn):
        """含 adjust_type 的旧查询在新版 schema 上应报错。"""
        with pytest.raises(Exception):
            new_schema_conn.execute("""
                SELECT DISTINCT stock_code
                FROM stock_daily
                WHERE adjust_type = 'none'
                ORDER BY stock_code
            """).fetchdf()
