"""
## Changelog
"""

import json
from typing import Optional

import logfire
import streamlit as st
from st_copy_to_clipboard import st_copy_to_clipboard

from .jina import JinaExtractor
from .pdf import DEFAULT_PROMPT, PDFProcessor


async def render_pdf_extractor() -> None:
    with st.sidebar:
        st.header("PDF 提取配置")
        chunk_size = st.number_input(
            "分块大小",
            min_value=1,
            max_value=10,
            value=3,
            help="每个处理块包含的 PDF 页数。",
        )

    st.title("通用 PDF 信息提取器")

    st.caption("""\
    小工具背景：

    - 苦于 https://www.textin.com/ 的方案纯文本精度不足。只能提取图片，无法概述图片，后续把数据喂给别的 Reasoning 模型也不方便；
    - 方案利用 Inference-Time Scaling 雕花。用人话说：牺牲「响应时间」与一定「结构准确度」，换取最好的「纯文本提取」；
    """)

    st.write("## 配置")

    st.caption("""\
    已知限制：

    - 仅支持中文；
    - 页数不建议超过 30 页；
    - 字体不能太小。
    """)

    pdf_file = st.file_uploader("上传文件：", type=["pdf"], key="pdf_uploader")

    user_instructions = st.text_area("补充指令：", "", height=70, key="pdf_instructions")
    prompt = DEFAULT_PROMPT + "\n" + user_instructions

    if pdf_file:
        if st.button("提取", key="extract_pdf"):
            with logfire.span(f"Processing - {pdf_file.name}"):
                st.session_state["pdf_extraction"] = None
                with st.spinner("正在提取中..."):
                    processor = PDFProcessor()
                    processor.chunk_size = chunk_size
                    result_text = await processor.extract(pdf_file, prompt)
                    st.session_state["pdf_extraction"] = result_text

    col1, col2 = st.columns([0.9, 0.1])
    with col1:
        if "pdf_extraction" in st.session_state and st.session_state["pdf_extraction"]:
            st.write("## 输出")
    with col2:
        if "pdf_extraction" in st.session_state and st.session_state["pdf_extraction"]:
            st_copy_to_clipboard(st.session_state["pdf_extraction"])

    if "pdf_extraction" in st.session_state and st.session_state["pdf_extraction"]:
        st.markdown(st.session_state["pdf_extraction"])


async def render_url_extractor() -> None:
    with st.sidebar:
        st.header("URL 提取配置")

    st.title("通用 URL 信息提取器")

    st.caption("""\
    小工具背景：

    - 利用大模型从网页中提取结构化信息；
    - 支持自定义提取指令和 JSON Schema；
    - 适用于新闻、文章、产品页面等各类网页内容提取。
    """)

    st.write("## 配置")

    url = st.text_input("输入 URL：", placeholder="https://sspai.com/post/96745")

    instruction = st.text_area(
        "提取指令（可选）：",
        placeholder="提取网页中的主要内容，包括标题、作者、正文和关键信息。",
        height=70,
    )

    default_schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "网页标题"},
            "author": {"type": "string", "description": "作者（如果有）"},
            "date": {"type": "string", "description": "发布日期（如果有）"},
            "content": {"type": "string", "description": "主要内容"},
            "summary": {"type": "string", "description": "内容摘要"},
            "keywords": {
                "type": "array",
                "items": {"type": "string"},
                "description": "关键词列表",
            },
        },
    }

    use_schema = st.checkbox("使用 JSON Schema", value=False)

    schema_json: Optional[dict] = None
    if use_schema:
        schema_text = st.text_area(
            "JSON Schema (Optional)",
            json.dumps(default_schema, indent=2, ensure_ascii=False),
            height=250,
        )

        try:
            if schema_text:
                schema_json = json.loads(schema_text)
        except json.JSONDecodeError:
            st.error("JSON Schema 格式错误，请检查后重试。")

    if st.button("提取", key="extract_url"):
        if not url:
            st.error("请输入有效的 URL。")
        else:
            try:
                with st.spinner("正在从 URL 提取信息..."):
                    jina_extractor = JinaExtractor()
                    result = jina_extractor.extract_info(
                        url=url,
                        instruction=instruction if instruction else None,
                        json_schema=schema_json,
                    )
                    st.session_state["url_extraction"] = result.text
            except Exception as e:
                st.error(f"提取失败：{str(e)}")

    col1, col2 = st.columns([0.9, 0.1])
    with col1:
        if "url_extraction" in st.session_state and st.session_state["url_extraction"]:
            st.write("## 输出")
    with col2:
        if "url_extraction" in st.session_state and st.session_state["url_extraction"]:
            st_copy_to_clipboard(st.session_state["url_extraction"])

    if "url_extraction" in st.session_state and st.session_state["url_extraction"]:
        st.markdown(st.session_state["url_extraction"])
