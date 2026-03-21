FROM python:3.9-slim

WORKDIR /app

COPY server.py /app/
COPY protocol.py /app/

EXPOSE 5000

CMD ["python", "server.py"]
