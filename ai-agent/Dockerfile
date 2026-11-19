FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY schemas.py k8s_enforcer.py agents.py main.py ./

RUN adduser --disabled-password --gecos "" --uid 1000 agentuser && \
    chown -R agentuser:agentuser /app

USER 1000

EXPOSE 5000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]
