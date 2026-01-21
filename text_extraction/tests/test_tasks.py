"""
Celery任务测试
"""

from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.test import TestCase

from text_extraction.models import File, Project
from text_extraction.tasks import process_pdf_task


class ProcessPdfTaskTestCase(TestCase):
    """process_pdf_task测试用例"""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser")
        self.project = Project.objects.create(
            name="测试项目",
            created_by=self.user,
            ontology_path="ontology/default_ontology.json",
        )
        self.file_obj = File.objects.create(
            project=self.project, filename="test.pdf", pdf_path="pdf/1/test.pdf"
        )

    @patch("text_extraction.tasks.os.path.exists")
    @patch("text_extraction.tasks.os.path.relpath")
    @patch("text_extraction.tasks.OntologyService")
    @patch("text_extraction.tasks.MinerUService")
    def test_process_pdf_task_success(
        self, mock_mineru, mock_ontology, mock_relpath, mock_exists
    ):
        """测试任务成功执行"""
        # Mock os.path.exists 总是返回 True
        mock_exists.return_value = True

        # Mock os.path.relpath 返回相对路径
        mock_relpath.side_effect = lambda path, start: str(path).replace(
            str(start) + "/", ""
        ).replace(str(start) + "\\", "")

        # Mock MinerU服务 - 模拟 MinerUConversionResult 对象
        mock_mineru_instance = MagicMock()
        mock_result = MagicMock()
        mock_result.status = "success"
        mock_result.output_path = "/path/to/output.md"
        mock_result.mode = "auto"
        mock_result.backend = "test_backend"
        mock_result.version = "1.0.0"
        # 支持字典式访问（tasks.py 中使用 mineru_result["output_path"]）
        mock_result.__getitem__ = lambda self, key: getattr(self, key)
        mock_mineru_instance.convert_pdf_to_markdown.return_value = mock_result
        mock_mineru.return_value = mock_mineru_instance

        # Mock Ontology服务
        mock_ontology_instance = MagicMock()
        mock_ontology_instance.extract_information.return_value = {
            "status": "success",
            "output_path": "/path/to/output.json",
            "document": "/path/to/input.md",
        }
        mock_ontology.return_value = mock_ontology_instance

        # 执行任务（同步调用，不使用delay）
        result = process_pdf_task(self.file_obj.id)

        # 验证结果
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["file_id"], self.file_obj.id)

        # 验证文件状态更新
        self.file_obj.refresh_from_db()
        self.assertEqual(self.file_obj.status, File.Status.COMPLETED)
        self.assertIsNotNone(self.file_obj.mineru_output_path)
        self.assertIsNotNone(self.file_obj.extraction_output_path)

    def test_process_pdf_task_file_not_exist(self):
        """测试处理不存在的文件"""
        result = process_pdf_task(99999)

        self.assertEqual(result["status"], "error")
        self.assertIn("message", result)

    @patch("text_extraction.tasks.MinerUService")
    def test_process_pdf_task_mineru_failure(self, mock_mineru):
        """测试MinerU服务失败"""
        mock_mineru_instance = MagicMock()
        mock_mineru_instance.convert_pdf_to_markdown.side_effect = Exception(
            "MinerU failed"
        )
        mock_mineru.return_value = mock_mineru_instance

        result = process_pdf_task(self.file_obj.id)

        self.assertEqual(result["status"], "error")

        # 验证文件状态更新为失败
        self.file_obj.refresh_from_db()
        self.assertEqual(self.file_obj.status, File.Status.FAILED)
        self.assertIsNotNone(self.file_obj.error_message)
