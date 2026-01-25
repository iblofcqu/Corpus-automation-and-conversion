"""
DRF序列化器
"""

import json
import os
from datetime import datetime

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
            "description",
            "ontology_path",
            "is_deleted",
            "created_by",
            "created_by_username",
            "file_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_by",
            "created_at",
            "updated_at",
            "is_deleted",
        ]

    def get_file_count(self, obj: Project) -> int:
        """获取项目的文件数量"""
        return obj.files.count()


class ProjectCreateSerializer(serializers.ModelSerializer):
    """项目创建序列化器（支持上传本体论文件）"""

    ontology_file = serializers.FileField(write_only=True, required=False)

    class Meta:
        model = Project
        fields = ["id", "name", "ontology_file", "description"]
        read_only_fields = ["id"]

    def create(self, validated_data):
        ontology_file = validated_data.pop("ontology_file", None)
        user = self.context["request"].user

        # 设置创建者
        validated_data["created_by"] = user
        # 生成文件路径
        filename = f"ontology_{user.username}_{validated_data['name']}.json"
        file_path = os.path.join("ontology", filename)
        full_path = os.path.join(settings.MEDIA_ROOT, file_path)

        # 保存文件
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        validated_data["ontology_path"] = file_path
        # 如果上传了自定义本体论文件
        if ontology_file:
            with open(full_path, "wb") as f:
                for chunk in ontology_file.chunks():
                    f.write(chunk)
            validated_data["ontology_path"] = file_path
        else:
            with (
                open(full_path, "wb") as f,
                open(settings.DEFAULT_ONTOLOGY_PATH, "rb") as f_r,
            ):
                f.write(f_r.read())
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


class ProjectUpdateSerializer(serializers.ModelSerializer):
    """项目更新序列化器（支持文件上传）"""

    ontology_path = serializers.FileField(
        required=False,
        allow_null=True,
        help_text="本体论JSON文件（上传时为文件对象，返回时为文件路径字符串）",
    )

    class Meta:
        model = Project
        fields = [
            "name",
            "id",
            "ontology_path",
        ]

    def validate_ontology_file(self, value):
        """验证上传的本体论文件"""
        if value and hasattr(value, "read"):  # 判断是否为文件对象
            # 验证文件扩展名
            if not value.name.endswith(".json"):
                raise serializers.ValidationError("只支持.json格式的文件")

            # 验证文件大小（限制为5MB）
            if value.size > 5 * 1024 * 1024:
                raise serializers.ValidationError("文件大小不能超过5MB")

            # 验证JSON格式
            try:
                content = value.read()
                json.loads(content)
                value.seek(0)  # 重置文件指针
            except json.JSONDecodeError as error:
                raise serializers.ValidationError("无效的JSON文件格式") from error

        return value

    def to_representation(self, instance):
        """自定义返回格式，将ontology_path转为字符串"""
        data = super().to_representation(instance)
        # 返回时，ontology_path 为字符串路径
        data["ontology_path"] = (
            instance.ontology_path if instance.ontology_path else None
        )
        return data

    def update(self, instance, validated_data):
        """更新项目，处理本体论文件上传"""
        ontology_file = validated_data.pop("ontology_path", None)

        # 更新基本字段
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # 处理本体论文件上传
        if ontology_file and hasattr(ontology_file, "read"):  # 判断是文件对象
            # 删除旧文件（如果存在）
            if instance.ontology_path:
                old_path = os.path.join(settings.MEDIA_ROOT, instance.ontology_path)
                if os.path.exists(old_path):
                    os.remove(old_path)

            # 保存新文件
            ontology_dir = os.path.join(settings.MEDIA_ROOT, "ontology")
            os.makedirs(ontology_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"project_{instance.id}_{timestamp}.json"
            file_path = os.path.join(ontology_dir, filename)

            # 写入文件
            with open(file_path, "wb") as f:
                for chunk in ontology_file.chunks():
                    f.write(chunk)

            # 更新数据库路径（相对路径）
            instance.ontology_path = os.path.join("ontology", filename)

        instance.save()
        return instance
