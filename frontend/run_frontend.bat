@echo off
echo Generating metadata index...
cd %~dp0
python generate_metadata_index.py

echo Starting NEUIToolkit Streamlit Frontend...
streamlit run app.py
pause 