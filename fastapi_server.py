from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import subprocess
from pathlib import Path
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath('.'))

# Import the analyzer
from src.integrations.metro.analyzer import analyze_property

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Create necessary directories
Path("templates").mkdir(exist_ok=True)
Path("static").mkdir(exist_ok=True)

# Create a simple template
with open("templates/index.html", "w") as f:
    f.write("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Nashville Zoning AI</title>
        <style>
            body {
                font-family: 'Times New Roman', Times, serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }
            iframe {
                width: 100%;
                height: 800px;
                border: 1px solid #ccc;
            }
        </style>
    </head>
    <body>
        <h1>Nashville Zoning AI</h1>
        <p>The Streamlit app should be embedded below. If you don't see it, try refreshing the page.</p>
        <iframe src="http://localhost:8051" frameborder="0"></iframe>
    </body>
    </html>
    """)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/analyze")
async def analyze_property_endpoint(request: dict):
    try:
        address = request.get("address")
        if not address:
            raise HTTPException(status_code=400, detail="Address is required")
            
        # Call the analyzer
        result = analyze_property(address)
        
        # Add any additional processing here if needed
        return JSONResponse(content=result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def start_streamlit():
    subprocess.Popen(["streamlit", "run", "ui_streamlit.py", "--server.port=8051", "--server.headless=true"])

if __name__ == "__main__":
    # Start Streamlit in the background
    start_streamlit()
    # Start FastAPI server on port 8001 to avoid conflicts
    uvicorn.run(app, host="127.0.0.1", port=8001)
