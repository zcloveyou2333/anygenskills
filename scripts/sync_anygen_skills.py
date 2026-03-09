#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步 AnyGen 技能市场数据到本地 CSV，并可选下载技能包/示例资源。

用法示例：
1) 仅拉取并导出 JSON（需要登录 Cookie）
   python scripts/sync_anygen_skills.py --cookie "session=xxx"

2) 拉取 + 回填 CSV
   python scripts/sync_anygen_skills.py --cookie "session=xxx" --update-csv

3) 拉取 + 回填 CSV + 下载可下载资源
   python scripts/sync_anygen_skills.py --cookie "session=xxx" --update-csv --download
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from urllib.parse import urlparse
from pathlib import Path
from typing import Any

import requests


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CSV = REPO_ROOT / "官方技能_数据表_表格.csv"
DEFAULT_OUT_DIR = REPO_ROOT / "_anygen_sync"
DEFAULT_DOWNLOAD_DIR = REPO_ROOT / "example" / "_anygen_downloads"

BASE_URL = "https://www.anygen.io"

# 技能市场分类标签映射（来自前端脚本）
TAG_TO_CATEGORY = {
    "": "推荐",
    "0": "通用",
    "1": "转换工具",
    "2": "市场营销",
    "3": "学生专用",
    "4": "内容创作",
    "5": "数据分析",
    "6": "开发者",
    "7": "产品设计",
}


class AnyGenAuthError(RuntimeError):
    pass


def parse_cookie_header(cookie_header: str) -> dict[str, str]:
    cookies: dict[str, str] = {}
    for part in cookie_header.split(";"):
        chunk = part.strip()
        if not chunk or "=" not in chunk:
            continue
        k, v = chunk.split("=", 1)
        cookies[k.strip()] = v.strip()
    return cookies


