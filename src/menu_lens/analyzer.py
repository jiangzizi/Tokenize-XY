"""数据分析模块"""

import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

import jieba

from .loader import MenuLoader


class MenuAnalyzer:
    """文章目录分析器"""

    # 基础停用词
    STOP_WORDS = {
        # 标点符号
        "", " ", "丨", "·", "【", "】", "《", "》", "（", "）", "：", "、",
        "•", "「", "」", "『", "』", "\n", "\t", "—", "-", "~", "～",
        # 常用虚词
        "的", "了", "和", "是", "在", "有", "我", "都", "个", "与", "也", "对",
        "为", "能", "很", "可以", "就", "不", "会", "要", "没有", "我们的",
        "这", "上", "他", "而", "及", "或", "但是", "对于", "以及", "还是",
        "着", "到", "从", "等", "被", "把", "给", "让", "向", "往", "比",
        "之", "所", "来", "去", "过", "也", "还", "只", "最", "更", "太",
        "非常", "已经", "正在", "曾经", "现在", "当时", "这样", "那么",
        # 代词
        "我", "你", "他", "她", "它", "我们", "你们", "他们", "她们", "它们",
        "自己", "本人", "该", "此", "这", "那", "这些", "那些", "这里", "那里",
        # 机构名（过于常见）
        "清华", "大学", "新雅", "书院", "新雅书院", "清华大学", "清华新雅",
        # 数字相关
        "一", "二", "三", "四", "五", "六", "七", "八", "九", "十",
        "第", "期", "年", "月", "日", "号", "届",
        "零", "〇",
        # 其他无意义词
        "关于", "有关", "进行", "开展", "组织", "举办", "举行", "召开",
    }

    # 领域特定停用词（根据内容分析添加）
    DOMAIN_STOP_WORDS = {
        "通知", "公告", "公示", "启事", "说明", "简介",
        "报名", "申请", "提交", "截止", "时间", "地点",
        "欢迎", "参加", "参与", "出席", "莅临",
    }

    def __init__(self, data_path: str | Path):
        """
        初始化分析器

        Args:
            data_path: JSON文件路径
        """
        self.loader = MenuLoader(data_path)
        self.data = self.loader.load_with_parsed_time()

    def analyze_titles(self, top_n: int = 20) -> dict[str, Any]:
        """
        分析标题特征

        Returns:
            包含标题统计信息的字典
        """
        titles = [item.get("title", "") for item in self.data]

        # 标题长度分布
        lengths = [len(t) for t in titles]
        avg_length = sum(lengths) / len(lengths) if lengths else 0

        # 提取关键词（简单分词）
        all_words = []
        for title in titles:
            words = self._extract_words(title)
            all_words.extend(words)

        word_freq = Counter(all_words)

        return {
            "total_count": len(titles),
            "length_stats": {
                "min": min(lengths) if lengths else 0,
                "max": max(lengths) if lengths else 0,
                "avg": round(avg_length, 2),
                "distribution": self._distribution(lengths, bins=[0, 10, 20, 30, 50, 100]),
            },
            "top_keywords": word_freq.most_common(top_n),
            "contains_series": len([t for t in titles if "第" in t and "期" in t]),
        }

    def analyze_digests(self, top_n: int = 20) -> dict[str, Any]:
        """
        分析摘要特征

        Returns:
            包含摘要统计信息的字典
        """
        digests = [item.get("digest", "") for item in self.data if item.get("digest")]

        if not digests:
            return {"total_count": 0, "has_digest_ratio": 0}

        lengths = [len(d) for d in digests]
        avg_length = sum(lengths) / len(lengths)

        # 提取关键词
        all_words = []
        for digest in digests:
            words = self._extract_words(digest)
            all_words.extend(words)

        word_freq = Counter(all_words)

        return {
            "total_count": len(digests),
            "has_digest_ratio": round(len(digests) / len(self.data), 2),
            "length_stats": {
                "min": min(lengths),
                "max": max(lengths),
                "avg": round(avg_length, 2),
            },
            "top_keywords": word_freq.most_common(top_n),
        }

    def analyze_time_distribution(self) -> dict[str, Any]:
        """
        分析发布时间分布

        Returns:
            时间分布统计
        """
        times = [item.get("parsed_create_time") for item in self.data if item.get("parsed_create_time")]

        if not times:
            return {}

        # 年份分布
        year_counts = Counter(t.year for t in times)

        # 月份分布
        month_counts = Counter(t.month for t in times)

        # 星期分布
        weekday_counts = Counter(t.weekday() for t in times)
        weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        weekday_dist = {weekday_names[k]: v for k, v in sorted(weekday_counts.items())}

        # 小时分布（发布时间偏好）
        hour_counts = Counter(t.hour for t in times)
        hour_dist = {f"{k:02d}:00": v for k, v in sorted(hour_counts.items())}

        # 时间跨度
        time_span = {
            "earliest": min(times).strftime("%Y-%m-%d %H:%M:%S"),
            "latest": max(times).strftime("%Y-%m-%d %H:%M:%S"),
            "span_days": (max(times) - min(times)).days,
        }

        return {
            "total_with_time": len(times),
            "year_distribution": dict(sorted(year_counts.items(), reverse=True)),
            "month_distribution": dict(sorted(month_counts.items())),
            "weekday_distribution": weekday_dist,
            "hour_distribution": hour_dist,
            "time_span": time_span,
        }

    def analyze_albums(self) -> dict[str, Any]:
        """
        分析专辑/栏目分布

        Returns:
            专辑统计信息
        """
        albums = self.loader.get_by_album()

        album_stats = []
        for album_name, items in albums.items():
            # 获取该专辑的时间跨度
            times = [
                datetime.fromtimestamp(item.get("create_time", 0))
                for item in items
                if item.get("create_time")
            ]

            stat = {
                "name": album_name,
                "article_count": len(items),
                "percentage": round(len(items) / len(self.data) * 100, 2),
            }

            if times:
                stat["time_span"] = {
                    "from": min(times).strftime("%Y-%m-%d"),
                    "to": max(times).strftime("%Y-%m-%d"),
                }

            album_stats.append(stat)

        # 按文章数排序
        album_stats.sort(key=lambda x: x["article_count"], reverse=True)

        return {
            "total_albums": len(albums),
            "uncategorized_count": len(albums.get("未分类", [])),
            "albums": album_stats,
        }

    def _extract_words(self, text: str, min_length: int = 2) -> list[str]:
        """
        使用jieba进行中文分词

        Args:
            text: 输入文本
            min_length: 最小词长度（过滤单字）

        Returns:
            分词结果列表
        """
        if not text:
            return []

        # 添加自定义词典（针对新雅书院的特定词汇）
        self._load_custom_dict()

        # 使用jieba分词（精确模式）
        words = jieba.lcut(text)

        filtered = []
        for word in words:
            word = word.strip()

            # 过滤空字符串
            if not word:
                continue

            # 过滤纯数字（年份、编号等）
            if re.match(r'^\d+$', word):
                continue

            # 过滤纯英文数字混合（如2022、3.14）
            if re.match(r'^[0-9\-\.:]+$', word):
                continue

            # 过滤长度不足的
            if len(word) < min_length:
                continue

            # 过滤停用词
            if word in self.STOP_WORDS or word in self.DOMAIN_STOP_WORDS:
                continue

            # 过滤纯标点
            if re.match(r'^[^\u4e00-\u9fa5a-zA-Z]+$', word):
                continue

            filtered.append(word)

        return filtered

    def _load_custom_dict(self) -> None:
        """加载自定义词典（只执行一次）"""
        if not hasattr(self, '_custom_dict_loaded'):
            # 添加一些新雅书院相关的专业词汇
            custom_words = [
                "新雅书院", "新雅", "通识教育", "通识", "书院制",
                "南十北", "惊鸿", "从游", "聚谈",
                "本科", "研究生", "博士", "硕士",
                "导师", "班主任", "辅导员", "教授",
                "人文", "社科", "科学", "工程",
                "跨学科", "交叉学科", "PPE", "CDIE",
            ]
            for word in custom_words:
                jieba.add_word(word, freq=1000)
            self._custom_dict_loaded = True

    def _distribution(self, values: list[int], bins: list[int]) -> dict[str, int]:
        """
        计算分布统计

        Args:
            values: 数值列表
            bins: 分箱边界

        Returns:
            分布字典
        """
        dist = {}
        for i in range(len(bins) - 1):
            low, high = bins[i], bins[i + 1]
            count = sum(1 for v in values if low <= v < high)
            dist[f"{low}-{high}"] = count

        # 处理超出最大边界的情况
        count = sum(1 for v in values if v >= bins[-1])
        if count > 0:
            dist[f">={bins[-1]}"] = count

        return dist

    def generate_report(self) -> dict[str, Any]:
        """
        生成完整分析报告

        Returns:
            包含所有分析结果的字典
        """
        return {
            "basic_info": {
                "total_articles": len(self.data),
                "data_source": str(self.loader.data_path),
            },
            "title_analysis": self.analyze_titles(),
            "digest_analysis": self.analyze_digests(),
            "time_analysis": self.analyze_time_distribution(),
            "album_analysis": self.analyze_albums(),
        }
