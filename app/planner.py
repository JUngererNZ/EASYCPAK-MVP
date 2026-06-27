# ===================== RECOMMENDATION ENGINE =====================

from app.trailer_library import TRAILER_TYPES, SuperlinkTrailer
import copy

def recommend_trailers(items: List[CargoItem]):
    """
    Suggests the optimal trailer configuration for the given items.
    Returns a dict with recommendation details and combined visualization.
    """
    # 1. Define the priority list (smallest to largest)
    # We filter only the types that exist in the library
    all_trailers = list(TRAILER_TYPES.keys())
    
    # Define a logical order for single trailers
    single_trailer_order = [
        "Flatbed Standard",
        "Low-Loader",
        "Tri-Axle Flatbed",
        "Tri-Axle Low-Loader",
        "Superlink (6m + 6m)",  # Interlink
        "Superlink (6m + 12m)",
        "Tri-Axle Superlink",
        "Abnormal (Extendable)",
        "Super-Abnormal"
    ]
    
    # Filter to only those that exist in the loaded library
    available_order = [t for t in single_trailer_order if t in all_trailers]
    # Add any remaining trailers that might not be in the list
    for t in all_trailers:
        if t not in available_order:
            available_order.append(t)
    
    # 2. Try all single trailers first (ascending)
    best_single_plan = None
    best_single_name = None
    for trailer_name in available_order:
        try:
            # Check if it's a Superlink or Single
            config = TRAILER_TYPES.get(trailer_name)
            if config and config.get('is_link'):
                result = plan_superlink(trailer_name, items)
            else:
                result = plan_single_trailer(trailer_name, items)
            
            # If it can legally fit ALL items, return immediately (best case)
            if (result.get('status') == 'success' and 
                result.get('is_safe', False) and 
                len(result.get('unplaced_items', [])) == 0):
                return {
                    "recommendation": f"1 x {trailer_name}",
                    "trailer_count": 1,
                    "trailers": [{
                        "type": trailer_name,
                        "plan": result
                    }],
                    "is_safe": True,
                    "total_mass_tons": result.get('total_mass_tons', 0),
                    "utilization_percent": result.get('utilization_percent', 0),
                    "unplaced_items": []
                }
            
            # Keep track of the best single trailer (fewest unplaced items)
            if best_single_plan is None:
                best_single_plan = result
                best_single_name = trailer_name
            else:
                current_unplaced = len(result.get('unplaced_items', []))
                best_unplaced = len(best_single_plan.get('unplaced_items', []))
                if current_unplaced < best_unplaced:
                    best_single_plan = result
                    best_single_name = trailer_name
                    
        except Exception as e:
            # Skip trailers that cause errors (e.g., mismatched configs)
            continue

    # 3. If a single trailer fails to fit all, use a multi-trailer greedy approach
    # Start with the LARGEST available (reverse order)
    multi_trailer_order = list(reversed(available_order))
    placed_plans = []
    remaining_items = list(items)
    trailer_used = []
    
    for trailer_name in multi_trailer_order:
        if not remaining_items:
            break
        
        try:
            config = TRAILER_TYPES.get(trailer_name)
            if config and config.get('is_link'):
                result = plan_superlink(trailer_name, remaining_items)
            else:
                result = plan_single_trailer(trailer_name, remaining_items)
            
            # Determine which items were actually placed
            placed_item_ids = set()
            # Extract placed items from the result structure
            if result.get('rear_trailer'):
                for p in result['rear_trailer'].get('placements', []):
                    placed_item_ids.add(p.get('item_id'))
            if result.get('front_trailer'):
                for p in result['front_trailer'].get('placements', []):
                    placed_item_ids.add(p.get('item_id'))
            
            # Filter remaining items
            new_remaining = []
            for item in remaining_items:
                if item.id not in placed_item_ids:
                    new_remaining.append(item)
            
            # Only keep this trailer if it actually placed something
            if len(placed_item_ids) > 0:
                trailer_used.append({
                    "type": trailer_name,
                    "plan": result
                })
                remaining_items = new_remaining
            else:
                # If it placed nothing, try a different trailer
                pass
                
        except Exception as e:
            # Skip problematic trailers
            continue
    
    # 4. Build the final recommendation
    if not trailer_used:
        # Fallback: just return the best single trailer we found earlier
        return {
            "recommendation": f"1 x {best_single_name} (partial load)",
            "trailer_count": 1,
            "trailers": [{"type": best_single_name, "plan": best_single_plan}],
            "is_safe": best_single_plan.get('is_safe', False),
            "total_mass_tons": best_single_plan.get('total_mass_tons', 0),
            "utilization_percent": best_single_plan.get('utilization_percent', 0),
            "unplaced_items": best_single_plan.get('unplaced_items', [])
        }
    
    # Build combined visualization for all trailers
    combined_vis_items = []
    container_len = 0
    container_wid = 2.4
    deck_height = 1.2
    
    for t in trailer_used:
        plan = t['plan']
        if plan.get('visualization'):
            vis = plan['visualization']
            for item in vis.get('items', []):
                # Offset X position for multiple trailers
                combined_vis_items.append({
                    "id": item['id'],
                    "x": item['x'] + container_len,
                    "y": item['y'],
                    "z": item['z'],
                    "width": item['width'],
                    "depth": item['depth'],
                    "height": item['height'],
                    "label": item.get('label', '')
                })
            container_len += vis.get('container_length_m', 18)
    
    # Total mass and utilization
    total_mass = sum(t['plan'].get('total_mass_tons', 0) for t in trailer_used)
    total_capacity = sum(t['plan'].get('max_payload_tons', 0) for t in trailer_used)
    util = (total_mass / total_capacity * 100) if total_capacity > 0 else 0
    
    recommendation_text = f"{len(trailer_used)} trailers: " + " + ".join([f"1x {t['type']}" for t in trailer_used])
    
    return {
        "recommendation": recommendation_text,
        "trailer_count": len(trailer_used),
        "trailers": trailer_used,
        "is_safe": all(t['plan'].get('is_safe', False) for t in trailer_used),
        "total_mass_tons": round(total_mass, 2),
        "utilization_percent": round(util, 1),
        "unplaced_items": [],  # We assume all items are placed in this scenario
        "combined_visualization": {
            "container_length_m": container_len,
            "container_width_m": container_wid,
            "container_height_m": 2.8,
            "deck_height_m": deck_height,
            "items": combined_vis_items
        }
    }