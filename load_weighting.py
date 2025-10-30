def load_weight(n, snapshot_number = 16):
    snapshot = n.snapshots[16]

    # Load per bus
    bus_load = n.loads_t.p_set.loc[snapshot].fillna(0.0)

    # Zone per bus
    bus_zone = n.loads["zone"].astype(str)

    # Total zone load
    zone_total = bus_load.groupby(bus_zone).sum()

    # Share for each bus
    bus_load_share = bus_load / zone_total[bus_zone].to_numpy()

    # Add share as new column in n.buses
    n.buses["load_share"] = bus_load_share.reindex(n.buses.index).fillna(0.0)

    return n
    