"""
本体论提取服务 - 封装Step5 OntologyAgent
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Optional

from django.conf import settings

logger = logging.getLogger(__name__)

# 添加项目根目录到Python路径，以便导入Step5
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


class OntologyException(Exception):
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
        output_path: str,
    ) -> dict:
        """
        从Markdown文件中提取本体论信息

        Args:
            markdown_path: Markdown文件完整路径
            ontology_path: 本体论定义文件完整路径
            output_path: 输出JSON文件完整路径

        Returns:
            提取结果字典

        Raises:
            OntologyException: 提取失败时抛出
        """
        try:
            logger.info(f"开始本体论提取: {markdown_path}")

            # 验证输入文件
            if not os.path.exists(markdown_path):
                raise OntologyException(f"Markdown文件不存在: {markdown_path}")

            if not os.path.exists(ontology_path):
                raise OntologyException(f"本体论文件不存在: {ontology_path}")

            # 导入Step5 OntologyAgent
            try:
                from Step5_ontology_agent_v2 import OntologyAgent
            except ImportError as e:
                raise OntologyException(f"无法导入Step5模块: {str(e)}") from e

            # 创建Agent实例
            agent = OntologyAgent(
                markdown_file=markdown_path,
                ontology_file=ontology_path,
                output_dir=os.path.dirname(output_path),
            )

            # 执行提取
            result = agent.run()

            # 验证输出文件
            if not os.path.exists(output_path):
                raise OntologyException(f"本体论输出文件未生成: {output_path}")

            logger.info(f"本体论提取成功: {output_path}")

            return {
                "status": "success",
                "output_path": output_path,
                "fields_extracted": result.get("fields_extracted", 0),
            }

        except OntologyException:
            raise

        except Exception as e:
            error_msg = f"本体论提取失败: {str(e)}"
            logger.error(error_msg)
            raise OntologyException(error_msg) from e

    def validate_ontology_file(self, ontology_path: str) -> bool:
        """
        验证本体论文件格式是否正确

        Args:
            ontology_path: 本体论文件路径

        Returns:
            是否有效
        """
        try:
            with open(ontology_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 基本结构验证
            if not isinstance(data, dict):
                return False

            # 检查必要的顶层键
            required_keys = ["categories"]
            for key in required_keys:
                if key not in data:
                    return False

            return True

        except Exception as e:
            logger.warning(f"本体论文件验证失败: {str(e)}")
            return False
