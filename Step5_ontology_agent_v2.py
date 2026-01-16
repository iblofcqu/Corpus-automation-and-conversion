"""
═══════════════════════════════════════════════════════════════════════════════
                   事故报告本体论驱动的智能处理 Agent
═══════════════════════════════════════════════════════════════════════════════

架构说明：
本 Agent 系统基于本体论（Ontology）设计，将事故调查报告转化为层级化的结构信息。

┌─────────────────────────────────────────────────────────────────────────────┐
│                           AGENT 架构全景图                                    │
└─────────────────────────────────────────────────────────────────────────────┘

        ┌───────────────────────────────────────────────────────┐
        │                   输入: Markdown 文件                  │
        │            (已由 Step3_organize_by_headings_llm.py           │
        │                  重写标题层级的文件)                    │
        └────────────────────┬──────────────────────────────────┘
                             │
                             ▼
        ┌─────────────────────────────────────────────────────────┐
        │            1️⃣  HeaderExtractor 标题提取器               │
        │  ┌───────────────────────────────────────────────────┐  │
        │  │  功能: 提取 MD 文件的所有标题层级                  │  │
        │  │  输出: [{level: 1, title: "...", content: "..."}] │  │
        │  └───────────────────────────────────────────────────┘  │
        └───────────────────────┬─────────────────────────────────┘
                                │  存入 Memory Pool
                                ▼
        ┌─────────────────────────────────────────────────────────┐
        │               Memory Pool (记忆池)                       │
        │  ┌───────────────────────────────────────────────────┐  │
        │  │ document_path:   文档路径                         │  │
        │  │ document_content: 完整文档内容                    │  │
        │  │ headers:         提取的标题层级列表                │  │
        │  │ split_plan:      LLM生成的拆分方案                │  │
        │  │ chunks:          拆分后的文档块                    │  │
        │  │ extracted_data:  提取的本体论数据                 │  │
        │  │ ontology:        本体论结构                       │  │
        │  └───────────────────────────────────────────────────┘  │
        └───────────────────────┬─────────────────────────────────┘
                                │  读取 ontology.json
                                ▼
        ┌─────────────────────────────────────────────────────────┐
        │            2️⃣  SplitPlanner 拆分规划器                  │
        │  ┌───────────────────────────────────────────────────┐  │
        │  │  功能: LLM 根据本体论和标题层级生成拆分方案       │  │
        │  │  输入: headers + ontology                         │  │
        │  │  输出: 拆分方案 {                                 │  │
        │  │          "chunk_1": {                             │  │
        │  │             "ontology_category": "事故基本情况",  │  │
        │  │             "header_ranges": [[0, 5]],            │  │
        │  │             "reason": "..."                       │  │
        │  │          }                                        │  │
        │  │        }                                          │  │
        │  └───────────────────────────────────────────────────┘  │
        └───────────────────────┬─────────────────────────────────┘
                                │  存入 Memory Pool
                                ▼
        ┌─────────────────────────────────────────────────────────┐
        │           3️⃣  DocumentSplitter 文档拆分器               │
        │  ┌───────────────────────────────────────────────────┐  │
        │  │  功能: 根据拆分方案执行文档切分                   │  │
        │  │  输入: split_plan + document_content              │  │
        │  │  输出: chunks = [{                                │  │
        │  │           "chunk_id": "chunk_1",                  │  │
        │  │           "ontology_category": "事故基本情况",    │  │
        │  │           "content": "完整的原文内容...",         │  │
        │  │           "headers_included": [...]               │  │
        │  │         }]                                        │  │
        │  └───────────────────────────────────────────────────┘  │
        └───────────────────────┬─────────────────────────────────┘
                                │  存入 Memory Pool
                                ▼
        ┌─────────────────────────────────────────────────────────┐
        │        4️⃣  InformationExtractor 信息提取器              │
        │  ┌───────────────────────────────────────────────────┐  │
        │  │  功能: 严格按照本体论提取信息(复制原文,不改写)   │  │
        │  │  策略:                                            │  │
        │  │    - copy_exact: 精确复制字段值                   │  │
        │  │    - copy_section: 复制整段内容                   │  │
        │  │    - list_extract: 逐条复制列表                   │  │
        │  │    - structured_extract: 按schema复制对象         │  │
        │  │    - structured_list_extract: 按schema复制列表    │  │
        │  │                                                   │  │
        │  │  输入: chunk + ontology_category                  │  │
        │  │  输出: 提取的结构化数据                           │  │
        │  └───────────────────────────────────────────────────┘  │
        └───────────────────────┬─────────────────────────────────┘
                                │  存入 Memory Pool
                                ▼
        ┌─────────────────────────────────────────────────────────┐
        │         5️⃣  OntologySerializer 序列化器                 │
        │  ┌───────────────────────────────────────────────────┐  │
        │  │  功能: 按本体论结构组织数据并序列化为JSON         │  │
        │  │  输入: extracted_data (各chunk提取的数据)         │  │
        │  │  输出: 符合本体论结构的完整JSON文件               │  │
        │  │  {                                                │  │
        │  │    "报告元信息": {...},                           │  │
        │  │    "事故基本情况": {...},                         │  │
        │  │    "事故经过与性质": {...},                       │  │
        │  │    "人员伤亡情况": {...},                         │  │
        │  │    "事故原因分析": {...},                         │  │
        │  │    "责任认定": {...}                              │  │
        │  │  }                                                │  │
        │  └───────────────────────────────────────────────────┘  │
        └───────────────────────┬─────────────────────────────────┘
                                │
                                ▼
        ┌─────────────────────────────────────────────────────────┐
        │                输出: JSON 文件                           │
        │           (符合本体论结构的事故报告数据)                 │
        └─────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────────────────┐
│                         核心设计原则                                          │
└─────────────────────────────────────────────────────────────────────────────┘

1. 本体论驱动 (Ontology-Driven)
   - 本体论定义了事故报告的标准分析框架
   - 所有提取操作严格遵循本体论定义的字段和策略

2. 严格原文复制 (Exact Copy)
   - 提取策略强调 "copy_exact" 而非 "generate"
   - LLM 的角色是 "定位和复制"，而非 "理解和改写"
   - 保证数据的原始性和准确性

3. 记忆池设计 (Memory Pool)
   - 各模块间通过统一的记忆池传递数据
   - 支持数据追溯和调试
   - 便于扩展新的处理模块

4. 策略可配置 (Strategy Configurable)
   - 提取策略在 ontology.json 中配置
   - 支持自定义 prompt_template
   - 灵活适应不同类型的字段提取需求

═══════════════════════════════════════════════════════════════════════════════
作者: Zijin Qiu
版本: v1.0
日期: 2025-10-26
═══════════════════════════════════════════════════════════════════════════════
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from openai import OpenAI
import copy


# ═══════════════════════════════════════════════════════════════════════════
#                           LLM 配置
# ═══════════════════════════════════════════════════════════════════════════

MODEL = "deepseek-chat"
API_KEY = 'sk-4f3ca5dd06a447aeb81989119aa197c6'
BASE_URL = "https://api.deepseek.com"

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)


# ═══════════════════════════════════════════════════════════════════════════
#                       Memory Pool (记忆池)
# ═══════════════════════════════════════════════════════════════════════════

class MemoryPool:
    """
    记忆池：用于在 Agent 各模块间传递和存储数据

    设计目的：
    1. 统一的数据存储接口
    2. 支持数据版本追溯
    3. 便于调试和日志记录
    """

    def __init__(self):
        self.memory = {
            "document_path": None,           # 文档路径
            "document_content": None,        # 完整文档内容
            "headers": [],                   # 提取的标题层级
            "ontology": None,                # 本体论结构
            "split_plan": None,              # 拆分方案
            "chunks": [],                    # 拆分后的文档块
            "extracted_data": {},            # 提取的数据
            "processing_log": [],            # 处理日志
        }

    def set(self, key: str, value: Any):
        """存储数据到记忆池"""
        self.memory[key] = value
        self.log(f"Memory updated: {key}")

    def get(self, key: str) -> Any:
        """从记忆池获取数据"""
        return self.memory.get(key)

    def log(self, message: str):
        """记录处理日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.memory["processing_log"].append(log_entry)
        print(f"  📝 {message}")

    def _convert_to_serializable(self, obj):
        """
        递归转换对象为可序列化格式

        处理:
        - Path 对象 → 字符串
        - 其他不可序列化对象 → 字符串表示
        """
        if isinstance(obj, Path):
            return str(obj)
        elif isinstance(obj, dict):
            return {key: self._convert_to_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_to_serializable(item) for item in obj]
        elif isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        else:
            # 其他类型转换为字符串
            return str(obj)

    def save_memory(self, output_path: str):
        """保存记忆池到文件（用于调试）"""
        # 创建可序列化的副本
        serializable_memory = copy.deepcopy(self.memory)

        # 转换所有不可序列化对象
        serializable_memory = self._convert_to_serializable(serializable_memory)

        # 截断过长的内容
        if serializable_memory.get("document_content"):
            content = serializable_memory["document_content"]
            if isinstance(content, str) and len(content) > 1000:
                serializable_memory["document_content"] = content[:1000] + "...(truncated)"

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_memory, f, ensure_ascii=False, indent=2)


