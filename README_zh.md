

# Task Manager Backend

这是一个功能强大的任务管理系统后端，旨在提供一个稳定、高效且可扩展的解决方案，用于处理任务分配、状态跟踪、文件管理和用户认证等核心业务。

## ✨ 功能特性

- **用户认证**：基于 JWT 的安全认证机制，支持用户注册和登录。
- **任务管理**：支持任务的增删改查，并提供丰富的查询条件。
- **文件管理**：支持文件上传、下载、重命名和删除，并与任务关联。
- **权限控制**：支持管理员和普通用户两种角色，并进行相应的权限控制。
- **日志记录**：记录详细的操作日志，便于问题排查和系统监控。
- **Docker 支持**：提供 Dockerfile 和 docker-compose.yml，支持容器化部署。

## 🛠️ 技术栈

- **后端框架**：FastAPI
- **数据验证**：Pydantic
- **异步处理**：Uvicorn
- **容器化**：Docker, Docker Compose
- **Web 服务器**：Nginx

## 🚀 环境配置与部署

### 1. 环境要求

- Python 3.9+
- Docker
- Docker Compose

### 2. 本地开发

1. **克隆项目**

   ```bash
   git clone https://github.com/radial-hks/TaskManagerBackend.git
   cd TaskManagerBackend
   ```

2. **安装依赖**

   ```bash
   pip install -r requirements.txt
   ```

3. **启动服务**

   ```bash
   uvicorn app.main:app --reload
   ```

### 3. Docker 部署

1. **构建镜像**

   ```bash
   docker build -t task-manager-backend:latest .
   ```

2. **启动容器**

   ```bash
   docker-compose up -d
   ```

3. **停止容器**

   ```bash
   docker-compose down
   ```

## 📚 API 文档

服务启动后，您可以通过以下地址访问自动生成的 API 文档：

- **Swagger UI**: `http://localhost:8008/docs`
- **ReDoc**: `http://localhost:8008/redoc`

## 🤝 贡献指南

我们欢迎任何形式的贡献，包括但不限于：

- **功能建议**：提出新的功能需求或改进建议。
- **代码贡献**：修复 Bug、优化性能或实现新功能。
- **文档完善**：补充和完善项目文档。

在提交贡献前，请确保您已经阅读并遵守我们的贡献指南。

## 📄 开源许可

本项目基于 [MIT License](LICENSE) 开源。