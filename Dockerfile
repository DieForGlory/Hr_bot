FROM python:3.11-slim
WORKDIR /app

# Установка и обновление системных SSL-сертификатов
RUN apt-get update && apt-get install -y ca-certificates && update-ca-certificates && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Установка пакета сертификатов для Python и остальных зависимостей
RUN pip install --no-cache-dir --upgrade certifi
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD python scripts/init_admin.py && uvicorn run_admin:app --host 0.0.0.0 --port 8000