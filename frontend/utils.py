import json
import pandas as pd
import networkx as nx
from pathlib import Path
import tempfile
import os
import rdflib
import base64
import plotly.express as px
from pyvis.network import Network
import streamlit as st

def get_all_output_files(output_dir):
    """
    Get a list of all output files in the specified directory.
    
    Args:
        output_dir (Path): Path to output directory
        
    Returns:
        dict: Dictionary of file types and their paths
    """
    files = {}
    
    for file_path in output_dir.glob("*"):
        if file_path.is_file():
            files[file_path.name] = file_path
    
    return files

def get_document_basenames(output_dir):
    """
    Get a list of all unique document base names in the output directory.
    
    Args:
        output_dir (Path): Path to output directory
        
    Returns:
        list: List of unique document base names
    """
    basenames = set()
    
    for file_path in output_dir.glob("*_entities.json"):
        basenames.add(file_path.name.replace("_entities.json", ""))
    
    return list(sorted(basenames))

def create_knowledge_graph(relationships, entities=None):
    """
    Create a knowledge graph from relationships data.
    
    Args:
        relationships (list): List of relationship dictionaries
        entities (list, optional): List of entity dictionaries for coloring
        
    Returns:
        str: HTML string of the network graph
    """
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
        
    return html

def create_ontology_graph(ontology_text):
    """
    Create a graph visualization from ontology text.
    
    Args:
        ontology_text (str): Ontology in Turtle format
        
    Returns:
        str: HTML string of the network graph or None if parsing fails
    """
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
            
        return html
    except Exception as e:
        st.error(f"Error visualizing ontology: {str(e)}")
        
        # Try manual parsing
        try:
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
                
                return html
        except Exception as e2:
            st.error(f"Failed to manually parse the ontology: {str(e2)}")
        
        return None

def create_entity_category_chart(entities):
    """
    Create a pie chart of entity categories.
    
    Args:
        entities (list): List of entity dictionaries
        
    Returns:
        plotly.graph_objects.Figure: Pie chart figure
    """
    # Convert to DataFrame for easier manipulation
    df = pd.DataFrame(entities)
    
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
    
    return fig

def download_link(object_to_download, download_filename, download_link_text):
    """
    Generate a link to download an object as a file.
    
    Args:
        object_to_download: Object to download
        download_filename (str): Name of the file to download
        download_link_text (str): Text for the download link
        
    Returns:
        str: HTML link for downloading
    """
    if isinstance(object_to_download, pd.DataFrame):
        object_to_download = object_to_download.to_csv(index=False)
    
    # Encode to base64
    b64 = base64.b64encode(object_to_download.encode()).decode()
    
    return f'<a href="data:file/txt;base64,{b64}" download="{download_filename}">{download_link_text}</a>' 