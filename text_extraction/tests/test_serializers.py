"""
序列化器测试
"""

from io import BytesIO

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.exceptions import ValidationError

from text_extraction.models import File, Project
from text_extraction.serializers import (
    FileUploadSerializer,
    ProjectCreateSerializer,
    ProjectSerializer,
)


class ProjectSerializerTestCase(TestCase):
    """ProjectSerializer测试用例"""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser")
        self.project = Project.objects.create(name="测试项目", created_by=self.user)

    def test_serialize_project(self):
        """测试序列化项目"""
        serializer = ProjectSerializer(self.project)
        data = serializer.data

        self.assertEqual(data["name"], "测试项目")
        self.assertEqual(data["created_by"], self.user.id)
        self.assertEqual(data["created_by_username"], "testuser")
        self.assertIn("file_count", data)

    def test_file_count_in_serializer(self):
        """测试文件数量统计"""
        File.objects.create(
            project=self.project, filename="test1.pdf", pdf_path="pdf/1/test1.pdf"
        )
        File.objects.create(
            project=self.project, filename="test2.pdf", pdf_path="pdf/1/test2.pdf"
        )

        serializer = ProjectSerializer(self.project)
        self.assertEqual(serializer.data["file_count"], 2)


class FileUploadSerializerTestCase(TestCase):
    """FileUploadSerializer测试用例"""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser")
        self.project = Project.objects.create(name="测试项目", created_by=self.user)

    def test_validate_valid_pdf(self):
        """测试验证有效PDF文件"""
        pdf_content = b"%PDF-1.4 fake pdf content"
        pdf_file = SimpleUploadedFile("test.pdf", pdf_content, content_type="application/pdf")

        serializer = FileUploadSerializer(
            data={"project_id": self.project.id, "file": pdf_file}
        )

        self.assertTrue(serializer.is_valid())

    def test_validate_invalid_file_extension(self):
        """测试验证非PDF文件"""
        txt_file = SimpleUploadedFile("test.txt", b"text content", content_type="text/plain")

        serializer = FileUploadSerializer(
            data={"project_id": self.project.id, "file": txt_file}
        )

        self.assertFalse(serializer.is_valid())
        self.assertIn("file", serializer.errors)

    def test_validate_nonexistent_project(self):
        """测试验证不存在的项目"""
        pdf_file = SimpleUploadedFile("test.pdf", b"%PDF-1.4", content_type="application/pdf")

        serializer = FileUploadSerializer(data={"project_id": 99999, "file": pdf_file})

        self.assertFalse(serializer.is_valid())
        self.assertIn("project_id", serializer.errors)

    def test_validate_deleted_project(self):
        """测试验证已删除的项目"""
        self.project.is_deleted = True
        self.project.save()

        pdf_file = SimpleUploadedFile("test.pdf", b"%PDF-1.4", content_type="application/pdf")
        serializer = FileUploadSerializer(
            data={"project_id": self.project.id, "file": pdf_file}
        )

        self.assertFalse(serializer.is_valid())
