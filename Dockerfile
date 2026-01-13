FROM python:3.11-slim

LABEL maintainer="Your Name"
LABEL description="GitHub Settings Sync Action"

WORKDIR /app

COPY src/ /app/src/

RUN chmod +x /app/src/main.py

ENTRYPOINT ["python", "/app/src/main.py"]
