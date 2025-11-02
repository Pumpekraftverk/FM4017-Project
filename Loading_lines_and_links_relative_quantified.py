import pandas as pd
import numpy as np

def loading_lines_and_links_relative_quantified(
    n,
    snapshot_number=17,
    number_of_displayed_links=100,
    number_of_displayed_lines=100
):
    snap = n.snapshots[snapshot_number]

    # === AC lines ===
    p0_lines = n.lines_t.p0.loc[snap]
    s_nom_lines = n.lines.s_nom.replace(0, np.nan)
    loading_lines_pct = np.abs(p0_lines) / s_nom_lines * 100
    loading_lines_mw = np.abs(p0_lines)

    # === HVDC links ===
    p0_links = n.links_t.p0.loc[snap]
    p_nom_links = n.links.p_nom.replace(0, np.nan)
    loading_links_pct = np.abs(p0_links) / p_nom_links * 100
    loading_links_mw = np.abs(p0_links)

    # === Zero-load diagnostics ===
    print("\n=== Zero Loaded Components ===")
    print(f"Zero-loaded AC Lines: {(loading_lines_pct == 0).sum()}")
    print(f"Zero-loaded HVDC Links: {(loading_links_pct == 0).sum()}")

    # === Build result DataFrames ===
    result_lines = pd.concat([
        n.lines[["bus0", "bus1"]],
        loading_lines_pct.rename("loading_percent"),
        loading_lines_mw.rename("loading_MW"),
        s_nom_lines.rename("rated_capacity_MW"),
    ], axis=1).assign(type="AC Line")

    result_links = pd.concat([
        n.links[["bus0", "bus1"]],
        loading_links_pct.rename("loading_percent"),
        loading_links_mw.rename("loading_MW"),
        p_nom_links.rename("rated_capacity_MW"),
    ], axis=1).assign(type="HVDC Link")

    # === Sort by highest loading ===
    result_lines = result_lines.sort_values("loading_percent", ascending=False)
    result_links = result_links.sort_values("loading_percent", ascending=False)

    # === Reorder columns (loading first after name) ===
    col_order = ["bus0", "bus1", "loading_percent", "loading_MW", "rated_capacity_MW", "type"]
    result_lines = result_lines[col_order]
    result_links = result_links[col_order]

    print("\n=== Most Loaded AC Lines ===")
    print(result_lines.head(number_of_displayed_lines))
    print("\n=== Most Loaded HVDC Links ===")
    print(result_links.head(number_of_displayed_links))

    # Combine for export if desired
    #combined = pd.concat([result_lines, result_links], axis=0)

    return 
