FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY common ./common

EXPOSE 9002

CMD ["uvicorn", "app.chat.main:app", "--host", "0.0.0.0", "--port", "9002", "--reload"]