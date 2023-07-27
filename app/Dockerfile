FROM python:3.9.13-slim

ENV PYTHONBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY . /app
RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates curl firefox-esr \
    && rm -fr /var/lib/apt/lists/* \
    && curl -L https://github.com/mozilla/geckodriver/releases/download/v0.33.0/geckodriver-v0.33.0-linux-aarch64.tar.gz  | tar xz -C /usr/local/bin \
    && apt-get purge -y curl
RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]
