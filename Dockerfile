# 使用官方 Python 3.11 slim 镜像作为基础镜像，减小体积
FROM python:3.11-slim AS builder

# 设置环境变量，防止 Python 生成 .pyc 文件，并确保输出不被缓冲
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 设置工作目录
WORKDIR /app

# 安装系统依赖（构建 Python 包所需的库）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制 requirements.txt 文件
COPY requirements.txt .

# 安装 Python 依赖到虚拟环境（/opt/venv）
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 第二阶段：运行时镜像
FROM python:3.11-slim AS runtime

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    # 设置 Django 设置模块
    DJANGO_SETTINGS_MODULE="backend.settings" \
    # 设置时区
    TZ=Asia/Shanghai

# 设置时区
RUN apt-get update && apt-get install -y --no-install-recommends tzdata && \
    ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone && \
    rm -rf /var/lib/apt/lists/*

# 安装运行时系统依赖（例如 libpq 用于 PostgreSQL 连接）
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 从构建阶段复制虚拟环境
COPY --from=builder /opt/venv /opt/venv

# 复制项目文件
COPY . .

# 暴露端口（默认 Django 开发服务器端口，生产环境使用 gunicorn）
EXPOSE 8080
# 启动命令（使用 gunicorn）
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "--threads", "2", "backend.wsgi:application"]