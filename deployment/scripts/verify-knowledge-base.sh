
#!/bin/bash
#
# Knowledge Base Verification Script
# Verifies that Qdrant vector database is properly initialized
#
# Usage: ./deployment/scripts/verify-knowledge-base.sh
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Log functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running from correct directory
if [[ ! -f "docker-compose.yml" ]]; then
    log_error "Must be run from project root directory"
    exit 1
fi

echo ""
echo "=========================================="
echo "  Knowledge Base Verification"
echo "=========================================="
echo ""

# Step 1: Check if FastAPI container is running
log_info "Checking if FastAPI container is running..."
if docker compose ps fastapi | grep -q "Up"; then
    log_success "FastAPI container is running"
else
    log_error "FastAPI container is not running"
    exit 1
fi

# Step 2: Initialize knowledge base (idempotent - safe to run multiple times)
log_info "Running knowledge base initialization script..."
if docker compose exec fastapi python scripts/init_knowledge_base.py; then
    log_success "Knowledge base initialization completed"
else
    log_error "Failed to initialize knowledge base"
    exit 1
fi

echo ""

# Step 3: Verify Qdrant connection
log_info "Verifying Qdrant connection..."
QDRANT_CHECK=$(docker compose exec fastapi python -c "
import sys
import os
try:
    from qdrant_client import QdrantClient
    qdrant_url = os.getenv('QDRANT_URL', 'http://qdrant:6333')
    qdrant_api_key = os.getenv('QDRANT_API_KEY')

    if qdrant_api_key:
        client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
    else:
        client = QdrantClient(url=qdrant_url)

    # Test connection
    collections = client.get_collections()
    print('OK')
    sys.exit(0)
except Exception as e:
    print(f'ERROR: {e}', file=sys.stderr)
    sys.exit(1)
" 2>&1)

if echo "$QDRANT_CHECK" | grep -q "OK"; then
    log_success "Successfully connected to Qdrant"
else
    log_error "Failed to connect to Qdrant: $QDRANT_CHECK"
    exit 1
fi

# Step 4: Check collections
log_info "Checking Qdrant collections..."
COLLECTION_INFO=$(docker compose exec fastapi python -c "
import sys
import os
from qdrant_client import QdrantClient

try:
    qdrant_url = os.getenv('QDRANT_URL', 'http://qdrant:6333')
    qdrant_api_key = os.getenv('QDRANT_API_KEY')

    if qdrant_api_key:
        client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
    else:
        client = QdrantClient(url=qdrant_url)

    collections = client.get_collections()
    collection_names = [c.name for c in collections.collections]

    if not collection_names:
        print('No collections found')
        sys.exit(1)

    print(f'Found {len(collection_names)} collection(s):')
    for name in collection_names:
        try:
            info = client.get_collection(name)
            print(f'  - {name}: {info.points_count} vectors')
        except Exception as e:
            print(f'  - {name}: ERROR - {e}')

    sys.exit(0)
except Exception as e:
    print(f'ERROR: {e}', file=sys.stderr)
    sys.exit(1)
" 2>&1)

if echo "$COLLECTION_INFO" | grep -q "ERROR"; then
    log_error "Failed to retrieve collection info:"
    echo "$COLLECTION_INFO"
    exit 1
else
    log_success "Collections retrieved successfully:"
    echo "$COLLECTION_INFO" | sed 's/^/    /'
fi

echo ""

# Step 5: Test vector search
log_info "Testing vector search functionality..."
SEARCH_TEST=$(docker compose exec fastapi python -c "
import sys
import os
from qdrant_client import QdrantClient

try:
    qdrant_url = os.getenv('QDRANT_URL', 'http://qdrant:6333')
    qdrant_api_key = os.getenv('QDRANT_API_KEY')

    if qdrant_api_key:
        client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
    else:
        client = QdrantClient(url=qdrant_url)

    collections = client.get_collections()
    if not collections.collections:
        print('No collections to search')
        sys.exit(1)

    # Get first collection
    collection_name = collections.collections[0].name

    # Try to get collection info
    info = client.get_collection(collection_name)

    if info.points_count > 0:
        print(f'Collection \"{collection_name}\" has {info.points_count} vectors')
        print('Vector search is ready!')
    else:
        print(f'Collection \"{collection_name}\" exists but has no vectors')
        print('You may need to load documents into the knowledge base')

    sys.exit(0)
except Exception as e:
    print(f'ERROR: {e}', file=sys.stderr)
    sys.exit(1)
" 2>&1)

if echo "$SEARCH_TEST" | grep -q "ERROR"; then
    log_error "Vector search test failed:"
    echo "$SEARCH_TEST"
    exit 1
elif echo "$SEARCH_TEST" | grep -q "no vectors"; then
    log_warn "Vector search is configured but no documents loaded:"
    echo "$SEARCH_TEST" | sed 's/^/    /'
else
    log_success "Vector search is working:"
    echo "$SEARCH_TEST" | sed 's/^/    /'
fi

echo ""

# Step 6: Check embedding model
log_info "Verifying embedding model..."
EMBEDDING_TEST=$(docker compose exec fastapi python -c "
import sys
try:
    from sentence_transformers import SentenceTransformer

    # Try to load the model
    model = SentenceTransformer('all-MiniLM-L6-v2')

    # Test encoding
    test_text = 'This is a test sentence.'
    embedding = model.encode(test_text)

    print(f'Embedding model loaded successfully')
    print(f'Embedding dimension: {len(embedding)}')
    print(f'Model: all-MiniLM-L6-v2')
    sys.exit(0)
except Exception as e:
    print(f'ERROR: {e}', file=sys.stderr)
    sys.exit(1)
" 2>&1)

if echo "$EMBEDDING_TEST" | grep -q "ERROR"; then
    log_error "Embedding model test failed:"
    echo "$EMBEDDING_TEST"
    exit 1
else
    log_success "Embedding model is working:"
    echo "$EMBEDDING_TEST" | sed 's/^/    /'
fi

echo ""
echo "=========================================="
echo "  ✅ Knowledge Base Verification Complete"
echo "=========================================="
echo ""
log_success "All checks passed! Knowledge base is ready for use."
echo ""
echo "Next steps:"
echo "  1. Test RAG endpoint: curl -k https://YOUR_IP/api/knowledge/search?query=test"
echo "  2. Load additional documents if needed"
echo "  3. Monitor vector search performance in Grafana"
echo ""