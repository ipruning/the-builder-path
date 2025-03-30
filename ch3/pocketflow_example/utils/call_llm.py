import os

from openai import OpenAI


def call_llm(prompt):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set")
    client = OpenAI(api_key=api_key)

    r = client.chat.completions.create(
        model="gpt-4o", messages=[{"role": "user", "content": prompt}]
    )
    return r.choices[0].message.content


if __name__ == "__main__":
    prompt = "What is the meaning of life?"
    print(call_llm(prompt))
