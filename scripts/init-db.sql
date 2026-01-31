-- =============================================================================
-- NornWeave Database Initialization Script
-- This script is run automatically when the PostgreSQL container starts
-- =============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";  -- pgvector for Phase 3 semantic search

-- Create schema comment
COMMENT ON DATABASE nornweave IS 'NornWeave - Inbox-as-a-Service for AI Agents';
