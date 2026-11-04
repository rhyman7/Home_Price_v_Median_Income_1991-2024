"""Reproduce the findings and figures from the project's saved comparison panels."""
import csv
import hashlib
import json
import math
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports' / 'findings'

def read(relative):
    with (ROOT / relative).open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))

def num(row, key):
    value = float(row[key])
    assert math.isfinite(value), (row, key)
    return value

def table(rows, kind):
    if kind == 'growth':
        lines = ['| State | Housing growth | Income growth | Gap (pp) |', '|---|---:|---:|---:|']
        for r in rows:
            lines.append(f"| {r['place_name']} | {num(r,'hpi_growth_pct'):.1f}% | {num(r,'income_growth_pct'):.1f}% | {num(r,'growth_gap_pp'):.1f} |")
    else:
        lines = ['| Area | Home value | Household income | Value / income |', '|---|---:|---:|---:|']
        for r in rows:
            lines.append(f"| {r['fhfa_place_name']} | ${num(r,'median_home_value_acs'):,.0f} | ${num(r,'median_household_income_acs'):,.0f} | {num(r,'home_value_to_income_ratio'):.2f}× |")
    return '\n'.join(lines)

def save(fig, name):
    fig.savefig(OUT / f'{name}.png', dpi=170, bbox_inches='tight', facecolor='white')
    plt.close(fig)

