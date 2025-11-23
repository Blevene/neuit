# Multi-Pass Knowledge Extraction Controller
# Enhanced with Quality Assurance and Neo4j Integration

import json
import logging
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import mimetypes
import magic
import sys
import os

# Add parent directory to Python path to make the llm module accessible
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from llm.llm_utils import call_llm_with_prompt, get_provider_stats
from backend.quality_assurance import QualityAssurance
from backend.neo4j_integration import create_neo4j_connector
from PyPDF2 import PdfReader
from docx import Document

# --- Configuration ---
PROMPT_DIR = Path("prompts")
INPUT_PATH = Path("data")
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)
TOP_N = 10
SUPPORTED_EXTENSIONS = ['.txt', '.md', '.json', '.pdf', '.docx']
ENABLE_PARALLELISM = True
MAX_WORKERS = 4

# Quality Assurance Configuration
ENABLE_QA = os.getenv("ENABLE_QA", "true").lower() == "true"
QA_MIN_CONFIDENCE = float(os.getenv("QA_MIN_CONFIDENCE", "0.5"))
QA_STRICT_MODE = os.getenv("QA_STRICT_MODE", "false").lower() == "true"

# Neo4j Integration Configuration
ENABLE_NEO4J = os.getenv("ENABLE_NEO4J", "false").lower() == "true"

# Global instances
qa_system = QualityAssurance(min_confidence=QA_MIN_CONFIDENCE, enable_strict_mode=QA_STRICT_MODE) if ENABLE_QA else None
neo4j_connector = None

