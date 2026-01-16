这是一个为您起草的标准学术项目 `README.md` 文档。它涵盖了项目背景、研究方法、核心发现、代码结构以及运行方式，风格专业且清晰，完美契合您的论文内容。

您可以直接复制以下内容保存为 `README.md` 文件。

---

# 基于大语言模型的 A 股上市公司气候风险测度研究

**Measuring Corporate Climate Risk using Large Language Models: Evidence from 2024 A-Share Annual Reports**

本仓库包含了西南财经大学课程论文《基于大语言模型的 A 股上市公司气候风险测度研究：来自 2024 年年报的证据》的数据处理代码、模型推理脚本及论文 LaTeX 源码。

## 📖 项目简介 (Introduction)

2024 年是《上市公司可持续发展报告指引》实施元年，A 股市场迎来了 ESG 信息披露的爆发。然而，海量文本中充斥着“漂绿”噪音与形式主义口号。

本项目旨在解决传统文本分析方法在气候金融领域的失效问题。我们利用 **2024 年 A 股全量年报**（5405 家公司），构建了包含 30,000 条句子的标准化测试集，系统对比了三种技术范式在气候风险测度中的表现：

1. **增强词典法 (Augmented Dictionary):** 基于 Word2Vec 扩充的关键词匹配。
2. **FinBERT2 预训练模型:** 基于金融语料预训练的判别式模型。
3. **DeepSeek 大语言模型:** 基于思维链（CoT）推理的生成式模型。

## 📊 核心发现 (Key Findings)

通过对比实验，本研究得出以下结论：

* **词典法：** 存在严重的**长尾分布**与稀疏性，漏判了表述隐晦的实质性风险。
* **FinBERT2：** 陷入**二元极化**陷阱，强制将中性噪音归类为风险或防范，且置信度显著偏低（均值 0.53），导致风险高估。
* **DeepSeek：** 展现了强大的**逻辑降噪**能力，成功剔除了 **89.0%** 的“漂绿”口号与合规声明，精准还原了“物理风险强证据、转型风险软预期”的结构性特征。

## 📂 项目结构 (Repository Structure)

```text
Climate_risk/
├── data/                      # 数据文件夹
│   ├── raw/                   # 原始年报文本 (示例)
│   ├── processed/             # 预处理后的句子级语料
│   └── dictionary/            # 增强词典种子词库
│
├── code/                      # 核心代码
│   ├── 01_dict_method.py      # 增强词典法实现 (Jieba分词+词频统计)
│   ├── 02_finbert_infer.py    # FinBERT2 零样本推理脚本
│   ├── 03_deepseek_api.py     # DeepSeek API 调用与 Prompt 设计
│   └── 04_visualization.py    # 绘图脚本 (KDE, ECDF, 饼图)
│
├── paper/                     # 论文源码
│   ├── main.tex               # LaTeX 主文件
│   ├── ref.bib                # 参考文献
│   ├── madia/                 # 论文插图 (swufe.jpg 等)
│   └── thesis.pdf             # 编译后的论文 PDF
│
├── results/                   # 结果输出
│   ├── finbert_analysis.png   # FinBERT 分析图
│   └── llm_efficacy.jpg       # DeepSeek 效能分析图
│
├── requirements.txt           # 依赖环境
└── README.md                  # 项目说明文档

```

## 🚀 快速开始 (Quick Start)

### 1. 环境准备

```bash
git clone https://github.com/sherry56/Climate_risk.git
cd Climate_risk
pip install -r requirements.txt

```

### 2. 复现绘图结果

如果您拥有处理好的结果数据 (`df_result.csv`)，可以直接运行可视化脚本复现论文中的图表（包括 FinBERT 的二元分布图与 DeepSeek 的三峰分布图）：

```bash
python code/04_visualization.py

```

### 3. 模型推理 (示例)

**DeepSeek 调用示例 (伪代码):**

```python
# code/03_deepseek_api.py
import openai

def analyze_climate_risk(text):
    prompt = f"""
    你是一名气候金融专家。请分析以下句子是否包含实质性气候风险：
    句子：{text}
    要求：
    1. 区分“风险暴露”、“风险防范”和“无关/口号”。
    2. 输出置信度 (0-1)。
    3. 剔除单纯的合规声明（如“严格遵守法律”）。
    """
    # ... API 调用逻辑 ...

```

## 📈 实验结果可视化

### FinBERT2 的二元极化与低置信度

*FinBERT2 将几乎所有文本强制分类，缺乏中性选项，且置信度集中在 0.5 左右的低水平。*

### DeepSeek 的逻辑降噪与风险结构

*DeepSeek 成功识别大量中性样本（绿色部分），并揭示了物理风险（红色）与转型风险（蓝色）的异质性。*

## 📝 引用 (Citation)

如果您在研究中使用了本项目的方法或代码，请参考以下引用格式：

```bibtex
@misc{ClimateRisk2024,
  author = {Your Name},
  title = {Measuring Corporate Climate Risk using Large Language Models: Evidence from 2024 A-Share Annual Reports},
  year = {2026},
  publisher = {GitHub},
  journal = {GitHub repository},
  howpublished = {\url{https://github.com/sherry56/Climate_risk}}
}

```

## 🤝 致谢 (Acknowledgements)

* 感谢 **西南财经大学** 提供的学术资源支持。
* 感谢 **DeepSeek** 提供的 LLM API 支持。
* FinBERT 模型来源: [Valuesimplex/FinBERT](https://github.com/valuesimplex/FinBERT)

---

*Last updated: Jan 2026*
