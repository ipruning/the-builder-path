"""
## ChangeLog

- 001 - AI - Added support for multiple API keys with fallback mechanism
- 002 - AI - Implemented concurrent processing of PDF chunks
- 003 - AI - Modified to ensure results are concatenated in the correct page order
- 004 - AI - Improved to maintain both concurrency and correct result ordering
- 005 - AI - Changed API key logging to show last 8 characters instead of first 5
- 006 - AI - Added short delay before retrying with next API key
- 007 - AI - Added timeout mechanism for individual chunk processing
- 008 - AI - Fixed chunk ordering issue by properly tracking task results with their original indices
"""

import asyncio
import os
import random
import tempfile
from typing import Any, AsyncGenerator, Dict, List, Tuple, Union

import fitz
import logfire
from google import genai
from google.genai import types

DEFAULT_PROMPT_CN = """
请尽可能提取 PDF 中的信息，并遵守以下规则：

- 你会从 ### 开始标题。
- 你不会滥用 **。
- 你不会用代码块 ```markdown``` 包裹信息。
- 你会用自然语言描述图片。
- 你会用 mermaid 来精确的提取图表中的信息。在 ```mermaid``` 中记得擅用 <br> 来调整布局。
- 你会用 markdown 来精确提取表格的信息。

你会在深度思考任务后直接输出提取的信息。
"""

DEFAULT_PROMPT_EN = """
Please extract information from the PDF as much as possible while adhering to the following rules:

- You will start the title with ###.
- You will not misuse **.
- You will not enclose information in code blocks ```markdown```.
- You will describe images in natural language.
- You will use mermaid to accurately extract information from charts. Remember to use <br> wisely within ```mermaid``` for layout adjustments.
- You will use markdown to precisely extract information from tables.
You will directly output the extracted information after deeply contemplating the task.
"""


