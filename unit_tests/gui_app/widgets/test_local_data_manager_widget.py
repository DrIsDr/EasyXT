#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""LocalDataManagerWidget 批量写入异常处理回归测试。"""

import inspect
import re

import pytest

from gui_app.widgets.local_data_manager_widget import DataDownloadThread


class TestDataDownloadThreadBatchFallback:
    """测试批量写入失败后的分批回退逻辑。"""

    def test_daily_is_table_initialized_before_batch_write(self):
        """daily_is_table 必须在批量写入 try 块之前初始化，避免 UnboundLocalError。"""
        source = inspect.getsource(DataDownloadThread._update_data)
        # 定位 "if update_data:" 之后、"try:" 之前存在 daily_is_table = False
        match = re.search(
            r"if update_data:\s*\n"
            r"(?:\s*#.*\n)*"
            r"\s*(daily_is_table\s*=\s*False)\s*\n"
            r"(?:\s*#.*\n)*"
            r"\s*try:",
            source,
        )
        assert match is not None, "daily_is_table 应在 try 块之前初始化为 False"

    def test_stock_data_fallback_sql_does_not_reference_adjust_type(self):
        """stock_data 分批回退 INSERT 不应引用已移除的 adjust_type 列。"""
        source = inspect.getsource(DataDownloadThread._update_data)
        # 定位 "尝试分批写入" 之后的 else 分支
        fallback_start = source.find('尝试分批写入')
        assert fallback_start != -1
        fallback_section = source[fallback_start:]

        match = re.search(
            r'INSERT OR IGNORE INTO stock_data \((.*?)\)\s*SELECT\s*(.*?)\s*FROM temp_batch',
            fallback_section,
            re.DOTALL,
        )
        assert match is not None, "应存在 stock_data 分批回退 INSERT"
        insert_cols = match.group(1)
        select_cols = match.group(2)
        assert 'adjust_type' not in insert_cols, "INSERT 列不应包含 adjust_type"
        assert 'adjust_type' not in select_cols, "SELECT 列不应包含 adjust_type"
