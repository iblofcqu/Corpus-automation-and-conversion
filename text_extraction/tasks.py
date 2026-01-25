"""
Celery异步任务
"""

import logging
import os
from pathlib import Path

from celery import shared_task

from .models import File
from .services import FileStorageService, MinerUService, OntologyService

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=0)
def process_pdf_task(self, file_id: int) -> dict:
    """
    处理PDF文件的异步任务

    Args:
        file_id: File模型ID

    Returns:
        处理结果字典
    """
    logger.info(f"开始处理文件 ID={file_id}")

    try:
        # 获取File对象
        file_obj = File.objects.select_related("project").get(id=file_id)

        # 更新状态为processing
        file_obj.status = File.Status.PROCESSING
        file_obj.save(update_fields=["status", "updated_at"])

        # 初始化服务
        storage_service = FileStorageService()
        mineru_service = MinerUService()
        ontology_service = OntologyService()

        # 1. 获取PDF完整路径
        pdf_full_path = storage_service.get_full_path(file_obj.pdf_path)

        # 2. 生成输出路径
        filename_without_ext = Path(file_obj.filename).stem
        mineru_relative_path = storage_service.get_mineru_output_path(
            file_obj.project_id, filename_without_ext
        )
        logger.info("mineru 相对路径%s", mineru_relative_path)
        mineru_full_path = storage_service.get_full_path(mineru_relative_path)
        logger.info("输出的绝对路径:%s", mineru_full_path)
        # 确保输出目录存在
        storage_service.ensure_dir(mineru_full_path)

        # 3. 调用MinerU转换PDF
        logger.info("调用MinerU服务...")
        # 传递相对路径
        mineru_result = mineru_service.convert_pdf_to_markdown(
            pdf_path=pdf_full_path,
            output_path=mineru_full_path,
            mode="ocr",
        )

        # 更新MinerU输出路径
        file_obj.mineru_output_path = os.path.join(
            mineru_relative_path,
            mineru_result.output_path,
        )
        file_obj.save(update_fields=["mineru_output_path", "updated_at"])

        # 5. 获取MinerU生成的Markdown文件路径（这是文件而非目录）
        # 绝对路径
        markdown_file_path = os.path.join(mineru_full_path, mineru_result.output_path)
        if not os.path.exists(markdown_file_path):
            raise Exception(f"MinerU输出的Markdown文件不存在: {markdown_file_path}")

        # 6. 生成本体论提取输出目录路径
        extraction_relative_path = storage_service.get_extraction_output_path(
            file_obj.project_id, filename_without_ext
        )
        extraction_output_dir = storage_service.get_full_path(extraction_relative_path)

        # 确保输出目录存在
        storage_service.ensure_dir(extraction_output_dir)

        # 7. 调用本体论提取服务
        logger.info("调用本体论提取服务...")
        extraction_result = ontology_service.extract_information(
            markdown_path=markdown_file_path,
            ontology_path=os.path.join(
                "media",
                file_obj.project.ontology_path,
            ),
            output_dir=extraction_output_dir,
        )

        # 更新提取输出路径（保存实际生成的JSON文件路径）,相对extraction_output_dir的路径
        actual_output_file = extraction_result.get("output_path")
        # 转换为相对路径
        file_obj.extraction_output_path = os.path.join(
            extraction_relative_path,
            actual_output_file,
        )
        file_obj.save(update_fields=["extraction_output_path", "updated_at"])

        # 8. 更新状态为completed
        file_obj.status = File.Status.COMPLETED
        file_obj.error_message = None
        file_obj.save(update_fields=["status", "error_message", "updated_at"])

        logger.info(f"文件处理成功 ID={file_id}")

        return {
            "status": "success",
            "file_id": file_id,
            "mineru_output": mineru_relative_path,
            "extraction_output": extraction_relative_path,
        }

    except File.DoesNotExist:
        error_msg = f"文件不存在: ID={file_id}"
        logger.error(error_msg)
        return {"status": "error", "message": error_msg}

    except Exception as e:
        error_msg = f"文件处理失败: {str(e)}"
        logger.error(error_msg, exc_info=True)

        # 更新状态为failed
        try:
            file_obj = File.objects.get(id=file_id)
            file_obj.status = File.Status.FAILED
            file_obj.error_message = error_msg
            file_obj.save(update_fields=["status", "error_message", "updated_at"])
        except Exception as save_error:
            logger.error(f"无法更新文件状态: {str(save_error)}")

        return {"status": "error", "message": error_msg}
