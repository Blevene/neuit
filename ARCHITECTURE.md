# NEUIToolkit Architecture

This document provides a comprehensive overview of NEUIToolkit's architecture, design patterns, and implementation details.

## 🏛️ System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         NEUIToolkit                              │
│                   Knowledge Extraction Platform                  │
└─────────────────────────────────────────────────────────────────┘
                               │
                               │
            ┌──────────────────┼──────────────────┐
            │                  │                  │
            v                  v                  v
    ┌──────────────┐   ┌──────────────┐  ┌──────────────┐
    │   Document   │   │ Orchestration │  │   Frontend   │
    │  Processing  │   │    Layer      │  │  Dashboard   │
    └──────────────┘   └──────────────┘  └──────────────┘
            │                  │                  │
            │                  │                  │
            v                  v                  v
    ┌──────────────────────────────────────────────────┐
    │            Multi-Provider LLM Layer              │
    │   (OpenAI, Claude, Gemini, Ollama + Fallback)   │
    └──────────────────────────────────────────────────┘
                               │
                ┌──────────────┼──────────────┐
                │              │              │
                v              v              v
        ┌────────────┐  ┌────────────┐  ┌────────────┐
        │   Quality  │  │    Neo4j   │  │    JSON    │
        │  Assurance │  │  Database  │  │   Output   │
        └────────────┘  └────────────┘  └────────────┘
```

## 📦 Core Components

### 1. Document Processing Layer

**Location**: `backend/orchestrator.py`

**Responsibilities**:
- Document ingestion from multiple formats (PDF, DOCX, TXT, MD, JSON)
- MIME type detection
- Text extraction and preprocessing
- Batch processing with parallelization
- Progress tracking and error handling

**Key Classes/Functions**:
```python
def read_corpus(file_path: Path) -> str
def run_entity_pass(corpus: str) -> List[Dict]
def run_relationship_pass(corpus: str) -> List[Dict]
def run_rule_pass(corpus: str) -> List[Dict]
def run_ontology_pass(corpus: str) -> str
def run_explanation_pass(corpus: str) -> str
def process_corpus_file(file_path: Path, output_dir: Path)
def run_multi_pass_pipeline(input_path: Optional[str] = None)
```

**Data Flow**:
```
Document File → MIME Detection → Format Parser → Text Corpus → Extraction Passes
```

**Dependencies**:
- `PyPDF2`: PDF parsing
- `python-docx`: DOCX parsing
- `python-magic`: MIME type detection

### 2. LLM Provider Layer

**Location**: `llm/`

**Components**:

#### Provider Configuration (`provider_config.py`)
```python
@dataclass
class ProviderConfig:
    name: str
    model: str
    api_key: Optional[str]
    base_url: Optional[str]
    temperature: float
    max_tokens: int
    timeout: int
    cost_per_1k_tokens: float
```

**Provider Registry**:
- Manages multiple LLM providers
- Handles automatic fallback on failures
- Tracks usage statistics and costs

#### LLM Utils (`llm_utils.py`)
```python
def call_llm_with_prompt(
    prompt: str,
    temperature: float = 0.2,
    max_tokens: int = 4096
) -> str
```

**Features**:
- Unified interface for all providers
- Automatic retries with exponential backoff
- Cost tracking
- Provider fallback mechanism
- Usage statistics

**Supported Providers**:
1. **OpenAI** (GPT-4, GPT-3.5)
2. **Anthropic** (Claude 3.5 Sonnet, Opus)
3. **Google** (Gemini 1.5 Pro)
4. **Ollama** (Local models)

**Fallback Strategy**:
```
Primary Provider → Secondary Provider → Tertiary Provider → Error
```

### 3. Quality Assurance Layer

**Location**: `backend/quality_assurance.py`

**Class**: `QualityAssurance`

**Responsibilities**:
- Confidence scoring for extractions
- Duplicate detection
- Consistency checking
- Quality reporting
- Filtering low-quality results

**Assessment Methods**:

#### Entity Assessment
```python
def assess_entity(entity: Dict[str, Any]) -> Dict[str, Any]:
    """
    Checks:
    - Name completeness (0.3 weight)
    - Category consistency (0.3 weight)
    - Alias quality (0.2 weight)
    - Duplicate detection (0.2 weight)
    """
