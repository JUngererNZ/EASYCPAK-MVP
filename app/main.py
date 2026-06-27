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