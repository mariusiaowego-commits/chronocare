"""Person and lab-metric aliases for natural-language queries."""

from __future__ import annotations

# Canonical person.name in DB → spoken / alternate names (longest match wins).
PERSON_ALIASES: dict[str, tuple[str, ...]] = {
    "qian": (
        "钱精华",
        "qian",
        "妈妈",
        "母亲",
        "mama",
        "mum",
        "mom",
        "钱",
        "妈",
    ),
    "tjh": (
        "tjh",
        "爸爸",
        "父亲",
        "papa",
        "dad",
        "汤",
        "爸",
    ),
}

# Canonical lab item name (as stored in lab_results.tests[].name) → aliases.
METRIC_ALIASES: dict[str, tuple[str, ...]] = {
    "糖化血红蛋白": ("糖化血红蛋白", "hba1c", "hb a1c", "a1c", "糖化血红", "糖化血色素", "糖化"),
    "丙氨酸氨基转移酶": ("丙氨酸氨基转移酶", "谷丙转氨酶", "alt", "gpt"),
    "天门冬氨酸氨基转移酶": ("天门冬氨酸氨基转移酶", "天冬氨酸氨基转移酶", "谷草转氨酶", "ast", "got"),
    "碱性磷酸酶": ("碱性磷酸酶", "alp"),
    "γ-谷氨酰转移酶": ("γ-谷氨酰转移酶", "谷氨酰转移酶", "ggt", "γ-gt", "γgt"),
    "总胆红素": ("总胆红素", "tbil", "t-bil"),
    "直接胆红素": ("直接胆红素", "dbil", "d-bil"),
    "总蛋白": ("总蛋白", "tp"),
    "白蛋白": ("白蛋白", "alb"),
    "球蛋白": ("球蛋白", "glb"),
    "尿素": ("尿素", "urea", "bun", "尿素氮"),
    "肌酐": ("肌酐", "cr", "creatinine", "crea"),
    "估算肾小球滤过率": ("估算肾小球滤过率", "egfr", "gfr", "肾小球滤过率"),
    "尿微量白蛋白": ("尿微量白蛋白", "malb", "微量白蛋白", "尿微量白"),
    "尿白蛋白/尿肌酐": ("尿白蛋白/尿肌酐", "acr", "尿白蛋白肌酐比", "白蛋白肌酐比"),
    "尿液肌酐测定": ("尿液肌酐测定", "尿肌酐"),
    "红细胞计数": ("红细胞计数", "rbc"),
    "血红蛋白浓度": ("血红蛋白浓度", "血红蛋白", "hgb", "hb"),
    "红细胞压积": ("红细胞压积", "hct", "红细胞比积"),
    "平均红细胞体积": ("平均红细胞体积", "mcv"),
    "平均红细胞血红蛋白含量": ("平均红细胞血红蛋白含量", "mch"),
    "白细胞计数": ("白细胞计数", "白细胞", "wbc", "白血球", "白血球计数"),
    "血小板计数": ("血小板计数", "plt", "血小板"),
    "中性粒细胞百分比": ("中性粒细胞百分比", "neut%", "中性粒细胞"),
    "D-二聚体": ("D-二聚体", "d二聚体", "ddimer", "d-dimer"),
    "胰岛素（空腹）": ("胰岛素（空腹）", "空腹胰岛素", "胰岛素"),
    "C肽（空腹）": ("C肽（空腹）", "空腹c肽", "c肽", "c-peptide", "c peptide"),
    "醛固酮质谱法": ("醛固酮质谱法", "醛固酮"),
    "肾素活性质谱法": ("肾素活性质谱法", "肾素活性", "肾素"),
    "醛固酮肾素活性比值": ("醛固酮肾素活性比值", "arr"),
    "血管紧张素II质谱法": ("血管紧张素II质谱法", "血管紧张素ii", "血管紧张素"),
    "葡萄糖（空腹）": ("葡萄糖（空腹）", "空腹血糖", "血糖", "fbg", "fpg"),
    "葡萄糖": ("尿糖", "glu"),
    "糖化白蛋白": ("糖化白蛋白", "糖化白", "ga"),
    "总胆固醇": ("总胆固醇", "胆固醇", "tch", "tc", "chol"),
    "甘油三酯": ("甘油三酯", "甘油三脂", "tg", "trig"),
    "低密度脂蛋白胆固醇": ("低密度脂蛋白胆固醇", "低密度脂蛋白", "ldl", "ldl-c"),
    "高密度脂蛋白胆固醇": ("高密度脂蛋白胆固醇", "高密度脂蛋白", "hdl", "hdl-c"),
    "尿酸": ("尿酸", "ua", "uric"),
    "钠": ("血钠", "钠离子", "na"),
    "钾": ("血钾", "钾离子", "k"),
    "氯": ("血氯", "氯离子", "cl"),
    "蛋白": ("尿蛋白", "蛋白"),
    "比重": ("比重", "sg"),
    "ph": ("ph", "酸碱度"),
    "亚硝酸盐": ("亚硝酸盐", "nit"),
    "肌酸激酶": ("肌酸激酶", "ck"),
    "前白蛋白": ("前白蛋白", "palb"),
}

