

```shell
uvicorn app.main:app --reload
```


docker build -t fastapi-app:latest .


docker run -d -p 8000:8000 --name fastapi-app fastapi-app:latest