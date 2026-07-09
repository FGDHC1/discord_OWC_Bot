From python:3.14-slim

WORKDIR /app

copy requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

copy bot.py bot.py

cmd ["python", "bot.py"]