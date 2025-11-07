import pypsa
import numpy as np
import pandas as pd
from shapely.geometry import Point
import os


def dc_links_modifications_power_distr(n, dc_flows_df):
    # Mapping of old link names to new ones
    rename_map = {
        "relation/8184632-500-DC": "Skagerak",
        "relation/3391954-500-DC": "Fenno-Skan 2",
        "relation/8184629-300-DC": "Konti-Skan",
        "relation/5487095-400-DC": "Storebaelt",
        "relation/8184631-400-DC": "Fenno-Skan 1"
    }

    # Rename all links at once
    n.links = n.links.rename(index=rename_map)

    # Update Skagerak capacity
    n.links.loc["Skagerak", "p_nom"] = 1634
    
    #Reversing Fenno-Skan 1 to the same convention as Fenno-Skan 2
    link_name = "Fenno-Skan 1"
    bus0_old = n.links.at[link_name, "bus0"]
    bus1_old = n.links.at[link_name, "bus1"]
    n.links.at[link_name, "bus0"] = bus1_old
    n.links.at[link_name, "bus1"] = bus0_old

    #dc_flows_df
    #print(n.links)
    dc_flows_df_mapping = {
        "DE_LU<->DK_2": "Kontek",
        "DE_LU<->NO_2": "NordLink",
        "DE_LU<->SE_4": "Baltic Cable", 
        "DK_1<->NO_2": "Skagerak",
        "EE<->FI": "Estlink",
        "FI<->SE_3": "Fenno-Skan 2",
        "GB<->NO_2": "North Sea Link",
        "LT<->SE_4": "NordBalt",
        "NL<->NO_2": "NorNed",
        "PL<->SE_4": "SwePol Link",
        "DK_1<->SE_3": "Konti-Skan",
        "DK_1<->DK_2": "Storebaelt"
        #"SE_3<->SE_4":"relation/8184633-300-DC" Cross border physical flow for this link is infeasible to determine, as ENTSO only provides the total flow between bidding zones. Ignore for now.
    }

    dc_flows_df = dc_flows_df.rename(columns=dc_flows_df_mapping)
    #dc_flows_df

    #Assigning load to DC links
    n.links_t.p_set = n.links_t.p_set.reindex(
        columns=n.links.index, fill_value=0.0
    )
    for col in dc_flows_df.columns:
        if col in n.links.index:
            n.links_t.p_set[col] = dc_flows_df[col]
        else:
            print(f"Column {col} not found in network links.")

    try:
        n.remove("Link", "relation/3391931-350-DC")
    except KeyError:
        print("Link 'relation/3391931-350-DC' not found in network or is already removed.")
    except Exception as e:
        print(f"An error occurred while removing link: {e}")

    print("relation/3391931-350-DC" in n.links.index)

    #Assigning DC links flow
    n.links_t.p_set = n.links_t.p_set.reindex(
        columns=n.links.index, fill_value=0.0
    )
    for col in dc_flows_df.columns:
        if col in n.links.index:
            n.links_t.p_set[col] = dc_flows_df[col]
        else:
            print(f"Column {col} not found in network links.")

        #Complains about columns not exsisting. We don't use the cables listed, so we can remove them from the mapping, and also from the API call if they are included there. 

    n.links_t.p_set["Fenno-Skan 1"] = (1-0.67) * n.links_t.p_set["Fenno-Skan 2"] #Assigning 33% of the load to Fenno-Skan 1
    n.links_t.p_set["Fenno-Skan 2"] = n.links_t.p_set["Fenno-Skan 2"] - n.links_t.p_set["Fenno-Skan 1"] #Assigning the remaning load to Fenno-Skan 2

    #n.links
    return