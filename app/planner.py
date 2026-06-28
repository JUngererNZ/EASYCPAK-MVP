from typing import List
from app.packer_engine import CargoItem, pack_floor_bin
from app.trailer_library import SuperlinkTrailer, TRAILER_TYPES, get_trailer


def plan_single_trailer(trailer_name: str, items: List[CargoItem]):
    config = get_trailer(trailer_name)
    if not config or config.get('is_link'):
        raise ValueError("Invalid single trailer config")

    placements = pack_floor_bin(
        items=items,
        bin_length_m=config['length_m'],
        bin_width_m=config['width_m']
    )
    
    total_mass = sum(p.item.mass_kg for p in placements)
    
    # Identify unplaced items
    placed_ids = set(id(p.item) for p in placements)
    unplaced = []
    for item in items:
        if id(item) not in placed_ids:
            unplaced.append({
                "id": item.id,
                "description": item.description,
                "length_m": item.length_m,
                "width_m": item.width_m,
                "height_m": item.height_m,
                "mass_kg": item.mass_kg,
                "reason": "Does not fit on trailer deck"
            })
    
    # Build visualization items
    vis_items = []
    for p in placements:
        vis_items.append({
            "id": p.item.id,
            "x": p.x_m,
            "y": p.y_m,
            "z": config['deck_height_m'],
            "width": p.item.width_m,
            "depth": p.item.length_m,
            "height": p.item.height_m,
            "label": p.item.description[:15],
            "rotated": p.rotated
        })

    return {
        "status": "success",
        "trailer_name": trailer_name,
        "trailer_type": "single",
        "is_safe": total_mass <= config['max_payload_kg'],
        "violations": [] if total_mass <= config['max_payload_kg'] else [f"Payload {total_mass/1000:.1f}t exceeds {config['max_payload_kg']/1000:.0f}t limit"],
        "total_mass_tons": round(total_mass / 1000, 2),
        "max_payload_tons": config['max_payload_kg'] / 1000,
        "utilization_percent": round((total_mass / config['max_payload_kg']) * 100, 1),
        "front_trailer": None,
        "rear_trailer": {
            "section": "Deck",
            "items_placed": len(placements),
            "total_mass_kg": total_mass,
            "placements": [{"item_id": p.item.id, "description": p.item.description, "length_m": p.item.length_m, "width_m": p.item.width_m, "height_m": p.item.height_m, "mass_kg": p.item.mass_kg, "x_m": p.x_m, "y_m": p.y_m, "z_m": p.z_m, "rotated": p.rotated} for p in placements]
        },
        "unplaced_items": unplaced,
        "axle_report": {
            "front_axle_load_tons": round(total_mass * 0.3 / 1000, 2),
            "rear_axle_group_load_tons": round(total_mass * 0.7 / 1000, 2),
            "center_of_gravity_m": round(total_mass * 0.4 / 1000, 2),
            "is_legal": total_mass <= config['max_payload_kg']
        },
        "visualization": {
            "container_length_m": config['length_m'],
            "container_width_m": config['width_m'],
            "container_height_m": 2.8,
            "deck_height_m": config['deck_height_m'],
            "items": vis_items
        }
    }


def plan_superlink(config_type: str, items: List[CargoItem]):
    superlink = SuperlinkTrailer(config_type=config_type)
    
    front_length = superlink.front['length_m']
    rear_length = superlink.rear['length_m']
    
    # Split items: if length > front, force to rear
    front_candidates = []
    rear_forced = []
    for item in items:
        min_len = min(item.length_m, item.width_m) if item.can_rotate else item.length_m
        if min_len <= front_length:
            front_candidates.append(item)
        else:
            rear_forced.append(item)
    
    # Stage 1: Front (Heaviest first)
    front_candidates.sort(key=lambda i: (i.mass_kg, i.length_m * i.width_m), reverse=True)
    front_placements = pack_floor_bin(front_candidates, front_length, superlink.front['width_m'])
    
    all_placed_ids = set()
    for p in front_placements:
        superlink.add_item_to_front(p.item, x_pos=p.x_m, y_pos=p.y_m)
        all_placed_ids.add(id(p.item))
    
    # Remaining items for rear
    remaining = list(rear_forced)
    for item in front_candidates:
        if id(item) not in all_placed_ids:
            remaining.append(item)
    
    # Stage 2: Rear
    remaining.sort(key=lambda i: (i.mass_kg, i.length_m * i.width_m), reverse=True)
    rear_placements = pack_floor_bin(remaining, rear_length, superlink.rear['width_m'])
    for p in rear_placements:
        superlink.add_item_to_rear(p.item, x_pos=p.x_m, y_pos=p.y_m)
        all_placed_ids.add(id(p.item))
    
    # Identify unplaced items
    unplaced = []
    for item in items:
        if id(item) not in all_placed_ids:
            unplaced.append({
                "id": item.id,
                "description": item.description,
                "length_m": item.length_m,
                "width_m": item.width_m,
                "height_m": item.height_m,
                "mass_kg": item.mass_kg,
                "reason": "Does not fit on superlink"
            })
    
    # Compliance
    is_safe, violations = superlink.is_safe()
    front_axle, rear_axle, cog = superlink.calculate_axle_loads()
    total_mass = superlink.total_mass_kg
    
    # Build visualization
    vis_items = []
    for item in superlink.front['items']:
        vis_items.append({
            "id": item.id,
            "x": item.x_pos,
            "y": item.y_pos,
            "z": superlink.deck_height_m,
            "width": item.width_m,
            "depth": item.length_m,
            "height": item.height_m,
            "label": item.description[:15]
        })
    for item in superlink.rear['items']:
        global_x = superlink.front['length_m'] + superlink.articulation_gap_m + item.x_pos
        vis_items.append({
            "id": item.id,
            "x": global_x,
            "y": item.y_pos,
            "z": superlink.deck_height_m,
            "width": item.width_m,
            "depth": item.length_m,
            "height": item.height_m,
            "label": item.description[:15]
        })

    return {
        "status": "success",
        "trailer_name": config_type,
        "trailer_type": "superlink",
        "is_safe": is_safe,
        "violations": violations,
        "total_mass_tons": round(total_mass / 1000, 2),
        "max_payload_tons": superlink.max_payload_kg / 1000,
        "utilization_percent": round((total_mass / superlink.max_payload_kg) * 100, 1) if superlink.max_payload_kg > 0 else 0,
        "front_trailer": {
            "section": "Leader (Front)",
            "items_placed": len(superlink.front['items']),
            "total_mass_kg": superlink.front['total_mass_kg'],
            "placements": [{"item_id": i.id, "description": i.description, "length_m": i.length_m, "width_m": i.width_m, "height_m": i.height_m, "mass_kg": i.mass_kg, "x_m": i.x_pos, "y_m": i.y_pos, "z_m": 0} for i in superlink.front['items']]
        },
        "rear_trailer": {
            "section": "Follower (Rear)",
            "items_placed": len(superlink.rear['items']),
            "total_mass_kg": superlink.rear['total_mass_kg'],
            "placements": [{"item_id": i.id, "description": i.description, "length_m": i.length_m, "width_m": i.width_m, "height_m": i.height_m, "mass_kg": i.mass_kg, "x_m": i.x_pos, "y_m": i.y_pos, "z_m": 0} for i in superlink.rear['items']]
        },
        "unplaced_items": unplaced,
        "axle_report": {
            "front_axle_load_tons": round(front_axle / 1000, 2),
            "rear_axle_group_load_tons": round(rear_axle / 1000, 2),
            "center_of_gravity_m": round(cog, 2),
            "is_legal": is_safe
        },
        "visualization": {
            "container_length_m": superlink.total_length_m,
            "container_width_m": superlink.width_m,
            "container_height_m": 2.8,
            "deck_height_m": superlink.deck_height_m,
            "items": vis_items
        }
    }


