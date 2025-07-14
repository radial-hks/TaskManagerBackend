from fastapi import FastAPI
from . import auth, task_routes

app = FastAPI()

app.include_router(auth.router)
app.include_router(task_routes.router)