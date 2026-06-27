from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class CargoItemInput(BaseModel):
    id: str
    description: str
    length_m: float
    width_m: float
    height_m: float
    mass_kg: float
    can_rotate: bool = True
    is_stackable: bool = False

class PlanRequest(BaseModel):
    trailer_name: str
    items: List[CargoItemInput]