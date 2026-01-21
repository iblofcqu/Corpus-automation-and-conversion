"""
MinerU服务 - PDF转Markdown
"""

import logging
from pathlib import Path
import uuid

import requests
from django.conf import settings
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class MinerUError(Exception):
    """MinerU服务异常"""

    pass


class MinerUConversionResult(BaseModel):
    """MinerU PDF转Markdown转换结果"""

    status: str = Field(description="转换状态，如 'success'")
    output_path: str = Field(description="生成的 Markdown 文件完整路径")
    mode: str = Field(description="使用的转换模式，'auto' 或 'ocr'")
    backend: str = Field(default="unknown", description="MinerU 后端类型")
    version: str = Field(default="unknown", description="MinerU 版本")


class MinerUService:
    """MinerU PDF转Markdown服务"""

    def __init__(self):
        self.api_url = settings.MINERU_API_URL
        self.timeout = settings.MINERU_TIMEOUT

    def convert_pdf_to_markdown(
        self, pdf_path: str, output_path: str, mode: str = "ocr"
    ) -> MinerUConversionResult:
        """
        将PDF转换为Markdown（调用 MinerU HTTP API）

        Args:
            pdf_path: PDF文件完整路径
            output_path: Markdown输出目录路径（不含文件名）
            mode: 转换模式 (auto/ocr)

        Returns:
            MinerUConversionResult: 转换结果数据模型

        Raises:
            MinerUError: 转换失败时抛出
        """

        try:
            logger.info(f"开始转换PDF: {pdf_path} -> {output_path}, 模式: {mode}")

            # 提取文件名（不含扩展名）
            file_stem = Path(pdf_path).stem

            # 构建 MinerU API 请求
            with open(pdf_path, "rb") as pdf_file:
                files = {"files": (Path(pdf_path).name, pdf_file, "application/pdf")}

                # 构建表单数据（参考用户提供的 curl 命令）
                data = {
                    "parse_method": mode,  # auto 或 ocr
                    "lang_list": "ch",  # 中文
                    "return_md": "true",  # 返回 Markdown 内容
                    "return_images": "false",  # 不返回图片（假设已保存到 output_dir）
                    "return_middle_json": "false",
                    "return_model_output": "false",
                    "return_content_list": "false",
                    "start_page_id": 0,
                    "end_page_id": None,  # 空表示处理到最后一页
                    "backend": "pipeline",
                    "table_enable": "false",
                    "formula_enable": "false",
                    "response_format_zip": "false",
                    "output_dir": "/media",  # MinerU 服务端的输出目录
                    "server_url": None,
                }

                # 发起 POST 请求
                response = requests.post(
                    f"{self.api_url}/file_parse",
                    files=files,
                    data=data,
                    timeout=self.timeout,
                )
                response.raise_for_status()

            # 解析响应
            api_response = response.json()
            logger.info(f"MinerU API 响应: {api_response}")

            # 提取 md_content
            results = api_response.get("results", {})
            if file_stem not in results:
                raise MinerUError(
                    f"API 响应中未找到文件 '{file_stem}' 的结果。响应: {api_response}"
                )

            md_content = results[file_stem].get("md_content")
            if not md_content:
                raise MinerUError(
                    f"API 响应中未找到 md_content。响应: {results[file_stem]}"
                )

            # 根据模式创建子目录 (auto/ 或 ocr/)
            method_dir = "ocr" if mode == "ocr" else "auto"
            output_dir = Path(output_path) / method_dir
            output_dir.mkdir(parents=True, exist_ok=True)

            # 写入 Markdown 文件
            markdown_file_path = output_dir / f"{uuid.uuid4()}.md"
            with open(markdown_file_path, "w", encoding="utf-8") as f:
                f.write(md_content)

            logger.info(f"PDF转换成功: {pdf_path} -> {markdown_file_path}")

            # 返回结果
            return MinerUConversionResult(
                status="success",
                output_path=str(markdown_file_path),
                mode=mode,
                backend=api_response.get("backend", "unknown"),
                version=api_response.get("version", "unknown"),
            )

        except FileNotFoundError as e:
            error_msg = f"PDF文件不存在: {pdf_path} - {str(e)}"
            logger.error(error_msg)
            raise MinerUError(error_msg) from e

        except requests.exceptions.Timeout as e:
            error_msg = f"MinerU服务超时（{self.timeout}秒）: {str(e)}"
            logger.error(error_msg)
            raise MinerUError(error_msg) from e

        except requests.exceptions.HTTPError as e:
            error_msg = (
                f"MinerU服务返回错误: HTTP {e.response.status_code} - {e.response.text}"
            )
            logger.error(error_msg)
            raise MinerUError(error_msg) from e

        except requests.exceptions.RequestException as e:
            error_msg = f"MinerU服务请求失败: {str(e)}"
            logger.error(error_msg)
            raise MinerUError(error_msg) from e

        except Exception as e:
            error_msg = f"MinerU转换失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise MinerUError(error_msg) from e
