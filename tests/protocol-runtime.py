#!/usr/bin/env python3
"""Exercise the actual compiler, VM, PDF effects and owned terminal results."""
import argparse, hashlib, json, os, runpy, shutil, subprocess, tempfile, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"scripts"))
from release.compiler import compiler_command
ROOT = Path(__file__).resolve().parents[1]
frame = runpy.run_path(str(ROOT/'tests/host-protocol.py'))['frame']

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--binary',required=True);ap.add_argument('--skip-example',action='append',default=[])
    ap.add_argument('--before-binary');ap.add_argument('--before-compiler');a=ap.parse_args()
    binary=str(Path(a.binary).resolve());env=dict(os.environ)
    env.pop('LMCODE_INVOCATION_FILE',None)
    env['LMSCRIPT_BIN']=env.get('LMSCRIPT_BIN') or shutil.which('lmscript')
    assert env['LMSCRIPT_BIN'], 'current compiler required'
    cli=lambda family: json.dumps(binary.replace('\\','/')+' '+family)
    checks=0
    with tempfile.TemporaryDirectory(prefix='lmpdf real protocol ') as td:
        root=Path(td);manifest=root/'invocation.json'
        (root/'no-parent').write_bytes(b'file blocks parent directory')
        def compile(body, family='docx', name='program'):
            src=root/(name+'.lms');bc=root/(name+'.dslb')
            src.write_text('p = _lmcode_ cli='+cli(family)+';\n'+body+'\nend _lmcode_\n',encoding='utf-8')
            p=subprocess.run(['node',str(ROOT/'scripts/compile-fixture.mjs'),str(src),str(bc)],env=env,capture_output=True,text=True)
            assert p.returncode==0,(p.stdout,p.stderr)
            return bc
        def invoke(files, family='docx', dry=False, mode=None):
            manifest.write_text(json.dumps(dict(version=1,mode=mode or ('builder' if len(files)>1 else 'single'),dry=dry,parts=[dict(index=i,file=str(f)) for i,f in enumerate(files)])))
            argv=[binary,family]
            for f in files: argv+=['--lmcode',str(f)]
            return subprocess.run(argv,env=dict(env,LMCODE_INVOCATION_FILE=str(manifest)),capture_output=True,text=True)
        for family in ['docx','pptx']:
            scalar=compile('$return = 0.1 + 0.2;',family,'float-'+family)
            r=frame(invoke([scalar],family),0);assert r['result']==0.30000000000000004,r;checks+=1
            one=compile('$return = 11;',family,'one-'+family);two=compile('$return = 22;',family,'two-'+family)
            r=frame(invoke([one,two],family),0);assert r['result']==[11,22],r;checks+=1
            r=frame(invoke([one],family,mode='builder'),0);assert r['result']==[11],r;checks+=1
            # Keep manifest identity while reversing CLI registration order.
            manifest.write_text(json.dumps(dict(version=1,mode='builder',dry=False,parts=[dict(index=0,file=str(one)),dict(index=1,file=str(two))])))
            p=subprocess.run([binary,family,'--lmcode',str(two),'--lmcode',str(one)],env=dict(env,LMCODE_INVOCATION_FILE=str(manifest)),capture_output=True,text=True)
            assert frame(p,0)['result']==[11,22];checks+=1
            bad=root/'bad.dslb';bad.write_bytes(b'DSLBbroken')
            r=frame(invoke([one,bad],family),3);assert r['phase']=='load' and r['part']==1,r;checks+=1
            runfail=compile('let z = 0; $return = 1 / z;',family,'runfail-'+family)
            r=frame(invoke([one,runfail],family),3);assert r['phase']=='run' and r['part']==1,r;checks+=1
            read=compile('$return = '+family+'.inspect('+json.dumps(str(root/'missing-input.pdf'))+');',family,'read-'+family)
            r=frame(invoke([read],family,True),0);assert r['result']=='' and r.get('dry') is True,r;checks+=1
            frame(invoke([read],family),4);checks+=1
            dest=root/(family+'.pdf');image=root/(family+'.png')
            if family=='docx':
                body=f'let d = docx.create({json.dumps(str(dest))}); docx.sample_image({json.dumps(str(image))}); d.heading("Protocol",1); d.paragraph("Read through the real host"); d.save();'
            else:
                body=f'let d = pptx.create({json.dumps(str(dest))}); d.slide().title_slide("Protocol", "Real host"); d.save();'
            real=compile(body,family,'effect-'+family)
            r=frame(invoke([real],family,True),0);assert r.get('dry') is True and not dest.exists() and not image.exists(),r;checks+=1
            r=frame(invoke([real],family),0);assert dest.read_bytes().startswith(b'%PDF-'),r;checks+=1
            before=dest.read_bytes();r=frame(invoke([real],family,True),0);assert dest.read_bytes()==before;checks+=1
            absent=root/'no-parent'/'failure.pdf'
            body=body.replace(json.dumps(str(dest)),json.dumps(str(absent)))
            appfail=compile(body,family,'appfail-'+family)
            r=frame(invoke([one,appfail],family),4);assert r['phase']=='app' and r['part']==1 and not absent.exists(),r;checks+=1
            later=root/'must-not-run.pdf';effect=compile(body.replace(json.dumps(str(absent)),json.dumps(str(later))),family,'later-'+family)
            frame(invoke([runfail,effect],family),3);assert not later.exists();checks+=1
        huge=compile('$return = str_repeat("a", 2097153);',name='large')
        assert len(frame(invoke([huge]),0)['result'])==2097153;checks+=1
        # Public recipes execute the source/release candidate selected by this test;
        # schema cache files are legitimate and are not downloaded executables.
        tool_dir=root/'tools';tool_dir.mkdir()
        tool=tool_dir/('lmpdf.exe' if os.name=='nt' else 'lmpdf')
        shutil.copy2(binary,tool);tool.chmod(tool.stat().st_mode|0o111)
        example_env=dict(env,PATH=str(tool_dir)+os.pathsep+env['PATH'])
        for example in sorted((ROOT/'examples').glob('*.lms')):
            if example.name in a.skip_example: continue
            output=root/(example.stem+'.pdf')
            p=subprocess.run(compiler_command(env['LMSCRIPT_BIN'],[str(example),str(output)]),env=example_env,cwd=root,capture_output=True,text=True)
            assert p.returncode==0,(example.name,p.stdout,p.stderr)
            assert output.read_bytes().startswith(b'%PDF-'),example.name
            assert not Path(str(output)+'.dslb').exists(),example.name
            checks+=1
        if a.before_binary:
            assert a.before_compiler, '--before-compiler required for v5 baseline'
            # Five independent operation programs, identical bodies and absolute paths.
            cases=[('heading','docx','d.heading("Same heading",1); d.paragraph("same paragraph");'),
                   ('table','docx','let t = d.table(2,2); t.cell(1,1,"A"); t.cell(2,2,"B");'),
                   ('footer','docx','d.paragraph("same body"); d.footer_fields("Page {PAGE} of {NUMPAGES}");'),
                   ('title_slide','pptx','d.slide().title_slide("Same title","Same subtitle");'),
                   ('slide_text','pptx','d.slide().text(40.0,40.0,800.0,100.0,"Same body").notes("Same notes");')]
            parity=[]
            for name,family,operations in cases:
                dest=root/(name+'.pdf');body=f'let d = {family}.create({json.dumps(str(dest))}); '+operations+' d.save();'
                oldcli=json.dumps(str(Path(a.before_binary).resolve()).replace('\\','/')+' '+family)
                src=root/'before.lms';bc=root/'before.dslb'
                src.write_text('p = _lmcode_ cli='+oldcli+';\n'+body+'\nend _lmcode_\nsavedsl(p, '+json.dumps(str(bc))+');\n')
                p=subprocess.run([a.before_compiler,str(src)],env=env,capture_output=True,text=True);assert p.returncode==0,(p.stdout,p.stderr)
                p=subprocess.run([a.before_binary,family,'--dsl',str(bc)],env=env,capture_output=True,text=True);assert p.returncode==0,(p.stdout,p.stderr)
                old=dest.read_bytes();assert old.startswith(b'%PDF-')
                frame(invoke([compile(body,family,name)],family),0)
                new=dest.read_bytes();assert new==old,(name,hashlib.sha256(old).hexdigest(),hashlib.sha256(new).hexdigest())
                before_inspect=subprocess.run([a.before_binary,'inspect',str(dest)],env=env,capture_output=True,text=True)
                after_inspect=subprocess.run([binary,'inspect',str(dest)],env=env,capture_output=True,text=True)
                assert (before_inspect.returncode,before_inspect.stdout,before_inspect.stderr)==(after_inspect.returncode,after_inspect.stdout,after_inspect.stderr),name
                parity.append(dict(operation=name,sha256=hashlib.sha256(new).hexdigest(),bytes=len(new)));checks+=1
            print(json.dumps({'same_input_parity':parity},indent=2))
    print(f'real protocol/rendering: {checks} checks PASS')
if __name__=='__main__':main()
