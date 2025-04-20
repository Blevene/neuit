# Streamlit App for Corpus Ingestion and Schema Induction

import streamlit as st
import pandas as pd
import json
import os
from io import BytesIO
from typing import List, Dict

# Optional imports for .docx and PDF parsing
try:
    import docx  # python-docx
except ImportError:
    docx = None

try:
    import PyPDF2  # PyPDF2 for PDF extraction
except ImportError:
    PyPDF2 = None

from schema_induction_tooling import (
    generate_ontology,
    suggest_labels,
    induce_rules,
    suggest_labels_from_corpus,
    induce_rules_from_corpus,
)

st.set_page_config(page_title="Neuro-Symbolic Schema Induction", layout="wide")
st.title("Neuro-Symbolic Schema Induction Interface")

# Initialize session state variables to persist outputs across reruns
if "ontology_output" not in st.session_state:
    st.session_state["ontology_output"] = ""
if "label_output" not in st.session_state:
    st.session_state["label_output"] = ""
if "rules_output" not in st.session_state:
    st.session_state["rules_output"] = ""

# --- Sidebar Controls ---
st.sidebar.header("Step 1: Upload Corpus")
corpus_file = st.sidebar.file_uploader(
    "Upload corpus file",
    type=["txt", "csv", "jsonl", "md", "docx", "pdf"],
)

sample_data = ""
if corpus_file is not None:
    file_type = corpus_file.name.split(".")[-1]
    if file_type == "txt":
        sample_data = corpus_file.read().decode("utf-8")
    elif file_type == "csv":
        df = pd.read_csv(corpus_file)
        sample_data = "\n".join(df.astype(str).apply(" ".join, axis=1))
    elif file_type == "jsonl":
        lines = corpus_file.readlines()
        sample_data = "\n".join([line.decode("utf-8") for line in lines])
    elif file_type == "md":
        sample_data = corpus_file.read().decode("utf-8")
    elif file_type == "docx":
        if docx is None:
            st.error("python-docx not installed. Run `pip install python-docx`.")
        else:
            try:
                document = docx.Document(BytesIO(corpus_file.getvalue()))
                sample_data = "\n".join([para.text for para in document.paragraphs])
            except Exception as e:
                st.error(f"Error reading DOCX: {e}")
    elif file_type == "pdf":
        if PyPDF2 is None:
            st.error("PyPDF2 not installed. Run `pip install PyPDF2`.")
        else:
            try:
                reader = PyPDF2.PdfReader(BytesIO(corpus_file.getvalue()))
                pages_text = []
                for page in reader.pages:
                    try:
                        pages_text.append(page.extract_text() or "")
                    except Exception:
                        continue
                sample_data = "\n".join(pages_text)
            except Exception as e:
                st.error(f"Error reading PDF: {e}")

if sample_data:
    st.subheader("Corpus Preview")
    st.text_area("Extracted Text", sample_data[:5000], height=250)

# --- Section: Ontology Generation ---
if st.button("Generate Ontology", key="btn_gen_ontology") and sample_data:
    with st.spinner("Generating ontology from corpus..."):
        st.session_state["ontology_output"] = generate_ontology(sample_data)

# Display persisted ontology
if st.session_state["ontology_output"]:
    st.subheader("Ontology Output")
    st.code(st.session_state["ontology_output"], language="text")

# --- Section: Label Suggestion ---
st.subheader("Label Suggestion")

use_corpus_labels = st.checkbox("Use corpus for label suggestion", value=True)

if use_corpus_labels:
    if st.button("Suggest Labels from Corpus", key="btn_label_corpus") and sample_data:
        with st.spinner("Generating label suggestions from corpus..."):
            st.session_state["label_output"] = suggest_labels_from_corpus(sample_data)
else:
    concepts_input = st.text_area("Enter comma-separated concepts", "", help="E.g., Fractions, Decimals, Ratio")
    context_input = st.text_area("Enter JSON context per concept", """{
  "Fractions": "Used in early math curriculum.",
  "Decimals": "Follows introduction to fractions.",
  "Ratio": "Depends on understanding of fractions."
}""")
    if st.button("Suggest Labels", key="btn_label_manual"):
        try:
            concepts = [c.strip() for c in concepts_input.split(",") if c.strip()]
            context = json.loads(context_input)
            with st.spinner("Generating label suggestions..."):
                st.session_state["label_output"] = suggest_labels(concepts, context)
        except Exception as e:
            st.error(f"Error parsing inputs: {e}")

# Display persisted label suggestions
if st.session_state["label_output"]:
    st.subheader("Suggested Labels")
    st.code(st.session_state["label_output"], language="text")

# --- Section: Rule Induction ---
st.subheader("Rule Induction")

if st.button("Induce Rules from Corpus", key="btn_rules") and sample_data:
    with st.spinner("Generating symbolic rules from corpus..."):
        st.session_state["rules_output"] = induce_rules_from_corpus(sample_data)

# Display persisted rule induction output
if st.session_state["rules_output"]:
    st.subheader("Generated Rules")
    st.code(st.session_state["rules_output"], language="text")

# Display API key status
st.sidebar.subheader("API Configuration")
api_status = "✅ Configured" if os.getenv("OPENAI_API_KEY") else "❌ Not configured"
st.sidebar.info(f"OpenAI API Key: {api_status}")
if not os.getenv("OPENAI_API_KEY"):
    st.sidebar.warning("Please set your OpenAI API key in the .env file.")
    st.sidebar.code("OPENAI_API_KEY=your_key_here", language="text")
