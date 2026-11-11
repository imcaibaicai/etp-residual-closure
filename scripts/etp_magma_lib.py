# -*- coding: utf-8 -*-
"""ETP 岩浆判定库（Equational Theories Project）。

用途
====
把「一条律 + 一张有限乘法表」这种判定问题一次性包干净：
从 ``equations.txt`` 的律表达式构造求值器，判定某张乘法表是否 **满足** 某条律
（对所有变量赋值都成立），判定它是否 **反驳** 某条律（存在赋值使两侧不等），
以及把乘法表按可读形式打印出来。

依赖：仅标准库（不依赖 numpy，避免 cp314 wheel 问题）。

数据约定
========
* 律的权威来源是 ``$ETP_HOME/parsimagma/data/etp/equations.txt``，**行序即编号，
  1-indexed**（第 1 行 = E1）。本库的 ``get_law(i)`` 按这个约定取第 i 条。
* 律的文本文法：变量为单个小写字母（``equations.txt`` 里只出现 ``x y z w``），
  二元运算写作 ``◇``（U+25C7）。打印器只在「复合子项」外加括号，所以
  ``◇`` 按 **右结合** 解析：``x ◇ y ◇ z`` == ``x ◇ (y ◇ z)``。
  只要输入是 ETP 自己打印的表达式，这个约定不会产生歧义。
* 一张 n 阶岩浆的乘法表就是 n×n 的 0-based 整数矩阵，``table[x][y]`` 表示
  ``x ◇ y``。这和 ``smallest_magma_examples.txt`` / ``refutations*.txt``
  里 ``[[0, 1], [1, 0]]`` 这种写法完全一致。
* 律的 **元数（arity）** 取「出现过的变量名集合的大小」；赋值枚举对该集合里的
  每个变量各取 0..n-1。未出现的变量不参与枚举（等价于全称量化不约束它）。

快速上手
========
::

    from etp_magma_lib import Magma, get_law, satisfies, refutes, format_table

    m = Magma([[0, 0], [1, 0]])
    e476 = get_law(476)                       # 从 equations.txt 按行号取
    assert refutes(m, e476)                   # 这张表反驳 E476
    assert satisfies(m, get_law(3))           # 但它满足 E3（x = x ◇ x）

    print(format_table(m))

主要接口
========
解析
    ``parse_law(text)`` / ``parse_term(text)`` / ``Law``
    ``load_equations(path)`` / ``get_equation_text(eid)`` / ``get_law(eid)``
    ``lookup_law_id(text)``

岩浆与求值
    ``Magma``（含 ``.n`` / ``.table`` / ``.op`` / ``from_json`` / ``to_json``）
    ``evaluate(term, magma, assignment)``
    ``compile_term(term)`` / ``run_program(prog, magma, values)``

判定
    ``counterexample(magma, law)``  返回一个反例赋值，满足则返回 None
    ``satisfies(magma, law)``
    ``refutes(magma, law)``
    ``is_implication_counterexample(table, hyp_law, tgt_law)``
    ``verify_implication(table, hyp, tgt)``  给「假设满足 / 目标被反驳」的完整判定书

杂项
    ``format_table(magma)`` / ``print_table(magma)``
    ``all_magmas(n)``
    ``canonical_form(magma)``   在全部标号重排下字典序最小的代表
"""

from __future__ import annotations

import itertools
import json
import os
from dataclasses import dataclass, field
from typing import Dict, Iterable, Iterator, List, Optional, Sequence, Tuple

__all__ = [
    "EQUATIONS_PATH",
    "Term",
    "Law",
    "Magma",
    "parse_term",
    "parse_law",
    "load_equations",
    "get_equation_text",
    "get_law",
    "lookup_law_id",
    "compile_term",
    "run_program",
    "evaluate",
    "counterexample",
    "satisfies",
    "refutes",
    "is_implication_counterexample",
    "verify_implication",
    "format_table",
    "print_table",
    "all_magmas",
    "canonical_form",
]

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------

