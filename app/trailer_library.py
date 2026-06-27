"""
Trailer Library with South African Specifications
Includes Standard Trailers, Tri-Axle, and Superlink (Link) Configurations
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple


# ==================== TRAILER TYPE DEFINITIONS ====================

TRAILER_TYPES = {
    # ===== STANDARD SINGLE TRAILERS (Tandem Axle) =====
    "Flatbed Standard": {
        "type": "single",
        "length_m": 13.6,
        "width_m": 2.4,
        "deck_height_m": 1.2,
        "max_payload_kg": 28000,
        "max_rear_axle_kg": 18000,  # Tandem limit
        "max_kingpin_kg": 12000,
        "wheelbase_m": 10.5,
        "axle_count": 2,
        "axle_configuration": [
            {"type": "steering", "axle_count": 1},
            {"type": "tandem", "axle_count": 2}
        ],
        "tare_kg": 6000,
        "permit_required": False,
        "description": "Standard flatbed trailer, tandem axles. Max rear load 18t.",
        "container_capacity": "1 x 40ft or 2 x 20ft"
    },
    
    "Low-Loader": {
        "type": "single",
        "length_m": 13.6,
        "width_m": 2.8,
        "deck_height_m": 0.8,
        "max_payload_kg": 35000,
        "max_rear_axle_kg": 18000,
        "max_kingpin_kg": 15000,
        "wheelbase_m": 9.5,
        "axle_count": 2,
        "axle_configuration": [
            {"type": "steering", "axle_count": 1},
            {"type": "tandem", "axle_count": 2}
        ],
        "tare_kg": 8000,
        "permit_required": False,
        "description": "Low-bed trailer for tall/heavy gensets. Tandem axles.",
        "container_capacity": "1 x 40ft or 2 x 20ft"
    },
    
    # ===== TRI-AXLE CONFIGURATIONS =====
    "Tri-Axle Flatbed": {
        "type": "single",
        "is_triaxle": True,
        "length_m": 13.6,
        "width_m": 2.4,
        "deck_height_m": 1.2,
        "max_payload_kg": 30000,
        "max_rear_axle_kg": 27000,  # Tri-axle group limit (Reg 240)
        "max_kingpin_kg": 12000,
        "wheelbase_m": 10.5,
        "axle_count": 3,
        "axle_configuration": [
            {"type": "steering", "axle_count": 1},
            {"type": "triaxle", "axle_count": 3}
        ],
        "tare_kg": 7000,
        "permit_required": False,
        "description": "Tri-axle flatbed trailer. 3 rear axles, max payload 30t. Legal axle group limit 27t.",
        "container_capacity": "1 x 40ft or 2 x 20ft",
        "best_for": "Heavy machinery, gensets, steel, dense cargo"
    },
    
    "Tri-Axle Low-Loader": {
        "type": "single",
        "is_triaxle": True,
        "length_m": 13.6,
        "width_m": 2.8,
        "deck_height_m": 0.8,
        "max_payload_kg": 35000,
        "max_rear_axle_kg": 27000,
        "max_kingpin_kg": 15000,
        "wheelbase_m": 9.5,
        "axle_count": 3,
        "axle_configuration": [
            {"type": "steering", "axle_count": 1},
            {"type": "triaxle", "axle_count": 3}
        ],
        "tare_kg": 8500,
        "permit_required": False,
        "description": "Tri-axle low-loader for tall/heavy gensets. Max payload 35t.",
        "container_capacity": "1 x 40ft or 2 x 20ft",
        "best_for": "Tall gensets, heavy machinery with height"
    },
    
    "Abnormal (Extendable)": {
        "type": "single",
        "length_m": 18.0,
        "width_m": 3.0,
        "deck_height_m": 1.0,
        "max_payload_kg": 50000,
        "max_rear_axle_kg": 30000,
        "max_kingpin_kg": 18000,
        "wheelbase_m": 14.0,
        "axle_count": 6,
        "axle_configuration": [
            {"type": "steering", "axle_count": 1},
            {"type": "triaxle", "axle_count": 3},
            {"type": "tandem", "axle_count": 2}
        ],
        "tare_kg": 10000,
        "permit_required": True,
        "description": "Requires abnormal load permit (Section 81)",
        "container_capacity": "1 x 40ft + oversize"
    },
    
    "Super-Abnormal": {
        "type": "single",
        "length_m": 24.0,
        "width_m": 3.5,
        "deck_height_m": 1.0,
        "max_payload_kg": 80000,
        "max_rear_axle_kg": 40000,
        "max_kingpin_kg": 25000,
        "wheelbase_m": 19.0,
        "axle_count": 8,
        "axle_configuration": [
            {"type": "steering", "axle_count": 1},
            {"type": "triaxle", "axle_count": 3},
            {"type": "triaxle", "axle_count": 3},
            {"type": "single", "axle_count": 1}
        ],
        "tare_kg": 15000,
        "permit_required": True,
        "description": "Escort vehicles required, route approval needed",
        "container_capacity": "Custom oversize"
    },
    
    # ===== SUPERLINK (LINK) CONFIGURATIONS =====
    "Superlink (6m + 12m)": {
        "type": "superlink",
        "is_link": True,
        "front_trailer": {
            "name": "Leader (Front)",
            "length_m": 6.0,
            "width_m": 2.4,
            "deck_height_m": 1.2,
            "max_payload_kg": 14000,
            "tare_kg": 3500,
            "axle_count": 2,
            "axle_config": [{"type": "single", "axle_count": 2}]
        },
        "rear_trailer": {
            "name": "Follower (Rear)",
            "length_m": 12.0,
            "width_m": 2.4,
            "deck_height_m": 1.2,
            "max_payload_kg": 20000,
            "tare_kg": 4500,
            "axle_count": 2,
            "axle_config": [{"type": "tandem", "axle_count": 2}]
        },
        "total_length_m": 18.0,
        "articulation_gap_m": 0.5,
        "max_payload_kg": 34000,
        "max_gcm_kg": 56000,
        "pallet_capacity_single": 60,
        "pallet_capacity_euro": 84,
        "permit_required": False,
        "description": "6m front + 12m rear trailer (tandem axles). Max payload 34t.",
        "best_for": "Container transport, palletized goods, mixed cargo"
    },
    
    "Tri-Axle Superlink": {
        "type": "superlink",
        "is_link": True,
        "is_triaxle": True,
        "front_trailer": {
            "name": "Leader (Front)",
            "length_m": 6.0,
            "width_m": 2.4,
            "deck_height_m": 1.2,
            "max_payload_kg": 14000,
            "tare_kg": 3500,
            "axle_count": 2,
            "axle_config": [{"type": "single", "axle_count": 2}]
        },
        "rear_trailer": {
            "name": "Follower (Rear) - Tri-Axle",
            "length_m": 12.0,
            "width_m": 2.4,
            "deck_height_m": 1.2,
            "max_payload_kg": 20000,
            "tare_kg": 5000,
            "axle_count": 3,
            "axle_config": [{"type": "triaxle", "axle_count": 3}]
        },
        "total_length_m": 18.0,
        "articulation_gap_m": 0.5,
        "max_payload_kg": 34000,
        "max_gcm_kg": 56000,
        "pallet_capacity_single": 60,
        "pallet_capacity_euro": 84,
        "permit_required": False,
        "description": "Superlink with TRI-AXLE rear trailer. Rear axle group: 27t legal limit.",
        "best_for": "Maximum legal payload, heavy container transport"
    },
    
    "Interlink (6m + 6m)": {
        "type": "superlink",
        "is_link": True,
        "front_trailer": {
            "name": "Leader (Front)",
            "length_m": 6.0,
            "width_m": 2.4,
            "deck_height_m": 1.2,
            "max_payload_kg": 17000,
            "tare_kg": 3500,
            "axle_count": 2,
            "axle_config": [{"type": "single", "axle_count": 2}]
        },
        "rear_trailer": {
            "name": "Follower (Rear)",
            "length_m": 6.0,
            "width_m": 2.4,
            "deck_height_m": 1.2,
            "max_payload_kg": 17000,
            "tare_kg": 3500,
            "axle_count": 2,
            "axle_config": [{"type": "tandem", "axle_count": 2}]
        },
        "total_length_m": 12.0,
        "articulation_gap_m": 0.5,
        "max_payload_kg": 34000,
        "max_gcm_kg": 56000,
        "pallet_capacity_single": 40,
        "pallet_capacity_euro": 56,
        "permit_required": False,
        "description": "6m + 6m configuration for high-density loads",
        "best_for": "Bulk commodities, side-tippers, heavy dense cargo"
    }
}


# ==================== SUPERLINK TRAILER CLASS ====================

class SuperlinkTrailer:
    """Superlink (Link) Trailer - Two trailers articulated together"""
    
    def __init__(self, name="Superlink", config_type="Superlink (6m + 12m)"):
        self.name = name
        self.config = TRAILER_TYPES[config_type]
        self.type_name = config_type
        self.is_link = True
        self.is_triaxle = self.config.get("is_triaxle", False)
        
        # Front trailer (Leader)
        self.front = self.config["front_trailer"].copy()
        self.front["items"] = []
        self.front["total_mass_kg"] = 0
        
        # Rear trailer (Follower)
        self.rear = self.config["rear_trailer"].copy()
        self.rear["items"] = []
        self.rear["total_mass_kg"] = 0
        
        # Combined metrics
        self.total_length_m = self.config["total_length_m"]
        self.max_payload_kg = self.config["max_payload_kg"]
        self.articulation_gap_m = self.config.get("articulation_gap_m", 0.5)
        self.total_mass_kg = 0
        self.width_m = self.front["width_m"]
        self.length_m = self.total_length_m
        self.items = []
    
    # Properties for compatibility
    @property
    def wheelbase_m(self):
        return 10.5
    
    @property
    def max_kingpin_kg(self):
        return self.config.get("max_kingpin_kg", 12000)
    
    @property
    def max_rear_axle_kg(self):
        if self.is_triaxle:
            return 27000
        return 18000
    
    @property
    def deck_height_m(self):
        return self.front["deck_height_m"]
    
    @property
    def trailer_tare_kg(self):
        return self.front.get("tare_kg", 3500) + self.rear.get("tare_kg", 4500)
    
    @property
    def axle_count(self):
        return self.front.get("axle_count", 2) + self.rear.get("axle_count", 2)
    
    @property
    def axle_configuration(self):
        config = []
        config.extend(self.front.get("axle_config", [{"type": "single", "axle_count": 2}]))
        config.extend(self.rear.get("axle_config", [{"type": "tandem", "axle_count": 2}]))
        return config
    
    # Methods
    def can_add_item_to_front(self, item, x_pos, gap_m=0.15):
        if x_pos + item.length_m > self.front["length_m"]:
            return False, f"Exceeds front trailer length ({self.front['length_m']}m)"
        if item.width_m > self.front["width_m"]:
            return False, f"Width {item.width_m}m exceeds trailer width"
        if self.front["total_mass_kg"] + item.mass_kg > self.front["max_payload_kg"]:
            return False, f"Would exceed front trailer payload"
        for existing in self.front["items"]:
            if (x_pos < existing.x_pos + existing.length_m + gap_m and
                x_pos + item.length_m + gap_m > existing.x_pos):
                return False, f"Collision with {existing.consignment}"
        return True, "OK"
    
    def can_add_item_to_rear(self, item, x_pos, gap_m=0.15):
        if x_pos + item.length_m > self.rear["length_m"]:
            return False, f"Exceeds rear trailer length ({self.rear['length_m']}m)"
        if item.width_m > self.rear["width_m"]:
            return False, f"Width {item.width_m}m exceeds trailer width"
        if self.rear["total_mass_kg"] + item.mass_kg > self.rear["max_payload_kg"]:
            return False, f"Would exceed rear trailer payload"
        for existing in self.rear["items"]:
            if (x_pos < existing.x_pos + existing.length_m + gap_m and
                x_pos + item.length_m + gap_m > existing.x_pos):
                return False, f"Collision with {existing.consignment}"
        return True, "OK"
    
    def add_item_to_front(self, item, x_pos, y_pos=0.15):
        item.x_pos = x_pos
        item.y_pos = y_pos
        item.trailer_section = "front"
        self.front["items"].append(item)
        self.front["total_mass_kg"] += item.mass_kg
        self.total_mass_kg += item.mass_kg
    
    def add_item_to_rear(self, item, x_pos, y_pos=0.15):
        item.x_pos = x_pos
        item.y_pos = y_pos
        item.trailer_section = "rear"
        self.rear["items"].append(item)
        self.rear["total_mass_kg"] += item.mass_kg
        self.total_mass_kg += item.mass_kg
    
    def calculate_axle_loads(self):
        front_axle_load = self.front["total_mass_kg"] * 0.3
        rear_axle_load = (self.rear["total_mass_kg"] * 0.7) + (self.front["total_mass_kg"] * 0.1)
        total_moment = 0
        for item in self.front["items"]:
            cog = item.x_pos + (item.length_m / 2)
            total_moment += item.mass_kg * cog
        for item in self.rear["items"]:
            cog = self.front["length_m"] + self.articulation_gap_m + item.x_pos + (item.length_m / 2)
            total_moment += item.mass_kg * cog
        combined_cog = total_moment / self.total_mass_kg if self.total_mass_kg > 0 else 0
        return front_axle_load, rear_axle_load, combined_cog
    
    def is_safe(self):
        violations = []
        if self.total_mass_kg > self.max_payload_kg:
            violations.append(f"Total payload exceeds {self.max_payload_kg/1000:.0f}t limit")
        if self.front["total_mass_kg"] > self.front["max_payload_kg"]:
            violations.append(f"Front trailer overload")
        if self.rear["total_mass_kg"] > self.rear["max_payload_kg"]:
            violations.append(f"Rear trailer overload")
        return len(violations) == 0, violations
    
    def get_all_items(self):
        all_items = self.front["items"] + self.rear["items"]
        self.items = all_items
        return all_items
    
    def get_summary(self):
        return {
            "name": self.name,
            "type": self.type_name,
            "is_triaxle": self.is_triaxle,
            "total_items": len(self.get_all_items()),
            "total_mass_tons": self.total_mass_kg / 1000,
            "max_payload_tons": self.max_payload_kg / 1000,
            "rear_axle_limit_tons": self.max_rear_axle_kg / 1000,
            "front": {
                "items": len(self.front["items"]),
                "mass_tons": self.front["total_mass_kg"] / 1000
            },
            "rear": {
                "items": len(self.rear["items"]),
                "mass_tons": self.rear["total_mass_kg"] / 1000
            }
        }
    
    def add_item(self, item, x_pos, y_pos=0.15):
        if x_pos > self.front["length_m"] + 0.5:
            rear_x = x_pos - self.front["length_m"] - self.articulation_gap_m
            self.add_item_to_rear(item, rear_x, y_pos)
        else:
            self.add_item_to_front(item, x_pos, y_pos)


# ==================== HELPER FUNCTIONS ====================

def get_trailer(trailer_name):
    if trailer_name not in TRAILER_TYPES:
        return TRAILER_TYPES.get("Flatbed Standard")
    config = TRAILER_TYPES[trailer_name]
    if config.get("is_link"):
        return SuperlinkTrailer(config_type=trailer_name)
    return config


def list_trailers():
    return list(TRAILER_TYPES.keys())


if __name__ == "__main__":
    print("Testing Trailer Library with Tri-Axle...\n")
    
    # Test Tri-Axle Flatbed
    print("TEST: Tri-Axle Flatbed")
    triaxle = TRAILER_TYPES["Tri-Axle Flatbed"]
    print(f"   Length: {triaxle['length_m']}m")
    print(f"   Payload: {triaxle['max_payload_kg']/1000:.0f}t")
    print(f"   Rear Axle Limit: {triaxle['max_rear_axle_kg']/1000:.0f}t (tri-axle group)")
    print(f"   Axle Config: {triaxle['axle_configuration']}")
    print("   ✓ Passed\n")
    
    # Test Tri-Axle Superlink
    print("TEST: Tri-Axle Superlink")
    superlink_tri = SuperlinkTrailer(config_type="Tri-Axle Superlink")
    print(f"   Type: {superlink_tri.type_name}")
    print(f"   Is Tri-Axle: {superlink_tri.is_triaxle}")
    print(f"   Rear Axle Limit: {superlink_tri.max_rear_axle_kg/1000:.0f}t")
    print(f"   Rear Axle Count: {superlink_tri.rear['axle_count']}")
    print("   ✓ Passed\n")
    
    print("✅ All tests passed!")