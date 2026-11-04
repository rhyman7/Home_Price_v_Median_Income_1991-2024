"""Download pinned ACS 1-year tables and geography labels for 2021–2024.
Existing snapshots are verified and reused, never silently refreshed.
"""
import hashlib,json,urllib.request
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/"data/raw/acs"
BASE="https://www2.census.gov/programs-surveys/acs/summary_file/"

def main():
 ROOT.mkdir(parents=True,exist_ok=True)
 mp=ROOT/"manifest.json"
 manifest=json.loads(mp.read_text()) if mp.exists() else []
 known={r["file"]:r for r in manifest}
 for year in range(2021,2025):
  jobs=[(f"{year}_{t}.dat",f"{BASE}{year}/table-based-SF/data/1YRData/acsdt1y{year}-{t}.dat") for t in ["b19013","b25077"]]
  jobs.append((f"{year}_geos.txt",f"{BASE}{year}/table-based-SF/documentation/Geos{year}1YR.txt"))
  for name,url in jobs:
   path=ROOT/name
   if name in known:
    if hashlib.sha256(path.read_bytes()).hexdigest()!=known[name]["sha256"]:raise ValueError(f"Checksum mismatch: {name}")
    continue
   if path.exists():raise FileExistsError(f"Untracked snapshot: {path}")
   with urllib.request.urlopen(url,timeout=45) as response:data=response.read()
   if not data.startswith((b"GEO_ID|",b"FILEID|")):raise ValueError(f"Unexpected format: {url}")
   path.write_bytes(data)
   manifest.append(dict(file=name,url=url,sha256=hashlib.sha256(data).hexdigest(),retrieved_utc=datetime.now(timezone.utc).isoformat()))
   mp.write_text(json.dumps(manifest,indent=2))
 print("Verified all 12 recent ACS source files")
if __name__=="__main__":main()
