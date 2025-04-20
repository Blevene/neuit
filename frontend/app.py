import streamlit as st
import json
import os
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px
from pyvis.network import Network
import rdflib
import tempfile
import base64

# Set page configuration
st.set_page_config(
    page_title="NEUIToolkit Visualizer",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Path to outputs directory
OUTPUTS_DIR = Path("../outputs")

def load_metadata_index():
    """Load the metadata index file containing information about all processed documents."""
    metadata_path = OUTPUTS_DIR / "metadata_index.json"
    if metadata_path.exists():
        with open(metadata_path, "r") as f:
            return json.load(f)
    return []

def load_document_data(doc_name):
    """Load all data related to a specific document."""
    base_name = doc_name.split('.')[0]
    data = {}
    
    # Load entities
    entity_path = OUTPUTS_DIR / f"{base_name}_entities.json"
    if entity_path.exists():
        with open(entity_path, "r") as f:
            data["entities"] = json.load(f)
    
    # Load relationships
    rel_path = OUTPUTS_DIR / f"{base_name}_relationships.json"
    if rel_path.exists():
        with open(rel_path, "r") as f:
            data["relationships"] = json.load(f)
    
    # Load rules
    rules_path = OUTPUTS_DIR / f"{base_name}_rules.json"
    if rules_path.exists():
        with open(rules_path, "r") as f:
            data["rules"] = json.load(f)
    
    # Load justifications
    just_path = OUTPUTS_DIR / f"{base_name}_justifications.json"
    if just_path.exists():
        with open(just_path, "r") as f:
            data["justifications"] = json.load(f)
    
    # Load ontology
    onto_path = OUTPUTS_DIR / f"{base_name}_ontology.ttl"
    if onto_path.exists():
        with open(onto_path, "r") as f:
            data["ontology"] = f.read()
    
    # Load metadata
    meta_path = OUTPUTS_DIR / f"{base_name}_metadata.json"
    if meta_path.exists():
        with open(meta_path, "r") as f:
            data["metadata"] = json.load(f)
    
    return data

def display_entities(entities):
    """Display entities as a table and pie chart."""
    if not entities:
        st.warning("No entities found for this document.")
        return
    
    # Convert to DataFrame for easier manipulation
    df = pd.DataFrame(entities)
    
    # Show table of entities
    st.subheader("Entities Table")
    st.dataframe(df, use_container_width=True)
    
    # Create pie chart of entity categories
    category_counts = df['category'].value_counts().reset_index()
    category_counts.columns = ['Category', 'Count']
    
    fig = px.pie(
        category_counts, 
        values='Count', 
        names='Category', 
        title='Entity Categories',
        color_discrete_sequence=px.colors.qualitative.Plotly
    )
    st.plotly_chart(fig, use_container_width=True)

def display_relationships(relationships, entities=None):
    """Display relationships as a table and network graph."""
    if not relationships:
        st.warning("No relationships found for this document.")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(relationships)
    
    # Show table of relationships
    st.subheader("Relationships Table")
    st.dataframe(df, use_container_width=True)
    
    # Create network graph
    st.subheader("Knowledge Graph Visualization")
    
    # Create network
    G = nx.DiGraph()
    
    # Add nodes and edges
    for rel in relationships:
        subject = rel["subject"]
        obj = rel["object"]
        predicate = rel["predicate"]
        
        # Add nodes if they don't exist
        if subject not in G:
            G.add_node(subject)
        if obj not in G:
            G.add_node(obj)
        
        # Add edge with predicate as label
        G.add_edge(subject, obj, label=predicate)
    
    # Create pyvis network for interactive visualization
    net = Network(height="600px", width="100%", directed=True, notebook=False)
    
    # If we have entity information, use it for node colors
    entity_categories = {}
    if entities:
        for entity in entities:
            entity_categories[entity["name"]] = entity["category"]
    
    # Color mapping for categories
    category_colors = {
        "Process": "#FF5733",
        "Organism": "#33FF57",
        "Structure": "#3357FF",
        "Substance": "#F3FF33",
        "Property": "#FF33F3",
        "Concept": "#33FFF3"
    }
    
    # Add nodes to pyvis network
    for node in G.nodes():
        category = entity_categories.get(node, "Unknown")
        color = category_colors.get(category, "#AAAAAA")
        net.add_node(node, label=node, title=f"Category: {category}", color=color)
    
    # Add edges to pyvis network
    for edge in G.edges(data=True):
        source, target, data = edge
        net.add_edge(source, target, title=data.get("label", ""))
    
    # Fix for pyvis creating 'lib' directory in current folder
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)  # Change to temp directory before saving graph
        tmpfile_path = os.path.join(tmpdir, "graph.html")
        net.save_graph(tmpfile_path)
        with open(tmpfile_path, 'r', encoding='utf-8') as f:
            html = f.read()
        
        # Change back to original directory
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    st.components.v1.html(html, height=600)

