"""
## Changelog
"""

import json
import os
from typing import Any, Dict, Optional

import logfire
import requests
from pydantic import BaseModel


class JinaResponse(BaseModel):
    text: str


class JinaExtractor:
    def __init__(self):
        self.api_key = os.environ.get("JINA_API_KEY")
        if not self.api_key:
            raise ValueError("JINA_API_KEY must be provided either through environment variable or constructor")

        self.base_url = "https://r.jina.ai/"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Respond-With": "readerlm-v2",
        }

    def extract_info(
        self,
        url: str,
        json_schema: Optional[Dict[str, Any]] = None,
        instruction: Optional[str] = None,
    ) -> JinaResponse:
        """
        Extract information from a URL using Jina API.

        Args:
            url: The target URL to extract information from
            json_schema: Optional JSON schema for structured extraction
            instruction: Optional instruction for the extraction

        Returns:
            JinaResponse object containing the extracted information

        Raises:
            requests.RequestException: If the API request fails
            ValueError: If the API key is not provided
        """
        data: Dict[str, Any] = {"url": url}

        if json_schema:
            data["jsonSchema"] = json_schema
        if instruction:
            data["instruction"] = instruction

        try:
            with logfire.span(f"Processing URL: {url}"):
                response = requests.post(self.base_url, headers=self.headers, data=json.dumps(data))
                response.raise_for_status()
                result = JinaResponse(text=response.text)
                logfire.info(f"URL - successfully extracted {len(result.text)} characters")
                return result
        except requests.RequestException as e:
            logfire.error(f"URL - API failed - {str(e)}")
            raise requests.RequestException(f"URL Extraction - API failed: {str(e)}")