# Combo queries → constituent lab names (matched against stored tests).
PANELS: dict[str, tuple[str, ...]] = {
    "肝功能": (
        "丙氨酸氨基转移酶",
        "天门冬氨酸氨基转移酶",
        "碱性磷酸酶",
        "γ-谷氨酰转移酶",
        "总胆红素",
        "直接胆红素",
        "总蛋白",
        "白蛋白",
        "球蛋白",
        "前白蛋白",
    ),
    "转氨酶": ("丙氨酸氨基转移酶", "天门冬氨酸氨基转移酶"),
    "肾功能": ("尿素", "肌酐", "估算肾小球滤过率", "尿酸"),
    "血脂": ("总胆固醇", "甘油三酯", "低密度脂蛋白胆固醇", "高密度脂蛋白胆固醇"),
    "血常规": (
        "红细胞计数",
        "血红蛋白浓度",
        "白细胞计数",
        "血小板计数",
        "中性粒细胞百分比",
        "淋巴细胞百分比",
    ),
    "尿常规": ("颜色", "比重", "pH", "蛋白", "葡萄糖", "酮体", "亚硝酸盐", "尿隐血", "白细胞酯酶"),
    "电解质": ("钠", "钾", "氯", "二氧化碳", "阴离子隙"),
    "心肌酶": ("肌酸激酶", "肌酸激酶MB亚型"),
}

PANEL_ALIASES: dict[str, tuple[str, ...]] = {
    "肝功能": ("肝功能", "肝功", "肝脏功能", "肝酶"),
    "转氨酶": ("转氨酶", "转氨酶高"),
    "肾功能": ("肾功能", "肾功", "肾脏功能"),
    "血脂": ("血脂", "血脂四项", "脂代谢"),
    "血常规": ("血常规", "血象"),
    "尿常规": ("尿常规", "尿检"),
    "电解质": ("电解质", "离子"),
    "心肌酶": ("心肌酶", "心酶"),
}


def normalize_text(text: str) -> str:
    """Lowercase, strip spaces, unify punctuation for matching."""
    if not text:
        return ""
    table = str.maketrans(
        {
            "（": "(",
            "）": ")",
            "％": "%",
            "—": "-",
            "–": "-",
            "／": "/",
            "γ": "γ",
        }
    )
    out = text.translate(table).lower()
    return "".join(out.split())


def _alias_pairs(mapping: dict[str, tuple[str, ...]]) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for canonical, aliases in mapping.items():
        seen: set[str] = set()
        for alias in (canonical, *aliases):
            key = normalize_text(alias)
            if len(key) < 2 or key in seen:
                continue
            seen.add(key)
            pairs.append((key, canonical))
    pairs.sort(key=lambda item: len(item[0]), reverse=True)
    return pairs


PERSON_ALIAS_PAIRS = _alias_pairs(PERSON_ALIASES)
METRIC_ALIAS_PAIRS = _alias_pairs(METRIC_ALIASES)

# Canonical keys in METRIC_ALIASES are already normalized-ish; keep a lookup
# from normalized canonical → original display canonical.
CANONICAL_DISPLAY = {normalize_text(name): name for name in METRIC_ALIASES}


def canonical_metric_names() -> list[str]:
    return list(METRIC_ALIASES.keys())


def aliases_for_test(test_name: str) -> tuple[str, ...]:
    """Aliases whose canonical equals this stored test name."""
    n = normalize_text(test_name)
    found: list[str] = []
    for canonical, aliases in METRIC_ALIASES.items():
        if normalize_text(canonical) == n:
            found.append(canonical)
            found.extend(aliases)
    return tuple(found)


def find_panel(text: str) -> str | None:
    """Match a combo query (肝功能/血脂) against the stripped remainder.

    Exact alias match only — substring would steal 丙氨酸氨基转移酶 via 转氨酶.
    """
    q = normalize_text(text)
    if len(q) < 2:
        return None
    best: str | None = None
    best_len = 0
    for canonical, aliases in PANEL_ALIASES.items():
        for alias in (canonical, *aliases):
            key = normalize_text(alias)
            if key == q and len(key) > best_len:
                best = canonical
                best_len = len(key)
    return best