# ===================== RECOMMENDATION ENGINE =====================

def recommend_trailers(items: List[CargoItem]):
    """
    Suggests the optimal trailer configuration for the given items.
    Returns a dict with recommendation details and combined visualization.
    """
    # 1. Define the priority list (smallest to largest)
    all_trailers = list(TRAILER_TYPES.keys())
    
    # Define a logical order for single trailers
    single_trailer_order = [
        "Flatbed Standard",
        "Low-Loader",
        "Tri-Axle Flatbed",
        "Tri-Axle Low-Loader",
        "Superlink (6m + 6m)",
        "Superlink (6m + 12m)",
        "Tri-Axle Superlink",
        "Abnormal (Extendable)",
        "Super-Abnormal"
    ]
    
    # Filter to only those that exist in the loaded library
    available_order = [t for t in single_trailer_order if t in all_trailers]
    for t in all_trailers:
        if t not in available_order:
            available_order.append(t)
    
    # 2. Try all single trailers first (ascending)
    best_single_plan = None
    best_single_name = None
    for trailer_name in available_order:
        try:
            config = TRAILER_TYPES.get(trailer_name)
            if config and config.get('is_link'):
                result = plan_superlink(trailer_name, items)
            else:
                result = plan_single_trailer(trailer_name, items)
            
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
            continue

    # 3. Multi-trailer greedy approach (largest capacity first)
    multi_trailer_order = sorted(available_order, key=lambda t: TRAILER_TYPES[t].get('max_payload_kg', 0) if isinstance(TRAILER_TYPES[t], dict) else TRAILER_TYPES[t].max_payload_kg, reverse=True)
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
            
            placed_item_ids = set()
            if result.get('rear_trailer'):
                for p in result['rear_trailer'].get('placements', []):
                    placed_item_ids.add(p.get('item_id'))
            if result.get('front_trailer'):
                for p in result['front_trailer'].get('placements', []):
                    placed_item_ids.add(p.get('item_id'))
            
            new_remaining = []
            for item in remaining_items:
                if item.id not in placed_item_ids:
                    new_remaining.append(item)
            
            if len(placed_item_ids) > 0:
                trailer_used.append({
                    "type": trailer_name,
                    "plan": result
                })
                remaining_items = new_remaining
                
        except Exception as e:
            continue
    
    # 4. Build the final recommendation
    if not trailer_used:
        return {
            "recommendation": f"1 x {best_single_name} (partial load)",
            "trailer_count": 1,
            "trailers": [{"type": best_single_name, "plan": best_single_plan}],
            "is_safe": best_single_plan.get('is_safe', False),
            "total_mass_tons": best_single_plan.get('total_mass_tons', 0),
            "utilization_percent": best_single_plan.get('utilization_percent', 0),
            "unplaced_items": best_single_plan.get('unplaced_items', [])
        }
    
    # Build combined visualization
    combined_vis_items = []
    container_len = 0
    container_wid = 2.4
    deck_height = 1.2
    
    for t in trailer_used:
        plan = t['plan']
        if plan.get('visualization'):
            vis = plan['visualization']
            for item in vis.get('items', []):
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
        "unplaced_items": [],
        "combined_visualization": {
            "container_length_m": container_len,
            "container_width_m": container_wid,
            "container_height_m": 2.8,
            "deck_height_m": deck_height,
            "items": combined_vis_items
        }
    }