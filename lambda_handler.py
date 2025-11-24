"""
AWS Lambda function for Docling document conversion.

This function accepts documents via HTTP POST (API Gateway) or direct Lambda invocation
and converts them to markdown format using the Docling library.
"""

import json
import base64
import tempfile
import os
from pathlib import Path
from typing import Dict, Any, Optional

try:
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
except ImportError:
    # Fallback for testing without docling installed
    DocumentConverter = None
    PdfFormatOption = None
    InputFormat = None
    PdfPipelineOptions = None


def create_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Create a properly formatted API Gateway response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "POST, OPTIONS"
        },
        "body": json.dumps(body)
    }


def parse_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse Lambda event from various sources.

    Supports:
    - API Gateway proxy integration (body as JSON string)
    - Direct Lambda invocation (event is the payload)
    - API Gateway with base64 encoded body
    """
    # Check if this is an API Gateway event
    if "body" in event:
        body = event.get("body")
        if body is None:
            return {}

        # Handle base64 encoded body from API Gateway
        if event.get("isBase64Encoded", False):
            body = base64.b64decode(body).decode("utf-8")

        # Parse JSON body
        if isinstance(body, str):
            try:
                return json.loads(body)
            except json.JSONDecodeError:
                return {}
        return body

    # Direct Lambda invocation - event is the payload
    return event


def convert_document(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert document to markdown using Docling.

    Expected input format:
    {
        "document": "base64_encoded_document_content",
        "filename": "document.pdf",  # optional, defaults to "document.pdf"
        "source_url": "https://example.com/doc.pdf",  # alternative to document
    }

    Returns:
    {
        "success": true,
        "markdown": "converted markdown content",
        "metadata": {...}
    }
    """
    # Validate DocumentConverter is available
    if DocumentConverter is None:
        return {
            "status_code": 500,
            "body": {
                "success": False,
                "error": "Docling library not available"
            }
        }

    # Parse input
    source_url = args.get("source_url")
    document_b64 = args.get("document")
    filename = args.get("filename", "document.pdf")

    if not source_url and not document_b64:
        return {
            "status_code": 400,
            "body": {
                "success": False,
                "error": "Either 'source_url' or 'document' (base64) must be provided"
            }
        }

    # Initialize converter with OCR disabled
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = False

    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

    # Process document
    if source_url:
        # Convert from URL
        result = converter.convert(source_url)
    else:
        # Convert from base64 encoded document
        document_bytes = base64.b64decode(document_b64)

        # Write to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename).suffix) as tmp_file:
            tmp_file.write(document_bytes)
            tmp_path = tmp_file.name

        try:
            result = converter.convert(tmp_path)
        finally:
            # Clean up temp file
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    # Export to markdown
    markdown_content = result.document.export_to_markdown()

    # Prepare metadata
    metadata = {
        "num_pages": len(result.document.pages) if hasattr(result.document, 'pages') else None,
        "source": source_url if source_url else filename
    }

    return {
        "status_code": 200,
        "body": {
            "success": True,
            "markdown": markdown_content,
            "metadata": metadata
        }
    }


def handler(event: Dict[str, Any], context: Optional[Any] = None) -> Dict[str, Any]:
    """
    AWS Lambda handler function.

    Args:
        event: Lambda event (API Gateway proxy or direct invocation)
        context: Lambda context object (optional)

    Returns:
        API Gateway compatible response
    """
    # Handle CORS preflight
    http_method = event.get("httpMethod") or event.get("requestContext", {}).get("http", {}).get("method")
    if http_method == "OPTIONS":
        return create_response(200, {"message": "OK"})

    # Handle health check
    path = event.get("path") or event.get("rawPath", "")
    if path == "/" and http_method == "GET":
        return create_response(200, {"status": "healthy", "service": "docling-converter"})

    try:
        # Parse the event to get conversion parameters
        args = parse_event(event)

        # Perform conversion
        result = convert_document(args)

        return create_response(result["status_code"], result["body"])

    except Exception as e:
        return create_response(500, {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        })


# For local testing
if __name__ == "__main__":
    # Test with a simple event
    test_event = {
        "body": json.dumps({
            "source_url": "https://arxiv.org/pdf/2408.09869"
        })
    }
    result = handler(test_event)
    print(json.dumps(result, indent=2))
