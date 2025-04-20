#!/usr/bin/env python
# Run the Schema Induction Streamlit App

import os
import subprocess
import sys

def main():
    """Run the Schema Induction Streamlit app."""
    print("Starting Schema Induction UI...")
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        if os.path.exists('.env.example'):
            print("No .env file found. Creating from .env.example...")
            with open('.env.example', 'r') as example_file:
                with open('.env', 'w') as env_file:
                    env_file.write(example_file.read())
            print("Created .env file. Please edit it to add your OpenAI API key.")
        else:
            print("Warning: No .env or .env.example file found.")
            with open('.env', 'w') as env_file:
                env_file.write("OPENAI_API_KEY=your_openai_api_key_here")
            print("Created .env file. Please edit it to add your OpenAI API key.")
    
    # Run the Streamlit app
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "prototype/prototype_frontend.py",
            "--browser.serverAddress", "localhost",
            "--server.port", "8501"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running Streamlit: {e}")
    except KeyboardInterrupt:
        print("\nApplication stopped.")

if __name__ == "__main__":
    main() 