#: ``equations.txt`` 的默认路径（行序即编号，1-indexed）。
#: 环境变量 ``ETP_EQUATIONS_PATH`` 优先，其次由 ``ETP_HOME`` 推出。
EQUATIONS_PATH = os.environ.get("ETP_EQUATIONS_PATH") or os.path.join(
    os.environ.get("ETP_HOME", ""), "parsimagma", "data", "etp", "equations.txt"
)

#: 二元运算符号。ETP 全库统一用这个字符。
OP_SYMBOL = "\u25c7"

_VAR_TAG = "var"
_OP_TAG = "op"


# ---------------------------------------------------------------------------
# 词法 / 语法
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> List[str]:
    """把律文本切成一串 token：变量字母、``(``、``)``、``=``、``◇``。

    空白一律丢弃。出现这三种以外的字符直接 ``ValueError``，避免把错字默默吃掉。
    """
    out: List[str] = []
    for ch in text:
        if ch.isspace():
            continue
        if ch in "()=" or ch == OP_SYMBOL or ch.isalpha():
            out.append(ch)
        else:
            raise ValueError(f"律表达式里出现无法识别的字符 {ch!r}：{text!r}")
    return out


def _parse_atom(tokens: Sequence[str], i: int) -> Tuple["Term", int]:
    """解析一个原子项：变量字母，或一对括号里的完整项。"""
    if i >= len(tokens):
        raise ValueError(f"表达式意外结束：{list(tokens)!r}")
    tok = tokens[i]
    if tok.isalpha():
        return (_VAR_TAG, tok), i + 1
    if tok == "(":
        inner, j = _parse_chain(tokens, i + 1)
        if j >= len(tokens) or tokens[j] != ")":
            raise ValueError(f"括号未闭合：{list(tokens)!r} 位置 {j}")
        return inner, j + 1
    raise ValueError(f"此处应为变量或 '('，实际是 {tok!r}：{list(tokens)!r}")


def _parse_chain(tokens: Sequence[str], i: int) -> Tuple["Term", int]:
    """解析一条 ``◇`` 运算链，**右结合**：``atom [◇ chain]``。"""
    lhs, i = _parse_atom(tokens, i)
    if i < len(tokens) and tokens[i] == OP_SYMBOL:
        rhs, i = _parse_chain(tokens, i + 1)
        return (_OP_TAG, lhs, rhs), i
    return lhs, i


def parse_term(text: str) -> "Term":
    """把单个项（不含 ``=``）解析成嵌套元组。

    返回的项是 ``("var", "x")`` 或 ``("op", 左项, 右项)``。

    >>> parse_term("x ◇ (x ◇ y)")
    ('op', ('var', 'x'), ('op', ('var', 'x'), ('var', 'y')))
    """
    tokens = _tokenize(text)
    term, i = _parse_chain(tokens, 0)
    if i != len(tokens):
        raise ValueError(f"解析在位置 {i} 提前结束，剩余 {tokens[i:]!r}：{text!r}")
    return term


def term_variables(term: "Term", acc: Optional[set] = None) -> set:
    """收集一个项里出现的全部变量名。"""
    if acc is None:
        acc = set()
    stack = [term]
    while stack:
        t = stack.pop()
        if t[0] == _VAR_TAG:
            acc.add(t[1])
        else:
            stack.append(t[1])
            stack.append(t[2])
    return acc


@dataclass(frozen=True)
class Law:
    """一条等式律。

    属性
    ----
    lhs, rhs : Term
        左右两侧的语法树。
    variables : tuple[str, ...]
        出现过的变量名，按字母序排列（赋值枚举就按这个顺序展开）。
    text : str
        原始文本，便于回显与查重。

    ``arity`` 是 ``len(variables)`` 的别名属性。
    """

    lhs: "Term"
    rhs: "Term"
    variables: Tuple[str, ...]
    text: str = ""

    @property
    def arity(self) -> int:
        """变量个数，也就是判定时需要枚举的维度。"""
        return len(self.variables)

    def __str__(self) -> str:  # pragma: no cover - 仅用于人读
        return self.text or f"{render_term(self.lhs)} = {render_term(self.rhs)}"


