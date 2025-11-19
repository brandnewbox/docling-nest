# Terraform Configuration for Docling Converter

This directory contains Terraform configuration files for deploying the Docling document converter as a DigitalOcean serverless function.

## Prerequisites

1. **Terraform**: Install Terraform (version >= 1.0)
   ```bash
   # macOS
   brew install terraform

   # Linux
   wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
   unzip terraform_1.6.0_linux_amd64.zip
   sudo mv terraform /usr/local/bin/
   ```

2. **DigitalOcean Account**: Create an account at https://www.digitalocean.com/

3. **DigitalOcean API Token**: Generate a personal access token from the DigitalOcean control panel
   - Go to: API → Tokens/Keys → Generate New Token
   - Give it a name and select both Read and Write scopes

4. **Git Repository**: Your code must be in a Git repository accessible to DigitalOcean

## Setup

1. **Set your DigitalOcean token as an environment variable**:
   ```bash
   export DIGITALOCEAN_TOKEN="your_digitalocean_token_here"
   ```

2. **Configure variables**:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your values
   ```

3. **Initialize Terraform**:
   ```bash
   terraform init
   ```

## Deployment

### Plan the deployment
```bash
terraform plan
```

### Apply the configuration
```bash
terraform apply
```

After successful deployment, Terraform will output the function URL.

### View outputs
```bash
terraform output
```

## Usage

Once deployed, you can call the function:

```bash
# Convert a document from URL
curl -X POST https://your-app-url.ondigitalocean.app/convert \
  -H "Content-Type: application/json" \
  -d '{
    "source_url": "https://example.com/sample.pdf"
  }'

# Convert a base64 encoded document
curl -X POST https://your-app-url.ondigitalocean.app/convert \
  -H "Content-Type: application/json" \
  -d '{
    "document": "base64_encoded_content_here",
    "filename": "document.pdf"
  }'
```

## Updating the Function

When you push changes to your Git repository:

```bash
terraform apply
```

This will trigger a redeployment with the latest code.

## Destroying the Infrastructure

To remove all resources:

```bash
terraform destroy
```

## Configuration Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `region` | DigitalOcean region | `nyc1` |
| `git_repo_url` | Git repository URL | *required* |
| `git_branch` | Git branch to deploy | `master` |
| `log_level` | Logging level | `INFO` |

## Available Regions

- `nyc1` - New York 1
- `nyc3` - New York 3
- `sfo3` - San Francisco 3
- `ams3` - Amsterdam 3
- `sgp1` - Singapore 1
- `lon1` - London 1
- `fra1` - Frankfurt 1
- `tor1` - Toronto 1
- `blr1` - Bangalore 1
- `syd1` - Sydney 1

## Cost Estimation

DigitalOcean Functions pricing (as of 2024):
- Free tier: 90,000 GB-seconds per month
- After free tier: $0.0000185 per GB-second

With 2GB memory allocation and 5-minute timeout:
- Maximum cost per invocation: ~$0.011
- Typical document processing (30 seconds): ~$0.001

## Troubleshooting

### Function deployment fails
- Ensure your Git repository is public or you've granted DigitalOcean access
- Check that the `project.yml` file is in the repository root
- Verify the function code is in `packages/docling/convert/`

### Function times out
- Increase the timeout in `project.yml`
- Consider optimizing document processing for large files

### Out of memory errors
- Increase memory allocation in `project.yml`
- Note: Larger memory allocations increase costs

## Additional Resources

- [DigitalOcean Functions Documentation](https://docs.digitalocean.com/products/functions/)
- [Terraform DigitalOcean Provider](https://registry.terraform.io/providers/digitalocean/digitalocean/latest/docs)
