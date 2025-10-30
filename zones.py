def assign_zones(n, zones_path="bidding_zones.geojson"):
    import geopandas as gpd

    # read zones + choose name column
    zones = gpd.read_file(zones_path)
    zone_col = next(c for c in ("zone_name","name","bzn_name") if c in zones.columns)

    # buses → GeoDataFrame (assumes lon/lat), project to zones CRS
    bus = gpd.GeoDataFrame(n.buses.copy(),
                           geometry=gpd.points_from_xy(n.buses.x, n.buses.y),
                           crs="EPSG:4326").to_crs(zones.crs)

    # within-join, then nearest for misses (in metric CRS)
    z = gpd.sjoin(bus, zones[[zone_col,"geometry"]], how="left", predicate="within")[zone_col]
    miss = z.isna() | (z.astype(str).str.strip()=="")
    if miss.any():
        jn = gpd.sjoin_nearest(
            bus.loc[miss].to_crs("EPSG:3035"),
            zones.to_crs("EPSG:3035")[[zone_col,"geometry"]],
            how="left"
        )[zone_col]
        z.loc[miss] = jn.values

    # mapping
    fix = {
        "NOS1":"NO_1","NOS2":"NO_2","NOM1":"NO_3","NON1":"NO_4","NOS5":"NO_5",
        "SE01":"SE_1","SE02":"SE_2","SE03":"SE_3","SE04":"SE_4",
        "FI00":"FI","DKE1":"DK_2","DKW1":"DK_1",
        "NL00":"NL","DE00":"DE_LU","EE00":"EE","LT00":"LT","PL00":"PL","GB00":"GB","GBNI":"GB",
    }
    z = z.replace(fix)

    # write back + propagate
    n.buses["zone"] = z.values
    # map helper to avoid KeyError when a component lacks a 'bus' column
    def _map_component_zone(component_df, bus_column="bus"):
        if component_df is None:
            return
        if getattr(component_df, "empty", True):
            return
        if bus_column in component_df.columns:
            component_df["zone"] = component_df[bus_column].map(n.buses["zone"])  # type: ignore[index]

    _map_component_zone(n.generators, "bus")
    _map_component_zone(n.storage_units, "bus")
    _map_component_zone(n.loads, "bus")
    # also map for stores if present in the network
    if hasattr(n, "stores"):
        _map_component_zone(n.stores, "bus")
    
    return n
