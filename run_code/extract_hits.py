# -*- coding: utf-8 -*-
"""
extract_hits_2024.py
从“扩展关键词表”抽取2024年年报中的相关句子。
"""

import argparse
import os
import re
from pathlib import Path
import pandas as pd

# 句末分句：句号/感叹号/问号
SENT_SPLIT_RE = re.compile(r"(?<=[。！？?])\s*")

def clean_text(text: str) -> str:
    """清洗文本：去除换行符、回车符和多余空格，确保匹配连贯。"""
    if not text:
        return ""
    # 去除换行符和回车
    text = text.replace('\n', '').replace('\r', '')
    # 将多个空格合并为一个
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def split_sents(text: str):
    """按句末切分，过长再按逗号二次切分，过滤过短片段。"""
    text = clean_text(text)
    if not text:
        return []
    parts = [p.strip() for p in SENT_SPLIT_RE.split(text) if p.strip()]
    out = []
    for p in parts:
        if len(p) > 120:
            out.extend([x.strip() for x in re.split(r"[，,]", p) if x.strip()])
        else:
            out.append(p)
    return [s for s in out if len(s) >= 4]

def load_dict(dict_path: str):
    """
    读取扩展关键词表：支持 Excel(_ALL) / CSV
    返回：{(cat, sub): set(words)}，包含种子词和扩展词
    """
    if dict_path.lower().endswith(".xlsx"):
        df = pd.read_excel(dict_path, sheet_name="_ALL")
    else:
        df = pd.read_csv(dict_path)

    df = df.fillna("")
    d = {}
    for _, r in df.iterrows():
        cat = str(r.get("一级分类", "")).strip()
        sub = str(r.get("二级分类", "")).strip()
        seed = str(r.get("种子词", "")).strip()
        wexp = str(r.get("扩展词", "")).strip()
        key = (cat, sub)
        if key not in d:
            d[key] = set()
        if seed:
            d[key].add(seed)
        if wexp:
            d[key].add(wexp)
    return {k: v for k, v in d.items() if v}

def parse_meta_from_filename(filename: str):
    """适配命名：000001_2024_公司名..."""
    name = os.path.basename(filename)
    parts = name.split("_")
    code = parts[0] if len(parts) > 0 else "000000"
    year = parts[1] if len(parts) > 1 else "2024"
    company = parts[2] if len(parts) > 2 else "Unknown"
    return code, year, company

def scan_dir(annual_dir: str, catmap: dict):
    rows = []
    if not os.path.exists(annual_dir):
        return rows
    files = [f for f in os.listdir(annual_dir) if f.lower().endswith(".txt")]
    for fn in files:
        fpath = os.path.join(annual_dir, fn)
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()
        
        sents = split_sents(text)
        code, year, company = parse_meta_from_filename(fn)

        for i, s in enumerate(sents):
            slow = s.lower()
            for (cat, sub), words in catmap.items():
                hit_words = {w for w in words if (w.lower() in slow if w.isascii() else w in s)}
                if hit_words:
                    rows.append({
                        "文件名": fn,
                        "股票代码": code,
                        "年份": year,
                        "公司": company,
                        "句序": i,
                        "一级分类": cat,
                        "二级分类": sub,
                        "命中关键词": "|".join(sorted(hit_words)),
                        "句子": s,
                    })
    return rows

def iter_2024_dirs(base_dir: Path):
    """仅遍历 base_dir 下 2024 年开头的子目录。"""
    if not base_dir.exists():
        return []
    # 修改正则，只匹配 2024_ 开头的目录
    year_2024_re = re.compile(r"^2024_")
    return sorted([p for p in base_dir.iterdir() if p.is_dir() and year_2024_re.match(p.name)])

def write_rows(df_all, out_path: Path):
    """写入 CSV (UTF-8-SIG 适配 Excel)"""
    if df_all.empty:
        print("[WARN] 没有匹配到任何结果。")
        return
    df_all.to_csv(out_path, index=False, encoding="utf-8-sig")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dict", required=True, help="扩展关键词表路径")
    # 确保添加了下面这一行参数定义
    ap.add_argument("--annual_dir", help="指定 2024 年报 TXT 文件所在的单目录")
    ap.add_argument("--base_dir", default="data/output", help="包含各年度子目录的根目录")
    ap.add_argument("--out", default="risk_hits_2024.csv", help="输出文件名")
    args = ap.parse_args()
    
    # 后续逻辑...
    args = ap.parse_args()

    catmap = load_dict(args.dict)
    base_dir = Path(args.base_dir)
    out_path = Path(args.out)

    dirs = iter_2024_dirs(base_dir)
    if not dirs:
        print(f"[ERR] 在 {base_dir} 下未找到以 2024_ 开头的目录。")
        return

    all_results = []
    total_hits = 0
    
    for d in dirs:
        print(f"[SCANNING 2024] {d.name}...")
        results = scan_dir(str(d), catmap)
        all_results.extend(results)
        total_hits += len(results)
        print(f"  -> 发现 {len(results)} 条匹配")

    if all_results:
        df_final = pd.DataFrame(all_results)
        write_rows(df_final, out_path)
        print(f"\n[DONE] 2024年匹配完成！结果保存至: {out_path.resolve()}")
        print(f"总计命中句数: {total_hits}")

if __name__ == "__main__":
    main()