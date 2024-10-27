FROM python:3.12 AS base

# Установка переменных окружения
ARG PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=on \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=500

# Установка необходимых пакетов
RUN apt-get update && apt-get install -y gcc
RUN python -m pip install --upgrade pip

# Задайте рабочую директорию
WORKDIR /app/src

# Копируем файл зависимостей
COPY requirements.txt ./  

# Установка виртуального окружения
ENV VIRTUAL_ENV=/app/src/.venv \
    PATH=/app/src/.venv/bin:$PATH

# Установка зависимостей
RUN pip install -r requirements.txt

# Копируем приложение
COPY ./lecture_2/hw/shop_api/ ./ 

# Стадия dev
FROM base AS dev
CMD ["bash", "-c", "while true; do sleep 1; done"]

# Стадия local
FROM base AS local
CMD ["uvicorn", "main:app", "--port", "8080", "--host", "0.0.0.0"]