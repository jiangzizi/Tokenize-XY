"""Dashboard 主应用"""

import sys
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align

from ..analyzer import MenuAnalyzer
from .panels import AlbumsPanel, KeywordsPanel, OverviewPanel, TimelinePanel


class MenuDashboard:
    """新雅书院 Menu Lens 交互式面板"""

    TABS = ["overview", "timeline", "keywords", "albums"]
    TAB_NAMES = {
        "overview": "📊 概览",
        "timeline": "📅 时间线",
        "keywords": "🔑 关键词",
        "albums": "📁 栏目",
    }

    def __init__(self, data_path: str | Path):
        self.data_path = Path(data_path)
        self.console = Console()
        self.data: dict[str, Any] = {}
        self.current_tab = "overview"
        self.running = True
        self._panels: dict[str, Any] = {}

    def load_data(self) -> None:
        """加载分析数据"""
        self.console.print("[dim]正在加载数据...[/]")
        analyzer = MenuAnalyzer(self.data_path)
        self.data = analyzer.generate_report()
        self.console.print(f"[green]✓[/] 已加载 {self.data['basic_info']['total_articles']} 篇文章")

    def _get_panel(self, tab: str) -> Panel:
        """获取指定标签页的面板"""
        if tab not in self._panels:
            panel_class = {
                "overview": OverviewPanel,
                "timeline": TimelinePanel,
                "keywords": KeywordsPanel,
                "albums": AlbumsPanel,
            }.get(tab)
            if panel_class:
                self._panels[tab] = panel_class(self.data)
        return self._panels[tab].render() if tab in self._panels else Panel("加载中...")

    def _render_header(self) -> Text:
        """渲染顶部标题栏"""
        return Text.assemble(
            ("╭─ ", "dim"),
            ("新雅书院公众号文章目录分析", "bold cyan"),
            (" ─╮", "dim"),
        )

    def _render_tabs(self) -> Panel:
        """渲染标签栏"""
        tab_texts = []
        for tab in self.TABS:
            name = self.TAB_NAMES[tab]
            if tab == self.current_tab:
                tab_texts.append(f"[bold white on blue] {name} ")
            else:
                tab_texts.append(f"[dim] {name} ")

        content = Text(" │ ").join([Text.from_markup(t) for t in tab_texts])
        return Align.center(content)

    def _render_footer(self) -> Text:
        """渲染底部帮助栏"""
        return Text.from_markup(
            "[dim][Tab] 下一标签"
            "  |  [Shift+Tab] 上一标签"
            "  |  [←/→] 切换"
            "  |  [1-4] 快速跳转"
            "  |  [a] 全部显示"
            "  |  [q] 退出[/]"
        )

    def _render(self) -> Table:
        """渲染完整界面"""
        main_content = self._get_panel(self.current_tab)

        layout = Table.grid(expand=True)
        layout.add_column()
        layout.add_row(Align.center(self._render_header()))
        layout.add_row("")
        layout.add_row(self._render_tabs())
        layout.add_row(main_content)
        layout.add_row(self._render_footer())

        return layout

    def run(self) -> None:
        """运行交互式面板"""
        import tty
        import termios
        import select

        self.load_data()

        old_settings = termios.tcgetattr(sys.stdin)
        try:
            tty.setcbreak(sys.stdin.fileno())

            with Live(self._render(), console=self.console, refresh_per_second=10, screen=True) as live:
                while self.running:
                    if select.select([sys.stdin], [], [], 0.1)[0]:
                        key = sys.stdin.read(1)

                        if key == 'q':
                            break
                        elif key == '\t':  # Tab 键 - 下一标签
                            idx = self.TABS.index(self.current_tab)
                            self.current_tab = self.TABS[(idx + 1) % len(self.TABS)]
                        elif key == '\x1b':  # ESC 序列 (方向键/Shift+Tab)
                            # 读取后续字符
                            seq = sys.stdin.read(2) if select.select([sys.stdin], [], [], 0.01)[0] else ''
                            if seq == '[Z':  # Shift+Tab
                                idx = self.TABS.index(self.current_tab)
                                self.current_tab = self.TABS[(idx - 1) % len(self.TABS)]
                            elif seq == '[C':  # 右方向键
                                idx = self.TABS.index(self.current_tab)
                                self.current_tab = self.TABS[(idx + 1) % len(self.TABS)]
                            elif seq == '[D':  # 左方向键
                                idx = self.TABS.index(self.current_tab)
                                self.current_tab = self.TABS[(idx - 1) % len(self.TABS)]
                        elif key in ('n', 'C'):
                            idx = self.TABS.index(self.current_tab)
                            self.current_tab = self.TABS[(idx + 1) % len(self.TABS)]
                        elif key in ('p', 'D'):
                            idx = self.TABS.index(self.current_tab)
                            self.current_tab = self.TABS[(idx - 1) % len(self.TABS)]
                        elif key in '1234':
                            self.current_tab = self.TABS[int(key) - 1]
                        elif key == 'a':
                            live.stop()
                            self.console.clear()
                            self.render_static()
                            return

                        live.update(self._render())

        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

    def render_static(self) -> None:
        """渲染静态输出"""
        if not self.data:
            self.load_data()
        for t in self.TABS:
            self.console.print(self._get_panel(t))
            self.console.print()


def main():
    """CLI入口"""
    import argparse
    import sys
    import os

    parser = argparse.ArgumentParser(description="新雅书院 Menu Lens 统计面板")
    parser.add_argument("--data", "-d", type=str, default="data/official_account_menu.json",
                        help="数据文件路径")
    parser.add_argument("--static", "-s", action="store_true",
                        help="静态模式")
    parser.add_argument("--lite", "-l", action="store_true",
                        help="使用轻量版数据")

    args = parser.parse_args()

    if args.lite:
        data_path = Path("data/official_account_menu_lite.json")
    else:
        data_path = Path(args.data)

    if not data_path.exists():
        print(f"错误: 数据文件不存在: {data_path}")
        sys.exit(1)

    dashboard = MenuDashboard(data_path)

    # 检测是否在交互式终端
    is_tty = sys.stdin.isatty() and sys.stdout.isatty()

    if args.static or not is_tty:
        if not is_tty and not args.static:
            print("[dim]非交互式环境，自动切换到静态模式[/]\n")
        dashboard.render_static()
    else:
        try:
            dashboard.run()
        except KeyboardInterrupt:
            print("\n再见!")


if __name__ == "__main__":
    main()
