import pypsa
import numpy as np
import pandas as pd
from shapely.geometry import Point
import os
def capacity_check_per_zone(n):
    techs = set()

    if not n.generators.empty and "carrier" in n.generators.columns:
        techs.update(n.generators["carrier"].dropna().unique())

    if hasattr(n, "storage_units") and not n.storage_units.empty and "carrier" in n.storage_units.columns:
        techs.update(n.storage_units["carrier"].dropna().unique())

    for t in sorted(techs):
        print(t)

    print(f"\nTotal technologies: {len(techs)}")


    def capacity_by(component):
        if component is None or getattr(component, "empty", True):
            return pd.DataFrame()
        required = {"zone", "carrier", "p_nom"}
        if not required.issubset(component.columns):
            return pd.DataFrame()
        df = component[["zone", "carrier", "p_nom"]].dropna(subset=["zone", "carrier"]).copy()
        df["zone"] = df["zone"].astype(str)
        cap = (
            df.groupby(["zone", "carrier"]) ["p_nom"]
            .sum()
            .unstack(fill_value=0)
            .sort_index()
        )
        cap = cap.reindex(sorted(cap.columns), axis=1)
        return cap.round(1)

    gen_cap = capacity_by(n.generators)
    stor_cap = capacity_by(n.storage_units)
    pd.set_option('display.max_rows', None)       # show all rows
    pd.set_option('display.max_columns', None)    # show all columns (optional)
    pd.set_option('display.width', 0)             # no line wrap (optional)

    print("\nGenerators capacity (MW) by zone and technology:")
    print(gen_cap)

    print("\nStorage units capacity (MW) by zone and technology:")
    print(stor_cap)
    return gen_cap, stor_cap