def api_get(session: requests.Session, path: str, params: dict[str, Any] | None = None) -> Any:
    url = f"{BASE_URL}{path}"
    resp = session.get(url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    # AnyGen 常见失败结构：{"code":5, "msg":"To view this content, please log in", ...}
    if isinstance(data, dict) and data.get("code") not in (0, None):
        msg = str(data.get("msg") or "")
        err = data.get("error") or {}
        err_code = err.get("Code")
        if err_code == 4101 or "log in" in msg.lower():
            raise AnyGenAuthError("AnyGen 接口鉴权失败（需要登录态 Cookie）。")
        raise RuntimeError(f"AnyGen API error: code={data.get('code')} msg={msg}")

    return data.get("data", data)


def normalize_source(source: str | None) -> str:
    s = (source or "").strip()
    if not s:
        return "AnyGen"
    if s.lower() == "official":
        return "AnyGen"
    return s


def infer_category_from_tags(tags: list[Any] | None) -> str:
    if not tags:
        return ""
    for t in tags:
        k = str(t)
        if k in TAG_TO_CATEGORY and k != "":
            return TAG_TO_CATEGORY[k]
    return ""


def fetch_marketplace(session: requests.Session) -> list[dict[str, Any]]:
    all_skills: dict[str, dict[str, Any]] = {}
    tags = ["", "0", "1", "2", "3", "4", "5", "6", "7"]

    for tag in tags:
        cursor = ""
        while True:
            params: dict[str, Any] = {"page_size": 24}
            if tag:
                params["tag"] = tag
            if cursor:
                params["cursor"] = cursor

            data = api_get(session, "/api/page/skills/marketplace", params=params)
            skills = data.get("skills") or []
            for skill in skills:
                skill_id = str(skill.get("id", ""))
                if not skill_id:
                    continue
                # 后抓到的补充前者
                merged = dict(all_skills.get(skill_id, {}))
                merged.update(skill)
                all_skills[skill_id] = merged

            if not data.get("has_more"):
                break
            cursor = str(data.get("next_cursor") or "")
            if not cursor:
                break

    detailed: list[dict[str, Any]] = []
    for skill_id, summary in all_skills.items():
        detail = api_get(
            session,
            "/api/page/skills/marketplace/detail",
            params={"skill_id": skill_id},
        )
        merged = dict(summary)
        if isinstance(detail, dict):
            merged.update(detail)
        merged["id"] = summary.get("id", detail.get("id", skill_id))
        merged["source"] = normalize_source(merged.get("source"))
        merged["category_infer"] = infer_category_from_tags(merged.get("listing_tags"))
        detailed.append(merged)

    return detailed


def skill_to_attachment_text(skill: dict[str, Any]) -> str:
    parts: list[str] = []
    ft = (skill.get("file_token") or "").strip()
    if ft:
        parts.append(f"skill_file_token:{ft}")
    examples = skill.get("examples") or []
    for ex in examples:
        title = (ex.get("title") or "").strip()
        url = (ex.get("url") or "").strip()
        img = (ex.get("img_token") or "").strip()
        chunk = []
        if title:
            chunk.append(title)
        if url:
            chunk.append(url)
        if img:
            chunk.append(f"img_token:{img}")
        if chunk:
            parts.append(" | ".join(chunk))
    return "\n".join(parts).strip()


def update_csv(csv_path: Path, skills: list[dict[str, Any]], overwrite: bool) -> tuple[int, int]:
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
        fieldnames = list(rows[0].keys()) if rows else [
            "名称", "分类", "状态", "说明", "作者", "源地址", "验证人", "场景", "附件", "结果"
        ]

    for col in ["说明", "作者", "场景", "附件", "分类"]:
        if col not in fieldnames:
            fieldnames.append(col)

    by_name: dict[str, dict[str, str]] = {}
    for row in rows:
        name = (row.get("名称") or "").strip().lower()
        if name:
            by_name[name] = row

    updated = 0
    appended = 0
    for skill in skills:
        name = str(skill.get("name") or "").strip()
        if not name:
            continue
        key = name.lower()
        row = by_name.get(key)
        if row is None:
            row = {k: "" for k in fieldnames}
            row["名称"] = name
            row["状态"] = "待验证"
            rows.append(row)
            by_name[key] = row
            appended += 1

        before = dict(row)
        description = (skill.get("description") or "").strip()
        author = normalize_source(skill.get("source"))
        prompt = (skill.get("prompt") or "").strip()
        attachment = skill_to_attachment_text(skill)
        category = (row.get("分类") or "").strip() or skill.get("category_infer", "")

        def put(col: str, value: str) -> None:
            if not value:
                return
            old = (row.get(col) or "").strip()
            if overwrite or not old:
                row[col] = value

        put("说明", description)
        put("作者", author)
        put("场景", prompt)
        put("附件", attachment)
        put("分类", category)

        if row != before:
            updated += 1

    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return updated, appended


def safe_filename(name: str) -> str:
    text = re.sub(r"[\\/:*?\"<>|]+", "_", name).strip()
    return text or "unknown"


def parse_filename_from_disposition(disposition: str | None) -> str:
    if not disposition:
        return ""
    # e.g. attachment; filename="xlsx.zip"; filename*=UTF-8''xlsx.zip
    m = re.search(r"filename\\*=UTF-8''([^;]+)", disposition)
    if m:
        return m.group(1).strip().strip('"')
    m = re.search(r'filename="([^"]+)"', disposition)
    if m:
        return m.group(1).strip()
    m = re.search(r"filename=([^;]+)", disposition)
    if m:
        return m.group(1).strip().strip('"')
    return ""


def infer_file_ext(resp: requests.Response, default_ext: str) -> str:
    ctype = (resp.headers.get("content-type") or "").lower()
    if "application/zip" in ctype or "application/x-zip" in ctype:
        return ".zip"
    if "application/pdf" in ctype:
        return ".pdf"
    if "image/png" in ctype:
        return ".png"
    if "image/jpeg" in ctype or "image/jpg" in ctype:
        return ".jpg"
    if "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in ctype:
        return ".xlsx"
    if "application/vnd.ms-excel" in ctype:
        return ".xls"
    return default_ext


def try_download_file_token(
    session: requests.Session,
    file_token: str,
    out_base_path: Path,
    default_ext: str = ".bin",
) -> Path | None:
    # 前端脚本未暴露统一下载接口，尝试常见路径
    candidates = [
        f"/space/api/box/stream/download/{file_token}",
        f"/space/api/box/stream/download/preview/{file_token}?preview_type=16",
    ]
    for path in candidates:
        url = f"{BASE_URL}{path}"
        try:
            resp = session.get(url, timeout=60)
            if resp.status_code != 200:
                continue
            ctype = (resp.headers.get("content-type") or "").lower()
            if "application/json" in ctype:
                continue
            if len(resp.content) < 128:
                continue
            out_ext = infer_file_ext(resp, default_ext=default_ext)
            out_path = out_base_path.with_suffix(out_ext)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_bytes(resp.content)
            return out_path
        except requests.RequestException:
            continue
    return None


def parse_task_token(task_url: str) -> str:
    if not task_url:
        return ""
    try:
        path = urlparse(task_url).path.strip("/")
    except ValueError:
        return ""
    parts = path.split("/")
    if len(parts) >= 2 and parts[0] == "task":
        return parts[1]
    return ""


def extract_file_nodes(payload: Any) -> list[dict[str, str]]:
    found: list[dict[str, str]] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            token = str(node.get("file_token") or node.get("token") or "").strip()
            if token:
                name = str(node.get("name") or node.get("file_name") or "").strip()
                version = str(node.get("version") or "").strip()
                found.append({"token": token, "name": name, "version": version})
            for v in node.values():
                walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)

    walk(payload)
    # dedup by (token, name, version)
    uniq: dict[tuple[str, str, str], dict[str, str]] = {}
    for item in found:
        uniq[(item["token"], item["name"], item["version"])] = item
    return list(uniq.values())


