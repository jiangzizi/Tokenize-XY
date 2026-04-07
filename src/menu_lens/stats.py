"""统计报表生成模块"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .analyzer import MenuAnalyzer


class MenuStats:
    """菜单数据统计报表生成器"""

    def __init__(self, data_path: str | Path, output_dir: str | Path = "reports"):
        """
        初始化统计器

        Args:
            data_path: JSON文件路径
            output_dir: 报告输出目录
        """
        self.analyzer = MenuAnalyzer(data_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_text_report(self) -> str:
        """
        生成文本格式报告

        Returns:
            报告文本内容
        """
        report = self.analyzer.generate_report()

        lines = [
            "=" * 60,
            "清华大学新雅书院公众号文章目录分析报告",
            "=" * 60,
            "",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"数据源: {report['basic_info']['data_source']}",
            "",
            "一、基本信息",
            "-" * 40,
            f"文章总数: {report['basic_info']['total_articles']} 篇",
            "",
            "二、标题分析",
            "-" * 40,
            f"标题数量: {report['title_analysis']['total_count']}",
            f"平均长度: {report['title_analysis']['length_stats']['avg']} 字符",
            f"长度范围: {report['title_analysis']['length_stats']['min']} - {report['title_analysis']['length_stats']['max']}",
            f"系列文章: {report['title_analysis']['contains_series']} 篇",
            "",
            "标题长度分布:",
        ]

        for range_key, count in report['title_analysis']['length_stats']['distribution'].items():
            lines.append(f"  {range_key} 字符: {count} 篇")

        lines.extend([
            "",
            "标题高频关键词 Top 10:",
        ])
        for word, count in report['title_analysis']['top_keywords'][:10]:
            lines.append(f"  {word}: {count} 次")

        lines.extend([
            "",
            "三、摘要分析",
            "-" * 40,
            f"有摘要的文章: {report['digest_analysis']['total_count']} 篇",
            f"摘要覆盖率: {report['digest_analysis']['has_digest_ratio'] * 100:.0f}%",
        ])

        if report['digest_analysis']['total_count'] > 0:
            lines.extend([
                f"平均长度: {report['digest_analysis']['length_stats']['avg']} 字符",
                "",
                "摘要高频关键词 Top 10:",
            ])
            for word, count in report['digest_analysis']['top_keywords'][:10]:
                lines.append(f"  {word}: {count} 次")

        time_analysis = report['time_analysis']
        if time_analysis:
            lines.extend([
                "",
                "四、时间分布分析",
                "-" * 40,
                f"有效时间数据: {time_analysis['total_with_time']} 篇",
                f"最早文章: {time_analysis['time_span']['earliest']}",
                f"最新文章: {time_analysis['time_span']['latest']}",
                f"时间跨度: {time_analysis['time_span']['span_days']} 天",
                "",
                "年份分布:",
            ])
            for year, count in list(time_analysis['year_distribution'].items())[:5]:
                lines.append(f"  {year}年: {count} 篇")

            lines.extend([
                "",
                "星期分布:",
            ])
            for weekday, count in time_analysis['weekday_distribution'].items():
                lines.append(f"  {weekday}: {count} 篇")

        album_analysis = report['album_analysis']
        lines.extend([
            "",
            "五、专辑/栏目分析",
            "-" * 40,
            f"专辑总数: {album_analysis['total_albums']}",
            f"未分类文章: {album_analysis['uncategorized_count']} 篇",
            "",
            "专辑排行:",
        ])
        for album in album_analysis['albums'][:10]:
            time_info = ""
            if 'time_span' in album:
                time_info = f" [{album['time_span']['from']} ~ {album['time_span']['to']}]"
            lines.append(f"  {album['name']}: {album['article_count']} 篇 ({album['percentage']}%){time_info}")

        lines.extend([
            "",
            "=" * 60,
            "报告生成完毕",
            "=" * 60,
        ])

        return "\n".join(lines)

    def generate_json_report(self) -> dict[str, Any]:
        """
        生成JSON格式报告

        Returns:
            报告字典
        """
        return self.analyzer.generate_report()

    def save_reports(self, prefix: str = "menu_analysis") -> dict[str, Path]:
        """
        保存报告到文件

        Args:
            prefix: 文件名前缀

        Returns:
            保存的文件路径字典
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 保存文本报告
        text_path = self.output_dir / f"{prefix}_{timestamp}.txt"
        text_path.write_text(self.generate_text_report(), encoding="utf-8")

        # 保存JSON报告
        json_path = self.output_dir / f"{prefix}_{timestamp}.json"
        report = self.generate_json_report()
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        return {
            "text": text_path,
            "json": json_path,
        }

    def print_summary(self) -> None:
        """打印简要摘要到控制台"""
        report = self.analyzer.generate_report()

        print("\n" + "=" * 50)
        print("📊 新雅书院公众号文章目录摘要")
        print("=" * 50)
        print(f"\n总文章数: {report['basic_info']['total_articles']} 篇")
        print(f"专辑数: {report['album_analysis']['total_albums']} 个")

        print("\n📁 主要栏目:")
        for album in report['album_analysis']['albums'][:5]:
            print(f"  • {album['name']}: {album['article_count']} 篇")

        if report['time_analysis']:
            print(f"\n📅 时间跨度: {report['time_analysis']['time_span']['span_days']} 天")
            print(f"  从 {report['time_analysis']['time_span']['earliest'][:10]}")
            print(f"  到 {report['time_analysis']['time_span']['latest'][:10]}")

        print("\n" + "=" * 50)
