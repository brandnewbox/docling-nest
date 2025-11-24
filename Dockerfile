# AWS Lambda Python base image for Docling document conversion
FROM public.ecr.aws/lambda/python:3.11

# Install system dependencies for document processing
# Lambda base images use Amazon Linux 2, which uses yum
RUN yum update -y && \
    yum install -y \
    mesa-libGL \
    glib2 \
    libSM \
    libXext \
    libXrender \
    libgomp \
    && yum clean all && \
    rm -rf /var/cache/yum

# Copy requirements and install Python dependencies
COPY packages/docling/convert/requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

# Copy Lambda handler code
COPY lambda_handler.py ${LAMBDA_TASK_ROOT}/

# Set the CMD to the Lambda handler
CMD ["lambda_handler.handler"]
