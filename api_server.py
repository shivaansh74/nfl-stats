from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any
import sys
import io
import os
from contextlib import redirect_stdout

# Import our CLI logic
from nfl_stats.main import process_query

app = FastAPI(title="NFL Stats API", version="1.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from nfl_stats.utils import console

class QueryRequest(BaseModel):
    query: str
    
class QueryResponse(BaseModel):
    query: str
    success: bool
    output: str
    html_output: Optional[str] = None
    error: Optional[str] = None
    animation_path: Optional[str] = None
    is_longest_play: bool = False
    data: Optional[Dict[str, Any]] = None

@app.get("/")
async def root():
    return {
        "message": "NFL Stats API",
        "version": "1.0.0",
        "endpoints": {
            "POST /api/query": "Process natural language NFL stats query",
            "GET /api/health": "Health check"
        }
    }

@app.get("/api/health")
async def health():
    return {"status": "healthy"}

@app.post("/api/query", response_model=QueryResponse)
async def query_stats(request: QueryRequest):
    """
    Process a natural language NFL stats query.
    
    Examples:
    - "mahomes vs allen 2024"
    - "tom brady patriots playoffs"
    - "lamar jackson rookie year"
    """
    try:
        # Clear previous capture
        console.clear()
        console.export_text(clear=True) 
        
        # Check if this is a longest play query
        is_longest = any(word in request.query.lower() for word in ['longest', 'biggest', 'furthest'])
        
        # Process the query using our CLI logic
        import glob
        import os
        import time
        
        # Get the directory where animations are saved (project root)
        project_root = os.path.dirname(os.path.abspath(__file__))
        animation_pattern = os.path.join(project_root, "play_animation_*.gif")
        
        # Get list of existing animation files before query
        before_files = set(glob.glob(animation_pattern))
        before_time = time.time()
        
        result_data = process_query(request.query, use_spinner=False)
        
        # Get list of animation files after query
        after_files = set(glob.glob(animation_pattern))
        
        # Find new animation file (created after query started)
        new_files = []
        for file in after_files:
            if file not in before_files:
                # Check if file was created recently (within last 30 seconds)
                if os.path.getmtime(file) > before_time:
                    new_files.append(os.path.basename(file))
        
        animation_path = new_files[0] if new_files else None
        
        # Get the captured output as HTML
        html_output = console.export_html(
            inline_styles=True, 
            clear=False,
            code_format="<pre style=\"font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace\">{code}</pre>"
        )
        text_output = console.export_text(clear=True)
        
        return QueryResponse(
            query=request.query,
            success=True,
            output=text_output,
            html_output=html_output,
            animation_path=animation_path,
            is_longest_play=is_longest,
            data=result_data
        )
    
    except Exception as e:
        return QueryResponse(
            query=request.query,
            success=False,
            output="",
            error=str(e),
            is_longest_play=False
        )

@app.get("/api/examples")
async def get_examples():
    """Return example queries for the frontend."""
    return {
        "examples": [
            {
                "category": "Comparisons",
                "queries": [
                    "patrick mahomes vs josh allen 2024",
                    "lamar jackson vs joe burrow 2023",
                    "derrick henry vs saquon barkley"
                ]
            },
            {
                "category": "Player Stats",
                "queries": [
                    "josh allen 2024",
                    "tom brady patriots",
                    "lamar jackson rookie year"
                ]
            },
            {
                "category": "Longest Plays",
                "queries": [
                    "longest catch by justin jefferson",
                    "longest run by saquon barkley",
                    "longest pass by patrick mahomes"
                ]
            },
            {
                "category": "Playoffs",
                "queries": [
                    "patrick mahomes playoffs",
                    "tom brady super bowl",
                    "lamar jackson playoffs bills"
                ]
            },
            {
                "category": "News",
                "queries": [
                    "joe burrow injuries",
                    "travis kelce news"
                ]
            }
        ]
    }

@app.get("/api/animation/{filename}")
async def get_animation(filename: str):
    """Serve animation GIF files."""
    file_path = os.path.join(os.getcwd(), filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Animation not found")
    
    if not filename.endswith('.gif'):
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    return FileResponse(file_path, media_type="image/gif")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
