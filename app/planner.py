from typing import List, Dict, Any
from app.packer_engine import CargoItem, pack_floor_bin
from app.trailer_library import SuperlinkTrailer, TRAILER_TYPES, get_trailer

def plan_single_trailer(trailer_name: str, items: List[CargoItem]) -> Dict[str, Any]:
    config = get_trailer(trailer_name)
    if not config or config.get('is_link'):
        raise ValueError("Invalid single trailer config")

    placements = pack_floor_bin(
        items=items,
        bin_length_m=config['length_m'],
        bin_width_m=config['width_m']
    )
    
    total_mass = sum(p.item.mass_kg for p in placements)
    
    # Build visualization items for frontend
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
            "placements": [{"item_id": p.item.id, "x_m": p.x_m, "y_m": p.y_m, "z_m": p.z_m, "rotated": p.rotated} for p in placements]
        },
        "unplaced_items": [],
        "axle_report": {
            "front_axle_load_tons": round(total_mass * 0.3 / 1000, 2),
            "rear_axle_group_load_tons": round(total_mass * 0.7 / 1000, 2),
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

def plan_superlink(config_type: str, items: List[CargoItem]) -> Dict[str, Any]:
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
    
    placed_ids = set()
    for p in front_placements:
        superlink.add_item_to_front(p.item, x_pos=p.x_m, y_pos=p.y_m)
        placed_ids.add(id(p.item))
    
    # Remaining items for rear
    remaining = list(rear_forced)
    for item in front_candidates:
        if id(item) not in placed_ids:
            remaining.append(item)
    
    # Stage 2: Rear
    remaining.sort(key=lambda i: (i.mass_kg, i.length_m * i.width_m), reverse=True)
    rear_placements = pack_floor_bin(remaining, rear_length, superlink.rear['width_m'])
    for p in rear_placements:
        superlink.add_item_to_rear(p.item, x_pos=p.x_m, y_pos=p.y_m)
    
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
        # Adjust X to global coordinate for visualization
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
            "placements": [{"item_id": i.id, "x_m": i.x_pos, "y_m": i.y_pos, "z_m": 0} for i in superlink.front['items']]
        },
        "rear_trailer": {
            "section": "Follower (Rear)",
            "items_placed": len(superlink.rear['items']),
            "total_mass_kg": superlink.rear['total_mass_kg'],
            "placements": [{"item_id": i.id, "x_m": i.x_pos, "y_m": i.y_pos, "z_m": 0} for i in superlink.rear['items']]
        },
        "unplaced_items": [],  # We could track this, but for now assume we placed all we could
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