# ═══════════════════════════════════════════════════════════════════════════
#                   1️⃣ HeaderExtractor (标题提取器)
# ═══════════════════════════════════════════════════════════════════════════

class HeaderExtractor:
    """
    标题提取器：从 Markdown 文件中提取标题层级结构

    输入: Markdown 文件内容
    输出: [{level: 1, title: "...", content: "...", start_line: 0, end_line: 10}, ...]
    """

    @staticmethod
    def extract(md_content: str, memory_pool: MemoryPool) -> List[Dict]:
        """
        提取标题层级

        Args:
            md_content: Markdown 文件内容
            memory_pool: 记忆池

        Returns:
            标题列表
        """
        memory_pool.log("HeaderExtractor: 开始提取标题层级")

        lines = md_content.split('\n')
        headers = []
        current_header = None
        first_header_line = None  # 记录第一个标题的行号

        # 先找到第一个标题的位置
        for i, line in enumerate(lines):
            if line.strip().startswith('#'):
                first_header_line = i
                break

        # 如果第一个标题之前有内容，创建一个虚拟的"文档开头"标题
        if first_header_line is not None and first_header_line > 0:
            preamble_content = '\n'.join(lines[0:first_header_line]).strip()
            if preamble_content:  # 只有非空内容才添加
                headers.append({
                    'index': 0,
                    'level': 0,
                    'title': '文档开头（基本信息）',
                    'start_line': 0,
                    'end_line': first_header_line - 1,
                    'content': preamble_content
                })
                memory_pool.log("HeaderExtractor: 检测到文档开头有基本信息（不在标题层级下）")

        for i, line in enumerate(lines):
            line_stripped = line.strip()

            # 检查是否是标题行
            if line_stripped.startswith('#'):
                # 保存上一个标题
                if current_header:
                    current_header['end_line'] = i - 1
                    current_header['content'] = '\n'.join(lines[current_header['start_line']:i]).strip()
                    headers.append(current_header)

                # 创建新标题
                level = len(line_stripped) - len(line_stripped.lstrip('#'))
                title = line_stripped.lstrip('#').strip()

                current_header = {
                    'index': len(headers),
                    'level': level,
                    'title': title,
                    'start_line': i,
                    'end_line': None,
                    'content': ''
                }

        # 保存最后一个标题
        if current_header:
            current_header['end_line'] = len(lines) - 1
            current_header['content'] = '\n'.join(lines[current_header['start_line']:]).strip()
            headers.append(current_header)

        memory_pool.log(f"HeaderExtractor: 提取到 {len(headers)} 个标题")
        memory_pool.set("headers", headers)

        return headers


