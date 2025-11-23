# NEUIToolkit - Neurosymbolic Knowledge Extraction Platform

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)

An AI-powered knowledge extraction and schema induction platform that transforms unstructured documents into structured, queryable knowledge graphs using Large Language Models and symbolic reasoning.

## ✨ Key Features

- **🤖 Multi-LLM Provider Support**: Use OpenAI, Claude, Gemini, or local models (Ollama)
- **🔍 Multi-Pass Extraction**: Entities, relationships, rules, ontologies, and justifications
- **✅ Quality Assurance**: Confidence scoring, duplicate detection, and consistency checking
- **📊 Neo4j Integration**: Direct export to graph databases with Cypher query interface
- **📄 Multi-Format Support**: PDF, DOCX, TXT, MD, and JSON files
- **🎯 Parallel Processing**: Batch processing with configurable workers
- **📈 Visualization Dashboard**: Interactive knowledge graph exploration with Streamlit

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/neuit.git
cd neuit

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your API key(s)
# At minimum, set OPENAI_API_KEY or another provider
nano .env
```

### 3. Run Extraction

```bash
# Process documents in the data/ directory
python backend/orchestrator.py

# Or process a specific file
python backend/orchestrator.py path/to/your/document.pdf

# Or process a specific directory
python backend/orchestrator.py --input path/to/documents/
```

### 4. Visualize Results

```bash
# Launch the Streamlit dashboard
streamlit run frontend/app.py
```

Visit `http://localhost:8501` to explore your knowledge graphs!

## 📚 Documentation

### LLM Provider Configuration

NEUIToolkit supports multiple LLM providers with automatic fallback:

#### OpenAI (GPT-4)
```bash
LLM_PROVIDER=openai
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4
```

#### Anthropic (Claude)
```bash
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_key_here
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
```

#### Google (Gemini)
```bash
LLM_PROVIDER=google
GOOGLE_API_KEY=your_key_here
GOOGLE_MODEL=gemini-1.5-pro
```

#### Ollama (Local Models)
```bash
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3
```

**Fallback Support**: Configure multiple providers, and the system will automatically try the next one if the primary fails.

### Quality Assurance

Enable quality assurance to filter and validate extracted knowledge:

```bash
ENABLE_QA=true
QA_MIN_CONFIDENCE=0.5      # Minimum confidence threshold (0.0-1.0)
QA_STRICT_MODE=false       # Reject low-quality extractions
```

**Features**:
- Confidence scoring for entities, relationships, and rules
- Duplicate detection
- Consistency checking
- Category validation
- Automatic quality reports

### Neo4j Integration

Export knowledge graphs directly to Neo4j:

```bash
ENABLE_NEO4J=true
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=neo4j
```

**Features**:
- Automatic schema creation with constraints and indexes
- Direct import of entities, relationships, and rules
- Cypher query interface
- Graph schema validation
- Document tracking

## 🏗️ Architecture

```
neuit/
├── backend/
│   ├── orchestrator.py              # Main extraction pipeline
│   ├── quality_assurance.py         # QA layer with confidence scoring
│   └── neo4j_integration.py         # Neo4j database connector
├── frontend/
│   ├── app.py                       # Streamlit visualization dashboard
│   └── utils.py                     # Visualization utilities
├── llm/
│   ├── llm_utils.py                 # Enhanced LLM abstraction
│   └── provider_config.py           # Multi-provider configuration
├── prompts/
│   ├── entity_extraction.prompt.txt
│   ├── relationship_extraction.prompt.txt
│   ├── rule_induction.prompt.txt
│   ├── ontology_generation.prompt.txt
│   └── explanation_generation.prompt.txt
├── data/                            # Input documents
├── outputs/                         # Extraction results
└── planning/
    └── PRD.md                       # Product Requirements Document
```

## 📖 Usage Examples

### Basic Extraction

```python
from backend.orchestrator import run_multi_pass_pipeline

# Process all documents in data/ directory
run_multi_pass_pipeline()

# Process specific file
run_multi_pass_pipeline("path/to/document.pdf")
```

### Quality Assurance

```python
from backend.quality_assurance import QualityAssurance

qa = QualityAssurance(min_confidence=0.7, enable_strict_mode=True)

# Assess entities
entities = [{"name": "Mitochondria", "category": "Organelle", "aliases": []}]
filtered_entities, metrics = qa.filter_low_quality(entities, 'entity')

# Generate quality report
report = qa.generate_quality_report(entity_metrics, rel_metrics, rule_metrics)
print(f"Overall Quality: {report['overall_quality_score']:.3f}")
```

### Neo4j Integration

```python
from backend.neo4j_integration import Neo4jConnector, Neo4jConfig

# Configure connection
config = Neo4jConfig(
    uri="bolt://localhost:7687",
    username="neo4j",
    password="password"
)

# Import knowledge graph
with Neo4jConnector(config) as connector:
    stats = connector.import_knowledge_graph(
        entities=entities,
        relationships=relationships,
        rules=rules,
        document_name="my_document.pdf"
    )
    print(f"Imported: {stats}")

    # Query knowledge
    results = connector.query_knowledge(category="Concept", limit=10)
```

## 🎯 Output Formats

### Entities
```json
{
  "name": "Mitochondria",
  "aliases": ["Powerhouse of the cell"],
  "category": "Organelle"
}
```

### Relationships
```json
{
  "subject": "Neuron",
  "predicate": "uses",
  "object": "Neurotransmitter",
  "justification": "Neurons use neurotransmitters to communicate."
}
```

### Rules
```json
{
  "id": 1,
  "if": "Student masters prerequisites",
  "then": "Student can advance to next topic",
  "confidence": 0.95
}
```

### Ontology
RDF/Turtle format (`.ttl` files) compatible with OWL reasoners.

## 🧪 Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=backend --cov=llm
```

## 📊 Performance

- **Processing Speed**: <30 seconds per 10-page document
- **Batch Throughput**: >100 documents/hour (with parallelization)
- **Quality Metrics**: >85% precision for entities, >75% for relationships
- **Cost**: <$0.50 per document (with GPT-4)

## 🗺️ Roadmap

See [PRD.md](planning/PRD.md) for the complete product roadmap.

### Phase 1 ✅ (Completed)
- [x] Multi-LLM Provider Support
- [x] Neo4j Integration
- [x] Quality Assurance Layer

### Phase 2 (Q1-Q2 2026)
- [ ] Prompt Engineering Framework
- [ ] Incremental Processing
- [ ] Hybrid Extraction (LLM + traditional NLP)
- [ ] Interactive Refinement UI
- [ ] Semantic Search

### Phase 3 (Q3-Q4 2026)
- [ ] REST API
- [ ] Scalability (Celery, Ray)
- [ ] Advanced Visualizations
- [ ] Collaboration Features

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines.

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [LiteLLM](https://github.com/BerriAI/litellm) for multi-provider LLM support
- Visualization powered by [Streamlit](https://streamlit.io/) and [PyVis](https://pyvis.readthedocs.io/)
- Graph database integration with [Neo4j](https://neo4j.com/)

## 📧 Support

For issues and questions:
- GitHub Issues: [https://github.com/yourusername/neuit/issues](https://github.com/yourusername/neuit/issues)
- Documentation: See [planning/PRD.md](planning/PRD.md)

---

**Made with ❤️ by the NEUIToolkit Team**
