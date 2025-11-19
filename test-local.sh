#!/bin/bash

# Test script for local Docker deployment

echo "Testing Docling serverless function locally..."
echo ""

# Health check
echo "1. Health check:"
curl -s http://localhost:8080/ | jq .
echo ""

# Test with URL
echo "2. Testing with sample URL (arXiv paper):"
curl -s -X POST http://localhost:8080/convert \
  -H "Content-Type: application/json" \
  -d '{
    "source_url": "https://arxiv.org/pdf/2408.09869"
  }' | jq -r '.success, .metadata'
echo ""

# Test with base64 document (example - you would need to provide actual base64)
echo "3. For base64 testing, use:"
echo 'curl -X POST http://localhost:8080/convert \\'
echo '  -H "Content-Type: application/json" \\'
echo '  -d '"'"'{'
echo '    "document": "BASE64_ENCODED_CONTENT",'
echo '    "filename": "document.pdf"'
echo '  }'"'"' | jq .'