# ═══════════════════════════════════════════════════════════════════════════
#                   2️⃣ SplitPlanner (拆分规划器)
# ═══════════════════════════════════════════════════════════════════════════

class SplitPlanner:
    """
    拆分规划器：根据本体论和标题层级，使用 LLM 生成文档拆分方案

    输入: 标题列表 + 本体论结构
    输出: 拆分方案
    """

    @staticmethod
    def plan(memory_pool: MemoryPool) -> Dict:
        """
        生成拆分方案

        Args:
            memory_pool: 记忆池

        Returns:
            拆分方案
        """
        memory_pool.log("SplitPlanner: 开始规划文档拆分方案")

        headers = memory_pool.get("headers")
        ontology = memory_pool.get("ontology")

        # 构建本体论类别摘要
        ontology_summary = []
        for category_name, category_info in ontology["ontology_structure"].items():
            ontology_summary.append({
                "类别名称": category_name,
                "优先级": category_info["priority"],
                "描述": category_info["description"],
                "关键词": category_info["keywords"],
                "最大tokens": category_info.get("max_tokens", 5000)
            })

        # 构建标题摘要
        headers_summary = []
        for h in headers:
            headers_summary.append({
                "索引": h["index"],
                "层级": h["level"],
                "标题": h["title"],
                "内容长度": len(h["content"])
            })

        # 构建 LLM prompt
        prompt = f"""
你是一个专业的事故报告分析专家。现在需要你根据本体论结构和文档的标题层级，制定一个文档拆分方案。

【本体论结构】（按优先级排序）
{json.dumps(ontology_summary, ensure_ascii=False, indent=2)}

【文档标题层级】
{json.dumps(headers_summary, ensure_ascii=False, indent=2)}

【任务要求】
1. 将文档标题分配到本体论的各个类别中
2. 每个类别可以包含多个标题（通过标题索引指定范围）
3. 考虑标题的语义和本体论类别的关键词匹配
4. 控制每个chunk的大小不超过类别的max_tokens
5. 优先级高的类别优先分配

【输出格式】
请返回一个JSON对象，格式如下：
{{
  "chunk_基本情况": {{
    "ontology_category": "事故基本情况",
    "header_indices": [0, 1, 2],
    "reason": "这些标题包含了工程概况、项目信息等基本情况"
  }},
  "chunk_事故经过": {{
    "ontology_category": "事故经过与性质",
    "header_indices": [3, 4],
    "reason": "这些标题描述了事故的发生过程"
  }},
  ...
}}

**重要：只返回JSON，不要有其他解释文字。**
"""

        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": "你是专业的事故报告分析专家。只返回JSON格式，不要添加任何解释文本。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )

            content_str = response.choices[0].message.content

            # 解析 JSON
            try:
                split_plan = json.loads(content_str)
            except json.JSONDecodeError:
                # 尝试提取 JSON 部分
                code_block_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', content_str, re.DOTALL)
                if code_block_match:
                    split_plan = json.loads(code_block_match.group(1))
                else:
                    json_match = re.search(r'\{.*\}', content_str, re.DOTALL)
                    if json_match:
                        split_plan = json.loads(json_match.group())
                    else:
                        raise ValueError("无法解析 LLM 返回的拆分方案")

            memory_pool.log(f"SplitPlanner: 生成了 {len(split_plan)} 个拆分chunk")
            memory_pool.set("split_plan", split_plan)

            return split_plan

        except Exception as e:
            memory_pool.log(f"SplitPlanner: 错误 - {e}")
            raise


