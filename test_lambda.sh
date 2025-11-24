#!/bin/bash
#
# Test script for Docling Lambda function
#
# Prerequisites:
#   - Docker container must be running: docker-compose up -d
#   - Wait for container to start before running tests
#
# Usage:
#   ./test_lambda.sh           # Run all tests
#   ./test_lambda.sh url       # Test URL-based conversion only
#   ./test_lambda.sh base64    # Test base64 document conversion only
#

set -e

LAMBDA_URL="http://localhost:9000/2015-03-31/functions/function/invocations"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

echo_error() {
    echo -e "${RED}✗ $1${NC}"
}

echo_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

# Check if container is running
check_container() {
    echo_info "Checking if Lambda container is running..."
    if ! curl -s -o /dev/null -w "%{http_code}" "$LAMBDA_URL" -d '{}' 2>/dev/null | grep -q "200\|400\|500"; then
        echo_error "Lambda container is not responding at $LAMBDA_URL"
        echo_info "Start the container with: docker-compose up -d"
        exit 1
    fi
    echo_success "Container is running"
}

# Test URL-based document conversion
test_url_conversion() {
    echo ""
    echo "=========================================="
    echo "Test: URL-based document conversion"
    echo "=========================================="

    # Using a small, publicly available PDF
    TEST_URL="https://arxiv.org/pdf/2408.09869"

    echo_info "Sending request to convert: $TEST_URL"
    echo_info "This may take a minute for the first request (model loading)..."

    RESPONSE=$(curl -s -X POST "$LAMBDA_URL" \
        -H "Content-Type: application/json" \
        -d "{\"body\": \"{\\\"source_url\\\": \\\"$TEST_URL\\\"}\"}")

    # Check if response is valid JSON
    if ! echo "$RESPONSE" | jq . > /dev/null 2>&1; then
        echo_error "Invalid JSON response"
        echo "$RESPONSE"
        return 1
    fi

    # Parse response
    STATUS_CODE=$(echo "$RESPONSE" | jq -r '.statusCode')
    SUCCESS=$(echo "$RESPONSE" | jq -r '.body' | jq -r '.success')

    if [ "$STATUS_CODE" == "200" ] && [ "$SUCCESS" == "true" ]; then
        echo_success "URL conversion successful!"
        echo_info "Response status code: $STATUS_CODE"

        # Show markdown preview (first 500 chars)
        MARKDOWN=$(echo "$RESPONSE" | jq -r '.body' | jq -r '.markdown')
        echo_info "Markdown preview (first 500 chars):"
        echo "---"
        echo "$MARKDOWN" | head -c 500
        echo ""
        echo "---"

        # Show metadata
        echo_info "Metadata:"
        echo "$RESPONSE" | jq -r '.body' | jq '.metadata'
        return 0
    else
        echo_error "URL conversion failed!"
        echo "Status code: $STATUS_CODE"
        echo "Response body:"
        echo "$RESPONSE" | jq -r '.body' | jq .
        return 1
    fi
}

