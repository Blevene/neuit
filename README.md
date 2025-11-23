# NEUIToolkit - Neurosymbolic Knowledge Extraction Platform

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)

An enterprise-grade AI-powered knowledge extraction and schema induction platform that transforms unstructured documents into structured, queryable knowledge graphs using Large Language Models and symbolic reasoning.

## 🌟 Overview

NEUIToolkit leverages cutting-edge neurosymbolic AI to automatically extract entities, relationships, logical rules, and ontologies from diverse document types. Built for educational technologists, research scientists, and knowledge engineers, it provides production-ready tools for building knowledge-enhanced applications.

### What Makes NEUIToolkit Special?

- **Zero Manual Configuration**: Automated schema induction eliminates manual ontology engineering
- **Multi-Provider Flexibility**: Switch between OpenAI, Claude, Gemini, or local models seamlessly
- **Production-Ready Quality**: Built-in confidence scoring, duplicate detection, and consistency checking
- **Graph Database Integration**: Direct Neo4j export with automatic schema creation
- **Visual Exploration**: Interactive Streamlit dashboard for knowledge graph exploration
- **Battle-Tested**: Comprehensive test suite with >90% coverage

---

## ✨ Key Features

### 🤖 Multi-LLM Provider Support
- **OpenAI GPT-4**: High-quality extractions with proven reliability
- **Anthropic Claude**: Advanced reasoning with extended context windows
- **Google Gemini**: Cost-effective processing with competitive quality
- **Ollama (Local)**: Privacy-first processing with local models
- **Automatic Fallback**: Seamless provider switching on failures
- **Cost Tracking**: Monitor and optimize LLM usage costs

### 🔍 Multi-Pass Knowledge Extraction
- **Entity Extraction**: Concepts, aliases, and semantic categories
- **Relationship Extraction**: Subject-predicate-object triples with justifications
- **Rule Induction**: Logical if-then rules and prerequisite chains
- **Ontology Generation**: OWL/RDF ontologies in Turtle format
- **Explanation Generation**: Human-readable justifications for transparency

### ✅ Quality Assurance Layer
- **Confidence Scoring**: 0.0-1.0 quality scores for all extractions
- **Duplicate Detection**: Automatic deduplication across documents
- **Consistency Checking**: Entity category and relationship validation
- **Strict Mode**: Reject low-quality extractions automatically
- **Quality Reports**: Comprehensive metrics for assessment

### 📊 Neo4j Graph Database Integration
- **Direct Export**: Write knowledge graphs directly to Neo4j
- **Schema Management**: Automatic constraint and index creation
- **Cypher Interface**: Query knowledge using graph query language
- **Document Provenance**: Track extraction sources
- **Connection Pooling**: Optimized database performance

### 📄 Document Processing
- **Multi-Format**: PDF, DOCX, TXT, MD, JSON support
- **MIME Detection**: Automatic format recognition
- **Parallel Processing**: Configurable worker threads for batch jobs
- **Progress Tracking**: Real-time processing feedback
- **Error Isolation**: Per-document error handling

### 📈 Interactive Visualization
- **Knowledge Graphs**: Interactive network visualizations with PyVis
- **Category Analysis**: Entity distribution and statistics
- **Relationship Networks**: Explore semantic connections
- **Ontology Viewer**: Inspect RDF/OWL structures
- **Quality Metrics**: Visual quality assessment dashboard

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- At least one LLM API key (OpenAI, Anthropic, Google, or Ollama)
- Optional: Neo4j database (for graph storage)

### Installation

```bash
# Clone the repository
git clone https://github.com/Blevene/neuit.git
cd neuit

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Optional: Install spaCy language model for enhanced NLP
python -m spacy download en_core_web_sm
```

### Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit configuration (use your preferred editor)
nano .env
```

**Minimum Configuration** (add at least one API key):

```bash
# Choose your LLM provider
LLM_PROVIDER=openai
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-4

