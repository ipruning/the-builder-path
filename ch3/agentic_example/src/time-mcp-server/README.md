# Time MCP Server

## Install

### Dependencies

- bun
- docker
- uv

### Using UV

```bash
# 如果网络环境不好请选择国内镜像源
export UV_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple

uvx --from ./src/time-mcp-server time-mcp-server
```

### Using Docker

```bash
# 命令默认在仓库根目录执行
# 构建镜像
docker build -t time-mcp-server src/time-mcp-server

# 运行容器
docker run -i --rm time-mcp-server
```

## Debug

### Using Inspector

```bash
# 启动 Inspector Debug UI
bunx @modelcontextprotocol/inspector uv --directory src/time-mcp-server run time-mcp-server
```
