"""Join ACS tract income using the full 11-digit state/county/tract GEOID."""
import json
import pandas as pd
from project_common import sources, OUT, read_spatial, save_geojson

income_path, tract_path, _ = sources()
income = pd.read_csv(income_path, dtype=str)[['GEO_ID', 'NAME', 'B19013_001E']]
income['tract_id'] = income.GEO_ID.str.extract(r'^1400000US(\d{11})$')[0]
income = income.loc[income.tract_id.notna()].copy()  # Removes the second header row.
income['income_topcoded'] = income.B19013_001E.str.contains('+', regex=False, na=False)
# Preserve capped estimates as their published lower bound, and flag them.
values = income.B19013_001E.str.replace(',', '', regex=False).str.replace('+', '', regex=False)
income['median_household_income'] = pd.to_numeric(values, errors='coerce')
income.loc[income.median_household_income <= 0, 'median_household_income'] = float('nan')
income = income.drop(columns='B19013_001E')
assert not income.tract_id.duplicated().any(), 'Duplicate ACS tract IDs'
tracts = read_spatial(tract_path)
key = next(c for c in tracts if c.lower() in ['geoid', 'geoid20', 'geoid2020'])
tracts['tract_id'] = tracts[key].astype(str).str.zfill(11)
assert tracts.tract_id.str.fullmatch(r'\d{11}').all()
assert not tracts.tract_id.duplicated().any(), 'Duplicate tract polygons'
joined = tracts.merge(income, on='tract_id', how='left', validate='one_to_one', indicator=True)
stats = {'total_tracts': len(joined), 'matched_tract_ids': int((joined._merge == 'both').sum()),
         'unmatched_tract_ids': int((joined._merge != 'both').sum()),
         'valid_income_tracts': int(joined.median_household_income.notna().sum()),
         'missing_income': int(joined.median_household_income.isna().sum()),
         'topcoded_income': int(joined.income_topcoded.fillna(False).sum())}
joined.loc[joined._merge != 'both', ['tract_id', 'boroname']].to_csv(OUT / 'unmatched_tracts.csv', index=False)
joined.loc[joined.median_household_income.isna(), ['tract_id', 'NAME']].to_csv(OUT / 'missing_income_tracts.csv', index=False)
income.loc[~income.tract_id.isin(tracts.tract_id)].to_csv(OUT / 'acs_without_polygon.csv', index=False)
save_geojson(joined.drop(columns='_merge'), 'nyc_tracts_income.geojson')
(OUT / '02_join_report.json').write_text(json.dumps(stats, indent=2))
print(json.dumps(stats, indent=2))
print('Missing income retained as NaN; omitted only from income analyses. Topcodes flagged.')
