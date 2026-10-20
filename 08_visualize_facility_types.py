"""Create the additional facility-type charts, map, and separate gallery."""
import argparse
import webbrowser
import numpy as np
import pandas as pd
from project_common import OUT, PROJECTED_CRS, read_spatial
from importlib import import_module
GROUPS = import_module('07_analyze_facility_types').GROUPS
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
from matplotlib.patches import Patch
from matplotlib.colors import ListedColormap

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--no-open', action='store_true')
args = parser.parse_args()
summary = pd.read_csv(OUT / 'bike_facility_type_by_income.csv')
quartiles = ['Q1','Q2','Q3','Q4']
groups = list(GROUPS)
colors = ['#007c83','#7a4da0','#dc8934','#4679b5','#749444']
figures = []

def save_chart(fig, ax, title, filename):
    ax.set_title(title, fontsize=15, pad=18)
    ax.spines[['top','right']].set_visible(False)
    ax.grid(axis='y', alpha=.2); ax.set_axisbelow(True)
    fig.text(.08,.018,'ACS 2024 5-year income; current NYC DOT routes (2026 download). '
             'Analytical groups, not an official safety ranking.\n'
             'Each tract weighted equally; mixed-type routes can contribute to multiple groups.',fontsize=9)
    fig.tight_layout(rect=(0,.075,1,1))
    fig.savefig(OUT / filename, dpi=300, facecolor='white'); plt.close(fig)
    figures.append((title, filename))

fig,ax = plt.subplots(figsize=(13,8))
x = np.arange(4); width=.15
for i, group in enumerate(groups):
    values = summary[summary.facility_group.eq(group)].set_index('income_quartile').reindex(quartiles).percent_with_facility
    bars = ax.bar(x+(i-2)*width, values, width, label=group, color=colors[i])
    ax.bar_label(bars, fmt='%.1f', padding=3, fontsize=8)
ax.set_xticks(x, quartiles); ax.set_ylim(0,100)
ax.yaxis.set_major_formatter(PercentFormatter(100))
ax.set_xlabel('Income quartile (Q1 = lowest income; Q4 = highest income)')
ax.set_ylabel('Tracts with some infrastructure in this group (%)')
ax.legend(loc='upper left', ncol=3, frameon=False, fontsize=9)
save_chart(fig,ax,'Access to Bicycle Infrastructure Types by NYC Income Quartile','facility_access_by_income_quartile.png')

fig,ax = plt.subplots(figsize=(13,8))
x=np.arange(5); width=.19
for i, quartile in enumerate(quartiles):
    values=summary[summary.income_quartile.eq(quartile)].set_index('facility_group').reindex(groups).average_facility_miles_per_sqmi
    bars=ax.bar(x+(i-1.5)*width,values,width,label=quartile,color=['#f5d87a','#e6a052','#a95a40','#663452'][i])
    ax.bar_label(bars,fmt='%.2f',padding=3,fontsize=8)
ax.set_xticks(x,['Protected','Buffered','Conventional /\nCurbside','Shared /\nSigned','Other /\nOff-street'])
ax.set_ylim(0,summary.average_facility_miles_per_sqmi.max()*1.25)
ax.set_ylabel('Average facility route miles per square mile'); ax.set_xlabel('Facility group')
ax.legend(title='Income quartile',frameon=False,ncol=4,loc='upper right')
save_chart(fig,ax,'Bicycle Infrastructure Type and Neighborhood Income','facility_density_by_income_quartile.png')

tracts=read_spatial(OUT / 'nyc_income_bike_facility_types.geojson').to_crs(PROJECTED_CRS)
categories=groups+['No bike infrastructure','Tie: multiple groups']
map_colors=colors+['#e5e5e5','#bd6b9b']
tracts['dominant_facility_group']=pd.Categorical(tracts.dominant_facility_group,categories=categories)
fig,ax=plt.subplots(figsize=(12,12))
tracts.plot(column='dominant_facility_group',categorical=True,cmap=ListedColormap(map_colors),ax=ax,linewidth=0)
tracts[['boroname','geometry']].dissolve(by='boroname').boundary.plot(ax=ax,color='#53616b',linewidth=.6)
ax.legend(handles=[Patch(facecolor=c,label=g) for g,c in zip(categories,map_colors)],loc='upper left',frameon=False,fontsize=9,
          title='Greatest route mileage within tract')
ax.set_title('Dominant Bicycle Infrastructure Type by NYC Census Tract',fontsize=16,pad=18)
ax.text(.98,.98,'N\n\u2191',transform=ax.transAxes,ha='center',va='top',fontsize=14)
ax.set_axis_off()
fig.text(.08,.025,'Sources: NYC DOT current routes (2026 download); NYC DCP shoreline-clipped 2020 census tracts.\n'
         'Analytical facility groups, not an official safety ranking. Gray outlines: boroughs.\n'
         'Mixed-direction groups may overlap. Ties are shown separately; dominance uses total route miles, not density.',fontsize=9)
filename='map_dominant_bike_facility_type.png'
fig.savefig(OUT / filename,dpi=300,bbox_inches='tight',facecolor='white'); plt.close(fig)
figures.append(('Dominant Bicycle Infrastructure Type by NYC Census Tract',filename))
html='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Bicycle infrastructure types and income</title><style>body{font-family:Arial;background:#eef2f5;color:#18303e;padding:25px}main{max-width:1100px;margin:auto}section{background:white;padding:20px;margin:24px 0}img{width:100%;height:auto}</style>
<main><h1>Bicycle infrastructure types and neighborhood income</h1><p>Analytical groups, not an official NYC DOT safety ranking. <a href="maps.html">Original protected-lane figures</a></p>'''
for title,filename in figures:
    html+=f'<section><h2>{title}</h2><a href="{filename}"><img src="{filename}" alt="{title}"></a></section>'
gallery=OUT / 'facility_types.html'
gallery.write_text(html+'</main></html>',encoding='utf-8')
print('Saved three figures and',gallery)
if not args.no_open:
    webbrowser.open(gallery.resolve().as_uri())
