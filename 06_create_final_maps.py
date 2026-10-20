"""Create three maps, save them, and open a gallery in your browser.

Run with --no-open to save the maps without opening the browser.
"""
import argparse
import webbrowser
import pandas as pd
from project_common import OUT, PROJECTED_CRS, read_spatial, income_groups
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams['text.parse_math'] = False  # Dollar signs in income ranges are currency.
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.colors import ListedColormap
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--no-open', action='store_true', help='Save maps without opening the gallery')
args = parser.parse_args()
saved_maps = []

tracts = read_spatial(OUT / 'nyc_income_bike_access.geojson').to_crs(PROJECTED_CRS)
lanes = read_spatial(OUT / 'protected_bike_lanes.geojson').to_crs(PROJECTED_CRS)
tracts['income_quartile'] = income_groups(tracts)
boroughs = tracts[['boroname','geometry']].dissolve(by='boroname')
missing = {'color':'#d6d6d6','label':'Income unavailable'}

def finish(fig,ax,title,filename,overlay=False):
    boroughs.boundary.plot(ax=ax,color='#4b555c',linewidth=.55)
    handles = [Line2D([0],[0],color='#4b555c',lw=.8,label='Borough boundary')]
    if overlay:
        lanes.plot(ax=ax,color='#007f86',linewidth=.85,alpha=1)
        handles.insert(0,Line2D([0],[0],color='#007f86',lw=2,label='Protected bike lane'))
    if not overlay:
        handles.append(Patch(facecolor='#ffffd4',label='Zero density: palest shade'))
    # Keep the categorical quartile legend when adding the line legend.
    old_legend = ax.get_legend()
    if old_legend is not None:
        ax.add_artist(old_legend)
    ax.legend(handles=handles,loc='lower right',frameon=False,fontsize=8)
    ax.set_title(title,fontsize=14,pad=16,loc='left'); ax.set_axis_off()
    ax.text(.98,.98,'N\n\u2191',transform=ax.transAxes,ha='center',va='top',fontsize=14)
    fig.text(.07,.035,'Sources: ACS 2024 5-year B19013; NYC DCP 2020 tracts; NYC DOT routes (2026 download).\nRoute miles within shoreline-clipped tracts; descriptive access proxy. Gray outlines show boroughs.',fontsize=8,color='#44515c')
    fig.savefig(OUT / filename,dpi=300,bbox_inches='tight',facecolor='white'); plt.close(fig)
    saved_maps.append((title, filename))
    print(f'Saved: {OUT / filename}')

fig,ax=plt.subplots(figsize=(10,11))
# Quantile boundaries come directly from observed income; missing income stays gray.
tracts['income_quintile'], edges = pd.qcut(tracts.median_household_income, 5,
                                         labels=False, retbins=True)
labels = [f'{i+1}: ${edges[i]:,.0f} to ${edges[i+1]:,.0f}' for i in range(5)]
tracts['income_class'] = pd.Categorical(tracts.income_quintile.map(dict(enumerate(labels))),
                                       categories=labels, ordered=True)
pd.DataFrame({'class':range(1,6), 'lower_bound':edges[:-1], 'upper_bound':edges[1:]}).to_csv(
    OUT / 'income_map_quantile_breaks.csv', index=False)
tracts.plot(column='income_class',categorical=True,cmap='YlOrBr',ax=ax,linewidth=0,legend=True,
            legend_kwds={'title':'Income: five quantiles (2024 dollars)', 'loc':'upper left',
                         'frameon':False, 'fontsize':9},missing_kwds=missing)
finish(fig,ax,'Median Household Income and Protected Bike Lanes in NYC','map_income_and_protected_lanes.png',True)

fig,ax=plt.subplots(figsize=(10,11))
# Show the full calculated density range with a linear color scale.
tracts.plot(column='protected_lane_miles_per_sqmi',cmap='YlGnBu',vmin=0,ax=ax,linewidth=0,legend=True,
            legend_kwds={'label':'Protected bike lane miles per square mile','shrink':.55})
finish(fig,ax,'Protected Bike Lane Density Across NYC Census Tracts','map_protected_lane_density.png')

fig,ax=plt.subplots(figsize=(10,11))
tracts.plot(column='income_quartile',categorical=True,cmap=ListedColormap(['#fff4bc','#fec66b','#ee8148','#a94027']),ax=ax,linewidth=0,legend=True,
            legend_kwds={'title':'Income quartile\nQ1 lowest; Q4 highest','loc':'upper left','frameon':False},missing_kwds=missing)
finish(fig,ax,'Income Quartiles and Protected Bike Infrastructure in NYC','map_income_quartiles_bike_lanes.png',True)
for title, filename in [
    ('Median Household Income vs. Protected Bike Lane Density', 'income_vs_protected_bike_access.png'),
    ('Average Protected Bike Lane Density by Income Quartile', 'average_protected_lane_density_by_income_quartile.png'),
    ('Share of NYC Census Tracts With Protected Bike Lanes by Income Quartile', 'protected_lane_access_by_income_quartile.png'),
]:
    if (OUT / filename).exists():
        saved_maps.append((title, filename))
# A local gallery displays all three saved maps together without a GUI plotting dependency.
gallery = OUT / 'maps.html'
cards = '\n'.join(f'<section><h2>{title}</h2><a href="{filename}"><img src="{filename}" alt="{title}"></a></section>'
                  for title, filename in saved_maps)
gallery.write_text('''<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>NYC income and protected bike routes</title>
<style>body{font-family:Arial,sans-serif;background:#eef2f5;color:#18303e;margin:0;padding:28px}
main{max-width:1100px;margin:auto}section{background:white;padding:20px;margin:24px 0;border-radius:10px}
img{width:100%;height:auto}h1{font-size:28px}h2{font-size:21px}</style>
<main><h1>NYC income and protected bike routes</h1>
<p>Click a map to view the full-size image. The PNG files are saved alongside this gallery.</p>
''' + cards + '</main></html>', encoding='utf-8')
print(f'Gallery: {gallery}')
if not args.no_open:
    webbrowser.open(gallery.resolve().as_uri())
