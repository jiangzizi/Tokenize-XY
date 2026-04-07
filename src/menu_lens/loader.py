"""数据加载模块"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class MenuLoader:
    """加载公众号文章目录数据"""

    def __init__(self, data_path: str | Path):
        """
        初始化加载器

        Args:
            data_path: JSON文件路径
        """
        self.data_path = Path(data_path)
        self.raw_data: list[dict] = []
        self._validate_path()

    def _validate_path(self) -> None:
        """验证数据文件路径"""
        if not self.data_path.exists():
            raise FileNotFoundError(f"数据文件不存在: {self.data_path}")
        if not self.data_path.suffix == ".json":
            raise ValueError(f"数据文件必须是JSON格式: {self.data_path}")

    def load(self) -> list[dict]:
        """
        加载并解析JSON数据

        Returns:
            文章列表
        """
        with open(self.data_path, "r", encoding="utf-8") as f:
            self.raw_data = json.load(f)
        return self.raw_data

    def load_with_parsed_time(self) -> list[dict]:
        """
        加载数据并解析时间戳为datetime对象

        Returns:
            添加了parsed_create_time和parsed_update_time的文章列表
        """
        data = self.load()
        for item in data:
            # 转换Unix时间戳为datetime
            create_ts = item.get("create_time")
            update_ts = item.get("update_time")

            if create_ts:
                item["parsed_create_time"] = datetime.fromtimestamp(create_ts)
            if update_ts:
                item["parsed_update_time"] = datetime.fromtimestamp(update_ts)

        return data

    def get_by_album(self, album_title: str | None = None) -> dict[str, list[dict]]:
        """
        按专辑分组获取文章

        Args:
            album_title: 专辑标题，为None则返回所有分组

        Returns:
            按专辑分组的字典
        """
        data = self.load()
        albums: dict[str, list[dict]] = {}

        for item in data:
            album_info = item.get("appmsg_album_infos", [])
            if album_info:
                album_name = album_info[0].get("title", "未分类")
            else:
                album_name = "未分类"

            if album_name not in albums:
                albums[album_name] = []
            albums[album_name].append(item)

        if album_title:
            return {album_title: albums.get(album_title, [])}
        return albums

    def filter_by_time_range(
        self, start: datetime | None = None, end: datetime | None = None
    ) -> list[dict]:
        """
        按时间范围筛选文章

        Args:
            start: 开始时间
            end: 结束时间

        Returns:
            符合条件的文章列表
        """
        data = self.load_with_parsed_time()
        result = []

        for item in data:
            create_time = item.get("parsed_create_time")
            if not create_time:
                continue

            if start and create_time < start:
                continue
            if end and create_time > end:
                continue

            result.append(item)

        return result

    def __len__(self) -> int:
        """返回文章总数"""
        if not self.raw_data:
            self.load()
        return len(self.raw_data)
