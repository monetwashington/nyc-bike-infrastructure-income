"""Select existing routes explicitly coded Protected in either direction."""
import json
import geopandas as gpd
from project_common import sources, OUT, FACILITY_FIELDS, PROJECTED_CRS, FEET_PER_MILE, read_spatial, save_geojson

_, _, bike_path = sources()
bikes = gpd.read_file(bike_path)
if bikes.crs is None:
    raise ValueError('Bike CRS missing')
fields = [c for c in FACILITY_FIELDS if c in bikes]
if not fields or 'status' not in bikes:
    raise ValueError('Inspect changed bike schema before selecting protection categories.')
protected = bikes[fields].apply(lambda col: col.str.strip().eq('Protected')).any(axis=1)
current = bikes.status.str.strip().eq('Current')
missing_geometry = bikes.geometry.isna() | bikes.geometry.is_empty
bikes.loc[missing_geometry].drop(columns='geometry').to_csv(OUT / 'bike_records_without_geometry.csv', index=False)
selected = bikes.loc[current & protected & ~missing_geometry].copy().to_crs(read_spatial(OUT / 'nyc_tracts_income.geojson').crs)
bad = ~selected.geometry.is_valid
selected.loc[bad, 'geometry'] = selected.loc[bad, 'geometry'].make_valid()
assert selected.geom_type.isin(['LineString', 'MultiLineString']).all()
projected = selected.to_crs(PROJECTED_CRS)
stats = {'total_records': len(bikes), 'current_records': int(current.sum()),
         'records_without_geometry': int(missing_geometry.sum()),
         'protected_records_without_geometry': int((current & protected & missing_geometry).sum()),
         'protected_records': len(selected), 'categories_included': ['Protected'],
         'facility_fields': fields,
         'record_length_miles': float(projected.length.sum() / FEET_PER_MILE),
         'unique_route_miles': float(projected.geometry.union_all().length / FEET_PER_MILE)}
save_geojson(selected, 'protected_bike_lanes.geojson')
(OUT / '03_protected_report.json').write_text(json.dumps(stats, indent=2))
print(json.dumps(stats, indent=2))
print('Only Current records explicitly marked Protected; each geometry counted once regardless of directions.')
