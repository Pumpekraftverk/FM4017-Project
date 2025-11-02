
import numpy as np
import pandas as pd



def merge_technologies(gens_df):
    gens_df_sum_before = gens_df.sum(axis=1)
    # ENTSO-E technologies that should be aggregated into "Other"
    other_sources = [
        "Fossil Brown coal/Lignite",
        "Fossil Peat",
        "Waste",
        "Other renewable",
        "Fossil Oil"
    ]

    print("Before merge:")
    print(f"Shape: {gens_df.shape}")
    print(f"Number of zones: {len(gens_df.columns.get_level_values('Zone').unique())}")
    print(f"Technologies for FI before: {gens_df['FI'].columns.tolist()}")

    # Make sure "Other" exists for each zone
    zones = gens_df.columns.get_level_values("Zone").unique()
    for zone in zones:
        if ("Zone" in gens_df.columns.names and 
            (zone, "Other") not in gens_df.columns):
            gens_df[(zone, "Other")] = 0.0

    # Go through each zone and aggregate "other_sources" into "Other"
    for zone in zones:
        for src in other_sources:
            col = (zone, src)
            if col in gens_df.columns:
                gens_df[(zone, "Other")] += gens_df[col]
                gens_df.drop(columns=[col], inplace=True)

    # Re-sort columns to keep order tidy
    gens_df = gens_df.sort_index(axis=1)

    print("\nAfter merge:")
    print(f"Shape: {gens_df.shape}")
    print(f"Technologies for FI after: {gens_df['FI'].columns.tolist()}")
    return gens_df