"""
## ChangeLog

- 001 - AI - Created script to test all Gemini API keys from .env file
- 002 - AI - Updated to test Gemini API keys with Google Search tool
- 003 - AI - Implemented concurrent testing of API keys using asyncio
- 004 - AI - Switched from asyncio to ThreadPoolExecutor for simpler concurrency
"""

import concurrent.futures
import os
from typing import Dict, List, Tuple

from dotenv import load_dotenv
from google import genai
from loguru import logger


def test_gemini_key(key_name: str, key: str) -> Tuple[str, bool]:
    try:
        client = genai.Client(api_key=key)

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents="日本最有名的动漫是什么？一句话回答。",
        )

        return key_name, response.candidates is not None
    except Exception as e:
        logger.error(f"Error testing key {key_name}: {str(e)}")
        return key_name, False


def get_gemini_keys() -> Dict[str, str]:
    load_dotenv()
    return {key: value for key, value in os.environ.items() if key.startswith("GEMINI_API_KEY")}


def test_all_keys(keys: Dict[str, str]) -> List[Tuple[str, bool]]:
    results = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_key = {
            executor.submit(test_gemini_key, key_name, key_value): key_name for key_name, key_value in keys.items()
        }

        for future in concurrent.futures.as_completed(future_to_key):
            results.append(future.result())

    return results


def main():
    keys_status = {"valid": [], "invalid": []}

    gemini_keys = get_gemini_keys()
    if not gemini_keys:
        logger.warning("No Gemini API keys found in environment variables")
        return

    logger.info(f"Testing GEMINI_API_KEY: 0/{len(gemini_keys)}")
    test_results = test_all_keys(gemini_keys)

    for key_name, is_valid in test_results:
        if is_valid:
            logger.success(f"{key_name}")
            keys_status["valid"].append(key_name)
        else:
            logger.error(f"{key_name}")
            keys_status["invalid"].append(key_name)

    logger.info(f"Passed: {len(keys_status['valid'])}/{len(gemini_keys)}")


if __name__ == "__main__":
    main()