# ═══════════════════════════════════════════════════════════════════════════
#                   3️⃣ DocumentSplitter (文档拆分器)
# ═══════════════════════════════════════════════════════════════════════════

class DocumentSplitter:
    """
    文档拆分器：根据拆分方案执行文档切分

    输入: 拆分方案 + 标题列表
    输出: 拆分后的文档块
    """

    @staticmethod
    def split(memory_pool: MemoryPool) -> List[Dict]:
        """
        执行文档拆分

        Args:
            memory_pool: 记忆池

        Returns:
            文档块列表
        """
        memory_pool.log("DocumentSplitter: 开始拆分文档")

        split_plan = memory_pool.get("split_plan")
        headers = memory_pool.get("headers")

        chunks = []

        for chunk_id, chunk_info in split_plan.items():
            ontology_category = chunk_info["ontology_category"]
            header_indices = chunk_info["header_indices"]

            # 合并指定索引的标题内容
            content_parts = []
            headers_included = []

            for idx in header_indices:
                if 0 <= idx < len(headers):
                    header = headers[idx]
                    content_parts.append(header["content"])
                    headers_included.append({
                        "index": header["index"],
                        "level": header["level"],
                        "title": header["title"]
                    })

            chunk = {
                "chunk_id": chunk_id,
                "ontology_category": ontology_category,
                "content": "\n\n".join(content_parts),
                "headers_included": headers_included,
                "char_count": sum(len(part) for part in content_parts)
            }

            chunks.append(chunk)
            memory_pool.log(f"DocumentSplitter: 创建chunk '{chunk_id}' (类别: {ontology_category}, {chunk['char_count']} 字符)")

        memory_pool.set("chunks", chunks)
        return chunks


# ═══════════════════════════════════════════════════════════════════════════
#                   4️⃣ InformationExtractor (信息提取器)
# ═══════════════════════════════════════════════════════════════════════════

