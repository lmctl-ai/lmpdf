#!/usr/bin/env python3
"""Native real/dry safety checks. Resource bounds belong to these caller probes only."""
import argparse,ctypes,json,os,runpy,shutil,struct,subprocess,tempfile,zlib,sys,signal
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
frame=runpy.run_path(str(ROOT/'tests/host-protocol.py'))['frame']
def darwin_memory_run(command,env,cwd,limit_bytes=1024**3):
    # Darwin does not support the AS rlimit used by the Linux probe. A new
    # private session gives this explicit caller a PID ownership boundary;
    # bound resident memory of decoder descendants, preserving the outer host
    # so its structured error handling is still exercised. No deadline/sleep.
    def core_limit():
        import resource
        resource.setrlimit(resource.RLIMIT_CORE,(0,resource.getrlimit(resource.RLIMIT_CORE)[1]))
    p=subprocess.Popen(command,cwd=cwd,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True,preexec_fn=core_limit)
    killed=[]
    while p.poll() is None:
        sample=subprocess.run(['ps','-axo','pid=,pgid=,rss='],capture_output=True,text=True,check=True)
        for line in sample.stdout.splitlines():
            fields=line.split()
            if not fields:continue
            pid,group=map(int,fields[:2])
            if group!=p.pid or pid==p.pid:continue
            rss=int(fields[2])
            if rss*1024>limit_bytes:
                try:
                    if os.getpgid(pid)==p.pid:os.kill(pid,signal.SIGKILL);killed.append(pid)
                except ProcessLookupError:pass
    out,err=p.communicate()
    if killed:err+='\ncaller RSS bound signalled owned worker PIDs '+repr(killed)+'\n'
    return subprocess.CompletedProcess(command,p.returncode,out,err)

