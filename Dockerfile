FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
docker.io && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY runner.py .
EXPOSE 9000
CMD ["uvicorn", "runner:app", "--host", "0.0.0.0", "--port", "9000"]
