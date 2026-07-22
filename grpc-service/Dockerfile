#
# Copyright Â© 2026 ZTUnion LLC. All rights reserved.
#
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

WORKDIR /app/app

RUN python -m grpc_tools.protoc \
    -I. \
    --python_out=. \
    --grpc_python_out=. \
    cms.proto

ENV PORT=8080

CMD ["python", "server.py"]