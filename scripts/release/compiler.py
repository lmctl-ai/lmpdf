"""Launch npm-provided LMScript shims without Windows CreateProcess ambiguity."""
import os
from pathlib import Path


def compiler_command(compiler, args, platform=None, bash_path=None):
    platform = platform or os.name
    if platform != 'nt' or str(compiler).lower().endswith('.exe'):
        return [str(compiler), *map(str, args)]
    # Git Bash is part of the hosted Windows build environment. Pass arguments
    # positionally: never interpolate fixture paths into shell program text.
    bash = bash_path or str(Path(os.environ.get('ProgramFiles', 'C:/Program Files'))/'Git/bin/bash.exe')
    if not Path(bash).is_file():
        raise RuntimeError(f'Git Bash is required to launch the npm LMScript shim: {bash}')
    name = str(compiler)
    if name.lower().endswith('.cmd') and Path(name[:-4]).is_file():
        name = name[:-4]
    return [bash, '-c', 'exec "$@"', 'lmpdf-compiler', name, *map(str, args)]
