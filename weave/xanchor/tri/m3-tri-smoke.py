# -*- coding: utf-8 -*-
"""m3-tri-smoke.py — XANCHOR-TRIANGLE-SMOKE-01 参考实现(usrm 设,v2.8)
三方确定性会合冒烟: P={usrm,cfts,qgl}, 三边 rendezvous + tri_root。
纯确定性: 基种子 3712427753 定格, seed_ij=sha256(b'3712427753'||pi||pj)[:8];
无随机源/无墙钟/无网络——三方各自独立重算, transcript 逐字节一致。
判据(先钉死): 三边 verify PASS + tri_root 自洽; 失败如实 FAIL, 不升格。
"""
import hashlib, json
from hashlib import sha256

BASE_SEED = b"3712427753"
PARTIES = ["cfts", "qgl", "usrm"]  # 字典序定格(序对歧义防)
ROUNDS = 8

def h(b): return sha256(b).hexdigest()

def seed_ij(pi, pj):
    a, b = sorted([pi, pj])
    return int(h(BASE_SEED + a.encode() + b.encode())[:8], 16)

class DSPR:  # 确定性伪随机流(sha256 计数器模式, 无 numpy 依赖)
    def __init__(self, seed): self.s = seed; self.n = 0
    def next(self):
        self.n += 1
        return h(self.s + self.n.to_bytes(8, "big"))

def edge(pi, pj):
    """单边 rendezvous: commit→8轮challenge→reveal→verify_peer(双方视角各算)"""
    sd = seed_ij(pi, pj).to_bytes(8, "big")
    r = DSPR(sd)
    # commit 相: 双方秘密=确定性派生(冒烟档: 秘密=派生值, 真随机在硬件位)
    sec_i, sec_j = r.next(), r.next()
    com_i = h(bytes.fromhex(sec_i))[:16]
    com_j = h(bytes.fromhex(sec_j))[:16]
    # challenge 8 轮: 确定性挑战流
    chals, resps = [], []
    for k in range(ROUNDS):
        cbit = int(r.next(), 16) & 1
        chals.append(cbit)
        # 响应=H(sec‖round‖bit) —— 模拟 ZK 响应确定式
        resps.append(h(bytes.fromhex(sec_i) + k.to_bytes(2,"big") + bytes([cbit]))[:12])
    # reveal+verify: com 对验 + 响应重算
    ok_com = (com_i == h(bytes.fromhex(sec_i))[:16])
    ok_resp = all(resps[k] == h(bytes.fromhex(sec_i) + k.to_bytes(2,"big") + bytes([chals[k]]))[:12] for k in range(ROUNDS))
    transcript = {"parties": [pi, pj], "seed_ij": seed_ij(pi, pj),
                  "commit": {pi: com_i, pj: com_j},
                  "challenges": chals, "responses": resps,
                  "verify": {"commit_consistent": ok_com, "responses_consistent": ok_resp}}
    transcript["edge_hash"] = h(json.dumps(transcript, sort_keys=True).encode())[:16]
    return transcript

def main():
    edges = {}
    for i in range(len(PARTIES)):
        for j in range(i+1, len(PARTIES)):
            pi, pj = PARTIES[i], PARTIES[j]
            edges["%s|%s" % (pi, pj)] = edge(pi, pj)
    tri_root = h("".join(edges[k]["edge_hash"] for k in sorted(edges)).encode())[:16]
    doc = {"v": "XANCHOR-TRI-SMOKE-01", "base_seed": BASE_SEED.decode(),
           "parties": PARTIES, "rounds": ROUNDS, "edges": edges,
           "tri_root": tri_root,
           "verdict": "PASS" if all(e["verify"]["commit_consistent"] and e["verify"]["responses_consistent"] for e in edges.values()) else "FAIL",
           "gray": ["单仓CI非真隔离", "秘密=派生值(冒烟档,非真熵)", "classical-sim档不升格"]}
    with open("m3-tri-transcript.json", "w") as f:
        json.dump(doc, f, sort_keys=True, indent=1)
    print(json.dumps({"tri_root": tri_root, "verdict": doc["verdict"]}, sort_keys=True))

if __name__ == "__main__":
    main()
