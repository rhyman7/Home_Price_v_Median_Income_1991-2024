"""Package the national-income benchmark explorer for GitHub Pages."""
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parents[1]

def build():
    out=ROOT/'site'
    out.mkdir(exist_ok=True)
    nav='<nav aria-label="Site navigation" style="padding:14px 24px;background:#17243b;color:white;font:16px system-ui;display:flex;gap:24px;flex-wrap:wrap"><a style="color:white" href="index.html">Explore housing &amp; U.S. income</a><a style="color:white" href="national-income.csv">Download all locations</a><a style="color:white" href="https://github.com/rhyman7/Home_Price_v_Median_Income_1991-2024">Project on GitHub</a></nav>'
    html=(ROOT/'reports/annual_growth_explorer.html').read_text(encoding='utf-8')
    if '<body>' not in html:raise ValueError('Missing HTML body')
    (out/'index.html').write_text(html.replace('<body>','<body>'+nav,1),encoding='utf-8')
    (out/'findings.html').write_text('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="0;url=index.html"><title>Housing &amp; U.S. income</title></head><body><p>The site now compares every location with U.S. income. <a href="index.html">Open the updated charts</a>.</p></body></html>',encoding='utf-8')
    (out/'.nojekyll').write_text('',encoding='utf-8')
    shutil.copy2(ROOT/'reports/national_income_comparison.csv',out/'national-income.csv')
    shutil.copy2(ROOT/'docs/national_income_comparison.md',out/'income-sources.md')
    # Retire published local-income downloads; research originals remain in data/.
    for name in ('metro-income.csv','income-coverage.csv','income-boundary-audit.csv'):
        (out/name).unlink(missing_ok=True)
    return out
if __name__=='__main__':print(build())
