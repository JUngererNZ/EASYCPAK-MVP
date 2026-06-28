import pandas as pd
import io
import re

def parse_upload_file(file_bytes: bytes, filename: str, unit_system: str = "m", mass_unit: str = "auto"):
    """
    Reads Excel/CSV, maps columns, normalizes units.
    Supports: cm, in, mm, m for dimensions
    Supports: kg, ton, auto for mass (auto-detects tons)
    """
    try:
        if filename.lower().endswith('.csv'):
            df = pd.read_csv(io.BytesIO(file_bytes))
        else:
            df = pd.read_excel(io.BytesIO(file_bytes))
    except Exception as e:
        return {"error": f"Failed to read file: {str(e)}"}

    # ====== COLUMN MAPPING ======
    col_map = {}
    
    for col in df.columns:
        col_lower = col.lower().strip()
        col_clean = re.sub(r'[^a-z]', '', col_lower)
        
        # Description columns
        if col_lower in ['cube', 'desc', 'description', 'item', 'name', 'product', 'code', 'model']:
            col_map['description'] = col
        elif 'cube' in col_lower or 'desc' in col_lower or 'model' in col_lower:
            if 'description' not in col_map:
                col_map['description'] = col
        
        # Length columns
        if col_lower in ['length', 'l', 'len']:
            col_map['length'] = col
        elif 'length' in col_lower and 'length' not in col_map:
            col_map['length'] = col
        
        # Width columns
        if col_lower in ['width', 'w', 'breadth']:
            col_map['width'] = col
        elif 'width' in col_lower and 'width' not in col_map:
            col_map['width'] = col
        
        # Height columns
        if col_lower in ['height', 'h', 'depth']:
            col_map['height'] = col
        elif 'height' in col_lower and 'height' not in col_map:
            col_map['height'] = col
        
        # Mass columns
        if col_lower in ['mass', 'weight', 'kg', 'mass_kg', 'weight_kg', 't', 'ton', 'tons']:
            col_map['mass'] = col
        elif 'mass' in col_lower or 'weight' in col_lower or 'ton' in col_lower:
            if 'mass' not in col_map:
                col_map['mass'] = col
        
        # Quantity columns
        if col_lower in ['qty', 'quantity', 'units', 'pieces', 'count', 'unit', 'pcs']:
            col_map['quantity'] = col

    # ====== FALLBACK: Use position-based guessing ======
    if not col_map or 'length' not in col_map:
        headers = list(df.columns)
        if len(headers) >= 5:
            col_map['description'] = headers[0] if 'description' not in col_map else col_map['description']
            col_map['length'] = headers[1] if 'length' not in col_map else col_map['length']
            col_map['width'] = headers[2] if 'width' not in col_map else col_map['width']
            col_map['height'] = headers[3] if 'height' not in col_map else col_map['height']
            col_map['mass'] = headers[4] if 'mass' not in col_map else col_map['mass']

    # ====== UNIT FACTORS ======
    if unit_system == "cm":
        factor = 0.01
    elif unit_system == "in":
        factor = 0.0254
    elif unit_system == "mm":
        factor = 0.001
    elif unit_system == "m":
        factor = 1.0
    else:
        factor = 1.0

    # ====== AUTO-DETECT MASS UNIT ======
    mass_factor = 1.0  # Default: kg
    
    # If user explicitly set mass unit, use that
    if mass_unit == "ton":
        mass_factor = 1000.0
    elif mass_unit == "kg":
        mass_factor = 1.0
    else:  # "auto" - detect from data
        mas_col = col_map.get('mass')
        if mas_col and mas_col in df:
            mass_values = df[mas_col].dropna().tolist()
            if mass_values:
                # Check if values look like tons (0.1 to 100, with decimals)
                avg_mass = sum(mass_values) / len(mass_values)
                max_mass = max(mass_values)
                min_mass = min(mass_values)
                
                # If all values are between 0.1 and 100, likely tons
                if 0.1 < avg_mass < 100 and max_mass < 100 and min_mass > 0.01:
                    mass_factor = 1000.0  # Convert tons to kg
                # If values are huge (1000+), likely already kg
                elif avg_mass > 1000:
                    mass_factor = 1.0
                # If values are tiny (0.001-0.1), could be tons of small items
                elif 0.001 < avg_mass < 0.1:
                    mass_factor = 1000.0

    # ====== PARSE DATA ======
    items = []
    errors = []
    
    qty_col = col_map.get('quantity')
    
    for idx, row in df.iterrows():
        try:
            desc_col = col_map.get('description')
            len_col = col_map.get('length')
            wid_col = col_map.get('width')
            hei_col = col_map.get('height')
            mas_col = col_map.get('mass')
            
            # Extract values
            l = float(row[len_col]) if len_col and len_col in row and pd.notna(row[len_col]) else 0.0
            w = float(row[wid_col]) if wid_col and wid_col in row and pd.notna(row[wid_col]) else 0.0
            h = float(row[hei_col]) if hei_col and hei_col in row and pd.notna(row[hei_col]) else 0.0
            mass_raw = float(row[mas_col]) if mas_col and mas_col in row and pd.notna(row[mas_col]) else 0.0
            desc = str(row[desc_col]) if desc_col and desc_col in row and pd.notna(row[desc_col]) else f"Item_{idx+2}"
            
            # Get quantity (default 1)
            qty = 1
            if qty_col and qty_col in row and pd.notna(row[qty_col]):
                qty = max(1, int(float(row[qty_col])))
            
            # Clean description
            if desc.endswith('.0'):
                desc = desc[:-2]
            if desc.lower() in ['nan', 'none', '']:
                desc = f"Item_{idx+2}"
            
            # Normalize dimensions to meters
            l_m = round(l * factor, 3)
            w_m = round(w * factor, 3)
            h_m = round(h * factor, 3)
            
            # Normalize mass to kg
            mass_kg = round(mass_raw * mass_factor, 3)
            
            # Detect dirty data
            is_dirty = (l_m == 0 or w_m == 0 or h_m == 0 or mass_kg == 0)
            dirty_fields = []
            if l_m == 0: dirty_fields.append("length")
            if w_m == 0: dirty_fields.append("width")
            if h_m == 0: dirty_fields.append("height")
            if mass_kg == 0: dirty_fields.append("mass")
            
            # Suggest mass based on volume
            suggested_mass = None
            if mass_kg == 0 and l_m > 0 and w_m > 0 and h_m > 0:
                suggested_mass = round(l_m * w_m * h_m * 500, 2)
            
            # Expand quantity into multiple items
            for copy_idx in range(qty):
                item_id = f"ROW_{idx+2}" if qty == 1 else f"ROW_{idx+2}_{copy_idx+1}"
                items.append({
                    "row_index": idx + 2 if qty == 1 else f"{idx+2}.{copy_idx+1}",
                    "id": item_id,
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
        "mass_unit": "ton" if mass_factor == 1000.0 else "kg",
        "mass_factor_used": mass_factor,
        "items": items,
        "errors": errors,
        "summary": {
            "total_items": len(items),
            "dirty_items": sum(1 for i in items if i["is_dirty"])
        }
    }