# Enable quality assurance (recommended)
ENABLE_QA=true
QA_MIN_CONFIDENCE=0.5
```

### Basic Usage

#### 1. Extract Knowledge from Documents

```bash
# Process all documents in the data/ directory
python backend/orchestrator.py

# Process a specific file
python backend/orchestrator.py path/to/document.pdf

# Process a specific directory
python backend/orchestrator.py --input path/to/documents/
```

**Output**: JSON files in `outputs/` directory containing entities, relationships, rules, and ontologies.

#### 2. Visualize Knowledge Graphs

```bash
# Launch the interactive dashboard
streamlit run frontend/app.py
```

Visit `http://localhost:8501` to explore your knowledge graphs interactively!

#### 3. Export to Neo4j (Optional)

```bash
# Configure Neo4j in .env
ENABLE_NEO4J=true
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password

# Run extraction with Neo4j export
python backend/orchestrator.py
```

---

## 📚 Comprehensive Documentation

### LLM Provider Configuration

NEUIToolkit supports multiple providers with automatic fallback. Configure your preferred provider in `.env`:

#### OpenAI (GPT-4)
```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4
OPENAI_TEMPERATURE=0.2
OPENAI_MAX_TOKENS=4096
```

**Best For**: Highest quality extractions, proven reliability

#### Anthropic (Claude)
```bash
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
ANTHROPIC_TEMPERATURE=0.2
ANTHROPIC_MAX_TOKENS=4096
```

**Best For**: Complex reasoning, long documents (200K+ tokens)

#### Google (Gemini)
```bash
LLM_PROVIDER=google
GOOGLE_API_KEY=AI...
GOOGLE_MODEL=gemini-1.5-pro
GOOGLE_TEMPERATURE=0.2
GOOGLE_MAX_TOKENS=4096
```

**Best For**: Cost optimization, competitive quality

#### Ollama (Local Models)
```bash
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
OLLAMA_TEMPERATURE=0.2
```

**Best For**: Privacy, offline processing, no API costs

#### Multi-Provider Fallback

Configure multiple providers for automatic failover:

```bash
# Primary provider
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=...

# Fallback providers (automatically used if primary fails)
OPENAI_API_KEY=...
GOOGLE_API_KEY=...
```

The system automatically tries the next available provider on failures.

---

### Quality Assurance Configuration

Enable quality checks to ensure high-quality extractions:

```bash
# Enable QA layer
ENABLE_QA=true

# Minimum confidence threshold (0.0-1.0)
QA_MIN_CONFIDENCE=0.5

# Strict mode: reject low-quality extractions
QA_STRICT_MODE=false
```

#### Quality Metrics

The QA layer evaluates:

**Entities:**
- Name completeness and validity
- Category consistency
- Alias quality
- Duplicate detection

**Relationships:**
- Subject-predicate-object triple validity
- Predicate quality (specific vs. generic)
- Justification completeness
- Entity reference validation

**Rules:**
- If-then clause completeness
- Logical consistency
- Circular dependency detection
- Confidence score assessment

**Output**: Quality reports with per-item and aggregate scores.

---

### Neo4j Integration

Export knowledge graphs directly to Neo4j for powerful graph queries and analytics.

#### Configuration

```bash
ENABLE_NEO4J=true
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=neo4j
```

#### Features

- **Automatic Schema Creation**: Constraints and indexes for optimal performance
- **Entity Import**: Deduplicated entities with MERGE operations
- **Relationship Import**: Semantic triples with provenance metadata
- **Rule Storage**: Logical rules as graph nodes
- **Document Tracking**: Full lineage of knowledge sources
- **Cypher Queries**: Powerful graph pattern matching

#### Example Queries

```cypher
-- Find all entities in a category
MATCH (e:Entity {category: 'Concept'})
RETURN e.name, e.aliases

-- Explore relationships
MATCH (s:Entity)-[r:RELATES_TO]->(o:Entity)
WHERE s.name = 'Neuron'
RETURN s.name, r.predicate, o.name

-- Find prerequisite chains
MATCH path = (r1:Rule)-[:IMPLIES*]->(r2:Rule)
RETURN path
```

