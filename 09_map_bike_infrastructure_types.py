"""One contextual map of Current bike routes; original analyses remain unchanged."""
from importlib import import_module
import pandas as pd
import geopandas as gpd
from project_common import OUT, sources, read_spatial, PROJECTED_CRS, FEET_PER_MILE, FACILITY_FIELDS
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

GROUPS = import_module('07_analyze_facility_types').GROUPS
bikes = gpd.read_file(sources()[2])
current = bikes.loc[bikes.status.eq('Current')].copy()
# Keep original directional fields untouched; normalize a separate matching table.
labels = current[FACILITY_FIELDS].fillna('').apply(lambda col: col.str.strip())
known = {label for _, members in GROUPS.values() for label in members}
unknown = set(labels.to_numpy().ravel()) - known - {''}
if unknown:
    raise ValueError(f'Unmapped Current facility labels: {unknown}')
missing = current.geometry.isna() | current.geometry.is_empty
routes = current.loc[~missing].copy()
if routes.crs is None:
    raise ValueError('Route CRS missing')
bad = ~routes.geometry.is_valid
routes.loc[bad,'geometry'] = routes.loc[bad,'geometry'].make_valid()
routes = routes.to_crs(PROJECTED_CRS)
assert routes.geom_type.isin(['LineString','MultiLineString']).all()
networks = {}
for group, (_, members) in GROUPS.items():
    selected = routes.loc[labels.loc[routes.index].isin(members).any(axis=1)]
    # One union per group removes exact overlaps, including repeated directions.
    networks[group] = selected.geometry.union_all()
network_miles = routes.geometry.union_all().length / FEET_PER_MILE
summary = pd.DataFrame([
    {'facility_group': group, 'total_route_miles': geometry.length / FEET_PER_MILE,
     'percent_of_total_bike_route_miles': 100 * geometry.length / FEET_PER_MILE / network_miles}
    for group, geometry in networks.items()
])
summary.to_csv(OUT / 'bike_infrastructure_type_summary.csv', index=False)
tracts = read_spatial(OUT / 'nyc_tracts_income.geojson').to_crs(PROJECTED_CRS)
boroughs = tracts[['boroname','geometry']].dissolve(by='boroname')
fig, ax = plt.subplots(figsize=(13,14))
boroughs.plot(ax=ax, color='#f4f5f3', edgecolor='none')
styles = {
    'Protected': ('#b00045', 1.25),
    'Buffered': ('#a99ac1', .65),
    'Conventional / Curbside': ('#83a5bd', .6),
    'Shared / Signed': ('#b5aa96', .55),
    'Other / Off-street': ('#a2b598', .6),
}
# Mixed-group segments appear in every represented group. Overlapping lines are
# drawn in this order; Protected is uppermost. This is visual emphasis, not reassignment.
order = ['Other / Off-street','Shared / Signed','Conventional / Curbside','Buffered','Protected']
for z, group in enumerate(order, start=2):
    color, width = styles[group]
    gpd.GeoSeries([networks[group]], crs=PROJECTED_CRS).plot(ax=ax, color=color, linewidth=width, zorder=z)
boroughs.boundary.plot(ax=ax,color='#65717a',linewidth=.5,zorder=7)
handles=[Line2D([0],[0],color=styles[group][0],lw=3 if group=='Protected' else 2,label=group) for group in GROUPS]
handles.append(Line2D([0],[0],color='#65717a',lw=.7,label='Borough boundary'))
ax.legend(handles=handles,title='Current bicycle infrastructure',loc='upper left',frameon=False,fontsize=10,title_fontsize=11)
ax.set_title('Types of Bicycle Infrastructure in NYC',fontsize=22,pad=20,loc='left')
ax.text(.97,.97,'N\n\u2191',transform=ax.transAxes,ha='center',va='top',fontsize=18)
ax.set_axis_off()
fig.text(.09,.035,'Sources: NYC DOT Bike Routes (2026 download); NYC DCP shoreline-clipped 2020 census tracts.\n'
         'Analytical facility groups, not an official safety ranking. Mixed-direction routes can belong to multiple groups;\n'
         'protected routes are drawn on top where groups overlap. Mileage measures route geometry, not directional lane counts.',fontsize=9,color='#45535d')
fig.savefig(OUT / 'map_bike_infrastructure_types.png',dpi=300,bbox_inches='tight',facecolor='white')
plt.close(fig)
ranked=summary.sort_values('total_route_miles',ascending=False)
p=summary.set_index('facility_group').loc['Protected']
notes=f'''Types of Bicycle Infrastructure in NYC

The most common group by unique route mileage is {ranked.iloc[0].facility_group} ({ranked.iloc[0].total_route_miles:.1f} miles), followed by {ranked.iloc[1].facility_group} ({ranked.iloc[1].total_route_miles:.1f} miles). Shared / Signed routes are the next largest group.

Protected routes total {p.total_route_miles:.1f} miles, or {p.percent_of_total_bike_route_miles:.1f}% of the {network_miles:.1f} unique miles in the usable Current network. They occur across all five boroughs, but the map shows a denser network in Manhattan and selected corridors in the other boroughs, rather than uniform coverage. These are visual observations, not a formal spatial-clustering test.

This map adds useful context to the income/protected-lane analysis: places with few protected routes may still contain conventional, shared, or other infrastructure. The map distinguishes those types without implying that income causes their distribution. It does not measure individual access, connectivity, or safety.

Methods and interpretation:
- Only status == Current is used. Original facility fields remain unchanged in memory and in the raw dataset; source data is never written. The detailed original-label audit remains available from script 07.
- {int(missing.sum())} Current records have missing/empty geometry and cannot contribute to mileage.
- Any matching directional field assigns a segment to a group; repeating a label or group across directions does not multiply its mileage. Exact overlapping line geometry is unioned separately within each group.
- A segment with different groups by direction belongs to all applicable groups. Non-protected overlaps follow the documented drawing order; Protected is drawn last among route layers and can conceal another group at the same location. This does not recategorize the source data.
- total_route_miles uses each group's full usable Current route geometry, including portions outside shoreline-clipped tract polygons (such as bridge or shoreline segments). It is not the sum of mileage clipped to tracts.
- percent_of_total_bike_route_miles divides by the union of all usable Current routes, {network_miles:.6f} miles. Cross-group overlaps are intentional; percentages sum to {summary.percent_of_total_bike_route_miles.sum():.2f}%, not necessarily 100%. These are network-coverage percentages, not mutually exclusive composition shares.
- CRS: EPSG:2263; US survey feet converted to miles. No snapping, directional lane-count multiplication, or safety-priority classification is used. Non-coincident parallel lines remain separate.
- Groups match script 07 exactly and are analytical groupings, not an official NYC DOT safety ranking.
'''
(OUT / 'bike_infrastructure_type_map_notes.txt').write_text(notes,encoding='utf-8')
print(summary.to_string(index=False))
print(notes)
print('Saved one additional map at 300 DPI.')
