# Schema Induction Tooling

Tools for schema induction via LLMs, including:
- Ontology Generation
- Label Suggestion
- Rule Induction

## Setup

1. Create a virtual environment:
```bash
python -m venv dev
```

2. Activate the virtual environment:
   - Windows (PowerShell): `.\dev\Scripts\Activate.ps1`
   - Windows (CMD): `.\dev\Scripts\activate.bat`
   - Linux/Mac: `source dev/bin/activate`

3. Install dependencies:
```bash
pip install openai python-dotenv streamlit pandas
```

4. Set up your API key:
   - Copy `.env.example` to `.env`
   - Replace `your_openai_api_key_here` with your actual OpenAI API key

## Running the Application

Run the Streamlit application with:

```bash
python run_app.py
```

This will:
1. Check for a `.env` file and create one if it doesn't exist
2. Launch the Streamlit interface at http://localhost:8501
3. Display the UI for schema induction tasks

## Using the Components Separately

The core functions can also be used independently:

```python
from prototype.schema_induction_tooling import generate_ontology, suggest_labels, induce_rules

# Generate ontology from text corpus
ontology = generate_ontology(corpus_text)

# Get label suggestions for concepts
labels = suggest_labels(concept_list, context_dict)

# Generate rules from patterns
rules = induce_rules(pattern_examples)
```

See examples in `prototype/schema_induction_tooling.py`.
