import pypsa
import numpy as np
import pandas as pd
from shapely.geometry import Point
import os
def add_ror_generators_NO(n, p_nom_ror=50):
    zones = ["NO_3", "NO_4"]

    for zone in zones:
        buses = n.buses.index[n.buses["zone"] == zone]
        print(f"Found {len(buses)} buses in {zone}")
        
        for bus in buses:
            gen_name = f"ror_{bus}"
            if gen_name not in n.generators.index:
                n.add(
                    "Generator",
                    name=gen_name,
                    bus=bus,
                    carrier="ror",
                    p_nom=p_nom_ror,
                    control="PQ"
                )
    n.generators["zone"] = n.generators["bus"].map(n.buses["zone"])
    return n



def add_other_generators_Nordic(n, p_nom_other=1.0):
    existing_other_buses = set(
        n.generators.loc[n.generators["carrier"].str.lower() == "other", "bus"]
    )

    added = 0
    for bus in n.buses.index:
        if bus in existing_other_buses:
            continue  # skip if 'other' generator already exists

        gen_name = f"{bus}_other"
        n.add(
            "Generator",
            name=gen_name,
            bus=bus,
            carrier="other",
            control="PQ",
            p_nom=p_nom_other,
        )

        # Initialize time series (zero production)
        n.generators_t.p_set[gen_name] = 0.0
        added += 1
    # Keep columns in order
    n.generators_t.p_set = n.generators_t.p_set.reindex(columns=n.generators.index)
    print(f"✅ Added {added} new 'other' PQ generators.")
#add_other_generators_Nordic(n, p_nom=1.0)