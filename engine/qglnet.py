"""qglnet — 盘件化网络助件（内核死亡后一行重建，TOKEN自钥匙面自取，绝不打印）"""
import os, json, time, base64, urllib.request, urllib.parse

_TOKEN_PATH = os.path.expanduser('~/.keys/qgl-first-route-token')
COOL = {}

def token():
    return open(_TOKEN_PATH).read().strip()

def gh(method, path, body=None, tok=None):
    tok = tok or token()
    if path in COOL and time.time() < COOL[path]:
        return (429, {'local_cool': int(COOL[path] - time.time())})
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request('https://api.github.com' + path, data=data, method=method,
        headers={'Authorization': 'Bearer ' + tok,
                 'Accept': 'application/vnd.github+json',
                 'X-GitHub-Api-Version': '2022-11-28',
                 'User-Agent': 'qgl-kernel'})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return (r.status, json.loads(r.read() or b'{}'))
    except urllib.error.HTTPError as e:
        b = e.read().decode()[:400]
        if e.code == 403 and 'rate limit' in b.lower():
            COOL[path] = time.time() + 300
            return (429, {'cooled': 300})
        return (e.code, {'raw': b})

def putfq(full, path, content, msg):
    p = urllib.parse.quote(path)
    st, r = gh('GET', f'/repos/{full}/contents/{p}')
    body = {'message': msg, 'content': base64.b64encode(content.encode()).decode()}
    if st == 200:
        body['sha'] = r['sha']
    return gh('PUT', f'/repos/{full}/contents/{p}', body)

def getf(full, path):
    st, r = gh('GET', f'/repos/{full}/contents/{urllib.parse.quote(path)}')
    if st == 200:
        return base64.b64decode(r['content']).decode()
    return None

def ls(full, path):
    st, r = gh('GET', f'/repos/{full}/contents/{urllib.parse.quote(path)}')
    return r if st == 200 else []
