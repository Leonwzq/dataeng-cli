FROM python:3.10-slim

WORKDIR /app

COPY pyproject.toml .
COPY dataeng_cli ./dataeng_cli

RUN pip install --no-cache-dir .

ENTRYPOINT ["dataeng-cli"]
CMD ["--help"]
