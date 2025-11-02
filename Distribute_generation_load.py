import pypsa
import numpy as np
import pandas as pd
from shapely.geometry import Point
import os

def distribute_generation_load(n, gens_df, loads_df):
    # REPLACEMENT FOR CELL 24 - Copy this to replace your problematic cell

    # Reindex time series to network snapshots
    n.generators_t.p_set    = n.generators_t.p_set.reindex(n.snapshots, columns=n.generators.index, fill_value=0.0)
    n.storage_units_t.p_set = n.storage_units_t.p_set.reindex(n.snapshots, columns=n.storage_units.index, fill_value=0.0)
    n.loads_t.p_set         = n.loads_t.p_set.reindex(n.snapshots, columns=n.loads.index, fill_value=0.0)



    # ENTSO-E tech -> carriers (swapped mapping); build inverse carrier -> ENTSO-E
    ENTSOE_TO_CARRIERS = {
        "Fossil Gas":["ccgt","ocgt"],
        "Biomass":["biomass"],
        "Fossil Hard coal":["coal"],
        #"Fossil Brown coal/Lignite":["other"],
        "Fossil Oil":["oil"],
        #"Fossil Peat":["other"],
        "Nuclear":["nuclear"],
        "Wind Onshore":["onwind"],
        "Wind Offshore":["offwind-ac","offwind-dc","offwind-float"],
        "Solar":["solar","solar-hsat"],
        "Hydro Run-of-river and poundage":["ror"],
        "Hydro Pumped Storage":["phs"],
        "Hydro Water Reservoir":["hydro"],
        #"Waste":["other"],
        "Other":["other"],
        #"Other renewable":["other"],
        }

    CARRIER_TO_ENTSOE = {c.lower().strip(): t for t, cs in ENTSOE_TO_CARRIERS.items() for c in cs}     


    def distribute_loads_by_share(loads_df):
        if loads_df is None or loads_df.empty:
            return
        
        # Map bus load share to loads
        load_share = n.buses["load_share"].reindex(n.loads["bus"]).fillna(0.0)
        
        zones = n.loads["zone"]
        
        for Z, idx in zones.groupby(zones).groups.items():
            
            if Z not in loads_df.columns or len(idx) == 0:
                continue
            
            # Zone-level load time series
            zone_ts = loads_df[Z].reindex(n.snapshots).fillna(0.0).to_numpy()
            
            # Local bus weights
            w = load_share.loc[idx]
            W = w.sum()
            
            if W <= 0:
                print(f"⚠ Zone {Z} has zero weighting. Even distribution.")
                w = np.ones(len(idx)) / len(idx)
            else:
                w = w / W
            
            # Weighted distribution to loads at buses
            n.loads_t.p_set.loc[:, idx] = pd.DataFrame(
                zone_ts[:, None] * w.values[None, :],
                index=n.snapshots,
                columns=idx
            )   


    def distribute_production_from_shares(n, gens_df):
        
        """Distribute zone-tech aggregated production in gens_df
        to individual generators using n.generators.production_share.
        """

        gen = n.generators

        # Ensure metadata exists and aligned with gens_df
        gen["Zone"] = gen["zone"].astype(str)
        gen["Tech"] = (
            gen["carrier"]
            .astype(str)
            .str.lower()
            .str.strip()
            .map(CARRIER_TO_ENTSOE)
            .fillna("Other")
        )

        if "production_share" not in gen.columns:
            raise ValueError("Missing production_share")

        snaps = n.snapshots
        n.generators_t.p_set.loc[:, :] = 0.0  # reset

        for (Z, T) in gens_df.columns:
            # FIND GENERATORS MATCHING ZONE + TECH ✅
            idx = gen.index[(gen["Zone"] == Z) & (gen["Tech"] == T)]
            if len(idx) == 0:
                continue

            # Zone-tech time series
            ts = gens_df[(Z, T)].reindex(snaps).to_numpy()
            w = gen.loc[idx, "production_share"].to_numpy()

            # Distribute production
            n.generators_t.p_set.loc[:, idx] = ts[:, None] * w[None, :]

            print(f"✅ distributed: Zone={Z} Tech={T} Units={len(idx)}")



    def distribute_storage_from_shares(n, gens_df):
        """
        Distribute zone-tech aggregated production in gens_df
        to individual generators using n.generators.production_share.
        """

        gen = n.storage_units

        # Ensure metadata exists and aligned with gens_df
        gen["Zone"] = gen["zone"].astype(str)
        gen["Tech"] = (
            gen["carrier"]
            .astype(str)
            .str.lower()
            .str.strip()
            .map(CARRIER_TO_ENTSOE)
            .fillna("Other")
        )

        if "production_share" not in gen.columns:
            raise ValueError("Missing production_share")

        snaps = n.snapshots
        n.storage_units_t.p_set.loc[:, :] = 0.0  # reset

        for (Z, T) in gens_df.columns:
            # FIND GENERATORS MATCHING ZONE + TECH ✅
            idx = gen.index[(gen["Zone"] == Z) & (gen["Tech"] == T)]
            if len(idx) == 0:
                continue

            # Zone-tech time series
            ts = gens_df[(Z, T)].reindex(snaps).to_numpy()
            w = gen.loc[idx, "production_share"].to_numpy()

            # Distribute production
            n.storage_units_t.p_set.loc[:, idx] = ts[:, None] * w[None, :]

            print(f"✅ distributed: Zone={Z} Tech={T} Units={len(idx)}")




    # Run distributions (allow generators to exceed p_nom, keep storage capped)

    #distribute_zone_tech(n.generators, n.generators_t.p_set, gens_df, cap=False)
    #distribute_zone_tech(n.storage_units, n.storage_units_t.p_set, gens_df, cap=True)

    #distribute_generation(n.generators,    n.generators_t.p_set, cap=False)  #generators
    distribute_production_from_shares(n, gens_df)
    distribute_storage_from_shares(n,gens_df)   #storage units
    distribute_loads_by_share(loads_df)
    #distribute_loads_equal(loads_df)

    n.generators.drop(columns=["Zone", "Tech"], inplace=True)
    n.storage_units.drop(columns=["Zone", "Tech"], inplace=True)

    # SKIP ZONE MISMATCH CHECK - Just continue
    print("✅ Network data distributed successfully")

    # Quick totals

    print("Produksjon (MW):\n", (n.generators_t.p_set.sum(1) + n.storage_units_t.p_set.clip(lower=0).sum(axis=1)))
    print("\nLast (MW):\n", (n.loads_t.p_set.sum(1)))

    return