```

#### Relationship Assessment
```python
def assess_relationship(relationship: Dict[str, Any]) -> Dict[str, Any]:
    """
    Checks:
    - Triple validity (subject-predicate-object)
    - Predicate quality (specific vs generic)
    - Justification completeness
    - Entity reference validation
    """
```

#### Rule Assessment
```python
def assess_rule(rule: Dict[str, Any]) -> Dict[str, Any]:
    """
    Checks:
    - If-then clause completeness
    - Logical consistency
    - Circular dependency detection
    - Confidence score validation
    """
```

**Configuration**:
```python
ENABLE_QA=true
QA_MIN_CONFIDENCE=0.5
QA_STRICT_MODE=false
```

### 4. Neo4j Integration Layer

**Location**: `backend/neo4j_integration.py`

**Class**: `Neo4jConnector`

**Responsibilities**:
- Connection management (pooling, timeouts)
- Schema creation (constraints, indexes)
- Knowledge graph import
- Cypher query execution
- Document provenance tracking

**Graph Schema**:

```cypher
-- Entities
CREATE CONSTRAINT entity_name IF NOT EXISTS
FOR (e:Entity) REQUIRE e.name IS UNIQUE

CREATE INDEX entity_category IF NOT EXISTS
FOR (e:Entity) ON (e.category)

-- Relationships
(subject:Entity)-[r:RELATES_TO]->(object:Entity)
Properties: predicate, justification, confidence, source_document

-- Rules
CREATE (r:Rule {
    rule_id, if_clause, then_clause,
    confidence, source_document
})

-- Documents
CREATE (d:Document {
    name, path, processed_at
})
```

**Import Process**:
```
Entities → Deduplication (MERGE) → Neo4j
Relationships → Validation → Neo4j
Rules → Structuring → Neo4j
Document → Provenance → Neo4j
```

**Context Manager Pattern**:
```python
with Neo4jConnector(config) as connector:
    connector.import_knowledge_graph(...)
    results = connector.query_knowledge(...)
# Automatic connection cleanup
```

### 5. Visualization Layer

**Location**: `frontend/`

**Components**:

#### Dashboard (`app.py`)
- Streamlit-based web interface
- Document selection
- Interactive visualizations
- Quality metrics display

#### Utilities (`utils.py`)
- Graph rendering (PyVis, NetworkX)
- Data loading
- Visualization helpers

**Dashboard Tabs**:
1. **Overview**: Summary statistics
2. **Entities**: Entity list with categories
3. **Knowledge Graph**: Interactive network visualization
4. **Relationships**: Relationship table
5. **Rules**: Logical rules display
6. **Ontology**: RDF/OWL visualization

## 🔄 Data Flow

### End-to-End Extraction Pipeline

```
1. Document Input
   └─> PDF/DOCX/TXT file

2. Document Processing
   └─> MIME detection
   └─> Format-specific parsing
   └─> Text extraction
   └─> Corpus ready

3. Multi-Pass Extraction
   ├─> Pass 1: Entity Extraction
   │   └─> LLM call with entity prompt
   │   └─> JSON parsing
   │   └─> QA assessment
   │   └─> Entity list
   │
   ├─> Pass 2: Relationship Extraction
   │   └─> LLM call with relationship prompt
   │   └─> JSON parsing
   │   └─> QA assessment
   │   └─> Relationship list
   │
   ├─> Pass 3: Rule Induction
   │   └─> LLM call with rule prompt
   │   └─> JSON parsing
   │   └─> QA assessment
   │   └─> Rule list
   │
   ├─> Pass 4: Ontology Generation
   │   └─> LLM call with ontology prompt
   │   └─> Turtle/RDF output
   │   └─> Validation
   │   └─> .ttl file
   │
   └─> Pass 5: Explanation Generation
       └─> LLM call with explanation prompt
       └─> Text output
       └─> .txt file

