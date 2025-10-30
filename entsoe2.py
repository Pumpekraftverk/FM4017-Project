# fetch_entsoe.py
# pip install entsoe-py pandas
import os, pandas as pd
from entsoe import EntsoePandasClient

ZONES = ["NO_1","NO_2","NO_3","NO_4","NO_5","FI","SE_1","SE_2","SE_3","SE_4","DK_2"]

AC_BORDERS = [
    ("NO_1","NO_2"), ("NO_1","NO_5"), ("NO_1","SE_3"), ("NO_1","NO_3"),
    ("NO_2","NO_5"), ("NO_3","NO_4"), ("NO_3","NO_5"), ("NO_3","SE_2"),
    ("NO_4","SE_1"), ("NO_4","SE_2"), ("SE_1","SE_2"), ("SE_2","SE_3"),
    ("SE_3","SE_4"), ("DK_2","SE_4"),
]
DC_BORDERS = [
    ("SE_3","FI"), ("NO_2","DK_1"), ("NO_2","NL"), ("NO_2","DE_LU"), ("NO_2","GB"),
    ("DK_1","NL"), ("DK_1","GB"), ("DK_2","DE_LU"), ("DK_1", "SE_3"),
    ("SE_4","DE_LU"), ("SE_4","LT"), ("SE_4","PL"), ("FI","EE"), ("SE_3","SE_4"), ("DK_1", "DK_2")
]

def fetch_entsoe_data(start_date, timezone="Europe/Oslo", api_key=None,
                      zones=None, ac_borders=None, dc_borders=None, save_csv=False):
    zones = zones or ZONES
    ac = sorted({tuple(sorted(p)) for p in (ac_borders or AC_BORDERS)})
    dc = sorted({tuple(sorted(p)) for p in (dc_borders or DC_BORDERS)})

    api_key = api_key or os.getenv("ENTSOE_API_TOKEN")
    if not api_key: raise RuntimeError("Set ENTSOE_API_TOKEN or pass api_key")
    c = EntsoePandasClient(api_key=api_key)

    # 24h window from local midnight
    t0 = pd.Timestamp(f"{start_date} 00:00", tz=timezone).tz_convert("UTC")
    t1 = t0 + pd.Timedelta(days=1)

    loads, gen_cols = {}, {}
    ac_flows, dc_flows = {}, {}

    # Loads + Generation (Zone first, Technology second)
    for z in zones:
        try:
            s = c.query_load(z, start=t0, end=t1).squeeze()
            if not s.empty: loads[z] = s.resample("h").mean()
        except Exception: pass

        try:
            g = c.query_generation(z, start=t0, end=t1)
            if isinstance(g, pd.Series): g = g.to_frame("Unknown")
            if not g.empty:
                g = g.resample("h").mean()
                for tech in g.columns:
                    gen_cols[(z, tech)] = g[tech]     # <-- Zone first
        except Exception: pass

    # Helper: net flow A->B = (A->B) - (B->A)
    def fetch_pairs(pairs):
        out = {}
        for a, b in pairs:
            try:
                f = c.query_crossborder_flows(a, b, start=t0, end=t1).squeeze()
                r = c.query_crossborder_flows(b, a, start=t0, end=t1).squeeze()
                s = (f - r).resample("h").mean()
                if not s.empty: out[f"{a}<->{b}"] = s
            except Exception: pass
        return out

    ac_flows = fetch_pairs(ac)
    dc_flows = fetch_pairs(dc)

    # Build DataFrames (UTC -> local, drop tz)
    def to_wide(d, name):
        if not d: return None
        df = pd.DataFrame(d).sort_index().fillna(0.0)
        df.index = df.index.tz_convert(timezone).tz_localize(None)
        df.index.name, df.columns.name = "Snapshot", name
        return df

    loads_df    = to_wide(loads, "Zone")
    ac_flows_df = to_wide(ac_flows, "AC interconnector")
    dc_flows_df = to_wide(dc_flows, "DC interconnector")

    gen_df = None
    if gen_cols:
        gen_df = pd.concat(gen_cols, axis=1)
        gen_df.index = gen_df.index.tz_convert(timezone).tz_localize(None)
        gen_df.index.name = "Snapshot"
        gen_df.columns = pd.MultiIndex.from_tuples(gen_df.columns, names=["Zone","Technology"])
        gen_df = gen_df.sort_index(axis=1)

    if save_csv:
        tag = start_date
        if loads_df    is not None: loads_df.to_csv(f"loads_{tag}.csv")
        if gen_df      is not None: gen_df.to_csv(f"generation_zone-tech_{tag}.csv")
        if ac_flows_df is not None: ac_flows_df.to_csv(f"flows_ac_{tag}.csv")
        if dc_flows_df is not None: dc_flows_df.to_csv(f"flows_dc_{tag}.csv")

    return loads_df, gen_df, ac_flows_df, dc_flows_df

if __name__ == "__main__":
    L, G, AC, DC = fetch_entsoe_data("2023-01-01")
    for title, df in [("Loads", L), ("Gen (Zone,Tech)", G), ("AC flows", AC), ("DC flows", DC)]:
        print(f"\n=== {title} ===")
        print(df.head() if df is not None else "No data")
