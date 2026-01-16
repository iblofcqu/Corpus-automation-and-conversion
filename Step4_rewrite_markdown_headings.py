"""
独立脚本：根据hierarchy_analysis.json重写Dataset下的markdown文件标题等级

使用场景：
1. 已经运行过organize_by_headings_llm.py生成了Dataset
2. 想要重新应用层级分类结果到原始md文件
3. 或者手动修改了hierarchy_analysis.json，想要重新应用
"""

import json
import os
from pathlib import Path


def rewrite_markdown_headings(md_file_path, hierarchy, output_path=None):
    """
    根据LLM分析的层级结果重写markdown文件的标题等级

    Args:
        md_file_path: 原始md文件路径
        hierarchy: LLM分析的层级信息列表
        output_path: 输出文件路径（如果为None，则覆盖原文件）
    """
    if output_path is None:
        output_path = md_file_path

    # 读取原始文件
    with open(md_file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    # 创建标题到层级的映射
    # key: 标题的内容（去除#和空格）, value: 新的level
    heading_level_map = {}
    for h in hierarchy:
        title_clean = h['title'].strip()
        heading_level_map[title_clean] = h['level']

    # 统计修改情况
    rewritten_count = 0
    unchanged_count = 0

    # 重写文件
    new_lines = []
    for i, line in enumerate(lines):
        line_stripped = line.strip()

        # 检查是否是标题行
        if line_stripped.startswith('#'):
            # 提取标题内容（去除所有#和空格）
            title_text = line_stripped.lstrip('#').strip()

            # 查找这个标题的新层级
            if title_text in heading_level_map:
                new_level = heading_level_map[title_text]
                # 生成新的标题行
                new_heading = '#' * new_level + ' ' + title_text
                # 保留原行的换行符
                new_lines.append(new_heading + '\n')
                rewritten_count += 1
            else:
                # 标题未找到对应层级，保持原样
                new_lines.append(line)
                unchanged_count += 1
        else:
            # 非标题行，保持原样
            new_lines.append(line)

    # 写入文件
    with open(output_path, 'w', encoding='utf-8', errors='ignore') as f:
        f.writelines(new_lines)

    return {
        "rewritten": rewritten_count,
        "unchanged": unchanged_count,
        "output_path": output_path
    }


def process_single_document(doc_folder):
    """
    处理单个文档文件夹

    Args:
        doc_folder: 文档文件夹路径（Dataset下的子文件夹）

    Returns:
        bool: 是否成功处理
    """
    doc_folder = Path(doc_folder)

    # 查找hierarchy_analysis.json
    hierarchy_file = doc_folder / "hierarchy_analysis.json"
    if not hierarchy_file.exists():
        print(f"  ✗ 未找到 hierarchy_analysis.json")
        return False

    # 读取层级信息
    try:
        with open(hierarchy_file, 'r', encoding='utf-8') as f:
            hierarchy_data = json.load(f)
        hierarchy = hierarchy_data.get('hierarchy', [])
        if not hierarchy:
            print(f"  ✗ hierarchy_analysis.json 中没有层级信息")
            return False
    except Exception as e:
        print(f"  ✗ 读取 hierarchy_analysis.json 失败: {e}")
        return False

    # 查找md文件
    md_files = list(doc_folder.glob("*.md"))
    # 排除 README.md
    md_files = [f for f in md_files if f.name.lower() != "readme.md"]

    if not md_files:
        print(f"  ✗ 未找到markdown文件")
        return False

    md_file = md_files[0]
    print(f"  找到markdown文件: {md_file.name}")
    print(f"  层级信息: {len(hierarchy)} 个标题")

    # 重写markdown文件
    try:
        result = rewrite_markdown_headings(md_file, hierarchy)
        print(f"  ✓ 标题重写完成:")
        print(f"    - 已修改: {result['rewritten']} 个标题")
        print(f"    - 未改变: {result['unchanged']} 个标题")
        return True
    except Exception as e:
        print(f"  ✗ 重写失败: {e}")
        return False


def process_all_documents(dataset_dir, dry_run=False):
    """
    处理Dataset目录下的所有文档

    Args:
        dataset_dir: Dataset目录路径
        dry_run: 如果为True，只显示将要处理的文件，不实际修改
    """
    dataset_path = Path(dataset_dir)

    if not dataset_path.exists():
        print(f"错误: Dataset目录不存在: {dataset_path}")
        return

    # 获取所有子文件夹
    doc_folders = [f for f in dataset_path.iterdir() if f.is_dir()]

    if not doc_folders:
        print(f"错误: Dataset目录下没有子文件夹")
        return

    print(f"\n{'='*80}")
    print(f"批量重写Markdown标题等级")
    print(f"{'='*80}")
    print(f"Dataset目录: {dataset_path}")
    print(f"找到 {len(doc_folders)} 个文档文件夹")
    print(f"模式: {'预览模式（不修改文件）' if dry_run else '执行模式（将修改文件）'}")
    print(f"{'='*80}\n")

    if dry_run:
        print("⚠️  预览模式：将显示待处理的文件，但不会实际修改")
        print()

    success_count = 0
    skip_count = 0
    fail_count = 0

    for i, doc_folder in enumerate(doc_folders, 1):
        print(f"[{i}/{len(doc_folders)}] 处理: {doc_folder.name}")

        if dry_run:
            # 预览模式：只检查文件是否存在
            hierarchy_file = doc_folder / "hierarchy_analysis.json"
            md_files = [f for f in doc_folder.glob("*.md") if f.name.lower() != "readme.md"]

            if hierarchy_file.exists() and md_files:
                print(f"  ✓ 准备就绪")
                print(f"    - 层级文件: {hierarchy_file.name}")
                print(f"    - Markdown: {md_files[0].name}")
                success_count += 1
            else:
                print(f"  ✗ 跳过（缺少必要文件）")
                skip_count += 1
        else:
            # 执行模式：实际处理
            if process_single_document(doc_folder):
                success_count += 1
            else:
                skip_count += 1

        print()

    # 总结
    print(f"{'='*80}")
    print(f"处理完成!")
    print(f"{'='*80}")
    if dry_run:
        print(f"  准备就绪: {success_count} 个")
        print(f"  将跳过: {skip_count} 个")
        print(f"\n运行时不加 --dry-run 参数即可执行实际修改")
    else:
        print(f"  成功: {success_count} 个")
        print(f"  跳过: {skip_count} 个")
        print(f"  失败: {fail_count} 个")
    print(f"{'='*80}")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='根据hierarchy_analysis.json重写Dataset下markdown文件的标题等级',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 预览模式（不修改文件）
  python Step4_rewrite_markdown_headings.py --dry-run

  # 执行模式（实际修改文件）
  python Step4_rewrite_markdown_headings.py

  # 指定Dataset目录
  python Step4_rewrite_markdown_headings.py --dataset-dir "D:\\MyDataset"

  # 处理单个文档
  python Step4_rewrite_markdown_headings.py --single "Dataset\\报告1"

注意：
  - 程序会直接修改Dataset下的md文件
  - 建议先用 --dry-run 预览
  - 或者先备份Dataset目录
        """
    )

    parser.add_argument(
        '--dataset-dir',
        default=r'C:\Users\Qzj\Desktop\projrct\MinerU\Dataset',
        help='Dataset目录路径（默认：C:\\Users\\Qzj\\Desktop\\projrct\\MinerU\\Dataset）'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='预览模式：只显示将要处理的文件，不实际修改'
    )

    parser.add_argument(
        '--single',
        type=str,
        help='只处理单个文档文件夹（提供文件夹路径）'
    )

    args = parser.parse_args()

    if args.single:
        # 处理单个文档
        print(f"\n{'='*80}")
        print(f"处理单个文档")
        print(f"{'='*80}")
        print(f"文档路径: {args.single}\n")

        if args.dry_run:
            print("⚠️  预览模式：将显示待处理的文件，但不会实际修改\n")

            doc_folder = Path(args.single)
            hierarchy_file = doc_folder / "hierarchy_analysis.json"
            md_files = [f for f in doc_folder.glob("*.md") if f.name.lower() != "readme.md"]

            if hierarchy_file.exists() and md_files:
                print(f"✓ 准备就绪")
                print(f"  - 层级文件: {hierarchy_file.name}")
                print(f"  - Markdown: {md_files[0].name}")
            else:
                print(f"✗ 缺少必要文件")
        else:
            process_single_document(args.single)
    else:
        # 处理所有文档
        process_all_documents(args.dataset_dir, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
