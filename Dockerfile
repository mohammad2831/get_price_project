FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DOCKER_ENV=1

RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# اضافه کن این خط — مهم!
RUN pip install gunicorn

COPY . .

EXPOSE 8000

CMD ["gunicorn", "get_price_project.wsgi:application", "--bind", "0.0.0.0:8000"]