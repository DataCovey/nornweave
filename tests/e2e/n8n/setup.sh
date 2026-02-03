#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
NODE_PKG_DIR="$SCRIPT_DIR/../../../packages/n8n-nodes-nornweave"
CUSTOM_NODES_DIR="$SCRIPT_DIR/custom-nodes/n8n-nodes-nornweave"

echo "Building NornWeave n8n node..."
cd "$NODE_PKG_DIR"
npm install
npm run build

echo "Installing to custom-nodes directory..."
mkdir -p "$CUSTOM_NODES_DIR"
cp -r dist "$CUSTOM_NODES_DIR/"
cp package.json "$CUSTOM_NODES_DIR/"

echo "Done! Run 'docker compose up -d' to start n8n"
