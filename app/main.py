from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import os
from .converter import convert_docx_to_html

app = FastAPI(title="Kenhub DOCX to HTML Converter")

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main page"""
    with open("static/index.html", "r") as f:
        return f.read()

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok"}

@app.post("/api/convert")
async def convert_docx(file: UploadFile = File(...)):
    """Convert DOCX file to Kenhub admin HTML"""
    if not file.filename.lower().endswith('.docx'):
        raise HTTPException(status_code=400, detail="File must be a DOCX document")
    
    try:
        # Read file content
        content = await file.read()
        
        # Convert to HTML
        result = convert_docx_to_html(content)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conversion failed: {str(e)}")