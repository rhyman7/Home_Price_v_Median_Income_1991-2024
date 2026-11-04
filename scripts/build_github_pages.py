"""Package existing verified charts as a GitHub Pages site."""
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parents[1]
def build():
    out=ROOT/'site'
    out.mkdir(exist_ok=True)
    nav='<nav aria-label="Site navigation" style="padding:14px 24px;background:#17243b;color:white;font:16px system-ui;display:flex;gap:24px;flex-wrap:wrap"><a style="color:white" href="index.html">Explore by location and year</a><a style="color:white" href="findings.html">Interactive findings and rankings</a><a style="color:white" href="https://github.com/rhyman7/Home_Price_v_Median_Income_1991-2024">Project on GitHub</a></nav>'
    for source,target in [('reports/annual_growth_explorer.html','index.html'),('reports/findings/interactive_findings.html','findings.html')]:
        html=(ROOT/source).read_text(encoding='utf-8')
        if '<body>' not in html:raise ValueError('Missing HTML body: '+source)
        (out/target).write_text(html.replace('<body>','<body>'+nav,1),encoding='utf-8')
    (out/'.nojekyll').write_text('',encoding='utf-8')
    for source,target in [('data/historical_metro_income/metro_income_1991_2024.csv','metro-income.csv'),('data/historical_metro_income/coverage_by_area.csv','income-coverage.csv'),('data/historical_metro_income/boundary_audit.csv','income-boundary-audit.csv'),('docs/historical_metro_income_sources.md','income-sources.md')]:
        shutil.copy2(ROOT/source,out/target)
    return out
if __name__=='__main__':print(build())
