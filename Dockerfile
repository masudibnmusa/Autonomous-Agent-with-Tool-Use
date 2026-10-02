# Sandbox image for code execution. Build with: docker build -t agent-sandbox .
FROM python:3.12-slim

RUN pip install --no-cache-dir numpy pandas

WORKDIR /tmp
CMD ["python", "-"]