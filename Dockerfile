FROM python:3.11-slim

WORKDIR /app

COPY . .

RUN pip install aiogram==3.5.0 aiosqlite==0.19.0

CMD ["python", "bot.py"]
