"""
DRF序列化器
"""

import os

from django.conf import settings
from rest_framework import serializers

from .models import File, Project


class ProjectSerializer(serializers.ModelSerializer):
    """项目序列化器"""

    created_by_username = serializers.CharField(
        source="created_by.username", read_only=True
    )
    file_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "id",
            "name",
            "ontology_path",
            "is_deleted",
            "created_by",
            "created_by_username",
            "file_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]

    def get_file_count(self, obj: Project) -> int:
        """获取项目的文件数量"""
        return obj.files.count()


class ProjectCreateSerializer(serializers.ModelSerializer):
    """项目创建序列化器（支持上传本体论文件）"""

    ontology_file = serializers.FileField(write_only=True, required=False)

    class Meta:
        model = Project
        fields = ["id", "name", "ontology_file"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        ontology_file = validated_data.pop("ontology_file", None)
        user = self.context["request"].user

        # 设置创建者
        validated_data["created_by"] = user

        # 如果上传了自定义本体论文件
        if ontology_file:
            # 生成文件路径
            filename = f"ontology_{user.username}_{validated_data['name']}.json"
            file_path = os.path.join("ontology", filename)
            full_path = os.path.join(settings.MEDIA_ROOT, file_path)

            # 保存文件
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "wb") as f:
                for chunk in ontology_file.chunks():
                    f.write(chunk)

            validated_data["ontology_path"] = file_path

        return super().create(validated_data)


class FileListSerializer(serializers.ModelSerializer):
    """文件列表序列化器（简化版）"""

    project_name = serializers.CharField(source="project.name", read_only=True)

    class Meta:
        model = File
        fields = [
            "id",
            "project",
            "project_name",
            "filename",
            "status",
            "created_at",
            "updated_at",
        ]


class FileDetailSerializer(serializers.ModelSerializer):
    """文件详情序列化器"""

    project_name = serializers.CharField(source="project.name", read_only=True)

    class Meta:
        model = File
        fields = [
            "id",
            "project",
            "project_name",
            "filename",
            "pdf_path",
            "status",
            "task_id",
            "mineru_output_path",
            "extraction_output_path",
            "error_message",
            "created_at",
            "updated_at",
        ]


class FileUploadSerializer(serializers.Serializer):
    """文件上传序列化器"""

    project_id = serializers.IntegerField()
    file = serializers.FileField()

    def validate_project_id(self, value):
        """验证项目是否存在且未删除"""
        try:
            Project.objects.get(id=value, is_deleted=False)
        except Project.DoesNotExist as exc:
            raise serializers.ValidationError("项目不存在或已删除") from exc
        return value

    def validate_file(self, value):
        """验证文件类型和大小"""
        # 检查文件扩展名
        if not value.name.lower().endswith(".pdf"):
            raise serializers.ValidationError("只支持PDF文件")

        # 检查文件大小
        max_size = settings.MAX_UPLOAD_SIZE
        if value.size > max_size:
            raise serializers.ValidationError(
                f"文件大小不能超过{max_size / 1024 / 1024:.0f}MB"
            )

        return value