class InformationExtractor:
    """
    信息提取器：严格按照本体论提取信息，强调原文复制而非改写

    核心策略：
    - copy_exact: 精确复制字段值
    - copy_section: 复制整段内容
    - list_extract: 逐条复制列表
    - structured_extract: 按schema复制对象
    - structured_list_extract: 按schema复制列表
    - cross_chunk_summarize: 跨chunk综合总结
    - cross_chunk_list_extract: 跨chunk列表提取
    - cross_chunk_structured_list_extract: 跨chunk结构化列表提取
    - classify_with_options: 从预定义选项中分类选择
    """

    # 预定义的分类选项
    ACCIDENT_LEVEL_OPTIONS = ["一般", "较大", "重大", "特别重大"]
    ACCIDENT_NATURE_OPTIONS = ["责任事故", "意外(非责任)事故"]

    @staticmethod
    def _extract_responsible_persons(memory_pool: MemoryPool, ontology: Dict) -> List[Dict]:
        """
        提取责任人员信息，综合人员伤亡情况和责任认定两部分

        Args:
            memory_pool: 记忆池
            ontology: 本体论

        Returns:
            责任人员列表
        """
        memory_pool.log("    跨chunk提取责任人员，综合人员伤亡情况和责任认定")

        # 收集人员伤亡情况内容
        casualties_content = InformationExtractor._collect_cross_chunk_content(
            ["人员伤亡情况"], memory_pool
        )

        # 收集责任认定内容
        responsibility_content = InformationExtractor._collect_cross_chunk_content(
            ["责任认定"], memory_pool
        )

        # 合并两部分内容
        combined_content = f"""【人员基本信息部分】
{casualties_content}

【责任认定部分】
{responsibility_content}"""

        # 获取责任人员的schema
        schema = {
            "姓名": {"type": "string", "extraction_strategy": "copy_exact"},
            "性别": {"type": "string", "extraction_strategy": "copy_exact"},
            "年龄": {"type": "string", "extraction_strategy": "copy_exact"},
            "职位或工种": {"type": "string", "extraction_strategy": "copy_exact"},
            "持证上岗情况": {"type": "string", "extraction_strategy": "copy_exact"},
            "所属单位": {"type": "string", "extraction_strategy": "copy_exact"},
            "责任认定": {"type": "text", "extraction_strategy": "copy_section"},
            "处罚意见": {"type": "text", "extraction_strategy": "copy_section"}
        }

        schema_str = json.dumps(schema, ensure_ascii=False, indent=2)

        prompt = f"""根据以下文档内容，提取所有事故责任人员的信息。要求：

1. 人员基本信息(姓名、性别、年龄、职位或工种、所属单位)主要从【人员基本信息部分】中获取
2. 责任认定和处罚意见从【责任认定部分】中获取
3. 需要将两部分信息关联起来（通过姓名匹配）
4. 只提取被认定有责任的人员（在责任认定部分有明确说明的人员）
5. 每个人员信息按照以下schema提取：

{schema_str}

6. 直接复制原文中的字段值，不要改写或总结
7. 以JSON数组格式返回

文档内容：
{combined_content[:15000]}

返回格式：[{{"姓名": "原文值1", "性别": "原文值", ...}}, {{"姓名": "原文值2", ...}}, ...]"""

        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": "你是专业的信息提取助手。综合分析人员基本信息和责任认定两部分内容，提取责任人员的完整信息。严格复制原文，不要改写。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=3000
            )

            result_str = response.choices[0].message.content.strip()

            # 解析 JSON
            try:
                result = json.loads(result_str)
            except json.JSONDecodeError:
                # 尝试提取 JSON 部分
                code_block_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', result_str, re.DOTALL)
                if code_block_match:
                    result = json.loads(code_block_match.group(1))
                else:
                    json_match = re.search(r'\[.*\]', result_str, re.DOTALL)
                    if json_match:
                        result = json.loads(json_match.group())
                    else:
                        memory_pool.log(f"    警告: 无法解析JSON结果")
                        result = []

            memory_pool.log(f"    提取到 {len(result)} 个责任人员")
            return result

        except Exception as e:
            memory_pool.log(f"    错误: 责任人员提取失败 - {e}")
            return []

    @staticmethod
    def _classify_with_options(content: str, field_name: str, options: List[str], memory_pool: MemoryPool) -> str:
        """
        从预定义选项中分类选择

        Args:
            content: 文档内容
            field_name: 字段名称
            options: 预定义选项列表
            memory_pool: 记忆池

        Returns:
            选中的选项
        """
        prompt = f"""从以下文本中识别「{field_name}」，并从预定义选项中选择最匹配的一项。

预定义选项：{', '.join(options)}

文本内容：
{content[:8000]}

要求：
1. 仔细阅读文本，找到与「{field_name}」相关的描述
2. 从预定义选项中选择一个最匹配的选项
3. 只返回选项本身，不要添加任何解释或其他文字
4. 如果文本中没有明确说明，请根据描述推断最合理的选项

只返回选中的选项："""

        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": f"你是专业的信息提取助手。从给定的预定义选项中选择一个：{', '.join(options)}。只返回选项本身。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=50
            )

            result = response.choices[0].message.content.strip()

            # 验证结果是否在选项中
            for option in options:
                if option in result:
                    memory_pool.log(f"    分类结果: {option}")
                    return option

            # 如果没有匹配，返回第一个选项作为默认值
            memory_pool.log(f"    警告: 分类结果 '{result}' 不在预定义选项中，使用默认值: {options[0]}")
            return options[0]

        except Exception as e:
            memory_pool.log(f"    错误: 分类失败 - {e}")
            return options[0]  # 返回默认值

    @staticmethod
    def _collect_cross_chunk_content(source_categories: List[str], memory_pool: MemoryPool) -> str:
        """
        收集多个类别的chunk内容

        Args:
            source_categories: 需要收集的本体论类别列表
            memory_pool: 记忆池

        Returns:
            合并后的内容
        """
        chunks = memory_pool.get("chunks")
        collected_content = []

        for category in source_categories:
            # 查找属于该类别的所有chunk
            for chunk in chunks:
                if chunk["ontology_category"] == category:
                    collected_content.append(f"【{category}】\n{chunk['content']}")

        if not collected_content:
            memory_pool.log(f"    警告: 未找到任何源类别的内容")
            return ""

        # 合并内容，限制总长度
        merged_content = "\n\n".join(collected_content)
        max_length = 12000  # 增加长度以容纳多个chunk

        if len(merged_content) > max_length:
            memory_pool.log(f"    提示: 内容过长({len(merged_content)}字符)，截取前{max_length}字符")
            merged_content = merged_content[:max_length]

        return merged_content

    @staticmethod
    def extract(memory_pool: MemoryPool) -> Dict:
        """
        提取信息

        Args:
            memory_pool: 记忆池

        Returns:
            提取的数据
        """
        memory_pool.log("InformationExtractor: 开始提取信息")

        chunks = memory_pool.get("chunks")
        ontology = memory_pool.get("ontology")

        extracted_data = {}
        processed_categories = set()  # 记录已处理的类别

        for chunk in chunks:
            chunk_id = chunk["chunk_id"]
            ontology_category = chunk["ontology_category"]
            content = chunk["content"]

            # 如果该类别已经处理过，跳过（避免重复提取）
            if ontology_category in processed_categories:
                memory_pool.log(f"InformationExtractor: 跳过已处理的类别 '{ontology_category}'")
                continue

            memory_pool.log(f"InformationExtractor: 处理chunk '{chunk_id}' (类别: {ontology_category})")

            # 获取本体论类别定义
            category_def = ontology["ontology_structure"].get(ontology_category)
            if not category_def:
                memory_pool.log(f"InformationExtractor: 警告 - 未找到本体论类别 '{ontology_category}'")
                continue

            # 提取该类别的所有字段
            category_data = {}

            for field_name, field_def in category_def["fields"].items():
                field_type = field_def["type"]
                extraction_strategy = field_def["extraction_strategy"]

                memory_pool.log(f"  提取字段: {field_name} (策略: {extraction_strategy})")

                # 根据策略提取
                extracted_value = InformationExtractor._extract_field(
                    field_name=field_name,
                    field_def=field_def,
                    content=content,
                    ontology=ontology,
                    memory_pool=memory_pool
                )

                category_data[field_name] = extracted_value

            extracted_data[ontology_category] = category_data
            processed_categories.add(ontology_category)  # 标记为已处理

        memory_pool.set("extracted_data", extracted_data)
        return extracted_data

    @staticmethod
    def _extract_field(field_name: str, field_def: Dict, content: str,
                      ontology: Dict, memory_pool: MemoryPool) -> Any:
        """
        提取单个字段

        Args:
            field_name: 字段名称
            field_def: 字段定义
            content: 文档内容（可能是单个chunk或跨chunk合并内容）
            ontology: 本体论
            memory_pool: 记忆池

        Returns:
            提取的字段值
        """
        extraction_strategy = field_def["extraction_strategy"]
        strategy_def = ontology["extraction_strategies"].get(extraction_strategy)
        reference_content = content  # 保留完整原文作为参考来源

        if not strategy_def:
            memory_pool.log(f"    警告: 未找到提取策略 '{extraction_strategy}'")
            return {"value": None, "reference": reference_content}

        # 特殊处理：分类型字段（事故等级和事故性质）
        if extraction_strategy == "classify_with_options":
            # 根据字段名称确定使用哪个选项列表
            if field_name == "事故等级":
                options = InformationExtractor.ACCIDENT_LEVEL_OPTIONS
            elif field_name == "事故性质":
                options = InformationExtractor.ACCIDENT_NATURE_OPTIONS
            else:
                # 如果字段定义中有选项列表，使用它
                options = field_def.get("options", [])

            if options:
                result = InformationExtractor._classify_with_options(content, field_name, options, memory_pool)
            else:
                memory_pool.log(f"    警告: 分类字段 '{field_name}' 没有定义选项列表")
                result = ""
            return {"value": result, "reference": reference_content}

        # 特殊处理：责任人员（需要综合人员伤亡情况和责任认定两部分）
        if field_name == "责任人员":
            result = InformationExtractor._extract_responsible_persons(memory_pool, ontology)
            return {"value": result, "reference": reference_content}

        # 检查是否需要跨chunk提取
        if "source_categories" in field_def:
            source_categories = field_def["source_categories"]
            memory_pool.log(f"    跨chunk提取，源类别: {', '.join(source_categories)}")
            content = InformationExtractor._collect_cross_chunk_content(source_categories, memory_pool)
            reference_content = content
            if not content:
                memory_pool.log(f"    警告: 未收集到任何内容")
                # 返回默认值
                if field_def["type"] == "array":
                    default_value = []
                elif field_def["type"] in ["object", "text"]:
                    default_value = {}
                else:
                    default_value = ""
                return {"value": default_value, "reference": reference_content}

        # 构建 prompt
        prompt_template = strategy_def["prompt_template"]

        # 处理 schema（如果有）
        schema_str = ""
        if "subfields" in field_def:
            schema_str = json.dumps(field_def["subfields"], ensure_ascii=False, indent=2)
        elif "item_schema" in field_def:
            schema_str = json.dumps(field_def["item_schema"], ensure_ascii=False, indent=2)

        # 添加字段说明（如果有）
        field_description = ""
        if "description" in field_def:
            field_description = f"\n【字段说明】{field_def['description']}\n"

        prompt = prompt_template.format(
            field_name=field_name,
            content=content[:15000],  # 增加内容长度限制以支持跨chunk
            schema=schema_str
        )

        # 将字段说明插入到 prompt 开头
        if field_description:
            prompt = field_description + prompt

        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": "你是专业的信息提取助手。严格复制原文内容，不要改写或总结。只返回提取结果，不要添加解释。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,  # 温度设为0，确保一致性
                max_tokens=2000
            )

            result_str = response.choices[0].message.content.strip()

            # 根据字段类型解析结果
            field_type = field_def["type"]

            if field_type in ["array", "object"]:
                # 尝试解析 JSON
                try:
                    result = json.loads(result_str)
                except json.JSONDecodeError:
                    # 尝试提取 JSON 部分
                    code_block_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', result_str, re.DOTALL)
                    if code_block_match:
                        result = json.loads(code_block_match.group(1))
                    else:
                        json_match = re.search(r'[\[\{].*[\]\}]', result_str, re.DOTALL)
                        if json_match:
                            result = json.loads(json_match.group())
                        else:
                            memory_pool.log(f"    警告: 无法解析JSON结果")
                            result = [] if field_type == "array" else {}
            else:
                # 字符串或文本类型
                result = result_str

            return {"value": result, "reference": reference_content}

        except Exception as e:
            memory_pool.log(f"    错误: 提取失败 - {e}")
            # 返回默认值
            if field_def["type"] == "array":
                default_value = []
            elif field_def["type"] == "object":
                default_value = {}
            else:
                default_value = ""
            return {"value": default_value, "reference": reference_content}


