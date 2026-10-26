# NYC Bike Infrastructure Analysis

This repository contains the Python scripts for preparing and analyzing New York City bike infrastructure and census data.

## Input files

Download these files and place them in the project directory. They are excluded from GitHub because they are source data.

- ACS 2024 five-year B19013 median household income CSV (`*B19013-Data.csv`)
- NYC 2020 census tract boundaries (`2020_Census_Tracts*.geojson`)
- NYC bike routes (`New_York_City_Bike_Routes*.geojson`)

Source pages:

- [NYC DOT bike routes](https://data.cityofnewyork.us/dataset/New-York-City-Bike-Routes/mzxg-pwib)
- [NYC 2020 census tracts](https://data.cityofnewyork.us/City-Government/2020-Census-Tracts/63ge-mke6)
- [ACS data](https://data.census.gov/)

## Setup

From the project directory, create an environment and install the dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Run

Run the numbered scripts in order, from `01_inspect_data.py` through `09_map_bike_infrastructure_types.py`. For example:

```powershell
python .\01_inspect_data.py
python .\02_clean_and_join_income.py
python .\03_filter_protected_bike_lanes.py
python .\04_calculate_bike_access.py
python .\05_analyze_relationship.py
python .\06_create_final_maps.py
python .\07_analyze_facility_types.py
python .\08_visualize_facility_types.py
python .\09_map_bike_infrastructure_types.py
```

The scripts use shared paths and helpers from `project_common.py`. Generated files are written to `output/`. `create_presentation_charts.py` is an additional chart-generation script.

## View the results

Pre-rendered charts, maps, presentation-ready PNG/SVG files, a PDF, and supporting summary tables are included in [`results/`](results/README.md). To recreate the presentation charts after running the numbered scripts, run:

```powershell
python .\create_presentation_charts.py
```

The input data files are not included in this repository. The README links above point to their source pages; downloading newer data may produce different results.
