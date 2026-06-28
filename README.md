# Load Planner

A web-based cargo load planning tool for heavy-haul logistics. Upload a cargo manifest, and the system recommends the optimal trailer configuration — including standard flatbeds, low-loaders, tri-axle variants, superlinks (articulated front+rear), and abnormal-load trailers — with 3D visualization and a downloadable load plan report.

## Features

- **CSV/Excel upload** — Upload cargo manifests; auto-detects column names (description, dimensions, mass) and unit systems (m, cm, in, mm; kg/ton auto-detect)
- **Quantity expansion** — Rows with a `Qty` / `Quantity` / `Units` column are automatically expanded into multiple items
- **Row-based greedy packer** — Places items on the trailer deck, sorted by mass then area, trying both orientations
- **Smart Recommend** — Tries every trailer type (smallest to largest) for a single-trailer fit; if none works, falls back to a multi-trailer greedy approach that minimizes the number of trailers needed
- **Trailer library** — South African specification trailers with legal payload, axle limits, and dimensions
- **Per-trailer breakdown** — View every trailer's items, positions, weight utilization, axle loads, and compliance status
- **3D visualization** — Browse trailers individually or see the combined fleet view with Three.js
- **Downloadable report** — Plain-text export of the complete load plan for sharing with transport vendors

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, FastAPI, uvicorn |
| Data processing | pandas, openpyxl |
| Frontend | Vanilla HTML/JS, Three.js (3D viewer), OrbitControls |
| Validation | Pydantic |

## Project Structure

```
app/
  __init__.py
  main.py               # FastAPI app, API endpoints
  models.py             # Pydantic request models
  parser.py             # CSV/Excel parser with column auto-detection
  packer_engine.py      # Row-based greedy floor packer
  planner.py            # Single-trailer, Superlink, and multi-trailer recommendation engine
  trailer_library.py    # SA-spec trailer definitions + Superlink class
static/
  index.html            # Single-page frontend
data/
  BARTRAC_HS_CLASSIFICATIONS.json  # HS code reference data
run.py                  # Dev server entry point
requirements.txt
```

## Quick Start

### 1. Create a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Run the server

```powershell
python run.py
```

The app is available at `http://localhost:8000`.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Serve the frontend |
| GET | `/api/trailers` | List available trailer types |
| POST | `/api/upload-preview` | Upload & parse a cargo file (CSV/XLSX) |
| POST | `/api/plan` | Generate a load plan for a specific trailer |
| POST | `/api/recommend` | Auto-recommend the best trailer configuration |

### `/api/recommend` — example response structure

```json
{
  "recommendation": "3 trailers: 1x Flatbed Standard + 2x Low-Loader",
  "trailer_count": 3,
  "trailers": [
    {
      "type": "Flatbed Standard",
      "plan": {
        "trailer_name": "Flatbed Standard",
        "is_safe": true,
        "total_mass_tons": 12.5,
        "max_payload_tons": 28,
        "utilization_percent": 44.6,
        "rear_trailer": {
          "section": "Deck",
          "items_placed": 6,
          "placements": [
            {
              "item_id": "ROW_2",
              "description": "DE88GC",
              "length_m": 2.3,
              "width_m": 1.12,
              "height_m": 1.62,
              "mass_kg": 1358,
              "x_m": 0.0,
              "y_m": 0.0,
              "rotated": false
            }
          ]
        },
        "axle_report": { "front_axle_load_tons": 3.75, "rear_axle_group_load_tons": 8.75, "center_of_gravity_m": 5.2, "is_legal": true },
        "visualization": { "container_length_m": 13.6, "container_width_m": 2.4, "deck_height_m": 1.2, "items": [...] }
      }
    }
  ],
  "is_safe": true,
  "total_mass_tons": 97.54,
  "utilization_percent": 63.2,
  "unplaced_items": [],
  "combined_visualization": { "container_length_m": 40.8, "container_width_m": 2.4, "deck_height_m": 1.2, "items": [...] }
}
```

## CSV Format

The parser auto-detects columns by name. A typical cargo file:

```csv
CUST_ORDER,DESC,LENGTH,WIDTH,HEIGHT,MASS,CUBE
CUST3073,DE88GC,2.30,1.12,1.62,1.358,4.173
CUST3074,DE88GC,2.30,1.12,1.62,1.358,4.173
```

Supported column names:
- **Description**: `desc`, `description`, `item`, `name`, `product`, `code`, `model`
- **Length**: `length`, `l`, `len`
- **Width**: `width`, `w`, `breadth`
- **Height**: `height`, `h`, `depth`
- **Mass**: `mass`, `weight`, `kg`, `ton`, `tons`
- **Quantity** (optional): `qty`, `quantity`, `units`, `pieces`, `count`

Mass values are auto-detected as tons (0.1–100 range) or kilograms and converted to kg internally. Dimensions can be uploaded in cm, in, mm, or m.

## Trailer Library

| Trailer | Length | Width | Payload | Notes |
|---------|--------|-------|---------|-------|
| Flatbed Standard | 13.6m | 2.4m | 28t | Standard tandem-axle flatbed |
| Low-Loader | 13.6m | 2.8m | 35t | Lower deck, wider |
| Tri-Axle Flatbed | 13.6m | 2.4m | 30t | 3 rear axles, 27t group limit |
| Tri-Axle Low-Loader | 13.6m | 2.8m | 35t | Low deck + tri-axle |
| Superlink (6m + 6m) | 12m | 2.4m | 34t | Articulated front+rear |
| Superlink (6m + 12m) | 18m | 2.4m | 34t | Articulated front+rear |
| Tri-Axle Superlink | 18m | 2.4m | 34t | Superlink with tri-axle rear |
| Interlink (6m + 6m) | 12m | 2.4m | 34t | High-density configuration |
| Abnormal (Extendable) | 18m | 3.0m | 50t | Requires permit |
| Super-Abnormal | 24m | 3.5m | 80t | Requires escort vehicles |

## Packing Algorithm

The `pack_floor_bin` function uses a **greedy row-based (shelf) approach**:

1. Items are sorted by mass descending, then by floor area descending (heaviest/largest first)
2. Items are placed lengthwise along the trailer, forming rows
3. When a row is full, a new row starts above it
4. Each item tries both orientations; the longer side is preferred along the trailer length
5. Items that don't fit on the floor are reported as unplaced

This is a 2D floor packer — stacking is not currently supported.
