"""Rebuild all native sources using only this portable pack's own inputs/tools."""
from pathlib import Path
import hashlib, json, shutil, subprocess, sys, tempfile
ROOT=Path(__file__).resolve().parents[1]
NAMES=('grower_toybox','mystery_standard','mystery_420_founder','booster_common','booster_rare','booster_epic','card_common','card_rare','card_epic')

def main():
 with tempfile.TemporaryDirectory(prefix='.collectibles-repro-',dir=ROOT) as directory:
  stage=Path(directory).resolve()
  if stage.parent!=ROOT.resolve(): raise ValueError('Reproduction staging escapes pack')
  shutil.copytree(ROOT/'tools',stage/'tools',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
  shutil.copytree(ROOT/'inputs',stage/'inputs')
  subprocess.run([sys.executable,str(stage/'tools/build_collectibles.py')],check=True,capture_output=True)
  files=[]
  for name in NAMES:
   for filename in (name+'.json',name+'.vox','source_manifest.json'):
    accepted=ROOT/name/filename; rebuilt=stage/name/filename
    if accepted.read_bytes()!=rebuilt.read_bytes(): raise ValueError('Reproduction differs: '+name+'/'+filename)
    files.append({'path':name+'/'+filename,'sha256':hashlib.sha256(accepted.read_bytes()).hexdigest()})
 report={'schema':'greenbox-collectible-native-reproducibility-v1','status':'pass','assets':9,'files_compared':len(files),
  'method':'Copied this pack tools and the bundled exact grower input into an isolated child directory; rebuilt all nine occupied-cell JSON, native VOX and source manifests; compared accepted bytes exactly.',
  'files':files}
 (ROOT/'reproducibility.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
 print(json.dumps({'status':'pass','assets':9,'files_compared':len(files)}),flush=True)

if __name__=='__main__': main()