def download_task_attachment_token(
    session: requests.Session,
    file_token: str,
    out_dir: Path,
    prefer_name: str = "",
    version: str = "",
) -> Path | None:
    candidates = [f"/space/api/box/stream/download/all/{file_token}"]
    if version:
        candidates.insert(0, f"/space/api/box/stream/download/all/{file_token}?version={version}")

    for path in candidates:
        url = f"{BASE_URL}{path}"
        try:
            resp = session.get(url, timeout=60)
            if resp.status_code != 200:
                continue
            ctype = (resp.headers.get("content-type") or "").lower()
            if "application/json" in ctype:
                continue
            if len(resp.content) < 128:
                continue

            header_name = parse_filename_from_disposition(resp.headers.get("content-disposition"))
            name = header_name or prefer_name or file_token
            name = safe_filename(name)
            stem, dot, ext = name.rpartition(".")
            if dot and ext:
                out_name = name
            else:
                out_ext = infer_file_ext(resp, default_ext=".bin")
                out_name = f"{name}{out_ext}"

            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / out_name
            out_path.write_bytes(resp.content)
            return out_path
        except requests.RequestException:
            continue
    return None


def download_task_attachments(
    session: requests.Session,
    skill: dict[str, Any],
    out_dir: Path,
) -> int:
    examples = skill.get("examples") or []
    downloaded = 0
    seen_tokens: set[str] = set()

    for ex_idx, ex in enumerate(examples, start=1):
        task_url = str(ex.get("url") or "").strip()
        task_token = parse_task_token(task_url)
        if not task_token:
            continue

        try:
            data = api_get(
                session,
                f"/api/page/pages/{task_token}/messages",
                params={"limit": 239},
            )
        except Exception:
            continue

        messages = (data or {}).get("messages") or []
        nodes = extract_file_nodes(messages)
        if not nodes:
            continue

        ex_dir = out_dir / f"example_task_{ex_idx}_{safe_filename(task_token)}"
        for node in nodes:
            token = node["token"]
            if token in seen_tokens:
                continue
            saved = download_task_attachment_token(
                session,
                token,
                ex_dir,
                prefer_name=node["name"],
                version=node["version"],
            )
            if saved:
                seen_tokens.add(token)
                downloaded += 1

    return downloaded


