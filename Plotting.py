import pypsa
import numpy as np
import pandas as pd
from shapely.geometry import Point
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import geopandas as gpd
def plot_network_with_loadings(n, snapshot_number=17):
    snap = n.snapshots[snapshot_number]

    # AC line loading
    p0_lines = n.lines_t.p0.loc[snap]
    s_nom_lines = n.lines.s_nom.replace(0, np.nan)
    loading_lines = np.abs(p0_lines) / s_nom_lines * 100

    # DC link loading
    p0_links = n.links_t.p0.loc[snap]
    p_nom_links = n.links.p_nom.replace(0, np.nan)
    loading_links = np.abs(p0_links) / p_nom_links * 100

    # Separate colormaps and normalizations
    norm_ac = plt.Normalize(vmin=0, vmax=np.nanmax(loading_lines))
    norm_dc = plt.Normalize(vmin=0, vmax=np.nanmax(loading_links))

    cmap_ac = plt.get_cmap("viridis")
    cmap_dc = plt.get_cmap("plasma")

    line_colors = pd.Series(
        list(cmap_ac(norm_ac(loading_lines))),
        index=loading_lines.index
    )

    link_colors = pd.Series(
        list(cmap_dc(norm_dc(loading_links))),
        index=loading_links.index
    )

    fig, ax = plt.subplots(
        figsize=(12, 10),
        subplot_kw={"projection": ccrs.PlateCarree()}
    )

    n.plot(
        ax=ax,
        bus_colors="gray",
        line_colors=line_colors,
        line_widths=2.0,
        link_colors=link_colors,
        link_widths=3.5,
        title=f"AC & DC Loading ({snap})"
    )

    # Load and plot bidding zones boundaries
    zones_gdf = gpd.read_file("bidding_zones.geojson")
    zones_gdf.plot(ax=ax, edgecolor="black", facecolor="none", linewidth=1)


    # ============================================
    # AC Flow Arrows
    # ============================================
    for line in n.lines.index:
        p = p0_lines[line]
        if np.isnan(p) or p == 0:
            continue

        bus0 = n.lines.at[line, "bus0"]
        bus1 = n.lines.at[line, "bus1"]
        x0, y0 = n.buses.at[bus0, "x"], n.buses.at[bus0, "y"]
        x1, y1 = n.buses.at[bus1, "x"], n.buses.at[bus1, "y"]

        if p > 0:
            start_x, start_y = (x0 + (x1-x0)/3), (y0 + (y1-y0)/3)  # Start arrow at midpoint
            dx, dy = x1 - x0, y1 - y0
        else:
            start_x, start_y = (x1 - (x1-x0)/3), (y1 - (y1-y0)/3)  # Start arrow at midpoint
            dx, dy = (x0 - x1) , (y0 - y1) 

        scale = np.abs(p) / np.nanmax(np.abs(p0_lines))

        ax.arrow(
            start_x, start_y,
            dx * 0.15 * scale, dy * 0.15 * scale,
            head_width=0.2,
            head_length=0.3,
            fc="black",
            ec="black",
            transform=ccrs.PlateCarree(),
            alpha=0.65,    # lighter and less bold than DC
            zorder=9       # below DC arrows
        )


    # ============================================
    # DC Flow Arrows
    # ============================================
    for link in n.links.index:
        p = p0_links[link]
        if np.isnan(p) or p == 0:
            continue
        
        bus0 = n.links.at[link, "bus0"]
        bus1 = n.links.at[link, "bus1"]
        x0, y0 = n.buses.at[bus0, "x"], n.buses.at[bus0, "y"]
        x1, y1 = n.buses.at[bus1, "x"], n.buses.at[bus1, "y"]
        
        if p > 0:
            start_x, start_y = (x0 + (x1-x0)/3), (y0 + (y1-y0)/3)  # Start arrow at midpoint
            dx, dy = x1 - x0, y1 - y0
        else:
            start_x, start_y = (x1 - (x1-x0)/3), (y1 - (y1-y0)/3)  # Start arrow at midpoint
            dx, dy = (x0 - x1) , (y0 - y1) 
        
        scale = np.abs(p) / np.nanmax(np.abs(p0_links))
        
        ax.arrow(
            start_x, start_y,
            dx * 0.2 * scale, dy * 0.2 * scale,
            head_width=0.3,
            head_length=0.4,
            fc="black",
            ec="black",
            transform=ccrs.PlateCarree(),
            alpha=0.95,
            zorder=10
        )


    # Colorbars
    sm_ac = plt.cm.ScalarMappable(cmap=cmap_ac, norm=norm_ac)
    sm_ac._A = []
    cbar_ac = plt.colorbar(sm_ac, ax=ax, fraction=0.046, pad=0.04)
    cbar_ac.set_label("AC line loading [%]")

    sm_dc = plt.cm.ScalarMappable(cmap=cmap_dc, norm=norm_dc)
    sm_dc._A = []
    cbar_dc = plt.colorbar(sm_dc, ax=ax, fraction=0.046, pad=0.08)
    cbar_dc.set_label("HVDC link loading [%]")

    plt.show()
    return