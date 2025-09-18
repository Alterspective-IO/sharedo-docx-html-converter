"""
Changelog route for the DOCX to HTML Converter
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from pathlib import Path
import markdown

router = APIRouter()

@router.get("/changelog", response_class=HTMLResponse)
async def get_changelog():
    """
    Display the changelog in a formatted HTML page
    """
    # Read the changelog file
    changelog_path = Path(__file__).parent.parent / "CHANGELOG.md"
    
    if not changelog_path.exists():
        return HTMLResponse(content="<h1>Changelog not found</h1>", status_code=404)
    
    # Read and convert markdown to HTML
    with open(changelog_path, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    # Convert markdown to HTML with extensions
    html_content = markdown.markdown(
        markdown_content,
        extensions=['extra', 'codehilite', 'toc', 'tables']
    )
    
    # Create full HTML page with Alterspective styling
    full_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Changelog - Alterspective DOCX to HTML Converter</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
        <link href="/static/css/alterspective.css" rel="stylesheet">
        <style>
            body {{
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }}
            .changelog-container {{
                max-width: 1000px;
                margin: 2rem auto;
                padding: 2rem;
                background: rgba(255, 255, 255, 0.95);
                border-radius: 16px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            }}
            .navbar {{
                background: var(--navy) !important;
            }}
            h1 {{
                color: var(--navy);
                border-bottom: 3px solid var(--citrus);
                padding-bottom: 1rem;
                margin-bottom: 2rem;
            }}
            h2 {{
                color: var(--marine);
                margin-top: 2rem;
                margin-bottom: 1rem;
            }}
            h3 {{
                color: var(--green);
                margin-top: 1.5rem;
                margin-bottom: 0.75rem;
            }}
            h4 {{
                color: var(--navy);
                margin-top: 1rem;
                margin-bottom: 0.5rem;
            }}
            ul {{
                margin-bottom: 1rem;
            }}
            li {{
                margin-bottom: 0.5rem;
            }}
            code {{
                background: rgba(0, 0, 0, 0.05);
                padding: 2px 6px;
                border-radius: 4px;
                font-size: 0.9em;
            }}
            pre {{
                background: #f8f9fa;
                padding: 1rem;
                border-radius: 8px;
                overflow-x: auto;
            }}
            .back-button {{
                display: inline-block;
                margin-bottom: 2rem;
                padding: 0.5rem 1.5rem;
                background: var(--marine);
                color: white;
                text-decoration: none;
                border-radius: 8px;
                transition: all 0.3s ease;
            }}
            .back-button:hover {{
                background: var(--green);
                color: white;
                transform: translateX(-5px);
            }}
            hr {{
                margin: 2rem 0;
                border-color: rgba(0, 0, 0, 0.1);
            }}
            table {{
                width: 100%;
                margin: 1rem 0;
                border-collapse: collapse;
            }}
            th, td {{
                padding: 0.75rem;
                border: 1px solid #dee2e6;
            }}
            th {{
                background: var(--navy);
                color: white;
            }}
            tr:nth-child(even) {{
                background: #f8f9fa;
            }}
        </style>
    </head>
    <body>
        <!-- Navigation -->
        <nav class="navbar navbar-expand-lg navbar-dark">
            <div class="container">
                <a class="navbar-brand" href="/">
                    <img src="/static/images/Alterspective_Logo_reversed_FA.png" alt="Alterspective" height="40">
                    <span>DOCX Converter</span>
                </a>
                <div class="navbar-nav ms-auto">
                    <a class="nav-link" href="/"><i class="fas fa-home"></i> Home</a>
                    <a class="nav-link" href="/docs"><i class="fas fa-book"></i> API Docs</a>
                    <a class="nav-link" href="https://github.com/Alterspective-io/sharedo-docx-converter">
                        <i class="fab fa-github"></i> GitHub
                    </a>
                </div>
            </div>
        </nav>
        
        <div class="changelog-container">
            <a href="/" class="back-button">
                <i class="fas fa-arrow-left"></i> Back to Home
            </a>
            {html_content}
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=full_html)