def parse_law(text: str) -> Law:
    """把 ``"x = x ◇ x"`` 这样的文本解析成 :class:`Law`。"""
    tokens = _tokenize(text)
    lhs, i = _parse_chain(tokens, 0)
    if i >= len(tokens) or tokens[i] != "=":
        raise ValueError(f"缺少 '='：{text!r}")
    rhs, i = _parse_chain(tokens, i + 1)
    if i != len(tokens):
        raise ValueError(f"'=' 右侧有残留 token {tokens[i:]!r}：{text!r}")
    names = tuple(sorted(term_variables(lhs) | term_variables(rhs)))
    return Law(lhs=lhs, rhs=rhs, variables=names, text=text.strip())


def render_term(term: "Term") -> str:
    """把语法树渲染回 ETP 风格的文本（复合子项一律加括号）。"""
    if term[0] == _VAR_TAG:
        return term[1]
    return f"({render_term(term[1])} {OP_SYMBOL} {render_term(term[2])})"


# ---------------------------------------------------------------------------
# equations.txt 读写
# ---------------------------------------------------------------------------

_EQUATION_CACHE: Dict[str, List[str]] = {}
_LAW_CACHE: Dict[Tuple[str, int], Law] = {}


def load_equations(path: str = EQUATIONS_PATH) -> List[str]:
    """读入 ``equations.txt``，返回按行排列的原始文本（下标 0 对应 E1）。

    结果按路径缓存，重复调用不再读盘。文件按 UTF-8 读取；ETP 的
    ``equations.txt`` 是无 BOM 的纯 UTF-8，``◇`` 是 U+25C7。
    """
    key = os.path.abspath(path)
    if key not in _EQUATION_CACHE:
        with open(key, "r", encoding="utf-8") as fh:
            _EQUATION_CACHE[key] = [ln.rstrip("\n") for ln in fh]
    return _EQUATION_CACHE[key]


def get_equation_text(eid: int, path: str = EQUATIONS_PATH) -> str:
    """按 1-indexed 编号取律的原始文本。

    >>> get_equation_text(476).startswith("x = y")
    True
    """
    lines = load_equations(path)
    if not 1 <= eid <= len(lines):
        raise IndexError(f"律编号 {eid} 越界，本文件共 {len(lines)} 条")
    return lines[eid - 1]


def get_law(eid: int, path: str = EQUATIONS_PATH) -> Law:
    """按 1-indexed 编号取解析好的 :class:`Law`（带缓存）。"""
    key = (os.path.abspath(path), eid)
    if key not in _LAW_CACHE:
        _LAW_CACHE[key] = parse_law(get_equation_text(eid, path))
    return _LAW_CACHE[key]


def lookup_law_id(text: str, path: str = EQUATIONS_PATH) -> int:
    """反查：给定律的文本，返回它在 ``equations.txt`` 里的编号（找不到返回 -1）。

    比较前会统一去掉所有空白并规范化 ``◇`` 两侧，因此多打空格也能命中。
    """
    target = "".join(text.split())
    for idx, line in enumerate(load_equations(path), 1):
        if "".join(line.split()) == target:
            return idx
    return -1


# ---------------------------------------------------------------------------
# 求值器
# ---------------------------------------------------------------------------

