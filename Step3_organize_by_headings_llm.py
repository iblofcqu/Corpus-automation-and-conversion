import os
import re
import json
import shutil
import sys
from pathlib import Path
from openai import OpenAI


def sanitize_filename(filename):
    """Sanitize filename to remove invalid characters and handle edge cases"""
    if not filename or not isinstance(filename, str):
        return "unnamed"

    # Remove or replace invalid characters for Windows filenames
    # Windows doesn't allow: < > : " / \ | ? *
    sanitized = re.sub(r'[<>:"/\\|?*]+', '_', filename)

    # Limit length to prevent issues with very long filenames (keeping it reasonable for Windows)    # Windows path limit is 260 chars, so keep filename reasonable
    sanitized = sanitized[:200]

    # Remove multiple consecutive underscores and spaces
    sanitized = re.sub(r'_+', '_', sanitized)
    sanitized = re.sub(r'\s+', ' ', sanitized)

    # Remove leading/trailing underscores, dots, and whitespace
    sanitized = sanitized.strip('_ .\t\n\r')

    # Handle case where filename becomes empty
    if not sanitized:
        sanitized = "unnamed"

    # Handle reserved Windows filenames
    reserved_names = {'CON', 'PRN', 'AUX', 'NUL'} | {f'COM{i}' for i in range(1, 10)} | {f'LPT{i}' for i in range(1, 10)}
    base_name = sanitized.split('.')[0] if '.' in sanitized else sanitized
    if base_name.upper() in reserved_names:
        sanitized = f"{sanitized}_file"

    return sanitized


def extract_all_headings_from_md(md_file_path):
    """
    Extract all headings from markdown file, treating them all as level 1 initially
    """
    headings = []
    with open(md_file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    for line_num, line in enumerate(lines):
        line = line.strip()

        # Skip empty lines
        if not line:
            continue

        # Pattern 1: Standard markdown headings (# ## ### etc.)
        if re.match(r'^#{1,6}\s+', line):
            # Extract the title (remove # symbols)
            title = re.sub(r'^#{1,6}\s+', '', line).strip()
            if title:
                headings.append({
                    'content': title,
                    'line_number': line_num,
                    'original_line': line
                })

    return headings


def call_deepseek_for_hierarchy(headings, api_key):
    """
    Call DeepSeek API to analyze heading hierarchy using Chain of Thought prompting
    """
    # Prepare the heading list for the prompt
    heading_list = [{"index": i, "content": h['content']} for i, h in enumerate(headings)]

    # Create the Chain of Thought prompt
    prompt = f"""你是一个文档结构分析专家。我将给你一个从PDF文档中提取的标题列表，这些标题目前都被标记为一级标题。

请使用思维链(Chain of Thought)的方式，分析这些标题的层级关系，并为每个标题分配合适的层级(level)。

标题列表：
{json.dumps(heading_list, ensure_ascii=False, indent=2)}

请按照以下步骤进行分析：

步骤1: 理解文档结构
- 分析标题的内容和语义
- 识别标题之间的关系（总分关系、并列关系、包含关系等）
- 识别标题的编号模式（如果有）

步骤2: 确定顶层结构
- 找出文档的最高层级标题（通常是章、部分、主要板块等）
- 这些标题应该被标记为 level 1

步骤3: 分析子层级
- 对于每个顶层标题，找出它下面的子标题
- 子标题应该比父标题的层级高一级
- 继续递归分析更深层级的标题

步骤4: 验证层级关系
- 确保层级过渡是合理的（不应该出现跳级，如从level 1直接到level 3）
- 确保同一层级的标题是并列关系

步骤5: 输出结果
请以JSON格式输出，包含你的思考过程和最终结果：

{{
  "analysis": "你的详细分析过程，说明你如何判断每个标题的层级",
  "hierarchy": [
    {{
      "index": 0,
      "content": "标题内容",
      "level": 1,
      "reasoning": "为什么这个标题是这个层级"
    }},
    ...
  ]
}}

请确保：
1. 层级从1开始（1是最高层级）
2. 层级数字越大表示层级越深
3. 不要跳过层级
4. 同一层级的标题应该是并列关系
5. 必须为所有标题分配层级

现在请开始分析："""

    try:
        # Initialize DeepSeek client (uses OpenAI-compatible API)
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )

        # Call the API
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个专业的文档结构分析助手，擅长使用逻辑推理分析文档层级结构。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        # Parse the response
        result = json.loads(response.choices[0].message.content)

        print("\n=== LLM 分析过程 ===")
        print(result.get('analysis', 'No analysis provided'))
        print("\n=== 层级划分结果 ===")

        # Extract hierarchy information
        hierarchy_result = result.get('hierarchy', [])

        # Validate and return
        if len(hierarchy_result) != len(headings):
            print(f"警告: LLM返回的标题数量({len(hierarchy_result)})与输入不匹配({len(headings)})")

        return hierarchy_result

    except Exception as e:
        print(f"调用 DeepSeek API 时出错: {str(e)}")
        print("将使用默认层级(所有标题都为level 1)")
        # Fallback: return all headings as level 1
        return [{"index": i, "content": h['content'], "level": 1, "reasoning": "API调用失败"}
                for i, h in enumerate(headings)]


