"""Rebuild native sources in an isolated pack copy and compare accepted bytes."""
from pathlib import Path
import hashlib, json, shutil, subprocess, sys, tempfile

ROOT=Path(__file__).resolve().parents[1]
NAMES=('rasta_grower','corporate_boss','robot','chef','blonde_lady','party_woman','skeleton')

def main():
    with tempfile.TemporaryDirectory(prefix='.garden-repro-',dir=ROOT) as directory:
        stage=Path(directory).resolve()
        if stage.parent!=ROOT.resolve(): raise ValueError('Reproduction staging must stay within this pack')
        shutil.copytree(ROOT/'tools',stage/'tools',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        subprocess.run([sys.executable,str(stage/'tools'/'build_garden.py')],check=True,capture_output=True)
        files=[]
        for name in NAMES:
            accepted=ROOT/name
            for source in sorted(accepted.glob('*.vox'))+[accepted/(name+'.json'),accepted/'source_manifest.json']:
                rebuilt=stage/name/source.name
                if rebuilt.read_bytes()!=source.read_bytes(): raise ValueError('Reproduction differs: '+str(source.relative_to(ROOT)))
                files.append({'path':source.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(source.read_bytes()).hexdigest()})
    report={'schema':'greenbox-garden-native-reproducibility-v1','status':'pass',
      'method':'Run copied portable authoring tools in an isolated pack under this directory; compare every assembled and part VOX, source JSON and manifest byte.',
      'assets':7,'files_compared':len(files),'files':files}
    (ROOT/'reproducibility.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({'status':'pass','assets':7,'files_compared':len(files)}))

if __name__=='__main__': main()
