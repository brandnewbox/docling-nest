"""
AWS Lambda function for Docling document conversion.

This function accepts documents via HTTP POST (API Gateway) or direct Lambda invocation
and converts them to markdown format using the Docling library.
"""

import os

# Set cache directories BEFORE importing any libraries that use them
# This must happen before importing docling, torch, transformers, etc.
#
# Models are pre-downloaded to /var/task/models during Docker build.
# We use HF_HUB_OFFLINE=1 to prevent any writes to the cache directory.
os.environ.setdefault("HOME", "/tmp")
os.environ.setdefault("HF_HOME", "/var/task/models/hf_home")
os.environ.setdefault("HF_HUB_OFFLINE", "1")  # Prevents writes to HF cache
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")  # Prevents transformers from downloading
os.environ.setdefault("TORCH_HOME", "/var/task/models/torch_home")
os.environ.setdefault("XDG_CACHE_HOME", "/tmp/.cache")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/.matplotlib")

import json
import base64
import tempfile
import zipfile
import io
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

try:
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling_core.types.doc import ImageRefMode
except ImportError:
    # Fallback for testing without docling installed
    DocumentConverter = None
    PdfFormatOption = None
    InputFormat = None
    PdfPipelineOptions = None
    ImageRefMode = None


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


def create_binary_response(status_code: int, body: bytes, filename: str) -> Dict[str, Any]:
    """Create a properly formatted API Gateway response for binary data."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/zip",
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "POST, OPTIONS"
        },
        "body": base64.b64encode(body).decode("utf-8"),
        "isBase64Encoded": True
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


def create_zip_with_images(result, source_name: str) -> Tuple[bytes, int]:
    """
    Create a zip file containing markdown with relative image references and extracted images.

    Args:
        result: The docling conversion result
        source_name: Base name for the output files

    Returns:
        Tuple of (zip_bytes, image_count)
    """
    zip_buffer = io.BytesIO()
    image_count = 0
    image_files = []

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        md_file = tmp_path / f"{source_name}.md"

        # Save markdown with referenced images to temp directory
        result.document.save_as_markdown(
            md_file,
            image_mode=ImageRefMode.REFERENCED
        )

        # Collect all image files
        for file_path in tmp_path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in ('.png', '.jpg', '.jpeg', '.gif', '.bmp'):
                image_files.append(file_path)
                image_count += 1

        # Read and fix markdown image references to use relative paths
        md_content = md_file.read_text()
        for img_file in image_files:
            # Replace absolute path with just the filename
            md_content = md_content.replace(str(img_file), img_file.name)

        # Create zip file in memory
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add the fixed markdown file
            zip_file.writestr(f"{source_name}.md", md_content)

            # Add all image files with flat structure
            for img_file in image_files:
                zip_file.write(img_file, img_file.name)

    zip_buffer.seek(0)
    return zip_buffer.getvalue(), image_count


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


def export_document(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Export document to a zip file containing markdown with images.

    Expected input format:
    {
        "document": "base64_encoded_document_content",
        "filename": "document.pdf",  # optional, defaults to "document.pdf"
        "source_url": "https://example.com/doc.pdf",  # alternative to document
    }

    Returns:
    {
        "status_code": 200,
        "zip_bytes": <bytes>,
        "filename": "document.zip"
    }
    """
    # Validate libraries are available
    if DocumentConverter is None:
        return {
            "status_code": 500,
            "error": "Docling library not available"
        }

    # Parse input
    source_url = args.get("source_url")
    document_b64 = args.get("document")
    filename = args.get("filename", "document.pdf")

    if not source_url and not document_b64:
        return {
            "status_code": 400,
            "error": "Either 'source_url' or 'document' (base64) must be provided"
        }

    # Initialize converter with image extraction enabled
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = False
    pipeline_options.generate_picture_images = True

    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

    # Process document
    if source_url:
        # Convert from URL
        result = converter.convert(source_url)
        base_name = Path(source_url).stem or "document"
    else:
        # Convert from base64 encoded document
        document_bytes = base64.b64decode(document_b64)
        base_name = Path(filename).stem

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

    # Create zip with images
    zip_bytes, image_count = create_zip_with_images(result, base_name)

    return {
        "status_code": 200,
        "zip_bytes": zip_bytes,
        "filename": f"{base_name}.zip"
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

        # Route to appropriate handler based on path
        if path == "/full" and http_method == "POST":
            # Export endpoint - returns zip with images
            result = export_document(args)
            if "error" in result:
                return create_response(result["status_code"], {
                    "success": False,
                    "error": result["error"]
                })
            return create_binary_response(
                result["status_code"],
                result["zip_bytes"],
                result["filename"]
            )
        elif path in ("", "/") and http_method == "POST":
            # Standard conversion endpoint - returns JSON
            result = convert_document(args)
            return create_response(result["status_code"], result["body"])
        else:
            return create_response(404, {
                "success": False,
                "error": f"Unknown endpoint: {http_method} {path}"
            })

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
