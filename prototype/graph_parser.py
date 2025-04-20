#!/usr/bin/env python
"""
Graph Parser for Schema Induction Output

This module transforms the outputs from the schema induction tooling:
- label_suggestions.txt/json: Concept labels with justifications
- ontology.txt: Ontology definitions in structured text format
- rules.txt: IF-THEN rules with confidence scores

Into a standardized JSONL format compliant with the unified graph schema.

Usage:
    python graph_parser.py /path/to/data/dir --output graph_data.jsonl
"""

import json
import re
import logging
from pathlib import Path
import argparse
from typing import Dict, List, Any, Optional, Set, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

# --- Utility Functions ---

def normalize_concept(text: str) -> str:
    """Convert concept text to a normalized slug form.
    
    Args:
        text: Raw concept text
        
    Returns:
        Normalized concept ID suitable for a graph database
    """
    if not text:
        return ""
    # Remove special characters, replace spaces with underscores, lowercase
    return re.sub(r"[^a-zA-Z0-9]", "_", text.strip()).lower()

def extract_json_from_text(text: str) -> Any:
    """Extract JSON data from potentially formatted text.
    
    Args:
        text: Raw text that might contain JSON
        
    Returns:
        Parsed JSON object or raises ValueError
    """
    # 1. Direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # 2. Remove markdown code fences
    cleaned = re.sub(r'```+\s*json`?', '', text)   # Remove ```json
    cleaned = re.sub(r'```+', '', cleaned)         # Remove remaining backticks
    cleaned = cleaned.strip()                      # Remove extra whitespace
    
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    
    # 3. Extract JSON array/object from within text
    json_pattern = r'(\[\s*\{.*\}\s*\]|\{\s*".*"\s*:.*\})'
    match = re.search(json_pattern, cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    
    # 4. Look for JSON objects line by line
    if cleaned.strip().startswith("{") and cleaned.strip().endswith("}"):
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass
    
    raise ValueError("Unable to extract valid JSON from text")

# --- Parsers ---

def parse_label_suggestions(file_path: Path) -> List[Dict[str, Any]]:
    """Parse the label suggestions file.
    
    Args:
        file_path: Path to label_suggestions.txt/json
        
    Returns:
        List of concept entries with labels
    """
    logging.info(f"Parsing label suggestions from {file_path}")
    
    # Check if we have JSON or TXT file
    is_json = file_path.suffix.lower() == '.json'
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        if is_json:
            data = json.loads(content)
        else:
            # Try to extract JSON from text
            try:
                data = extract_json_from_text(content)
            except ValueError:
                logging.warning(f"Could not parse JSON from {file_path}, falling back to text parsing")
                # Fallback to text parsing if needed
                lines = [line.strip() for line in content.splitlines() if line.strip()]
                data = [{"concept": line, "labels": []} for line in lines]
    except Exception as e:
        logging.error(f"Error reading {file_path}: {str(e)}")
        return []
    
    # Process the data into our standard format
    concepts = []
    for item in data:
        if not isinstance(item, dict) or "concept" not in item:
            continue
        
        concept_name = item["concept"]
        concept_id = normalize_concept(concept_name)
        
        # Process labels
        labels = []
        raw_labels = item.get("labels", [])
        
        if isinstance(raw_labels, list):
            for lbl in raw_labels:
                if isinstance(lbl, dict):
                    labels.append({
                        "text": lbl.get("text", ""),
                        "type": lbl.get("type", "Unknown"),
                        "justification": lbl.get("justification", "")
                    })
                elif isinstance(lbl, str):
                    labels.append({
                        "text": lbl,
                        "type": "Unknown",
                        "justification": ""
                    })
        
        # Get related concepts if available
        related_concepts = item.get("related_concepts", [])
        related_concepts = [normalize_concept(rc) for rc in related_concepts]
        
        # Get ontology class if available
        ontology_class = item.get("ontology_class", "")
        
        concepts.append({
            "concept": concept_id,
            "concept_name": concept_name,
            "labels": labels,
            "related_concepts": related_concepts,
            "ontology_class": ontology_class,
            "from_corpus": str(file_path.name)
        })
    
    logging.info(f"Extracted {len(concepts)} concepts with labels")
    return concepts

def parse_rules(file_path: Path) -> List[Dict[str, Any]]:
    """Parse the rules file.
    
    Args:
        file_path: Path to rules.txt
        
    Returns:
        List of rule entries
    """
    logging.info(f"Parsing rules from {file_path}")
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Try to extract structured rules from text format (Rule ID: N, IF: X, THEN: Y, Confidence: Z%)
        rule_pattern = r'Rule\s*ID:\s*(\d+).*?IF:\s*(.*?)THEN:\s*(.*?)Confidence:\s*(\d+)%'
        matches = re.finditer(rule_pattern, content, re.DOTALL | re.IGNORECASE)
        
        rules = []
        for match in matches:
            rule_id = int(match.group(1))
            if_text = match.group(2).strip()
            then_text = match.group(3).strip()
            confidence = int(match.group(4))
            
            # Extract justification if available
            justification = ""
            justification_match = re.search(r'Justification:\s*(.*?)(?=Ontology\s*Classes:|$)', 
                                           content[match.end():], re.DOTALL)
            if justification_match:
                justification = justification_match.group(1).strip()
            
            # Extract ontology classes if available
            ontology_classes = []
            classes_match = re.search(r'Ontology\s*Classes:\s*(.*?)(?=Rule\s*ID:|$)', 
                                     content[match.end():], re.DOTALL)
            if classes_match:
                class_text = classes_match.group(1).strip()
                ontology_classes = [cls.strip() for cls in class_text.split(',')]
            
            # Create a more structured rule with the parsed data
            rule = {
                "id": rule_id,
                "if_text": if_text,
                "then_text": then_text,
                "confidence": confidence,
                "justification": justification, 
                "ontology_classes": ontology_classes,
                "from_corpus": str(file_path.name)
            }
            
            # Normalize for the graph representation
            # Try to identify key concepts from the rule text
            if_concepts = []
            for cls in ontology_classes:
                if_concepts.append(normalize_concept(cls))
                
            # If no classes found, extract nouns from the text
            if not if_concepts:
                if_concepts = [normalize_concept(if_text)]
                
            rule["if_concepts"] = if_concepts
            rule["then_concept"] = normalize_concept(then_text)
            
            rules.append(rule)
        
        logging.info(f"Extracted {len(rules)} rules from {file_path}")
        return rules
    
    except Exception as e:
        logging.error(f"Error parsing rules from {file_path}: {str(e)}")
        return []

def parse_ontology(file_path: Path) -> List[Dict[str, Any]]:
    """Parse the ontology file.
    
    Args:
        file_path: Path to ontology.txt
        
    Returns:
        List of ontology class entries
    """
    logging.info(f"Parsing ontology from {file_path}")
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Extract class definitions using regex pattern
        # Looks for "Class: [Name]" followed by details
        class_pattern = r'Class:\s*(\[?[\w:]+\]?)\s*(?:SubClassOf:\s*(\[?[\w:]+\]?))?\s*Description:\s*(.*?)(?=Class:|$)'
        class_matches = re.finditer(class_pattern, content, re.DOTALL)
        
        ontology_classes = []
        for match in class_matches:
            class_name = match.group(1).strip('[]')
            superclass = match.group(2).strip('[]') if match.group(2) else None
            description = match.group(3).strip()
            
            # Extract properties
            properties = []
            prop_section = re.search(r'Properties:(.+?)(?=Related Concepts:|$)', match.group(0), re.DOTALL)
            if prop_section:
                prop_lines = prop_section.group(1).strip().split('\n')
                for line in prop_lines:
                    line = line.strip()
                    if line and line.startswith('-'):
                        prop_match = re.search(r'-\s*\[?([^:]+)\]?:\s*\[?([^-]+)\]?(?:-\s*(.+))?', line)
                        if prop_match:
                            prop_name = prop_match.group(1).strip()
                            prop_type = prop_match.group(2).strip()
                            prop_desc = prop_match.group(3).strip() if prop_match.group(3) else ""
                            properties.append({
                                "name": prop_name,
                                "type": prop_type,
                                "description": prop_desc
                            })
            
            # Extract related concepts
            related_concepts = []
            rel_section = re.search(r'Related Concepts:(.+?)(?=Class:|$)', match.group(0), re.DOTALL)
            if rel_section:
                rel_lines = rel_section.group(1).strip().split('\n')
                for line in rel_lines:
                    line = line.strip()
                    if line and line.startswith('-'):
                        rel_match = re.search(r'-\s*\[?([^:]+)\]?:\s*\[?([^-]+)\]?', line)
                        if rel_match:
                            rel_concept = rel_match.group(1).strip()
                            rel_type = rel_match.group(2).strip()
                            related_concepts.append({
                                "concept": normalize_concept(rel_concept),
                                "relationship": rel_type
                            })
            
            ontology_classes.append({
                "class": normalize_concept(class_name),
                "class_name": class_name,
                "superclass": normalize_concept(superclass) if superclass else None,
                "superclass_name": superclass,
                "description": description,
                "properties": properties,
                "related_concepts": related_concepts,
                "from_corpus": str(file_path.name)
            })
        
        if ontology_classes:
            logging.info(f"Extracted {len(ontology_classes)} ontology classes")
            return ontology_classes
        else:
            logging.warning(f"No structured ontology classes found in {file_path}")
            return []
        
    except Exception as e:
        logging.error(f"Error parsing ontology from {file_path}: {str(e)}")
        return []

# --- Integration Functions ---

def build_knowledge_graph(
    concepts: List[Dict[str, Any]], 
    rules: List[Dict[str, Any]], 
    ontology: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Build a unified knowledge graph from parsed data.
    
    Args:
        concepts: Parsed concept data
        rules: Parsed rule data
        ontology: Parsed ontology data
        
    Returns:
        List of combined graph nodes ready for JSONL output
    """
    # Create a dictionary to hold all concepts
    graph_nodes: Dict[str, Dict[str, Any]] = {}
    
    # First create a mapping of concept names for normalization
    concept_name_map = {}
    for concept in concepts:
        concept_id = concept["concept"]
        concept_name = concept.get("concept_name", "")
        if concept_name:
            # Add lowercase mapping for easier matching
            concept_name_map[concept_name.lower()] = concept_id
    
    # Add ontology class names to mapping
    for cls in ontology:
        class_id = cls["class"]
        class_name = cls.get("class_name", "")
        if class_name:
            concept_name_map[class_name.lower()] = class_id
    
    # Add concept nodes from labels
    for concept in concepts:
        concept_id = concept["concept"]
        if not concept_id:
            continue
            
        if concept_id not in graph_nodes:
            graph_nodes[concept_id] = {
                "concept": concept_id,
                "concept_name": concept.get("concept_name", concept_id),
                "labels": [],
                "rules_if": [],
                "rules_then": [],
                "from_ontology": False,
                "related_concepts": [],
                "sources": set(),
                "rule_data": []
            }
        
        # Add label information
        graph_nodes[concept_id]["labels"].extend(concept["labels"])
        
        # Add related concepts
        related = concept.get("related_concepts", [])
        if related:
            current = set(graph_nodes[concept_id]["related_concepts"])
            current.update(related)
            graph_nodes[concept_id]["related_concepts"] = list(current)
        
        # Add source
        graph_nodes[concept_id]["sources"].add(concept["from_corpus"])
    
    # Add rule relationships
    for rule in rules:
        rule_id = rule["id"]
        
        # Store the full rule data
        rule_data = {
            "id": rule_id,
            "if_text": rule.get("if_text", ""),
            "then_text": rule.get("then_text", ""),
            "confidence": rule.get("confidence", 100),
            "justification": rule.get("justification", ""),
            "ontology_classes": rule.get("ontology_classes", [])
        }
        
        # Look for concepts mentioned in the ontology_classes
        for cls_name in rule.get("ontology_classes", []):
            cls_id = normalize_concept(cls_name)
            
            # Check if this class matches any existing concept
            found = False
            for concept_name, concept_id in concept_name_map.items():
                if cls_name.lower() in concept_name or concept_name in cls_name.lower():
                    if concept_id not in graph_nodes:
                        # This shouldn't happen but just in case
                        continue
                        
                    # Add rule references
                    if rule_id not in graph_nodes[concept_id]["rules_if"]:
                        graph_nodes[concept_id]["rules_if"].append(rule_id)
                    
                    # Add rule data
                    graph_nodes[concept_id]["rule_data"].append(rule_data)
                    graph_nodes[concept_id]["sources"].add(rule["from_corpus"])
                    found = True
            
            # If not found, create a new concept
            if not found and cls_id:
                if cls_id not in graph_nodes:
                    graph_nodes[cls_id] = {
                        "concept": cls_id,
                        "concept_name": cls_name,
                        "labels": [],
                        "rules_if": [rule_id],
                        "rules_then": [],
                        "from_ontology": False,
                        "related_concepts": [],
                        "sources": set([rule["from_corpus"]]),
                        "rule_data": [rule_data]
                    }
                else:
                    graph_nodes[cls_id]["rules_if"].append(rule_id)
                    graph_nodes[cls_id]["rule_data"].append(rule_data)
                    graph_nodes[cls_id]["sources"].add(rule["from_corpus"])
        
        # Process the then concept as well
        then_concept = rule.get("then_concept")
        if then_concept:
            # Try to find a matching concept
            found = False
            for concept_name, concept_id in concept_name_map.items():
                if then_concept in concept_name or concept_name in then_concept:
                    if concept_id not in graph_nodes:
                        continue
                        
                    # Add rule references
                    if rule_id not in graph_nodes[concept_id]["rules_then"]:
                        graph_nodes[concept_id]["rules_then"].append(rule_id)
                    
                    # Add rule data if not already there
                    if not any(r["id"] == rule_id for r in graph_nodes[concept_id]["rule_data"]):
                        graph_nodes[concept_id]["rule_data"].append(rule_data)
                    
                    graph_nodes[concept_id]["sources"].add(rule["from_corpus"])
                    found = True
            
            # If not found, create a new concept
            if not found:
                if then_concept not in graph_nodes:
                    graph_nodes[then_concept] = {
                        "concept": then_concept,
                        "concept_name": rule.get("then_text", "").replace("_", " ").title(),
                        "labels": [],
                        "rules_if": [],
                        "rules_then": [rule_id],
                        "from_ontology": False,
                        "related_concepts": [],
                        "sources": set([rule["from_corpus"]]),
                        "rule_data": [rule_data]
                    }
                else:
                    graph_nodes[then_concept]["rules_then"].append(rule_id)
                    if not any(r["id"] == rule_id for r in graph_nodes[then_concept]["rule_data"]):
                        graph_nodes[then_concept]["rule_data"].append(rule_data)
                    graph_nodes[then_concept]["sources"].add(rule["from_corpus"])
    
    # Add ontology classes - unify with existing concepts when possible
    for cls in ontology:
        class_id = cls["class"]
        class_name = cls.get("class_name", "")
        if not class_id:
            continue
            
        # Try to find a matching concept from the labels
        matching_concept_id = None
        for concept_id, concept in graph_nodes.items():
            concept_name = concept.get("concept_name", "")
            if concept_name.lower() == class_name.lower() or class_id == concept_id:
                matching_concept_id = concept_id
                break
        
        if matching_concept_id and matching_concept_id != class_id:
            # We found a match with a different ID, merge them
            if class_id in graph_nodes:
                # Copy data from class_id to matching_concept_id
                graph_nodes[matching_concept_id]["from_ontology"] = True
                graph_nodes[matching_concept_id]["sources"].add(cls["from_corpus"])
                
                # Merge related concepts
                related = set(graph_nodes[matching_concept_id]["related_concepts"])
                related.update(graph_nodes[class_id].get("related_concepts", []))
                graph_nodes[matching_concept_id]["related_concepts"] = list(related)
                
                # Add ontology data
                graph_nodes[matching_concept_id]["ontology_data"] = {
                    "superclass": cls.get("superclass"),
                    "superclass_name": cls.get("superclass_name"),
                    "description": cls.get("description", ""),
                    "properties": cls.get("properties", [])
                }
                
                # Remove the duplicate
                del graph_nodes[class_id]
                
                # Update any references to the old ID
                for node_id, node in graph_nodes.items():
                    if class_id in node.get("related_concepts", []):
                        node["related_concepts"].remove(class_id)
                        if matching_concept_id not in node["related_concepts"]:
                            node["related_concepts"].append(matching_concept_id)
            else:
                # Just mark the existing node as from ontology
                graph_nodes[matching_concept_id]["from_ontology"] = True
                graph_nodes[matching_concept_id]["sources"].add(cls["from_corpus"])
                
                # Add ontology data
                graph_nodes[matching_concept_id]["ontology_data"] = {
                    "superclass": cls.get("superclass"),
                    "superclass_name": cls.get("superclass_name"),
                    "description": cls.get("description", ""),
                    "properties": cls.get("properties", [])
                }
        elif class_id not in graph_nodes:
            # No match found, create a new entry
            graph_nodes[class_id] = {
                "concept": class_id,
                "concept_name": class_name,
                "labels": [],
                "rules_if": [],
                "rules_then": [],
                "from_ontology": True,
                "related_concepts": [],
                "sources": set([cls["from_corpus"]]),
                "rule_data": [],
                "ontology_data": {
                    "superclass": cls.get("superclass"),
                    "superclass_name": cls.get("superclass_name"),
                    "description": cls.get("description", ""),
                    "properties": cls.get("properties", [])
                }
            }
        else:
            # Entry already exists, update it
            graph_nodes[class_id]["from_ontology"] = True
            graph_nodes[class_id]["concept_name"] = class_name
            graph_nodes[class_id]["sources"].add(cls["from_corpus"])
            
            # Add ontology data
            graph_nodes[class_id]["ontology_data"] = {
                "superclass": cls.get("superclass"),
                "superclass_name": cls.get("superclass_name"),
                "description": cls.get("description", ""),
                "properties": cls.get("properties", [])
            }
        
        # Update concept to use our node ID (might have been changed)
        node_id = matching_concept_id or class_id
        
        # Connect superclass relationship
        superclass = cls.get("superclass")
        if superclass and superclass not in graph_nodes[node_id]["related_concepts"]:
            graph_nodes[node_id]["related_concepts"].append(superclass)
        
        # Add related concepts from ontology and create bidirectional relationships
        for rel in cls.get("related_concepts", []):
            rel_concept = rel.get("concept")
            if rel_concept and rel_concept not in graph_nodes[node_id]["related_concepts"]:
                graph_nodes[node_id]["related_concepts"].append(rel_concept)
                
                # Create the related concept if it doesn't exist
                if rel_concept not in graph_nodes:
                    graph_nodes[rel_concept] = {
                        "concept": rel_concept,
                        "concept_name": rel_concept.replace("_", " ").title(),
                        "labels": [],
                        "rules_if": [],
                        "rules_then": [],
                        "from_ontology": False,
                        "related_concepts": [node_id],  # Add bidirectional relationship
                        "sources": set([cls["from_corpus"]]),
                        "rule_data": []
                    }
                elif node_id not in graph_nodes[rel_concept]["related_concepts"]:
                    graph_nodes[rel_concept]["related_concepts"].append(node_id)
                    graph_nodes[rel_concept]["sources"].add(cls["from_corpus"])
    
    # Convert to list and finalize
    result = []
    for node_id, node in graph_nodes.items():
        # Convert sources set to list for JSON serialization
        node["sources"] = list(node["sources"])
        result.append(node)
    
    return result

def write_jsonl(data: List[Dict[str, Any]], output_path: Path) -> None:
    """Write data to JSONL file.
    
    Args:
        data: List of data items to write
        output_path: Path to output file
    """
    # Ensure the parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        for item in data:
            f.write(json.dumps(item) + "\n")
    
    logging.info(f"Wrote {len(data)} items to {output_path}")

def main() -> None:
    parser = argparse.ArgumentParser(description="Parse schema induction outputs to JSONL")
    parser.add_argument(
        "input_dir", 
        type=Path, 
        help="Directory containing label_suggestions.txt/json, ontology.txt, and rules.txt"
    )
    parser.add_argument(
        "--output", 
        "-o", 
        type=Path, 
        default=Path("knowledge_graph.jsonl"), 
        help="Path for output JSONL file"
    )
    parser.add_argument(
        "--verbose", 
        "-v", 
        action="store_true", 
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate input directory
    if not args.input_dir.exists() or not args.input_dir.is_dir():
        logging.error(f"Input directory {args.input_dir} does not exist or is not a directory")
        return
    
    # Look for input files
    label_files = list(args.input_dir.glob("label_suggestions.*"))
    if not label_files:
        logging.error(f"No label_suggestions.txt or label_suggestions.json found in {args.input_dir}")
        return
    
    label_file = next((f for f in label_files if f.suffix.lower() == '.json'), None)
    if not label_file:
        label_file = next((f for f in label_files if f.suffix.lower() == '.txt'), None)
    
    ontology_file = args.input_dir / "ontology.txt"
    rules_file = args.input_dir / "rules.txt"
    
    if not label_file.exists():
        logging.error(f"Label file {label_file} not found")
        return
    
    if not ontology_file.exists():
        logging.error(f"Ontology file {ontology_file} not found")
        return
    
    if not rules_file.exists():
        logging.error(f"Rules file {rules_file} not found")
        return
    
    # Parse the input files
    concepts = parse_label_suggestions(label_file)
    rules = parse_rules(rules_file)
    ontology_classes = parse_ontology(ontology_file)
    
    # Build the knowledge graph
    knowledge_graph = build_knowledge_graph(concepts, rules, ontology_classes)
    
    # Write to JSONL
    write_jsonl(knowledge_graph, args.output)
    
    logging.info(f"Schema parsing complete. Output written to {args.output}")

if __name__ == "__main__":
    main()