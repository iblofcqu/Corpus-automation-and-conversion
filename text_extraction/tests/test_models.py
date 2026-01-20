"""
数据模型测试
"""

from django.contrib.auth.models import User
from django.test import TestCase

from text_extraction.models import File, Project


class ProjectModelTestCase(TestCase):
    """Project模型测试用例"""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser")

    def test_create_project(self):
        """测试创建项目"""
        project = Project.objects.create(
            name="测试项目", created_by=self.user, ontology_path="ontology/test.json"
        )

        self.assertEqual(project.name, "测试项目")
        self.assertEqual(project.created_by, self.user)
        self.assertFalse(project.is_deleted)
        self.assertIsNotNone(project.created_at)
        self.assertIsNotNone(project.updated_at)

    def test_soft_delete_project(self):
        """测试软删除项目"""
        project = Project.objects.create(name="待删除项目", created_by=self.user)

        project.is_deleted = True
        project.save()

        self.assertTrue(project.is_deleted)
        self.assertTrue(Project.objects.filter(id=project.id).exists())

    def test_project_string_representation(self):
        """测试项目字符串表示"""
        project = Project.objects.create(name="显示名称", created_by=self.user)

        self.assertEqual(str(project), "显示名称")


class FileModelTestCase(TestCase):
    """File模型测试用例"""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser")
        self.project = Project.objects.create(name="测试项目", created_by=self.user)

    def test_create_file(self):
        """测试创建文件"""
        file_obj = File.objects.create(
            project=self.project,
            filename="test.pdf",
            pdf_path="pdf/1/test.pdf",
            status=File.Status.PENDING,
        )

        self.assertEqual(file_obj.filename, "test.pdf")
        self.assertEqual(file_obj.project, self.project)
        self.assertEqual(file_obj.status, File.Status.PENDING)
        self.assertIsNone(file_obj.task_id)

    def test_file_status_choices(self):
        """测试文件状态选项"""
        file_obj = File.objects.create(
            project=self.project, filename="test.pdf", pdf_path="pdf/1/test.pdf"
        )

        # 测试所有状态
        for status in [
            File.Status.PENDING,
            File.Status.PROCESSING,
            File.Status.COMPLETED,
            File.Status.FAILED,
        ]:
            file_obj.status = status
            file_obj.save()
            file_obj.refresh_from_db()
            self.assertEqual(file_obj.status, status)

    def test_file_with_error_message(self):
        """测试带错误信息的文件"""
        file_obj = File.objects.create(
            project=self.project,
            filename="error.pdf",
            pdf_path="pdf/1/error.pdf",
            status=File.Status.FAILED,
            error_message="处理失败",
        )

        self.assertEqual(file_obj.status, File.Status.FAILED)
        self.assertEqual(file_obj.error_message, "处理失败")

    def test_file_string_representation(self):
        """测试文件字符串表示"""
        file_obj = File.objects.create(
            project=self.project,
            filename="display.pdf",
            pdf_path="pdf/1/display.pdf",
            status=File.Status.COMPLETED,
        )

        self.assertIn("display.pdf", str(file_obj))
        self.assertIn("已完成", str(file_obj))
