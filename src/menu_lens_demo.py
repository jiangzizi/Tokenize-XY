#!/usr/bin/env python3
"""
Menu Lens 演示脚本
使用 lite 数据展示分析功能
"""

import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent))

from menu_lens import MenuLoader, MenuAnalyzer, MenuStats


def main():
    # 数据路径
    data_path = Path(__file__).parent.parent / "data" / "official_account_menu_lite.json"

    print(f"加载数据: {data_path}")
    print("-" * 50)

    # 1. 使用 MenuLoader 加载数据
    loader = MenuLoader(data_path)
    print(f"✓ 文章总数: {len(loader)} 篇")

    # 2. 按专辑分组
    albums = loader.get_by_album()
    print(f"\n✓ 发现 {len(albums)} 个专辑/栏目:")
    for name, items in albums.items():
        print(f"  - {name}: {len(items)} 篇")

    # 3. 使用 MenuAnalyzer 进行分析
    print("\n" + "=" * 50)
    print("开始分析...")
    print("=" * 50)

    analyzer = MenuAnalyzer(data_path)

    # 标题分析
    title_stats = analyzer.analyze_titles(top_n=5)
    print(f"\n📌 标题统计:")
    print(f"  平均长度: {title_stats['length_stats']['avg']} 字符")
    print(f"  Top 5 关键词: {', '.join(w for w, _ in title_stats['top_keywords'])}")

    # 摘要分析
    digest_stats = analyzer.analyze_digests(top_n=5)
    print(f"\n📌 摘要统计:")
    print(f"  有摘要的文章: {digest_stats['total_count']} 篇")
    if digest_stats['total_count'] > 0:
        print(f"  平均长度: {digest_stats['length_stats']['avg']} 字符")

    # 时间分析
    time_stats = analyzer.analyze_time_distribution()
    if time_stats:
        print(f"\n📌 时间分布:")
        print(f"  时间跨度: {time_stats['time_span']['span_days']} 天")
        print(f"  最早: {time_stats['time_span']['earliest']}")
        print(f"  最新: {time_stats['time_span']['latest']}")

    # 4. 使用 MenuStats 生成完整报告
    print("\n" + "=" * 50)
    print("生成完整报告...")
    print("=" * 50)

    stats = MenuStats(data_path, output_dir="reports")
    stats.print_summary()

    # 保存报告
    saved = stats.save_reports(prefix="menu_lite_analysis")
    print(f"\n✓ 报告已保存:")
    for fmt, path in saved.items():
        print(f"  [{fmt}] {path}")


if __name__ == "__main__":
    main()
