"""Create presentation charts from existing CSV outputs; source files stay unchanged."""
from pathlib import Path
import os
BASE = Path(__file__).resolve().parent
OUT = BASE / 'output' / 'presentation_charts'
OUT.mkdir(parents=True, exist_ok=True)
os.environ.setdefault('MPLCONFIGDIR', str(BASE / 'output' / '.matplotlib'))
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, PercentFormatter
from matplotlib.backends.backend_pdf import PdfPages

raw = pd.read_csv(BASE / 'output/nyc_income_bike_access.csv')
d = raw.dropna(subset=['median_household_income']).copy()
qs = ['Q1', 'Q2', 'Q3', 'Q4']
d['quartile'] = pd.qcut(d.median_household_income, 4, labels=qs)
ycol = 'protected_lane_miles_per_sqmi'
xcol = 'median_household_income'
assert d[ycol].notna().all() and (d[ycol] >= 0).all()
summary = d.groupby('quartile', observed=True).agg(n=(ycol, 'size'), presence=('has_protected_lane', 'mean'))
saved = pd.read_csv(BASE / 'output/income_quartile_bike_access.csv').set_index('income_quartile')
assert np.allclose(summary.presence * 100, saved.loc[qs, 'percent_with_protected_lane'])
colors = ['#276B83', '#659DA5', '#D3A65A', '#AE5C3F']
labels = ['Q1 · lowest', 'Q2', 'Q3', 'Q4 · highest']
plt.rcParams.update({'text.parse_math':False, 'font.family':'DejaVu Sans', 'font.size':12, 'axes.titlesize':15,
                     'axes.labelsize':12, 'axes.spines.top':False, 'axes.spines.right':False,
                     'figure.facecolor':'white', 'axes.labelcolor':'#243746', 'text.color':'#243746'})
source = f'Sources: ACS 2024 5-year income (2020–2024); supplied 2026 NYC bike routes. {len(d):,} tracts with usable income.'
scope = 'Each tract weighted equally. Routes inside tract boundaries measure infrastructure presence, not residents’ usable access.'
pdf = PdfPages(OUT / 'all_five_charts.pdf')
items = []
def finish(fig, stem, title, note):
    fig.suptitle(title, x=.075, y=.97, ha='left', fontsize=21, fontweight='bold')
    fig.text(.075, .91, note, fontsize=11)
    fig.text(.075, .047, source, fontsize=9)
    fig.text(.075, .022, scope, fontsize=9)
    fig.savefig(OUT / f'{stem}.png', dpi=300, facecolor='white')
    fig.savefig(OUT / f'{stem}.svg', facecolor='white')
    pdf.savefig(fig)
    items.append((stem, title))
    plt.close(fig)

fig, ax = plt.subplots(figsize=(13.33, 7.5))
fig.subplots_adjust(left=.10, right=.96, bottom=.20, top=.82)
bars = ax.bar(labels, summary.presence * 100, color=colors, width=.6)
ax.bar_label(bars, labels=[f'{v*100:.1f}%' for v in summary.presence], padding=9, fontsize=17, fontweight='bold')
ax.set(ylim=(0,100), ylabel='Tracts containing protected routes', xlabel='Tract median household income quartile')
ax.yaxis.set_major_formatter(PercentFormatter(100)); ax.grid(axis='y', alpha=.18); ax.set_axisbelow(True)
finish(fig, '01_protected_route_presence', 'Protected routes: highest presence in the highest-income quarter',
       'The lowest-income quarter also exceeds both middle-income quarters. Q1–Q4 each contain approximately 550 tracts.')

fig, ax = plt.subplots(figsize=(13.33,7.5))
fig.subplots_adjust(left=.10,right=.96,bottom=.20,top=.82)
groups = [d.loc[d.quartile == q, ycol] for q in qs]
bp = ax.boxplot(groups, tick_labels=labels, patch_artist=True, widths=.5, showmeans=True,
                meanprops={'marker':'D','markerfacecolor':'#AE5C3F','markeredgecolor':'white','markersize':7},
                medianprops={'color':'#172F42','linewidth':2},
                flierprops={'marker':'.','markersize':4,'alpha':.4})
for box, color in zip(bp['boxes'], colors): box.set_facecolor(color); box.set_alpha(.5)
ax.set(ylabel='Protected route miles per square mile',xlabel='Tract median household income quartile',ylim=(-.5,d[ycol].max()*1.08))
ax.grid(axis='y',alpha=.18); ax.set_axisbelow(True)
finish(fig,'02_density_box_plot','Within-group variation matters',
       'Zeros and all outliers included. Boxes: middle 50%; line: median; diamond: mean; whiskers: 1.5 × IQR.')