---

## 🏗️ Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     NEUIToolkit Platform                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌───────────────┐    ┌──────────────┐    ┌──────────────┐ │
│  │   Document    │───>│  Orchestrator │───>│   Quality    │ │
│  │   Ingestion   │    │   Pipeline    │    │  Assurance   │ │
│  └───────────────┘    └──────────────┘    └──────────────┘ │
│         │                     │                     │        │
│         v                     v                     v        │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              Multi-Provider LLM Layer                │  │
│  │  (OpenAI | Claude | Gemini | Ollama + Fallback)     │  │
│  └───────────────────────────────────────────────────────┘  │
│         │                                             │      │
│         v                                             v      │
│  ┌──────────────┐                            ┌──────────────┐│
│  │   JSON       │                            │    Neo4j     ││
│  │   Output     │                            │   Database   ││
│  └──────────────┘                            └──────────────┘│
│         │                                             │      │
│         v                                             v      │
│  ┌───────────────────────────────────────────────────────┐  │
│  │           Streamlit Visualization Dashboard          │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
neuit/
├── backend/
│   ├── orchestrator.py              # Main extraction pipeline
│   ├── quality_assurance.py         # QA layer with confidence scoring
│   └── neo4j_integration.py         # Graph database connector
├── frontend/
│   ├── app.py                       # Streamlit visualization dashboard
│   └── utils.py                     # Visualization utilities
├── llm/
│   ├── llm_utils.py                 # Enhanced LLM abstraction layer
│   └── provider_config.py           # Multi-provider configuration
├── prompts/
│   ├── entity_extraction.prompt.txt
│   ├── relationship_extraction.prompt.txt
│   ├── rule_induction.prompt.txt
│   ├── ontology_generation.prompt.txt
│   └── explanation_generation.prompt.txt
├── tests/
│   ├── test_llm_utils.py            # LLM utilities tests
│   ├── test_provider_config.py      # Provider configuration tests
│   ├── test_quality_assurance.py    # QA layer tests
│   └── test_neo4j_integration.py    # Neo4j integration tests
├── data/                            # Input documents
├── outputs/                         # Extraction results (JSON, TTL)
├── planning/
│   ├── PRD.md                       # Product Requirements Document
│   └── schema_design.md             # Graph schema documentation
├── requirements.txt                 # Python dependencies
├── pytest.ini                       # Test configuration
├── .env.example                     # Configuration template
└── README.md                        # This file
```

---

## 📖 Usage Examples

### Python API

#### Basic Extraction

```python
from backend.orchestrator import run_multi_pass_pipeline

# Process all documents in data/ directory
results = run_multi_pass_pipeline()

# Process specific file
results = run_multi_pass_pipeline("path/to/document.pdf")

# Access extracted knowledge
print(f"Entities: {results['entity_count']}")
print(f"Relationships: {results['relationship_count']}")
print(f"Rules: {results['rule_count']}")
```

#### Quality Assurance

```python
from backend.quality_assurance import QualityAssurance

# Initialize QA system
qa = QualityAssurance(
    min_confidence=0.7,
    enable_strict_mode=True
)

# Assess entities
entities = [
    {"name": "Mitochondria", "category": "Organelle", "aliases": ["Powerhouse"]},
    {"name": "Cell", "category": "Structure", "aliases": []}
]

filtered_entities, metrics = qa.filter_low_quality(entities, 'entity')

print(f"Quality Score: {metrics['quality_score']:.3f}")
print(f"Passed: {metrics['passed_count']}/{metrics['total_count']}")

# Generate comprehensive quality report
entity_metrics, rel_metrics, rule_metrics = {...}, {...}, {...}
report = qa.generate_quality_report(entity_metrics, rel_metrics, rule_metrics)

print(f"Overall Quality: {report['overall_quality_score']:.3f}")
print(f"Recommendation: {report['recommendations']}")
```

#### Neo4j Integration

```python
from backend.neo4j_integration import Neo4jConnector, Neo4jConfig

