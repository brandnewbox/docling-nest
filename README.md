# Docling Nest

A DigitalOcean serverless function that exposes the [Docling](https://github.com/docling-project/docling) library for document conversion to markdown.

## Features

- Convert documents (PDF, DOCX, etc.) to markdown format
- Support for both URL-based and base64-encoded document input
- Run locally with Docker for development and testing
- Deploy to DigitalOcean Functions with Terraform
- Built on IBM Research's Docling library

## Quick Start

### Local Development with Docker

1. **Start the local server:**
   ```bash
   docker-compose up --build
   ```

2. **Test the function:**
   ```bash
   ./test-local.sh
   ```

   Or manually:
   ```bash
   # Health check
   curl http://localhost:8080/

   # Convert from URL
   curl -X POST http://localhost:8080/convert \
     -H "Content-Type: application/json" \
     -d '{
       "source_url": "https://arxiv.org/pdf/2408.09869"
     }'

   # Convert from base64-encoded document
   curl -X POST http://localhost:8080/convert \
     -H "Content-Type: application/json" \
     -d '{
       "document": "BASE64_ENCODED_CONTENT",
       "filename": "document.pdf"
     }'
   ```

## API Reference

### Endpoint: POST /convert

Convert a document to markdown format.

#### Request Body

```json
{
  "source_url": "https://example.com/document.pdf",
  "document": "base64_encoded_content",
  "filename": "document.pdf",
  "extract_tables_as_images": false,
  "image_resolution_scale": 2
}
```

**Parameters:**

- `source_url` (string, optional): URL to the document to convert
- `document` (string, optional): Base64-encoded document content
- `filename` (string, optional): Original filename (used when providing base64 content)
- `extract_tables_as_images` (boolean, optional): Extract tables as images. Default: `false`
- `image_resolution_scale` (integer, optional): Image resolution scale. Default: `2`

**Note:** Either `source_url` or `document` must be provided.

#### Response

**Success (200):**
```json
{
  "success": true,
  "markdown": "# Converted Document\n\n...",
  "metadata": {
    "num_pages": 10,
    "source": "https://example.com/document.pdf"
  }
}
```

**Error (400/500):**
```json
{
  "success": false,
  "error": "Error message",
  "error_type": "ExceptionType"
}
```

## Deployment to DigitalOcean

### Prerequisites

- DigitalOcean account
- Terraform installed
- DigitalOcean API token

### Deploy with Terraform

1. **Navigate to the terraform directory:**
   ```bash
   cd terraform
   ```

2. **Create your variables file:**
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```

3. **Edit `terraform.tfvars` with your settings:**
   ```hcl
   do_token = "your-digitalocean-api-token"
   git_repo = "https://github.com/yourusername/docling-nest"
   git_branch = "master"
   region = "nyc"
   ```

4. **Initialize and deploy:**
   ```bash
   terraform init
   terraform plan
   terraform apply
   ```

5. **Get the function URL:**
   ```bash
   terraform output function_url
   ```

For detailed deployment instructions, see [terraform/README.md](terraform/README.md).

### Manual Deployment

You can also deploy using the DigitalOcean CLI or web console:

```bash
doctl serverless deploy .
```

## Project Structure

```
docling-nest/
├── packages/
│   └── docling/
│       └── convert/
│           ├── __main__.py       # Main function handler
│           └── requirements.txt  # Python dependencies
├── terraform/
│   ├── main.tf                   # Terraform configuration
│   ├── variables.tf              # Terraform variables
│   ├── terraform.tfvars.example  # Example configuration
│   └── README.md                 # Deployment guide
├── project.yml                   # DigitalOcean Functions config
├── Dockerfile                    # Docker image for local dev
├── docker-compose.yml            # Docker Compose setup
└── test-local.sh                 # Local testing script
```

## Development

### Requirements

- Python 3.11
- Docker and Docker Compose (for local development)
- Terraform (for deployment)

### Adding Dependencies

Add Python packages to `packages/docling/convert/requirements.txt`:

```txt
docling>=2.0.0
your-package>=1.0.0
```

### Testing Locally

The local Docker setup includes a Flask wrapper that mimics the DigitalOcean Functions runtime:

```bash
# Start the service
docker-compose up --build

# In another terminal, run tests
./test-local.sh
```

### Function Configuration

Modify `project.yml` to adjust function settings:

- `timeout`: Maximum execution time (default: 300000ms = 5 minutes)
- `memory`: Memory allocation (default: 2048MB)
- Environment variables

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

DigitalOcean Functions pricing is based on GB-seconds of execution:

- **Free tier:** 90,000 GB-seconds per month
- **Additional usage:** $0.0000185 per GB-second

With 2GB memory allocation:
- ~750 seconds (12.5 minutes) of execution in the free tier
- Each 30-second conversion costs approximately $0.001

See the [Terraform README](terraform/README.md) for detailed cost analysis.

## Troubleshooting

### Local Development Issues

**Container fails to start:**
- Ensure Docker has enough memory (at least 4GB recommended)
- Check Docker logs: `docker-compose logs`

**Conversion fails:**
- Some documents may require additional system dependencies
- Check the Docling logs for specific errors
- Increase memory allocation if needed

### Deployment Issues

**Function timeout:**
- Increase timeout in `project.yml`
- Large documents may take longer to process

**Memory errors:**
- Increase memory allocation in `project.yml`
- Docling's ML models require significant memory

**See [terraform/README.md](terraform/README.md) for deployment-specific troubleshooting.**

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

This project is provided as-is. The Docling library is licensed under the MIT License.

## Resources

- [Docling GitHub Repository](https://github.com/docling-project/docling)
- [DigitalOcean Functions Documentation](https://docs.digitalocean.com/products/functions/)
- [Terraform DigitalOcean Provider](https://registry.terraform.io/providers/digitalocean/digitalocean/latest/docs)
