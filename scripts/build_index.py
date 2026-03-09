#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 官方技能_数据表_表格.csv 和本地 SKILL 目录生成 INDEX.md 索引。
用法：在仓库根目录执行  python scripts/build_index.py
"""
from pathlib import Path
import csv

REPO_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = REPO_ROOT / "官方技能_数据表_表格.csv"
INDEX_PATH = REPO_ROOT / "INDEX.md"


def load_skills_csv(path: Path) -> list[dict]:
    """读取 CSV，每行一个 dict，键为列名。"""
    rows = []
    with open(path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("名称") or "").strip()
            if not name:
                continue
            rows.append({
                "名称": name,
                "分类": (row.get("分类") or "").strip(),
                "状态": (row.get("状态") or "").strip(),
                "说明": (row.get("说明") or "").strip().replace("\n", " "),
                "作者": (row.get("作者") or "").strip(),
                "源地址": (row.get("源地址") or "").strip(),
            })
    return rows


def find_local_skill_dirs(root: Path) -> set[str]:
    """扫描仓库下所有包含 SKILL.md 的目录名（作为 skill 名称）。"""
    names = set()
    for p in root.iterdir():
        if not p.is_dir():
            continue
        if (p / "SKILL.md").exists():
            names.add(p.name)
    return names


def build_index():
    if not CSV_PATH.exists():
        print(f"未找到 CSV: {CSV_PATH}")
        return
    skills = load_skills_csv(CSV_PATH)
    local_dirs = find_local_skill_dirs(REPO_ROOT)

    # 按分类分组，分类顺序按首次出现顺序
    by_cat: dict[str, list[dict]] = {}
    cat_order: list[str] = []
    for s in skills:
        cat = s["分类"] or "未分类"
        if cat not in by_cat:
            by_cat[cat] = []
            cat_order.append(cat)
        s["本地"] = "✅" if s["名称"] in local_dirs else "—"
        by_cat[cat].append(s)

    lines = [
        "# AnyGen Skills 索引",
        "",
        "由 `scripts/build_index.py` 根据 **官方技能_数据表_表格.csv** 与本地目录自动生成。",
        "",
        "- **本地**：✅ = 本仓库已有该 skill 目录（含 SKILL.md），— = 未导入。",
        "- 更新索引：在仓库根目录执行 `python scripts/build_index.py`。",
        "",
    ]

    for cat in cat_order:
        lines.append(f"## {cat}\n")
        lines.append("| 名称 | 状态 | 说明 | 本地 | 源地址 |")
        lines.append("|------|------|------|------|--------|")
        for s in by_cat[cat]:
            desc = (s["说明"][:60] + "…") if len(s["说明"]) > 60 else s["说明"]
            link = s["源地址"]
            addr = f"[链接]({link})" if link else "—"
            lines.append(f"| {s['名称']} | {s['状态']} | {desc} | {s['本地']} | {addr} |")
        lines.append("")
        lines.append("")

    INDEX_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"已生成: {INDEX_PATH}（共 {len(skills)} 条，本地 {len(local_dirs)} 个）")


if __name__ == "__main__":
    build_index()
