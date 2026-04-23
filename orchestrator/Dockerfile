FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
COPY orchestrator/requirements.txt ./requirements-orch.txt

RUN pip install --no-cache-dir -r requirements.txt -r requirements-orch.txt

COPY shared /app/shared
COPY orchestrator /app/orchestrator

WORKDIR /app/orchestrator

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
