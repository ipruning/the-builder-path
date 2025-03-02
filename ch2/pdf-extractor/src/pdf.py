"""
## Changelog

- [001] - [refactor] - Replaced logfire with Python's standard logging module
"""

import logging
import os
import tempfile
from typing import Any, List, Tuple

import fitz
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)

DEFAULT_PROMPT = """
请尽可能提取 PDF 中的信息，并遵守以下规则：

- 你会从 ### 开始标题。
- 你不会滥用 **。
- 你不会用代码块 ```markdown``` 包裹信息。
- 你会用自然语言描述图片。
- 你会用 mermaid 来精确的提取图表中的信息。在 ```mermaid``` 中记得擅用 <br> 来调整布局。
- 你会用 markdown 来精确提取表格的信息。

你会在深度思考任务后直接输出提取的信息。
"""


class PDFProcessor:
    def __init__(self):
        self.client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        self.model_id = "gemini-2.0-flash-thinking-exp-01-21"
        self.max_tokens = 65536
        self.chunk_size = 5

    def _create_temp_pdf(self, doc: fitz.Document, start: int, end: int) -> str:
        temp_chunk = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        new_doc = fitz.open()

        # end is exclusive in fitz, so we don't need to subtract 1
        new_doc.insert_pdf(doc, from_page=start, to_page=end)
        new_doc.save(temp_chunk.name)
        new_doc.close()
        return temp_chunk.name

    def split_pdf(self, pdf_file: Any) -> List[Tuple[str, int, int]]:
        temp_input = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        temp_input.write(pdf_file.read())
        temp_input.close()

        doc = fitz.open(temp_input.name)
        total_pages = len(doc)
        chunks = []

        for start in range(0, total_pages, self.chunk_size):
            end = min(start + self.chunk_size, total_pages)
            temp_path = self._create_temp_pdf(doc, start, end)

            # end - 1 because we want inclusive end page number for logging
            chunks.append((temp_path, start, end - 1))

        doc.close()
        os.remove(temp_input.name)

        return chunks

    async def process_pdf_chunk(self, temp_pdf_path: str, start_page: int, end_page: int, prompt: str) -> str:
        try:
            async_client = self.client.aio
            upload_config = types.UploadFileConfig(mime_type="application/pdf")

            with open(temp_pdf_path, "rb") as f:
                uploaded_file = await async_client.files.upload(file=f, config=upload_config)

            logger.info(f"PDF - processing {start_page + 1}-{end_page + 1}")
            response = await async_client.models.generate_content(
                model=self.model_id,
                config=types.GenerateContentConfig(
                    system_instruction=prompt,
                    max_output_tokens=self.max_tokens,
                ),
                contents=[uploaded_file],
            )

            if not response.text:
                raise Exception("Model IS RETURNING EMPTY RESPONSE")

            logger.info(f"PDF - {start_page + 1}-{end_page + 1} - {len(response.text)} characters")

            return response.text

        except Exception as e:
            logger.error(f"PDF - {start_page + 1}-{end_page + 1} - {str(e)}")
            return f"PDF - {start_page + 1}-{end_page + 1} - {str(e)}"

        finally:
            if os.path.exists(temp_pdf_path):
                os.remove(temp_pdf_path)

    async def extract(self, pdf_file: Any, prompt: str = DEFAULT_PROMPT) -> str:
        chunks = self.split_pdf(pdf_file)
        results = []

        for temp_path, start, end in chunks:
            chunk_result = await self.process_pdf_chunk(temp_path, start, end, prompt)
            if chunk_result.strip():
                results.append(chunk_result)

        if not results:
            logger.error("PDF - failed")
            return "PDF - failed"

        logger.info(f"PDF - {len(chunks)} chunks / {len(results)} processed")

        return "\n\n---\n\n".join(results)