def extract_content_between_headings(lines, start_line, end_line):
    """Extract content between two headings"""
    content_lines = []
    for i in range(start_line + 1, end_line):
        if i < len(lines):
            content_lines.append(lines[i].rstrip())
    return '\n'.join(content_lines).strip()


def build_heading_hierarchy_with_llm(headings, llm_hierarchy, lines):
    """Build a hierarchical structure of headings with their content using LLM results"""
    hierarchy = []

    # Create a mapping from index to LLM hierarchy info
    llm_map = {item['index']: item for item in llm_hierarchy}

    for i, heading in enumerate(headings):
        # Find the next heading to determine content boundaries
        next_heading_line = len(lines)
        if i + 1 < len(headings):
            next_heading_line = headings[i + 1]['line_number']

        # Extract content for this heading
        content = extract_content_between_headings(lines, heading['line_number'], next_heading_line)

        # Get level from LLM result
        llm_info = llm_map.get(i, {"level": 1, "reasoning": "未找到LLM结果"})
        level = llm_info['level']

        # Find parent heading path by looking backwards for higher level headings
        parent_path = []
        current_level = level

        for j in range(i - 1, -1, -1):
            prev_llm_info = llm_map.get(j, {"level": 1})
            if prev_llm_info['level'] < current_level:
                parent_path.insert(0, headings[j]['content'])
                current_level = prev_llm_info['level']
                if current_level == 1:
                    break

        hierarchy.append({
            'level': level,
            'title': heading['content'],
            'content': content,
            'parent_path': parent_path,
            'reasoning': llm_info.get('reasoning', ''),
            'index': i
        })

    return hierarchy


def copy_images_recursively(source_images_dir, dest_doc_folder):
    """Copy all images from source to destination, maintaining structure"""
    if not source_images_dir.exists():
        print("    - No images folder found")
        return

    dest_images_dir = dest_doc_folder / "images"

    # Remove existing images directory if it exists
    if dest_images_dir.exists():
        import stat
        def handle_remove_readonly(func, path, exc):
            if os.path.exists(path):
                os.chmod(path, stat.S_IWRITE)
                func(path)

        shutil.rmtree(dest_images_dir, onerror=handle_remove_readonly)

    # Copy the entire images directory
    shutil.copytree(source_images_dir, dest_images_dir)

    # Count copied images
    image_count = 0
    for root, dirs, files in os.walk(dest_images_dir):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.webp')):
                image_count += 1

    print(f"    - Copied {image_count} images to images folder")


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
                print(f"    重写标题: [{new_level}] {title_text[:50]}...")
            else:
                # 标题未找到对应层级，保持原样
                new_lines.append(line)
        else:
            # 非标题行，保持原样
            new_lines.append(line)

    # 写入文件
    with open(output_path, 'w', encoding='utf-8', errors='ignore') as f:
        f.writelines(new_lines)

    print(f"  ✓ Markdown标题层级已更新: {Path(output_path).name}")
    return output_path


