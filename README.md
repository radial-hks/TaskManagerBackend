

```shell
uvicorn app.main:app --reload
```


docker build -t fastapi-app:latest .

docker build -t fastapi-app:dev .


docker run -d -p 8000:8000 --name fastapi-app fastapi-app:latest
docker run -d -p 8000:8000 --name fastapi-app fastapi-app:dev

```
sudo docker run -d -p 8000:8000 --name fastapi-app -v "$(pwd)/data:/app/data" -v "$(pwd)/log:/app/log" -v "$(pwd)/recordings:/app/recordings" fastapi-app:dev
```


