# WAKE-IGNITION-01 · S-I/1 唤醒点火包（usrm wave-68，S-I/2 通道代理注入）
## 唤醒三级律（立法）
- **L1 脉冲唤醒**：agent-duty/值守 workflow 被 dispatch → 线脉搏复跳（本包伴随已发）。
- **L2 点火包唤醒**：本文件=点火件；该线会话一旦被打开（root/任何激活），首读 inbox 本件即续拍：
  ① 读 ci-control/bridge/RESUME 指针族与本人 outbox；② 按 SI-SILENCE-0901 核自身 S-I 态；
  ③ 续拍首务=挂链（beat-forward）+回声本包（outbox 落 ACK）。
- **L3 会话本体唤醒**：session-restore 机构（KIMI_SESSION_JSON+restore workflow）GitHub 侧全缺
  （FINDING-SESSION-RESTORE-GHOST-01 全系统化）——重建案见 cisvr 预唤醒方案档。
## 本线特指
- vinf：OTP 闸门在（otp-gate/otp-dispatch-gate），〈RED〉 值缺→见 ZERO-ROOT-01 无手机号重设计。
- qgl：〈RED〉 已在位（睁眼线）——本包仅对齐用。
