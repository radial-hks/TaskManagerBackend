# 使用官方 Python 镜像作为基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装 uv
RUN pip install uv

# 复制 pyproject.toml 和 uv.lock 文件
COPY pyproject.toml uv.lock ./

# 使用 uv 安装依赖
RUN uv pip install --system -r pyproject.toml

# 复制应用代码
COPY ./app /app/app

# 暴露端口
EXPOSE 8000

# 运行应用
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]