def create_folder_structure_for_document(doc_folder, hierarchy, md_file, auto_dir):
    """Create folder structure for a single document based on heading hierarchy"""

    # Skip document title (usually the first level 1 heading) from folder creation
    filtered_hierarchy = []
    first_level1_found = False

    for heading_info in hierarchy:
        # Skip the first level 1 heading as it's typically the document title
        if heading_info['level'] == 1 and not first_level1_found:
            first_level1_found = True
            # Save the document title as README.md in root folder
            readme_file = doc_folder / "README.md"
            with open(readme_file, 'w', encoding='utf-8', errors='ignore') as f:
                f.write(f"# {heading_info['title']}\n\n{heading_info['content']}")
            print(f"    - Created: README.md (document title)")
            continue
        filtered_hierarchy.append(heading_info)

    # Create folders and save content for each heading
    for heading_info in filtered_hierarchy:
        # Build the folder path based on parent hierarchy
        folder_path = doc_folder

        # Add parent folders (excluding document title)
        for parent in heading_info['parent_path']:
            # Skip the first level 1 heading (document title) in path
            if hierarchy and parent == hierarchy[0]['title'] and hierarchy[0]['level'] == 1:
                continue
            parent_clean = sanitize_filename(parent)
            if parent_clean:  # Only add non-empty folder names
                folder_path = folder_path / parent_clean

        # Add current heading folder
        current_clean = sanitize_filename(heading_info['title'])
        if current_clean:  # Only create folder if name is valid
            folder_path = folder_path / current_clean

            # Create the folder
            folder_path.mkdir(parents=True, exist_ok=True)

            # Save the heading content as a markdown file
            content_file = folder_path / f"{current_clean}.md"
            with open(content_file, 'w', encoding='utf-8', errors='ignore') as f:
                # Include the heading title and content
                f.write(f"# {heading_info['title']}\n\n{heading_info['content']}")

            try:
                rel_path = content_file.relative_to(doc_folder)
                print(f"    - Created: {rel_path}")
            except:
                print(f"    - Created: {content_file}")

    # Copy required files to the document root folder
    # 1. Copy original markdown file
    if md_file.exists():
        dest_md = doc_folder / md_file.name
        shutil.copy2(md_file, dest_md)
        print(f"    - Copied markdown: {dest_md.name}")

    # 2. Copy PDF files (look for .origin.pdf in auto directory and parent directory)
    pdf_files = list(auto_dir.glob("*.origin.pdf"))
    # Also check parent directory for PDF files
    parent_dir = auto_dir.parent
    pdf_files.extend(list(parent_dir.glob("*.pdf")))

    for pdf_file in pdf_files:
        dest_pdf = doc_folder / pdf_file.name
        if not dest_pdf.exists():  # Avoid duplicates
            shutil.copy2(pdf_file, dest_pdf)
            print(f"    - Copied PDF: {dest_pdf.name}")

    # 3. Copy images folder with all images
    images_dir = auto_dir / "images"
    copy_images_recursively(images_dir, doc_folder)

    # 4. Rewrite markdown file headings based on LLM hierarchy
    if hierarchy and md_file.exists():
        dest_md = doc_folder / md_file.name
        if dest_md.exists():
            print(f"    - Rewriting markdown headings based on LLM analysis...")
            try:
                rewrite_markdown_headings(dest_md, hierarchy)
            except Exception as e:
                print(f"      Warning: Failed to rewrite headings: {e}")



