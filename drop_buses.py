# Fjern busser med carrier h2/battery + alt som er koblet til dem
def drop_buses(n):
    B = set(n.buses.index[n.buses["carrier"].astype(str).str.lower().isin({"h2","battery"})])

    for comp, tbl, cols in [
        ("Store","stores",["bus"]),
        ("Link","links",["bus0","bus1","bus2","bus3"]),
    ]:
        df = getattr(n, tbl, None)
        if df is None or df.empty: 
            continue
        use = [c for c in cols if c in df.columns]
        if not use:
            continue
        idx = df.index[df[use].isin(B).any(axis=1)]
        if len(idx):
            n.remove(comp, idx.tolist())

    if B:
        n.remove("Bus", list(B))
    return n