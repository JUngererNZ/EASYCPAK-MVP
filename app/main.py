from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import os
import json

from app.parser import parse_upload_file
from app.planner import plan_single_trailer, plan_superlink, recommend_trailers
from app.models import PlanRequest, CargoItemInput
from app.packer_engine import CargoItem
from app.trailer_library import TRAILER_TYPES, get_trailer, SuperlinkTrailer

app = FastAPI()

# Allow frontend to access API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def get_root():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/trailers")
async def list_trailers():
    return {"trailers": list(TRAILER_TYPES.keys())}

@app.post("/api/upload-preview")
async def upload_preview(
    file: UploadFile = File(...), 
    units: str = Form("m"),
    mass_unit: str = Form("kg")
):
    contents = await file.read()
    result = parse_upload_file(contents, file.filename, units, mass_unit)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@app.post("/api/plan")
async def generate_plan(request: PlanRequest):
    # Convert Pydantic models to CargoItem dataclass
    cargo_items = []
    for item in request.items:
        cargo_items.append(CargoItem(
            id=item.id,
            description=item.description,
            length_m=item.length_m,
            width_m=item.width_m,
            height_m=item.height_m,
            mass_kg=item.mass_kg,
            can_rotate=item.can_rotate
        ))
    
    trailer_name = request.trailer_name
    config = get_trailer(trailer_name)
    
    # Check if it's a Superlink
    is_superlink = False
    if hasattr(config, 'is_link') and config.is_link:
        is_superlink = True
    elif isinstance(config, dict) and config.get('is_link'):
        is_superlink = True
    
    if is_superlink:
        result = plan_superlink(trailer_name, cargo_items)
    else:
        result = plan_single_trailer(trailer_name, cargo_items)
    
    return result

@app.post("/api/recommend")
async def auto_recommend(request: PlanRequest):
    """
    Automatically suggests the best trailer configuration
    """
    # Convert Pydantic models to CargoItem dataclass
    cargo_items = []
    for item in request.items:
        cargo_items.append(CargoItem(
            id=item.id,
            description=item.description,
            length_m=item.length_m,
            width_m=item.width_m,
            height_m=item.height_m,
            mass_kg=item.mass_kg,
            can_rotate=item.can_rotate
        ))
    
    # Call the recommendation engine
    result = recommend_trailers(cargo_items)
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)