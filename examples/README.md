# NEUIToolkit Examples

This directory contains example notebooks and scripts demonstrating how to use NEUIToolkit for various knowledge extraction tasks.

## 📚 Jupyter Notebooks

### 01_getting_started.ipynb
**Difficulty**: Beginner
**Duration**: 15-20 minutes

Learn the basics of NEUIToolkit:
- Extract entities, relationships, and rules from text
- Use the quality assurance layer
- Visualize knowledge graphs
- Export results to JSON

**Prerequisites**:
- Python 3.8+
- At least one LLM API key configured
- Basic understanding of knowledge graphs

**Run**:
```bash
jupyter notebook examples/01_getting_started.ipynb
```

### 02_neo4j_integration.ipynb *(Coming Soon)*
**Difficulty**: Intermediate
**Duration**: 20-30 minutes

Advanced workflow with Neo4j:
- Set up Neo4j database
- Export knowledge graphs to Neo4j
- Query knowledge using Cypher
- Visualize graph database results

**Prerequisites**:
- Neo4j database running (local or cloud)
- Neo4j credentials configured

### 03_batch_processing.ipynb *(Coming Soon)*
**Difficulty**: Intermediate
**Duration**: 25-35 minutes

Process multiple documents efficiently:
- Batch document processing
- Parallel extraction with workers
- Error handling and recovery
- Performance optimization tips

**Prerequisites**:
- Multiple sample documents
- Understanding of concurrent processing

### 04_custom_prompts.ipynb *(Coming Soon)*
**Difficulty**: Advanced
**Duration**: 30-40 minutes

Customize extraction for your domain:
- Modify prompt templates
- Domain-specific entity categories
- Few-shot learning examples
- Prompt engineering best practices

**Prerequisites**:
- Understanding of prompt engineering
- Domain-specific knowledge

### 05_multi_provider.ipynb *(Coming Soon)*
**Difficulty**: Intermediate
**Duration**: 15-25 minutes

Work with multiple LLM providers:
- Configure multiple providers
- Implement fallback strategies
- Compare provider results
- Cost optimization techniques

**Prerequisites**:
- Multiple LLM API keys (OpenAI, Claude, Gemini)

## 🐍 Python Scripts

### extract_single_document.py *(Coming Soon)*
Simple script to extract knowledge from a single document.

```bash
python examples/extract_single_document.py path/to/document.pdf
```

### batch_extract.py *(Coming Soon)*
Batch process multiple documents with progress tracking.

```bash
python examples/batch_extract.py --input data/ --output results/
```

### export_to_neo4j.py *(Coming Soon)*
Export existing JSON results to Neo4j database.

```bash
python examples/export_to_neo4j.py --results outputs/ --neo4j bolt://localhost:7687
```

## 📊 Sample Data

### sample_documents/ *(Coming Soon)*
Sample documents for testing:
- `biology_textbook_chapter.pdf` - Educational content
- `research_paper.pdf` - Scientific paper
- `technical_documentation.md` - Technical docs

### sample_outputs/ *(Coming Soon)*
Example extraction results:
- Entity lists
- Relationship graphs
- Rule sets
- Quality reports

## 🚀 Quick Start

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install jupyter  # For notebooks
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

3. **Launch Jupyter**:
   ```bash
   jupyter notebook examples/
   ```

4. **Start with notebook 01**:
   Open `01_getting_started.ipynb` and follow along!

## 📖 Learning Path

### Beginner Path
1. Start with `01_getting_started.ipynb`
2. Run `extract_single_document.py` on your own document
3. Explore the Streamlit dashboard: `streamlit run frontend/app.py`

### Intermediate Path
1. Complete beginner path
2. Work through `02_neo4j_integration.ipynb`
3. Try `03_batch_processing.ipynb` with your document collection
4. Experiment with `05_multi_provider.ipynb`

### Advanced Path
1. Complete intermediate path
2. Study `04_custom_prompts.ipynb`
3. Modify prompt templates for your domain
4. Implement custom extraction passes
5. Contribute improvements to the project!

## 🎯 Use Case Examples

### Educational Technology
- Extract concepts from textbooks
- Build prerequisite knowledge graphs
- Generate quiz questions from content

### Research
- Extract entities from academic papers
- Build domain ontologies
- Organize literature reviews

### Enterprise
- Extract knowledge from documentation
- Build internal knowledge bases
- Automated metadata generation

## 💡 Tips

- **Start small**: Test with short documents first
- **Monitor costs**: Check LLM provider costs with `get_provider_stats()`
- **Use QA layer**: Always enable quality assurance for production
- **Experiment with thresholds**: Adjust confidence thresholds based on your needs
- **Cache results**: Save extraction results to avoid re-processing

## 🐛 Troubleshooting

### Common Issues

**ImportError: No module named 'backend'**
```bash
# Make sure you're in the neuit directory
cd /path/to/neuit
# Or add to Python path in notebook
import sys
sys.path.append('/path/to/neuit')
```

**LLM API errors**
```bash
# Check your API key is set
echo $OPENAI_API_KEY
# Or verify in .env file
```

**Neo4j connection failed**
```bash
# Check Neo4j is running
curl http://localhost:7474
# Verify credentials in .env
```

## 📧 Support

- **Questions**: [GitHub Discussions](https://github.com/Blevene/neuit/discussions)
- **Bug Reports**: [GitHub Issues](https://github.com/Blevene/neuit/issues)
- **Documentation**: [README.md](../README.md)

## 🤝 Contributing Examples

Have a useful example? Contributions welcome!

1. Create a new notebook or script
2. Add clear documentation and comments
3. Test with sample data
4. Submit a Pull Request

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

---

**Happy Learning!** 🎓
