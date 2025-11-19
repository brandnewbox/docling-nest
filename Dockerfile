FROM python:3.11-slim

# Install system dependencies for document processing
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY packages/docling/convert/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy function code
COPY packages/docling/convert/__main__.py .

# Create a simple Flask wrapper for local testing
RUN pip install --no-cache-dir flask

# Create a Flask app wrapper
RUN echo 'from flask import Flask, request, jsonify\n\
import __main__ as docling_function\n\
\n\
app = Flask(__name__)\n\
\n\
@app.route("/", methods=["GET"])\n\
def health():\n\
    return jsonify({"status": "healthy", "service": "docling-converter"})\n\
\n\
@app.route("/convert", methods=["POST"])\n\
def convert():\n\
    args = request.get_json() or {}\n\
    result = docling_function.main(args)\n\
    status_code = result.get("statusCode", 200)\n\
    body = result.get("body", result)\n\
    return jsonify(body), status_code\n\
\n\
if __name__ == "__main__":\n\
    app.run(host="0.0.0.0", port=8080)\n\
' > app.py

EXPOSE 8080

CMD ["python", "app.py"]