def build():
    OUT.mkdir(parents=True, exist_ok=True)
    annual = read('data/annual/comparison_annual.csv')
    dollars = read('data/dollars/acs_dollar_comparison.csv')
    for data in [annual, dollars]:
        assert len(data) == len({(r['geography_level'], r['place_id'], r['year']) for r in data}) == 5168
    base = {(r['geography_level'],r['place_id']):r for r in annual if r['year']=='1991'}
    for r in annual:
        b=base[(r['geography_level'],r['place_id'])]
        assert math.isclose(num(r,'hpi_growth_pct'),(num(r,'hpi_annual_sa')/num(b,'hpi_annual_sa')-1)*100,abs_tol=1e-8)
        if r['median_household_income']:
            inc=(num(r,'median_household_income')/num(b,'median_household_income')-1)*100
            assert math.isclose(num(r,'income_growth_pct'),inc,abs_tol=1e-8)
            assert math.isclose(num(r,'growth_gap_pp'),num(r,'hpi_growth_pct')-inc,abs_tol=1e-8)
    for r in dollars:
        if r['pair_status']=='available':
            assert math.isclose(num(r,'home_value_to_income_ratio'),num(r,'median_home_value_acs')/num(r,'median_household_income_acs'),abs_tol=1e-10)
        else:
            assert not r['home_value_to_income_ratio']
    states = [r for r in annual if r['geography_level']=='state' and r['place_name']!='District of Columbia']
    gaps=sorted([r for r in states if r['year']=='2024'],key=lambda r:num(r,'growth_gap_pp'))
    assert len(gaps)==50
    ratios={level:sorted([r for r in dollars if r['year']=='2024' and r['geography_level']==level and r['fhfa_place_name']!='District of Columbia'],key=lambda r:num(r,'home_value_to_income_ratio')) for level in ['national','state','metro']}
    assert [len(ratios[k]) for k in ['national','state','metro']]==[1,50,100]
    n=sorted([r for r in annual if r['geography_level']=='national'],key=lambda r:int(r['year']))
    n24=n[-1]; d24=ratios['national'][0]
    peak=max(n,key=lambda r:num(r,'growth_gap_pp'))
    all_ahead=[year for year in range(1992,2025) if sum(num(r,'growth_gap_pp')>0 for r in states if r['year']==str(year))==50]
    dc=next(r for r in dollars if r['year']=='2024' and r['fhfa_place_name']=='District of Columbia')
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False,'axes.titleweight':'bold'})
    fig,ax=plt.subplots(figsize=(11,5.8))
    for key,label,color in [('hpi_growth_pct','Housing price index','#3659b8'),('income_growth_pct','Household income','#138473')]:
        ax.plot([int(r['year']) for r in n],[num(r,key) for r in n],label=label,lw=2.8,color=color)
        ax.annotate(f"{num(n24,key):.1f}%",(2024,num(n24,key)),xytext=(8,0),textcoords='offset points',color=color,weight='bold')
    ax.set(title='U.S. housing prices grew faster than household income',xlabel='Year',ylabel='Cumulative growth since 1991 (%)',xlim=(1991,2027))
    ax.set_xticks([1991,1995,2000,2005,2010,2015,2020,2024]); ax.grid(axis='y',alpha=.2); ax.legend(loc='upper left',frameon=False)
    fig.text(.12,-.02,'FHFA annual average, purchase-only SA HPI; Census historical nominal household income.\n1991 annual baseline. The 2024 gap is %.1f percentage points.' % num(n24,'growth_gap_pp'),fontsize=9)
    save(fig,'national_growth')
    fig,ax=plt.subplots(figsize=(11,6.8)); selected=gaps[:5]+gaps[-5:]
    ax.barh([r['place_name'] for r in selected],[num(r,'growth_gap_pp') for r in selected],color=['#138473']*5+['#3659b8']*5)
    for i,r in enumerate(selected):ax.text(num(r,'growth_gap_pp')+3,i,f"{num(r,'growth_gap_pp'):.1f}",va='center')
    ax.set(title='2024 state growth gaps: five smallest and five largest',xlabel='Housing growth minus income growth since 1991 (percentage points)',xlim=(0,400))
    ax.invert_yaxis(); ax.grid(axis='x',alpha=.2);ax.set_axisbelow(True)
    fig.text(.12,-.01,'50 states, excluding D.C. Sources: FHFA annual HPI and Census historical nominal income.\nThese are cumulative growth gaps, not dollar affordability ratios.',fontsize=9)
    save(fig,'state_growth_gaps')
    fig,axes=plt.subplots(2,1,figsize=(13,11));fig.subplots_adjust(left=.39,hspace=.5,bottom=.1,top=.92)
    for ax,level,title in zip(axes,['state','metro'],['50 states (D.C. excluded)','100 selected metro areas / divisions']):
        selected=ratios[level][:5]+ratios[level][-5:]
        labels=[r['fhfa_place_name'].replace(' (MSAD)',' [division]') for r in selected]
        ax.barh(labels,[num(r,'home_value_to_income_ratio') for r in selected],color=['#138473']*5+['#7655aa']*5)
        for i,r in enumerate(selected):ax.text(num(r,'home_value_to_income_ratio')+.08,i,f"{num(r,'home_value_to_income_ratio'):.2f}×",va='center',fontsize=10)
        ax.axvline(num(d24,'home_value_to_income_ratio'),ls='--',color='#333333',lw=1,label=f"U.S. {num(d24,'home_value_to_income_ratio'):.2f}×")
        ax.set(title=title,xlim=(0,11),xlabel='Median owner-occupied home value / annual median household income')
        ax.invert_yaxis();ax.grid(axis='x',alpha=.2);ax.set_axisbelow(True);ax.legend(loc='upper right',fontsize=9)
    fig.suptitle('2024 home-value-to-income ratios: five lowest and five highest',fontsize=16,weight='bold')
    fig.text(.04,.025,'Source: Census ACS 2024 1-year B25077 and B19013, same release and geography.\nPoint-estimate rankings; differences are not tested for statistical significance. Metro areas are not city-proper boundaries.',fontsize=9)
    save(fig,'value_income_ratios')
    summary=f'''## Verified findings

Using the annual 1991 baseline, U.S. housing prices rose **{num(n24,'hpi_growth_pct'):.1f}%** through 2024, while nominal median household income rose **{num(n24,'income_growth_pct'):.1f}%**. The difference was **{num(n24,'growth_gap_pp'):.1f} percentage points**. The national gap was largest in **{peak['year']}** within this dataset, rather than peaking in 2022.

In 2024, cumulative housing growth exceeded income growth in **all 50 states**. This also occurred in **{', '.join(map(str,all_ahead[:-1]))}**. Illinois had income growth ahead of housing growth in 2021 and 2023, so the pattern was not uninterrupted after 2021.

The smallest 2024 state gaps were **{', '.join(r['place_name'] for r in gaps[:5])}**. The largest were **{', '.join(r['place_name'] for r in reversed(gaps[-5:]))}**. These rankings exclude D.C.

The separate 2024 ACS comparison reports a U.S. median owner-occupied home value of **${num(d24,'median_home_value_acs'):,.0f}** and median household income of **${num(d24,'median_household_income_acs'):,.0f}**, a **{num(d24,'home_value_to_income_ratio'):.2f}×** ratio. Among the 50 states, **{ratios['state'][0]['fhfa_place_name']}** has the lowest point estimate ({num(ratios['state'][0],'home_value_to_income_ratio'):.2f}×) and **{ratios['state'][-1]['fhfa_place_name']}** the highest ({num(ratios['state'][-1],'home_value_to_income_ratio'):.2f}×). Among the 100 selected metro/division areas, the range runs from **{ratios['metro'][0]['fhfa_place_name']}** ({num(ratios['metro'][0],'home_value_to_income_ratio'):.2f}×) to **{ratios['metro'][-1]['fhfa_place_name']}** ({num(ratios['metro'][-1],'home_value_to_income_ratio'):.2f}×).

These are descriptive comparisons. They do not establish causes or measure mortgage-payment affordability. The ACS ratio compares two population medians and uses home values, not sale prices. Rankings use point estimates without significance testing.
'''
    coverage='''## Coverage and interpretation

- Growth uses annual averages of all four seasonally adjusted FHFA quarters, rebased to 1991. Income uses the repository's historical Census current-dollar series. These are nominal measures. That preserved income source has not been refreshed against the latest release.
- Dollar comparisons use ACS 1-year B25077 and B19013 from the same year and geography. ACS income is not spliced into the historical growth series. U.S. 2024 historical income is $83,730, compared with ACS income of $81,604.
- National and state/DC ACS coverage is 2005–2019 and 2021–2024. Paired ACS home-value comparisons do not cover 1991–2004, and no standard ACS 1-year estimates exist for 2020. The separate household-income panel adds 129 verified observations for 1999–2004 across 27 metros; 30 are explicitly labeled constant-dollar estimates. Missing values remain missing.
- All 100 selected metro/division areas have paired dollar estimates in 2023–2024. Older coverage varies. Exact code matches do not guarantee unchanged boundaries; earlier metro geographies have not been harmonized. These are metro areas/divisions, not individual city boundaries or all U.S. metros.
- The explorer now includes a Household income view with earlier Census/ACS records, source labels, dollar years, and missing-data reasons. See `docs/historical_metro_income_sources.md` and `data/historical_metro_income/coverage_by_area.csv`.
- Metro income growth since 1991 is unavailable. State rankings exclude D.C.; the explorer still includes it.
- Source margins of error are retained in the dollar data. No ratio margin of error or ranking significance test has been calculated. Home values cover owner-occupied homes, while income covers households generally. Interest rates, down payments, taxes, insurance, and household-specific costs are not modeled.
'''
    report='# Housing and income: verified findings, 1991–2024\n\n[Open interactive charts](interactive_findings.html).\n\n'+summary+'\n![National growth](national_growth.png)\n\n### State growth extremes\n\n'+table(gaps[:5]+list(reversed(gaps[-5:])),'growth')+'\n\n![State growth gaps](state_growth_gaps.png)\n\n### 2024 dollar comparisons\n\n'+table([d24,dc],'ratio')
    for level,title in [('state','States'),('metro','Selected metro areas / divisions')]:
        report+='\n\n### '+title+': five lowest ratios\n\n'+table(ratios[level][:5],'ratio')+'\n\n### '+title+': five highest ratios\n\n'+table(list(reversed(ratios[level][-5:])),'ratio')
    report+='\n\n![Value-to-income ratios](value_income_ratios.png)\n\n'+coverage+'''\n## Reproduction and source trail

Run `python scripts/build_findings.py` from the repository environment. Inputs are `data/annual/comparison_annual.csv` and `data/dollars/acs_dollar_comparison.csv`. This build checks unique keys, recomputes all annual growth and gap values from their levels and 1991 baselines, and recomputes all 2,640 available ACS ratios. Source input hashes and complete rankings are saved in `findings_audit.json`.

Source definitions and acquisition details: `docs/annual_foundation_validation.md` and `docs/dollar_sources_report.md`. Original publishers: [FHFA HPI](https://www.fhfa.gov/data/hpi) and [Census ACS summary files](https://www.census.gov/programs-surveys/acs/data/summary-file.html). The analysis uses the project's saved source snapshots, not a new live-data refresh.
'''
    (OUT/'housing_income_findings.md').write_text(report,encoding='utf-8')
    audit={'input_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['data/annual/comparison_annual.csv','data/dollars/acs_dollar_comparison.csv']},'all_50_states_housing_ahead_years':all_ahead,'state_growth_ascending':gaps,'dollar_ratio_ascending':ratios,'validated_available_pairs':sum(r['pair_status']=='available' for r in dollars)}
    (OUT/'findings_audit.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
    readme=ROOT/'README.md'; old=readme.read_text(encoding='utf-8');marker='## Findings\n'
    if marker in old:
        archive=ROOT/'docs'/'historical_readme_findings.md'
        if not archive.exists():archive.write_text('# Superseded README findings\n\nPreserved for project history. Use reports/findings/housing_income_findings.md for the corrected annual results.\n\n'+old.split(marker,1)[1],encoding='utf-8')
        old=old.split(marker,1)[0]
    elif '## Verified findings\n' in old:
        old=old.split('## Verified findings\n',1)[0]
    old=old.replace('**Historical analysis below:**','**Historical project description below (the verified findings appear at the end):**')
    old=old.replace(' The superseded README conclusions are archived in `docs/historical_readme_findings.md`.','')
    old=old.replace('They use Q1 housing values and should not be cited as results of this annual rebuild.','They use Q1 housing values and should not be cited as results of this annual rebuild. The superseded README conclusions are archived in `docs/historical_readme_findings.md`.')
    readme.write_text(old+summary+'\n![National growth](reports/findings/national_growth.png)\n\n'+coverage+'\nOpen [the interactive findings charts](reports/findings/interactive_findings.html), or read [the full findings and ranking tables](reports/findings/housing_income_findings.md). Rebuild the report and three charts with `python scripts/build_findings.py`.\n',encoding='utf-8')
    from build_interactive_findings import build as build_interactive
    build_interactive()
    print(json.dumps({'state_count':len(gaps),'metro_count':len(ratios['metro']),'all_states_ahead_years':all_ahead,'national_peak_gap_year':peak['year'],'available_pairs':audit['validated_available_pairs']}))

if __name__=='__main__':build()
