# Streamlit App for Corpus Ingestion and Schema Induction

import streamlit as st
import pandas as pd
from typing import List, Dict
from schema_induction_tooling import generate_ontology, suggest_labels, induce_rules

st.set_page_config(page_title="Neuro-Symbolic Schema Induction", layout="wide")
st.title("Neuro-Symbolic Schema Induction Interface")

# --- Sidebar Controls ---
st.sidebar.header("Step 1: Upload Corpus")
corpus_file = st.sidebar.file_uploader("Upload text, CSV, JSONL, or Markdown file", type=["txt", "csv", "jsonl", "md"])

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

if sample_data:
    st.subheader("Corpus Preview")
    st.text_area("Extracted Text", sample_data[:5000], height=250)

# --- Section: Ontology Generation ---
if st.button("Generate Ontology") and sample_data:
    with st.spinner("Generating ontology from corpus..."):
        ontology = generate_ontology(sample_data)
        st.subheader("Ontology Output")
        st.code(ontology, language="text")

# --- Section: Label Suggestion ---
st.subheader("Label Suggestion")
concepts_input = st.text_area("Enter comma-separated concepts", "", help="E.g., Fractions, Decimals, Ratio")
context_input = st.text_area("Enter JSON context per concept", """{
  "Fractions": "Used in early math curriculum.",
  "Decimals": "Follows introduction to fractions.",
  "Ratio": "Depends on understanding of fractions."
}""")

if st.button("Suggest Labels"):
    try:
        concepts = [c.strip() for c in concepts_input.split(",") if c.strip()]
        context = eval(context_input)  # WARNING: Use safer JSON parsing in production
        with st.spinner("Generating label suggestions..."):
            labels = suggest_labels(concepts, context)
            st.subheader("Suggested Labels")
            st.code(labels, language="text")
    except Exception as e:
        st.error(f"Error parsing inputs: {e}")

# --- Section: Rule Induction ---
st.subheader("Rule Induction")
examples_input = st.text_area("Provide examples of concept relationships or mastery patterns", """- Concept A is a prerequisite of Concept B.
- Students who fail Concept A tend to also struggle with Concept B.
- Reviewing A improves B performance.""")

if st.button("Induce Rules"):
    with st.spinner("Generating symbolic rules..."):
        rules = induce_rules(examples_input)
        st.subheader("Generated Rules")
        st.code(rules, language="text")
