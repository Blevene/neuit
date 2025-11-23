# Product Requirements Document (PRD)
## NEUIToolkit - Neurosymbolic Knowledge Extraction Platform

**Version:** 1.0
**Date:** November 23, 2025
**Status:** Active Development

---

## Executive Summary

NEUIToolkit is an AI-powered knowledge extraction and schema induction platform that transforms unstructured documents into structured, queryable knowledge graphs. By combining Large Language Models (LLMs) with symbolic reasoning techniques, the system extracts entities, relationships, rules, and ontologies from diverse document types, enabling knowledge-based applications in education, research, and adaptive learning systems.

---

## 1. Product Vision

### 1.1 Vision Statement
To democratize knowledge extraction by providing an accessible, powerful toolkit that transforms any text corpus into structured, machine-readable knowledge that can power intelligent applications, educational tools, and reasoning systems.

### 1.2 Core Value Proposition
- **Automated Schema Induction**: Eliminates manual ontology engineering by automatically generating domain-specific schemas from text
- **Multi-Format Support**: Works with PDFs, DOCX, plain text, markdown, and JSON files
- **Neurosymbolic Approach**: Combines neural language understanding with symbolic knowledge representation
- **Visual Exploration**: Interactive dashboards for exploring and validating extracted knowledge
- **Graph-Ready Output**: Neo4j-compatible formats for immediate integration with graph databases

---

## 2. Target Users

### 2.1 Primary Users
1. **Educational Technologists**
   - Need: Automated content structuring for adaptive learning systems
   - Use Case: Transform textbooks and course materials into knowledge graphs

2. **Research Scientists**
   - Need: Extract domain knowledge from academic papers and documents
   - Use Case: Build domain-specific ontologies for research organization

3. **Knowledge Engineers**
   - Need: Rapid prototyping of knowledge bases
   - Use Case: Quick validation of extraction approaches before production deployment

### 2.2 Secondary Users
1. **Data Scientists**: Exploring knowledge graph approaches to ML problems
2. **Software Developers**: Building knowledge-enhanced applications
3. **Educators**: Creating structured educational resources

---

## 3. Current State Assessment

### 3.1 What Works Well
✅ **Multi-pass extraction pipeline** with 5 distinct passes:
- Entity extraction (concepts, aliases, categories)
- Relationship extraction (subject-predicate-object triples)
- Rule induction (if-then logical rules)
- Ontology generation (OWL/RDF format)
- Justification generation (explanations for extracted knowledge)

✅ **File format support**: PDF, DOCX, TXT, MD, JSON via MIME-type detection

✅ **Visualization dashboard**: Streamlit-based UI with:
- Interactive knowledge graph visualization (PyVis)
- Entity category breakdowns
- Relationship network views
- Ontology visualization
- Metrics and summaries

✅ **Parallel processing**: ThreadPoolExecutor for batch document processing

✅ **Robust error handling**: Graceful degradation with comprehensive logging

### 3.2 Current Limitations
⚠️ **LLM dependency**: Requires OpenAI API (cost and latency considerations)
⚠️ **No persistent storage**: Outputs to files only, no database integration yet
⚠️ **Limited validation**: No built-in quality assurance for extracted knowledge
⚠️ **Single LLM provider**: Locked to OpenAI, no provider flexibility
⚠️ **No incremental updates**: Must reprocess entire documents
⚠️ **Basic prompts**: Room for domain-specific prompt optimization

---

## 4. Core Features

### 4.1 Knowledge Extraction Pipeline

#### 4.1.1 Entity Extraction
**Status:** ✅ Implemented
**Description:** Identifies key concepts, entities, and their semantic categories from text.

**Outputs:**
```json
{
  "name": "Mitochondria",
  "aliases": ["Powerhouse of the cell"],
  "category": "Structure"
}
```

**Performance Target:** >85% precision on domain-specific texts

#### 4.1.2 Relationship Extraction
**Status:** ✅ Implemented
**Description:** Extracts semantic triples (subject-predicate-object) with justifications.

**Outputs:**
```json
{
  "subject": "Neuron",
  "predicate": "uses",
  "object": "Neurotransmitter",
  "justification": "Neurons use neurotransmitters to communicate across synapses."
}
```

**Performance Target:** >75% recall on explicit relationships

#### 4.1.3 Rule Induction
**Status:** ✅ Implemented
**Description:** Identifies logical if-then rules and prerequisites from text.

**Use Case:** Educational sequencing, prerequisite mapping

#### 4.1.4 Ontology Generation
**Status:** ✅ Implemented
**Description:** Generates OWL/RDF ontologies in Turtle format.

**Output Format:** RDF/Turtle (.ttl)

#### 4.1.5 Explanation Generation
**Status:** ✅ Implemented
**Description:** Provides justifications and explanations for induced rules.

**Purpose:** Transparency, validation, educational feedback

### 4.2 Visualization & Exploration

#### 4.2.1 Document Dashboard
**Status:** ✅ Implemented
**Components:**
- Document selector
- Summary metrics (entity/relationship/rule counts)
- Tabbed interface (6 tabs)