class PDFProcessor:
    def __init__(self):
        self.api_keys = self._collect_api_keys()
        self.clients = self._initialize_clients()
        self.model_id = "gemini-2.0-flash-thinking-exp-01-21"
        self.max_tokens = 60000
        self.chunk_size = 2
        self.max_concurrent_tasks = max(int(len(self.api_keys) * 1.6), 1)
        self.semaphore = asyncio.Semaphore(self.max_concurrent_tasks)
        self.chunk_timeout_s = 180
        self.api_call_timeout_s = 60

    def _collect_api_keys(self) -> List[str]:
        keys = []

        default_key = os.environ.get("GEMINI_API_KEY")
        if default_key:
            keys.append(default_key)

        key_prefixes = [k for k in os.environ.keys() if k.startswith("GEMINI_API_KEY_")]

        for prefix in key_prefixes:
            key = os.environ.get(prefix)
            if key and key not in keys:
                keys.append(key)

        if not keys:
            raise ValueError("No Gemini API keys found in environment variables")

        return keys

    def _initialize_clients(self) -> Dict[str, genai.Client]:
        return {key: genai.Client(api_key=key) for key in self.api_keys}

    def _create_temp_pdf(self, doc: fitz.Document, start: int, end: int) -> str:
        temp_chunk = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        new_doc = fitz.open()

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

    async def _process_with_fallback(self, temp_pdf_path: str, start_page: int, end_page: int, prompt: str) -> str:
        available_keys = list(self.api_keys)
        random.shuffle(available_keys)

        retry_delay_s = 0.5
        max_retry_delay_s = 5.0

        for i, api_key in enumerate(available_keys):
            try:
                client = self.clients[api_key]
                async_client = client.aio
                upload_config = types.UploadFileConfig(mime_type="application/pdf")

                with open(temp_pdf_path, "rb") as f:
                    try:
                        upload_task = async_client.files.upload(file=f, config=upload_config)
                        uploaded_file = await asyncio.wait_for(upload_task, timeout=self.api_call_timeout_s)
                    except asyncio.TimeoutError:
                        logfire.warn(f"File upload timed out for pages {start_page}-{end_page}")
                        if i < len(available_keys) - 1:
                            await asyncio.sleep(retry_delay_s)
                            retry_delay_s = min(retry_delay_s * 1.5, max_retry_delay_s)
                        continue

                with logfire.span(f"Processing pages {start_page}-{end_page}"):
                    try:
                        generate_task = async_client.models.generate_content(
                            model=self.model_id,
                            config=types.GenerateContentConfig(
                                system_instruction=prompt,
                                max_output_tokens=self.max_tokens,
                            ),
                            contents=[uploaded_file],
                        )
                        response = await asyncio.wait_for(generate_task, timeout=self.api_call_timeout_s)
                    except asyncio.TimeoutError:
                        logfire.warn(f"Content generation timed out for pages {start_page}-{end_page}")
                        if i < len(available_keys) - 1:
                            await asyncio.sleep(retry_delay_s)
                            retry_delay_s = min(retry_delay_s * 1.5, max_retry_delay_s)
                        continue

                    if not response.text:
                        logfire.warn(f"Received empty response from API for pages {start_page}-{end_page}")
                        if i < len(available_keys) - 1:
                            await asyncio.sleep(retry_delay_s)
                            retry_delay_s = min(retry_delay_s * 1.5, max_retry_delay_s)
                        continue

                    logfire.info(
                        f"Successfully processed pages {start_page}-{end_page} with {len(response.text)} characters"
                    )
                    return response.text

            except Exception:
                logfire.warn(f"Failed to process pages {start_page}-{end_page}")
                if i < len(available_keys) - 1:
                    await asyncio.sleep(retry_delay_s)
                    retry_delay_s = min(retry_delay_s * 1.5, max_retry_delay_s)
                continue

        logfire.error(f"Processing failed with all API keys for pages {start_page}-{end_page}")
        return "All API Keys Failed"

    async def process_pdf_chunk(self, temp_pdf_path: str, start_page: int, end_page: int, prompt: str) -> str:
        try:
            async with self.semaphore:
                try:
                    result = await asyncio.wait_for(
                        self._process_with_fallback(temp_pdf_path, start_page, end_page, prompt),
                        timeout=self.chunk_timeout_s,
                    )
                    return result
                except asyncio.TimeoutError:
                    logfire.error(f"PDF chunk processing timed out for pages {start_page}-{end_page}")
                    return "Processing timeout"
        finally:
            if os.path.exists(temp_pdf_path):
                os.remove(temp_pdf_path)

    async def extract(self, pdf_file: Any, prompt) -> AsyncGenerator[Union[int, str], None]:
        chunks = self.split_pdf(pdf_file)
        total_chunks = len(chunks)

        # Create tasks and store them with their indices
        pending_tasks = {}
        for i, (temp_path, start, end) in enumerate(chunks):
            task = asyncio.create_task(self.process_pdf_chunk(temp_path, start, end, prompt))
            pending_tasks[task] = i

        results_by_index = {}
        completed_chunks = 0

        # Process tasks as they complete
        while pending_tasks:
            done, _ = await asyncio.wait(pending_tasks.keys(), return_when=asyncio.FIRST_COMPLETED)

            for task in done:
                # Get the original index for this task
                original_index = pending_tasks.pop(task)

                try:
                    result = task.result()
                    # Store result with its original index
                    results_by_index[original_index] = result
                except Exception as e:
                    logfire.error(f"Task error: {e}")
                    results_by_index[original_index] = f"Processing error: {str(e)}"

                completed_chunks += 1
                progress = int((completed_chunks / total_chunks) * 100)

                # Log progress
                logfire.info(f"Processing progress: {progress}% ({completed_chunks}/{total_chunks} chunks)")
                yield progress

        # Get results in the original order
        ordered_results = [
            results_by_index[i]
            for i in range(total_chunks)
            if i in results_by_index and results_by_index[i] and results_by_index[i].strip()
        ]

        if not ordered_results:
            logfire.error(f"PDF processing failed completely. Total chunks: {len(ordered_results)}/{len(chunks)}")
            yield "Processing failed completely"
        else:
            yield "\n\n---\n\n".join(ordered_results)