# Test base64 document conversion
test_base64_conversion() {
    echo ""
    echo "=========================================="
    echo "Test: Base64 document conversion"
    echo "=========================================="

    # Create a minimal test PDF
    # This is a minimal valid PDF that contains "Hello World"
    SAMPLE_PDF_B64="JVBERi0xLjEKMSAwIG9iago8PCAvVHlwZSAvQ2F0YWxvZyAvUGFnZXMgMiAwIFIgPj4KZW5kb2JqCjIgMCBvYmoKPDwgL1R5cGUgL1BhZ2VzIC9LaWRzIFszIDAgUl0gL0NvdW50IDEgPj4KZW5kb2JqCjMgMCBvYmoKPDwgL1R5cGUgL1BhZ2UgL1BhcmVudCAyIDAgUiAvTWVkaWFCb3ggWzAgMCA2MTIgNzkyXQovQ29udGVudHMgNCAwIFIgL1Jlc291cmNlcyA8PCAvRm9udCA8PCAvRjEgNSAwIFIgPj4gPj4gPj4KZW5kb2JqCjQgMCBvYmoKPDwgL0xlbmd0aCA0NCA+PgpzdHJlYW0KQlQKL0YxIDI0IFRmCjEwMCA3MDAgVGQKKEhlbGxvIFdvcmxkISkgVGoKRVQKZW5kc3RyZWFtCmVuZG9iago1IDAgb2JqCjw8IC9UeXBlIC9Gb250IC9TdWJ0eXBlIC9UeXBlMSAvQmFzZUZvbnQgL0hlbHZldGljYSA+PgplbmRvYmoKeHJlZgowIDYKMDAwMDAwMDAwMCA2NTUzNSBmIAowMDAwMDAwMDA5IDAwMDAwIG4gCjAwMDAwMDAwNTggMDAwMDAgbiAKMDAwMDAwMDExNSAwMDAwMCBuIAowMDAwMDAwMjcwIDAwMDAwIG4gCjAwMDAwMDAzNjMgMDAwMDAgbiAKdHJhaWxlcgo8PCAvU2l6ZSA2IC9Sb290IDEgMCBSID4+CnN0YXJ0eHJlZgo0NDIKJSVFT0YK"

    echo_info "Sending base64-encoded PDF for conversion..."

    RESPONSE=$(curl -s -X POST "$LAMBDA_URL" \
        -H "Content-Type: application/json" \
        -d "{\"body\": \"{\\\"document\\\": \\\"$SAMPLE_PDF_B64\\\", \\\"filename\\\": \\\"test.pdf\\\"}\"}")

    # Check if response is valid JSON
    if ! echo "$RESPONSE" | jq . > /dev/null 2>&1; then
        echo_error "Invalid JSON response"
        echo "$RESPONSE"
        return 1
    fi

    # Parse response
    STATUS_CODE=$(echo "$RESPONSE" | jq -r '.statusCode')
    SUCCESS=$(echo "$RESPONSE" | jq -r '.body' | jq -r '.success')

    if [ "$STATUS_CODE" == "200" ] && [ "$SUCCESS" == "true" ]; then
        echo_success "Base64 conversion successful!"
        echo_info "Response status code: $STATUS_CODE"

        # Show markdown content
        MARKDOWN=$(echo "$RESPONSE" | jq -r '.body' | jq -r '.markdown')
        echo_info "Converted markdown:"
        echo "---"
        echo "$MARKDOWN"
        echo "---"

        # Show metadata
        echo_info "Metadata:"
        echo "$RESPONSE" | jq -r '.body' | jq '.metadata'
        return 0
    else
        echo_error "Base64 conversion failed!"
        echo "Status code: $STATUS_CODE"
        echo "Response body:"
        echo "$RESPONSE" | jq -r '.body' | jq .
        return 1
    fi
}

# Test error handling - missing input
test_error_handling() {
    echo ""
    echo "=========================================="
    echo "Test: Error handling (missing input)"
    echo "=========================================="

    echo_info "Sending request without document or URL..."

    RESPONSE=$(curl -s -X POST "$LAMBDA_URL" \
        -H "Content-Type: application/json" \
        -d '{"body": "{}"}')

    STATUS_CODE=$(echo "$RESPONSE" | jq -r '.statusCode')
    SUCCESS=$(echo "$RESPONSE" | jq -r '.body' | jq -r '.success')

    if [ "$STATUS_CODE" == "400" ] && [ "$SUCCESS" == "false" ]; then
        echo_success "Error handling works correctly!"
        echo_info "Got expected error response:"
        echo "$RESPONSE" | jq -r '.body' | jq .
        return 0
    else
        echo_error "Error handling test failed - expected 400 status code"
        echo "$RESPONSE" | jq .
        return 1
    fi
}

# Main execution
main() {
    echo "=========================================="
    echo "  Docling Lambda Function Test Suite"
    echo "=========================================="

    check_container

    TEST_TYPE=${1:-all}
    FAILED=0

    case $TEST_TYPE in
        url)
            test_url_conversion || FAILED=1
            ;;
        base64)
            test_base64_conversion || FAILED=1
            ;;
        error)
            test_error_handling || FAILED=1
            ;;
        all)
            test_error_handling || FAILED=1
            test_base64_conversion || FAILED=1
            test_url_conversion || FAILED=1
            ;;
        *)
            echo "Unknown test type: $TEST_TYPE"
            echo "Usage: $0 [url|base64|error|all]"
            exit 1
            ;;
    esac

    echo ""
    echo "=========================================="
    if [ $FAILED -eq 0 ]; then
        echo_success "All tests passed!"
    else
        echo_error "Some tests failed!"
        exit 1
    fi
}

main "$@"
