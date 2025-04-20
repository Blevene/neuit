import streamlit as st
import pandas as pd
import networkx as nx
import plotly.graph_objects as go
import json
from pyvis.network import Network
from neo4j import GraphDatabase
import os
import tempfile
from datetime import datetime

# Neo4j connection parameters from environment variables or default values
URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
USERNAME = os.environ.get("NEO4J_USER", "neo4j")
PASSWORD = os.environ.get("NEO4J_PASSWORD", "password")

# Page config and title
st.set_page_config(
    page_title="Knowledge Graph Explorer",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🧠 Educational Knowledge Graph Explorer")
st.markdown("""
This tool allows you to explore the educational knowledge graph built from the corpus data.
Use the sidebar to navigate different exploration views and search functionality.
""")

# Connect to Neo4j
@st.cache_resource
def get_neo4j_driver():
    return GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

try:
    driver = get_neo4j_driver()
    # Test the connection
    with driver.session() as session:
        result = session.run("RETURN 'Connected to Neo4j' AS message")
        message = result.single()[0]
        st.sidebar.success(message)
        st.sidebar.info(f"Connected to: {URI}")
except Exception as e:
    st.sidebar.error(f"Failed to connect to Neo4j: {str(e)}")
    st.sidebar.info(f"Attempted connection to: {URI}")
    st.sidebar.info("If running locally, make sure your Neo4j Docker container is running.")
    st.sidebar.info("Run: docker compose up -d")
    st.stop()

# Sidebar navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Choose a page",
    ["Overview", "Concept Explorer", "Relationship Visualizer", "Rule Browser", "Search"]
)

# Helper functions
def run_query(query, params=None):
    with driver.session() as session:
        if params:
            result = session.run(query, params)
        else:
            result = session.run(query)
        return [record for record in result]

def get_all_concepts():
    query = """
    MATCH (c:Concept)
    RETURN c.id AS id, c.name AS name, c.from_ontology AS from_ontology
    ORDER BY c.name
    """
    records = run_query(query)
    return [(r["id"], r["name"]) for r in records]

def get_concept_details(concept_id):
    query = """
    MATCH (c:Concept {id: $concept_id})
    OPTIONAL MATCH (c)-[:HAS_LABEL]->(l:Label)
    RETURN c.name AS name, 
           c.from_ontology AS from_ontology, 
           c.sources AS sources,
           collect({text: l.text, type: l.type, justification: l.justification}) AS labels
    """
    records = run_query(query, {"concept_id": concept_id})
    if records:
        return records[0]
    return None

def get_concept_relationships(concept_id):
    query = """
    MATCH (c:Concept {id: $concept_id})-[r]->(other)
    RETURN type(r) AS relationship_type, 
           CASE WHEN other:Concept THEN other.name ELSE labels(other)[0] + ': ' + other.id END AS related_entity,
           CASE WHEN other:Concept THEN 'Concept' ELSE labels(other)[0] END AS entity_type,
           other.id AS entity_id,
           'outgoing' AS direction
    UNION
    MATCH (other)-[r]->(c:Concept {id: $concept_id})
    RETURN type(r) AS relationship_type, 
           CASE WHEN other:Concept THEN other.name ELSE labels(other)[0] + ': ' + other.id END AS related_entity,
           CASE WHEN other:Concept THEN 'Concept' ELSE labels(other)[0] END AS entity_type,
           other.id AS entity_id,
           'incoming' AS direction
    """
    return run_query(query, {"concept_id": concept_id})

def get_rules():
    query = """
    MATCH (r:Rule)
    RETURN r.id AS id, r.if_text AS if_text, r.then_text AS then_text, r.confidence AS confidence
    ORDER BY r.id
    """
    return run_query(query)

def get_rule_details(rule_id):
    query = """
    MATCH (r:Rule {id: $rule_id})
    OPTIONAL MATCH (concept)-[:SUPPORTS_RULE]->(r)
    OPTIONAL MATCH (r)-[:SUPPORTS_RULE]->(concept2)
    RETURN r.if_text AS if_text, 
           r.then_text AS then_text, 
           r.confidence AS confidence,
           r.justification AS justification,
           r.ontology_classes AS ontology_classes,
           collect(DISTINCT concept.name) AS if_concepts,
           collect(DISTINCT concept2.name) AS then_concepts
    """
    records = run_query(query, {"rule_id": rule_id})
    if records:
        return records[0]
    return None

