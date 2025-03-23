"""
## ChangeLog

- 001 - AI - Created FastHTML application for PDF extraction and URL processing
- 002 - AI - Added file upload, URL extraction, and result display functionality
- 003 - AI - Integrated PDFProcessor component
- 004 - AI - Fixed linter errors by giving unique names to route handlers
- 005 - AI - Added language selection for PDF extraction (Chinese and English)
- 006 - AI - Improved user experience by separating file upload from processing
- 007 - AI - Simplified request/response models by removing PDFUploadResponse
- 008 - AI - Improved file handling and button state management
"""

import asyncio
import os
import time
import urllib.parse
import uuid
from enum import Enum
from tempfile import NamedTemporaryFile
from typing import Dict, Optional

import logfire
from fasthtml.common import *
from pydantic import BaseModel, Field

from reader.config import configure_logfire
from reader.pdf import DEFAULT_PROMPT_CN, DEFAULT_PROMPT_EN, PDFProcessor


class TaskStatus(Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


class Task(BaseModel):
    status: TaskStatus = Field(default=TaskStatus.PROCESSING)
    original_filename: str
    temp_filename: str
    result: Optional[str] = None
    error: Optional[str] = None
    progress: int = Field(default=0)


class PDFRequest(BaseModel):
    temp_filename: str
    original_filename: str
    language: str = Field(default="cn", pattern="^(cn|en)$")


class TaskManager:
    def __init__(self):
        self.tasks: Dict[str, Task] = {}

    def add_task(self, task_id: str, original_filename: str, temp_filename: str) -> Task:
        # Clean up previous temp file if it exists
        if task_id in self.tasks and os.path.exists(self.tasks[task_id].temp_filename):
            try:
                os.remove(self.tasks[task_id].temp_filename)
            except Exception as e:
                logfire.error(f"Failed to remove old temp file: {str(e)}")

        task = Task(original_filename=original_filename, temp_filename=temp_filename, progress=0)
        self.tasks[task_id] = task
        return task

    def update_progress(self, task_id: str, progress: int) -> None:
        if task_id in self.tasks:
            self.tasks[task_id].progress = progress

    def set_completed(self, task_id: str, result: str) -> None:
        if task_id in self.tasks:
            self.tasks[task_id].status = TaskStatus.COMPLETED
            self.tasks[task_id].result = result
            self.tasks[task_id].progress = 100

    def set_error(self, task_id: str, error: str) -> None:
        if task_id in self.tasks:
            self.tasks[task_id].status = TaskStatus.ERROR
            self.tasks[task_id].error = error

    def get_task(self, task_id: str) -> Optional[Task]:
        return self.tasks.get(task_id)

    def is_processing(self, temp_filename: str) -> bool:
        return any(
            task.status == TaskStatus.PROCESSING and task.temp_filename == temp_filename for task in self.tasks.values()
        )


configure_logfire()

task_manager = TaskManager()


def get_version() -> str:
    return str(int(time.time()))


app, rt = fast_app(
    title="Reader",
    pico=True,
    debug=True,
    hdrs=(
        Link(rel="stylesheet", href=f"/static/css/styles.css?v={get_version()}", type="text/css"),
        Script(src=f"/static/js/file-input.js?v={get_version()}"),
        Script(src=f"/static/js/clipboard.js?v={get_version()}"),
    ),
)


@rt("/")
def home() -> FT:
    return Titled(
        "上下文助手",
        Div(
            Div(
                Form(
                    Div(
                        Label("选择文件", for_="pdf_file", cls="form-label"),
                        Div(
                            Label(
                                "PDF",
                                Input(
                                    type="file",
                                    name="pdf_file",
                                    id="pdf_file",
                                    accept=".pdf",
                                    onchange="updateFileName(this)",
                                ),
                                cls="file-input-label",
                                for_="pdf_file",
                            ),
                            Div(id="file-name-display", cls="file-name"),
                            Div(id="upload-status", cls="upload-status"),
                            cls="file-input-container",
                        ),
                        cls="form-group",
                    ),
                    Div(
                        Label("选择语言", cls="form-label"),
                        Div(
                            Div(
                                Input(type="radio", name="language", id="lang-en", value="en"),
                                Label("英语", for_="lang-en"),
                                cls="language-option",
                            ),
                            Div(
                                Input(type="radio", name="language", id="lang-cn", value="cn", checked=True),
                                Label("中文", for_="lang-cn"),
                                cls="language-option",
                            ),
                            cls="language-selection",
                        ),
                        cls="form-group",
                    ),
                    Input(type="hidden", name="temp_filename", id="temp_filename"),
                    Div(
                        Button(
                            Div("提取", cls="button-text"),
                            type="submit",
                            cls="btn-extract",
                        ),
                        cls="form-group",
                        style="margin-top: 1rem;",
                    ),
                    hx_post="/api/pdf/extract",
                    hx_target="#results",
                    enctype="multipart/form-data",
                ),
                cls="form-section",
            ),
            Div(id="results", cls="results-section"),
        ),
    )


@rt("/api/pdf/upload")
async def upload_pdf(pdf_file: UploadFile):
    try:
        with NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(await pdf_file.read())

        return {"success": True, "temp_filename": temp_file.name, "original_filename": pdf_file.filename}
    except Exception as e:
        logfire.error(f"/api/pdf/upload: {str(e)}")
        return {"success": False, "error": str(e)}


@rt("/api/pdf/extract")
async def extract_pdf(request: PDFRequest):
    try:
        if not os.path.exists(request.temp_filename):
            return Div("Error: Temporary file not found. Please try uploading again.", cls="error")

        # Check if the file is already being processed
        if task_manager.is_processing(request.temp_filename):
            return Div(
                "Error: This file is already being processed. Please wait for the current process to complete.",
                cls="error",
            )

        encoded_temp_filename = urllib.parse.quote(request.temp_filename)
        encoded_original_filename = urllib.parse.quote(request.original_filename)
        encoded_language = urllib.parse.quote(request.language)

        return Div(
            Script("disableExtractButton();"),  # Disable the extract button
            Div(
                id="extraction-result",
                hx_get=f"/api/pdf/process?temp_filename={encoded_temp_filename}&original_filename={encoded_original_filename}&language={encoded_language}",
                hx_trigger="load",
            ),
            cls="processing-container",
        )
    except Exception as e:
        logfire.error(f"/api/pdf/extract: {str(e)}")
        return Div(f"Error: {str(e)}", cls="error")


@rt("/api/pdf/process")
async def process_pdf(request: PDFRequest):
    temp_filename = urllib.parse.unquote(request.temp_filename)
    original_filename = urllib.parse.unquote(request.original_filename)
    language = urllib.parse.unquote(request.language)

    task_id = str(uuid.uuid4())
    task_manager.add_task(task_id, original_filename, temp_filename)
    asyncio.create_task(process_pdf_background(task_id, temp_filename, original_filename, language))

    return Div(
        Script("updateProcessingStatus('Processing', 0);"),
        Div(
            id="result-container",
            hx_get=f"/api/tasks/{task_id}/status",
            hx_trigger="every 1s",
            hx_swap="outerHTML",
        ),
    )


async def process_pdf_background(
    task_id: str,
    temp_filename: str,
    original_filename: str,
    language: str = "cn",
) -> None:
    with logfire.span(f"/process-pdf: {original_filename}"):
        try:
            pdf_processor = PDFProcessor()
            prompt = DEFAULT_PROMPT_EN if language == "en" else DEFAULT_PROMPT_CN

            with open(temp_filename, "rb") as pdf_file:
                async for progress in pdf_processor.extract(pdf_file, prompt):
                    if isinstance(progress, int):
                        task_manager.update_progress(task_id, progress)
                    else:
                        task_manager.set_completed(task_id, progress)

        except Exception as e:
            logfire.error(f"/process-pdf: {str(e)}")
            task_manager.set_error(task_id, str(e))


@rt("/api/tasks/{task_id}/status")
async def check_status(task_id: str):
    task = task_manager.get_task(task_id)

    if not task:
        return Div(
            Script("enableExtractButton();"),
            Div("The task does not exist or has expired", cls="error"),
        )

    if task.status == TaskStatus.PROCESSING:
        return Div(
            Script(f"updateProcessingStatus('Processing', {task.progress});"),
            Div(
                id="result-container",
                hx_get=f"/api/tasks/{task_id}/status",
                hx_trigger="every 1s",
                hx_swap="outerHTML",
            ),
        )

    elif task.status == TaskStatus.COMPLETED:
        result = task.result
        result_id = "pdf-result-" + str(hash(result))[1:8]

        return Div(
            Script("enableExtractButton();"),
            Div(
                Button(
                    Div("复制文本", style="display: inline-flex; align-items: center; gap: 0.35rem;"),
                    id=f"copy-btn-{result_id}",
                    cls="copy-btn",
                    onclick=f"copyToClipboard('{result_id}')",
                ),
                cls="copy-btn-container",
            ),
            Div(result, id=result_id, cls="result"),
        )

    else:  # Error case
        return Div(
            Script("enableExtractButton();"),
            Div(f"ERROR at /api/tasks/{task_id}/status: {task.error}", cls="error"),
        )


@rt("/up")
def up():
    return "OK"


if __name__ == "__main__":
    serve()
