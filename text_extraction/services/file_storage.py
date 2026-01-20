"""
文件存储服务 - 管理文件路径和目录
"""

import os
from pathlib import Path

from django.conf import settings


class FileStorageService:
    """文件存储服务"""

    @staticmethod
    def get_full_path(relative_path: str) -> str:
        """
        获取完整文件路径

        Args:
            relative_path: 相对于MEDIA_ROOT的路径

        Returns:
            完整文件路径
        """
        return os.path.join(settings.MEDIA_ROOT, relative_path)

    @staticmethod
    def ensure_dir(file_path: str) -> None:
        """
        确保文件所在目录存在

        Args:
            file_path: 文件完整路径
        """
        directory = os.path.dirname(file_path)
        os.makedirs(directory, exist_ok=True)

    @staticmethod
    def get_mineru_output_path(project_id: int, filename: str) -> str:
        """
        生成MinerU输出路径（Markdown文件）

        Args:
            project_id: 项目ID
            filename: 原始文件名（不含扩展名）

        Returns:
            相对路径
        """
        return os.path.join("mineru", str(project_id), f"{filename}.md")

    @staticmethod
    def get_extraction_output_path(project_id: int, filename: str) -> str:
        """
        生成本体论提取输出路径（JSON文件）

        Args:
            project_id: 项目ID
            filename: 原始文件名（不含扩展名）

        Returns:
            相对路径
        """
        return os.path.join("extraction", str(project_id), f"{filename}_ontology.json")

    @staticmethod
    def read_file(relative_path: str, encoding: str = "utf-8") -> str:
        """
        读取文件内容

        Args:
            relative_path: 相对路径
            encoding: 文件编码

        Returns:
            文件内容
        """
        full_path = FileStorageService.get_full_path(relative_path)
        with open(full_path, "r", encoding=encoding) as f:
            return f.read()

    @staticmethod
    def write_file(relative_path: str, content: str, encoding: str = "utf-8") -> None:
        """
        写入文件内容

        Args:
            relative_path: 相对路径
            content: 文件内容
            encoding: 文件编码
        """
        full_path = FileStorageService.get_full_path(relative_path)
        FileStorageService.ensure_dir(full_path)
        with open(full_path, "w", encoding=encoding) as f:
            f.write(content)
