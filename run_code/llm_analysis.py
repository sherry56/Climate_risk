import os
import json
import time
import pandas as pd
import openai
from dotenv import load_dotenv
from tqdm import tqdm

# 1. 加载环境变量
load_dotenv(".env")

# ================= ⚙️ 配置区域 =================
INPUT_FILE = r'E:\projects\risk-pipeline\data\output\climaterisk_final_sample.csv'
# 最终输出文件
OUTPUT_FILE = r'E:\projects\risk-pipeline\data\output\climaterisk_LLM_Full_Labeled.csv'
# 中断备份文件（用于断点续传）
CHECKPOINT_FILE = r'E:\projects\risk-pipeline\data\output\label_checkpoint.tmp'

def setup_client():
    api_key = os.getenv("DEEP_API_KEY")
    base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    if not api_key:
        raise ValueError("❌ 错误: 未在环境变量中找到 DEEP_API_KEY")
    return openai.OpenAI(api_key=api_key, base_url=base_url)

# ================= Prompt 设计 =================
SYSTEM_PROMPT = """你是一个气候金融专家。分析文本语义并输出 JSON：
1. 【暴露】 (-1)：具体描述了气候灾害损失、资产减值或合规成本上升。
2. 【防范】 (1)：具体描述了减排投入、转型技术、管理架构或明确目标。
3. 【不相关】 (0)：空洞口号、洗绿话术或单纯政策复述。

输出格式示例：
{
  "label": -1,
  "prob_exposed": 0.8,
  "prob_prevent": 0.1,
  "prob_neutral": 0.1,
  "reason": "内容描述了极端天气导致的供应链中断"
}"""

def main():
    client = setup_client()
    
    # 1. 加载全量数据
    df = pd.read_csv(INPUT_FILE, encoding='utf-8-sig')
    total_count = len(df)
    
    # 2. 检查是否有断点（续传逻辑）
    if os.path.exists(CHECKPOINT_FILE):
        processed_df = pd.read_csv(CHECKPOINT_FILE, encoding='utf-8-sig')
        start_idx = len(processed_df)
        print(f"🔄 检测到断点，从第 {start_idx} 条开始续传...")
    else:
        processed_df = pd.DataFrame()
        start_idx = 0
        print(f"🚀 全量模式启动，共计 {total_count} 条待标注...")

    # 3. 核心推理循环
    # 仅处理尚未标注的部分
    target_sentences = df['句子'].iloc[start_idx:].tolist()
    
    for i, text in enumerate(tqdm(target_sentences, desc="DeepSeek 标注中", initial=start_idx, total=total_count)):
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"文本：{text}"}
                ],
                response_format={'type': 'json_object'},
                temperature=0.1
            )
            
            # 解析内容
            data = json.loads(response.choices[0].message.content)
            
            # 整理当前行数据
            current_row = df.iloc[[start_idx + i]].copy()
            current_row['LLM_Label'] = data.get('label')
            current_row['LLM_Prob_Exposed'] = data.get('prob_exposed')
            current_row['LLM_Prob_Prevent'] = data.get('prob_prevent')
            current_row['LLM_Prob_Neutral'] = data.get('prob_neutral')
            current_row['LLM_Reason'] = data.get('reason')
            
            # 实时追加到已处理 DataFrame
            processed_df = pd.concat([processed_df, current_row], ignore_index=True)
            
            # 每 10 条保存一次临时文件，防止断电
            if (i + 1) % 10 == 0:
                processed_df.to_csv(CHECKPOINT_FILE, index=False, encoding='utf-8-sig')
                
        except Exception as e:
            print(f"\n⚠️ 处理第 {start_idx + i} 条时出错: {e}")
            # 保存当前进度并退出，方便稍后重启
            processed_df.to_csv(CHECKPOINT_FILE, index=False, encoding='utf-8-sig')
            print("💾 进度已安全保存至临时文件。")
            break
        
        # 针对全量标注微调延迟
        time.sleep(0.05)

    # 4. 完成后保存最终文件并清理临时文件
    if len(processed_df) >= total_count:
        processed_df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
        if os.path.exists(CHECKPOINT_FILE):
            os.remove(CHECKPOINT_FILE)
        print(f"\n✅ 全量标注任务已圆满完成！结果保存至: {OUTPUT_FILE}")
    else:
        print(f"\n⏸️ 任务暂停，已完成 {len(processed_df)} / {total_count}。请检查网络后重启。")

if __name__ == "__main__":
    main()