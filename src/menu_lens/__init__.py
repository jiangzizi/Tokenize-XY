"""
Menu Lens - 清华大学新雅书院公众号文章目录分析工具

提供对公众号文章metadata的分析功能，包括：
- 文章基本信息统计
- 时间分布分析
- 专辑/栏目分析
- 标题关键词提取
"""

from .loader import MenuLoader
from .analyzer import MenuAnalyzer
from .stats import MenuStats

__version__ = "0.1.0"
__all__ = ["MenuLoader", "MenuAnalyzer", "MenuStats"]
