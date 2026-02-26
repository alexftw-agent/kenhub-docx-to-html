from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, Response
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
import os
from .converter import convert_docx_to_html

app = FastAPI(title="Kenhub DOCX to HTML Converter")
security = HTTPBasic()

AUTH_USER = os.getenv("BASIC_AUTH_USER", "kenhub")
AUTH_PASS = os.getenv("BASIC_AUTH_PASS", "orkSsB5l1m6rxKn")

def verify_auth(credentials: HTTPBasicCredentials = Depends(security)):
    correct_user = secrets.compare_digest(credentials.username.encode(), AUTH_USER.encode())
    correct_pass = secrets.compare_digest(credentials.password.encode(), AUTH_PASS.encode())
    if not (correct_user and correct_pass):
        raise HTTPException(status_code=401, detail="Unauthorized", headers={"WWW-Authenticate": "Basic"})
    return credentials

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def root(credentials: HTTPBasicCredentials = Depends(verify_auth)):
    """Serve the main page"""
    with open("static/index.html", "r") as f:
        return f.read()

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok"}

@app.post("/api/convert")
async def convert_docx(file: UploadFile = File(...), credentials: HTTPBasicCredentials = Depends(verify_auth)):
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