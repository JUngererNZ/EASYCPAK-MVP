import pandas as pd
import io

def parse_upload_file(file_bytes: bytes, filename: str, unit_system: str = "m", mass_unit: str = "kg"):
    """
    Reads Excel/CSV, maps columns, normalizes units.
    Supports: cm, in, mm, m for dimensions
    Supports: kg, ton for mass
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
        elif 'weight' in c or 'mass' in c or 'kg' in c or 'mass_kg' in c:
            col_map['mass'] = col
        elif 'description' in c or 'item' in c or 'name' in c or 'cube' in c or 'product' in c or 'code' in c or 'desc' in c:
            col_map['description'] = col

    # Unit factor: convert to meters
    if unit_system == "cm":
        factor = 0.01
    elif unit_system == "in":
        factor = 0.0254
    elif unit_system == "mm":
        factor = 0.001
    elif unit_system == "m":
        factor = 1.0
    else:
        factor = 0.01

    # Mass factor: convert to kg
    if mass_unit == "ton":
        mass_factor = 1000.0  # 1 ton = 1000 kg
    else:
        mass_factor = 1.0  # Already in kg

    items = []
    errors = []
    
    for idx, row in df.iterrows():
        try:
            l = float(row.get(col_map.get('length', 0))) if col_map.get('length') in row else 0.0
            w = float(row.get(col_map.get('width', 0))) if col_map.get('width') in row else 0.0
            h = float(row.get(col_map.get('height', 0))) if col_map.get('height') in row else 0.0
            mass_raw = float(row.get(col_map.get('mass', 0))) if col_map.get('mass') in row else 0.0
            desc = str(row.get(col_map.get('description', ''), f"Item {idx+2}")) if col_map.get('description') in row else f"Item {idx+2}"
            
            # Normalize to meters
            l_m = round(l * factor, 3)
            w_m = round(w * factor, 3)
            h_m = round(h * factor, 3)
            
            # Normalize mass to kg
            mass_kg = round(mass_raw * mass_factor, 2)
            
            is_dirty = (l_m == 0 or w_m == 0 or h_m == 0 or mass_kg == 0)
            dirty_fields = []
            if l_m == 0: dirty_fields.append("length")
            if w_m == 0: dirty_fields.append("width")
            if h_m == 0: dirty_fields.append("height")
            if mass_kg == 0: dirty_fields.append("mass")
            
            suggested_mass = None
            if mass_kg == 0 and l_m > 0 and w_m > 0 and h_m > 0:
                suggested_mass = round(l_m * w_m * h_m * 500, 2)
            
            items.append({
                "row_index": idx + 2,
                "id": f"ROW_{idx+2}",
                "description": desc,
                "length_m": l_m,
                "width_m": w_m,
                "height_m": h_m,
                "mass_kg": mass_kg,
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
        "mass_unit": mass_unit,
        "items": items,
        "errors": errors,
        "summary": {
            "total_items": len(items),
            "dirty_items": sum(1 for i in items if i["is_dirty"])
        }
    }