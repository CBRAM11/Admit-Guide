FROM python:3.11-slim

WORKDIR /app

# Copy requirements from src folder
COPY ../src/requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

# Copy entire source folder
COPY ../src /app

EXPOSE 7860 8000

CMD ["python", "main.py"]