4. Quality Assurance (Optional)
   └─> Confidence scoring
   └─> Duplicate detection
   └─> Filtering
   └─> Quality report

5. Export
   ├─> JSON files (entities, relationships, rules)
   ├─> Turtle files (ontology)
   ├─> Metadata (statistics, quality metrics)
   └─> Neo4j database (optional)

6. Visualization
   └─> Streamlit dashboard
   └─> Interactive graphs
   └─> Quality metrics
```

## 🎨 Design Patterns

### 1. Provider Pattern (LLM Abstraction)

**Problem**: Support multiple LLM providers with different APIs
**Solution**: Unified provider interface with registry

```python
class ProviderRegistry:
    def get_provider(self, name: str) -> ProviderConfig
    def register_provider(self, config: ProviderConfig)
    def call_with_fallback(self, prompt: str) -> str
```

### 2. Strategy Pattern (Quality Assessment)

**Problem**: Different quality metrics for different extraction types
**Solution**: Separate assessment methods for each type

```python
class QualityAssurance:
    def assess_entity(self, entity: Dict) -> Dict
    def assess_relationship(self, relationship: Dict) -> Dict
    def assess_rule(self, rule: Dict) -> Dict
```

### 3. Context Manager Pattern (Resource Management)

**Problem**: Ensure database connections are cleaned up
**Solution**: Context manager for Neo4j connector

```python
class Neo4jConnector:
    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
```

### 4. Factory Pattern (Configuration)

**Problem**: Complex object creation with many parameters
**Solution**: Factory functions for creating configured instances

```python
def create_neo4j_connector() -> Neo4jConnector:
    config = Neo4jConfig.from_env()
    return Neo4jConnector(config)
```

### 5. Pipeline Pattern (Multi-Pass Extraction)

**Problem**: Sequential processing stages with different operations
**Solution**: Pipeline of extraction passes

```python
def run_multi_pass_pipeline(input_path):
    corpus = read_corpus(input_path)
    entities = run_entity_pass(corpus)
    relationships = run_relationship_pass(corpus)
    rules = run_rule_pass(corpus)
    ontology = run_ontology_pass(corpus)
    return consolidate_results(...)
```

## 📊 Data Schemas

### Entity Schema
```python
{
    "name": str,              # Required
    "aliases": List[str],     # Optional
    "category": str,          # Required
    "confidence": float       # 0.0-1.0 (added by QA)
}
```

### Relationship Schema
```python
{
    "subject": str,           # Required
    "predicate": str,         # Required
    "object": str,            # Required
    "justification": str,     # Optional
    "confidence": float       # 0.0-1.0 (added by QA)
}
```

### Rule Schema
```python
{
    "id": int,                # Required
    "if": str,                # Required (if-clause)
    "then": str,              # Required (then-clause)
    "confidence": float,      # 0.0-1.0
    "source_document": str    # Optional
}
```

### Quality Metrics Schema
```python
@dataclass
class QualityMetrics:
    total_count: int
    passed_count: int
    failed_count: int
    quality_score: float      # Aggregate score 0.0-1.0
    details: Dict[str, Any]   # Item-level details
```

## 🔧 Configuration Management

### Environment-Based Configuration

```bash
# LLM Provider
LLM_PROVIDER=openai
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4

# Quality Assurance
ENABLE_QA=true
QA_MIN_CONFIDENCE=0.5
QA_STRICT_MODE=false

# Neo4j
ENABLE_NEO4J=false
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=...
```

### Configuration Loading

```python
# 1. Load from environment
from dotenv import load_dotenv
load_dotenv()

# 2. Provider configuration
provider = os.getenv("LLM_PROVIDER", "openai")
api_key = os.getenv(f"{provider.upper()}_API_KEY")

