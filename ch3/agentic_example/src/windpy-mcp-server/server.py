import json
from enum import Enum
from typing import Sequence

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import EmbeddedResource, ImageContent, TextContent, Tool
from pydantic import BaseModel, Field


class KnownDataSource(str, Enum):
    SHANGHAI_POWER = "S0048389"  # 上海电力装机量
    WUXI_POWER = "S0048390"  # 无锡电力装机量


class WindEdbInput(BaseModel):
    """
    用于拉取 edb 数据的输入结构
    可以根据实际需要再添加更多字段
    如 start_date、周期、步长、条件等
    """

    code: str = Field(
        ..., description="Wind EDB 数据源代码，比如 'S0048389' 表示上海电力装机量"
    )
    indicators: str = Field("ED-10Y", description="Wind EDB 指标，如 'ED-10Y'")
    end_date: str = Field("2024-12-28", description="结束日期，格式为 YYYY-MM-DD")
    fill: str = Field("Previous", description="填充方式，如 'Fill=Previous'")
    max_rows: int = Field(
        50, description="最多返回多少行。如果实际数据超过该数，会进行截断。"
    )


class WindTools(str, Enum):
    LIST_DATA_SOURCES = "list_data_sources"
    FETCH_EDB_DATA = "fetch_edb_data"


class WindServer:
    """
    这里的"server"仅做逻辑封装演示，便于在 call_tool 中调用。
    如果无法导入 WindPy，会自动进入 mock 模式。
    """

    def __init__(self):
        self.is_mock_mode = False
        try:
            from WindPy import w

            self.w = w
            self.w.start()
        except ImportError:
            self.is_mock_mode = True
            print("Warning: WindPy not available, running in mock mode")

    def list_data_sources(self) -> list[dict]:
        """
        列出我们可用的数据源信息。例如上海电力装机量、无锡电力装机量...
        可以返回更多描述信息。
        """
        return [
            {
                "code": KnownDataSource.SHANGHAI_POWER.value,
                "description": "上海电力装机量（S0048389）",
            },
            {
                "code": KnownDataSource.WUXI_POWER.value,
                "description": "无锡电力装机量（S0048390）",
            },
            # ...
        ]

    def fetch_edb_data(self, input_data: WindEdbInput) -> dict:
        """
        调用 WindPy 的 w.edb(...) 获取数据并返回。
        如果在 mock 模式下，返回模拟数据。
        """
        if not self.is_mock_mode:
            # 实际调用 Wind API
            error_code, df = self.w.edb(
                input_data.code,
                input_data.indicators,
                input_data.end_date,
                input_data.fill,
                usedf=True,
            )

            if error_code != 0:
                return {
                    "error_code": error_code,
                    "message": f"Failed to fetch data from Wind, error_code={error_code}",
                    "data": None,
                }
        else:
            # Mock 模式：返回模拟数据
            import numpy as np
            import pandas as pd

            # 根据不同的数据源生成不同的模拟数据
            if input_data.code == KnownDataSource.SHANGHAI_POWER.value:
                # 上海电力装机量模拟数据
                base_value = 25000  # 基准值（兆瓦）
                dates = pd.date_range("2023-01-01", periods=80, freq="M")
                # 生成一个带有季节性波动和增长趋势的数据
                seasonal = np.sin(np.linspace(0, 4 * np.pi, 80)) * 1000  # 季节性波动
                trend = np.linspace(0, 2000, 80)  # 增长趋势
                values = (
                    base_value + seasonal + trend + np.random.randn(80) * 500
                )  # 添加随机噪声
            elif input_data.code == KnownDataSource.WUXI_POWER.value:
                # 无锡电力装机量模拟数据
                base_value = 15000  # 基准值（兆瓦）
                dates = pd.date_range("2023-01-01", periods=80, freq="M")
                # 生成一个带有季节性波动和增长趋势的数据
                seasonal = np.sin(np.linspace(0, 4 * np.pi, 80)) * 600  # 季节性波动
                trend = np.linspace(0, 1500, 80)  # 增长趋势
                values = (
                    base_value + seasonal + trend + np.random.randn(80) * 300
                )  # 添加随机噪声
            else:
                # 其他数据源返回随机数据
                dates = pd.date_range("2023-01-01", periods=80, freq="M")
                values = np.random.randn(80) * 1000 + 10000

            # 创建 DataFrame
            df = pd.DataFrame(
                {
                    "VALUE": values,
                },
                index=dates,
            )

        # 处理数据截断
        full_count = len(df)
        if full_count > input_data.max_rows:
            df_truncated = df.head(input_data.max_rows).copy()
            truncated = True
        else:
            df_truncated = df
            truncated = False

        # 序列化 DataFrame
        df_json = df_truncated.to_json(orient="split", date_format="iso")

        result = {
            "error_code": 0,
            "rows_count": full_count,
            "truncated": truncated,
            "data": json.loads(df_json),  # json 可读
            "is_mock": self.is_mock_mode,  # 添加标记表明是否是模拟数据
        }
        return result


async def serve() -> None:
    server = Server("wind-mcp-server")
    wind_server = WindServer()

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """声明 Wind MCP 服务器有哪些可用工具。"""
        return [
            Tool(
                name=WindTools.LIST_DATA_SOURCES.value,
                description="列出可用的数据源代码，如上海/无锡等",
                inputSchema={
                    "type": "object",
                    "properties": {},  # 无输入
                },
            ),
            Tool(
                name=WindTools.FETCH_EDB_DATA.value,
                description="调用 w.edb(...) 拉取指定 code 的数据表，返回（截断后）json",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "Wind EDB 数据源代码，比如 'S0048389'",
                        },
                        "indicators": {
                            "type": "string",
                            "description": "Wind EDB 指标，如 'ED-10Y'",
                        },
                        "end_date": {
                            "type": "string",
                            "description": "结束日期，格式 YYYY-MM-DD",
                        },
                        "fill": {
                            "type": "string",
                            "description": "填充方式，如 Fill=Previous",
                        },
                        "max_rows": {
                            "type": "number",
                            "description": "返回多少行后截断",
                        },
                    },
                    "required": ["code"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
        try:
            match name:
                case WindTools.LIST_DATA_SOURCES.value:
                    # 不需要输入
                    datas = wind_server.list_data_sources()
                    return [TextContent(type="text", text=json.dumps(datas, indent=2))]

                case WindTools.FETCH_EDB_DATA.value:
                    # 将 arguments 转为 pydantic
                    input_data = WindEdbInput(**arguments)
                    result_dict = wind_server.fetch_edb_data(input_data)
                    return [
                        TextContent(type="text", text=json.dumps(result_dict, indent=2))
                    ]

                case _:
                    raise ValueError(f"Unknown tool: {name}")

        except Exception as e:
            # 避免信息泄露，或可以返回错误信息
            return [TextContent(type="text", text=f"Error: {str(e)}")]

    options = server.create_initialization_options()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, options)


def main():
    """Wind MCP Server - 从 WindPy 拉取 EDB 数据的示例。"""
    import asyncio

    asyncio.run(serve())


if __name__ == "__main__":
    main()