def organize_document_by_headings(source_dir, output_base_dir, api_key):
    """
    Organize documents by headings in hierarchical folder structure using LLM for hierarchy detection
    Each source document gets its own folder in the output directory
    """
    source_path = Path(source_dir)
    output_path = Path(output_base_dir)

    # Create output directory if it doesn't exist
    output_path.mkdir(exist_ok=True)

    # Iterate through all subdirectories in the source directory
    for subdir in source_path.iterdir():
        if not subdir.is_dir():
            continue

        # Find the auto directory
        auto_dir = subdir / "auto"
        if not auto_dir.exists():
            print(f"Skipping {subdir.name}, no auto directory found")
            continue

        # Find markdown file
        md_files = list(auto_dir.glob("*.md"))
        if not md_files:
            print(f"Skipping {subdir.name}, no markdown file found")
            continue

        md_file = md_files[0]  # Take the first markdown file found
        doc_name = subdir.name  # Use the original directory name
        doc_name_clean = sanitize_filename(doc_name)  # Clean the name for file system

        print(f"\n{'='*60}")
        print(f"Processing document: {doc_name}")
        if doc_name != doc_name_clean:
            print(f"  (Sanitized to: {doc_name_clean})")
        print(f"{'='*60}")

        # Create document folder in output directory (using sanitized name)
        doc_folder = output_path / doc_name_clean
        doc_folder.mkdir(parents=True, exist_ok=True)

        # Extract headings from markdown file (all as level 1 initially)
        headings = extract_all_headings_from_md(md_file)

        if not headings:
            print(f"  No headings found in {doc_name}, copying files only")
            # Still copy the required files even if no headings
            create_folder_structure_for_document(doc_folder, [], md_file, auto_dir)
            continue

        print(f"  Found {len(headings)} headings, calling LLM for hierarchy analysis...")

        # Call LLM to determine hierarchy
        llm_hierarchy = call_deepseek_for_hierarchy(headings, api_key)

        # Read the full markdown content
        with open(md_file, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()

        # Build heading hierarchy with content using LLM results
        hierarchy = build_heading_hierarchy_with_llm(headings, llm_hierarchy, lines)

        # Ensure the document folder exists before saving files
        doc_folder.mkdir(parents=True, exist_ok=True)

        # Save hierarchy analysis to JSON file for reference
        hierarchy_json_file = doc_folder / "hierarchy_analysis.json"
        print(f"  Saving hierarchy analysis to: {hierarchy_json_file}")

        try:
            with open(hierarchy_json_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "document": doc_name,
                    "total_headings": len(headings),
                    "hierarchy": [
                        {
                            "index": h['index'],
                            "level": h['level'],
                            "title": h['title'],
                            "reasoning": h['reasoning'],
                            "parent_path": h['parent_path']
                        }
                        for h in hierarchy
                    ]
                }, f, ensure_ascii=False, indent=2)
            print(f"  ✓ Saved hierarchy analysis to hierarchy_analysis.json")
        except Exception as e:
            print(f"  ⚠ Warning: Could not save hierarchy analysis: {e}")
            print(f"     Folder: {doc_folder}")
            print(f"     Exists: {doc_folder.exists()}")

        # Create folder structure and save content
        create_folder_structure_for_document(doc_folder, hierarchy, md_file, auto_dir)

        print(f"  ✓ Completed processing {doc_name}")


def main():
    # Get DeepSeek API key from environment variable or user input
    api_key = os.environ.get('DEEPSEEK_API_KEY')

    if not api_key:
        # print("请设置 DEEPSEEK_API_KEY 环境变量，或直接输入:")
        # api_key = input("DeepSeek API Key: ").strip()
        api_key = 'sk-4f3ca5dd06a447aeb81989119aa197c6'

        if not api_key:
            print("错误: 必须提供 DeepSeek API Key")
            sys.exit(1)

    # Define source and output directories
    source_dir = r"C:\Users\Qzj\Desktop\projrct\MinerU\Mineru_changed"
    output_dir = r"C:\Users\Qzj\Desktop\projrct\MinerU\Dataset"

    print("\n" + "="*60)
    print("使用 LLM 智能层级划分开始组织文档")
    print("="*60)
    print(f"源目录: {source_dir}")
    print(f"输出目录: {output_dir}")
    print(f"LLM: DeepSeek (使用 Chain of Thought 提示)")
    print("="*60 + "\n")

    organize_document_by_headings(source_dir, output_dir, api_key)

    print("\n" + "="*60)
    print("✓ 所有文档处理完成!")
    print("="*60)


if __name__ == "__main__":
    main()