def scatter(ax, frame, color='#276B83'):
    ax.scatter(frame[xcol],frame[ycol],s=15,alpha=.32,color=color,edgecolors='none',rasterized=True)
    ax.set(xlim=(0,260000),ylim=(-.5,d[ycol].max()*1.07))
    ax.set_xticks([0,50000,100000,150000,200000,250000])
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v,p:f'${v/1000:.0f}k'))
    ax.grid(alpha=.15); ax.set_axisbelow(True)

fig,ax=plt.subplots(figsize=(13.33,7.5))
fig.subplots_adjust(left=.10,right=.96,bottom=.20,top=.82)
scatter(ax,d)
r=d[xcol].corr(d[ycol]); rho=d[xcol].rank().corr(d[ycol].rank())
ax.text(.02,.95,f'Pearson r = {r:.3f}\nSpearman ρ = {rho:.3f}',transform=ax.transAxes,va='top',fontsize=13)
ax.set(xlabel='Tract median household income (2024 dollars)',ylabel='Protected route miles per square mile')
finish(fig,'03_income_density_scatter','Income and protected-route density: a weak positive relationship',
       'One point per census tract; overlapping points appear darker. The 13 income estimates of $250,000+ are plotted at $250,000.')

facility=pd.read_csv(BASE/'output/bike_facility_type_by_income.csv')
order=['Protected','Buffered','Conventional / Curbside','Shared / Signed','Other / Off-street']
matrix=facility.pivot(index='income_quartile',columns='facility_group',values='percent_with_facility').loc[qs,order]
assert matrix.shape==(4,5) and matrix.notna().all().all()
fig,ax=plt.subplots(figsize=(13.33,7.5))
fig.subplots_adjust(left=.16,right=.90,bottom=.23,top=.81)
im=ax.imshow(matrix,cmap='YlGnBu',vmin=0,vmax=100,aspect='auto')
ax.set_xticks(range(5),['Protected','Buffered','Conventional /\nCurbside','Shared /\nSigned','Other /\nOff-street'])
ax.set_yticks(range(4),labels)
ax.set_ylabel('Income quartile')
for i in range(4):
    for j in range(5):
        value=matrix.iloc[i,j]
        ax.text(j,i,f'{value:.1f}%',ha='center',va='center',fontsize=17,color='white' if value>55 else '#172F42')
cb=fig.colorbar(im,ax=ax,pad=.025); cb.ax.yaxis.set_major_formatter(PercentFormatter(100))
cb.set_label('Tracts containing facility type')
finish(fig,'04_facility_type_heatmap','The infrastructure mix differs across income groups',
       'Facility categories overlap: a tract can contain several types. Percentages do not sum to 100%; categories are not a safety ranking.')

fig,axs=plt.subplots(2,3,figsize=(16,9))
fig.subplots_adjust(left=.07,right=.97,bottom=.18,top=.80,wspace=.22,hspace=.39)
for ax,borough in zip(axs.flat,['Bronx','Brooklyn','Manhattan','Queens','Staten Island']):
    sub=d[d.boroname==borough]
    scatter(ax,sub)
    ax.set_xticks([0,100000,200000]); ax.tick_params(labelsize=10)
    ax.set_title(f'{borough}  ·  n = {len(sub):,}',loc='left',fontweight='bold')
    ax.text(.04,.95,f'Pearson r = {sub[xcol].corr(sub[ycol]):.3f}',transform=ax.transAxes,va='top',fontsize=11)
axs[1,2].axis('off')
axs[1,2].text(.03,.85,'Read across boroughs\n\nAll panels use identical scales.\nAll valid-income tracts are included.\n\nRelationships are descriptive;\nincome does not establish causation.',va='top',fontsize=13,linespacing=1.5)
fig.text(.48,.115,'Tract median household income (2024 dollars)',ha='center')
fig.text(.012,.49,'Protected route miles per square mile',va='center',rotation=90)
finish(fig,'05_borough_scatter_plots','The citywide relationship varies across boroughs',
       'One point per census tract. No single income–infrastructure relationship describes all five boroughs.')
pdf.close()
html='<!doctype html><html lang="en"><meta charset="utf-8"><title>NYC bicycle infrastructure charts</title><style>body{font:18px system-ui;max-width:1200px;margin:40px auto;padding:0 24px;color:#243746;background:#f4f6f8}img{width:100%;background:white}section{margin:40px 0}a{color:#276b83}</style><h1>NYC bicycle infrastructure and income</h1><p>Five charts based on existing analysis outputs. <a href="all_five_charts.pdf">Download all charts as PDF</a>.</p>'
for stem,title in items:
    html+=f'<section><h2>{title}</h2><p><a href="{stem}.png">300-DPI PNG</a> · <a href="{stem}.svg">Editable SVG</a></p><img src="{stem}.png" alt="{title}"></section>'
(OUT/'gallery.html').write_text(html,encoding='utf-8')
print(f'Created {len(items)} charts as PNG and SVG, combined PDF, and gallery in {OUT}')
print(f'Validated presence percentages against saved summary; n={len(d)}, excluded missing income={len(raw)-len(d)}.')
