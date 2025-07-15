# 使用官方 Python 镜像作为基础镜像
FROM python:3.11-slim

# 安装必要的系统依赖（Pillow 等需要）
# RUN apt-get update && apt-get install -y \
#     libjpeg-dev \
#     zlib1g-dev \
#     && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 安装 uv (推荐使用官方安装方式)
# RUN pip install --no-cache-dir uv

# 复制依赖文件
COPY pyproject.toml uv.lock requirements.txt ./

# 使用 uv 安装依赖（更高效的安装方式）
RUN pip install -r requirements.txt

# 复制应用代码
COPY ./app /app/app
COPY ./data /app/data

# 创建日志和录音目录
RUN mkdir -p /app/log /app/recordings

# 暴露端口
EXPOSE 8000

# 运行应用（推荐使用生产配置）
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]