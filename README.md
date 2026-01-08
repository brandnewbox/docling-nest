# Docling Nest

An AWS Lambda function that exposes the [Docling](https://github.com/docling-project/docling) library for document conversion to markdown.

## Features

- Convert documents (PDF, DOCX, etc.) to markdown format
- Support for both URL-based and base64-encoded document input
- Run locally with Docker for development and testing
- Deploy as AWS Lambda function with container images
- Built on IBM Research's Docling library

## Quick Start

### Local Development with Docker

1. **Start the local Lambda emulator:**
   ```bash
   docker-compose up --build
   ```

2. **Test the function:**
   ```bash
   ./test_lambda.sh
   ```

   Or manually:
   ```bash
   # Convert from URL (returns JSON with markdown)
   curl -X POST "http://localhost:9000/2015-03-31/functions/function/invocations" \
     -H "Content-Type: application/json" \
     -d '{
       "path": "/",
       "httpMethod": "POST",
       "body": "{\"source_url\": \"https://arxiv.org/pdf/2408.09869\"}"
     }'

   # Export with images (returns base64-encoded zip)
   curl -s -X POST "http://localhost:9000/2015-03-31/functions/function/invocations" \
     -H "Content-Type: application/json" \
     -d '{
       "path": "/full",
       "httpMethod": "POST",
       "body": "{\"source_url\": \"https://arxiv.org/pdf/2408.09869\"}"
     }' | jq -r '.body' | base64 -d > output.zip

   # Convert from base64-encoded document
   curl -X POST "http://localhost:9000/2015-03-31/functions/function/invocations" \
     -H "Content-Type: application/json" \
     -d '{
       "path": "/",
       "httpMethod": "POST",
       "body": "{\"document\": \"BASE64_ENCODED_CONTENT\", \"filename\": \"document.pdf\"}"
     }'
   ```

## API Reference

The Lambda function provides two endpoints for document conversion.

### Common Request Format

Both endpoints accept the same input parameters (inside the body JSON):

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `source_url` | string | Either this or `document` | URL to the document to convert |
| `document` | string | Either this or `source_url` | Base64-encoded document content |
| `filename` | string | No | Original filename (defaults to `document.pdf`) |

---

### POST / — Convert to Markdown

Converts a document and returns the markdown content as JSON.

#### Request

```json
{
  "path": "/",
  "httpMethod": "POST",
  "body": "{\"source_url\": \"https://example.com/document.pdf\"}"
}
```

#### Response

**Success (200):**
```json
{
  "statusCode": 200,
  "headers": {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*"
  },
  "body": "{\"success\": true, \"markdown\": \"# Converted Document\\n\\n...\", \"metadata\": {\"num_pages\": 10, \"source\": \"https://example.com/document.pdf\"}}"
}
```

**Response body fields:**

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | `true` if conversion succeeded |
| `markdown` | string | The converted markdown content |
| `metadata.num_pages` | number | Number of pages in the document |
| `metadata.source` | string | The source URL or filename |

---

### POST /full — Markdown with Images

Converts a document and returns a zip file containing the markdown with extracted images.

#### Request

```json
{
  "path": "/export",
  "httpMethod": "POST",
  "body": "{\"source_url\": \"https://example.com/document.pdf\"}"
}
```

#### Response

**Success (200):**
```json
{
  "statusCode": 200,
  "headers": {
    "Content-Type": "application/zip",
    "Content-Disposition": "attachment; filename=\"document.zip\"",
    "Access-Control-Allow-Origin": "*"
  },
  "body": "<base64-encoded-zip-content>",
  "isBase64Encoded": true
}
```

**Zip file structure (flat):**
```
document.zip
├── document.md        # Markdown with relative image references
├── image_000000_xxx.png
├── image_000001_xxx.png
└── ...
```

The markdown file contains relative image references like `![Image](image_000000_xxx.png)` that correspond to the extracted image files in the zip.

---

### Error Responses

Both endpoints return errors in the same format:

**Error (400/500):**
```json
{
  "statusCode": 400,
  "body": "{\"success\": false, \"error\": \"Error message\", \"error_type\": \"ExceptionType\"}"
}
```

## Deployment to AWS Lambda

### Prerequisites

- AWS account
- AWS CLI configured
- Docker installed (for building container images)

### Build and Push Container Image

1. **Build the Docker image:**
   ```bash
   docker build -t docling-lambda .
   ```

2. **Create an ECR repository:**
   ```bash
   aws ecr create-repository --repository-name docling-lambda --region us-east-1
   ```

3. **Authenticate Docker with ECR:**
   ```bash
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
   ```

4. **Tag and push the image:**
   ```bash
   docker tag docling-lambda:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/docling-lambda:latest
   docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/docling-lambda:latest
   ```

### Create Lambda Function

1. **Create the Lambda function from the container image:**
   ```bash
   aws lambda create-function \
     --function-name docling-converter \
     --package-type Image \
     --code ImageUri=<account-id>.dkr.ecr.us-east-1.amazonaws.com/docling-lambda:latest \
     --role arn:aws:iam::<account-id>:role/lambda-execution-role \
     --memory-size 2048 \
     --timeout 300
   ```

2. **Test the function:**
   ```bash
   aws lambda invoke \
     --function-name docling-converter \
     --payload '{"body": "{\"source_url\": \"https://arxiv.org/pdf/2408.09869\"}"}' \
     response.json
   ```

### API Gateway Integration (Optional)

To expose the Lambda function as an HTTP API:

1. Create an HTTP API in API Gateway
2. Add a POST route (e.g., `/convert`)
3. Integrate with the Lambda function
4. Enable CORS if needed

## CI/CD with GitHub Actions

This project uses GitHub Actions to automatically deploy to AWS Lambda on every push to `main`.

### GitHub Configuration

The workflow requires these secrets and variables in your GitHub repository settings:

**Secrets** (Settings → Secrets and variables → Actions → Secrets):
- `AWS_ROLE_ARN` - The IAM role ARN for GitHub Actions to assume

**Variables** (Settings → Secrets and variables → Actions → Variables):
- `AWS_REGION` - AWS region (e.g., `us-east-1`)
- `ECR_REPOSITORY` - ECR repository name
- `LAMBDA_FUNCTION_NAME` - Lambda function name

### AWS IAM Configuration

The GitHub Actions workflow uses OIDC authentication. The IAM resources can be found in the AWS Console:

| Resource | Location |
|----------|----------|
| OIDC Provider | IAM → Identity providers → `token.actions.githubusercontent.com` |
| IAM Role | IAM → Roles → `github-actions-docling-nest` |
| Trust Policy | IAM → Roles → `github-actions-docling-nest` → Trust relationships |
| Permissions | IAM → Roles → `github-actions-docling-nest` → Permissions → `docling-nest-deploy` |

To modify permissions (e.g., add S3 access), edit the inline policy `docling-nest-deploy` on the IAM role.

## Project Structure

```
docling-nest/
├── lambda_handler.py         # Lambda function handler
├── requirements.txt          # Python dependencies
├── Dockerfile                # AWS Lambda container image
├── docker-compose.yml        # Local Lambda RIE setup
├── test_lambda.sh            # Local testing script
└── terraform/                # Legacy Terraform configuration
    ├── main.tf
    ├── variables.tf
    └── README.md
```

## Development

### Requirements

- Python 3.11
- Docker and Docker Compose (for local development)
- AWS CLI (for deployment)

### Testing Locally

The local Docker setup uses AWS Lambda Runtime Interface Emulator (RIE) to simulate the Lambda environment:

```bash
# Start the Lambda emulator
docker-compose up --build

# In another terminal, run tests
./test_lambda.sh

# Or run specific tests
./test_lambda.sh url      # Test URL-based conversion
./test_lambda.sh base64   # Test base64 document conversion
./test_lambda.sh error    # Test error handling
```

### Lambda Configuration

Recommended Lambda settings:

- **Memory:** 2048 MB (Docling's ML models require significant memory)
- **Timeout:** 300 seconds (5 minutes, for processing large documents)
- **Ephemeral storage:** 512 MB (default is sufficient)

## Supported Document Formats

Docling supports various document formats including:

- PDF
- DOCX
- PPTX
- HTML
- Images (PNG, JPG, etc.)
- And more...

See the [Docling documentation](https://github.com/docling-project/docling) for the full list.

## Cost Estimation

AWS Lambda pricing is based on:

- **Requests:** $0.20 per 1 million requests
- **Duration:** $0.0000166667 per GB-second (for 2GB memory)

With 2GB memory allocation:
- A 30-second conversion costs approximately $0.001
- Free tier includes 400,000 GB-seconds per month

## Troubleshooting

### Local Development Issues

**Container fails to start:**
- Ensure Docker has enough memory (at least 4GB recommended)
- Check Docker logs: `docker-compose logs`

**Conversion fails:**
- Some documents may require additional system dependencies
- Check the Docling logs for specific errors
- Ensure the Lambda has sufficient memory

### Deployment Issues

**Function timeout:**
- Increase Lambda timeout (max 900 seconds)
- Large documents may take longer to process

**Memory errors:**
- Increase Lambda memory allocation
- Docling's ML models require at least 2GB memory

**Cold start latency:**
- First invocation may be slow (30-60 seconds) due to model loading
- Consider provisioned concurrency for production workloads

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

This project is provided as-is. The Docling library is licensed under the MIT License.

## Resources

- [Docling GitHub Repository](https://github.com/docling-project/docling)
- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [AWS Lambda Container Images](https://docs.aws.amazon.com/lambda/latest/dg/images-create.html)
