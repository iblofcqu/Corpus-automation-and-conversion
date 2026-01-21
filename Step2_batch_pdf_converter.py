# Copyright (c) Opendatalab. All rights reserved.
import argparse
import os
from pathlib import Path

from loguru import logger
from mineru.cli.common import do_parse, read_fn
from mineru.utils.guess_suffix_or_lang import guess_suffix_by_path

# 支持的文件后缀
pdf_suffixes = ["pdf"]
image_suffixes = ["png", "jpeg", "jp2", "webp", "gif", "bmp", "jpg"]


def batch_convert_pdfs(input_path, output_dir, backend="pipeline", method="auto", lang="ch",
                      start_page_id=0, end_page_id=None, formula_enable=True, table_enable=True):
    """
    批量转换PDF文件

    参数:
    input_path: 输入文件路径或目录
    output_dir: 输出目录
    backend: 解析后端 (pipeline, vlm-transformers, vlm-vllm-engine, vlm-http-client)
    method: 解析方法 (auto, txt, ocr)
    lang: 文档语言
    start_page_id: 起始页码
    end_page_id: 结束页码
    formula_enable: 是否启用公式解析
    table_enable: 是否启用表格解析
    """

    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)

    # 获取所有待处理的文件路径
    path_list = []
    if os.path.isdir(input_path):
        # 如果是目录，遍历目录中的所有支持的文件
        for doc_path in Path(input_path).glob('*'):
            if guess_suffix_by_path(doc_path) in pdf_suffixes + image_suffixes:
                path_list.append(doc_path)
        logger.info(f"找到 {len(path_list)} 个文件待处理")
    else:
        # 如果是单个文件
        if guess_suffix_by_path(input_path) in pdf_suffixes + image_suffixes:
            path_list.append(Path(input_path))
            logger.info("找到 1 个文件待处理")
        else:
            logger.error(f"不支持的文件类型: {input_path}")
            return

    if not path_list:
        logger.warning("没有找到支持的文件")
        return

    try:
        # 准备文件数据
        file_name_list = []
        pdf_bytes_list = []
        lang_list = []

        for path in path_list:
            file_name = str(Path(path).stem)
            pdf_bytes = read_fn(path)
            file_name_list.append(file_name)
            pdf_bytes_list.append(pdf_bytes)
            lang_list.append(lang)
            logger.info(f"已加载文件: {file_name}")

        # 执行批量转换
        logger.info("开始批量转换...")
        do_parse(
            output_dir=output_dir,
            pdf_file_names=file_name_list,
            pdf_bytes_list=pdf_bytes_list,
            p_lang_list=lang_list,
            backend=backend,
            parse_method=method,
            formula_enable=formula_enable,
            table_enable=table_enable,
            start_page_id=start_page_id,
            end_page_id=end_page_id
        )

        logger.info(f"批量转换完成，结果保存在: {output_dir}")

    except Exception as e:
        logger.exception(f"批量转换过程中出现错误: {e}")

def main():
    # 如果需要直接使用input_file和output_file变量，可以在这里设置默认值
    # 但为了保持命令行工具的灵活性，我们仍然使用argparse
    parser = argparse.ArgumentParser(description="批量PDF转换工具")
    parser.add_argument(
        "-p", "--path",
        dest="input_path",
        type=str,
        required=True,
        help="输入文件路径或目录，支持PDF和图像文件"
    )
    parser.add_argument(
        "-o", "--output",
        dest="output_dir",
        type=str,
        required=True,
        help="输出目录"
    )
    parser.add_argument(
        "-b", "--backend",
        dest="backend",
        type=str,
        choices=["pipeline", "vlm-transformers", "vlm-vllm-engine", "vlm-http-client"],
        default="pipeline",
        help="解析后端"
    )
    parser.add_argument(
        "-m", "--method",
        dest="method",
        type=str,
        choices=["auto", "txt", "ocr"],
        default="auto",
        help="解析方法"
    )
    parser.add_argument(
        "-l", "--lang",
        dest="lang",
        type=str,
        default="ch",
        help="文档语言"
    )
    parser.add_argument(
        "-s", "--start",
        dest="start_page_id",
        type=int,
        default=0,
        help="起始页码 (从0开始)"
    )
    parser.add_argument(
        "-e", "--end",
        dest="end_page_id",
        type=int,
        default=None,
        help="结束页码 (从0开始)"
    )
    parser.add_argument(
        "--no-formula",
        dest="formula_enable",
        action="store_false",
        help="禁用公式解析"
    )
    parser.add_argument(
        "--no-table",
        dest="table_enable",
        action="store_false",
        help="禁用表格解析"
    )

    args = parser.parse_args()

    # 执行批量转换
    batch_convert_pdfs(
        input_path=args.input_path,
        output_dir=args.output_dir,
        backend=args.backend,
        method=args.method,
        lang=args.lang,
        start_page_id=args.start_page_id,
        end_page_id=args.end_page_id,
        formula_enable=args.formula_enable,
        table_enable=args.table_enable
    )

# 添加一个可以直接调用的函数，使用预设的输入输出路径
def run_with_paths(input_file, output_file):
    """
    使用预设的输入和输出路径运行批量转换
    参数:
    input_file: 输入文件路径或目录
    output_file: 输出目录路径
    """
    batch_convert_pdfs(
        input_path=input_file,
        output_dir=output_file,
        backend="pipeline",
        method="auto",
        lang="ch",
        start_page_id=0,
        end_page_id=None,
        formula_enable=True,
        table_enable=True
    )

if __name__ == "__main__":
    # 检查是否通过命令行传参
    import sys
    if len(sys.argv) > 1:
        # 如果有命令行参数，按原有方式执行
        main()
    else:
        # 如果没有命令行参数，在IDE中直接运行时使用以下默认路径
        # 请根据您的实际路径修改以下两个变量
        input_file = r"C:\Users\Qzj\Desktop\projrct\MinerU\input_file_pdf"  # 修改为您的输入文件或目录路径
        output_file = r"C:\Users\Qzj\Desktop\projrct\MinerU\output_file"  # 修改为您的输出目录路径

        # 确保输出目录存在
        os.makedirs(output_file, exist_ok=True)
        os.environ['MINERU_DEVICE_MODE'] = 'cuda'  # 强制使用 CUDA
        # 运行转换
        run_with_paths(input_file, output_file)
