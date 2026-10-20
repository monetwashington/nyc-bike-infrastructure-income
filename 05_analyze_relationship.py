"""Descriptive correlations, income quartiles, exceptions, and scatter plot."""
import json
import numpy as np
import pandas as pd
from project_common import OUT, read_spatial, income_groups
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import StrMethodFormatter, PercentFormatter

tracts = read_spatial(OUT / 'nyc_income_bike_access.geojson')
data = tracts.dropna(subset=['median_household_income']).copy()
data['income_quartile'], bins = pd.qcut(data.median_household_income, 4, labels=['Q1','Q2','Q3','Q4'], retbins=True)
x = data.median_household_income
y = data.protected_lane_miles_per_sqmi
pearson = x.corr(y)
# Pearson correlation of average ranks is Spearman, with ties handled explicitly.
spearman = x.rank(method='average').corr(y.rank(method='average'))
summary = data.groupby('income_quartile', observed=True).agg(
    number_of_tracts=('tract_id','size'),
    average_median_household_income=('median_household_income','mean'),
    average_protected_lane_miles=('protected_lane_miles','mean'),
    average_protected_lane_miles_per_sqmi=('protected_lane_miles_per_sqmi','mean'),
    percent_with_protected_lane=('has_protected_lane',lambda s: s.mean()*100))
summary.to_csv(OUT / 'income_quartile_bike_access.csv')
data[['median_household_income','protected_lane_miles','tract_area_sqmi','protected_lane_miles_per_sqmi','has_protected_lane']].describe().to_csv(OUT / 'descriptive_statistics.csv')
stats = {'analysis_tracts': len(data), 'excluded_missing_income': len(tracts)-len(data),
         'pearson': float(pearson), 'spearman': float(spearman), 'quartile_edges_dollars': bins.tolist()}
(OUT / '05_relationship_report.json').write_text(json.dumps(stats, indent=2))
print(json.dumps(stats, indent=2)); print(summary.to_string())
data.groupby('boroname').agg(tracts=('tract_id','size'),mean_density=('protected_lane_miles_per_sqmi','mean'),percent_with_lane=('has_protected_lane', lambda s:s.mean()*100)).to_csv(OUT / 'borough_summary.csv')
data.groupby(['boroname','ntaname']).agg(tracts=('tract_id','size'),mean_density=('protected_lane_miles_per_sqmi','mean')).sort_values('mean_density',ascending=False).to_csv(OUT / 'neighborhood_summary.csv')
columns = ['tract_id','boroname','ntaname','median_household_income','protected_lane_miles','protected_lane_miles_per_sqmi']
data.loc[data.income_quartile == 'Q1'].nlargest(10,'protected_lane_miles_per_sqmi')[columns].to_csv(OUT / 'lower_income_high_access_examples.csv', index=False)
data.loc[(data.income_quartile == 'Q4') & (data.has_protected_lane == 0)].nlargest(10,'median_household_income')[columns].to_csv(OUT / 'higher_income_zero_access_examples.csv', index=False)
# Sensitivity checks help reveal whether outliers or borough differences drive results.
checks = []
for label, subset in [('All valid income', data), ('Exclude top 1% density', data[y <= y.quantile(.99)]),
                       ('Exclude topcoded income', data[~data.income_topcoded.fillna(False).astype(bool)])]:
    a,b = subset.median_household_income, subset.protected_lane_miles_per_sqmi
    checks.append({'sample':label,'n':len(subset),'pearson':a.corr(b),'spearman':a.rank().corr(b.rank())})
for borough, subset in data.groupby('boroname'):
    a,b = subset.median_household_income,subset.protected_lane_miles_per_sqmi
    checks.append({'sample':borough,'n':len(subset),'pearson':a.corr(b),'spearman':a.rank().corr(b.rank())})
pd.DataFrame(checks).to_csv(OUT / 'sensitivity_checks.csv',index=False)
fig,ax = plt.subplots(figsize=(11,7))
ax.scatter(x,y,s=12,alpha=.32,color='#176c86',edgecolors='none')
slope,intercept = np.polyfit(x,y,1)
line_x = np.linspace(x.min(),x.max(),100)
ax.plot(line_x,intercept+slope*line_x,color='#c34532',lw=2,label='Linear trend (descriptive)')
ax.set(title='Median Household Income vs. Protected Bike Lane Density',xlabel='Median household income (2024 dollars)',ylabel='Protected bike lane miles per square mile')
ax.xaxis.set_major_formatter(StrMethodFormatter('${x:,.0f}'))
ax.text(.03,.96,f'n = {len(data):,}\nPearson r = {pearson:.3f}\nSpearman rho = {spearman:.3f}',transform=ax.transAxes,va='top')
ax.legend(loc='upper right'); ax.grid(alpha=.15); ax.set_axisbelow(True)
fig.text(.1,.015,'2024 ACS 5-year income; current routes in supplied 2026 download. Each point is one tract.',fontsize=8)
fig.tight_layout(rect=(0,.04,1,1)); fig.savefig(OUT / 'income_vs_protected_bike_access.png',dpi=300); plt.close(fig)

# Use the actual tract means and binary-variable percentages, ordered Q1 to Q4.
summary = summary.reindex(['Q1', 'Q2', 'Q3', 'Q4'])
colors = ['#fff4bc', '#fec66b', '#ee8148', '#a94027']
for column, title, ylabel, filename, percentage in [
    ('average_protected_lane_miles_per_sqmi',
     'Average Protected Bike Lane Density by Income Quartile',
     'Average protected bike lane miles per square mile',
     'average_protected_lane_density_by_income_quartile.png', False),
    ('percent_with_protected_lane',
     'Share of NYC Census Tracts With Protected Bike Lanes by Income Quartile',
     'Census tracts with at least one protected bike lane (%)',
     'protected_lane_access_by_income_quartile.png', True),
]:
    fig, ax = plt.subplots(figsize=(12,7))
    bars = ax.bar(summary.index.astype(str), summary[column], color=colors,
                  edgecolor='#705a48', linewidth=.7, width=.65)
    ax.bar_label(bars, labels=[f'{v:.1f}%' if percentage else f'{v:.3f}'
                              for v in summary[column]], padding=5, fontsize=12)
    ax.set(title=title, xlabel='Income quartile (Q1 = lowest income; Q4 = highest income)', ylabel=ylabel)
    ax.set_ylim(0, 100 if percentage else summary[column].max()*1.2)
    if percentage:
        ax.yaxis.set_major_formatter(PercentFormatter(100))
    ax.spines[['top','right']].set_visible(False)
    ax.grid(axis='y', alpha=.2); ax.set_axisbelow(True)
    fig.text(.08,.02, f'{len(data):,} tracts with usable income; each tract weighted equally. '
             'ACS 2024 5-year income; supplied 2026 bike routes.', fontsize=9)
    fig.tight_layout(rect=(0,.05,1,1))
    fig.savefig(OUT / filename, dpi=300, facecolor='white'); plt.close(fig)
    print(f'Saved: {OUT / filename}')
