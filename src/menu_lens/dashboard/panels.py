"""面板组件 - 各个标签页的内容渲染"""

from abc import ABC, abstractmethod
from typing import Any

from rich.align import Align
from rich.bar import Bar
from rich.columns import Columns
from rich.console import Console, ConsoleOptions, RenderResult
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn
from rich.table import Table
from rich.text import Text
from rich.tree import Tree


class BasePanel(ABC):
    """面板基类"""

    def __init__(self, data: dict[str, Any]):
        self.data = data

    @property
    @abstractmethod
    def title(self) -> str:
        """面板标题"""
        pass

    @abstractmethod
    def render(self) -> Panel:
        """渲染面板内容"""
        pass

    def _make_bar_chart(self, data: dict, title: str, unit: str = "") -> Table:
        """创建条形图"""
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("label", style="cyan", justify="right", width=12)
        table.add_column("bar", style="green")
        table.add_column("value", style="white", justify="right", width=8)

        max_val = max(data.values()) if data else 1
        for label, value in data.items():
            bar_width = int((value / max_val) * 30)
            bar = "█" * bar_width
            table.add_row(str(label), f"[green]{bar}[/]", f"{value}{unit}")

        return table


class OverviewPanel(BasePanel):
    """概览面板"""

    @property
    def title(self) -> str:
        return "📊 概览"

    def render(self) -> Panel:
        """渲染概览内容"""
        basic = self.data.get("basic_info", {})
        title_stats = self.data.get("title_analysis", {})
        time_stats = self.data.get("time_analysis", {})

        # 创建网格布局
        grid = Table.grid(expand=True)
        grid.add_column(justify="center", ratio=1)
        grid.add_column(justify="center", ratio=1)
        grid.add_column(justify="center", ratio=1)
        grid.add_column(justify="center", ratio=1)

        # 大数字卡片
        total = basic.get("total_articles", 0)
        albums = self.data.get("album_analysis", {}).get("total_albums", 0)
        series = title_stats.get("contains_series", 0)
        span_days = time_stats.get("time_span", {}).get("span_days", 0)

        grid.add_row(
            self._big_card("文章总数", f"{total}", "blue"),
            self._big_card("栏目数量", f"{albums}", "green"),
            self._big_card("系列文章", f"{series}", "yellow"),
            self._big_card("运营天数", f"{span_days}", "magenta"),
        )

        # 详细信息表
        info_table = Table(show_header=False, box=None, padding=(0, 2))
        info_table.add_column("key", style="dim", justify="right", width=15)
        info_table.add_column("value", style="white")

        if time_stats:
            time_span = time_stats.get("time_span", {})
            info_table.add_row("最早文章:", time_span.get("earliest", "N/A"))
            info_table.add_row("最新文章:", time_span.get("latest", "N/A"))

        digest_stats = self.data.get("digest_analysis", {})
        if digest_stats:
            coverage = digest_stats.get("has_digest_ratio", 0) * 100
            info_table.add_row("摘要覆盖率:", f"{coverage:.0f}%")
            info_table.add_row("平均摘要长度:", f"{digest_stats.get('length_stats', {}).get('avg', 0):.0f} 字符")

        title_len = title_stats.get("length_stats", {})
        info_table.add_row("平均标题长度:", f"{title_len.get('avg', 0):.1f} 字符")

        # 组合布局
        main_layout = Table.grid(expand=True)
        main_layout.add_column()
        main_layout.add_row(grid)
        main_layout.add_row("")
        main_layout.add_row(info_table)

        return Panel(main_layout, title=self.title, border_style="blue")

    def _big_card(self, label: str, value: str, color: str) -> Panel:
        """创建大数字卡片"""
        content = Text.assemble(
            (value, f"bold {color}"),
            "\n",
            (label, "dim"),
        )
        return Panel(Align.center(content), border_style=color, width=20)


