import pypsa
import numpy as np
import pandas as pd
from shapely.geometry import Point
import os




def DC_links_add(n, df_links_path=r"links_needed.csv"):
    df_links = pd.read_csv(
        df_links_path, header = 0, usecols=range(10)
    )


    # Make sure bus names are strings with no whitespace errors
    df_links["bus0"] = df_links["bus0"].astype(str).str.strip()
    df_links["bus1"] = df_links["bus1"].astype(str).str.strip()

    # Find all referenced buses
    referenced_buses = set(df_links["bus0"]) | set(df_links["bus1"])

    # Detect which buses do not exist in the network
    missing_buses = referenced_buses - set(n.buses.index)

    print("Missing buses:", missing_buses)

    # Your links dataframe
    # df_links = ...


    for _, row in df_links.iterrows():
        n.add(
            "Link",
            name=str(row["link_id"]),
            bus0=row["bus0"],
            bus1=row["bus1"],
            p_nom=row.get("p_nom",0),
            efficiency=row.get("efficiency",1),
            length=row.get("length", None)/1000,
            carrier='DC'
        )
    return n