from fastapi import FastAPI
from . import auth, task_routes
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 配置 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源（生产环境建议指定具体域名）
    allow_credentials=True,
    allow_methods=["*"],   # 允许所有方法（GET/POST等）
    allow_headers=["*"],   # 允许所有请求头
)

app.include_router(auth.router)
app.include_router(task_routes.router)