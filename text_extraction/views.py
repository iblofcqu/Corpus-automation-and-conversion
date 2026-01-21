"""
API视图
"""

import json
import os
import uuid
from pathlib import Path

from django.conf import settings
from django.http import Http404
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiTypes,
    extend_schema,
    extend_schema_view,
)
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import File, Project
from .serializers import (
    FileDetailSerializer,
    FileListSerializer,
    FileUploadSerializer,
    ProjectCreateSerializer,
    ProjectSerializer,
    ProjectUpdateSerializer,
)


# X-User-ID Header 参数定义
X_USER_ID_PARAM = OpenApiParameter(
    name="X-User-ID",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.HEADER,
    required=True,
    description="用户ID，用于身份验证",
)


@extend_schema_view(
    list=extend_schema(
        summary="获取项目列表", tags=["项目管理"], parameters=[X_USER_ID_PARAM]
    ),
    create=extend_schema(
        summary="创建项目", tags=["项目管理"], parameters=[X_USER_ID_PARAM]
    ),
    retrieve=extend_schema(
        summary="获取项目详情", tags=["项目管理"], parameters=[X_USER_ID_PARAM]
    ),
    destroy=extend_schema(
        summary="删除项目（软删除）", tags=["项目管理"], parameters=[X_USER_ID_PARAM]
    ),
    update=extend_schema(
        summary="修改项目",
        tags=["项目管理"],
        parameters=[X_USER_ID_PARAM],
    ),
)
class ProjectViewSet(viewsets.ModelViewSet):
    """项目管理ViewSet"""

    serializer_class = ProjectSerializer
    queryset = Project.objects.all()

    def get_queryset(self):
        """只返回未删除的项目"""
        return Project.objects.filter(
            created_by=self.request.user, is_deleted=False
        ).order_by("-created_at")

    def get_serializer_class(self):
        """根据动作选择序列化器"""
        if self.action == "create":
            return ProjectCreateSerializer
        if self.action in ["update", "partial_update"]:
            return ProjectUpdateSerializer
        return ProjectSerializer

    def perform_destroy(self, instance):
        """软删除"""
        instance.is_deleted = True
        instance.save()


@extend_schema(
    request=FileUploadSerializer,
    responses={201: FileDetailSerializer},
    summary="上传PDF文件",
    tags=["文件管理"],
    parameters=[X_USER_ID_PARAM],
)
class FileUploadView(APIView):
    """文件上传视图"""

    def post(self, request):
        serializer = FileUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        project_id = serializer.validated_data["project_id"]
        uploaded_file = serializer.validated_data["file"]

        # 获取项目
        try:
            project = Project.objects.get(id=project_id, is_deleted=False)
        except Project.DoesNotExist:
            return Response(
                {"error": "项目不存在或已删除"}, status=status.HTTP_404_NOT_FOUND
            )

        # 生成UUID文件名
        file_uuid = uuid.uuid4().hex
        original_name = uploaded_file.name
        pdf_filename = f"{file_uuid}_{original_name}"

        # 构建文件路径
        pdf_relative_path = os.path.join("pdf", str(project_id), pdf_filename)
        pdf_full_path = os.path.join(settings.MEDIA_ROOT, pdf_relative_path)

        # 确保目录存在
        os.makedirs(os.path.dirname(pdf_full_path), exist_ok=True)

        # 保存文件
        with open(pdf_full_path, "wb") as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)

        # 创建File记录
        file_obj = File.objects.create(
            project=project,
            filename=original_name,
            pdf_path=pdf_relative_path,
            status=File.Status.PENDING,
        )

        # 触发Celery任务
        from .tasks import process_pdf_task

        task = process_pdf_task.delay(file_obj.id)
        file_obj.task_id = task.id
        file_obj.save(update_fields=["task_id"])

        return Response(
            FileDetailSerializer(file_obj).data, status=status.HTTP_201_CREATED
        )


@extend_schema_view(
    list=extend_schema(
        summary="获取文件列表", tags=["文件管理"], parameters=[X_USER_ID_PARAM]
    ),
    retrieve=extend_schema(
        summary="获取文件详情", tags=["文件管理"], parameters=[X_USER_ID_PARAM]
    ),
)
class FileViewSet(viewsets.ReadOnlyModelViewSet):
    """文件查询ViewSet（只读）"""

    queryset = File.objects.all()

    def get_queryset(self):
        """过滤查询集"""
        queryset = File.objects.select_related("project").filter(
            project__created_by=self.request.user, project__is_deleted=False
        )

        # 按项目ID过滤
        project_id = self.request.query_params.get("project_id")
        if project_id:
            queryset = queryset.filter(project_id=project_id)

        # 按状态过滤
        status_param = self.request.query_params.get("status")
        if status_param:
            queryset = queryset.filter(status=status_param)

        return queryset.order_by("-created_at")

    def get_serializer_class(self):
        """根据动作选择序列化器"""
        if self.action == "list":
            return FileListSerializer
        return FileDetailSerializer

    @extend_schema(
        summary="获取文件内容",
        tags=["文件管理"],
        parameters=[X_USER_ID_PARAM],
        responses={
            200: {
                "type": "object",
                "properties": {
                    "markdown": {"type": "string"},
                    "ontology": {"type": "object"},
                },
            }
        },
    )
    @action(detail=True, methods=["get"])
    def content(self, request, pk=None):
        """获取文件的Markdown和本体论JSON内容"""
        file_obj = self.get_object()

        if file_obj.status != File.Status.COMPLETED:
            return Response(
                {"error": "文件尚未处理完成"}, status=status.HTTP_400_BAD_REQUEST
            )

        result = {}

        # 读取Markdown内容
        if file_obj.mineru_output_path:
            markdown_path = os.path.join(
                settings.MEDIA_ROOT, file_obj.mineru_output_path
            )
            if os.path.exists(markdown_path):
                with open(markdown_path, "r", encoding="utf-8") as f:
                    result["markdown"] = f.read()

        # 读取本体论JSON
        if file_obj.extraction_output_path:
            ontology_path = os.path.join(
                settings.MEDIA_ROOT, file_obj.extraction_output_path
            )
            if os.path.exists(ontology_path):
                with open(ontology_path, "r", encoding="utf-8") as f:
                    result["ontology"] = json.load(f)

        return Response(result)
