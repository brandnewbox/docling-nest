# Implementation Plan: Refactor to AWS Lambda

## Overview
Refactor the DigitalOcean serverless function to an AWS Lambda function that implements the Docling API for document conversion.

## Tasks

### Task 1: Create Lambda handler module ✅
- [x] Create `lambda_handler.py` with proper Lambda event/response format
- [x] Adapt the existing conversion logic to Lambda handler signature
- [x] Support both API Gateway proxy integration and direct Lambda invocation
- [x] Handle base64 encoding/decoding for binary payloads

### Task 2: Create Dockerfile using AWS Lambda Python base image
- [ ] Use `public.ecr.aws/lambda/python:3.11` as base image
- [ ] Install system dependencies for document processing
- [ ] Install Python dependencies (docling)
- [ ] Copy handler code to Lambda task root
- [ ] Set CMD to point to Lambda handler

### Task 3: Update docker-compose.yml for local testing
- [ ] Configure Lambda RIE (Runtime Interface Emulator) for local testing
- [ ] Set up proper port mapping (9000 for Lambda)
- [ ] Update volume mounts for development

### Task 4: Create test script
- [ ] Create a test script that sends a sample PDF to the Lambda function
- [ ] Test both URL-based and base64 document conversion
- [ ] Verify the response format

### Task 5: Clean up old DigitalOcean files
- [ ] Remove or archive `.do/app.yaml`
- [ ] Remove or archive `project.yml`
- [ ] Update any remaining references

## Progress Notes
- Task 1 completed: Created lambda_handler.py with proper Lambda integration