def search_concepts(query_text):
    # Using a simple CONTAINS search
    cypher_query = """
    MATCH (c:Concept)
    WHERE toLower(c.name) CONTAINS toLower($query) OR toLower(c.id) CONTAINS toLower($query)
    RETURN c.id AS id, c.name AS name, c.from_ontology AS from_ontology
    UNION
    MATCH (c:Concept)-[:HAS_LABEL]->(l:Label)
    WHERE toLower(l.text) CONTAINS toLower($query)
    RETURN c.id AS id, c.name AS name, c.from_ontology AS from_ontology
    """
    return run_query(cypher_query, {"query": query_text})

def get_graph_summary():
    summaries = []
    
    # Count concepts
    query = "MATCH (c:Concept) RETURN count(c) AS count"
    result = run_query(query)
    concept_count = result[0]["count"] if result else 0
    summaries.append({"Entity": "Concepts", "Count": concept_count})
    
    # Count labels
    query = "MATCH (l:Label) RETURN count(l) AS count"
    result = run_query(query)
    label_count = result[0]["count"] if result else 0
    summaries.append({"Entity": "Labels", "Count": label_count})
    
    # Count rules
    query = "MATCH (r:Rule) RETURN count(r) AS count"
    result = run_query(query)
    rule_count = result[0]["count"] if result else 0
    summaries.append({"Entity": "Rules", "Count": rule_count})
    
    # Count ontology classes
    query = "MATCH (o:OntologyClass) RETURN count(o) AS count"
    result = run_query(query)
    ontology_count = result[0]["count"] if result else 0
    summaries.append({"Entity": "Ontology Classes", "Count": ontology_count})
    
    # Count relationships
    query = "MATCH ()-[r]->() RETURN count(r) AS count"
    result = run_query(query)
    rel_count = result[0]["count"] if result else 0
    summaries.append({"Entity": "Relationships", "Count": rel_count})
    
    # Top 5 concepts with most relationships
    query = """
    MATCH (c:Concept)-[r]-()
    WITH c, count(r) AS rel_count
    RETURN c.name AS concept, rel_count
    ORDER BY rel_count DESC
    LIMIT 5
    """
    top_concepts = run_query(query)
    
    return summaries, top_concepts

def generate_neighborhood_graph(concept_id, depth=1):
    query = f"""
    MATCH path = (c:Concept {{id: $concept_id}})-[*1..{depth}]-(other:Concept)
    RETURN path
    LIMIT 50
    """
    results = run_query(query, {"concept_id": concept_id})
    
    G = nx.Graph()
    
    # Add the central node
    central_details = get_concept_details(concept_id)
    central_name = central_details["name"] if central_details else concept_id
    G.add_node(concept_id, label=central_name, color="#ff9900", size=20, group=1)
    
    # Process paths
    for record in results:
        path = record["path"]
        nodes = path.nodes
        relationships = path.relationships
        
        for node in nodes:
            node_id = node._properties.get("id", str(node.id))
            node_name = node._properties.get("name", node_id)
            if node_id == concept_id:
                continue  # Skip central node as we already added it
            
            if node_id not in G:
                G.add_node(node_id, label=node_name, color="#6699cc", size=15, group=2)
        
        for rel in relationships:
            start_id = rel.start_node._properties.get("id", str(rel.start_node.id))
            end_id = rel.end_node._properties.get("id", str(rel.end_node.id))
            rel_type = rel.type
            
            if (start_id, end_id) not in G.edges and (end_id, start_id) not in G.edges:
                G.add_edge(start_id, end_id, title=rel_type, label=rel_type)
    
    return G

