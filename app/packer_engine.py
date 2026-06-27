from typing import List
from dataclasses import dataclass

@dataclass
class CargoItem:
    id: str
    length_m: float
    width_m: float
    height_m: float
    mass_kg: float
    can_rotate: bool = True
    description: str = ""

@dataclass
class Placement:
    item: CargoItem
    x_m: float
    y_m: float
    z_m: float
    rotated: bool

def pack_floor_bin(items: List[CargoItem], bin_length_m: float, bin_width_m: float) -> List[Placement]:
    """
    Strict Row (Shelf) Greedy Packer.
    Sorts by Mass descending (front-heavy), then area.
    """
    if not items:
        return []

    sorted_items = sorted(items, key=lambda i: (i.mass_kg, i.length_m * i.width_m), reverse=True)
    
    placements = []
    current_y = 0.0
    current_x = 0.0
    current_row_height = 0.0

    for item in sorted_items:
        placed = False
        orientations = [(item.width_m, item.length_m)]
        if item.can_rotate:
            orientations.append((item.length_m, item.width_m))
        
        # Try longer side along X first to use row length efficiently
        orientations.sort(key=lambda o: o[1], reverse=True)
        
        for w, l in orientations:
            if (current_x + l <= bin_length_m + 0.001) and (current_y + w <= bin_width_m + 0.001):
                placements.append(Placement(
                    item=item,
                    x_m=current_x,
                    y_m=current_y,
                    z_m=0.0,
                    rotated=(w != item.width_m)
                ))
                current_x += l
                current_row_height = max(current_row_height, w)
                placed = True
                break
        
        if placed:
            continue

        # Start new row
        current_y += current_row_height
        current_x = 0.0
        current_row_height = 0.0

        min_needed_width = min(item.width_m, item.length_m) if item.can_rotate else item.width_m
        if current_y + min_needed_width > bin_width_m + 0.001:
            break 

        for w, l in orientations:
            if (current_x + l <= bin_length_m + 0.001) and (current_y + w <= bin_width_m + 0.001):
                placements.append(Placement(
                    item=item,
                    x_m=current_x,
                    y_m=current_y,
                    z_m=0.0,
                    rotated=(w != item.width_m)
                ))
                current_x += l
                current_row_height = max(current_row_height, w)
                placed = True
                break
        
        if not placed:
            break

    return placements