#### 4.2.2 Interactive Knowledge Graphs
**Status:** ✅ Implemented
**Features:**
- Node coloring by entity category
- Edge labels for predicates
- Interactive zoom/pan
- Click for details

#### 4.2.3 Ontology Visualization
**Status:** ✅ Implemented
**Features:**
- Turtle format viewer
- Graph-based ontology rendering
- Fallback parsing for malformed RDF

### 4.3 File Processing

#### 4.3.1 Multi-Format Ingestion
**Status:** ✅ Implemented
**Supported Formats:**
- PDF (via PyPDF2)
- DOCX (via python-docx)
- TXT, MD (plain text)
- JSON (structured data)

**MIME Detection:** Via python-magic library

#### 4.3.2 Batch Processing
**Status:** ✅ Implemented
**Features:**
- Parallel processing (configurable workers)
- Progress tracking (tqdm)
- Per-document error isolation

---

## 5. Technical Architecture

### 5.1 System Components

```
neuit/
├── backend/
│   └── orchestrator.py          # Multi-pass extraction pipeline
├── frontend/
│   └── app.py                    # Streamlit visualization dashboard
├── llm/
│   └── llm_utils.py              # OpenAI API wrapper
├── prompts/
│   ├── entity_extraction.prompt.txt
│   ├── relationship_extraction.prompt.txt
│   ├── rule_induction.prompt.txt
│   ├── ontology_generation.prompt.txt
│   └── explanation_generation.prompt.txt
├── outputs/                      # Extraction results (JSON, TTL)
├── data/                         # Input documents
└── prototype/                    # Legacy code (being phased out)
```

### 5.2 Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| LLM Provider | OpenAI GPT | Natural language understanding |
| Backend | Python 3.x | Core processing logic |
| File Parsing | PyPDF2, python-docx | Document reading |
| Frontend | Streamlit | Interactive dashboards |
| Visualization | PyVis, Plotly, NetworkX | Graph and chart rendering |
| Ontology | RDFLib | RDF/OWL processing |
| Concurrency | ThreadPoolExecutor | Parallel processing |
| Logging | Python logging | Error tracking |

### 5.3 Data Flow

```
Document Input → MIME Detection → Format-Specific Parser → Text Corpus
                                                                  ↓
                                          [Multi-Pass LLM Extraction]
                                                                  ↓
                        ┌─────────────────┬────────────────┬─────┴────┬─────────────┐
                        ↓                 ↓                ↓          ↓             ↓
                   Entities        Relationships       Rules    Ontology    Justifications
                        ↓                 ↓                ↓          ↓             ↓
                   JSON Files      +      Graph Data      +     TTL Files
                        ↓                                                           ↓
                   Metadata Index ────────────────────────────────────────> Visualization Dashboard
```

### 5.4 Output Schema

#### Entities
```json
{
  "name": "string",
  "aliases": ["string"],
  "category": "string"
}
```

#### Relationships
```json
{
  "subject": "string",
  "predicate": "string",
  "object": "string",
  "justification": "string"
}
```

#### Rules
```json
{
  "id": "number",
  "if": "string",
  "then": "string",
  "confidence": "number"
}
```

#### Metadata
```json
{
  "filename": "string",
  "num_entities": "number",
  "num_relationships": "number",
  "num_rules": "number",
  "num_justifications": "number",
  "ontology_lines": "number",
  "source_path": "string"
}
```

---

## 6. Future Roadmap

### 6.1 Phase 1: Foundation Hardening (Q1 2026)

#### P0 - Critical
- [ ] **Multi-LLM Provider Support**
  - Abstract LLM interface
  - Support Claude, Gemini, local models (Ollama)
  - Cost optimization through provider routing

- [ ] **Neo4j Integration**
  - Direct graph database writes
  - Cypher query interface
  - Graph schema validation

- [ ] **Quality Assurance Layer**
  - Confidence scoring
  - Fact verification
  - Duplicate detection
  - Consistency checking

#### P1 - High Priority
- [ ] **Prompt Engineering Framework**
  - Domain-specific prompt templates
  - Few-shot learning support
  - Prompt versioning and A/B testing

- [ ] **Incremental Processing**
  - Document change detection
  - Differential updates
  - Version control for knowledge graphs

### 6.2 Phase 2: Advanced Capabilities (Q2 2026)

#### P1 - High Priority
- [ ] **Hybrid Extraction**
  - Combine LLM with traditional NLP (spaCy, NLTK)
  - Entity linking to external KBs (DBpedia, Wikidata)
  - Coreference resolution

- [ ] **Interactive Refinement**
  - Human-in-the-loop validation
  - Entity/relationship editing in UI
  - Feedback loop to improve prompts

- [ ] **Semantic Search**
  - Embedding-based search (FAISS, ChromaDB)
  - Natural language queries
  - Similar document finding

#### P2 - Medium Priority
- [ ] **Reasoning Engine**
  - Forward/backward chaining on rules
  - Explanation generation for inferences
  - Conflict resolution

