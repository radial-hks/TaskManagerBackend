## 项目结构

```
project_root/
├── app/
│   ├── __init__.py
│   ├── main.py                # FastAPI 入口
│   ├── auth.py                # 用户认证模块
│   ├── models.py              # 数据模型定义
│   ├── storage.py             # JSON 读写封装
│   ├── task_routes.py         # 任务相关路由
│   └── utils.py               # 工具函数，如密码加密、UUID
├── data/
│   ├── users.json             # 用户信息
│   └── tasks.json             # 任务信息
├── recordings/               # 存储音频文件
└── requirements.txt          # 依赖包列表
```

---

## requirements.txt
```
fastapi
uvicorn
python-jose[cryptography]
bcrypt
pydantic
```

---

## 示例数据

### data/users.json
```json
[
  {
    "username": "admin",
    "password_hash": "$2b$12$3RCXwqgPIEVdcKyoGDr2tOmLbRHfEj35PBsT8OayWmHLR0Kk4Nz/q",  // 密码为 "admin123"
    "role": "admin"
  },
  {
    "username": "user1",
    "password_hash": "$2b$12$8tLZjtzM3ycbxAeWmDbPSOHptcIo7vIGpO62AThzXtUjGyaMldcxu",  // 密码为 "user123"
    "role": "user"
  }
]
```

### data/tasks.json
```json
[
  {
    "id": "test-uuid-1",
    "title": "会议纪要整理",
    "description": "请将上周的会议音频转成文本。",
    "priority": "high",
    "owner": "user1",
    "category": "会议纪要",
    "tags": ["转录", "会议"],
    "audio_file": "recordings/test-uuid-1.wav",
    "created_at": "2025-07-13T08:00:00"
  },
  {
    "id": "test-uuid-2",
    "title": "客户反馈分析",
    "description": "分析最近客户的音频反馈内容。",
    "priority": "medium",
    "owner": "user1",
    "category": "客户反馈",
    "tags": ["客户", "分析"],
    "audio_file": null,
    "created_at": "2025-07-13T09:30:00"
  }
]
```

---

## Swagger 示例说明

FastAPI 内置 Swagger UI：访问 http://localhost:8000/docs

推荐使用示例请求体测试：

### 创建任务 POST /tasks
```json
{
  "title": "录音转文字",
  "description": "将电话录音文件转为文字文档",
  "priority": "medium",
  "category": "转写",
  "tags": ["语音", "文字"]
}
```

### 搜索任务 GET /tasks/search 示例
```
/tasks/search?keyword=会议&priority=high&tags=转录&owner=user1
```

---

其余部分代码结构与实现保持不变，如需补充 OpenAPI 文档注解 (`@router.post(..., response_model=...)` 和 `Body(...)`)，可继续请求。
