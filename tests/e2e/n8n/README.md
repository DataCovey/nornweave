# n8n E2E Testing Environment

Local n8n instance for testing the NornWeave community node.

## Prerequisites

- Docker and Docker Compose installed
- Node.js (for building the NornWeave n8n node package)

## Quick Start

From this directory (`tests/e2e/n8n`):

```bash
# 1. Build and install the NornWeave node
./setup.sh

# 2. Start n8n
docker compose up -d

# 3. Open n8n in browser
open http://localhost:5678
```

## Manual Setup

If you prefer to run steps manually:

```bash
# Build the n8n node package
cd ../../../packages/n8n-nodes-nornweave
npm install
npm run build

# Copy built node to custom-nodes directory
cd ../../../tests/e2e/n8n
mkdir -p custom-nodes/n8n-nodes-nornweave
cp -r ../../../packages/n8n-nodes-nornweave/dist custom-nodes/n8n-nodes-nornweave/
cp ../../../packages/n8n-nodes-nornweave/package.json custom-nodes/n8n-nodes-nornweave/

# Start n8n
docker compose up -d
```

## Using the NornWeave Node

1. Open http://localhost:5678
2. Create an account (first-time setup)
3. Create a new workflow
4. Search for "NornWeave" in the nodes panel
5. Configure credentials with your NornWeave API URL and key

## Stopping

```bash
docker compose down
```

To also remove the data volume (fresh start):

```bash
docker compose down -v
```

## Troubleshooting

**Node not appearing in n8n:**
- Ensure the build completed successfully
- Check n8n logs: `docker compose logs -f n8n`
- Restart n8n: `docker compose restart n8n`

**Rebuilding after code changes:**
```bash
./setup.sh
docker compose restart n8n
```
