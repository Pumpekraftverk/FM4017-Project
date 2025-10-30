#Code trying to compute production share per generator per technology per bidding zone
def production_weight(n):
    gen = n.generators.copy()

    gen["Zone"] = gen["zone"].astype(str)
    gen["Tech"] = gen["carrier"].astype(str).str.lower().str.strip()

    # Total p_nom in each (Zone,Tech)
    cap_zone_tech = (
        gen.groupby(["Zone", "Tech"])["p_nom"]
        .sum()
        .rename("total_zone_tech")
    )

    # Lookup the matching total per generator in the same order
    totals = gen.set_index(["Zone", "Tech"]).index.map(cap_zone_tech)

    # Compute production share
    gen["production_share"] = gen["p_nom"] / totals.values

    # Write back into network
    n.generators["production_share"] = gen["production_share"]
    return n

def storage_weight(n):
    gen = n.storage_units.copy()

    gen["Zone"] = gen["zone"].astype(str)
    gen["Tech"] = gen["carrier"].astype(str).str.lower().str.strip()

    # Total p_nom in each (Zone,Tech)
    cap_zone_tech = (
        gen.groupby(["Zone", "Tech"])["p_nom"]
        .sum()
        .rename("total_zone_tech")
    )

    # Lookup the matching total per generator in the same order
    totals = gen.set_index(["Zone", "Tech"]).index.map(cap_zone_tech)

    # Compute production share
    gen["production_share"] = gen["p_nom"] / totals.values

    # Write back into network
    n.storage_units["production_share"] = gen["production_share"]
    return n