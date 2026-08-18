-- Enable pgvector extension for hybrid legal retrieval
CREATE EXTENSION IF NOT EXISTS vector;

-- Full-text search configuration for legal sources
CREATE TEXT SEARCH CONFIGURATION IF NOT EXISTS legal_english (COPY = english);
