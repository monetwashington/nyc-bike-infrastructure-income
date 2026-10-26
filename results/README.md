# NYC Bike Infrastructure Analysis: Charts and Maps

These pre-rendered figures are included so readers can view the project results directly on GitHub. The source code and instructions are in the [project README](../README.md).

The figures were produced from 2,199 census tracts with usable household-income estimates. The underlying raw datasets are not included in this repository. The analysis used the ACS 2024 five-year income table, the NYC 2020 census tract boundaries, and the NYC Bike Routes snapshot available to the project when it was run. The source pages are [ACS data](https://data.census.gov/), [NYC 2020 Census Tracts](https://data.cityofnewyork.us/City-Government/2020-Census-Tracts/63ge-mke6), and [NYC Bike Routes](https://data.cityofnewyork.us/dataset/New-York-City-Bike-Routes/mzxg-pwib). Later downloads may differ, especially for bike routes.

## Maps

### Household income and protected bike routes

![Median household income and protected bike lanes](maps/map_income_and_protected_lanes.png)

![Protected bike lane density across NYC census tracts](maps/map_protected_lane_density.png)

![Income quartiles and protected bike infrastructure](maps/map_income_quartiles_bike_lanes.png)

### Bike infrastructure types

![Bike infrastructure types in NYC](maps/map_bike_infrastructure_types.png)

![Dominant bike facility type by census tract](maps/map_dominant_bike_facility_type.png)

The [maps gallery](maps/maps.html) and [facility types gallery](maps/facility_types.html) can also be downloaded with the PNG files and opened locally in a browser.

## Analysis charts

![Income and protected bike access](charts/income_vs_protected_bike_access.png)

![Average protected route density by income quartile](charts/average_protected_lane_density_by_income_quartile.png)

![Share of tracts with a protected route by income quartile](charts/protected_lane_access_by_income_quartile.png)

![Access to infrastructure types by income quartile](charts/facility_access_by_income_quartile.png)

![Infrastructure type density by income quartile](charts/facility_density_by_income_quartile.png)

Supporting summaries: [income and protected access](charts/income_quartile_bike_access.csv), [facility type by income](charts/bike_facility_type_by_income.csv), and [infrastructure mileage summary](maps/bike_infrastructure_type_summary.csv).

## Presentation charts

The five presentation charts are available as PNG and editable SVG files, with a [combined PDF](presentation/all_five_charts.pdf). A [gallery page](presentation/gallery.html) is included for local viewing alongside the image files.

![Protected route presence by income group](presentation/01_protected_route_presence.png)

![Variation in protected route density](presentation/02_density_box_plot.png)

![Income and protected route density](presentation/03_income_density_scatter.png)

![Infrastructure type mix by income](presentation/04_facility_type_heatmap.png)

![Protected route density by borough](presentation/05_borough_scatter_plots.png)

## Interpretation

These are tract-level comparisons. Route mileage inside a tract does not measure how many people use a route, how easy it is to reach, or how safe riders feel.
