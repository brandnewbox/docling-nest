# Terraform Configuration for Docling Converter

> **Note:** This Terraform configuration is for the legacy DigitalOcean deployment. The project has been migrated to AWS Lambda. See the main [README.md](../README.md) for AWS Lambda deployment instructions.

## AWS Lambda Deployment

The recommended deployment method is now AWS Lambda with container images. See the [main README](../README.md) for:

- Building and pushing Docker images to ECR
- Creating Lambda functions
- API Gateway integration

## Legacy DigitalOcean Configuration

The Terraform files in this directory were used for the original DigitalOcean Functions deployment. They are kept for reference but are no longer actively maintained.

If you need to deploy to AWS Lambda with Terraform, consider using:
- [AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Lambda Function resource](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function)
- [ECR Repository resource](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ecr_repository)

## Original Configuration Files

| File | Description |
|------|-------------|
| `main.tf` | DigitalOcean App Platform configuration |
| `variables.tf` | Variable definitions |
| `terraform.tfvars.example` | Example variable values |
