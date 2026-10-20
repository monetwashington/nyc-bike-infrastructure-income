"""Additional facility-type analysis. Run after scripts 01-05; originals are unchanged."""
import json
import numpy as np
import pandas as pd
import geopandas as gpd
from project_common import OUT, sources, read_spatial, save_geojson, PROJECTED_CRS, FEET_PER_MILE, FACILITY_FIELDS

GROUPS = {
    'Protected': ('protected', ['Protected']),
    'Buffered': ('buffered', ['Conventional Buffered', 'Curbside Buffered']),
    'Conventional / Curbside': ('conventional_curbside', ['Conventional', 'Curbside']),
    'Shared / Signed': ('shared_signed', ['Shared', 'Signed Route', 'Wide Parking Lane']),
    'Other / Off-street': ('other_offstreet', ['Sidewalk', 'Boardwalk', 'Unpaved', 'Link', 'Ped Plaza']),
}

if __name__ == '__main__':
    bikes = gpd.read_file(sources()[2])
    inspection = []
    for field in FACILITY_FIELDS:
        inspection.append(f'{field}:\n{bikes[field].value_counts(dropna=False).to_string()}')
    report = '\n\n'.join(inspection)
    print(report)
    (OUT / '07_facility_values.txt').write_text(report, encoding='utf-8')
    current = bikes.loc[bikes.status.eq('Current')].copy()
    current['source_row'] = current.index
    # Preserve every original directional field; use separate normalized fields for matching.
    labels = current[FACILITY_FIELDS].fillna('').apply(lambda col: col.str.strip())
    known = {label for _, values in GROUPS.values() for label in values}
    observed = set(labels.to_numpy().ravel()) - {''}
    if observed - known:
        raise ValueError(f'Unmapped facility labels: {observed - known}')
    label_sets = labels.apply(lambda row: sorted(set(row) - {''}), axis=1)
    group_sets = label_sets.map(lambda values: [group for group, (_, members) in GROUPS.items() if set(values) & set(members)])
    current['original_facility_labels'] = label_sets.map(json.dumps)
    current['facility_groups'] = group_sets.map(json.dumps)
    current['multiple_facility_types'] = label_sets.map(len).gt(1)
    current['multiple_facility_groups'] = group_sets.map(len).gt(1)
    missing = current.geometry.isna() | current.geometry.is_empty
    current['missing_geometry'] = missing
    current.drop(columns='geometry').to_csv(OUT / 'current_routes_facility_audit.csv', index=False)
    long = current.drop(columns='geometry').melt(id_vars=['source_row','segmentid'], value_vars=FACILITY_FIELDS,
                                                var_name='direction_field', value_name='original_facility_label')
    lookup = {label: group for group, (_, members) in GROUPS.items() for label in members}
    long['facility_group'] = long.original_facility_label.fillna('').str.strip().map(lookup)
    long.to_csv(OUT / 'route_direction_facility_labels.csv', index=False)
    valid = current.loc[~missing].copy()
    bad = ~valid.geometry.is_valid
    valid.loc[bad,'geometry'] = valid.loc[bad,'geometry'].make_valid()
    valid = valid.to_crs(PROJECTED_CRS)
    assert valid.geom_type.isin(['LineString','MultiLineString']).all()
    tracts = read_spatial(OUT / 'nyc_income_bike_access.geojson').to_crs(PROJECTED_CRS)
    # Reuse step 04's input geometry to avoid another CRS/GeoJSON round-trip at boundaries.
    original_tracts = read_spatial(OUT / 'nyc_tracts_income.geojson').to_crs(PROJECTED_CRS).set_index('tract_id')
    tracts['geometry'] = tracts.tract_id.map(original_tracts.geometry)
    edges = json.loads((OUT / '05_relationship_report.json').read_text())['quartile_edges_dollars']
    tracts['income_quartile'] = pd.cut(tracts.median_household_income, edges, labels=['Q1','Q2','Q3','Q4'], include_lowest=True)
    assert tracts.income_quartile.notna().sum() == tracts.median_household_income.notna().sum()
    domain = tracts.geometry.union_all()
    audits, route_groups, summaries = [], [], []
    for group, (stem, members) in GROUPS.items():
        selected = valid.loc[labels.loc[valid.index].isin(members).any(axis=1)].copy()
        selected['facility_group'] = group
        route_groups.append(selected)
        # Union within each category removes repeats from directions and overlapping records.
        network = selected.geometry.union_all()
        if group == 'Protected':
            # Same verified selection, using the exact saved geometry from step 03.
            existing = read_spatial(OUT / 'protected_bike_lanes.geojson').to_crs(PROJECTED_CRS)
            assert len(existing) == len(selected)
            network = existing.geometry.union_all()
        lines = gpd.GeoDataFrame(geometry=[network], crs=PROJECTED_CRS).explode(index_parts=False).reset_index(drop=True)
        pieces = gpd.overlay(lines, tracts[['tract_id','geometry']], how='intersection', keep_geom_type=True)
        pieces['miles'] = pieces.length / FEET_PER_MILE
        tracts[stem+'_miles'] = tracts.tract_id.map(pieces.groupby('tract_id').miles.sum()).fillna(0)
        tracts[stem+'_miles_per_sqmi'] = tracts[stem+'_miles'] / tracts.tract_area_sqmi
        tracts['has_'+stem] = tracts[stem+'_miles'].gt(0).astype(int)
        inside = network.intersection(domain).length / FEET_PER_MILE
        audits.append({'facility_group':group, 'records':len(selected), 'unique_route_miles':network.length/FEET_PER_MILE,
                       'unique_miles_inside_tracts':inside, 'summed_tract_miles':tracts[stem+'_miles'].sum(),
                       'shared_boundary_extra_miles':tracts[stem+'_miles'].sum()-inside})
        summary = tracts.dropna(subset=['income_quartile']).groupby('income_quartile', observed=True).agg(
            number_of_tracts=('tract_id','size'), average_facility_miles=(stem+'_miles','mean'),
            average_facility_miles_per_sqmi=(stem+'_miles_per_sqmi','mean'),
            percent_with_facility=('has_'+stem,lambda s:100*s.mean())).reset_index()
        summary['facility_group'] = group
        summaries.append(summary)
    difference = tracts.protected_miles - tracts.protected_lane_miles
    print('Protected comparison: maximum absolute miles', difference.abs().max(),
          'sum absolute miles', difference.abs().sum())
    assert np.allclose(tracts.protected_miles, tracts.protected_lane_miles, atol=1e-8, rtol=1e-8), 'Protected results changed'
    mileage = tracts[[stem+'_miles' for stem,_ in GROUPS.values()]].to_numpy()
    maximum = mileage.max(axis=1)
    ties = np.isclose(mileage, maximum[:,None], atol=1e-9, rtol=1e-9).sum(axis=1)>1
    tracts['dominant_facility_group'] = np.array(list(GROUPS))[mileage.argmax(axis=1)]
    tracts.loc[ties & (maximum>0),'dominant_facility_group'] = 'Tie: multiple groups'
    tracts.loc[maximum==0,'dominant_facility_group'] = 'No bike infrastructure'
    save_geojson(tracts, 'nyc_income_bike_facility_types.geojson')
    tracts.drop(columns='geometry').to_csv(OUT / 'nyc_income_bike_facility_types.csv', index=False)
    save_geojson(gpd.GeoDataFrame(pd.concat(route_groups, ignore_index=True), crs=PROJECTED_CRS), 'current_bike_routes_by_facility_group.geojson')
    summary = pd.concat(summaries, ignore_index=True)
    summary.to_csv(OUT / 'bike_facility_type_by_income.csv', index=False)
    pd.DataFrame(audits).to_csv(OUT / 'facility_group_mileage_audit.csv', index=False)
    stats = {'current_records':len(current), 'multiple_labels':int(current.multiple_facility_types.sum()),
             'multiple_groups':int(current.multiple_facility_groups.sum()), 'missing_geometry':int(missing.sum()),
             'no_facility_label':int(label_sets.map(len).eq(0).sum()),
             'dominant_counts':tracts.dominant_facility_group.value_counts().to_dict()}
    (OUT / '07_facility_report.json').write_text(json.dumps(stats, indent=2))
    print(json.dumps(stats, indent=2)); print(summary.to_string(index=False))