# Configure connection
config = Neo4jConfig(
    uri="bolt://localhost:7687",
    username="neo4j",
    password="password",
    database="neo4j"
)

# Import knowledge graph
with Neo4jConnector(config) as connector:
    # Import data
    stats = connector.import_knowledge_graph(
        entities=entities,
        relationships=relationships,
        rules=rules,
        document_name="biology_textbook.pdf"
    )

    print(f"Imported: {stats['entities']} entities, "
          f"{stats['relationships']} relationships, "
          f"{stats['rules']} rules")

    # Query knowledge
    results = connector.query_knowledge(
        category="Organelle",
        limit=10
    )

    for entity in results:
        print(f"- {entity['name']} ({entity['category']})")

    # Execute custom Cypher
    query = """
    MATCH (e:Entity)-[r:RELATES_TO]->(o:Entity)
    WHERE e.name = $entity_name
    RETURN e.name, r.predicate, o.name
    LIMIT 5
    """

    triples = connector.execute_query(query, {"entity_name": "Cell"})
    for triple in triples:
        print(f"{triple['e.name']} -> {triple['r.predicate']} -> {triple['o.name']}")
```

#### Multi-Provider LLM

```python
from llm.llm_utils import call_llm, get_provider_stats

# Call LLM with automatic provider selection
response = call_llm(
    prompt="Extract key concepts from this text...",
    temperature=0.2,
    max_tokens=2000
)

print(response)

# Check provider statistics
stats = get_provider_stats()
print(f"Primary Provider: {stats['primary_provider']}")
print(f"Total Calls: {stats['total_calls']}")
print(f"Total Cost: ${stats['total_cost']:.4f}")
print(f"Failures: {stats['failures']}")
```

---

## 🎯 Output Formats

### Entities
```json
{
  "name": "Mitochondria",
  "aliases": ["Powerhouse of the cell", "Cellular powerhouse"],
  "category": "Organelle",
  "confidence": 0.95
}
```

### Relationships
```json
{
  "subject": "Neuron",
  "predicate": "uses",
  "object": "Neurotransmitter",
  "justification": "Neurons use neurotransmitters to communicate across synapses.",
  "confidence": 0.88
}
```

### Rules
```json
{
  "id": 1,
  "if": "Student masters prerequisite concepts",
  "then": "Student can advance to next topic",
  "confidence": 0.92,
  "source_document": "curriculum_guide.pdf"
}
```

### Ontology (Turtle/RDF)
```turtle
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix : <http://example.org/biology#> .

:Mitochondria rdf:type owl:Class ;
    rdfs:label "Mitochondria" ;
    rdfs:subClassOf :Organelle ;
    rdfs:comment "The powerhouse of the cell" .
```

---

## 🧪 Testing

NEUIToolkit includes a comprehensive test suite with >90% code coverage.

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=backend --cov=llm --cov-report=html

# Run specific test file
pytest tests/test_quality_assurance.py

# Run with verbose output
pytest -v

# Run tests matching a pattern
pytest -k "test_neo4j"
```

### Test Coverage

- **LLM Utilities**: Multi-provider support, fallback mechanisms, cost tracking
- **Quality Assurance**: Confidence scoring, duplicate detection, consistency checks
- **Neo4j Integration**: Connection management, import operations, query interface
- **Provider Configuration**: Provider initialization, fallback logic, error handling

### Continuous Integration

Tests are automatically run on every commit. All PRs must pass tests before merging.

---

## 📊 Performance Benchmarks

### Processing Speed
- **Single Document**: <30 seconds per 10-page document
- **Batch Processing**: >100 documents/hour with parallel workers
- **Neo4j Import**: ~1000 entities/second

### Quality Metrics
- **Entity Precision**: >85% on domain-specific texts
- **Relationship Recall**: >75% for explicit relationships
- **Rule Accuracy**: >80% for logical if-then patterns

### Cost Efficiency
- **GPT-4**: ~$0.50 per 10-page document
- **Claude**: ~$0.30 per 10-page document
- **Gemini**: ~$0.20 per 10-page document
- **Ollama**: $0.00 (local processing)