class TimelinePanel(BasePanel):
    """时间线面板"""

    @property
    def title(self) -> str:
        return "📅 时间分布"

    def render(self) -> Panel:
        """渲染时间分布"""
        time_stats = self.data.get("time_analysis", {})
        if not time_stats:
            return Panel("暂无时间数据", title=self.title)

        # 主布局 - 左右分栏
        layout = Table.grid(expand=True)
        layout.add_column(ratio=1)
        layout.add_column(ratio=1)

        # 左栏：年份分布 + 月份分布
        left_col = Table.grid(expand=True)
        left_col.add_column()

        # 年份分布
        year_data = time_stats.get("year_distribution", {})
        if year_data:
            year_table = self._make_bar_chart(year_data, "年份分布", "篇")
            left_col.add_row(Panel(year_table, title="[cyan]年份分布", border_style="cyan"))

        left_col.add_row("")

        # 月份分布
        month_data = time_stats.get("month_distribution", {})
        if month_data:
            month_display = {f"{k}月": v for k, v in sorted(month_data.items())}
            month_table = self._make_bar_chart(month_display, "月份分布", "篇")
            left_col.add_row(Panel(month_table, title="[green]月份分布", border_style="green"))

        # 右栏：星期 + 小时分布
        right_col = Table.grid(expand=True)
        right_col.add_column()

        # 星期分布
        weekday_data = time_stats.get("weekday_distribution", {})
        if weekday_data:
            weekday_table = self._make_bar_chart(weekday_data, "星期分布", "篇")
            right_col.add_row(Panel(weekday_table, title="[yellow]星期分布", border_style="yellow"))

        right_col.add_row("")

        # 小时分布 - 简化为时段
        hour_data = time_stats.get("hour_distribution", {})
        if hour_data:
            # 聚类为时段
            periods = {
                "早晨 (6-9)": sum(v for k, v in hour_data.items() if 6 <= int(k[:2]) < 9),
                "上午 (9-12)": sum(v for k, v in hour_data.items() if 9 <= int(k[:2]) < 12),
                "中午 (12-14)": sum(v for k, v in hour_data.items() if 12 <= int(k[:2]) < 14),
                "下午 (14-18)": sum(v for k, v in hour_data.items() if 14 <= int(k[:2]) < 18),
                "晚上 (18-22)": sum(v for k, v in hour_data.items() if 18 <= int(k[:2]) < 22),
                "深夜 (22-6)": sum(v for k, v in hour_data.items() if int(k[:2]) >= 22 or int(k[:2]) < 6),
            }
            period_table = self._make_bar_chart(periods, "发布时段", "篇")
            right_col.add_row(Panel(period_table, title="[magenta]时段分布", border_style="magenta"))

        layout.add_row(left_col, right_col)

        return Panel(layout, title=self.title, border_style="cyan")


class KeywordsPanel(BasePanel):
    """关键词面板"""

    @property
    def title(self) -> str:
        return "🔑 关键词分析"

    def render(self) -> Panel:
        """渲染关键词分析"""
        layout = Table.grid(expand=True)
        layout.add_column(ratio=1)
        layout.add_column(ratio=1)

        # 标题关键词
        title_stats = self.data.get("title_analysis", {})
        title_keywords = title_stats.get("top_keywords", [])
        if title_keywords:
            title_table = self._keyword_table(title_keywords[:15], "cyan")
            layout.add_row(
                Panel(title_table, title="[cyan]标题高频词 Top 15", border_style="cyan")
            )

        # 摘要关键词
        digest_stats = self.data.get("digest_analysis", {})
        digest_keywords = digest_stats.get("top_keywords", [])
        if digest_keywords:
            digest_table = self._keyword_table(digest_keywords[:15], "green")
            layout.add_row(
                Panel(digest_table, title="[green]摘要高频词 Top 15", border_style="green")
            )

        return Panel(layout, title=self.title, border_style="green")

    def _keyword_table(self, keywords: list[tuple[str, int]], color: str) -> Table:
        """创建关键词表格"""
        table = Table(show_header=False, box=None, expand=True)
        table.add_column("rank", style="dim", width=4)
        table.add_column("word", style=color, min_width=10)
        table.add_column("count", style="white", justify="right", width=6)
        table.add_column("bar", width=15)

        max_count = max(c for _, c in keywords) if keywords else 1
        for i, (word, count) in enumerate(keywords, 1):
            bar_len = int((count / max_count) * 12)
            bar = "█" * bar_len
            # 截断长词避免换行
            display_word = word[:12] + "..." if len(word) > 12 else word
            table.add_row(f"{i}.", display_word, str(count), f"[{color}]{bar}[/]")

        return table


class AlbumsPanel(BasePanel):
    """专辑/栏目面板"""

    @property
    def title(self) -> str:
        return "📁 栏目分析"

    def render(self) -> Panel:
        """渲染栏目分析"""
        album_stats = self.data.get("album_analysis", {})
        albums = album_stats.get("albums", [])

        if not albums:
            return Panel("暂无栏目数据", title=self.title)

        # 栏目列表（排除未分类）
        table = Table(expand=True)
        table.add_column("排名", justify="right", style="dim", width=4)
        table.add_column("栏目名称", style="cyan")
        table.add_column("文章数", justify="right", style="green")
        table.add_column("占比", justify="right", style="yellow")
        table.add_column("时间跨度", style="dim")
        table.add_column("趋势图", width=20)

        max_count = max(a["article_count"] for a in albums[:20]) if albums else 1

        for i, album in enumerate(albums[:20], 1):
            name = album["name"]
            count = album["article_count"]
            pct = album["percentage"]
            time_span = album.get("time_span", {})
            time_range = ""
            if time_span:
                time_range = f"{time_span.get('from', '')} ~ {time_span.get('to', '')}"

            # 条形图
            bar_len = int((count / max_count) * 15)
            bar = "█" * bar_len

            table.add_row(
                str(i),
                name[:30] + "..." if len(name) > 30 else name,
                str(count),
                f"{pct}%",
                time_range,
                f"[green]{bar}[/]"
            )

        # 统计摘要
        summary = Text.assemble(
            ("栏目总数: ", "dim"),
            (str(album_stats.get("total_albums", 0)), "bold cyan"),
            "  |  ",
            ("未分类: ", "dim"),
            (str(album_stats.get("uncategorized_count", 0)), "bold yellow"),
        )

        layout = Table.grid(expand=True)
        layout.add_column()
        layout.add_row(Align.center(summary))
        layout.add_row("")
        layout.add_row(table)

        return Panel(layout, title=self.title, border_style="yellow")
