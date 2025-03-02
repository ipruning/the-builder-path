"""
## ChangeLog

- [001] - [refactor] - Added logging initialization
"""

import asyncio

import streamlit as st

from src.config import configure_logging
from src.ui import render_pdf_extractor, render_url_extractor


async def main():
    configure_logging()

    st.set_page_config(page_title="Demo")

    pdf_tab, url_tab = st.tabs(["PDF 提取", "URL 提取"])

    pdf_render_task = None
    url_render_task = None

    with pdf_tab:
        pdf_render_task = asyncio.create_task(render_pdf_extractor())

    with url_tab:
        url_render_task = asyncio.create_task(render_url_extractor())

    await asyncio.gather(pdf_render_task, url_render_task)


if __name__ == "__main__":
    asyncio.run(main())
