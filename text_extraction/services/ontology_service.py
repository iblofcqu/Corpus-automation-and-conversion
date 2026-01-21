"""
本体论提取服务 - 封装Step5 OntologyAgent
"""

import json
import logging
import os
import sys
from pathlib import Path

from django.conf import settings

from Step5_ontology_agent_v2 import OntologyAgent

logger = logging.getLogger(__name__)

# 添加项目根目录到Python路径，以便导入Step5
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


class OntologyError(Exception):
    """本体论提取异常"""

    pass


class OntologyService:
    """本体论信息提取服务"""

    def __init__(self):
        self.deepseek_api_key = settings.DEEPSEEK_API_KEY
        self.deepseek_base_url = settings.DEEPSEEK_BASE_URL
        self.deepseek_model = settings.DEEPSEEK_MODEL

    def extract_information(
        self,
        markdown_path: str,
        ontology_path: str,
        output_dir: str,
    ) -> dict:
        """
        从Markdown文件中提取本体论信息

        Args:
            markdown_path: Markdown文件完整路径
            ontology_path: 本体论定义文件完整路径
            output_dir: 输出目录路径（Agent会自动生成{filename}_ontology.json）

        Returns:
            提取结果字典

        Raises:
            OntologyError: 提取失败时抛出
        """
        try:
            logger.info(f"开始本体论提取: {markdown_path}")

            # 验证输入文件
            if not os.path.exists(markdown_path):
                raise OntologyError(f"Markdown文件不存在: {markdown_path}")

            if not os.path.exists(ontology_path):
                raise OntologyError(f"本体论文件不存在: {ontology_path}")

            # 创建输出目录
            os.makedirs(output_dir, exist_ok=True)

            # 创建Agent实例（参数是ontology_path）
            agent = OntologyAgent(ontology_path=ontology_path)

            # 执行提取（调用 process_document 方法）
            result = agent.process_document(
                md_file_path=markdown_path, output_dir=output_dir
            )

            # 验证结果
            if not result.get("success"):
                error = result.get("error", "Unknown error")
                raise OntologyError(f"本体论提取失败: {error}")

            output_path = result.get("output")
            if not output_path or not os.path.exists(
                os.path.join(output_dir, output_path)
            ):
                raise OntologyError(f"本体论输出文件未生成: {output_path}")

            logger.info(f"本体论提取成功: {output_path}")

            return {
                "status": "success",
                "output_path": output_path,
                "document": result.get("document"),
            }

        except OntologyError:
            raise

        except Exception as e:
            error_msg = f"本体论提取失败: {str(e)}"
            logger.error(error_msg)
            raise OntologyError(error_msg) from e

    def validate_ontology_file(self, ontology_path: str) -> bool:
        """
        验证本体论文件格式是否正确

        Args:
            ontology_path: 本体论文件路径

        Returns:
            是否有效
        """
        try:
            with open(ontology_path, encoding="utf-8") as f:
                data = json.load(f)

            # 基本结构验证
            if not isinstance(data, dict):
                return False

            # 检查必要的顶层键
            required_keys = ["categories"]
            return all(key in data for key in required_keys)

        except Exception as e:
            logger.warning(f"本体论文件验证失败: {str(e)}")
            return False
