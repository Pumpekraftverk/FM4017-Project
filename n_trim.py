def drop_buses(n, carriers=("h2","battery"), dry_run=False):
    buses = n.buses.index[n.buses["carrier"].astype(str).str.lower()
             .isin({str(c).lower() for c in carriers})].tolist()
    bset = set(buses)

    for comp, tbl, cols in [
        ("Generator","generators",["bus"]),
        ("Load","loads",["bus"]),
        ("Store","stores",["bus"]),
        ("StorageUnit","storage_units",["bus"]),
        ("Link","links",["bus0","bus1","bus2","bus3"]),
        ("Line","lines",["bus0","bus1"]),
        ("Transformer","transformers",["bus0","bus1"]),
        ("ShuntImpedance","shunt_impedances",["bus"]),
    ]:
        df = getattr(n, tbl, None)
        if df is None or df.empty: 
            continue
        use = [c for c in cols if c in df.columns]
        if not use:
            continue
        names = df.index[df[use].isin(bset).any(axis=1)].tolist()
        if names:
            print(("Vil fjerne" if dry_run else "Fjerner"), comp, f"({len(names)}):", names)
            if not dry_run:
                n.mremove(comp, names)

    if buses:
        print(("Vil fjerne" if dry_run else "Fjerner"), "Bus", f"({len(buses)}):", buses)
        if not dry_run:
            n.mremove("Bus", buses)
    else:
        print("Ingen Bus.")