def display_rules(rules):
    """Display rules as a table."""
    if not rules:
        st.warning("No rules found for this document.")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(rules)
    
    # Show table of rules
    st.subheader("Extracted Rules")
    st.dataframe(df, use_container_width=True)

def display_justifications(justifications):
    """Display justifications."""
    if not justifications:
        st.warning("No justifications found for this document.")
        return
    
    st.subheader("Justifications")
    
    for i, just in enumerate(justifications):
        with st.expander(f"Justification {i+1}"):
            for key, value in just.items():
                st.markdown(f"**{key.capitalize()}:** {value}")

def display_ontology(ontology_text):
    """Display ontology as raw text and visualization if possible."""
    if not ontology_text:
        st.warning("No ontology found for this document.")
        return
    
    st.subheader("Ontology (Turtle Format)")
    with st.expander("View Raw Ontology"):
        st.code(ontology_text, language="turtle")
    
    # Try to parse and visualize the ontology
    try:
        # Add standard RDF prefixes if they're missing
        standard_prefixes = """
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
"""
        # Check if any of these prefixes are missing and prepend them
        if "@prefix rdf:" not in ontology_text:
            ontology_text = standard_prefixes + ontology_text
        
        g = rdflib.Graph()
        g.parse(data=ontology_text, format="turtle")
        
        # Convert to a networkx graph for visualization
        G = nx.DiGraph()
        
        for s, p, o in g:
            s_str = str(s)
            p_str = str(p).split("/")[-1].split("#")[-1]  # Get the last part of the URI
            o_str = str(o)
            
            G.add_node(s_str)
            G.add_node(o_str)
            G.add_edge(s_str, o_str, label=p_str)
        
        # Create pyvis network for interactive visualization
        net = Network(height="600px", width="100%", directed=True, notebook=False)
        
        # Add nodes to pyvis network
        for node in G.nodes():
            net.add_node(node, label=node.split("/")[-1].split("#")[-1])
        
        # Add edges to pyvis network
        for edge in G.edges(data=True):
            source, target, data = edge
            net.add_edge(source, target, title=data.get("label", ""))
        
        # Fix for pyvis creating 'lib' directory in current folder
        with tempfile.TemporaryDirectory() as tmpdir:
            os.chdir(tmpdir)  # Change to temp directory before saving graph
            tmpfile_path = os.path.join(tmpdir, "graph.html")
            net.save_graph(tmpfile_path)
            with open(tmpfile_path, 'r', encoding='utf-8') as f:
                html = f.read()
            
            # Change back to original directory
            os.chdir(os.path.dirname(os.path.abspath(__file__)))
        
        st.subheader("Ontology Visualization")
        st.components.v1.html(html, height=600)
    except Exception as e:
        st.error(f"Error visualizing ontology: {str(e)}")
        st.info("Attempting to fix and parse the ontology manually...")
        
        try:
            # More aggressive fix attempt - create a simplified visualization
            # Extract triples manually using regex
            import re
            
            # Create manual graph using subject-predicate-object patterns
            G = nx.DiGraph()
            
            # Simple pattern matching for triples in the form "subject predicate object ."
            triple_pattern = r'([A-Za-z0-9:_#]+)\s+([A-Za-z0-9:_#]+)\s+([A-Za-z0-9:_#"\']+)\s*\.'
            matches = re.findall(triple_pattern, ontology_text)
            
            for match in matches:
                subject, predicate, obj = match
                G.add_node(subject)
                G.add_node(obj)
                G.add_edge(subject, obj, label=predicate)
            
            if len(G.nodes()) > 0:
                # Create pyvis network for interactive visualization
                net = Network(height="600px", width="100%", directed=True, notebook=False)
                
                # Add nodes to pyvis network
                for node in G.nodes():
                    net.add_node(node, label=node)
                
                # Add edges to pyvis network
                for edge in G.edges(data=True):
                    source, target, data = edge
                    net.add_edge(source, target, title=data.get("label", ""))
                
                # Fix for pyvis creating 'lib' directory in current folder
                with tempfile.TemporaryDirectory() as tmpdir:
                    os.chdir(tmpdir)  # Change to temp directory before saving graph
                    tmpfile_path = os.path.join(tmpdir, "graph.html")
                    net.save_graph(tmpfile_path)
                    with open(tmpfile_path, 'r', encoding='utf-8') as f:
                        html = f.read()
                    
                    # Change back to original directory
                    os.chdir(os.path.dirname(os.path.abspath(__file__)))
                
                st.subheader("Ontology Visualization (Manual Parsing)")
                st.components.v1.html(html, height=600)
            else:
                st.warning("Could not extract any valid triples from the ontology.")
        except Exception as e2:
            st.error(f"Failed to manually parse the ontology: {str(e2)}")

