# README

## Prerequisites

- 配置 uv
- 配置 wsl (if you are on Windows)
- 配置 cursor
- 把 OPENAI_API_KEY 和 OPENAI_BASE_URL 配如 bashrc 文件

## Utils

```bash
op inject -i .env.tpl -o .env
```

```bash
# 运行脚本；如果这个目录有 pyproject.toml 文件，则会尝试更新 .venv 环境后运行；如果没有则会把 py 看成脚本来运行；
uv run FILENAME.py

# 添加依赖到当前环境；同时会更新 pyproject.toml 文件
uv add openai

# 添加依赖到指定脚本
uv add --script ./ch1/example_response_format_openai.py openai
```

## TODO

- 4090 能跑的 emb 微调脚本
- great_tables
