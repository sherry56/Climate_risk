# -*- coding: utf-8 -*-
import os, re, json, argparse, glob, unicodedata
import pandas as pd

def try_imports():
    mods = {}
    try:
        from modelscope.hub.snapshot_download import snapshot_download
        mods["snapshot_download"] = snapshot_download
    except Exception:
        mods["snapshot_download"] = None
    try:
        from gensim.models import Word2Vec, KeyedVectors
        mods["Word2Vec"] = Word2Vec
        mods["KeyedVectors"] = KeyedVectors
    except Exception:
        mods["Word2Vec"] = None
        mods["KeyedVectors"] = None
    try:
        import jieba
        mods["jieba"] = jieba
    except Exception:
        mods["jieba"] = None
    return mods

def load_seeds(path="SEEDS.json"):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def load_blacklist(path):
    s = set()
    if path and os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                w = line.strip()
                if w:
                    s.add(w)
    return s

def iter_corpus(paths):
    for p in paths or []:
        if not os.path.isdir(p):
            continue
        for fn in os.listdir(p):
            if fn.lower().endswith(".txt"):
                full = os.path.join(p, fn)
                try:
                    with open(full, "r", encoding="utf-8", errors="ignore") as fh:
                        yield fh.read()
                except Exception:
                    pass

def tokenize(text, jieba=None):
    text = (text or "").strip()
    if not text: return []
    if jieba is not None:
        return [w for w in jieba.cut(text) if len(w) > 1]
    import re as _re
    parts = _re.split(r"[^\u4e00-\u9fa5A-Za-z0-9]+", text)
    return [p for p in parts if len(p) > 1]

def build_corpus(paths, jieba=None):
    docs = []
    for doc in iter_corpus(paths):
        toks = tokenize(doc, jieba)
        if toks:
            docs.append(toks)
    return docs

def load_pretrained_any(path, KeyedVectors):
    if KeyedVectors is None:
        return None
    if path.endswith(".kv"):
        return KeyedVectors.load(path, mmap='r')
    binary = path.endswith(".bin")
    return KeyedVectors.load_word2vec_format(path, binary=binary)

def train_or_load_w2v(docs, model_path, Word2Vec):
    if Word2Vec is None:
        return None
    if os.path.exists(model_path):
        try:
            from gensim.models import Word2Vec as W2V
            return W2V.load(model_path)
        except Exception:
            pass
    if not docs:
        return None
    model = Word2Vec(sentences=docs, vector_size=100, window=5, min_count=2, workers=4, sg=1)
    try:
        model.save(model_path)
    except Exception:
        pass
    return model

# ---------- seed normalization & variants ----------
def normalize_cn(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "").strip()
    s = s.replace("（", "(").replace("）", ")")
    s = re.sub(r"\s+", " ", s)
    return s

ALIAS = {
    "SQL 注入": ["SQL注入","Sql注入","sql注入","结构化查询语言注入"],
    "拒绝服务": ["DDoS","ddos","Ddos","分布式拒绝服务"],
    "DNS 劫持": ["DNS劫持","域名系统劫持"],
    "数据泄露": ["数据外泄","数据泄漏","信息外泄","信息泄露"],
    "隐私泄露": ["隐私暴露"],
    "AI 幻觉": ["AI幻觉","模型幻觉"],
}

def generate_variants(word: str):
    w = normalize_cn(word)
    cands = set([w])
    # remove spaces
    cands.add(w.replace(" ", ""))
    # drop parentheses content
    cands.add(re.sub(r"\(.*?\)", "", w).strip())
    # try to extract abbr inside parentheses
    m = re.search(r"\((.*?)\)", w)
    if m:
        abbr = m.group(1).strip()
        if abbr:
            cands.update([abbr, abbr.lower(), abbr.upper(), abbr.capitalize()])
    # alias
    for k, vs in ALIAS.items():
        if k in w:
            cands.update(vs)
    # cleanup
    return [x for x in cands if x]

# ---------- expansion core ----------
def expand_for_seed(model_like, word, topn=10, blacklist=None):
    kv = getattr(model_like, "wv", model_like)
    if kv is None:
        return []

    results = []
    tried = set()

    # A) try word variants directly
    for cand in generate_variants(word):
        if cand in tried:
            continue
        tried.add(cand)
        try:
            if cand in kv:
                sims = kv.most_similar(cand, topn=topn)
                results.extend(sims)
        except Exception:
            pass

    # B) fallback: token-average vector (requires jieba when installed)
    if not results:
        try:
            import jieba
            toks = [t for t in jieba.cut(normalize_cn(word)) if t.strip()]
            vecs = []
            for t in toks:
                for tv in generate_variants(t):
                    if tv in kv:
                        vecs.append(kv[tv])
                        break
            if vecs:
                import numpy as np
                q = np.mean(vecs, axis=0)
                sims = kv.most_similar(positive=[q], topn=topn)
                results.extend(sims)
        except Exception:
            pass

    # dedup + filter
    uniq = {}
    for w, s in results:
        if blacklist and w in blacklist:
            continue
        if not re.search(r"[\u4e00-\u9fa5A-Za-z0-9]", w):
            continue
        s = float(s)
        if w not in uniq or s > uniq[w]:
            uniq[w] = s

    out = sorted(uniq.items(), key=lambda x: x[1], reverse=True)[:topn]
    return out

