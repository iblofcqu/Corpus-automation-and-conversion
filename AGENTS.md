# AI 工具项目导航

> 本文档为 AI 编程工具提供项目结构、关键组件位置和开发规范的快速索引。

## 项目概览

事故调查报告智能处理系统，将 PDF 格式的事故报告转换为结构化的本体论 JSON 数据。

**核心流程**: PDF → Markdown → 层级重组 → 本体论驱动信息提取 → 结构化 JSON

**技术特点**: 本体论驱动、严格原文复制（定位和复制，而非理解和改写）、LLM 辅助提取

## Python 版本和技术栈

- **Python 版本**: 3.11+（必需）
- **PDF 解析**: MinerU
- **LLM 服务**: DeepSeek API（deepseek-chat 模型）
- **依赖管理**: requirements.txt
- **代码质量**: ruff（配置在 pyproject.toml）

## 工作流程和入口文件

5 步处理管道，按顺序执行：

| 步骤   | 文件                                                                  | 职责                                     | LLM |
| ------ | --------------------------------------------------------------------- | ---------------------------------------- | --- |
| Step 1 | [Step1_batch_word2pdf.py](Step1_batch_word2pdf.py)                       | Word 转 PDF 批处理                       | ❌  |
| Step 2 | [Step2_batch_pdf_converter.py](Step2_batch_pdf_converter.py)             | PDF 转 Markdown（MinerU）                | ✅  |
| Step 3 | [Step3_organize_by_headings_llm.py](Step3_organize_by_headings_llm.py)   | 智能标题层级重组                         | ❌  |
| Step 4 | [Step4_rewrite_markdown_headings.py](Step4_rewrite_markdown_headings.py) | 可选的标题重写                           | ❌  |
| Step 5 | [Step5_ontology_agent_v2.py](Step5_ontology_agent_v2.py)                 | **核心 Agent：本体论驱动信息提取** | ✅  |

## 关键组件位置

### 核心 Agent 系统

**文件**: [Step5_ontology_agent_v2.py](Step5_ontology_agent_v2.py)

**主要类**:

- `OntologyAgent`: 主 Agent 类，协调整个提取流程
- `HeadingExtractor`: 提取 Markdown 标题层级
- `SplitPlanner`: LLM 驱动的文档拆分规划
- `ContentSplitter`: 执行文档切分
- `InformationExtractor`: LLM 驱动的结构化信息提取（8 种提取策略）
- `ResultSerializer`: 序列化为 JSON
- `MemoryPool`: 记忆池，跨模块数据传递和日志记录

**提取策略**（InformationExtractor 实现）:

- `copy_exact`: 精确复制字段值
- `copy_section`: 复制整段内容
- `list_extract`: 逐条复制列表
- `structured_extract`: 按 schema 复制对象
- `structured_list_extract`: 按 schema 复制列表
- `cross_chunk_summarize`: 跨 chunk 综合总结
- `cross_chunk_list_extract`: 跨 chunk 列表提取
- `classify_with_options`: 从预定义选项中分类选择

### 本体论定义

**文件**: [ontology_v2.json](ontology_v2.json)

定义事故报告的标准分析框架，包含 6 大类别：

1. 报告元信息
2. 事故基本情况
3. 事故经过与性质
4. 人员伤亡情况
5. 事故原因分析
6. 责任认定

每个字段指定：提取策略、优先级、关键词、子字段结构等。

### LLM 集成位置

**Step 3**: [Step3_organize_by_headings_llm.py](Step3_organize_by_headings_llm.py)

- 第 93-98 行：DeepSeek API 配置
- 第 208-306 行：Chain of Thought 标题层级分析

**Step 5**: [Step5_ontology_agent_v2.py](Step5_ontology_agent_v2.py)

- 第 89-94 行：DeepSeek API 配置
- 第 418 行：拆分规划 LLM 调用
- 第 606 行：字段提取 LLM 调用
- 第 671 行：分类提取 LLM 调用
- 第 885 行：跨 chunk 提取 LLM 调用

## 开发规范

### 第三方库添加

通过在`requirements.txt` 中添加, 再安装的方式, 更新库的依赖. 不能直接pip install 第三方库.

### 代码质量要求

✅ **必须满足**（适用于新增和修改的代码）:

- 使用完整的 Python type hints（函数参数、返回值、类属性）
- 通过 ruff 检测（配置在 pyproject.toml，包含 PEP 8 规范）
- 保持既有代码不改动的原则（除非明确要求重构）

❌ **不强制要求**:

- docstring（可选）

### 测试要求

- 通过 Django 单元测试执行（后续集成后台服务时）

### 核心设计原则

**本体论驱动的"严格原文复制"**:

- 定位和复制原文，而非理解和改写
- 所有提取结果必须来自原文，不允许 LLM 生成或改写
- 提取策略的选择基于本体论定义

## 文档索引

详细设计文档位于 [docs/](docs/) 目录：

- [docs/01_需求分析.md](docs/01_需求分析.md): 业务需求和功能目标
- [docs/02_概要设计.md](docs/02_概要设计.md): 系统架构和技术选型
- [docs/03_详细设计.md](docs/03_详细设计.md): Django 后台服务设计（规划中）
- [docs/04_部署运维.md](docs/04_部署运维.md): 部署方案和运维策略

## 快速定位指南

AI 工具执行常见任务的文件映射：

### 修改提取逻辑

| 任务            | 目标文件                                              | 位置                                       |
| --------------- | ----------------------------------------------------- | ------------------------------------------ |
| 修改提取策略    | [Step5_ontology_agent_v2.py](Step5_ontology_agent_v2.py) | `InformationExtractor` 类的各个提取方法  |
| 添加新提取策略  | [Step5_ontology_agent_v2.py](Step5_ontology_agent_v2.py) | `InformationExtractor` 类中添加新方法    |
| 修改拆分逻辑    | [Step5_ontology_agent_v2.py](Step5_ontology_agent_v2.py) | `SplitPlanner` 和 `ContentSplitter` 类 |
| 修改 LLM Prompt | [Step5_ontology_agent_v2.py](Step5_ontology_agent_v2.py) | 各 LLM 调用处的 prompt 字符串              |

### 修改本体论定义

| 任务           | 目标文件                          | 说明                         |
| -------------- | --------------------------------- | ---------------------------- |
| 添加/删除字段  | [ontology_v2.json](ontology_v2.json) | 修改 JSON 结构，指定提取策略 |
| 调整字段优先级 | [ontology_v2.json](ontology_v2.json) | 修改字段的 `priority` 值   |
| 添加关键词     | [ontology_v2.json](ontology_v2.json) | 修改字段的 `keywords` 数组 |

### 修改标题重组逻辑

| 任务                | 目标文件                                                            | 位置                                             |
| ------------------- | ------------------------------------------------------------------- | ------------------------------------------------ |
| 修改层级分析 Prompt | [Step3_organize_by_headings_llm.py](Step3_organize_by_headings_llm.py) | `analyze_heading_levels_chain_of_thought` 函数 |
| 修改层级应用规则    | [Step3_organize_by_headings_llm.py](Step3_organize_by_headings_llm.py) | `apply_heading_levels` 函数                    |

### 调试和追溯

| 任务           | 位置                                         | 说明                                 |
| -------------- | -------------------------------------------- | ------------------------------------ |
| 查看记忆池日志 | [data/ontology/](data/ontology/)*_memory.json   | 记录处理日志、中间结果、LLM 调用详情 |
| 查看本体论输出 | [data/ontology/](data/ontology/)*_ontology.json | 最终的结构化 JSON 结果               |

## 数据路径约定

```
data/
├── input/           # 输入文件（PDF 或 Word）
├── output/          # 各步骤输出（Markdown、JSON 等）
│   └── {文档名称}_{时间戳}/
│       ├── auto/    # MinerU 自动模式输出
│       └── ocr/     # MinerU OCR 模式输出
└── ontology/        # 本体论提取结果
    ├── {文档名称}_ontology.json  # 结构化本体论数据
    ├── {文档名称}_memory.json    # 记忆池调试日志
    └── _processing_summary.json  # 批量处理摘要
```

## 项目状态

- ✅ **已实现**: Step1-5 处理管道、OntologyAgent 系统、本体论定义
- 📝 **规划中**: Django REST API 后台服务（参见 [docs/03_详细设计.md](docs/03_详细设计.md)）
- ⏳ **待创建**: pyproject.toml（ruff 配置）、Django 单元测试

---

**最后更新**: 2026-01-20