# --- Logging ---
logging.basicConfig(
    filename=OUTPUT_DIR / "pipeline.log",
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# --- Prompt Templates ---
PROMPTS = {
    "entity": (PROMPT_DIR / "entity_extraction.prompt.txt").read_text(),
    "relationship": (PROMPT_DIR / "relationship_extraction.prompt.txt").read_text(),
    "rule": (PROMPT_DIR / "rule_induction.prompt.txt").read_text(),
    "ontology": (PROMPT_DIR / "ontology_generation.prompt.txt").read_text(),
    "justification": (PROMPT_DIR / "explanation_generation.prompt.txt").read_text()
}

# --- File Handling ---
def read_corpus(file_path: Path) -> str:
    try:
        mime = magic.from_file(str(file_path), mime=True)
        logger.info(f"Detected MIME type for {file_path.name}: {mime}")

        # Check file extension as a fallback
        file_ext = file_path.suffix.lower()

        if mime == "application/pdf" or file_ext == '.pdf':
            reader = PdfReader(file_path)
            return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
        elif mime == "application/vnd.openxmlformats-officedocument.wordprocessingml.document" or mime == "application/zip" and file_ext == '.docx':
            doc = Document(file_path)
            return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
        elif mime == "application/json" or file_ext == '.json':
            with open(file_path) as f:
                return json.dumps(json.load(f), indent=2)
        elif mime in ["text/plain", "text/markdown"] or file_ext in [".txt", ".md"]:
            return file_path.read_text()
        else:
            logger.warning(f"Unsupported MIME type for {file_path.name}: {mime}")
            return "[UNSUPPORTED FILE TYPE]"

    except Exception as e:
        logger.error(f"Error reading {file_path.name}: {e}")
        return f"[ERROR reading {file_path.name}: {e}]"

# --- Knowledge Extraction Passes ---
def run_entity_pass(corpus: str):
    prompt = PROMPTS["entity"].replace("{corpus}", corpus).replace("{top_n}", str(TOP_N))
    response = call_llm_with_prompt(prompt)
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        logger.error("Failed to parse entity response as JSON")
        return []

def run_relationship_pass(entities, corpus):
    concepts = ", ".join([e["name"] for e in entities])
    prompt = PROMPTS["relationship"].replace("{concepts}", concepts).replace("{corpus}", corpus)
    response = call_llm_with_prompt(prompt)
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        logger.error("Failed to parse relationship response as JSON")
        return []

def run_rule_pass(corpus):
    prompt = PROMPTS["rule"].replace("{corpus}", corpus)
    response = call_llm_with_prompt(prompt)
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        logger.error("Failed to parse rule response as JSON")
        return []

def run_ontology_pass(corpus):
    prompt = PROMPTS["ontology"].replace("{corpus}", corpus)
    return call_llm_with_prompt(prompt)

def run_justification_pass(rules, corpus):
    prompt = PROMPTS["justification"].replace("{corpus}", corpus).replace("{rules}", json.dumps(rules))
    response = call_llm_with_prompt(prompt)
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        logger.error("Failed to parse justification response as JSON")
        # Save the original response as text for troubleshooting
        return [{"explanation": response}]

# --- File Processor ---
master_metadata = []

def process_corpus_file(file_path: Path):
    try:
        corpus = read_corpus(file_path)
        base_name = file_path.stem
        logger.info(f"[START] Processing {file_path.name}")

        # Reset QA system for new document
        if qa_system:
            qa_system.reset()

        # Run extraction passes
        entities = run_entity_pass(corpus)
        relationships = run_relationship_pass(entities, corpus)
        rules = run_rule_pass(corpus)
        ontology = run_ontology_pass(corpus)
        justifications = run_justification_pass(rules, corpus)

        # Apply Quality Assurance
        quality_report = None
        if qa_system and ENABLE_QA:
            logger.info("[QA] Running quality assurance checks...")

            # Filter and assess entities
            entities, entity_metrics = qa_system.filter_low_quality(entities, 'entity')

            # Filter and assess relationships
            relationships, rel_metrics = qa_system.filter_low_quality(relationships, 'relationship')

            # Filter and assess rules
            rules, rule_metrics = qa_system.filter_low_quality(rules, 'rule')

            # Generate quality report
            quality_report = qa_system.generate_quality_report(entity_metrics, rel_metrics, rule_metrics)
            logger.info(f"[QA] Quality Score: {quality_report.get('overall_quality_score', 0):.3f}")

        def save_json(obj, suffix):
            try:
                (OUTPUT_DIR / f"{base_name}_{suffix}.json").write_text(json.dumps(obj, indent=2))
                return True
            except Exception as e:
                logger.error(f"Error saving {suffix} JSON: {e}")
                return False

        # Save all outputs
        save_json(entities, "entities")
        save_json(relationships, "relationships")
        save_json(rules, "rules")
        save_json(justifications, "justifications")

        # Save quality report if available
        if quality_report:
            save_json(quality_report, "quality_report")

        try:
            (OUTPUT_DIR / f"{base_name}_ontology.ttl").write_text(ontology)
            ontology_lines = len(ontology.strip().splitlines())
        except Exception as e:
            logger.error(f"Error saving ontology: {e}")
            ontology_lines = 0

        # Export to Neo4j if enabled
        neo4j_stats = None
        if ENABLE_NEO4J and neo4j_connector:
            try:
                logger.info("[Neo4j] Exporting to graph database...")
                neo4j_stats = neo4j_connector.import_knowledge_graph(
                    entities=entities,
                    relationships=relationships,
                    rules=rules,
                    document_name=file_path.name
                )
                logger.info(f"[Neo4j] Export complete: {neo4j_stats}")
            except Exception as e:
                logger.error(f"[Neo4j] Export failed: {e}")
                neo4j_stats = {"error": str(e)}

        # Prepare metadata
        metadata = {
            "filename": file_path.name,
            "num_entities": len(entities),
            "num_relationships": len(relationships),
            "num_rules": len(rules),
            "num_justifications": len(justifications),
            "ontology_lines": ontology_lines,
            "source_path": str(file_path.resolve()),
            "success": True
        }

        # Add quality metrics to metadata
        if quality_report:
            metadata["quality"] = quality_report

        # Add Neo4j stats to metadata
        if neo4j_stats:
            metadata["neo4j"] = neo4j_stats

        save_json(metadata, "metadata")
        master_metadata.append(metadata)
        logger.info(f"[SUCCESS] {file_path.name} processed.")

    except Exception as e:
        logger.error(f"[FAILURE] Error processing {file_path.name}: {e}")
        # Still add some minimal metadata in case of failure
        try:
            metadata = {
                "filename": file_path.name,
                "error": str(e),
                "source_path": str(file_path.resolve()),
                "success": False
            }
            (OUTPUT_DIR / f"{file_path.stem}_metadata.json").write_text(json.dumps(metadata, indent=2))
            master_metadata.append(metadata)
        except:
            pass

# --- Main Execution Pipeline ---
def run_multi_pass_pipeline(input_path=None):
    global neo4j_connector

    # Initialize Neo4j connection if enabled
    if ENABLE_NEO4J:
        try:
            logger.info("[Neo4j] Initializing connection...")
            neo4j_connector = create_neo4j_connector()
            if neo4j_connector:
                neo4j_connector.connect()
                logger.info("[Neo4j] Connected successfully")
        except Exception as e:
            logger.error(f"[Neo4j] Connection failed: {e}")
            logger.warning("[Neo4j] Continuing without Neo4j integration")
            neo4j_connector = None

    # Use provided input path or default to INPUT_PATH
    source_path = Path(input_path) if input_path else INPUT_PATH

    if source_path.is_file():
        files = [source_path]
    else:
        files = sorted([f for f in source_path.iterdir() if f.suffix.lower() in SUPPORTED_EXTENSIONS])

    logger.info(f"Processing {len(files)} files with settings:")
    logger.info(f"  - Quality Assurance: {'Enabled' if ENABLE_QA else 'Disabled'}")
    logger.info(f"  - Neo4j Export: {'Enabled' if ENABLE_NEO4J else 'Disabled'}")
    logger.info(f"  - Parallel Processing: {'Enabled' if ENABLE_PARALLELISM else 'Disabled'}")

    if ENABLE_PARALLELISM:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(process_corpus_file, f): f.name for f in files}
            for future in tqdm(as_completed(futures), total=len(futures), desc="Processing Files"):
                future.result()
    else:
        for file_path in tqdm(files, desc="Processing Files"):
            process_corpus_file(file_path)

    # Save metadata index
    (OUTPUT_DIR / "metadata_index.json").write_text(json.dumps(master_metadata, indent=2))

    # Print statistics
    print("\n" + "=" * 60)
    print("[✓] Knowledge extraction complete!")
    print("=" * 60)

    # LLM Provider Statistics
    try:
        llm_stats = get_provider_stats()
        print(f"\n📊 LLM Usage Statistics:")
        print(f"  - Total Requests: {llm_stats.get('total_requests', 0)}")
        print(f"  - Total Cost: ${llm_stats.get('total_cost', 0):.2f}")
        print(f"  - Avg Cost/Request: ${llm_stats.get('avg_cost_per_request', 0):.4f}")
    except Exception as e:
        logger.debug(f"Could not retrieve LLM stats: {e}")

    # Quality Statistics
    if ENABLE_QA:
        successful_docs = [m for m in master_metadata if m.get("success")]
        if successful_docs:
            avg_quality = sum(m.get("quality", {}).get("overall_quality_score", 0) for m in successful_docs) / len(successful_docs)
            print(f"\n✅ Quality Assurance:")
            print(f"  - Average Quality Score: {avg_quality:.3f}")
            print(f"  - Confidence Threshold: {QA_MIN_CONFIDENCE}")

    # Neo4j Statistics
    if ENABLE_NEO4J and neo4j_connector:
        try:
            schema_info = neo4j_connector.validate_graph_schema()
            print(f"\n🔗 Neo4j Graph Database:")
            print(f"  - Total Nodes: {schema_info.get('node_count', 0)}")
            print(f"  - Total Relationships: {schema_info.get('relationship_count', 0)}")
        except Exception as e:
            logger.debug(f"Could not retrieve Neo4j stats: {e}")

    print(f"\n📁 Outputs saved to: {OUTPUT_DIR.absolute()}")
    print("=" * 60)

    logger.info("[✓] Pipeline execution complete.")

    # Clean up Neo4j connection
    if neo4j_connector:
        try:
            neo4j_connector.close()
        except Exception as e:
            logger.debug(f"Error closing Neo4j connection: {e}")

# --- Entrypoint ---
if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Multi-Pass Knowledge Extraction Pipeline")
    parser.add_argument("input_path", nargs="?", help="Path to input file or directory")
    parser.add_argument("--input", "-i", help="Path to input file or directory")
    args = parser.parse_args()
    
    # Use either positional argument or --input flag
    input_path = args.input_path if args.input_path else args.input
    run_multi_pass_pipeline(input_path)
