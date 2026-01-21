"""
API视图测试
"""

from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APITestCase

from text_extraction.models import File, Project


class ProjectViewSetTestCase(APITestCase):
    """ProjectViewSet测试用例"""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser")
        self.client.force_authenticate(user=self.user)

    def test_list_projects(self):
        """测试获取项目列表"""
        Project.objects.create(name="项目1", created_by=self.user)
        Project.objects.create(name="项目2", created_by=self.user)

        response = self.client.get("/api/v1/projects/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_create_project(self):
        """测试创建项目"""
        data = {"name": "新项目"}
        response = self.client.post("/api/v1/projects/", data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "新项目")
        self.assertTrue(Project.objects.filter(name="新项目").exists())

    def test_retrieve_project(self):
        """测试获取项目详情"""
        project = Project.objects.create(name="测试项目", created_by=self.user)

        response = self.client.get(f"/api/v1/projects/{project.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "测试项目")

    def test_delete_project_soft_delete(self):
        """测试删除项目（软删除）"""
        project = Project.objects.create(name="待删除项目", created_by=self.user)

        response = self.client.delete(f"/api/v1/projects/{project.id}/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # 验证软删除
        project.refresh_from_db()
        self.assertTrue(project.is_deleted)

    def test_list_projects_excludes_deleted(self):
        """测试项目列表不包含已删除项目"""
        Project.objects.create(name="正常项目", created_by=self.user)
        Project.objects.create(name="已删除项目", created_by=self.user, is_deleted=True)

        response = self.client.get("/api/v1/projects/")

        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["name"], "正常项目")


class FileUploadViewTestCase(APITestCase):
    """FileUploadView测试用例"""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser")
        self.client.force_authenticate(user=self.user)
        self.project = Project.objects.create(name="测试项目", created_by=self.user)

    @patch("text_extraction.tasks.process_pdf_task")
    def test_upload_file_success(self, mock_task):
        """测试上传文件成功"""
        mock_task.delay.return_value = MagicMock(id="task-123")

        pdf_content = b"%PDF-1.4 fake pdf content"
        pdf_file = SimpleUploadedFile(
            "test.pdf", pdf_content, content_type="application/pdf"
        )

        data = {"project_id": self.project.id, "file": pdf_file}
        response = self.client.post("/api/v1/upload/", data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["filename"], "test.pdf")
        self.assertEqual(response.data["status"], File.Status.PENDING)

        # 验证文件已创建
        self.assertTrue(File.objects.filter(filename="test.pdf").exists())

    def test_upload_file_invalid_project(self):
        """测试上传到不存在的项目"""
        pdf_file = SimpleUploadedFile(
            "test.pdf", b"%PDF-1.4", content_type="application/pdf"
        )

        data = {"project_id": 99999, "file": pdf_file}
        response = self.client.post("/api/v1/upload/", data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_upload_non_pdf_file(self):
        """测试上传非PDF文件"""
        txt_file = SimpleUploadedFile("test.txt", b"text", content_type="text/plain")

        data = {"project_id": self.project.id, "file": txt_file}
        response = self.client.post("/api/v1/upload/", data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class FileViewSetTestCase(APITestCase):
    """FileViewSet测试用例"""

    def setUp(self):
        self.user = User.objects.create_user(username="testuser")
        self.client.force_authenticate(user=self.user)
        self.project = Project.objects.create(name="测试项目", created_by=self.user)
        self.file_obj = File.objects.create(
            project=self.project, filename="test.pdf", pdf_path="pdf/1/test.pdf"
        )

    def test_list_files(self):
        """测试获取文件列表"""
        response = self.client.get("/api/v1/files/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_list_files_filter_by_project(self):
        """测试按项目过滤文件"""
        response = self.client.get(f"/api/v1/files/?project_id={self.project.id}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_list_files_filter_by_status(self):
        """测试按状态过滤文件"""
        response = self.client.get(f"/api/v1/files/?status={File.Status.PENDING}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_retrieve_file(self):
        """测试获取文件详情"""
        response = self.client.get(f"/api/v1/files/{self.file_obj.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["filename"], "test.pdf")

    def test_get_file_content_not_completed(self):
        """测试获取未完成文件的内容"""
        response = self.client.get(f"/api/v1/files/{self.file_obj.id}/content/")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("text_extraction.views.os.path.exists")
    @patch("builtins.open")
    def test_get_file_content_completed(self, mock_open, mock_exists):
        """测试获取已完成文件的内容"""
        self.file_obj.status = File.Status.COMPLETED
        self.file_obj.mineru_output_path = "mineru/1/test.md"
        self.file_obj.extraction_output_path = "extraction/1/test.json"
        self.file_obj.save()

        mock_exists.return_value = True
        mock_open.return_value.__enter__.return_value.read.side_effect = [
            "# Markdown content",
            '{"data": "test"}',
        ]

        response = self.client.get(f"/api/v1/files/{self.file_obj.id}/content/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("markdown", response.data)
        self.assertIn("ontology", response.data)


# 导入MagicMock供其他测试使用
from unittest.mock import MagicMock
