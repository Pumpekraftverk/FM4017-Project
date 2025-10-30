import pandas as pd
import numpy as np

def loading_lines_and_links_relative_quantified(n, snapshot_number=17, number_of_displayed_links=100, number_of_displayed_lines=100):
    snap = n.snapshots[snapshot_number]

    # AC line loading
    p0_lines = n.lines_t.p0.loc[snap]
    s_nom_lines = n.lines.s_nom.replace(0, np.nan)
    loading_lines = np.abs(p0_lines) / s_nom_lines * 100

    # HVDC link loading
    p0_links = n.links_t.p0.loc[snap]
    p_nom_links = n.links.p_nom.replace(0, np.nan)
    loading_links = np.abs(p0_links) / p_nom_links * 100


    print("\n=== Zero Loaded Components ===")

    zero_lines = loading_lines[(loading_lines == 0) | loading_lines.isna()]
    zero_links = loading_links[(loading_links == 0) | loading_links.isna()]

    print(f"Zero-loaded AC Lines: {len(zero_lines)}")
    print(f"Zero-loaded HVDC Links: {len(zero_links)}")


    print("\n=== AC Lines loading %===")
    least_lines = loading_lines.sort_values().head(number_of_displayed_lines)
    result_lines = pd.concat([
        n.lines.loc[least_lines.index, ["bus0", "bus1"]],
        least_lines.rename("loading_percent")
    ], axis=1)
    print(result_lines)


    print("\n=== HVDC Links loading % ===")
    least_links = loading_links.sort_values().head(number_of_displayed_links)
    result_links = pd.concat([
        n.links.loc[least_links.index, ["bus0", "bus1"]],
        least_links.rename("loading_percent")
    ], axis=1)
    print(result_links)
    return