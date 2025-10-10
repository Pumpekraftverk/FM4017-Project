def nordic(n, nord=("NO","SE","FI","DK"), drop_h2_batt=False, extra_buses=()):
    import numpy as np, pandas as pd

    def _drop_buses_and_attachments(n, buses):
        buses = pd.Index(buses).intersection(n.buses.index)
        if len(buses) == 0: 
            return
        for comp, cols in [
            ("Line",        ["bus0","bus1"]),
            ("Transformer", ["bus0","bus1"]),
            ("Link",        ["bus0","bus1","bus2","bus3"]),
            ("Generator",   ["bus"]),
            ("Load",        ["bus"]),
            ("Store",       ["bus"]),
            ("StorageUnit", ["bus"]),
        ]:
            df = getattr(n, comp.lower()+"s", None)
            if df is not None and not df.empty:
                use = [c for c in cols if c in df.columns]
                if use:
                    n.remove(comp, df.index[df[use].isin(buses).any(axis=1)])
        n.remove("Bus", buses)

    # --- finn nordisk sync-ID fra bussnavn "SE0...", "DK1..." ---
    idx  = n.buses.index.astype(str)
    sync = pd.Series(idx.str[2], index=n.buses.index)
    cntr = pd.Series(idx.str[:2], index=n.buses.index)
    syncN = sync[cntr.isin(nord)].value_counts().idxmax()

    # --- AC: behold bare linjer helt inne i nordisk sync ---
    keep_ac = (sync.reindex(n.lines.bus0).to_numpy() == syncN) & \
              (sync.reindex(n.lines.bus1).to_numpy() == syncN)
    n.remove("Line", n.lines.index[~keep_ac])

    # --- DC: fjern linker som ikke berører nordisk sync (reindex unngår KeyError) ---
    is_dc = n.links.get("carrier","").astype(str).str.contains("DC", case=False, na=False) if "carrier" in n.links.columns else pd.Series(False, index=n.links.index)
    touches = np.zeros(len(n.links), dtype=bool)
    for c in ("bus0","bus1","bus2","bus3"):
        if c in n.links.columns:
            touches |= (sync.reindex(n.links[c]).to_numpy() == syncN)
    n.remove("Link", n.links.index[is_dc & ~touches])

    # --- valgfritt: fjern alle H2/battery-busser + alt som henger på dem ---
    if drop_h2_batt and "carrier" in n.buses.columns:
        h2b = n.buses.index[n.buses["carrier"].astype(str).str.lower().isin(["h2","battery"])]
        _drop_buses_and_attachments(n, h2b)

    # --- valgfritt: fjern oppgitte ekstra busser + alt som henger på dem ---
    if extra_buses:
        _drop_buses_and_attachments(n, extra_buses)

    return n
