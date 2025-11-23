FROM python:3.14-slim as builder

WORKDIR /app

COPY . /app


RUN pip install uv

COPY pyproject.toml uv.lock* ./

RUN make install

COPY . .


COPY --from=builder /app /app

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}"]