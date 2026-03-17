FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8000
ENV FASTMCP_HOST=0.0.0.0

CMD ["python", "server.py"]
