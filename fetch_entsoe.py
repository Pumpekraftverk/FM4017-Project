# fetch_entsoe.py
# pip install entsoe-py pandas

import os
import pandas as pd
from entsoe import EntsoePandasClient
from entsoe.exceptions import NoMatchingDataError

ZONES = ["NO_1","NO_2","NO_3","NO_4","NO_5","FI","SE_1","SE_2","SE_3","SE_4","DK_2"]

BORDERS = [
    # AC inside Nordics
    ("NO_1","NO_2"), ("NO_1","NO_5"), ("NO_1","SE_3"), ("NO_1","NO_3"),
    ("NO_2","NO_5"),
    ("NO_3","NO_4"), ("NO_3","NO_5"), ("NO_3","SE_2"),
    ("NO_4","SE_1"), ("NO_4","SE_2"),
    ("SE_1","SE_2"), ("SE_2","SE_3"), ("SE_3","SE_4"), ("DK_2","SE_4"),
    # DC links (ENTSO-E zone codes)
    ("SE_3","FI"), ("NO_2","DK_1"), ("NO_2","NL"), ("NO_2","DE_LU"), ("NO_2","GB"),
    ("DK_1","NL"), ("DK_1","GB"), ("DK_2","DE_LU"),
    ("SE_4","DE_LU"), ("SE_4","LT"), ("SE_4","PL"), ("FI","EE"),
]

def fetch_entsoe_data(start_date: str, timezone: str = "Europe/Oslo",
                      api_key: str | None = None,
                      zones: list[str] | None = None,
                      borders: list[tuple[str,str]] | None = None,
                      save_csv: bool = False):
    """Fetch 24h from local midnight: loads (Zone), gen by (Tech, Zone), flows (A<->B)."""
    zones = zones or ZONES
    borders = sorted({tuple(sorted(p)) for p in (borders or BORDERS)})  # dedupe A/B vs B/A
    api_key = api_key or os.getenv("ENTSOE_API_TOKEN")
    if not api_key:
        raise RuntimeError("Set ENTSOE_API_TOKEN or pass api_key")

    # window [start, start+24h) in UTC
    t0 = pd.Timestamp(f"{start_date} 00:00", tz=timezone).astimezone("UTC")
    t1 = t0 + pd.Timedelta(days=1)

    c = EntsoePandasClient(api_key=api_key)
    loads, flows, gen_cols = {}, {}, {}  # {(tech, zone): Series} for gen_cols

    for z in zones:
        # LOADS (MW)
        try:
            s = c.query_load(z, start=t0, end=t1)
            s = s.squeeze() if isinstance(s, pd.DataFrame) else s
            if not s.empty: loads[z] = s.resample("h").mean()
        except (NoMatchingDataError, Exception):
            pass

        # GENERATION by technology (MW)
        try:
            g = c.query_generation(z, start=t0, end=t1)   # columns = tech
            if isinstance(g, pd.Series): g = g.to_frame("Unknown")
            if not g.empty:
                g = g.resample("h").mean()
                for tech in g.columns:
                    gen_cols[(tech, z)] = g[tech]
        except (NoMatchingDataError, Exception):
            pass

    # FLOWS (MW), net = a->b minus b->a
    for a, b in borders:
        col = f"{a}<->{b}"
        try:
            fwd = c.query_crossborder_flows(a, b, start=t0, end=t1)
            rev = c.query_crossborder_flows(b, a, start=t0, end=t1)
            fwd = fwd.squeeze() if isinstance(fwd, pd.DataFrame) else fwd
            rev = rev.squeeze() if isinstance(rev, pd.DataFrame) else rev
            net = (fwd - rev).resample("h").mean()
            if not net.empty: flows[col] = net
        except (NoMatchingDataError, Exception):
            pass

    # --- build DataFrames (convert UTC -> local, drop tz) ---
    def wide(d, name):
        if not d: return None
        df = pd.DataFrame(d).sort_index().fillna(0.0)
        df.index = df.index.tz_convert(timezone).tz_localize(None)
        df.index.name, df.columns.name = "Snapshot", name
        return df

    loads_df = wide(loads, "Zone")
    flows_df = wide(flows, "Interconnector")

    if gen_cols:
        gen_df = pd.concat(gen_cols, axis=1)
        gen_df.index = gen_df.index.tz_convert(timezone).tz_localize(None)
        gen_df.index.name = "Snapshot"
        gen_df.columns = pd.MultiIndex.from_tuples(gen_df.columns, names=["Technology","Zone"])
        gen_df = gen_df.sort_index(axis=1)
    else:
        gen_df = None

    if save_csv:
        tag = start_date
        if loads_df is not None: loads_df.to_csv(f"loads_{tag}.csv")
        if gen_df   is not None: gen_df.to_csv(f"generation_by_tech_zone_{tag}.csv")
        if flows_df is not None: flows_df.to_csv(f"flows_{tag}.csv")

    return loads_df, gen_df, flows_df

if __name__ == "__main__":
    L, G, F = fetch_entsoe_data("2025-09-01")
    for title, df in [("Loads", L), ("Gen by Tech/Zone", G), ("Flows", F)]:
        print(f"\n=== {title} ===")
        print(df.head() if df is not None else "No data")