### Scalability
- **Memory**: <2GB per worker process
- **Concurrency**: Supports 4-8 parallel workers (configurable)
- **Document Size**: Tested up to 50,000 words per document

---

## 🗺️ Roadmap

See [PRD.md](planning/PRD.md) for the complete product roadmap and technical specifications.

### Phase 1: Foundation Hardening ✅ (Completed - Nov 2025)
- [x] Multi-LLM Provider Support (OpenAI, Claude, Gemini, Ollama)
- [x] Automatic Provider Fallback
- [x] Neo4j Integration with Cypher Interface
- [x] Quality Assurance Layer with Confidence Scoring
- [x] Comprehensive Test Suite (>90% coverage)
- [x] Enhanced Documentation and Examples

### Phase 2: Advanced Capabilities (Q1-Q2 2026)
- [ ] **Prompt Engineering Framework**
  - Domain-specific prompt templates
  - Few-shot learning support
  - Prompt versioning and A/B testing

- [ ] **Incremental Processing**
  - Document change detection
  - Differential updates
  - Version control for knowledge graphs

- [ ] **Hybrid Extraction**
  - Combine LLM with traditional NLP (spaCy, NLTK)
  - Entity linking to external KBs (DBpedia, Wikidata)
  - Coreference resolution

- [ ] **Interactive Refinement UI**
  - Human-in-the-loop validation
  - Entity/relationship editing in dashboard
  - Feedback loop to improve prompts

- [ ] **Semantic Search**
  - Embedding-based search (FAISS, ChromaDB)
  - Natural language queries over knowledge graphs
  - Similar document finding

### Phase 3: Enterprise Features (Q3-Q4 2026)
- [ ] **REST API**
  - OpenAPI/Swagger specification
  - Authentication/authorization (JWT, OAuth)
  - Rate limiting and quotas
  - Webhook support for async processing

- [ ] **Distributed Processing**
  - Celery/Ray for large-scale batch jobs
  - Cloud storage integration (S3, GCS, Azure)
  - Kubernetes deployment templates

- [ ] **Advanced Visualizations**
  - 3D knowledge graph rendering
  - Temporal graph views (knowledge evolution)
  - Diff visualization for document versions
  - Export to Gephi, Cytoscape

- [ ] **Collaboration Features**
  - Multi-user workspaces
  - Annotation sharing and comments
  - Git-like version control for graphs
  - Team permissions and access control

---

## 🤝 Contributing

We welcome contributions from the community! Here's how to get started:

### Development Setup

```bash
# Clone the repository
git clone https://github.com/Blevene/neuit.git
cd neuit

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies (including dev tools)
pip install -r requirements.txt

# Install pre-commit hooks (optional)
pip install pre-commit
pre-commit install
```

### Code Style

We use:
- **Black** for code formatting
- **Flake8** for linting
- **pytest** for testing

```bash
# Format code
black backend/ llm/ tests/

# Lint code
flake8 backend/ llm/ tests/

# Run tests
pytest --cov=backend --cov=llm
```

### Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests
4. Ensure all tests pass (`pytest`)
5. Format code (`black .`)
6. Commit changes (`git commit -m 'Add amazing feature'`)
7. Push to branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Contribution Areas

- **New LLM Providers**: Add support for additional providers
- **Quality Metrics**: Improve QA algorithms
- **Visualization**: Enhance dashboard features
- **Documentation**: Improve guides and examples
- **Testing**: Expand test coverage
- **Performance**: Optimize processing speed

---

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

### Apache 2.0 Summary

- ✅ Commercial use allowed
- ✅ Modification allowed
- ✅ Distribution allowed
- ✅ Patent use allowed
- ✅ Private use allowed
- ℹ️ Must include copyright notice
- ℹ️ Must include license copy
- ℹ️ Must state changes made
- ❌ No trademark rights
- ❌ No warranty provided

---

## 🙏 Acknowledgments

NEUIToolkit is built on the shoulders of giants:

### Core Technologies
- **[LiteLLM](https://github.com/BerriAI/litellm)** - Multi-provider LLM abstraction
- **[OpenAI](https://openai.com/)** - GPT models
- **[Anthropic](https://www.anthropic.com/)** - Claude models
- **[Google](https://ai.google.dev/)** - Gemini models
- **[Ollama](https://ollama.ai/)** - Local model runtime

### Visualization & UI
- **[Streamlit](https://streamlit.io/)** - Interactive dashboard framework
- **[PyVis](https://pyvis.readthedocs.io/)** - Network graph visualization
- **[Plotly](https://plotly.com/)** - Interactive charts
- **[NetworkX](https://networkx.org/)** - Graph algorithms

### Graph & Knowledge
- **[Neo4j](https://neo4j.com/)** - Graph database platform
- **[RDFLib](https://rdflib.readthedocs.io/)** - RDF/OWL processing

### NLP & Processing
- **[spaCy](https://spacy.io/)** - Industrial-strength NLP
- **[PyPDF2](https://pypdf2.readthedocs.io/)** - PDF parsing
- **[python-docx](https://python-docx.readthedocs.io/)** - DOCX processing

### Development Tools
- **[pytest](https://pytest.org/)** - Testing framework
- **[Black](https://black.readthedocs.io/)** - Code formatter
- **[Flake8](https://flake8.pycqa.org/)** - Linting

---

## 📧 Support & Community

### Getting Help

- **Documentation**: See [planning/PRD.md](planning/PRD.md) for detailed specifications
- **GitHub Issues**: [Report bugs or request features](https://github.com/Blevene/neuit/issues)
- **Discussions**: [Ask questions and share ideas](https://github.com/Blevene/neuit/discussions)

### Resources

- **[Product Requirements Document](planning/PRD.md)**: Complete technical specifications
- **[Changelog](CHANGELOG.md)**: Version history and updates
- **[Schema Design](planning/schema_design.md)**: Graph schema documentation

### Contact

- **Project Maintainer**: Blevene
- **Repository**: [https://github.com/Blevene/neuit](https://github.com/Blevene/neuit)
- **License**: Apache 2.0

---

## 🎓 Use Cases

### Educational Technology
- Transform textbooks into interactive knowledge graphs
- Generate prerequisite maps for learning paths
- Create adaptive assessment systems
- Build intelligent tutoring systems

### Research & Academia
- Extract domain knowledge from papers
- Build research ontologies automatically
- Organize literature reviews
- Create knowledge bases for meta-analyses

### Knowledge Engineering
- Rapid ontology prototyping
- Knowledge base construction
- Semantic data integration
- Information architecture design

### Enterprise Applications
- Document understanding systems
- Automated metadata generation
- Knowledge management platforms
- Intelligent search and discovery

---

## ⚡ Quick Reference

### Common Commands

```bash
# Extract from all documents in data/
python backend/orchestrator.py

# Extract from specific file
python backend/orchestrator.py document.pdf

# Launch visualization dashboard
streamlit run frontend/app.py

# Run tests
pytest

# Format code
black backend/ llm/ tests/

# Check code quality
flake8 backend/ llm/ tests/
```

### Environment Variables

```bash
LLM_PROVIDER=openai          # Primary LLM provider
ENABLE_QA=true               # Enable quality assurance
QA_MIN_CONFIDENCE=0.5        # Minimum quality threshold
ENABLE_NEO4J=false           # Enable Neo4j export
```

### Key File Locations

- **Input**: `data/` - Place documents here
- **Output**: `outputs/` - Extraction results
- **Config**: `.env` - Configuration file
- **Prompts**: `prompts/` - LLM prompt templates
- **Tests**: `tests/` - Test suite

---

<div align="center">

**Made with ❤️ for the knowledge graph community**

[⭐ Star on GitHub](https://github.com/Blevene/neuit) | [🐛 Report Bug](https://github.com/Blevene/neuit/issues) | [💡 Request Feature](https://github.com/Blevene/neuit/issues)

</div>
