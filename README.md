# 基于大语言模型的 A 股上市公司气候风险测度研究

**Measuring Corporate Climate Risk using Large Language Models: Evidence from 2024 A-Share Annual Reports**

本仓库包含了西南财经大学课程论文《基于大语言模型的 A 股上市公司气候风险测度研究》的完整代码实现与数据集。项目通过对比**增强词典法**、**FinBERT2** 与 **DeepSeek** 大模型，揭示了 2024 年 ESG 披露元年下的企业气候风险披露特征。

## 📂 项目结构 (Project Structure)

基于您上传的目录结构，项目文件组织如下：

```text
Climate_risk/
├── date/                               # 数据存放目录 (Data)
│   ├── 000001_2024_平安银行_...pdf     # [示例] 原始年报文件 (PDF/TXT)
│   ├── 000001_2024_平安银行_经营...    # [示例] 提取后的 MD&A 文本
│   ├── keywords.json                   # 基础种子词库 (Seed Keywords)
│   ├── keywords_expand.xlsx            # 基于 Word2Vec 扩充后的增强词典
│   ├── climaterisk_final_sample.csv    # 最终用于实验的标准化样本集 (30,000条)
│   ├── risk_Finbert_labeled.csv        # FinBERT 模型推理结果
│   ├── climaterisk_LLM_Full_Labeled.csv# DeepSeek 大模型推理结果 (核心产出)
│   └── 年报数据来源.txt                # 数据来源说明文档
│
├── run_code/                           # 代码执行目录 (Source Code)
│   ├── extract_mda.py                  # 步骤1: 年报文本提取与清洗脚本
│   ├── keyword_expand_w2v.py           # 步骤2: 词向量扩充词典脚本
│   ├── extract_hits.py                 # 步骤3: 词典法词频统计脚本
│   ├── llm_analysis.py                 # 步骤4: DeepSeek API 调用与推理脚本
│   └── run.ipynb                       # 步骤5: 数据汇总、FinBERT调用及绘图分析
│
├── README.md                           # 项目说明文档
└── requirements.txt                    # 环境依赖文件

```

## 💾 数据文件说明 (Data Description)

位于 `date/` 目录下的核心数据文件说明：

| 文件名 | 说明 | 关键列 |
| --- | --- | --- |
| `keywords.json` | 初始构建的物理风险、转型风险种子词 | `category`, `words` |
| `keywords_expand.xlsx` | 引入腾讯 AI Lab 词向量扩充后的词典 | `seed_word`, `similar_word`, `cosine_sim` |
| `climaterisk_final_sample.csv` | 经过清洗、分层抽样的实验语料 | `id`, `sentence`, `source_type` |
| **`climaterisk_LLM_Full_Labeled.csv`** | **DeepSeek 输出的最终标注结果** | `sentence`, `label` (-1/0/1), `confidence`, `reasoning` |
| `risk_Finbert_labeled.csv` | FinBERT 输出的分类结果 | `sentence`, `finbert_label`, `score` |

## 🚀 运行指南 (Usage Pipeline)

请按照以下顺序执行代码以复现论文结果：

### 1. 文本提取 (Text Extraction)

从原始年报中提取管理层讨论与分析 (MD&A) 章节：

```bash
python run_code/extract_mda.py

```

*输入：`date/` 下的原始年报 | 输出：`date/` 下的文本片段*

### 2. 词典构建 (Dictionary Expansion)

基于种子词扩展语义近义词：

```bash
python run_code/keyword_expand_w2v.py

```

*输入：`keywords.json` | 输出：`keywords_expand.xlsx*`

### 3. 词典法测度 (Dictionary Method)

运行传统的词频统计：

```bash
python run_code/extract_hits.py

```

### 4. 大模型推理 (LLM Inference)

调用 DeepSeek API 进行思维链推理（需配置 API Key）：

```bash
python run_code/llm_analysis.py

```

*核心逻辑：通过 Prompt Engineering 区分实质性风险与口号式披露。*

### 5. 结果分析与绘图 (Analysis & Visualization)

打开 Jupyter Notebook 进行 FinBERT 推理（如未单独运行）、数据合并及可视化图表生成（论文中的 KDE 图、ECDF 图等）：

```bash
jupyter notebook run_code/run.ipynb

```

## ⚙️ 环境依赖 (Requirements)

* Python 3.8+
* pandas
* numpy
* torch (用于 FinBERT)
* transformers (用于调用 HuggingFace 模型)
* openai (用于调用 DeepSeek API)
* jieba (中文分词)
* matplotlib / seaborn (绘图)

安装命令：

```bash
pip install -r requirements.txt

```

## 📝 引用 (Citation)

```bibtex
@article{ClimateRisk2024,
  title={基于大语言模型的 A 股上市公司气候风险测度研究},
  author={Your Name},
  year={2026},
  school={Southwestern University of Finance and Economics}
}

```

## 🤝 致谢 (Acknowledgments)

* 数据来源：巨潮资讯网、Wind 金融终端。
* 模型支持：DeepSeek-V3, FinBERT2。