# ═══════════════════════════════════════════════════════════════════════════
#                   5️⃣ OntologySerializer (序列化器)
# ═══════════════════════════════════════════════════════════════════════════

class OntologySerializer:
    """
    序列化器：按本体论结构组织数据并序列化为 JSON

    输入: 提取的数据
    输出: 符合本体论结构的 JSON 文件
    """

    @staticmethod
    def serialize(memory_pool: MemoryPool, output_path: str):
        """
        序列化为 JSON

        Args:
            memory_pool: 记忆池
            output_path: 输出路径
        """
        memory_pool.log("OntologySerializer: 开始序列化数据")

        extracted_data = memory_pool.get("extracted_data")
        ontology = memory_pool.get("ontology")
        document_path = memory_pool.get("document_path")

        # 构建最终的 JSON 结构
        final_json = {
            "_metadata": {
                "本体论版本": ontology["ontology_metadata"]["version"],
                "本体论名称": ontology["ontology_metadata"]["name"],
                "源文档": str(document_path),
                "处理时间": datetime.now().isoformat(),
                "处理器": "OntologyAgent v1.0"
            }
        }

        # 按本体论的优先级顺序组织数据
        ontology_structure = ontology["ontology_structure"]
        sorted_categories = sorted(
            ontology_structure.items(),
            key=lambda x: x[1]["priority"]
        )

        for category_name, category_def in sorted_categories:
            if category_name in extracted_data:
                final_json[category_name] = extracted_data[category_name]
            else:
                # 如果没有提取到，创建空结构
                final_json[category_name] = {}

        # 保存为 JSON 文件
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(final_json, f, ensure_ascii=False, indent=2)

        memory_pool.log(f"OntologySerializer: 已保存到 {output_path}")


