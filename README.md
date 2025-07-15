

```shell
uvicorn app.main:app --reload
```


docker build -t fastapi-app:latest .


docker run -d -p 8000:8000 --name fastapi-app fastapi-app:latest

```
sudo docker run -d -p 8000:8000 --name fastapi-app 
-v "$(pwd)/data:/app/data" 
-v "$(pwd)/log:/app/log" 
-v "$(pwd)/recordings:/app/recordings" fastapi-app:latest
```