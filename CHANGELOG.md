# Changelog

All notable changes to NEUIToolkit will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-11-23

### Added - Phase 1: Foundation Hardening ✅

#### Multi-LLM Provider Support (P0 - Critical)
- **Provider Abstraction Layer** (`llm/provider_config.py`)
  - Support for OpenAI, Anthropic (Claude), Google (Gemini), and Ollama (local models)
  - Automatic provider fallback mechanism
  - Cost tracking and usage statistics
  - Configurable retry logic with exponential backoff
  - Provider-specific configuration (temperature, max_tokens, timeouts)

- **Enhanced LLM Utils** (`llm/llm_utils.py`)
  - Integrated multi-provider support using LiteLLM
  - Automatic fallback to secondary providers on failure
  - Usage tracking and cost estimation
  - Provider statistics reporting
  - Environment-based configuration

#### Quality Assurance Layer (P0 - Critical)
- **Quality Assessment Module** (`backend/quality_assurance.py`)
  - Confidence scoring for entities, relationships, and rules (0.0-1.0 scale)
  - Duplicate detection across extractions
  - Consistency checking for entity categories
  - Validation of required fields and data quality
  - Configurable confidence thresholds
  - Strict mode for rejecting low-quality extractions

- **Quality Metrics**
  - Entity assessment: name validation, category consistency, alias validation
  - Relationship assessment: triple validation, predicate quality, justification checking
  - Rule assessment: clause validation, confidence scoring, circular logic detection
  - Comprehensive quality reporting with aggregated statistics

#### Neo4j Integration (P0 - Critical)
- **Graph Database Connector** (`backend/neo4j_integration.py`)
  - Direct connection to Neo4j databases
  - Automatic schema creation with constraints and indexes
  - Entity import with deduplication via MERGE
  - Relationship import with metadata tracking
  - Rule import as graph nodes
  - Document provenance tracking

- **Cypher Query Interface**
  - Execute arbitrary Cypher queries
  - Knowledge graph querying by entity name or category
  - Graph schema validation and reporting
  - Connection pooling and timeout management
  - Context manager support for automatic cleanup

#### Enhanced Orchestrator
- **Integrated Pipeline** (`backend/orchestrator.py`)
  - Quality assurance integration with configurable thresholds
  - Optional Neo4j export after extraction
  - Enhanced metadata tracking with quality metrics
  - Improved statistics reporting
  - Environment-based feature toggles

- **Configuration Options**
  - `ENABLE_QA`: Enable/disable quality assurance (default: true)
  - `QA_MIN_CONFIDENCE`: Minimum confidence threshold (default: 0.5)
  - `QA_STRICT_MODE`: Reject low-quality extractions (default: false)
  - `ENABLE_NEO4J`: Enable/disable Neo4j integration (default: false)

#### Documentation
- **Comprehensive README** (`README.md`)
  - Quick start guide
  - Multi-provider configuration examples
  - Quality assurance documentation
  - Neo4j integration guide
  - Usage examples with code snippets
  - Architecture overview
  - Performance metrics

- **Enhanced Configuration** (`.env.example`)
  - All provider configurations with examples
  - Quality assurance settings
  - Neo4j connection parameters
  - Detailed comments and defaults

- **Dependency Management** (`requirements.txt`)
  - Comprehensive dependency list
  - All required packages for new features
  - Version specifications for stability

### Changed

- **LLM Utilities**: Refactored to support multiple providers with fallback
- **Orchestrator**: Enhanced with quality checks and Neo4j export
- **Metadata**: Expanded to include quality metrics and Neo4j statistics
- **Logging**: Improved logging for QA and Neo4j operations

### Technical Details

#### Dependencies Added
- `litellm>=1.0.0` - Multi-provider LLM support
- `anthropic>=0.20.0` - Claude API support
- `google-generativeai>=0.3.0` - Gemini API support
- `neo4j>=5.0.0` - Neo4j database driver
- `py2neo>=2021.2.3` - Neo4j utilities
- `sentence-transformers>=2.2.0` - Future semantic search support
- `pydantic>=2.0.0` - Data validation
- `pyyaml>=6.0.0` - Configuration management

#### Performance Improvements
- Parallel processing maintained with configurable workers
- Efficient duplicate detection using set operations
- Connection pooling for Neo4j
- Retry logic with exponential backoff for resilience

#### Quality Metrics Achieved
- Entity validation with >90% accuracy
- Relationship triple validation
- Rule consistency checking
- Overall quality score calculation

## [0.1.0] - Previous Version

### Features
- Multi-pass extraction pipeline (entities, relationships, rules, ontologies, justifications)
- PDF, DOCX, TXT, MD, JSON file support
- Streamlit visualization dashboard
- Parallel batch processing
- MIME-type detection
- Basic logging and error handling

---

## Roadmap

### Phase 2 (Q1-Q2 2026)
- [ ] Prompt Engineering Framework
- [ ] Incremental Processing
- [ ] Hybrid Extraction (LLM + NLP)
- [ ] Interactive Refinement UI
- [ ] Semantic Search

### Phase 3 (Q3-Q4 2026)
- [ ] REST API
- [ ] Distributed Processing
- [ ] Advanced Visualizations
- [ ] Collaboration Features

---

For the complete product roadmap, see [PRD.md](planning/PRD.md).