def display_summary(metadata):
    """Display summary of document extraction results."""
    if not metadata:
        st.warning("No metadata found for this document.")
        return
    
    st.subheader("Document Summary")
    
    # Display metrics in a row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Entities", metadata.get("num_entities", 0))
    
    with col2:
        st.metric("Relationships", metadata.get("num_relationships", 0))
    
    with col3:
        st.metric("Rules", metadata.get("num_rules", 0))
    
    with col4:
        st.metric("Justifications", metadata.get("num_justifications", 0))
    
    # Display source file
    st.info(f"Source: {metadata.get('source_path', 'Unknown')}")

def main():
    st.title("NEUIToolkit Knowledge Extraction Visualizer")
    
    # Sidebar for document selection
    st.sidebar.title("Navigation")
    
    # Load metadata index
    metadata = load_metadata_index()
    
    if not metadata:
        st.error("No processed documents found. Please run the extraction pipeline first.")
        return
    
    # Document selection
    selected_doc = st.sidebar.selectbox(
        "Select Document",
        [doc["filename"] for doc in metadata],
        format_func=lambda x: x
    )
    
    # Load document data
    data = load_document_data(selected_doc)
    
    if not data:
        st.error(f"No data found for document: {selected_doc}")
        return
    
    # Navigation tabs
    tab_names = ["Summary", "Entities", "Relationships", "Rules", "Justifications", "Ontology"]
    tabs = st.tabs(tab_names)
    
    # Summary tab
    with tabs[0]:
        display_summary(data.get("metadata", {}))
    
    # Entities tab
    with tabs[1]:
        display_entities(data.get("entities", []))
    
    # Relationships tab
    with tabs[2]:
        display_relationships(data.get("relationships", []), data.get("entities", []))
    
    # Rules tab
    with tabs[3]:
        display_rules(data.get("rules", []))
    
    # Justifications tab
    with tabs[4]:
        display_justifications(data.get("justifications", []))
    
    # Ontology tab
    with tabs[5]:
        display_ontology(data.get("ontology", ""))

if __name__ == "__main__":
    main() 