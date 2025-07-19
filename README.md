

# Task Manager Backend

This is a powerful task management system backend, designed to provide a stable, efficient, and scalable solution for handling core business operations such as task assignment, status tracking, file management, and user authentication.

## ✨ Features

- **User Authentication**: Secure authentication mechanism based on JWT, supporting user registration and login.
- **Task Management**: Supports CRUD operations for tasks with rich query conditions.
- **File Management**: Supports file upload, download, rename, and delete, associated with tasks.
- **Access Control**: Supports two roles, administrator and regular user, with corresponding access control.
- **Logging**: Records detailed operation logs for easy troubleshooting and system monitoring.
- **Docker Support**: Provides Dockerfile and docker-compose.yml for containerized deployment.

## 🛠️ Tech Stack

- **Backend Framework**: FastAPI
- **Data Validation**: Pydantic
- **Asynchronous Server**: Uvicorn
- **Containerization**: Docker, Docker Compose
- **Web Server**: Nginx

## 🚀 Environment Setup and Deployment

### 1. Prerequisites

- Python 3.9+
- Docker
- Docker Compose

### 2. Local Development

1. **Clone the project**

   ```bash
   git clone https://github.com/radial-hks/TaskManagerBackend.git
   cd TaskManagerBackend
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Start the service**

   ```bash
   uvicorn app.main:app --reload
   ```

### 3. Docker Deployment

1. **Build the image**

   ```bash
   docker build -t task-manager-backend:latest .
   ```

2. **Start the containers**

   ```bash
   docker-compose up -d
   ```

3. **Stop the containers**

   ```bash
   docker-compose down
   ```

## 📚 API Documentation

After the service starts, you can access the auto-generated API documentation at the following addresses:

- **Swagger UI**: `http://localhost:8008/docs`
- **ReDoc**: `http://localhost:8008/redoc`

## 🤝 Contribution Guidelines

We welcome any form of contribution, including but not limited to:

- **Feature Suggestions**: Propose new features or improvements.
- **Code Contributions**: Fix bugs, optimize performance, or implement new features.
- **Documentation Improvement**: Supplement and improve project documentation.

Before submitting contributions, please ensure you have read and complied with our contribution guidelines.

## 📄 License

This project is open-sourced under the [MIT License](LICENSE).