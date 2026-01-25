"""
数据模型定义
"""

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models


class Project(models.Model):
    """项目模型"""

    name = models.CharField(max_length=255, verbose_name="项目名称")
    description = models.CharField(
        max_length=255,
        verbose_name="项目描述",
        default="",
    )
    ontology_path = models.CharField(
        max_length=500,
        default=settings.DEFAULT_ONTOLOGY_PATH,
        verbose_name="本体论文件路径",
        help_text="相对于MEDIA_ROOT的路径",
    )
    is_deleted = models.BooleanField(default=False, verbose_name="是否已删除")
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="projects", verbose_name="创建者"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "project"
        verbose_name = "项目"
        verbose_name_plural = "项目"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["created_by", "is_deleted"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return self.name


class File(models.Model):
    """文件模型"""

    class Status(models.TextChoices):
        PENDING = "pending", "待处理"
        PROCESSING = "processing", "处理中"
        COMPLETED = "completed", "已完成"
        FAILED = "failed", "失败"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="files",
        verbose_name="所属项目",
    )
    filename = models.CharField(max_length=500, verbose_name="文件名")
    pdf_path = models.CharField(
        max_length=500,
        verbose_name="PDF文件路径",
        help_text="相对于MEDIA_ROOT的路径",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="处理状态",
    )
    task_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        verbose_name="Celery任务ID",
    )
    mineru_output_path = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name="MinerU输出路径",
        help_text="Markdown文件路径",
    )
    extraction_output_path = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        verbose_name="提取输出路径",
        help_text="本体论JSON文件路径",
    )
    error_message = models.TextField(
        null=True,
        blank=True,
        verbose_name="错误信息",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    class Meta:
        db_table = "file"
        verbose_name = "文件"
        verbose_name_plural = "文件"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["project", "status"]),
            models.Index(fields=["task_id"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.filename} ({self.get_status_display()})"