# Pages
def overview_page():
    st.header("📊 Knowledge Graph Overview")
    
    summaries, top_concepts = get_graph_summary()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Graph Statistics")
        st.dataframe(pd.DataFrame(summaries), use_container_width=True)
    
    with col2:
        st.subheader("Top Connected Concepts")
        if top_concepts:
            fig = go.Figure([go.Bar(
                x=[c["concept"] for c in top_concepts],
                y=[c["rel_count"] for c in top_concepts],
                marker_color='indianred'
            )])
            fig.update_layout(title="Concepts with Most Relationships", 
                              xaxis_title="Concept",
                              yaxis_title="Number of Relationships")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No relationship data available.")
    
    # Sample visualization of the graph
    st.subheader("Sample Graph Visualization")
    
    # Get a few random concepts for the sample visualization
    query = """
    MATCH (c:Concept)
    WITH c LIMIT 15
    OPTIONAL MATCH (c)-[r]-(other:Concept)
    RETURN c, r, other
    """
    results = run_query(query)
    
    if results:
        # Create a network
        net = Network(height="600px", width="100%", notebook=True, cdn_resources="remote")
        net.toggle_physics(True)
        net.set_options("""
        var options = {
            "nodes": {
                "font": {
                    "size": 16
                }
            },
            "edges": {
                "arrows": {
                    "to": {
                        "enabled": true
                    }
                },
                "color": {
                    "inherit": true
                },
                "smooth": {
                    "enabled": false
                }
            },
            "physics": {
                "forceAtlas2Based": {
                    "gravitationalConstant": -100,
                    "centralGravity": 0.05,
                    "springLength": 200,
                    "springConstant": 0.08
                },
                "minVelocity": 0.75,
                "solver": "forceAtlas2Based"
            }
        }
        """)
        
        # Create a set to track added nodes and edges
        added_nodes = set()
        added_edges = set()
        
        for record in results:
            # Process nodes and relationships
            if "c" in record and record["c"] is not None:
                node = record["c"]
                node_id = node._properties.get("id", str(node.id))
                node_name = node._properties.get("name", node_id)
                
                if node_id not in added_nodes:
                    net.add_node(node_id, label=node_name, title=node_name, color="#6699cc")
                    added_nodes.add(node_id)
            
            if ("r" in record and record["r"] is not None and 
                "other" in record and record["other"] is not None):
                relationship = record["r"]
                other_node = record["other"]
                
                start_id = relationship.start_node._properties.get("id", str(relationship.start_node.id))
                end_id = relationship.end_node._properties.get("id", str(relationship.end_node.id))
                rel_type = relationship.type
                
                # Add the other node if not added yet
                other_id = other_node._properties.get("id", str(other_node.id))
                other_name = other_node._properties.get("name", other_id)
                
                if other_id not in added_nodes:
                    net.add_node(other_id, label=other_name, title=other_name, color="#6699cc")
                    added_nodes.add(other_id)
                
                # Add the edge if not added yet
                edge_id = f"{start_id}-{end_id}-{rel_type}"
                if edge_id not in added_edges:
                    net.add_edge(start_id, end_id, title=rel_type, label=rel_type)
                    added_edges.add(edge_id)
        
        # Generate and display the graph
        try:
            path = os.path.join(tempfile.gettempdir(), f"graph_{datetime.now().strftime('%Y%m%d%H%M%S')}.html")
            net.save_graph(path)
            with open(path, "r", encoding="utf-8") as f:
                html = f.read()
            st.components.v1.html(html, height=600)
        except Exception as e:
            st.error(f"Error generating graph visualization: {str(e)}")
    else:
        st.info("No data available to visualize.")

def concept_explorer_page():
    st.header("🔍 Concept Explorer")
    
    # Get all concepts
    concepts = get_all_concepts()
    
    if not concepts:
        st.warning("No concepts found in the database.")
        return
    
    # Create a selectbox for concept selection
    selected_concept = st.selectbox(
        "Select a concept to explore:",
        options=[c[0] for c in concepts],
        format_func=lambda x: next((name for id, name in concepts if id == x), x)
    )
    
    if selected_concept:
        # Get concept details
        details = get_concept_details(selected_concept)
        
        if details:
            st.subheader(f"Concept: {details['name']}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**General Information**")
                st.write(f"From Ontology: {details['from_ontology']}")
                
                sources = json.loads(details['sources']) if details['sources'] else []
                st.write(f"Sources: {', '.join(sources)}")
                
                st.markdown("**Labels**")
                if details['labels'] and len(details['labels']) > 0 and details['labels'][0].get('text'):
                    for label in details['labels']:
                        st.markdown(f"- **{label['text']}** ({label['type']})")
                        st.markdown(f"  *{label['justification']}*")
                else:
                    st.info("No labels found for this concept.")
            
            with col2:
                st.markdown("**Relationships**")
                relationships = get_concept_relationships(selected_concept)
                
                if relationships:
                    outgoing = [r for r in relationships if r['direction'] == 'outgoing']
                    incoming = [r for r in relationships if r['direction'] == 'incoming']
                    
                    if outgoing:
                        st.markdown("**Outgoing Relationships:**")
                        for rel in outgoing:
                            st.markdown(f"- **{rel['relationship_type']}** → {rel['related_entity']} ({rel['entity_type']})")
                    
                    if incoming:
                        st.markdown("**Incoming Relationships:**")
                        for rel in incoming:
                            st.markdown(f"- {rel['related_entity']} ({rel['entity_type']}) **{rel['relationship_type']}** → This concept")
                else:
                    st.info("No relationships found for this concept.")
        
        # Visualization of neighborhood
        st.subheader("Concept Neighborhood Visualization")
        depth = st.slider("Relationship Depth", min_value=1, max_value=3, value=1, 
                         help="How many relationships to traverse from this concept")
        
        graph = generate_neighborhood_graph(selected_concept, depth)
        
        if len(graph.nodes) > 0:
            net = Network(height="600px", width="100%", notebook=True, cdn_resources="remote")
            net.toggle_physics(True)
            net.from_nx(graph)
            net.set_options("""
            var options = {
                "nodes": {
                    "font": {
                        "size": 16
                    }
                },
                "edges": {
                    "color": {
                        "inherit": true
                    },
                    "smooth": {
                        "enabled": false
                    }
                },
                "physics": {
                    "forceAtlas2Based": {
                        "gravitationalConstant": -100,
                        "centralGravity": 0.05,
                        "springLength": 200,
                        "springConstant": 0.08
                    },
                    "minVelocity": 0.75,
                    "solver": "forceAtlas2Based"
                }
            }
            """)
            
            try:
                path = os.path.join(tempfile.gettempdir(), f"neighborhood_{datetime.now().strftime('%Y%m%d%H%M%S')}.html")
                net.save_graph(path)
                with open(path, "r", encoding="utf-8") as f:
                    html = f.read()
                st.components.v1.html(html, height=600)
            except Exception as e:
                st.error(f"Error generating neighborhood visualization: {str(e)}")
        else:
            st.info(f"No connected concepts found within depth {depth}.")

