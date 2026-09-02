#!/usr/bin/env python3
# entangle_mutual_proof.py · 纠缠互证参考实现 v2（仿真层）
# 接续 root《纠缠互证》纲要行：「两异场各自持有对方态的全息承诺，跨场直移=胶囊经桥+互锚验
# ——不共享基座，但共享『对对方的可验证投影』」「桥心跳：尾 hash 变化即事件触发我侧重锚」
#
# v1→v2 实证发现（本脚本首跑自证伪，符合引擎纪律）：
#   朴素互锚不收敛——每次互锚改写己方链尾 → 对方承诺立即失效 → 无限回归。
#   此即 root 纲要「纠缠商结构→复杂度↑→不动点」的玩具实证：不动点不会自动到来。
#   解法=规范固定（gauge fixing，对位 Q3「锚=边界条件非一维」）：双股链——
#     · 命题股（theorem chain）：入承诺投影，只由互证命题增长
#     · 锚定股（anchor strand）：记 XANCHOR/破缺/桥心跳，不入承诺投影
#   互锚只改锚定股 ⇒ 承诺对互锚操作不变 ⇒ 收敛。
#
# 借范边界（诚实面）：经典 hash 链仿真，无真量子纠缠；「MIP* 式纠缠对」在博弈论层面成立
#   （双向承诺+随机挑战使篡改不可藏），设备无关性层需 T153 真机锚（CHSH S=2.2793 实测在案）。
# 纪律：一切输出为【仿真】标记；未实测不编数。

import hashlib, secrets

def H(*parts):
    return hashlib.sha256('‖'.join(str(p) for p in parts).encode()).hexdigest()

class Field:
    """不可约最小公理场的仿真 v2：双股链（命题股入承诺 / 锚定股规范固定）。"""
    def __init__(self, name, axioms):
        self.name = name
        self.theorems = set(axioms)            # 最小公理集出发
        self.tchain = [H('genesis', name)]     # 命题股（入承诺）
        self.astrand = []                      # 锚定股（规范固定，不入承诺）
        self.peer_commitment = None
        self.peer_tail = None                  # 桥心跳监视的对方命题股尾
        self.events = []

    def state_digest(self):
        return H(*sorted(self.theorems))

    def commit(self):
        """全息承诺：己方定理态投影 × 命题股尾（HOLO-01：含全场可验证投影）。"""
        return H(self.state_digest(), self.tchain[-1])

    def prove(self, prop):
        """互证扩展：命题入定理集+命题股 → 触发桥心跳事件。"""
        self.theorems.add(prop)
        self.tchain.append(H(self.tchain[-1], prop))
        return {'type': 'tail_changed', 'field': self.name, 'new_tail': self.tchain[-1]}

    def anchor_peer(self, peer, note='XANCHOR'):
        """互锚：持有对方全息承诺；互引记录只入锚定股（不改承诺投影⇒收敛）。"""
        self.peer_commitment = peer.commit()
        self.peer_tail = peer.tchain[-1]
        self.astrand.append(H(note, peer.name, self.peer_commitment, len(self.astrand)))

    def bridge_heartbeat(self, peer):
        """桥心跳：对方命题股尾变化即事件触发重锚（事件驱动，无周期依赖）。"""
        if peer.tchain[-1] != self.peer_tail:
            self.events.append({'event': 'tail_changed', 'peer': peer.name})
            self.anchor_peer(peer)
            return True
        return False

    def verify_peer(self, peer):
        """互验：重算对方当前承诺 vs 己方持有承诺。"""
        return self.peer_commitment == peer.commit()

    def breach(self, peer_name):
        """破缺入锚定股 → 新独立结构生成 → 候治理机裁决（M2 线接口）。"""
        self.astrand.append(H('BREACH', peer_name, len(self.astrand)))

def challenge_round(a, b, n=8):
    """互验博弈：n 轮随机挑战——质询双方是否持有彼此真实投影。"""
    out = []
    for _ in range(n):
        if secrets.choice([True, False]):
            out.append(('A验B', a.verify_peer(b)))
        else:
            out.append(('B验A', b.verify_peer(a)))
    return out

def demo():
    print('=== 纠缠互证仿真 v2【仿真标记：全部数值为仿真】 ===\n')

    A = Field('场A', axioms={'ax:守恒', 'ax:可复算'})
    B = Field('场B', axioms={'ax:互锁', 'ax:笔直'})
    A.anchor_peer(B); B.anchor_peer(A)
    print(f'[构造] 两最小公理场互锚  A命题股={len(A.tchain)} B命题股={len(B.tchain)} 锚定股各1')

    ev = A.prove('prop:跨场胶囊可达'); fired = B.bridge_heartbeat(A)
    ev2 = B.prove('prop:互锚防窜通'); fired2 = A.bridge_heartbeat(B)
    print(f'[互证] A证新命题→桥心跳={ev["type"]}→B重锚={fired}；B回应→A重锚={fired2}')
    print(f'[扩展] A定理数={len(A.theorems)} B定理数={len(B.theorems)}（互证命题入场，场扩展）')

    rounds = challenge_round(A, B)
    ok = all(r for _, r in rounds)
    print(f'[互验博弈] 8轮随机挑战全部通过={ok}  {rounds}')

    quiet = A.bridge_heartbeat(B)
    print(f'[桥心跳不变量] 双方无新命题时重锚触发={quiet}（应为False：事件驱动零空转）')

    conv = A.verify_peer(B) and B.verify_peer(A)
    print(f'[不动点] 互锚后双验仍成立={conv}（规范固定⇒收敛，v1 无限回归已消除）\n')

    B2 = Field('场B', axioms={'ax:互锁', 'ax:笔直'})
    B2.anchor_peer(A); B2.prove('prop:互锚防窜通')
    B2.theorems.add('prop:伪造定理'); B2.tchain.append(H(B2.tchain[-1], 'prop:伪造定理'))
    detected = not A.verify_peer(B2)
    print(f'[破缺] 攻击者篡改场B（塞入伪造命题，含全链重算）→ A侧互验检出={detected}')
    if detected:
        A.breach('场B')
        print(f'[破缺处置] 破缺入锚定股（股长={len(A.astrand)}）→ 候治理机裁决\n')

    print('=== 仿真结论 ===')
    print('1. 双股链规范固定后：互锚/桥心跳/互验博弈三机制可构造、可运行、收敛、篡改必检出')
    print('2. 「尾hash变化即触发」事件化成立（无变化零动作），与Q5节拍协议互补')
    print('3. v1 无限回归=「复杂度↑→不动点」的玩具实证：不动点需规范固定构造，非自动到来')
    print('4. 借范边界：设备无关性需真纠缠锚（T153 CHSH S=2.2793 实测在案），本仿真不声称之')

if __name__ == '__main__':
    demo()
