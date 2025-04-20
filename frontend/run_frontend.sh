#!/bin/bash
echo "Generating metadata index..."
cd "$(dirname "$0")"
python generate_metadata_index.py

echo "Starting NEUIToolkit Streamlit Frontend..."
streamlit run app.py 