- [ ] **Educational Features**
  - Prerequisite graph generation
  - Learning path optimization
  - Quiz generation from knowledge graphs

### 6.3 Phase 3: Enterprise Features (Q3-Q4 2026)

#### P1 - High Priority
- [ ] **REST API**
  - OpenAPI/Swagger specification
  - Authentication/authorization
  - Rate limiting
  - Webhook support

- [ ] **Scalability**
  - Distributed processing (Celery, Ray)
  - Cloud storage integration (S3, GCS)
  - Kubernetes deployment

#### P2 - Medium Priority
- [ ] **Advanced Visualizations**
  - 3D graph rendering
  - Temporal graph views
  - Diff visualization
  - Export to Gephi, Cytoscape

- [ ] **Collaboration Features**
  - Multi-user workspaces
  - Annotation sharing
  - Version control (git-like)

---

## 7. Success Metrics

### 7.1 Quality Metrics
- **Extraction Precision**: >85% for entities, >75% for relationships
- **Ontology Completeness**: >90% coverage of domain concepts
- **User Validation Rate**: <15% corrections needed on extracted knowledge

### 7.2 Performance Metrics
- **Processing Speed**: <30 seconds per 10-page document
- **Batch Throughput**: >100 documents/hour (with parallelization)
- **API Latency**: <2 seconds p95 for single extractions

### 7.3 Adoption Metrics
- **User Retention**: >60% monthly active users (for hosted service)
- **GitHub Stars**: >500 (community interest)
- **Integration Deployments**: >10 production systems using NEUIToolkit

### 7.4 Cost Metrics
- **LLM Cost**: <$0.50 per document processed
- **Error Rate**: <5% failed extractions
- **Support Tickets**: <10% of users require assistance

---

## 8. Non-Functional Requirements

### 8.1 Performance
- Support documents up to 50,000 words
- Handle batch processing of 1,000+ documents
- Memory footprint <2GB per worker process

### 8.2 Reliability
- 99% uptime for API services (future)
- Graceful degradation on LLM failures
- Automatic retry with exponential backoff

### 8.3 Security
- API key encryption at rest
- No storage of user documents (optional processing modes)
- Audit logging for all extraction operations

### 8.4 Usability
- Zero-configuration local setup
- CLI interface for power users
- Visual debugging of extraction results

### 8.5 Maintainability
- 80%+ test coverage
- Comprehensive API documentation
- Modular architecture for easy extension

---

## 9. Dependencies & Integrations

### 9.1 Current Dependencies
```
openai>=1.0.0
python-dotenv
streamlit
pandas
PyPDF2
python-docx
python-magic
networkx
matplotlib
plotly
pyvis
rdflib
tqdm
```

### 9.2 Planned Integrations
- **Neo4j**: Primary graph database
- **ChromaDB/FAISS**: Vector search
- **spaCy**: NLP augmentation
- **Hugging Face**: Model hosting
- **LangChain**: LLM orchestration (optional)

---

## 10. Open Questions & Risks

### 10.1 Open Questions
1. **Domain Specialization**: How to optimize prompts for specific domains (medical, legal, scientific)?
2. **Quality Thresholds**: What confidence scores warrant automatic acceptance vs. human review?
3. **Graph Schema**: Should we enforce a strict graph schema or allow flexible structures?
4. **Hosting Model**: SaaS vs. self-hosted vs. hybrid?

### 10.2 Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| LLM API changes breaking extraction | High | Medium | Multi-provider support, API version pinning |
| Poor extraction quality on specialized domains | High | High | Domain-specific prompt tuning, hybrid approaches |
| High LLM costs at scale | Medium | High | Caching, smaller models for simple tasks, cost monitoring |
| Neo4j integration complexity | Medium | Medium | Start with JSONL export, incremental integration |
| User retention challenges | Medium | Medium | Focus on UX, educational content, community building |

---

## 11. Success Criteria

### 11.1 MVP Success (Current)
- ✅ Process common document formats (PDF, DOCX, TXT)
- ✅ Extract entities, relationships, rules, ontologies
- ✅ Visualize results in interactive dashboard
- ✅ Support batch processing

### 11.2 v1.0 Success (6 months)
- [ ] Multi-LLM provider support
- [ ] Neo4j integration working
- [ ] Quality assurance layer operational
- [ ] 10+ active production deployments
- [ ] Documentation complete

### 11.3 v2.0 Success (12 months)
- [ ] REST API in production
- [ ] Semantic search capabilities
- [ ] Interactive refinement UI
- [ ] 100+ GitHub stars
- [ ] Published case studies/papers

---

## 12. Conclusion

NEUIToolkit is positioned to become a leading open-source solution for automated knowledge extraction and schema induction. By focusing on quality, flexibility, and user experience, we can serve educational, research, and enterprise use cases while building a vibrant community around neurosymbolic AI approaches.

The foundation is solid, with working extraction pipelines and visualization tools. The next phase focuses on hardening quality, expanding provider options, and integrating with production-grade graph databases to unlock real-world applications.

---

**Document Owner:** Development Team
**Last Updated:** November 23, 2025
**Next Review:** December 15, 2025
