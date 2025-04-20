# Multi-Pass Knowledge Extraction Controller
# Organized for clarity, robustness, and support for parallel processing and smart MIME-type detection

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
from llm.llm_utils import call_llm_with_prompt
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

        entities = run_entity_pass(corpus)
        relationships = run_relationship_pass(entities, corpus)
        rules = run_rule_pass(corpus)
        ontology = run_ontology_pass(corpus)
        justifications = run_justification_pass(rules, corpus)

        def save_json(obj, suffix):
            try:
                (OUTPUT_DIR / f"{base_name}_{suffix}.json").write_text(json.dumps(obj, indent=2))
                return True
            except Exception as e:
                logger.error(f"Error saving {suffix} JSON: {e}")
                return False

        # Save all outputs, even if some fail
        save_json(entities, "entities")
        save_json(relationships, "relationships")
        save_json(rules, "rules")
        save_json(justifications, "justifications")
        
        try:
            (OUTPUT_DIR / f"{base_name}_ontology.ttl").write_text(ontology)
            ontology_lines = len(ontology.strip().splitlines())
        except Exception as e:
            logger.error(f"Error saving ontology: {e}")
            ontology_lines = 0

        metadata = {
            "filename": file_path.name,
            "num_entities": len(entities),
            "num_relationships": len(relationships),
            "num_rules": len(rules),
            "num_justifications": len(justifications),
            "ontology_lines": ontology_lines,
            "source_path": str(file_path.resolve())
        }
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
    # Use provided input path or default to INPUT_PATH
    source_path = Path(input_path) if input_path else INPUT_PATH
    
    if source_path.is_file():
        files = [source_path]
    else:
        files = sorted([f for f in source_path.iterdir() if f.suffix.lower() in SUPPORTED_EXTENSIONS])

    if ENABLE_PARALLELISM:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(process_corpus_file, f): f.name for f in files}
            for future in tqdm(as_completed(futures), total=len(futures), desc="Processing Files"):
                future.result()
    else:
        for file_path in tqdm(files, desc="Processing Files"):
            process_corpus_file(file_path)

    (OUTPUT_DIR / "metadata_index.json").write_text(json.dumps(master_metadata, indent=2))
    logger.info("[✓] Knowledge extraction complete. See outputs/")
    print("[✓] Knowledge extraction complete. See outputs/")

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
