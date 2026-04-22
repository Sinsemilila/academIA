FROM python:3.14-slim
WORKDIR /app

# academie-core (shared pedagogy + taxonomy layer, Sprint 4 Phase B onwards)
# Build context is /opt/academie/ (repo root) — see webapp/docker-compose.webapp.yml
COPY packages/academie-core /packages/academie-core
RUN pip install --no-cache-dir -e /packages/academie-core

# webapp deps + code
COPY webapp/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY webapp/backend/ .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
