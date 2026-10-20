"""Inspect raw files without changing them; save the full inspection report."""
import contextlib
import pandas as pd
import geopandas as gpd
from project_common import sources, OUT, FACILITY_FIELDS

def inspect():
    income_path, tract_path, bike_path = sources()
    for path in (income_path, tract_path, bike_path):
        spatial = path.suffix == '.geojson'
        data = gpd.read_file(path) if spatial else pd.read_csv(path, dtype=str)
        print(f'\nFILE: {path}\nRows, columns: {data.shape}\nColumns: {list(data.columns)}')
        print(data.head().to_string(index=False))
        print('Missing values by field:\n', data.isna().sum().to_string())
        if spatial:
            print('CRS:', data.crs, '\nGeometry types:', data.geom_type.value_counts().to_dict())
            print('Invalid geometries:', (~data.geometry.is_valid).sum())
            print('Empty geometries:', data.geometry.is_empty.sum())
        for key in ['GEO_ID', 'geoid', 'boroct2020']:
            if key in data:
                print(f'Duplicate {key}:', data[key].duplicated().sum())
        if path == income_path:
            print('Raw income values not numeric (including label row):')
            print(data.loc[pd.to_numeric(data.B19013_001E, errors='coerce').isna(),
                           'B19013_001E'].value_counts(dropna=False).to_string())
        if path == bike_path:
            for field in FACILITY_FIELDS + ['facilitycl', 'allclasses', 'status']:
                if field in data:
                    print(f'\n{field}:\n{data[field].value_counts(dropna=False).to_string()}')
            print('\nPROTECTED DEFINITION: status=Current and exact category Protected in any of', FACILITY_FIELDS)
            print('These directional fields explicitly describe protection. Buffered, curbside, shared,')
            print('sidewalk, boardwalk, and other categories are not automatically called protected.')
            print('A route with two protected directions is counted once, not twice.')
            print('Metadata: https://data.cityofnewyork.us/dataset/New-York-City-Bike-Routes/mzxg-pwib')

if __name__ == '__main__':
    with (OUT / '01_inspection.txt').open('w', encoding='utf-8') as report:
        with contextlib.redirect_stdout(report):
            inspect()
    print((OUT / '01_inspection.txt').read_text(encoding='utf-8'))
