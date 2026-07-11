# -*- coding: utf-8 -*-
"""单元测试共享配置。"""
import sys
from pathlib import Path

# 将项目根目录加入 sys.path，使 gui_app 等非包模块可被导入
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
