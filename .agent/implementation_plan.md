# Implementation Plan: Refactor to AWS Lambda

## Overview
Refactor the DigitalOcean serverless function to an AWS Lambda function that implements the Docling API for document conversion.

## Tasks

### Task 1: Create Lambda handler module ✅
- [x] Create `lambda_handler.py` with proper Lambda event/response format
- [x] Adapt the existing conversion logic to Lambda handler signature
- [x] Support both API Gateway proxy integration and direct Lambda invocation
- [x] Handle base64 encoding/decoding for binary payloads

### Task 2: Create Dockerfile using AWS Lambda Python base image ✅
- [x] Use `public.ecr.aws/lambda/python:3.11` as base image
- [x] Install system dependencies for document processing
- [x] Install Python dependencies (docling)
- [x] Copy handler code to Lambda task root
- [x] Set CMD to point to Lambda handler

### Task 3: Update docker-compose.yml for local testing ✅
- [x] Configure Lambda RIE (Runtime Interface Emulator) for local testing
- [x] Set up proper port mapping (9000 for Lambda)
- [x] Update volume mounts for development

### Task 4: Create test script ✅
- [x] Create a test script that sends a sample PDF to the Lambda function
- [x] Test both URL-based and base64 document conversion
- [x] Verify the response format

### Task 5: Clean up old DigitalOcean files ✅
- [x] Remove or archive `.do/app.yaml`
- [x] Remove or archive `project.yml`
- [ ] Update any remaining references (README still references DigitalOcean - separate task)

## Progress Notes
- Task 1 completed: Created lambda_handler.py with proper Lambda integration (commit fa5977a)
- Task 2 completed: Created Dockerfile using AWS Lambda Python base image (commit e39dfa1)
- Task 3 completed: Updated docker-compose.yml for Lambda RIE local testing (commit 0d69392)
- Task 4 completed: Created test_lambda.sh with URL, base64, and error handling tests (commit f25e03c)
- Task 5 completed: Removed .do/app.yaml and project.yml (DigitalOcean-specific config files)
