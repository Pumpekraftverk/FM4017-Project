import pypsa
import numpy as np
import pandas as pd
from shapely.geometry import Point
import os

def dk_1_cleanup(n):
    # Remove all generators, loads, and storage units for DK_1
    dk1_buses = n.buses[n.buses['zone'] == 'DK_1'].index.tolist()
    print(f"Found {len(dk1_buses)} buses in DK_1 zone")

    # Remove components connected to DK_1 buses
    for bus in dk1_buses:
        # Remove generators
        gens_to_remove = n.generators[n.generators['bus'] == bus].index.tolist()
        if gens_to_remove:
            n.remove("Generator", gens_to_remove)
            print(f"Removed {len(gens_to_remove)} generators from {bus}")
        
        # Remove loads
        loads_to_remove = n.loads[n.loads['bus'] == bus].index.tolist()
        if loads_to_remove:
            n.remove("Load", loads_to_remove)
            print(f"Removed {len(loads_to_remove)} loads from {bus}")
        
        # Remove storage units
        if not n.storage_units.empty:
            stor_to_remove = n.storage_units[n.storage_units['bus'] == bus].index.tolist()
            if stor_to_remove:
                n.remove("StorageUnit", stor_to_remove)
                print(f"Removed {len(stor_to_remove)} storage units from {bus}")

    # Add one slack generator to DK_1
    if dk1_buses:
        dk1_bus = dk1_buses[0]  # Use first DK_1 bus
        n.add(
            "Generator",
            name="slack_DK_1",
            bus=dk1_bus,
            p_min_pu=0,
            p_max_pu=1,
            carrier="slack",
            control="Slack"
        )
        print(f"✅ Added slack generator to {dk1_bus}")