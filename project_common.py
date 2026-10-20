"""Shared paths and helpers for the analysis scripts."""
from pathlib import Path
import os
import geopandas as gpd
import pandas as pd

HERE = Path(__file__).resolve().parent
# Works both in the ACS download folder and in the social mapping folder.
ROOT = HERE if list(HERE.glob('2020_Census_Tracts*.geojson')) else HERE.parent
OUT = Path(os.environ.get('GIS_OUTPUT_DIR', str(ROOT / 'output')))
OUT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault('MPLCONFIGDIR', str(OUT / '.matplotlib'))
PROJECTED_CRS = 'EPSG:2263'  # New York Long Island, US survey feet
FEET_PER_MILE = 1609.344 / (1200 / 3937)
FACILITY_FIELDS = ['ft_facilit', 'tf_facilit', 'ft2facilit', 'tf2facilit']

def one_file(pattern):
    files = [p for p in ROOT.rglob(pattern) if 'output' not in p.parts and '.venv' not in p.parts]
    if len(files) != 1:
        raise ValueError(f'Expected one {pattern}: {files}')
    return files[0]

def sources():
    return (one_file('*B19013-Data.csv'), one_file('2020_Census_Tracts*.geojson'),
            one_file('New_York_City_Bike_Routes*.geojson'))

def read_spatial(path):
    data = gpd.read_file(path)
    if data.crs is None:
        raise ValueError(f'Missing CRS: {path}')
    if data.geometry.isna().any() or data.geometry.is_empty.any():
        raise ValueError(f'Missing/empty geometry: {path}')
    bad = ~data.geometry.is_valid
    if bad.any():
        print(f'Repairing {bad.sum()} invalid geometries in memory: {path.name}')
        data.loc[bad, 'geometry'] = data.loc[bad, 'geometry'].make_valid()
    return data

def save_geojson(data, name):
    data.to_crs(4326).to_file(OUT / name, driver='GeoJSON', index=False)

def income_groups(data):
    return pd.qcut(data['median_household_income'], 4, labels=['Q1', 'Q2', 'Q3', 'Q4'])
