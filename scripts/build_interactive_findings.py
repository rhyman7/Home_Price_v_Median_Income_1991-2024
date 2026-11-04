"""Build offline, interactive versions of the three findings charts."""
import csv
from pathlib import Path
import plotly.graph_objects as go
from plotly.offline import get_plotlyjs
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/findings/interactive_findings.html'
CONFIG={'responsive':True,'displaylogo':False,'scrollZoom':False}

def read(name):
    with (ROOT/name).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))

def style(fig,title,x,y,height=560):
    fig.update_layout(template='plotly_white',title={'text':title,'font':{'size':20}},height=height,
        margin={'t':130,'l':100,'r':40,'b':80},xaxis_title=x,yaxis_title=y,font={'family':'Arial','size':12},
        legend={'orientation':'h','y':1.08},hoverlabel={'namelength':-1})
    return fig

def menu(buttons):
    return [dict(buttons=buttons,direction='down',x=0,y=1.04,xanchor='left',yanchor='bottom',showactive=True)]

def figures():
    a=read('data/annual/comparison_annual.csv');d=read('data/dollars/acs_dollar_comparison.csv')
    n=sorted([r for r in a if r['geography_level']=='national'],key=lambda r:int(r['year']))
    growth=go.Figure()
    for key,label,color in [('hpi_growth_pct','Housing price index','#3659b8'),('income_growth_pct','Household income','#138473')]:
        growth.add_scatter(x=[int(r['year']) for r in n],y=[float(r[key]) for r in n],name=label,mode='lines+markers',line={'color':color},marker={'size':5},hovertemplate='%{x}: %{y:.2f}%<extra>%{fullData.name}</extra>')
    style(growth,'U.S. housing and income growth, 1991–2024','Year','Growth since 1991 (%)')
    growth.update_layout(hovermode='x unified',margin={'t':100,'l':80,'r':30,'b':80})
    growth.update_xaxes(rangeslider={'visible':True,'thickness':.1})
    gaps=go.Figure();buttons=[]
    for i,year in enumerate(range(1991,2025)):
        rows=sorted([r for r in a if r['geography_level']=='state' and r['place_name']!='District of Columbia' and int(r['year'])==year],key=lambda r:float(r['growth_gap_pp']),reverse=True)
        assert len(rows)==50
        gaps.add_bar(x=[float(r['growth_gap_pp']) for r in rows],y=[r['place_name'] for r in rows],orientation='h',visible=year==2024,
            marker_color='#3659b8',customdata=[[float(r['hpi_growth_pct']),float(r['income_growth_pct'])] for r in rows],
            hovertemplate='%{y}<br>Gap: %{x:.2f} pp<br>Housing growth: %{customdata[0]:.2f}%<br>Income growth: %{customdata[1]:.2f}%<extra></extra>')
        visible=[False]*34;visible[i]=True
        buttons.append(dict(label=str(year),method='update',args=[{'visible':visible},{'title.text':f'{year}: housing growth minus income growth by state'}]))
    style(gaps,'2024: housing growth minus income growth by state','Gap since 1991 (percentage points)','',1400)
    gaps.update_layout(updatemenus=menu(buttons),showlegend=False);gaps.layout.updatemenus[0].active=33
    gaps.update_yaxes(autorange='reversed',automargin=True)
    ratio=go.Figure();buttons=[];national=next(float(r['home_value_to_income_ratio']) for r in d if r['geography_level']=='national' and r['year']=='2024')
    specs=[]
    for level,label in [('state','States'),('metro','Metro areas / divisions')]:
        rows=sorted([r for r in d if r['year']=='2024' and r['geography_level']==level and r['fhfa_place_name']!='District of Columbia'],key=lambda r:float(r['home_value_to_income_ratio']))
        assert len(rows)==(50 if level=='state' else 100)
        for subset,chosen in [('Highest 10',rows[-10:][::-1]),('Lowest 10',rows[:10]),('All',rows[::-1])]:
            specs.append((f'{label}: {subset}',chosen))
    for i,(label,rows) in enumerate(specs):
        ratio.add_bar(x=[float(r['home_value_to_income_ratio']) for r in rows],y=[r['fhfa_place_name'] for r in rows],orientation='h',visible=i==0,marker_color='#7655aa',
            customdata=[[float(r['median_home_value_acs']),float(r['median_household_income_acs'])] for r in rows],
            hovertemplate='%{y}<br>Value / income: %{x:.2f}×<br>Median home value: $%{customdata[0]:,.0f}<br>Median household income: $%{customdata[1]:,.0f}<extra></extra>')
        visible=[False]*len(specs);visible[i]=True
        buttons.append(dict(label=label,method='update',args=[{'visible':visible},{'height':max(600,30*len(rows)+220),'title.text':'2024 home-value-to-income ratios'}]))
    style(ratio,'2024 home-value-to-income ratios','Home value / annual household income','',600)
    ratio.update_layout(updatemenus=menu(buttons),showlegend=False,margin={'l':340,'r':40,'t':130,'b':80})
    ratio.update_yaxes(autorange='reversed',automargin=True)
    ratio.add_vline(x=national,line_dash='dash',line_color='#222')
    return growth,gaps,ratio

