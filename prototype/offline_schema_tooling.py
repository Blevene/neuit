#!/usr/bin/env python
"""Offline Schema Induction Tooling

This script walks a directory, reads supported document types, aggregates the text,
and then invokes the existing LLM‑powered helpers to generate:
    • Ontology
    • Label suggestions
    • Symbolic rules

Supported file extensions: .txt, .md, .json, .docx, .pdf

Usage
-----
$ python prototype/offline_schema_tooling.py /path/to/corpus --max-files 100 --top-n 15

Dependencies (optional)
-----------------------
- python-docx   → `pip install python-docx`
- PyPDF2        → `pip install PyPDF2`

Environment
-----------
Requires OPENAI_API_KEY to be set, as per the online tooling.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path
from typing import List
from io import BytesIO

# Optional imports for DOCX / PDF extraction
try:
    import docx  # type: ignore
except ImportError:
    docx = None

try:
    import PyPDF2  # type: ignore
except ImportError:
    PyPDF2 = None

from schema_induction_tooling import (
    generate_ontology,
    suggest_labels_from_corpus,
    induce_rules_from_corpus,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# Directory where outputs are persisted
OUTPUT_DIR = Path("data/corpus/dev")

SUPPORTED_EXTS = {".txt", ".md", ".json", ".docx", ".pdf"}


def extract_text(path: Path) -> str:
    """Extract raw text from supported document types."""
    ext = path.suffix.lower()
    try:
        if ext in {".txt", ".md"}:
            return path.read_text(encoding="utf-8", errors="ignore")
        if ext == ".json":
            with path.open(encoding="utf-8", errors="ignore") as fp:
                try:
                    data = json.load(fp)
                except json.JSONDecodeError:
                    fp.seek(0)
                    return fp.read()
            return json.dumps(data, indent=2)
        if ext == ".docx":
            if docx is None:
                logging.warning("Skipping %s (python-docx not installed)", path)
                return ""
            document = docx.Document(str(path))
            return "\n".join(p.text for p in document.paragraphs)
        if ext == ".pdf":
            if PyPDF2 is None:
                logging.warning("Skipping %s (PyPDF2 not installed)", path)
                return ""
            reader = PyPDF2.PdfReader(str(path))
            pages = []
            for page in reader.pages:
                try:
                    pages.append(page.extract_text() or "")
                except Exception:  # noqa: BLE001
                    continue
            return "\n".join(pages)
    except Exception as exc:  # noqa: BLE001
        logging.error("Failed to read %s: %s", path, exc)
    return ""


def build_corpus(root: Path, max_files: int | None = None) -> str:
    """Walk *root* recursively and concatenate text from supported files."""
    texts: List[str] = []
    count = 0
    for file_path in root.rglob("*"):
        if not file_path.is_file() or file_path.suffix.lower() not in SUPPORTED_EXTS:
            continue
        texts.append(extract_text(file_path))
        count += 1
        if max_files and count >= max_files:
            break
    logging.info("Loaded %d documents totaling ~%d characters", count, sum(len(t) for t in texts))
    return "\n\n".join(texts)


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline schema induction over a folder of documents.")
    parser.add_argument("folder", type=Path, help="Path to folder containing corpus files")
    parser.add_argument("--max-files", type=int, default=None, help="Limit number of files scanned")
    parser.add_argument("--top-n-labels", type=int, default=10, help="Top N concepts for label suggestion")
    args = parser.parse_args()

    if not args.folder.exists():
        parser.error(f"Folder {args.folder} does not exist")

    corpus = build_corpus(args.folder, args.max_files)
    if not corpus.strip():
        logging.error("No text extracted from the provided folder.")
        return

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Ontology
    logging.info("Generating ontology …")
    ontology = generate_ontology(corpus)
    print("\n=== ONTOLOGY ===\n")
    print(ontology)
    
    # Write ontology immediately
    logging.info("Writing ontology output to %s", OUTPUT_DIR / "ontology.txt")
    (OUTPUT_DIR / "ontology.txt").write_text(ontology, encoding="utf-8")

    # 2. Labels
    logging.info("Generating label suggestions …")
    labels = suggest_labels_from_corpus(corpus, top_n=args.top_n_labels)
    print("\n=== LABEL SUGGESTIONS ===\n")
    print(labels)
    
    # Write labels immediately
    logging.info("Writing label suggestions to %s", OUTPUT_DIR)
    try:
        # Try to parse and pretty-print the JSON for better readability
        labels_data = json.loads(labels)
        (OUTPUT_DIR / "label_suggestions.json").write_text(
            json.dumps(labels_data, indent=2), encoding="utf-8"
        )
        logging.info("Saved formatted JSON to label_suggestions.json")
        # Keep the text version for backward compatibility
        (OUTPUT_DIR / "label_suggestions.txt").write_text(labels, encoding="utf-8")
    except json.JSONDecodeError:
        # Fallback to text if not valid JSON
        logging.warning("Could not parse labels as JSON, saving as plain text")
        (OUTPUT_DIR / "label_suggestions.txt").write_text(labels, encoding="utf-8")

    # 3. Rules
    logging.info("Generating symbolic rules …")
    rules = induce_rules_from_corpus(corpus)
    print("\n=== RULES ===\n")
    print(rules)
    
    # Write rules immediately
    logging.info("Writing rules to %s", OUTPUT_DIR / "rules.txt")
    (OUTPUT_DIR / "rules.txt").write_text(rules, encoding="utf-8")
    
    logging.info("All outputs successfully written to %s", OUTPUT_DIR)


if __name__ == "__main__":
    main() 