"""
DigitalOcean serverless function for Docling document conversion.

This function accepts documents via HTTP POST and converts them to markdown format.
"""

import json
import base64
import tempfile
import os
from pathlib import Path
from typing import Dict, Any

try:
    from docling.document_converter import DocumentConverter
except ImportError:
    # Fallback for testing without docling installed
    DocumentConverter = None


def main(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main handler for the DigitalOcean function.

    Expected input format:
    {
        "document": "base64_encoded_document_content",
        "filename": "document.pdf",  # optional
        "source_url": "https://example.com/doc.pdf",  # alternative to document
        "extract_tables_as_images": false,  # optional
        "image_resolution_scale": 2  # optional
    }

    Returns:
    {
        "success": true,
        "markdown": "converted markdown content",
        "metadata": {...}
    }
    """
    try:
        # Validate DocumentConverter is available
        if DocumentConverter is None:
            return {
                "statusCode": 500,
                "body": {
                    "success": False,
                    "error": "Docling library not available"
                }
            }

        # Parse input
        source_url = args.get("source_url")
        document_b64 = args.get("document")
        filename = args.get("filename", "document.pdf")

        # Additional conversion options
        extract_tables_as_images = args.get("extract_tables_as_images", False)
        image_resolution_scale = args.get("image_resolution_scale", 2)

        if not source_url and not document_b64:
            return {
                "statusCode": 400,
                "body": {
                    "success": False,
                    "error": "Either 'source_url' or 'document' (base64) must be provided"
                }
            }

        # Initialize converter
        converter = DocumentConverter()

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
            "statusCode": 200,
            "body": {
                "success": True,
                "markdown": markdown_content,
                "metadata": metadata
            }
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            }
        }
