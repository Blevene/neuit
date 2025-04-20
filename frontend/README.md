# NEUIToolkit Frontend

A Streamlit-based visualization frontend for the NEUIToolkit knowledge extraction system.

## Features

- View metadata summary for all processed documents
- Visualize entities, relationships, rules, and justifications
- Interactive knowledge graph visualization
- Ontology visualization in graph format

## Installation

1. Install the required Python packages:

```bash
pip install -r requirements.txt
```

## Running the Frontend

To start the Streamlit application:

```bash
streamlit run app.py
```

This will start the Streamlit server, and the application will be available at `http://localhost:8501`.

## Usage

1. Make sure you have run the knowledge extraction pipeline in the backend first to generate the output files
2. Launch the Streamlit application
3. Use the sidebar to select a document to visualize
4. Navigate through the tabs to explore different aspects of the extracted knowledge

## Directory Structure

```
frontend/
├── app.py               # Main Streamlit application
├── requirements.txt     # Python dependencies
└── README.md            # This file
```

## Notes

- The application looks for output files in the `../outputs/` directory
- The application requires that `metadata_index.json` exists in the outputs directory
- Each document should have separate JSON files for entities, relationships, rules, and justifications 