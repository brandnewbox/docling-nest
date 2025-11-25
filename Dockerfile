# AWS Lambda Python base image for Docling document conversion
FROM public.ecr.aws/lambda/python:3.14

# Install system dependencies for document processing
# AL2023 uses dnf instead of yum
# gcc and python3-devel are needed to compile NumPy and other native extensions
RUN dnf update -y && \
    dnf install -y \
    gcc \
    gcc-c++ \
    mesa-libGL \
    glib2 \
    libSM \
    libXext \
    libXrender \
    libgomp \
    && dnf clean all && \
    rm -rf /var/cache/dnf

# Copy requirements and install Python dependencies
COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

# Pre-download Docling models during build
# This eliminates the ~30-60 second cold start delay for model downloads
ENV HF_HOME=/var/task/models/hf_home
ENV TORCH_HOME=/var/task/models/torch_home

# Download models by converting a sample PDF (models are loaded lazily)
# We use a small test PDF to trigger all model downloads
RUN python -c "\
from docling.document_converter import DocumentConverter; \
from docling.datamodel.base_models import InputFormat; \
from docling.datamodel.pipeline_options import PdfPipelineOptions; \
from docling.document_converter import PdfFormatOption; \
pipeline_options = PdfPipelineOptions(); \
pipeline_options.do_ocr = False; \
converter = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}); \
converter.convert('https://arxiv.org/pdf/2408.09869'); \
print('Models downloaded successfully')"

COPY lambda_handler.py ${LAMBDA_TASK_ROOT}/
# Ensure read permissions of the handler
RUN chmod 644 ${LAMBDA_TASK_ROOT}/lambda_handler.py

# Set the CMD to the Lambda handler
CMD ["lambda_handler.handler"]
