#!/usr/bin/env python3
"""
Startup script for Nashville Zoning AI Assistant
Handles initial setup and starts the FastAPI server
"""

import os
import sys
import subprocess
from pathlib import Path

def check_ollama():
    """Check if Ollama is running and has required models"""
    print("🔍 Checking Ollama setup...")
    
    try:
        # Check if ollama is running
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Ollama is not running. Please start it with: ollama serve")
            return False
        
        models = result.stdout
        required_models = ["llama3.1:8b", "nomic-embed-text"]
        
        for model in required_models:
            if model not in models:
                print(f"📥 Pulling required model: {model}")
                subprocess.run(["ollama", "pull", model], check=True)
        
        print("✅ Ollama setup complete")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error with Ollama: {e}")
        return False
    except FileNotFoundError:
        print("❌ Ollama not found. Please install Ollama first.")
        return False

def check_documents():
    """Check if Nashville Zoning Code PDF is present"""
    print("🔍 Checking documents...")
    
    pdf_path = Path("data/zoning_pdfs/nashville_zoning_code_2025.pdf")
    if not pdf_path.exists():
        print("⚠️  Nashville Zoning Code PDF not found at data/zoning_pdfs/")
        print("   Please ensure the PDF is in the correct location")
        return False
    
    print("✅ Documents found")
    return True

def check_dependencies():
    """Check if required Python packages are installed"""
    print("🔍 Checking dependencies...")
    
    try:
        import fastapi
        import uvicorn
        import langchain
        import chromadb
        import requests
        print("✅ Dependencies installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("   Run: pip install -r requirements.txt")
        return False

def start_server():
    """Start the FastAPI server"""
    print("🚀 Starting Nashville Zoning AI Assistant...")
    print("   API will be available at: http://localhost:8000")
    print("   Interactive docs at: http://localhost:8000/docs")
    print("   Press Ctrl+C to stop")
    print("-" * 50)
    
    try:
        subprocess.run([
            "uvicorn", "app.api:app", 
            "--reload", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ])
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

def main():
    """Main startup sequence"""
    print("🏢 Nashville Zoning AI Assistant")
    print("=" * 40)
    
    # Check all prerequisites
    if not check_dependencies():
        sys.exit(1)
    
    if not check_ollama():
        sys.exit(1)
    
    if not check_documents():
        print("⚠️  Continuing without documents - some features may not work")
    
    # Start the server
    start_server()

if __name__ == "__main__":
    main()
