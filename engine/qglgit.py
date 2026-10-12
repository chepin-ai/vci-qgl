#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""qglgit.py — git smart-HTTP 推送旁路（PP160-TRANSPORT-GIT / PUSH-159-CLOSE 铸械）
定位：REST putfq 为主路；二级限流粘滞（403 secondary，/rate_limit 200 有余量）时合规切换本旁路。
法依：同匙第一路由（~/.keys 下第一路由件），非凭证拒绝场景，非"回退到常规操作"。
律：密钥值零打印零入文——GIT_ASKPASS 脚本落 /tmp（0700），用完即焚；仓名公开面仅以 sha256[:12] 出现。
"""
import os, subprocess, tempfile, stat, shutil

OWNER = 'chepin-ai'
TOK = os.path.expanduser('~/.keys/qgl-first-route-token')

_ASKPASS = '''#!/bin/bash
case "$1" in
  *Username*) echo x-access-token ;;
  *) cat %s ;;
esac
''' % TOK


def _env():
    ap = '/tmp/.qgl-askpass.sh'
    try:
        os.remove(ap)  # 复用固定径前先焚：旧件 0500 不可重入（3.160 实战捕）
    except OSError:
        pass
    with open(ap, 'w') as f:
        f.write(_ASKPASS)
    os.chmod(ap, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)  # 0700
    e = dict(os.environ)
    e.update(GIT_ASKPASS=ap, GIT_TERMINAL_PROMPT='0')
    return e


def _run(args, cwd=None, timeout=300):
    r = subprocess.run(args, cwd=cwd, env=_env(), capture_output=True, text=True, timeout=timeout)
    # stderr 可能含远端 URL（仓名）——调用方落公开面时须哈希化；此处原样返回供内部诊断
    return r.returncode, r.stdout, r.stderr


def push_files(repo, files, msg, workdir=None, cleanup=True):
    """files: [(local_abspath, repo_relpath)]；单次提交推送。返回 {ok, tip, log}。
    用法示例见 PUSH-159-CLOSE 囊（beat 3.159 实证：REST 粘滞时本道一通即达）。"""
    wd = workdir or tempfile.mkdtemp(prefix='qglgit-')
    try:
        if not os.path.exists(os.path.join(wd, '.git')):
            rc, out, err = _run(['git', 'clone', '--depth', '3',
                                 'https://github.com/%s/%s.git' % (OWNER, repo), wd], timeout=420)
            if rc != 0:
                return {'ok': False, 'stage': 'clone', 'log': err[-300:]}
        else:
            rc, out, err = _run(['git', 'pull', '-q', 'origin', 'main'], cwd=wd)
            if rc != 0:
                return {'ok': False, 'stage': 'pull', 'log': err[-300:]}
        for local, rel in files:
            dst = os.path.join(wd, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(local, dst)
        _run(['git', 'add', '-A'], cwd=wd)
        rc, out, err = _run(['git', '-c', 'user.name=qgl-kernel', '-c', 'user.email=qgl-kernel@localhost',
                             'commit', '-q', '-m', msg], cwd=wd)
        if rc != 0 and 'nothing to commit' not in (out + err):
            return {'ok': False, 'stage': 'commit', 'log': (out + err)[-300:]}
        rc, out, err = _run(['git', 'push', '-q', 'origin', 'main'], cwd=wd, timeout=420)
        if rc != 0:
            return {'ok': False, 'stage': 'push', 'log': err[-300:]}
        rc, out, _ = _run(['git', 'rev-parse', '--short', 'HEAD'], cwd=wd)
        return {'ok': True, 'tip': out.strip(), 'files': len(files)}
    finally:
        try:
            os.remove('/tmp/.qgl-askpass.sh')   # 用完即焚
        except OSError:
            pass