def download_assets(session: requests.Session, skills: list[dict[str, Any]], out_dir: Path) -> tuple[int, int, int]:
    skill_count = 0
    img_count = 0
    task_attachment_count = 0
    for skill in skills:
        name = safe_filename(str(skill.get("name") or "unknown"))
        skill_dir = out_dir / name
        package_dir = skill_dir / "skill_package"
        preview_dir = skill_dir / "example_preview"
        task_files_dir = skill_dir / "example_attachments"
        file_token = (skill.get("file_token") or "").strip()
        if file_token:
            saved = try_download_file_token(
                session,
                file_token,
                package_dir / "skill_package",
                default_ext=".zip",
            )
            if saved:
                skill_count += 1

        for idx, ex in enumerate(skill.get("examples") or [], start=1):
            img_token = (ex.get("img_token") or "").strip()
            if not img_token:
                continue
            url = f"{BASE_URL}/space/api/box/stream/download/preview/{img_token}?preview_type=16"
            try:
                resp = session.get(url, timeout=30)
                if resp.status_code == 200 and len(resp.content) > 128:
                    ext = infer_file_ext(resp, default_ext=".png")
                    preview_dir.mkdir(parents=True, exist_ok=True)
                    (preview_dir / f"example_{idx}{ext}").write_bytes(resp.content)
                    img_count += 1
            except requests.RequestException:
                pass

        task_attachment_count += download_task_attachments(session, skill, task_files_dir)

    return skill_count, img_count, task_attachment_count


def main() -> None:
    parser = argparse.ArgumentParser(description="同步 AnyGen 技能市场数据")
    parser.add_argument("--cookie", default="", help="浏览器 Cookie 字符串，例如: session=xxx; other=yyy")
    parser.add_argument("--cookie-file", default="", help="包含完整 Cookie 字符串的文本文件路径")
    parser.add_argument("--csv", default=str(DEFAULT_CSV), help="CSV 文件路径")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="输出目录")
    parser.add_argument("--download-dir", default=str(DEFAULT_DOWNLOAD_DIR), help="资源下载目录")
    parser.add_argument("--update-csv", action="store_true", help="将抓取结果回填到 CSV")
    parser.add_argument("--overwrite", action="store_true", help="回填 CSV 时覆盖已有内容")
    parser.add_argument("--download", action="store_true", help="下载可下载的技能包/示例资源")
    args = parser.parse_args()

    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Referer": f"{BASE_URL}/skills",
        "Origin": BASE_URL,
    })

    # 初始化会话
    session.get(f"{BASE_URL}/home", timeout=30)

    cookie_raw = ""
    if args.cookie_file:
        cookie_raw = Path(args.cookie_file).read_text(encoding="utf-8-sig").strip()
    if args.cookie.strip():
        cookie_raw = args.cookie.strip()
    cookie_raw = cookie_raw.lstrip("\ufeff").strip()

    if cookie_raw:
        # AnyGen 认证对原始 Cookie 头更稳定；同时保留 cookie jar 以兼容重定向场景
        session.headers["Cookie"] = cookie_raw
        session.cookies.update(parse_cookie_header(cookie_raw))

    try:
        skills = fetch_marketplace(session)
    except AnyGenAuthError as e:
        print(str(e))
        print("请传入登录后的 --cookie 或 --cookie-file 再执行。")
        return

    json_path = out_dir / "skills_full.json"
    json_path.write_text(json.dumps(skills, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"已导出技能 JSON: {json_path}（{len(skills)} 条）")

    if args.update_csv:
        csv_path = Path(args.csv).resolve()
        updated, appended = update_csv(csv_path, skills, overwrite=args.overwrite)
        print(f"CSV 已更新: {csv_path}（更新 {updated} 行，新增 {appended} 行）")

    if args.download:
        download_dir = Path(args.download_dir).resolve()
        skill_files, example_images, task_attachments = download_assets(session, skills, download_dir)
        print(
            f"资源下载完成：技能包 {skill_files}，示例图片 {example_images}，"
            f"任务附件 {task_attachments}，目录 {download_dir}"
        )


if __name__ == "__main__":
    main()
