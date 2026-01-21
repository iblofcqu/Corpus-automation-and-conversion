"""
Service层测试
"""

import logging
import json
import os
import tempfile
from unittest.mock import MagicMock, patch

from django.conf import settings
from django.test import TestCase

from text_extraction.services import (
    FileStorageService,
    MinerUService,
    OntologyService,
)
from text_extraction.services.mineru_service import MinerUConversionResult

logger = logging.getLogger(__name__)


class FileStorageServiceTestCase(TestCase):
    """FileStorageService测试用例"""

    def test_get_full_path(self):
        """测试获取完整路径"""
        relative_path = "pdf/1/test.pdf"
        full_path = FileStorageService.get_full_path(relative_path)

        expected_path = os.path.join(settings.MEDIA_ROOT, relative_path)
        self.assertEqual(full_path, expected_path)

    def test_get_mineru_output_path(self):
        """测试生成MinerU输出路径"""
        path = FileStorageService.get_mineru_output_path(1, "test")

        self.assertIn("mineru", path)
        self.assertIn("1", path)
        self.assertTrue(path.endswith(".md"))

    def test_get_extraction_output_path(self):
        """测试生成本体论输出路径"""
        path = FileStorageService.get_extraction_output_path(1, "test")

        self.assertIn("extraction", path)
        self.assertIn("1", path)
        self.assertTrue(path.endswith(".json"))

    def test_ensure_dir(self):
        """测试确保目录存在"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "subdir", "test.txt")
            FileStorageService.ensure_dir(test_file)

            self.assertTrue(os.path.exists(os.path.dirname(test_file)))


class MinerUServiceTestCase(TestCase):
    """MinerUService测试用例"""

    def setUp(self):
        self.service = MinerUService()

    def test_convert_pdf_to_markdown_success(self):
        """测试PDF转Markdown成功"""
        result = self.service.convert_pdf_to_markdown(
            pdf_path=r"data\input\北京地铁17号线工程土建施工08合同段“5.14”.pdf",
            output_path=r"data\output",
            mode="ocr",
        )

        # 验证返回对象类型
        self.assertIsInstance(result, MinerUConversionResult)
        # 验证必需字段
        self.assertEqual(result.status, "success")
        self.assertIsNotNone(result.output_path)
        self.assertTrue(os.path.exists(result.output_path))
        self.assertTrue(result.output_path.endswith(".md"))
        # 验证模式字段
        self.assertEqual(result.mode, "ocr")
        # 验证路径包含正确的子目录
        self.assertIn("ocr", result.output_path)
        # 验证可选字段存在
        self.assertIsNotNone(result.backend)
        self.assertIsNotNone(result.version)
        logger.info("测试输出结果%s", result)


class OntologyServiceTestCase(TestCase):
    """OntologyService测试用例"""

    def setUp(self):
        self.service = OntologyService()

    def test_validate_ontology_file_success(self):
        """测试验证有效的本体论文件"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"categories": []}, f)
            temp_path = f.name

        try:
            result = self.service.validate_ontology_file(temp_path)
            self.assertTrue(result)
        finally:
            os.unlink(temp_path)

    def test_validate_ontology_file_invalid_format(self):
        """测试验证无效格式的本体论文件"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"wrong_key": []}, f)
            temp_path = f.name

        try:
            result = self.service.validate_ontology_file(temp_path)
            self.assertFalse(result)
        finally:
            os.unlink(temp_path)

    def test_validate_ontology_file_not_dict(self):
        """测试验证非字典格式的本体论文件"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump([], f)
            temp_path = f.name

        try:
            result = self.service.validate_ontology_file(temp_path)
            self.assertFalse(result)
        finally:
            os.unlink(temp_path)
