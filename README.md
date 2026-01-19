# MinerU Ontology Extraction Pipeline

This project turns accident investigation reports into structured ontology JSON.
It focuses on two core functions:
1) PDF to text (MinerU parsing)
2) Ontology extraction from Markdown (LLM-driven)

## Features
- PDF to text: batch or single-file parsing with MinerU.
- Ontology extraction: LLM plans document splitting and extracts fields using `ontology_v2.json`.

## Install
```bash
pip install -r requirements.txt
```

If you want MinerU from the local source, use the editable install already listed in `requirements.txt`:
```bash
pip install -e ./MinerU-master
```

## Configuration
- Step3 uses `DEEPSEEK_API_KEY` (environment variable).
- Step5 uses constants in `Step5_ontology_agent_v2.py`: `API_KEY`, `MODEL`, `BASE_URL`.

## Usage

### 1) PDF to Text (MinerU)

Command line:
```bash
python Step2_batch_pdf_converter.py -p "C:\\path\\to\\pdf_or_images" -o "C:\\path\\to\\output"
```

Python import (single file or directory):
```python
from Step2_batch_pdf_converter import batch_convert_pdfs

batch_convert_pdfs(
    input_path=r"C:\\path\\to\\pdf_or_images",
    output_dir=r"C:\\path\\to\\output",
    backend="pipeline",
    method="auto",
    lang="ch"
)
```

Output: the `output_dir` will contain MinerU parsing results (Markdown, images, and metadata).

### 2) Ontology Extraction (LLM)

Input: a Dataset folder where each document has a Markdown file. You can build it via:
- Step3 (`Step3_organize_by_headings_llm.py`) to create `Dataset/` from MinerU output
- Or place your own Markdown into `Dataset/<doc>/` manually

Command line (batch, default paths in code):
```bash
python Step5_ontology_agent_v2.py
```

Python import (single document):
```python
from Step5_ontology_agent_v2 import OntologyAgent

agent = OntologyAgent(ontology_path=r"C:\\path\\to\\ontology_v2.json")
result = agent.process_document(
    md_file_path=r"C:\\path\\to\\Dataset\\Doc1\\Doc1.md",
    output_dir=r"C:\\path\\to\\ontology_output_v2"
)
print(result)
```

Python import (batch):
```python
from Step5_ontology_agent_v2 import OntologyAgent

agent = OntologyAgent(ontology_path=r"C:\\path\\to\\ontology_v2.json")
agent.process_all_documents(
    dataset_dir=r"C:\\path\\to\\Dataset",
    output_dir=r"C:\\path\\to\\ontology_output_v2"
)
```

Output:
- `<name>_ontology.json`: structured ontology data
- `<name>_memory.json`: split plan, chunks, and processing log (debug)

## Notes on Extraction Logic
- Step5 groups chunks by ontology category and feeds all related content to the LLM.
- Long content is split into segments; each segment is processed sequentially and merged.
- `source_categories` in the ontology lets a field pull content from other categories.

## Suggested Workflow
1) (Optional) Word to PDF: `Step1_batch_word2pdf.py`
2) PDF to text: `Step2_batch_pdf_converter.py`
3) Build Dataset with LLM heading hierarchy: `Step3_organize_by_headings_llm.py`
4) (Optional) Rewrite headings: `Step4_rewrite_markdown_headings.py`
5) Ontology extraction: `Step5_ontology_agent_v2.py`
