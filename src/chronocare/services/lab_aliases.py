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
    "白细胞计数": ("白细胞计数", "wbc", "白血球"),
    "血小板计数": ("血小板计数", "plt", "血小板"),
    "中性粒细胞百分比": ("中性粒细胞百分比", "neut%", "中性粒细胞"),
    "D-二聚体": ("D-二聚体", "d二聚体", "ddimer", "d-dimer"),
    "胰岛素（空腹）": ("胰岛素（空腹）", "空腹胰岛素", "胰岛素"),
    "C肽（空腹）": ("C肽（空腹）", "空腹c肽", "c肽", "c-peptide", "c peptide"),
    "醛固酮质谱法": ("醛固酮质谱法", "醛固酮"),
    "肾素活性质谱法": ("肾素活性质谱法", "肾素活性", "肾素"),
    "醛固酮肾素活性比值": ("醛固酮肾素活性比值", "arr"),
    "血管紧张素II质谱法": ("血管紧张素II质谱法", "血管紧张素ii", "血管紧张素"),
    "葡萄糖": ("葡萄糖", "glu", "血糖"),
    "蛋白": ("尿蛋白", "蛋白"),
    "比重": ("比重", "sg"),
    "ph": ("ph", "酸碱度"),
    "亚硝酸盐": ("亚硝酸盐", "nit"),
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