# ═══════════════════════════════════════════════════════════════════════════
#                       OntologyAgent (主控制器)
# ═══════════════════════════════════════════════════════════════════════════

class OntologyAgent:
    """
    本体论驱动的事故报告处理 Agent

    主流程：
    1. 加载本体论
    2. 提取标题层级
    3. LLM 规划拆分方案
    4. 执行文档拆分
    5. 提取信息
    6. 序列化为 JSON
    """

    def __init__(self, ontology_path: str):
        """
        初始化 Agent

        Args:
            ontology_path: 本体论文件路径
        """
        self.ontology_path = Path(ontology_path)
        self.ontology = self._load_ontology()

    def _load_ontology(self) -> Dict:
        """加载本体论"""
        print(f"\n📖 加载本体论: {self.ontology_path}")
        with open(self.ontology_path, 'r', encoding='utf-8') as f:
            ontology = json.load(f)
        print(f"   版本: {ontology['ontology_metadata']['version']}")
        print(f"   名称: {ontology['ontology_metadata']['name']}")
        print(f"   类别数: {len(ontology['ontology_structure'])}")
        return ontology

    def process_document(self, md_file_path: str, output_dir: str) -> Dict:
        """
        处理单个文档

        Args:
            md_file_path: Markdown 文件路径
            output_dir: 输出目录

        Returns:
            处理结果
        """
        md_path = Path(md_file_path)
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True, parents=True)

        print(f"\n{'='*80}")
        print(f"处理文档: {md_path.name}")
        print(f"{'='*80}")

        # 初始化记忆池
        memory_pool = MemoryPool()
        memory_pool.set("document_path", md_path)
        memory_pool.set("ontology", self.ontology)

        try:
            # 读取文档
            memory_pool.log("读取文档内容")
            with open(md_path, 'r', encoding='utf-8', errors='ignore') as f:
                md_content = f.read()
            memory_pool.set("document_content", md_content)
            print(f"   文档大小: {len(md_content):,} 字符")

            # 1️⃣ 提取标题层级
            print(f"\n1️⃣  提取标题层级")
            headers = HeaderExtractor.extract(md_content, memory_pool)
            print(f"   ✓ 提取到 {len(headers)} 个标题")

            # 2️⃣ LLM 规划拆分方案
            print(f"\n2️⃣  LLM 规划拆分方案")
            split_plan = SplitPlanner.plan(memory_pool)
            print(f"   ✓ 生成 {len(split_plan)} 个拆分chunk")

            # 3️⃣ 执行文档拆分
            print(f"\n3️⃣  执行文档拆分")
            chunks = DocumentSplitter.split(memory_pool)
            print(f"   ✓ 拆分完成，共 {len(chunks)} 个chunk")
            for chunk in chunks:
                print(f"      - {chunk['chunk_id']}: {chunk['char_count']:,} 字符")

            # 4️⃣ 提取信息
            print(f"\n4️⃣  提取信息 (严格复制原文)")
            extracted_data = InformationExtractor.extract(memory_pool)
            print(f"   ✓ 提取完成，共 {len(extracted_data)} 个类别")

            # 5️⃣ 序列化为 JSON
            print(f"\n5️⃣  序列化为 JSON")
            json_output_path = output_path / f"{md_path.stem}_ontology.json"
            OntologySerializer.serialize(memory_pool, str(json_output_path))
            print(f"   ✓ 保存到: {json_output_path.name}")

            # stats: count source chars and output value chars (skip reference)
            def _sum_value_len(obj):
                if isinstance(obj, dict):
                    total = 0
                    if "value" in obj:
                        total += _sum_value_len(obj["value"])
                    for k, v in obj.items():
                        if k in ("value", "reference"):
                            continue
                        total += _sum_value_len(v)
                    return total
                if isinstance(obj, list):
                    return sum(_sum_value_len(x) for x in obj)
                if isinstance(obj, str):
                    return len(obj)
                return 0

            try:
                src_len = len(md_path.read_text(encoding="utf-8"))
                output_data = json.load(open(json_output_path, encoding="utf-8"))
                payload = {k: v for k, v in output_data.items() if k != "_metadata"}
                value_len = _sum_value_len(payload)
                print(f"   stats: src_chars={src_len}, output_value_chars={value_len}")
            except Exception as e:
                print(f"   stats calculation failed: {e}")

            # 保存记忆池（用于调试）
            memory_output_path = output_path / f"{md_path.stem}_memory.json"
            memory_pool.save_memory(str(memory_output_path))
            print(f"   ✓ 记忆池已保存: {memory_output_path.name}")

            print(f"\n{'='*80}")
            print(f"✓ 处理完成")
            print(f"{'='*80}")

            return {
                "success": True,
                "document": str(md_path),
                "output": str(json_output_path)
            }

        except Exception as e:
            memory_pool.log(f"处理失败: {e}")
            print(f"\n✗ 处理失败: {e}")
            import traceback
            traceback.print_exc()

            return {
                "success": False,
                "document": str(md_path),
                "error": str(e)
            }

    def process_all_documents(self, dataset_dir: str, output_dir: str):
        """
        批量处理 Dataset 目录下的所有文档

        Args:
            dataset_dir: Dataset 目录路径
            output_dir: 输出目录
        """
        dataset_path = Path(dataset_dir)
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True, parents=True)

        print(f"\n{'='*80}")
        print(f"批量处理文档")
        print(f"{'='*80}")
        print(f"Dataset目录: {dataset_path}")
        print(f"输出目录: {output_path}")

        # 获取所有文档文件夹
        doc_folders = [f for f in dataset_path.iterdir() if f.is_dir()]
        print(f"找到 {len(doc_folders)} 个文档文件夹")
        print(f"{'='*80}")

        results = []
        success_count = 0
        fail_count = 0

        for i, doc_folder in enumerate(doc_folders, 1):
            print(f"\n[{i}/{len(doc_folders)}]")

            # 查找 md 文件
            md_files = [f for f in doc_folder.glob("*.md") if f.name.lower() != "readme.md"]

            if not md_files:
                print(f"  ✗ 未找到 markdown 文件")
                fail_count += 1
                continue

            md_file = md_files[0]

            # 处理文档
            result = self.process_document(str(md_file), str(output_path))
            results.append(result)

            if result["success"]:
                success_count += 1
            else:
                fail_count += 1

        # 保存汇总结果
        summary_path = output_path / "_processing_summary.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        print(f"\n{'='*80}")
        print(f"批量处理完成")
        print(f"{'='*80}")
        print(f"  成功: {success_count} 个")
        print(f"  失败: {fail_count} 个")
        print(f"  汇总文件: {summary_path.name}")
        print(f"{'='*80}")


# ═══════════════════════════════════════════════════════════════════════════
#                               主程序
# ═══════════════════════════════════════════════════════════════════════════

def main():
    """主程序入口"""

    # 配置路径
    ONTOLOGY_PATH = r"C:\Users\Qzj\Desktop\projrct\MinerU\ontology_v2.json"
    DATASET_DIR = r"C:\Users\Qzj\Desktop\projrct\MinerU\Dataset"
    OUTPUT_DIR = r"C:\Users\Qzj\Desktop\projrct\MinerU\ontology_output_v2"

    # 创建 Agent
    agent = OntologyAgent(ontology_path=ONTOLOGY_PATH)

    # 批量处理所有文档
    agent.process_all_documents(dataset_dir=DATASET_DIR, output_dir=OUTPUT_DIR)


if __name__ == "__main__":
    main()
