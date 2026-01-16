FROM registry.redhat.io/ubi9/python-311:9.6

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY mcp/ ./mcp/

CMD ["python", "mcp/server.py"]
