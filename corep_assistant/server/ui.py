"""UI routes for serving frontend"""
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from .api import app

# Setup templates
TEMPLATE_DIR = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve main UI page"""
    return templates.TemplateResponse("index.html", {"request": request})
