FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=7860

COPY requirements-hf.txt .
RUN pip install --no-cache-dir -r requirements-hf.txt

COPY . .

EXPOSE 7860

CMD ["python", "app.py"]
