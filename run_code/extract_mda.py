# -*- coding: utf-8 -*-
"""
年报 MD&A 提取脚本
- 功能：批量提取管理层讨论与分析章节，并清洗文本（去除换行符）。
- 输入：E:\projects\risk-pipeline\data\annual_txt
- 输出：E:\projects\risk-pipeline\data\output
"""

import os
import sys
import re
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed

# ======== 配置区域 ========
IN_BASE  = r'E:\projects\risk-pipeline\data\annual_txt'
OUT_BASE = r'E:\projects\risk-pipeline\data\output'

# 章节标题候选
TITLE_KEYWORDS = [
    '董事会报告','董事局报告','经营情况讨论与分析','经营层讨论与分析',
    '管理层讨论与分析','管理层分析与讨论','董事会工作报告','董事局工作报告'
]
# 下一章节的截断标识
NEXT_KEYWORDS = [
    '监事会工作报告','监事会报告','重要事项','公司治理'
]

FNAME_RE = re.compile(r'^(\d{6})_(\d{4})_([^_]+)_(.+?)_(\d{4}-\d{2}-\d{2})\.txt$')

def parse_filename(fname: str):
    m = FNAME_RE.match(fname)
    if not m: return None
    code, year, company, _, _ = m.groups()
    return {"code": code, "year": year, "company": company}

def extract_content(in_path: str, out_dir: str) -> str:
    """处理单个文件：提取、清洗、保存"""
    fname = os.path.basename(in_path)
    meta = parse_filename(fname)
    out_name = f"{meta['code']}_{meta['year']}_{meta['company']}_经营情况段落.txt" if meta else f"{os.path.splitext(fname)[0]}_提取.txt"
    out_path = os.path.join(out_dir, out_name)

    try:
        with open(in_path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
    except: return 'fail'

    # 1. 定位章节标题
    min_idx = sys.maxsize
    topic = None
    for t in TITLE_KEYWORDS:
        pos = text.find(t)
        if pos != -1:
            # 简单逻辑排除目录：检查标题后的第一个非空字符
            nxt_ch = text[pos + len(t): pos + len(t) + 1]
            if nxt_ch in ['“','。','分','一','中','关','之','》','"','—','”','第']:
                pos2 = text.find(t, pos + 1)
                if pos2 != -1 and pos2 < min_idx:
                    min_idx, topic = pos2, t
            elif pos < min_idx:
                min_idx, topic = pos, t

    if not topic: return 'skip'

    # 2. 提取正文
    split_text = text.split(topic)
    if len(split_text) < 2: return 'skip'
    
    result = None
    tail_blocks = split_text[1:]
    for ind, j in enumerate(tail_blocks):
        if len(j) > 0 and (j[:2] == ' \n' or j[0] in ['\n', ' ', '\t']):
            result = ''.join(tail_blocks[ind+1:])
            break
    if result is None: result = ''.join(tail_blocks)

    # 3. 截断到下一章节
    cut_points = [result.find(nt) for nt in NEXT_KEYWORDS if result.find(nt) != -1]
    if not cut_points:
        cut_points = [result.find(t) for t in TITLE_KEYWORDS if t != topic and result.find(t) != -1]
    
    if cut_points:
        end_idx = min(cut_points)
        if end_idx > 0: result = result[:end_idx]

    # 4. 清洗文本：去除换行符、回车符及多余空格
    result = re.sub(r'[\r\n\t]', '', result)  # 去除换行和制表符
    result = re.sub(r'\s+', ' ', result).strip() # 将连续空格替换为单个空格

    # 5. 保存
    try:
        os.makedirs(out_dir, exist_ok=True)
        with open(out_path, 'w', encoding='utf-8') as w:
            w.write(result)
        return 'ok'
    except: return 'fail'

if __name__ == "__main__":
    from tqdm import tqdm
    
    years = [str(y) for y in range(2014, 2025)]
    workers = max(1, (os.cpu_count() or 4) - 1)
    print(f"🔧 启动多进程提取，并行数：{workers}")

    for year in years:
        # 扫描年度子目录
        subdirs = [d for d in os.listdir(IN_BASE) if year in d and os.path.isdir(os.path.join(IN_BASE, d))]
        for subdir in subdirs:
            in_dir = os.path.join(IN_BASE, subdir)
            out_dir = os.path.join(OUT_BASE, subdir)
            
            files = [os.path.join(in_dir, n) for n in os.listdir(in_dir) if n.lower().endswith('.txt')]
            if not files: continue

            print(f"\n📂 处理目录: {subdir} (共 {len(files)} 份)")
            
            ok, fail, skip = 0, 0, 0
            with ProcessPoolExecutor(max_workers=workers) as ex:
                futures = [ex.submit(extract_content, fp, out_dir) for fp in files]
                for fut in tqdm(as_completed(futures), total=len(futures), desc=f"{year}进度"):
                    status = fut.result()
                    if status == 'ok': ok += 1
                    elif status == 'fail': fail += 1
                    else: skip += 1
            
            print(f"✅ 完成：成功 {ok}, 失败 {fail}, 跳过 {skip}")