"""Intersect unique protected linework with shoreline-clipped tract polygons."""
import json
import numpy as np
import geopandas as gpd
from project_common import OUT, PROJECTED_CRS, FEET_PER_MILE, read_spatial, save_geojson

tracts = read_spatial(OUT / 'nyc_tracts_income.geojson').to_crs(PROJECTED_CRS)
lanes = read_spatial(OUT / 'protected_bike_lanes.geojson').to_crs(PROJECTED_CRS)
# Union removes exactly overlapping records and direction duplication, without snapping.
network = lanes.geometry.union_all()
unique_lines = gpd.GeoDataFrame(geometry=[network], crs=PROJECTED_CRS).explode(index_parts=False).reset_index(drop=True)
pieces = gpd.overlay(unique_lines, tracts[['tract_id', 'geometry']], how='intersection', keep_geom_type=True)
pieces['miles'] = pieces.length / FEET_PER_MILE
lengths = pieces.groupby('tract_id').miles.sum()
tracts['protected_lane_miles'] = tracts.tract_id.map(lengths).fillna(0)
# DCP's supplied 2020 tract dataset is clipped to the shoreline. Polygon area
# is our land-area proxy, not the Census ALAND attribute (absent from this file).
tracts['tract_area_sqmi'] = tracts.area / FEET_PER_MILE**2
assert (tracts.tract_area_sqmi > 0).all()
tracts['protected_lane_miles_per_sqmi'] = tracts.protected_lane_miles / tracts.tract_area_sqmi
tracts['has_protected_lane'] = (tracts.protected_lane_miles > 0).astype(int)
inside_miles = network.intersection(tracts.geometry.union_all()).length / FEET_PER_MILE
stats = {'projected_crs': PROJECTED_CRS, 'tracts': len(tracts),
         'tracts_with_protected_lane': int(tracts.has_protected_lane.sum()),
         'land_area_proxy_sqmi': float(tracts.tract_area_sqmi.sum()),
         'summed_tract_miles': float(tracts.protected_lane_miles.sum()),
         'unique_miles_inside_tracts': float(inside_miles),
         'unique_miles_outside_tracts': float(network.length / FEET_PER_MILE - inside_miles),
         'shared_boundary_extra_miles': float(tracts.protected_lane_miles.sum() - inside_miles)}
assert np.isfinite(tracts.protected_lane_miles_per_sqmi).all()
assert (tracts.protected_lane_miles >= 0).all()
save_geojson(tracts, 'nyc_income_bike_access.geojson')
tracts.drop(columns='geometry').to_csv(OUT / 'nyc_income_bike_access.csv', index=False)
(OUT / '04_access_report.json').write_text(json.dumps(stats, indent=2))
print(json.dumps(stats, indent=2))
print('Boundary lines count for both adjacent tracts when exactly coincident; do not sum tract mileage as network mileage.')