def compile_term(
    term: "Term", var_index: Optional[Dict[str, int]] = None
) -> List[Tuple[int, int]]:
    """把项编译成「栈机器」指令序列，供 :func:`run_program` 高速反复执行。

    指令只有两种：``(0, k)`` = 把第 k 个变量的取值压栈；``(1, _)`` = 弹出两个
    元素 ``b, a``（先 b 后 a），压入 ``a ◇ b``。

    参数
    ----
    term : Term
        要编译的语法树。
    var_index : dict, 可选
        变量名 → 赋值元组下标。省略时按变量名的字母序自动编号，此时
        ``run_program`` 的 ``values`` 必须是「按字母序排列的变量取值」。
    """
    if var_index is None:
        var_index = {name: k for k, name in enumerate(sorted(term_variables(term)))}
    prog: List[Tuple[int, int]] = []

    def emit(t: "Term") -> None:
        # 显式栈的深度优先展开，避免深树递归爆栈（ETP 最深也就十层，稳妥起见）。
        stack: List[object] = [t]
        while stack:
            node = stack.pop()
            if isinstance(node, str):  # 后序标记：这里是运算
                prog.append((1, 0))
            elif node[0] == _VAR_TAG:
                prog.append((0, var_index[node[1]]))
            else:
                stack.append("op")
                stack.append(node[2])
                stack.append(node[1])

    emit(term)
    return prog


def run_program(
    prog: Sequence[Tuple[int, int]], magma: "Magma", values: Sequence[int]
) -> int:
    """在给定赋值下执行 :func:`compile_term` 生成的程序，返回结果元素序号。"""
    table = magma.flat
    n = magma.n
    stack: List[int] = []
    for kind, arg in prog:
        if kind == 0:
            stack.append(values[arg])
        else:
            b = stack.pop()
            a = stack.pop()
            stack.append(table[a * n + b])
    return stack[0]


def evaluate(term: "Term", magma: "Magma", assignment: Dict[str, int]) -> int:
    """在 ``assignment``（变量名 → 元素）下求一个项的值。

    >>> evaluate(parse_term("x ◇ y"), Magma([[1, 1], [0, 1]]), {"x": 0, "y": 1})
    1
    """
    names = tuple(sorted(assignment))
    values = [assignment[name] for name in names]
    prog = compile_term(term, {name: k for k, name in enumerate(names)})
    return run_program(prog, magma, values)


# ---------------------------------------------------------------------------
# 岩浆
# ---------------------------------------------------------------------------

class Magma:
    """一张 n 阶有限乘法表。

    参数
    ----
    table : 可迭代对象
        n×n 的 0-based 整数矩阵，``table[x][y]`` 就是 ``x ◇ y``。
        扁平序列请用 :meth:`from_raw`。

    属性
    ----
    n : int
        载体大小。
    table : list[list[int]]
        原样的二维表（构造时做过合法性检查）。
    flat : tuple[int, ...]
        行优先展开的一维表，求值器用它换速度。
    """

    __slots__ = ("table", "flat", "n")

    def __init__(self, table: Iterable):
        rows = [[int(v) for v in row] for row in table]
        if not rows:
            raise ValueError("乘法表为空")
        size = len(rows)
        if any(len(row) != size for row in rows):
            raise ValueError(f"乘法表不是方阵：各行长度为 {[len(r) for r in rows]}")
        flat: List[int] = []
        for row in rows:
            for v in row:
                iv = int(v)
                if not 0 <= iv < size:
                    raise ValueError(f"表项 {iv} 超出载体 0..{size - 1}")
                flat.append(iv)
        self.n = size
        self.table = [list(r) for r in rows]
        self.flat = tuple(flat)

    # -- 基本操作 ---------------------------------------------------------

    def op(self, x: int, y: int) -> int:
        """``x ◇ y``。"""
        return self.flat[x * self.n + y]

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Magma) and self.flat == other.flat

    def __hash__(self) -> int:
        return hash(self.flat)

    def __repr__(self) -> str:
        return f"Magma(n={self.n}, table={self.table})"

    # -- 序列化 -----------------------------------------------------------

    @classmethod
    def from_json(cls, text: str) -> "Magma":
        """解析 ``smallest_magma_examples.txt`` / ``refutations*.txt`` 里的表。

        >>> Magma.from_json("[[0, 1], [1, 1]]").n
        2
        """
        return cls(json.loads(text))

    def to_json(self) -> str:
        """输出与 ETP 数据文件同格式的紧凑 JSON（``[[0, 1], [1, 1]]``）。"""
        return json.dumps(self.table)

    @classmethod
    def from_raw(cls, values: Sequence[int], n: int) -> "Magma":
        """从扁平表 + 阶数构造。"""
        vals = list(values)
        if len(vals) != n * n:
            raise ValueError(f"扁平表长度 {len(vals)} 与 n={n} 不匹配")
        return cls([vals[i * n:(i + 1) * n] for i in range(n)])


