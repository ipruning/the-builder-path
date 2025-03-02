# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "lancedb",
#     "openai",
# ]
# ///
from typing import List

import lancedb
from lancedb.pydantic import LanceModel, Vector
from openai import OpenAI

LANCEDB_PATH = "data/lancedb"
EMBEDDING_MODEL = "openai:text-embedding-3-small"
EMBEDDING_DIMENSION = 1536
BATCH_SIZE = 200

database = lancedb.connect(LANCEDB_PATH)
client = OpenAI()


class DocumentSchema(LanceModel):
    text: str
    vector: Vector(EMBEDDING_DIMENSION)  # type: ignore


def get_embedding(text: str, model: str) -> List[float]:
    """
    从 OpenAI 模型获取给定文本的嵌入向量。

    参数：
        text: 需要嵌入的文本
        model: 模型字符串，格式为 "provider:model_id"

    返回：
        嵌入向量
    """
    model_provider, model_id = model.split(":") if ":" in model else ("", model)

    if model_provider == "openai":
        if model_id in ["text-embedding-3-large", "text-embedding-3-small"]:
            response = client.embeddings.create(input=[text], model=model_id)
            return response.data[0].embedding
        else:
            raise ValueError(f"Unsupported OpenAI model: {model_id}")
    else:
        raise ValueError(f"Unsupported model provider: {model_provider}")


def create_and_insert_to_table(texts: List[str], table_name="docs"):
    """
    创建一个新表并插入文本及其嵌入向量。

    参数：
        texts: 要嵌入和存储的文本列表
        table_name: 要创建的表名
    """
    table = database.create_table(
        table_name, schema=DocumentSchema.to_arrow_schema(), mode="overwrite"
    )

    data = []
    for text in texts:
        embedding = get_embedding(text, model=EMBEDDING_MODEL)
        data.append(DocumentSchema(text=text, vector=embedding))

    table.add(data)
    print(f"Added {len(data)} documents to table '{table_name}'")


def search_similar_texts(query_text: str, table_name="docs", limit=5):
    """
    搜索与查询文本最相似的文档。

    参数：
        query_text: 查询文本
        table_name: 要搜索的表名
        limit: 返回的最大结果数

    返回：
        相似文档列表
    """
    query_embedding = get_embedding(query_text, model=EMBEDDING_MODEL)
    table = database.open_table(table_name)
    results = table.search(query_embedding).limit(limit).to_list()

    return results


if __name__ == "__main__":
    texts = [
        "LanceDB 是一个向量数据库，适用于存储和检索嵌入向量。",
        "OpenAI 提供了强大的文本嵌入模型，如 text-embedding-3-small。",
        "向量搜索可以快速找到语义相似的文档。",
    ]

    create_and_insert_to_table(texts, "example_docs")

    query = "如何向量搜索？"
    results = search_similar_texts(query, "example_docs")

    print(f"查询：'{query}'")
    for i, result in enumerate(results):
        print(f"{i + 1}. 文本：{result['text']}")
        print(f"   相似度得分：{result['_distance']}")
        print()
