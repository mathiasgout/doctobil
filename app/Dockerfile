FROM python:3.9.13-slim

ENV PYTHONBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY . /app
RUN apt-get update \
    && apt-get install -y git
RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]
