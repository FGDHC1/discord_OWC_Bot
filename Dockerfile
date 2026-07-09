FROM python:3.14-slim

WORKDIR /app

COPY bot/requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY bot/bot.py bot.py

CMD ["python", "bot.py"]