def all_magmas(n: int) -> Iterator[Magma]:
    """枚举 n 阶的全部岩浆（共 ``n**(n*n)`` 张），按行优先字典序。

    仅供 n ≤ 3 使用（n=4 已是 4^16 ≈ 4.3e9，不要用这个函数穷举）。
    """
    slots = n * n
    for code in itertools.product(range(n), repeat=slots):
        yield Magma.from_raw(code, n)


# ---------------------------------------------------------------------------
# 判定：满足 / 反驳
# ---------------------------------------------------------------------------

def _assignments(n: int, arity: int) -> Iterator[Tuple[int, ...]]:
    """枚举全部 ``n**arity`` 个赋值元组。"""
    return itertools.product(range(n), repeat=arity)


def counterexample(magma: Magma, law: Law) -> Optional[Tuple[int, ...]]:
    """找一条律在某张表里的**反例**。

    返回第一个使两侧取值不等的赋值元组（顺序与 ``law.variables`` 一致），
    若该表满足这条律则返回 ``None``。

    语义：对 ``law.variables`` 里每个变量独立地跑遍 ``0..n-1``，
    这是「对所有变量赋值都成立」的否定——即存在一组具体取值使两侧不等。
    """
    prog_l = compile_term(law.lhs, {v: i for i, v in enumerate(law.variables)})
    prog_r = compile_term(law.rhs, {v: i for i, v in enumerate(law.variables)})
    for values in _assignments(magma.n, law.arity):
        if run_program(prog_l, magma, values) != run_program(prog_r, magma, values):
            return values
    return None


def satisfies(magma: Magma, law: Law) -> bool:
    """该表是否**满足**这条律（对所有变量赋值两侧都相等）。"""
    return counterexample(magma, law) is None


def refutes(magma: Magma, law: Law) -> bool:
    """该表是否**反驳**这条律（存在一组赋值使两侧不等）。"""
    return counterexample(magma, law) is not None


def refuted_laws(magma: Magma, laws: Iterable[Law]) -> List[int]:
    """批量判定：返回 ``laws`` 里被这张表反驳的那些律的下标（调用方给顺序）。"""
    return [i for i, law in enumerate(laws) if refutes(magma, law)]


def is_implication_counterexample(
    table, hyp: Law, tgt: Law, magma: Optional[Magma] = None
) -> bool:
    """这张表是否构成 ``hyp ⊨ tgt`` 的反例：满足 hyp，同时反驳 tgt。

    ``table`` 可以是 :class:`Magma`、``[[...]]`` 嵌套列表或 JSON 文本。
    """
    m = magma or _as_magma(table)
    return satisfies(m, hyp) and refutes(m, tgt)


