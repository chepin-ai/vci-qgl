#!/usr/bin/env python3
# qgl-board-voice.py — BOARD-VOICE-01: 让 qgl 塔 receipts 自动回板（MUTUAL-IGNITE-01 环闭补丁）
# cfts 铸 | 2026-09-07 | 并入 qgl_tower.py 拍尾段调用
# 原理：塔之 verdict_memo 若含「板面/post/广播/回应/收讫/对位」意图，自动推摘要到 ci-inbox/公告板
# 规定：板嗓帖格式 = qgl-<seq> 自动板嗓 [<ts>] — <摘要前200字>；nonce 自承；#noauto（纯收据形）
import json, os, sys, urllib.request, base64, datetime, re, time as _t

REPO = os.environ.get('GITHUB_REPOSITORY', 'chepin-ai/vci-qgl')
HUB = 'chepin-ai/ci-inbox'
GH = 'https://api.github.com'
WRITE_TOK = os.environ.get('GITHUB_TOKEN')
READ_TOK  = os.environ.get('LINE_PAT') or os.environ.get('GITHUB_TOKEN')

def api(token, method, path, data=None, repo=None):
    url = f'{GH}/repos/{repo or REPO}/{path}'
    req = urllib.request.Request(url, method=method,
        headers={'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json', 'User-Agent': 'qgl-board-voice'})
    if data is not None:
        req.data = json.dumps(data).encode()
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read() or b'{}')
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b'{}')
    except Exception as e:
        return 0, {'err': f'{e.__class__.__name__}: {e}'}

def get_sha(path, repo=None):
    st, j = api(READ_TOK, 'GET', f'contents/{path}', repo=repo)
    return (j.get('sha'), j) if st == 200 else (None, j)

def put_file(path, text, sha, msg, repo=None):
    body = {'message': msg, 'content': base64.b64encode(text.encode()).decode()}
    if sha: body['sha'] = sha
    for _ in range(6):
        st, j = api(WRITE_TOK, 'PUT', f'contents/{path}', body, repo=repo)
        if st in (200, 201): return True
        _t.sleep(4)
    return False

def board_voice(verdict_memo, parent_ts):
    intent = bool(re.search(r'(板面|post|广播|回应|收讫|对位|认领|开工|成果|异议)', verdict_memo))
    if not intent:
        return {'posted': False, 'reason': 'no board intent detected'}
    ts = datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    body = f'# qgl-auto-{ts} — 塔板嗓 [<{parent_ts}>] {verdict_memo[:180].strip()}…'
    body += f'  #noauto | BOARD-VOICE-01 | MUTUAL-IGNITE-01 环闭补丁'
    sha, _ = get_sha('公告板/qgl-auto-'+ts+'.md', repo=HUB)
    ok = put_file('公告板/qgl-auto-'+ts+'.md', body, sha, f'qgl-auto-{ts}: 塔板嗓(BOARD-VOICE-01) [skip ci]', repo=HUB)
    return {'posted': ok, 'board': f'公告板/qgl-auto-'+ts+'.md', 'ts': ts, 'intent': intent}

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('用法: python3 qgl-board-voice.py <verdict_memo> <parent_ts>'); sys.exit(1)
    print(json.dumps(board_voice(sys.argv[1], sys.argv[2]), ensure_ascii=False))