def relationship_visualizer_page():
    st.header("🔗 Relationship Visualizer")
    
    # Get all concepts
    concepts = get_all_concepts()
    
    if not concepts:
        st.warning("No concepts found in the database.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Multi-select for concepts
        selected_concepts = st.multiselect(
            "Select concepts to visualize relationships:",
            options=[c[0] for c in concepts],
            format_func=lambda x: next((name for id, name in concepts if id == x), x),
            default=[concepts[0][0]] if concepts else None,
            max_selections=10
        )
    
    with col2:
        # Relationship types to include
        relationship_types = st.multiselect(
            "Filter by relationship types (leave empty for all):",
            options=["RELATED_TO", "SUBCLASS_OF", "INSTANCE_OF", "HAS_LABEL", "SUPPORTS_RULE"],
            default=["RELATED_TO", "SUBCLASS_OF", "INSTANCE_OF"]
        )
    
    if selected_concepts:
        # Build query based on selections
        rel_filter = ""
        if relationship_types:
            rel_types = ", ".join([f"'{r}'" for r in relationship_types])
            rel_filter = f"AND type(r) IN [{rel_types}]"
        
        concept_ids = ", ".join([f"'{c}'" for c in selected_concepts])
        query = f"""
        MATCH (c1:Concept)-[r]-(c2:Concept)
        WHERE c1.id IN [{concept_ids}] AND c2.id IN [{concept_ids}] {rel_filter}
        RETURN c1, r, c2
        """
        
        results = run_query(query)
        
        if results:
            # Create network
            net = Network(height="700px", width="100%", notebook=True, cdn_resources="remote")
            net.toggle_physics(True)
            
            # Set advanced options
            net.set_options("""
            var options = {
                "nodes": {
                    "font": {
                        "size": 18
                    },
                    "borderWidth": 2,
                    "shadow": true
                },
                "edges": {
                    "arrows": {
                        "to": {
                            "enabled": true
                        }
                    },
                    "font": {
                        "size": 14
                    },
                    "width": 2,
                    "shadow": true
                },
                "physics": {
                    "forceAtlas2Based": {
                        "gravitationalConstant": -120,
                        "centralGravity": 0.1,
                        "springLength": 150,
                        "springConstant": 0.09
                    },
                    "minVelocity": 0.75,
                    "solver": "forceAtlas2Based"
                }
            }
            """)
            
            # Track added nodes and edges
            added_nodes = set()
            added_edges = set()
            
            for record in results:
                # Extract nodes and relationship
                node1 = record["c1"]
                node2 = record["c2"]
                relationship = record["r"]
                
                # Get properties
                node1_id = node1._properties.get("id", str(node1.id))
                node1_name = node1._properties.get("name", node1_id)
                node2_id = node2._properties.get("id", str(node2.id))
                node2_name = node2._properties.get("name", node2_id)
                rel_type = relationship.type
                
                # Add nodes if not already added
                if node1_id not in added_nodes:
                    color = "#ff9900" if node1_id in selected_concepts else "#6699cc"
                    net.add_node(node1_id, label=node1_name, title=node1_name, color=color, size=20 if node1_id in selected_concepts else 15)
                    added_nodes.add(node1_id)
                
                if node2_id not in added_nodes:
                    color = "#ff9900" if node2_id in selected_concepts else "#6699cc"
                    net.add_node(node2_id, label=node2_name, title=node2_name, color=color, size=20 if node2_id in selected_concepts else 15)
                    added_nodes.add(node2_id)
                
                # Add edge
                edge_id = f"{node1_id}-{node2_id}-{rel_type}"
                if edge_id not in added_edges:
                    net.add_edge(node1_id, node2_id, title=rel_type, label=rel_type)
                    added_edges.add(edge_id)
            
            # Generate and display the graph
            try:
                path = os.path.join(tempfile.gettempdir(), f"relationships_{datetime.now().strftime('%Y%m%d%H%M%S')}.html")
                net.save_graph(path)
                with open(path, "r", encoding="utf-8") as f:
                    html = f.read()
                st.components.v1.html(html, height=700)
            except Exception as e:
                st.error(f"Error generating visualization: {str(e)}")
        else:
            st.info("No relationships found between the selected concepts with the specified filters.")
    else:
        st.info("Please select at least one concept to visualize.")

def rule_browser_page():
    st.header("📏 Rule Browser")
    
    # Get all rules
    rules = get_rules()
    
    if not rules:
        st.warning("No rules found in the database.")
        return
    
    # Create a selectbox for rule selection
    selected_rule = st.selectbox(
        "Select a rule to explore:",
        options=[r["id"] for r in rules],
        format_func=lambda x: f"Rule {x}: {next((r['if_text'][:50] + '...' if len(r['if_text']) > 50 else r['if_text'] for r in rules if r['id'] == x), x)}"
    )
    
    if selected_rule:
        # Get rule details
        details = get_rule_details(selected_rule)
        
        if details:
            st.subheader(f"Rule {selected_rule}")
            
            confidence = details["confidence"]
            confidence_color = "#4CAF50" if confidence >= 80 else "#FFC107" if confidence >= 60 else "#F44336"
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**Confidence:** <span style='color:{confidence_color}'>{confidence}%</span>", unsafe_allow_html=True)
                st.markdown("**IF:**")
                st.markdown(f"*{details['if_text']}*")
                
                st.markdown("**THEN:**")
                st.markdown(f"*{details['then_text']}*")
                
                if details["justification"]:
                    st.markdown("**Justification:**")
                    st.markdown(f"*{details['justification']}*")
            
            with col2:
                st.markdown("**Ontology Classes:**")
                ontology_classes = json.loads(details["ontology_classes"]) if details["ontology_classes"] else []
                for cls in ontology_classes:
                    st.markdown(f"- {cls}")
                
                st.markdown("**IF Concepts:**")
                if_concepts = details["if_concepts"]
                if if_concepts and if_concepts[0]:
                    for concept in if_concepts:
                        st.markdown(f"- {concept}")
                else:
                    st.info("No IF concepts found.")
                
                st.markdown("**THEN Concepts:**")
                then_concepts = details["then_concepts"]
                if then_concepts and then_concepts[0]:
                    for concept in then_concepts:
                        st.markdown(f"- {concept}")
                else:
                    st.info("No THEN concepts found.")
            
            # Visualization of rule relationships
            st.subheader("Rule Relationship Visualization")
            
            # Get if/then concepts for visualization
            if_concepts = [c for c in details["if_concepts"] if c]
            then_concepts = [c for c in details["then_concepts"] if c]
            
            if if_concepts or then_concepts:
                # Create a simple directed graph
                net = Network(height="500px", width="100%", directed=True, notebook=True, cdn_resources="remote")
                
                # Add rule node
                rule_node_id = f"rule_{selected_rule}"
                rule_label = f"Rule {selected_rule}"
                net.add_node(rule_node_id, label=rule_label, title=details["if_text"], color="#e74c3c", shape="box", size=20)
                
                # Add if concepts and connections
                for concept in if_concepts:
                    concept_id = f"if_{concept}"
                    net.add_node(concept_id, label=concept, title=concept, color="#3498db", size=15)
                    net.add_edge(concept_id, rule_node_id, title="IF", label="IF", color="#3498db")
                
                # Add then concepts and connections
                for concept in then_concepts:
                    concept_id = f"then_{concept}"
                    net.add_node(concept_id, label=concept, title=concept, color="#2ecc71", size=15)
                    net.add_edge(rule_node_id, concept_id, title="THEN", label="THEN", color="#2ecc71")
                
                # Set options
                net.set_options("""
                var options = {
                    "nodes": {
                        "font": {
                            "size": 16
                        }
                    },
                    "edges": {
                        "arrows": {
                            "to": {
                                "enabled": true
                            }
                        },
                        "color": {
                            "inherit": false
                        },
                        "smooth": {
                            "enabled": true,
                            "type": "curvedCW",
                            "roundness": 0.3
                        }
                    },
                    "physics": {
                        "forceAtlas2Based": {
                            "gravitationalConstant": -50,
                            "centralGravity": 0.01,
                            "springLength": 200,
                            "springConstant": 0.08
                        },
                        "minVelocity": 0.75,
                        "solver": "forceAtlas2Based"
                    }
                }
                """)
                
                # Generate and display the graph
                try:
                    path = os.path.join(tempfile.gettempdir(), f"rule_{datetime.now().strftime('%Y%m%d%H%M%S')}.html")
                    net.save_graph(path)
                    with open(path, "r", encoding="utf-8") as f:
                        html = f.read()
                    st.components.v1.html(html, height=500)
                except Exception as e:
                    st.error(f"Error generating rule visualization: {str(e)}")
            else:
                st.info("No concepts associated with this rule for visualization.")

def search_page():
    st.header("🔎 Search Knowledge Graph")
    
    search_query = st.text_input("Search for concepts, labels, or rules:", "")
    
    if search_query:
        st.subheader(f"Search Results for: {search_query}")
        
        # Search for concepts
        concept_results = search_concepts(search_query)
        
        if concept_results:
            st.write(f"Found {len(concept_results)} matching concepts:")
            
            # Display results in a table
            results_df = pd.DataFrame([
                {
                    "ID": r["id"],
                    "Name": r["name"],
                    "From Ontology": "Yes" if r["from_ontology"] else "No"
                }
                for r in concept_results
            ])
            
            st.dataframe(results_df, use_container_width=True)
            
            # Allow exploring a search result
            if len(concept_results) > 0:
                selected_result = st.selectbox(
                    "Select a result to explore:",
                    options=[r["id"] for r in concept_results],
                    format_func=lambda x: next((r["name"] for r in concept_results if r["id"] == x), x)
                )
                
                if selected_result:
                    # Get concept details
                    details = get_concept_details(selected_result)
                    
                    if details:
                        st.subheader(f"Concept: {details['name']}")
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**General Information**")
                            st.write(f"From Ontology: {details['from_ontology']}")
                            
                            sources = json.loads(details['sources']) if details['sources'] else []
                            st.write(f"Sources: {', '.join(sources)}")
                            
                            st.markdown("**Labels**")
                            if details['labels'] and len(details['labels']) > 0 and details['labels'][0].get('text'):
                                for label in details['labels']:
                                    st.markdown(f"- **{label['text']}** ({label['type']})")
                                    st.markdown(f"  *{label['justification']}*")
                            else:
                                st.info("No labels found for this concept.")
                        
                        with col2:
                            st.markdown("**Relationships**")
                            relationships = get_concept_relationships(selected_result)
                            
                            if relationships:
                                outgoing = [r for r in relationships if 'target' in r]
                                incoming = [r for r in relationships if 'source' in r]
                                
                                if outgoing:
                                    st.markdown("**Outgoing Relationships:**")
                                    for rel in outgoing:
                                        st.markdown(f"- **{rel['relationship_type']}** → {rel['target']} ({rel['entity_type']})")
                                
                                if incoming:
                                    st.markdown("**Incoming Relationships:**")
                                    for rel in incoming:
                                        st.markdown(f"- {rel['source']} ({rel['entity_type']}) **{rel['relationship_type']}** → This concept")
                            else:
                                st.info("No relationships found for this concept.")
        else:
            st.info("No matching concepts found.")

# Display the selected page
if page == "Overview":
    overview_page()
elif page == "Concept Explorer":
    concept_explorer_page()
elif page == "Relationship Visualizer":
    relationship_visualizer_page()
elif page == "Rule Browser":
    rule_browser_page()
elif page == "Search":
    search_page()

# Footer
st.markdown("---")
st.markdown("**Knowledge Graph Explorer** | Built with Streamlit & Neo4j") 