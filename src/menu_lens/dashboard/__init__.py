"""
Menu Lens Dashboard - 现代化 CLI 统计面板

基于 rich 和 textual 构建的交互式数据可视化面板
"""

from .app import MenuDashboard
from .panels import OverviewPanel, TimelinePanel, KeywordsPanel, AlbumsPanel

__all__ = ["MenuDashboard", "OverviewPanel", "TimelinePanel", "KeywordsPanel", "AlbumsPanel"]