def verify_implication(table, hyp: Law, tgt: Law, label: str = "") -> dict:
    """对一张表做完整判定书：假设是否满足、目标是否被反驳、反例赋值是什么。

    返回的字典字段
    ------
    ``label`` / ``n`` / ``satisfies_hypothesis`` / ``refutes_target``
    ``ok``（两者同时成立，即这张表确实是反例）
    ``target_counterexample``（反例赋值元组，或 None）
    ``table``（二维表，方便直接贴进报告）
    """
    m = _as_magma(table)
    ce = counterexample(m, tgt)
    hyp_ok = satisfies(m, hyp)
    return {
        "label": label,
        "n": m.n,
        "satisfies_hypothesis": hyp_ok,
        "refutes_target": ce is not None,
        "ok": hyp_ok and ce is not None,
        "target_counterexample": ce,
        "target_variables": tgt.variables,
        "table": m.table,
    }


def _as_magma(table) -> Magma:
    """把 Magma / 嵌套列表 / JSON 文本统一成 :class:`Magma`。"""
    if isinstance(table, Magma):
        return table
    if isinstance(table, str):
        return Magma.from_json(table)
    return Magma(table)


# ---------------------------------------------------------------------------
# 打印
# ---------------------------------------------------------------------------

def format_table(magma: Magma, header: str = OP_SYMBOL) -> str:
    """把乘法表渲染成等宽文本（表头用 ``◇``，左下角空白）。

    例（2 阶）::

        ◇ 0 1
        0 1 1
        1 0 1
    """
    n = magma.n
    width = max(len(str(n - 1)), 1)
    lines = [" " * width + " " + " ".join(f"{y:>{width}}" for y in range(n))]
    for x in range(n):
        cells = " ".join(f"{magma.op(x, y):>{width}}" for y in range(n))
        lines.append(f"{x:>{width}} {cells}")
    return "\n".join(lines)


def print_table(magma: Magma, header: str = OP_SYMBOL) -> None:
    """把 :func:`format_table` 的结果打印出来。"""
    print(format_table(magma, header))


# ---------------------------------------------------------------------------
# 标号重排
# ---------------------------------------------------------------------------

def canonical_form(magma: Magma) -> Tuple[int, ...]:
    """在全部 ``n!`` 种标号重排下，返回字典序最小的扁平表。

    重排按同构的标准写法：标号映射 ``p: 旧标号 → 新标号``，
    ``T2[p[x]][p[y]] = p[T[x][y]]``。

    用途：搜索里判重（同构的两张表会有相同的规范形）。
    代价 ``n! * n**2``，n=5 也就 3000 次操作。
    """
    n = magma.n
    flat = magma.flat
    best: Optional[Tuple[int, ...]] = None
    for perm in itertools.permutations(range(n)):
        t2 = [0] * (n * n)
        for x in range(n):
            px = perm[x]
            base = x * n
            for y in range(n):
                t2[px * n + perm[y]] = perm[flat[base + y]]
        key = tuple(t2)
        if best is None or key < best:
            best = key
    assert best is not None
    return best


# ---------------------------------------------------------------------------
# 自检（`python etp_magma_lib.py`）
# ---------------------------------------------------------------------------

def _smoke_test() -> None:
    """最小冒烟测试：解析、求值、判定、打印各走一遍。"""
    assert parse_term("x ◇ (x ◇ y)") == (
        _OP_TAG,
        (_VAR_TAG, "x"),
        (_OP_TAG, (_VAR_TAG, "x"), (_VAR_TAG, "y")),
    )
    m = Magma([[0, 0], [1, 0]])
    assert refutes(m, get_law(476)), "该表应当反驳 E476"
    assert satisfies(Magma([[0, 1], [1, 1]]), get_law(3)), "该表应当满足 E3（幂等）"
    assert canonical_form(Magma([[0, 0], [0, 1]])) == canonical_form(
        Magma([[0, 1], [1, 1]])
    ), "同构的表应当有相同规范形"
    assert canonical_form(Magma([[0, 1], [1, 1]])) != canonical_form(
        Magma([[1, 1], [1, 0]])
    ), "不同构的表不应当撞规范形"
    print("smoke test ok; E476 =", get_equation_text(476))
    print(format_table(m))


if __name__ == "__main__":
    _smoke_test()
