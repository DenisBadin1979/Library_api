# Этап 1: Сборщик
FROM python:3.13-slim AS builder

WORKDIR /app

# Устанавливаем зависимости системы
RUN apt-get update && apt-get install -y \\\\
    gcc \\\\
    libpq-dev \\\\
    && apt-get clean \\\\
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install -r requirements.txt


# Копируем весь проект
COPY . .

# Этап 2: Финальный образ
FROM python:3.13-slim

WORKDIR /app

# Установка системных зависимостей (только необходимые)
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Копируем виртуальное окружение из builder
COPY --from=builder /app/.venv .venv

# Копируем код приложения
COPY --from=builder /app /app

# Активируем виртуальное окружение
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

# Команда для запуска приложения
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# Устанавливает переменную окружения, которая гарантирует, что вывод из python будет отправлен прямо в терминал без предварительной буферизации
ENV PYTHONUNBUFFERED 1