def bounded_run(command,env,cwd,memory=False):
    def limits():
        import resource
        resource.setrlimit(resource.RLIMIT_CORE,(0,0))
        if memory:resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3))
    if sys.platform=='darwin' and memory:return darwin_memory_run(command,env,cwd)
    if os.name!='nt':return subprocess.run(command,cwd=cwd,env=env,capture_output=True,text=True,preexec_fn=limits)
    if not memory:return subprocess.run(command,cwd=cwd,env=env,capture_output=True,text=True)
    # A per-process Job limit is inherited by worker descendants. Start suspended
    # so no decoder can run before this explicit test-caller limit is attached.
    from ctypes import wintypes as W
    class Basic(ctypes.Structure):_fields_=[('process_time',ctypes.c_int64),('job_time',ctypes.c_int64),('flags',W.DWORD),('min_working',ctypes.c_size_t),('max_working',ctypes.c_size_t),('active',W.DWORD),('affinity',ctypes.c_size_t),('priority',W.DWORD),('scheduling',W.DWORD)]
    class IO(ctypes.Structure):_fields_=[(n,ctypes.c_uint64) for n in ['read_ops','write_ops','other_ops','read_bytes','write_bytes','other_bytes']]
    class Extended(ctypes.Structure):_fields_=[('basic',Basic),('io',IO),('process_memory',ctypes.c_size_t),('job_memory',ctypes.c_size_t),('peak_process',ctypes.c_size_t),('peak_job',ctypes.c_size_t)]
    k=ctypes.WinDLL('kernel32',use_last_error=True);k.CreateJobObjectW.restype=W.HANDLE;k.SetInformationJobObject.argtypes=[W.HANDLE,ctypes.c_int,ctypes.c_void_p,W.DWORD];k.AssignProcessToJobObject.argtypes=[W.HANDLE,W.HANDLE];k.CloseHandle.argtypes=[W.HANDLE]
    job=k.CreateJobObjectW(None,None);info=Extended();info.basic.flags=0x100;info.process_memory=1024**3
    assert job and k.SetInformationJobObject(job,9,ctypes.byref(info),ctypes.sizeof(info)),ctypes.get_last_error()
    p=subprocess.Popen(command,cwd=cwd,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,creationflags=0x4)
    try:
        if not k.AssignProcessToJobObject(job,W.HANDLE(int(p._handle))):p.kill();p.wait();raise AssertionError('cannot assign owned child to caller memory Job')
        nt=ctypes.WinDLL('ntdll');nt.NtResumeProcess.argtypes=[W.HANDLE];assert nt.NtResumeProcess(W.HANDLE(int(p._handle)))==0
        out,err=p.communicate();return subprocess.CompletedProcess(command,p.returncode,out,err)
    finally:k.CloseHandle(job)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--binary',required=True);a=ap.parse_args();binary=str(Path(a.binary).resolve());compiler=os.environ.get('LMSCRIPT_BIN') or shutil.which('lmscript');assert compiler
    with tempfile.TemporaryDirectory(prefix='html-doc-safety-') as folder:
        root=Path(folder);env=dict(os.environ,HOME=str(root/'home'),LMCTL_HOME=str(root/'home/profile'),LMSCRIPT_BIN=compiler);(root/'home').mkdir();checks=0
        def invoke(name,xml,css='',error=False,memory=False,warning=False):
            nonlocal checks
            source=root/(name+'.lms');bc=root/(name+'.lmcb');dest=root/(name+'.pdf')
            source.write_text('xml='+json.dumps(xml,ensure_ascii=False)+'; css='+json.dumps(css,ensure_ascii=False)+';\np=_lmcode_ cli='+json.dumps(binary.replace('\\','/')+' docx')+';\nlet d=docx.create('+json.dumps(str(dest))+');\nd.html_doc(${xml},${css});\nd.save();\nend _lmcode_\n',encoding='utf8')
            p=subprocess.run(['node',str(ROOT/'scripts/compile-fixture.mjs'),str(source),str(bc)],env=env,text=True,capture_output=True);assert p.returncode==0,p.stdout+p.stderr
            for dry in [False,True]:
                manifest=root/'invocation.json';manifest.write_text(json.dumps({'version':1,'mode':'single','dry':dry,'parts':[{'index':0,'file':str(bc)}]}));before=dest.read_bytes() if dest.exists() else None
                p=bounded_run([binary,'docx','--lmcode',str(bc)],dict(env,LMCODE_INVOCATION_FILE=str(manifest)),root,memory)
                value=frame(p,3 if error else 0)
                if error:assert value['code']=='RUN_HOST' and value.get('line') and 'html-doc line' in value['message'],value
                if dry:assert value.get('dry') is True and before==(dest.read_bytes() if dest.exists() else None),(name,value)
                if warning:assert 'matched no elements' in p.stderr,p.stderr
                checks+=1
        html=lambda x:'<article xmlns="http://www.w3.org/1999/xhtml">'+x+'</article>'
        for tag in ['div','span']:
            inner=('<'+tag+'>')*15000+('<p>DEEP</p>' if tag=='div' else 'DEEP')+('</'+tag+'>')*15000
            invoke('deep-'+tag,html(inner if tag=='div' else '<p>'+inner+'</p>'))
        def chunk(k,v):return struct.pack('>I',len(v))+k+v+struct.pack('>I',zlib.crc32(k+v)&0xffffffff)
        (root/'huge.png').write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',100000,100000,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(b'\0'))+chunk(b'IEND',b''))
        # Mutate the SOF dimensions of a checked-in valid JPEG, without a new imaging dependency.
        data=bytearray((ROOT/'tests/fixtures/small.jpg').read_bytes());pos=data.index(b'\xff\xc0');data[pos+5:pos+9]=b'\xff\xff\xff\xff';(root/'huge.jpg').write_bytes(data)
        for ext in ['png','jpg']:invoke('huge-'+ext,html('<img src="huge.'+ext+'" alt="" width="80pt" height="30pt"/>'),error=True,memory=True)
        invoke('missing-glyph',html('<p>Before '+chr(0x378)+' after</p>'),error=True)
        invoke('warning',html('<p>plain</p>'),'<style xmlns="urn:lmctl:css:1"><rule select=".absent"><set name="color" value="#123456"/></rule></style>',warning=True)
        print(f'html-doc native safety: {checks} real/dry controls PASS')
if __name__=='__main__':main()
