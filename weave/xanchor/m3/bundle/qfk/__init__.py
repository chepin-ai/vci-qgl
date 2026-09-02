"""QFK（qf-know）— QF-OS 链-哈希知识底座快速原型包（v0.2）。

八模块 ↔ 七洞察映射（详见 README.md 架构映射表）：
  findings=I1 残差引擎主循环 / chain=I2 三档验证脊柱 / beacon=I6 熵锚+软抽签 /
  circle=I2+I4 圈签链头 / field=I5 Git+prolly+beacon 场 / tensor=I1+I7 张量微内核 /
  trans=I4 四语契约 / ipmp=三机 MIP（无星）互证（v0.2 新增，结构同构不升格）。
  一切规模钉在 I7 物理面内（写者≤5、圈≤30、log10FLOPs≲12）。
硬约束：纯 Python≥3.11；依赖仅 numpy+cryptography；链内部全 256-bit；
12-hex 仅显示别名永不入验证路径；LLM 权重恒 0；测试零网络。
"""

from . import beacon, chain, circle, field, findings, ipmp, tensor, trans  # noqa: F401

__version__ = "0.2.0"
