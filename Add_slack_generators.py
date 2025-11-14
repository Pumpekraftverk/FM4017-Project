import pypsa
import numpy as np
import pandas as pd
from shapely.geometry import Point

def add_slack_generators(n, nordic_slack_bus = 'SE1 16', nordic_slack_name = f"slack_Forsmark"):
    # Coordinatees to buses is found in OSM as the GPS coordinates to static inverter plants related to the DC links
    n.add("Carrier", "other")
    n.add("Carrier", "slack")
    add_countries = {
        "DE": {"name": "Germany", "y": 54.07611776227856, "x": 10.02805057158303},
        "NL": {"name": "Netherlands", "y": 53.434444, "x": 6.865833},
        "GB": {"name": "Great Britain", "y": 55.1506, "x": -1.5510},
        "PL": {"name": "Poland", "y": 54.502111, "x": 16.891222},
        "LT": {"name": "Lithuania", "y": 55.681667, "x": 21.256667},
        "EE": {"name": "Estonia", "y": 59.384722, "x": 24.560278},
    }
    #, 9.3425
    # Add Nordic sync grid buses using loop
    for country_code, data in add_countries.items():
        n.add(
            "Bus",
            name=country_code,
            v_nom=380,
            y=data["y"],
            x=data["x"],
            carrier="AC"
            
        )
        n.add(
            "Generator",
            name=f"slack_{country_code}",
            bus=country_code,
            carrier="slack",
            control="Slack"
        )

    print(" Added buses:", list(add_countries.keys()))

    n.add("Generator",
            name = nordic_slack_name,
            bus = nordic_slack_bus,
            p_nom=1e6,
            marginal_cost=200,
            carrier = "slack",
            control = "Slack")
    print("Added {} to Nordic area at bus {}".format(nordic_slack_name, nordic_slack_bus))
    return
    # Slack gen should perhaps be added to "SE1 7" instead. Forsmark is located somewhere between these to nodes, but it seems the actual generator is per now connected to SE1 7. Discuss in group 