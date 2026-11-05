#!/usr/bin/env python3
"""Offline controls for the actual release installer: exact pin and integrity."""
import hashlib,os,subprocess,tempfile,unittest,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class Install(unittest.TestCase):
 def case(self,corrupt=False,old_pin=False):
  with tempfile.TemporaryDirectory(prefix='lmpdf-install-pin-') as td:
   t=Path(td);(t/'examples').mkdir();(t/'tools').mkdir();(t/'scripts').mkdir()
   shutil.copy2(ROOT/'scripts/install-hosts.sh',t/'scripts/install-hosts.sh')
   (t/'examples/a.lms').write_text('p = _lmcode_ cli="lmpdf docx" install="github:lmctl-ai/lmpdf@v0.2.2";\n')
   (t/'tools/gh').write_text('''#!/usr/bin/env python3
import sys,os,hashlib
from pathlib import Path
a=sys.argv[1:]
if a[:2]==['repo','view']:print('{"name":"lmpdf"}')
elif a[:2]==['release','list']:print('v0.2.3' if os.environ.get('OLD_PIN') else 'v0.2.3\\nv0.2.2')
elif a[:2]==['release','view']:print(a[2])
elif a[0]=='api':print('v0.2.3')
elif a[:2]==['release','download']:
 tag=a[2];d=Path(a[a.index('--dir')+1]);data=b'#!/bin/sh\\nexit 0\\n# '+tag.encode()+b'\\n'
 (d/'lmpdf-linux-x64').write_bytes(data)
 (d/'SHA256SUMS').write_text(('0'*64 if os.environ.get('CORRUPT') else hashlib.sha256(data).hexdigest())+'  lmpdf-linux-x64\\n')
else:sys.exit(55)
''');(t/'tools/gh').chmod(0o755)
   env=dict(os.environ,PATH=str(t/'tools')+os.pathsep+os.environ['PATH'],RUNNER_TEMP=str(t),LMCTL_HOST_BIN_DIR=str(t/'installed'),CORRUPT='yes' if corrupt else '',OLD_PIN='yes' if old_pin else '')
   r=subprocess.run(['bash','scripts/install-hosts.sh'],cwd=t,env=env,text=True,capture_output=True)
   data=(t/'installed/lmpdf').read_text() if (t/'installed/lmpdf').exists() else ''
   return r,data
 def test_exact_pin_beats_newer_latest(self):
  r,data=self.case();self.assertEqual(r.returncode,0,r.stdout+r.stderr);self.assertIn('# v0.2.2',data)
 def test_exact_pin_need_not_be_in_recent_release_page(self):
  r,data=self.case(old_pin=True);self.assertEqual(r.returncode,0,r.stdout+r.stderr);self.assertIn('# v0.2.2',data)
 def test_bad_checksum_fails_before_install(self):
  r,data=self.case(True);self.assertNotEqual(r.returncode,0,r.stdout+r.stderr);self.assertEqual(data,'');self.assertIn('FAILED',r.stdout+r.stderr)
 def test_verified_candidate_pin_bypasses_unpublished_tag_lookup(self):
  with tempfile.TemporaryDirectory(prefix='lmpdf-install-candidate-') as td:
   t=Path(td);(t/'examples').mkdir();(t/'tools').mkdir();(t/'candidate').mkdir();(t/'installed').mkdir();(t/'scripts').mkdir()
   shutil.copy2(ROOT/'scripts/install-hosts.sh',t/'scripts/install-hosts.sh')
   (t/'examples/a.lms').write_text('p = _lmcode_ cli="lmpdf docx" install="github:lmctl-ai/lmpdf@v0.2.99";\n')
   (t/'candidate/lmpdf').write_text('#!/bin/sh\nexit 0\n');(t/'candidate/lmpdf').chmod(0o755)
   (t/'tools/gh').write_text('''#!/usr/bin/env python3
import sys
from pathlib import Path
Path("calls.log").open("a").write(" ".join(sys.argv[1:])+"\\n")
a=sys.argv[1:]
if a[:2]==['repo','view']:print('{"name":"lmpdf"}')
elif a[0]=='api':print('v0.2.14')
else:sys.exit(55)
''')
   (t/'tools/gh').chmod(0o755)
   path=os.pathsep.join([str(t/'candidate'),str(t/'tools'),os.environ['PATH']])
   env=dict(os.environ,PATH=path,RUNNER_TEMP=str(t),LMCTL_HOST_BIN_DIR=str(t/'installed'),LMPDF_QUALIFY_TAG='v0.2.99')
   result=subprocess.run(['bash','scripts/install-hosts.sh'],cwd=t,env=env,text=True,capture_output=True)
   calls=(t/'calls.log').read_text()
   self.assertEqual(result.returncode,0,result.stdout+result.stderr)
   self.assertIn('using the verified candidate already staged on PATH',result.stdout)
   self.assertNotIn('release view v0.2.99',calls)
   self.assertNotIn('release download v0.2.99',calls)
   self.assertFalse((t/'installed/lmpdf').exists())
 def test_schema_probe_does_not_inherit_gh_token(self):
  with tempfile.TemporaryDirectory(prefix='lmpdf-install-token-') as td:
   t=Path(td);(t/'examples').mkdir();(t/'tools').mkdir();(t/'scripts').mkdir()
   shutil.copy2(ROOT/'scripts/install-hosts.sh',t/'scripts/install-hosts.sh')
   (t/'examples/a.lms').write_text('p = _lmcode_ cli="lmpdf docx" install="github:lmctl-ai/lmpdf@v0.2.2";\n')
   record=t/'host-token.json'
   host=("#!"+sys.executable+"\nimport json,os,pathlib,sys\n"
         "if '--lmcode-schema' in sys.argv:\n"
         " pathlib.Path("+repr(str(record))+').write_text(json.dumps(bool(os.environ.get(\'GH_TOKEN\'))))\n'
         " print('{}')\n").encode()
   (t/'tools/gh').write_text('''#!/usr/bin/env python3
import sys,hashlib
from pathlib import Path
a=sys.argv[1:]
if a[:2]==['repo','view']:print('{"name":"lmpdf"}')
elif a[:2]==['release','list']:print('v0.2.3\\nv0.2.2')
elif a[:2]==['release','view']:print(a[2])
elif a[0]=='api':print('v0.2.3')
elif a[:2]==['release','download']:
 d=Path(a[a.index('--dir')+1]);d.mkdir(parents=True,exist_ok=True);(d/'lmpdf-linux-x64').write_bytes(bytes.fromhex("'''+host.hex()+'''"));(d/'SHA256SUMS').write_text(hashlib.sha256(bytes.fromhex("'''+host.hex()+'''" )).hexdigest()+'  lmpdf-linux-x64\\n')
else:sys.exit(2)
''');(t/'tools/gh').chmod(0o755)
   env=dict(os.environ,PATH=str(t/'tools')+os.pathsep+os.environ['PATH'],RUNNER_TEMP=str(t),LMCTL_HOST_BIN_DIR=str(t/'installed'),GH_TOKEN='SYNTHETIC_ONLY')
   result=subprocess.run(['bash','scripts/install-hosts.sh'],cwd=t,env=env,text=True,capture_output=True)
   self.assertEqual(result.returncode,0,result.stdout+result.stderr)
   self.assertEqual((t/'host-token.json').read_text(),'false')
if __name__=='__main__':unittest.main()
