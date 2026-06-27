import pandas as pd
import io

def parse_upload_file(file_bytes: bytes, filename: str, unit_system: str = "cm"):
    """
    Reads Excel/CSV, maps columns (including CUBE), normalizes units.
    Supports: cm, in, mm
    """
    try:
        if filename.lower().endswith('.csv'):
            df = pd.read_csv(io.BytesIO(file_bytes))
        else:
            df = pd.read_excel(io.BytesIO(file_bytes))
    except Exception as e:
        return {"error": f"Failed to read file: {str(e)}"}

    # Column mapping heuristics
    col_map = {}
    for col in df.columns:
        c = col.lower().strip()
        if 'length' in c or c == 'l':
            col_map['length'] = col
        elif 'width' in c or c == 'w' or 'breadth' in c:
            col_map['width'] = col
        elif 'height' in c or c == 'h' or 'depth' in c:
            col_map['height'] = col
        elif 'weight' in c or 'mass' in c or 'kg' in c:
            col_map['mass'] = col
        elif 'description' in c or 'item' in c or 'name' in c or 'cube' in c or 'product' in c or 'code' in c:
            col_map['description'] = col

    # Unit factor: convert to meters
    if unit_system == "cm":
        factor = 0.01
    elif unit_system == "in":
        factor = 0.0254
    elif unit_system == "mm":
        factor = 0.001
    else:
        factor = 0.01  # default to cm

    items = []
    errors = []
    
    for idx, row in df.iterrows():
        try:
            l = float(row.get(col_map.get('length', 0))) if col_map.get('length') in row else 0.0
            w = float(row.get(col_map.get('width', 0))) if col_map.get('width') in row else 0.0
            h = float(row.get(col_map.get('height', 0))) if col_map.get('height') in row else 0.0
            mass = float(row.get(col_map.get('mass', 0))) if col_map.get('mass') in row else 0.0
            desc = str(row.get(col_map.get('description', ''), f"Item {idx+2}")) if col_map.get('description') in row else f"Item {idx+2}"
            
            # Normalize to meters
            l_m = round(l * factor, 3)
            w_m = round(w * factor, 3)
            h_m = round(h * factor, 3)
            
            is_dirty = (l_m == 0 or w_m == 0 or h_m == 0 or mass == 0)
            dirty_fields = []
            if l_m == 0: dirty_fields.append("length")
            if w_m == 0: dirty_fields.append("width")
            if h_m == 0: dirty_fields.append("height")
            if mass == 0: dirty_fields.append("mass")
            
            suggested_mass = None
            if mass == 0 and l_m > 0 and w_m > 0 and h_m > 0:
                suggested_mass = round(l_m * w_m * h_m * 500, 2)
            
            items.append({
                "row_index": idx + 2,
                "id": f"ROW_{idx+2}",
                "description": desc,
                "length_m": l_m,
                "width_m": w_m,
                "height_m": h_m,
                "mass_kg": mass,
                "is_dirty": is_dirty,
                "dirty_fields": dirty_fields,
                "suggested_mass": suggested_mass
            })
        except Exception as e:
            errors.append(f"Row {idx+2}: Parse error - {str(e)}")

    return {
        "status": "success",
        "detected_columns": col_map,
        "unit_system": unit_system,
        "items": items,
        "errors": errors,
        "summary": {
            "total_items": len(items),
            "dirty_items": sum(1 for i in items if i["is_dirty"])
        }
    }