def auto_find_vectors(dir_path):
    order = ["*.bin", "*.txt", "*.kv"]
    cands = []
    for patt in order:
        cands += glob.glob(os.path.join(dir_path, "**", patt), recursive=True)
        if cands:
            break
    if not cands:
        return None
    cands.sort(key=lambda p: os.path.getsize(p), reverse=True)
    return cands[0]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="SEEDS.json", help="SEEDS 字典文件路径")
    ap.add_argument("--use-tencent", action="store_true", help="自动下载 lili666/text2vec-word2vec-tencent-chinese")
    ap.add_argument("--pretrained", default="", help="已下载的预训练向量路径（.txt/.bin/.kv）")
    ap.add_argument("--cache_dir", default="./ms_models", help="ModelScope 下载缓存目录")
    ap.add_argument("--topn", type=int, default=10, help="每个种子扩展数量")
    ap.add_argument("--min_sim", type=float, default=0.0, help="相似度阈值（默认不过滤）")
    ap.add_argument("--blacklist", default="", help="黑名单词列表文件（每行一个），用于去噪")
    ap.add_argument("--excel", default="SEEDS_expend.xlsx", help="输出 Excel 文件名")
    ap.add_argument("--csv", default="", help="同时输出 CSV（UTF-8-SIG）。若留空，将按 Excel 名自动生成 .csv")
    ap.add_argument("--model", default="w2v.model", help="（回退）本地训练模型保存/加载路径")
    ap.add_argument("--corpus", nargs="*", default=None, help="（回退）本地语料目录")
    args = ap.parse_args()

    mods = try_imports()
    KeyedVectors = mods["KeyedVectors"]
    Word2Vec = mods["Word2Vec"]
    snapshot_download = mods["snapshot_download"]
    jieba = mods["jieba"]

    seeds = load_seeds(args.seeds)
    blacklist = load_blacklist(args.blacklist)

    model_like = None
    vec_path = None

    if args.pretrained:
        vec_path = args.pretrained
    elif args.use_tencent:
        if snapshot_download is None:
            print("[ERR] 请先安装 modelscope: pip install modelscope")
        else:
            print("[INFO] 从 ModelScope 下载 lili666/text2vec-word2vec-tencent-chinese ...")
            local_dir = snapshot_download('lili666/text2vec-word2vec-tencent-chinese', cache_dir=args.cache_dir)
            print("[OK] 模型缓存目录:", local_dir)
            vec_path = auto_find_vectors(local_dir)
            if not vec_path:
                print("[ERR] 未找到 .bin/.txt/.kv 文件，请检查模型仓库内容。")

    if vec_path and KeyedVectors is not None:
        try:
            model_like = load_pretrained_any(vec_path, KeyedVectors)
            print("[OK] 已加载预训练向量：", vec_path)
        except Exception as e:
            print("[ERR] 预训练向量加载失败：", e)

    if model_like is None:
        docs = build_corpus(args.corpus, jieba=jieba) if args.corpus else []
        model_like = train_or_load_w2v(docs, args.model, Word2Vec)
        if model_like is None:
            print("[WARN] 无法加载预训练向量且本地语料不可用，将仅输出种子词。")

    rows = []
    for cat_sub, kws in seeds.items():
        try:
            cat, sub = cat_sub.split("|")
        except ValueError:
            cat, sub = cat_sub, ""
        for kw in kws:
            expanded = []
            if model_like is not None:
                expanded = expand_for_seed(model_like, kw, topn=args.topn, blacklist=blacklist)
                if args.min_sim > 0:
                    expanded = [(w, s) for (w, s) in expanded if s >= args.min_sim]
            if expanded:
                for w, score in expanded:
                    rows.append({
                        "一级分类": cat, "二级分类": sub, "种子词": kw,
                        "扩展词": w, "相似度": round(float(score), 4),
                        "来源": "预训练" if vec_path else "本地训练"
                    })
            else:
                rows.append({
                    "一级分类": cat, "二级分类": sub, "种子词": kw,
                    "扩展词": "", "相似度": "", "来源": "（无扩展）"
                })

    df = pd.DataFrame(rows, columns=["一级分类","二级分类","种子词","扩展词","相似度","来源"])

    # Excel
    with pd.ExcelWriter(args.excel, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="_ALL", index=False)
        for sub, sub_df in df.groupby("二级分类"):
            name = sub[:28] if sub else "未分组"
            sub_df.to_excel(writer, sheet_name=name, index=False)

    # CSV
    csv_path = args.csv or os.path.splitext(args.excel)[0] + ".csv"
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    print("[DONE] 输出：", os.path.abspath(args.excel))
    print("[DONE] 另存 CSV：", os.path.abspath(csv_path))

if __name__ == "__main__":
    main()