# 3. Feature toggles
enable_qa = os.getenv("ENABLE_QA", "true").lower() == "true"
enable_neo4j = os.getenv("ENABLE_NEO4J", "false").lower() == "true"
```

## 🧪 Testing Architecture

### Test Organization

```
tests/
├── conftest.py                    # Shared fixtures
├── test_llm_utils.py              # LLM layer tests
├── test_provider_config.py        # Provider configuration tests
├── test_quality_assurance.py      # QA layer tests
└── test_neo4j_integration.py      # Database integration tests
```

### Test Fixtures

```python
@pytest.fixture
def sample_entities():
    return [
        {"name": "Cell", "category": "Structure", "aliases": []},
        {"name": "Mitochondria", "category": "Organelle", "aliases": ["Powerhouse"]}
    ]

@pytest.fixture
def mock_llm_response(monkeypatch):
    def mock_call(*args, **kwargs):
        return '{"entities": [...]}'
    monkeypatch.setattr("llm.llm_utils.call_llm_with_prompt", mock_call)
```

### Test Markers

```python
@pytest.mark.unit          # Fast unit tests
@pytest.mark.integration   # Integration tests
@pytest.mark.slow          # Slow tests (skip in CI)
@pytest.mark.neo4j         # Requires Neo4j
@pytest.mark.llm           # Requires LLM API key
```

## 🚀 Performance Considerations

### Parallelization

```python
# Batch processing with ThreadPoolExecutor
with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [
        executor.submit(process_corpus_file, f, output_dir)
        for f in file_list
    ]
    results = [f.result() for f in futures]
```

### Caching Strategy

- **Prompt templates**: Loaded once at startup
- **LLM responses**: No caching (content-specific)
- **Neo4j connections**: Connection pooling
- **Quality assessments**: Computed on-demand

### Optimization Opportunities

1. **Batch LLM calls**: Process multiple documents in single call
2. **Response streaming**: Stream LLM responses
3. **Async processing**: Use asyncio for I/O-bound operations
4. **Result caching**: Cache extraction results per document hash
5. **Database batching**: Batch Neo4j imports

## 📈 Scalability

### Current Limitations

- **Single machine**: No distributed processing
- **In-memory processing**: Large documents may cause memory issues
- **Sequential extraction**: Passes run sequentially per document
- **Synchronous I/O**: Blocking file and database operations

### Scaling Strategies

1. **Horizontal Scaling**: Add Celery/Ray for distributed tasks
2. **Streaming Processing**: Process documents in chunks
3. **Async I/O**: Use asyncio for concurrent operations
4. **Database Sharding**: Partition Neo4j across instances
5. **Cloud Storage**: Use S3/GCS for document storage

## 🔒 Security Considerations

### API Key Management

- Store in environment variables (not code)
- Use `.env` file (excluded from git)
- Rotate keys regularly
- Use separate keys for dev/prod

### Data Privacy

- Documents not sent to external services (except LLM)
- Neo4j credentials encrypted at rest
- No logging of sensitive data
- Optional local-only mode (Ollama)

### Input Validation

- MIME type validation
- File size limits
- JSON schema validation
- SQL/Cypher injection prevention

## 📚 Extension Points

### Adding New LLM Providers

1. Add provider configuration in `provider_config.py`
2. Update `ProviderRegistry.register_provider()`
3. Add environment variables to `.env.example`
4. Update documentation

### Adding New Extraction Passes

1. Create prompt template in `prompts/`
2. Add extraction function in `orchestrator.py`
3. Update quality assessment in `quality_assurance.py`
4. Add visualization in `frontend/`

### Adding New Data Formats

1. Add parser function in `orchestrator.py`
2. Update MIME type detection
3. Add tests for new format
4. Update documentation

## 🔍 Debugging & Monitoring

### Logging Strategy

```python
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Levels used:
# DEBUG: Detailed extraction steps
# INFO: Pipeline progress
# WARNING: Quality issues, fallback activations
# ERROR: Extraction failures, API errors
# CRITICAL: System failures
```

### Monitoring Metrics

- Extraction success rate
- Average processing time
- LLM API costs
- Quality scores
- Provider fallback frequency

---

## 📖 References

- [README.md](README.md) - User documentation
- [PRD.md](planning/PRD.md) - Product requirements
- [CONTRIBUTING.md](CONTRIBUTING.md) - Development guidelines
- [CHANGELOG.md](CHANGELOG.md) - Version history