def build():
    figs=figures()
    titles=['National growth','State growth gaps','2024 dollar comparisons']
    notes=[
      'Drag the slider below the chart to focus on a period. Hover for exact values. Click a legend label to hide or show a series. Sources: annual FHFA purchase-only seasonally adjusted HPI and historical Census nominal income, rebased to 1991.',
      'Choose a year above the chart. All 50 states are ranked by cumulative housing growth minus income growth since 1991. D.C. is excluded. A negative gap means income growth was higher. This is a percentage-point gap, not a home-value-to-income ratio.',
      f'Choose states or the 100 selected metro areas/divisions, then highest, lowest, or all. The dashed line is the U.S. ratio ({next(float(r["home_value_to_income_ratio"]) for r in read("data/dollars/acs_dollar_comparison.csv") if r["geography_level"]=="national" and r["year"]=="2024"):.2f}×). Sources: ACS 2024 1-year B25077 and B19013. Ratios compare population medians, not mortgage-payment affordability. Point-estimate rankings are not tested for statistical significance. D.C. is excluded; metro areas are not city-proper boundaries.'
    ]
    parts=[]
    for i,(fig,title,note) in enumerate(zip(figs,titles,notes)):
        parts.append(f'<section id="section{i}"><h2>{title}</h2><p>{note}</p><div class="chart-wrap">'+fig.to_html(full_html=False,include_plotlyjs=False,config=CONFIG,div_id=f'chart{i}')+'</div></section>')
    html='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Housing and income — interactive findings</title><style>body{font:16px/1.6 system-ui,sans-serif;background:#f4f6fa;color:#17243b;margin:0}main{max-width:1250px;margin:auto;padding:32px 20px}h1{font-size:36px;line-height:1.2}h2{margin:0}section{background:white;border:1px solid #dce2ea;border-radius:14px;padding:24px;margin:24px 0}p{max-width:1000px;color:#42536b}nav{display:flex;gap:20px;flex-wrap:wrap}a{color:#3659b8}.chart-wrap{overflow-x:auto}.plotly-graph-div{min-width:650px}footer{padding:20px 0;font-size:14px}@media(max-width:700px){main{padding:16px 8px}section{padding:12px}h1{font-size:28px}}</style><script>'''+get_plotlyjs()+'''</script></head><body><main><h1>Housing &amp; income</h1><p>Interactive findings, 1991–2024. Hover to inspect values, drag to zoom, and double-click a chart to reset. Use chart menus to change the comparison. All data and charts work offline.</p><nav><a href="#section0">National growth</a><a href="#section1">State growth gaps</a><a href="#section2">2024 dollar comparisons</a></nav>'''+''.join(parts)+'''<section><h2>Earlier metro household income</h2><p>The location explorer now includes 129 verified income observations for 1999–2004 across 27 metro areas/divisions. The Household income view separates sources and dollar bases: 30 observations from 2000–2001 are in constant 2002 or 2003 dollars. These records do not supply a 1991 income baseline or extend the paired home-value ratios.</p><p><a href="index.html">Explore household income by location and year</a> · <a href="income-coverage.csv">Download area coverage</a> · <a href="income-sources.md">Sources and matching audit</a></p></section><footer>Growth and dollar comparisons use separate income sources. ACS dollar coverage begins in 2005 and excludes 2020; older metro boundaries are not harmonized. This report's dollar rankings use 2024 only. Metro income growth from a 1991 baseline is unavailable. On smaller screens, scroll horizontally within charts.</footer></main></body></html>'''
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(html,encoding='utf-8')
    return OUT

if __name__=='__main__':print(build())
