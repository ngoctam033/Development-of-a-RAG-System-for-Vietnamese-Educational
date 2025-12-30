import json
import pandas as pd
import os
import re
import csv
# import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Tuple, Any, Optional
from openai import OpenAI

# Cấu hình trang Dashboard
# st.set_page_config(layout="wide", page_title="RAG System Evaluation Dashboard")

# =============================================================================
# 1. I/O & FILE OPERATIONS (ĐỌC/GHI FILE)
# =============================================================================

def load_json_file(file_path: str) -> Optional[Any]:
    """Đọc file JSON an toàn."""
    if not os.path.exists(file_path):
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Lỗi đọc JSON {file_path}: {e}")
        return None

def load_csv_file(file_path: str) -> Optional[pd.DataFrame]:
    """Đọc file CSV an toàn."""
    if not os.path.exists(file_path):
        return None
    try:
        return pd.read_csv(file_path)
    except Exception as e:
        print(f"❌ Lỗi đọc CSV {file_path}: {e}")
        return None

def save_dataframe_to_csv(df: pd.DataFrame, file_path: str) -> None:
    """Lưu DataFrame xuống CSV."""
    try:
        df.to_csv(file_path, index=False, encoding='utf-8')
        print(f"✅ Đã lưu file: {file_path} ({len(df)} dòng)")
    except Exception as e:
        print(f"❌ Lỗi lưu CSV {file_path}: {e}")

# =============================================================================
# 2. LOG PARSING LOGIC (XỬ LÝ TEXT LOG)
# =============================================================================

def split_log_file_into_blocks(file_path: str, separator: str = "==================================================") -> List[str]:
    """Đọc file log và tách thành các block text dựa trên dòng phân cách."""
    blocks = []
    current_lines = []
    
    if not os.path.exists(file_path):
        return []

    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            if separator in line:
                content = "".join(current_lines).strip()
                if content:
                    blocks.append(content)
                current_lines = []
            else:
                current_lines.append(line)
        
        # Xử lý block cuối cùng
        content = "".join(current_lines).strip()
        if content:
            blocks.append(content)
            
    return blocks

def extract_log_metadata(raw_text: str) -> Dict[str, Any]:
    """Trích xuất thông tin cơ bản từ text log (Question, Model, Pipeline Type)."""
    # Filter: Chỉ lấy log của model cụ thể này (giữ nguyên logic cũ)
    if "Sử dụng model: qwen/qwen3-4b-2507" not in raw_text:
        return {}

    data = {"raw": raw_text}
    
    # 1. Extract Question
    match_q = re.search(r'Question:\s*(.*)', raw_text)
    data["question"] = match_q.group(1).strip() if match_q else ""

    # 2. Extract Pipeline Type
    if "[pipeline_6.py:26]" in raw_text:
        data["pipeline_type"] = "metadata"
    else:
        data["pipeline_type"] = "base line"
        
    return data

def extract_log_answer_and_chunks(raw_text: str) -> Dict[str, Any]:
    """Trích xuất câu trả lời và danh sách chunk index."""
    data = {}
    
    # 1. Extract Answer
    match_ans = re.search(r'- ANSWER:\s*(.*)', raw_text, re.DOTALL)
    llm_answer = match_ans.group(1).strip() if match_ans else ""
    data["llm_answer"] = llm_answer
    
    # 2. Check Has Answer
    # Logic: Nếu model trả lời kiểu "không tìm thấy" -> has_answer = False
    refusal_phrase = "Tôi không tìm thấy thông tin đủ để trả lời câu hỏi này"
    data["has_answer"] = False if refusal_phrase in llm_answer else True

    # 3. Extract Retrieved Chunks
    matches_chunks = re.findall(r'"chunk_index":\s*(\d+)', raw_text)
    chunks = [int(c) for c in matches_chunks] if matches_chunks else []
    
    data["retrieved_chunks_list"] = str(chunks) # Lưu dạng string để save CSV
    data["retrieved_chunks_raw"] = chunks # Lưu dạng list để tính toán
    data["retrieved_chunks_count"] = len(chunks)
    
    return data

# =============================================================================
# 3. METRIC CALCULATION (TÍNH TOÁN CHỈ SỐ)
# =============================================================================

def calculate_rank_and_mrr(target_id: int, retrieved_ids: List[int]) -> Tuple[int, float, int]:
    """Tính Rank, MRR và Hit (Recall)."""
    if target_id == -1 or not retrieved_ids:
        return 0, 0.0, 0
        
    if target_id in retrieved_ids:
        rank = retrieved_ids.index(target_id) + 1
        mrr = 1.0 / rank
        is_hit = 1
    else:
        rank = 0
        mrr = 0.0
        is_hit = 0
        
    return rank, mrr, is_hit

def calculate_crr(retrieved_count: int, total_docs: int) -> float:
    """Tính Candidate Reduction Ratio."""
    if total_docs <= 0:
        return 0.0
    return 1.0 - (retrieved_count / total_docs)

# =============================================================================
# 4. DATA PROCESSING (XỬ LÝ DATAFRAME & LOGIC NGHIỆP VỤ)
# =============================================================================

def process_dim_chunk(json_data: List[Dict]) -> Optional[pd.DataFrame]:
    """Chuyển đổi dữ liệu JSON dim_chunk thành DataFrame phẳng."""
    if not json_data:
        return None
    try:
        df_raw = pd.DataFrame(json_data)
        if 'metadata' in df_raw.columns:
            df_metadata = pd.json_normalize(df_raw['metadata'])
            df = pd.concat([df_raw.drop(columns=['metadata']), df_metadata], axis=1)
        else:
            df = df_raw
            
        # Sắp xếp cột ưu tiên
        priority_cols = ['chunk_index', 'document_name', 'content'] 
        existing_cols = [c for c in priority_cols if c in df.columns]
        other_cols = [c for c in df.columns if c not in existing_cols]
        
        return df[existing_cols + other_cols]
    except Exception as e:
        print(f"Lỗi xử lý dim_chunk: {e}")
        return None

def load_ground_truth_map(file_path: str) -> Tuple[Dict[str, int], int]:
    """Load Ground Truth và trả về Mapping {Question: ChunkIndex} cùng tổng số docs."""
    gt_map = {}
    max_idx = 0
    default_total = 1000

    df_gt = load_csv_file(file_path)
    if df_gt is None:
        print(f"⚠️ Cảnh báo: Không tìm thấy Ground Truth tại {file_path}")
        return gt_map, default_total

    if 'Question' in df_gt.columns and 'Chunk_index' in df_gt.columns:
        df_clean = df_gt.dropna(subset=['Question', 'Chunk_index'])
        for _, row in df_clean.iterrows():
            q = str(row['Question']).strip()
            try:
                c_idx = int(row['Chunk_index'])
                gt_map[q] = c_idx
                if c_idx > max_idx:
                    max_idx = c_idx
            except ValueError:
                continue
    
    print(f"Đã load Ground Truth: {len(gt_map)} câu hỏi.")
    return gt_map, (max_idx if max_idx > 0 else default_total)

def clean_processed_logs(df: pd.DataFrame) -> pd.DataFrame:
    """Lọc rác, xóa dòng lỗi, xóa trùng lặp."""
    if df.empty: 
        return df
    
    initial_len = len(df)
    
    # 1. Xóa dòng không có chunks (list rỗng '[]')
    if 'retrieved_chunks_list' in df.columns:
        df = df[df['retrieved_chunks_list'] != '[]']
        
    # 2. Xóa dòng không có câu trả lời (chuỗi rỗng)
    if 'llm_answer' in df.columns:
        df = df[df['llm_answer'].astype(str).str.strip() != '']
        
    # 3. Deduplicate (giữ log mới nhất cho cùng 1 câu hỏi + pipeline)
    if 'question' in df.columns and 'pipeline_type' in df.columns:
        df = df.drop_duplicates(subset=['question', 'pipeline_type'], keep='last')
        
    print(f"🧹 Validation: Đã lọc {initial_len - len(df)} dòng rác/trùng lặp.")
    return df
def call_lm_studio_completion(prompt: str, system_prompt: str = "You are a helpful assistant.", temperature: float = 0.2) -> str:
    """
    Hàm sinh văn bản sử dụng Local LLM thông qua LM Studio (OpenAI Compatible API).
    Yêu cầu: Đã cài đặt thư viện 'openai' (pip install openai).
    """

    try:
        # Cấu hình Client trỏ tới Local Server của LM Studio
        client = OpenAI(
            base_url="http://localhost:1234/v1", 
            api_key="lm-studio"
        )

        # Lấy danh sách model đang load
        try:
            models = client.models.list()
            if not models.data:
                print("⚠️ [LM Studio] Không có model nào được load.")
                return ""
            model_name = models.data[0].id
        except Exception:
            # Fallback nếu API list models gặp lỗi
            model_name = "local-model"

        # Gọi Chat Completion
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=200, # Giới hạn token output cho task verify ngắn gọn
        )
        
        return response.choices[0].message.content.strip()
            
    except Exception as e:
        print(f"❌ Lỗi kết nối LM Studio: {str(e)}")
        return ""
def find_best_matching_chunk_with_llm(question: str, answer: str, retrieved_ids: List[int], chunk_df: pd.DataFrame) -> int:
    """
    Gọi Local LLM để kiểm tra xem trong danh sách retrieved_ids có chunk nào
    thực sự chứa thông tin trả lời cho câu hỏi không (Semantic Match).
    Sử dụng chunk_df (pandas DataFrame) để tra cứu nội dung.
    Trả về chunk_index phù hợp nhất hoặc -1.
    """
    
    if not retrieved_ids or chunk_df is None or chunk_df.empty:
        return -1

    # Kiểm tra xem DataFrame có cột chunk_index không để query cho chính xác
    has_index_col = 'chunk_index' in chunk_df.columns
    has_content_col = 'content' in chunk_df.columns

    if not has_content_col:
        return -1

    print(f"🔍 Đang gọi Local LLM để verify chunk cho câu hỏi: '{question}'...")
    
    # System Prompt dành riêng cho task Verification
    verification_system_prompt = (
        "You are an expert evaluator for a RAG system. "
        "Your task is to verify if the provided Context contains the specific information needed to answer the Question."
    )

    for c_id in retrieved_ids:
        chunk_content = ""
        
        # Lấy nội dung từ DataFrame
        if has_index_col:
            # Lọc theo cột chunk_index
            match_row = chunk_df[chunk_df['chunk_index'] == c_id]
            if not match_row.empty:
                chunk_content = str(match_row.iloc[0]['content'])
        else:
            # Fallback: Giả sử index của DF là chunk_index nếu không có cột rõ ràng
            if c_id in chunk_df.index:
                 chunk_content = str(chunk_df.loc[c_id]['content'])

        if not chunk_content:
            continue
            
        # Prompt đánh giá
        prompt = f"""
        Question: {question}
        Answer: {answer}
        
        Context:
        {chunk_content}
        
        Task: Does the Context provided above contain the specific information used to generate the Answer?
        Respond with EXACTLY one word: "YES" or "NO".
        """
        
        # --- GỌI API THỰC TẾ ---
        response_text = call_lm_studio_completion(
            prompt=prompt, 
            system_prompt=verification_system_prompt,
            temperature=0.0 # Temp = 0 để kết quả nhất quán
        )
        
        # Kiểm tra kết quả trả về
        if response_text and "YES" in response_text.upper():
            print(f"✅ LLM Found Match: Chunk {c_id}")
            return c_id

    return -1
def evaluate_single_log_item(item: Dict[str, Any], gt_map: Dict[str, int], total_docs: int, chunk_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Tính toán các chỉ số đánh giá cho một dòng log đơn lẻ.
    Bao gồm logic kiểm tra lại bằng LLM nếu không khớp nhãn.
    """
    retrieved_ids = item.get("retrieved_chunks_raw", [])
    
    # 1. Determine Target Chunk ID (WITH LLM FALLBACK)
    gt_target_id = gt_map.get(item["question"], -1)
    final_target_id = gt_target_id
    
    # # Logic kiểm tra bằng LLM nếu target gốc bị thiếu hoặc không tìm thấy trong list retrieved
    if (final_target_id == -1 or final_target_id not in retrieved_ids) and retrieved_ids:
        
        corrected_id = find_best_matching_chunk_with_llm(
            item["question"], 
            item["llm_answer"], 
            retrieved_ids, 
            chunk_df
        )
        
        if corrected_id != -1:
            final_target_id = corrected_id
            item["is_corrected_by_llm"] = True
        else:
            item["is_corrected_by_llm"] = False

    item["target_chunk_id"] = final_target_id
    
    # 2. Calculate Metrics
    rank, mrr, is_hit = calculate_rank_and_mrr(final_target_id, retrieved_ids)
    # crr = calculate_crr(item.get("retrieved_chunks_count", 0), total_docs)
    
    item.update({
        "rank": rank,
        "mrr": mrr,
        "hit_rate": is_hit,
        "recall": is_hit,
        "recall_preservation_rate": 1.0 if is_hit else 0.0,
        # "crr": crr
    })
    item["is_processed"] = True
    return item
def process_log_files(folder_path: str, gt_map: Dict[str, int], total_docs: int, chunk_df: pd.DataFrame, fact_query_path: str) -> List[Dict]:
    """Hàm lõi: Duyệt file log -> Parse -> Tính metric -> Trả về list dict."""
    processed_data = []
            
    # Tạo set lookup cho các câu trả lời đã được xử lý (is_processed = True) để tăng tốc độ kiểm tra
    processed_answers_set = {
        item['llm_answer'] 
        for item in processed_data 
        if item.get('is_processed') == True and 'llm_answer' in item
    }
    
    if not os.path.exists(folder_path):
        return processed_data

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if not os.path.isfile(file_path):
            continue

        blocks = split_log_file_into_blocks(file_path)
        
        for raw_text in blocks:
            # 1. Extract Metadata
            meta = extract_log_metadata(raw_text)
            if not meta: 
                continue
                
            # 2. Extract Answer & Retrieval Info
            content = extract_log_answer_and_chunks(raw_text)
            
            # --- KIỂM TRA ĐÃ XỬ LÝ CHƯA ---
            # Nếu câu trả lời đã tồn tại trong dữ liệu cũ và is_processed = True -> Bỏ qua
            if content.get("llm_answer") in processed_answers_set:
                continue

            # 3. Merge Info
            item = {**meta, **content}
            
            # # 4. Calculate Metrics (Delegated to evaluate_single_log_item)
            item = evaluate_single_log_item(item, gt_map, total_docs, chunk_df)
            
            # Xóa các trường tạm
            if "raw" in item: del item["raw"]
            if "retrieved_chunks_raw" in item: del item["retrieved_chunks_raw"]
            
            processed_data.append(item)
            
    return processed_data


# =============================================================================
# 5. VISUALIZATION COMPONENTS (DASHBOARD PANELS)
# =============================================================================

# def render_overview_panel(df: pd.DataFrame):
#     """Vẽ Panel 1: Overview KPIs."""
#     st.header("🟦 PANEL 1: OVERVIEW (EXECUTIVE)")
    
#     agg_dict = {
#         'hit_rate': 'mean',
#         'mrr': 'mean',
#         'retrieved_chunks_count': 'mean'
#     }
    
#     has_ans_col = None
#     if 'has_answer' in df.columns:
#         df['has_answer_int'] = df['has_answer'].astype(int)
#         agg_dict['has_answer_int'] = 'mean'
#         has_ans_col = 'has_answer_int'

#     kpi_df = df.groupby('pipeline_type').agg(agg_dict).reset_index()

#     col1, col2 = st.columns(2)
#     with col1:
#         st.subheader("Recall Comparison")
#         fig = px.bar(kpi_df, x='pipeline_type', y='hit_rate', color='pipeline_type', 
#                      text_auto='.2%', title="Recall Hit Rate")
#         st.plotly_chart(fig, use_container_width=True)
        
#     with col2:
#         if has_ans_col:
#             st.subheader("Response Rate Comparison")
#             fig = px.bar(kpi_df, x='pipeline_type', y=has_ans_col, color='pipeline_type', 
#                          text_auto='.2%', title="Response Rate")
#         else:
#             st.subheader("MRR Comparison")
#             fig = px.bar(kpi_df, x='pipeline_type', y='mrr', color='pipeline_type', 
#                          text_auto='.2f', title="Mean Reciprocal Rank")
#         st.plotly_chart(fig, use_container_width=True)

# def render_retrieval_panel(df: pd.DataFrame, df_merged: pd.DataFrame):
#     """Vẽ Panel 2: Retrieval Effectiveness."""
#     st.markdown("---")
#     st.header("🟦 PANEL 2: RETRIEVAL EFFECTIVENESS")
    
#     tab1, tab2, tab3 = st.tabs(["Metrics Dist", "Candidate Reduction", "Header Analysis"])
    
#     with tab1:
#         c1, c2 = st.columns(2)
#         with c1:
#             fig = px.box(df, x='pipeline_type', y='mrr', color='pipeline_type', title="MRR Distribution")
#             st.plotly_chart(fig, use_container_width=True)
#         with c2:
#             df_hits = df[df['rank'] > 0]
#             if not df_hits.empty:
#                 fig = px.box(df_hits, x='pipeline_type', y='rank', color='pipeline_type', title="Rank Distribution")
#                 fig.update_yaxes(autorange="reversed")
#                 st.plotly_chart(fig, use_container_width=True)
                
#     with tab2:
#         c1, c2 = st.columns(2)
#         with c1:
#             fig = px.violin(df, x='pipeline_type', y='crr', box=True, color='pipeline_type', title="CRR")
#             st.plotly_chart(fig, use_container_width=True)
#         with c2:
#             fig = px.histogram(df, x='retrieved_chunks_count', color='pipeline_type', title="Chunk Count Dist")
#             st.plotly_chart(fig, use_container_width=True)
            
#     with tab3:
#         df_hits_only = df_merged[df_merged['hit_rate'] == 1]
#         if not df_hits_only.empty and 'chapter_title' in df_hits_only.columns:
#             stats = df_hits_only.groupby(['chapter_title', 'pipeline_type']).size().reset_index(name='count')
#             top = stats.groupby('chapter_title')['count'].sum().nlargest(10).index
#             stats_top = stats[stats['chapter_title'].isin(top)]
#             fig = px.density_heatmap(stats_top, x='pipeline_type', y='chapter_title', z='count', title="Heatmap")
#             st.plotly_chart(fig, use_container_width=True)

def classify_behavior_row(row):
    """Logic phân loại hành vi Generation."""
    hit = row['hit_rate'] > 0
    answered = bool(row['has_answer'])
    
    if hit and answered: return "Grounded Answer (Good)"
    if not hit and not answered: return "Safe Refusal (Good)"
    if not hit and answered: return "Potential Hallucination (Risk)"
    if hit and not answered: return "Over-Conservative (Miss)"
    return "Unknown"

# def render_generation_panel(df: pd.DataFrame):
#     """Vẽ Panel 3: Generation Behavior."""
#     st.markdown("---")
#     st.header("🟦 PANEL 3: GENERATION BEHAVIOR")
    
#     if 'has_answer' not in df.columns:
#         st.warning("Thiếu cột 'has_answer'.")
#         return

#     df['behavior_class'] = df.apply(classify_behavior_row, axis=1)
    
#     counts = df.groupby(['pipeline_type', 'behavior_class']).size().reset_index(name='count')
#     totals = df.groupby('pipeline_type').size().reset_index(name='total')
#     counts = counts.merge(totals, on='pipeline_type')
#     counts['percentage'] = counts['count'] / counts['total']
    
#     color_map = {
#         "Grounded Answer (Good)": "#2ecc71",
#         "Safe Refusal (Good)": "#3498db",
#         "Potential Hallucination (Risk)": "#e74c3c",
#         "Over-Conservative (Miss)": "#f1c40f"
#     }
    
#     fig = px.bar(counts, x='pipeline_type', y='percentage', color='behavior_class', 
#                  color_discrete_map=color_map, text_auto='.1%', title="Behavior Distribution")
#     st.plotly_chart(fig, use_container_width=True)

# def render_comparison_table(df: pd.DataFrame):
#     """Vẽ Panel 5: Comparison Table."""
#     st.markdown("---")
#     st.header("🟦 PANEL 5: KEY CONCLUSION")
    
#     agg_conf = {
#         'hit_rate': 'mean', 'mrr': 'mean', 
#         'retrieved_chunks_count': 'mean', 
#         'rank': lambda x: x[x>0].mean() if (x>0).any() else 0
#     }
#     if 'has_answer_int' in df.columns:
#         agg_conf['has_answer_int'] = 'mean'
        
#     pivot = df.groupby('pipeline_type').agg(agg_conf).reset_index()
    
#     rename_map = {
#         'pipeline_type': 'Pipeline', 'hit_rate': 'Recall', 'mrr': 'MRR',
#         'rank': 'Avg Rank (Correct)', 'retrieved_chunks_count': 'Avg Count',
#         'has_answer_int': 'Response Rate'
#     }
#     pivot = pivot.rename(columns=rename_map)
    
#     # Tính Delta nếu có 2 dòng
#     if len(pivot) == 2:
#         pivot = pivot.sort_values('Pipeline').reset_index(drop=True)
#         delta = {'Pipeline': 'Δ (Delta)'}
#         for col in pivot.select_dtypes(include='number').columns:
#             delta[col] = pivot.iloc[1][col] - pivot.iloc[0][col]
#         pivot = pd.concat([pivot, pd.DataFrame([delta])], ignore_index=True)

    # st.dataframe(pivot.style.highlight_max(axis=0, color='lightgreen').format("{:.2%}", subset=['Recall', 'Response Rate']), use_container_width=True)

# def create_dashboard_report(df_chunk, df_fact, df_gt):
#     """Hàm Main của Dashboard: Ghép các panel lại."""
#     # st.title("📊 RAG System Evaluation Dashboard")
    
#     # Merge dữ liệu chunk info vào fact
#     df_merged = pd.merge(
#         df_fact, 
#         df_chunk[['chunk_index', 'chapter_title', 'header_path']], 
#         left_on='target_chunk_id', 
#         right_on='chunk_index', 
#         how='left'
#     )
    
#     render_overview_panel(df_fact)
#     render_retrieval_panel(df_fact, df_merged)
#     render_generation_panel(df_fact)
#     render_comparison_table(df_fact)
def cal_hit_rate(row, chunk_df: pd.DataFrame):
    """
    Hàm tính toán lại hit_rate và target_chunk_id.
    """
    # Lấy giá trị hiện tại làm mặc định
    original_target = row.get('target_chunk_id', 0)
    
    # Mặc định giữ nguyên giá trị cũ nếu không tính toán được gì mới
    new_hit_rate = row.get('hit_rate', 0.0) 
    new_target_chunk_id = original_target
    rank = row.get('rank', 0)
    mrr = row.get('mrr', 0.0)
    recall_preservation_rate = row.get('recall_preservation_rate', 0.0)

    # 1. Xử lý retrieved_chunks_list (Quan trọng: Convert string sang list nếu cần)
    retrieved_list = row.get("retrieved_chunks_list", [])

    try:
        print(f"--> Đang gọi LLM cho câu hỏi: {str(row.get('question'))[:30]}...")
        
        corrected_id = find_best_matching_chunk_with_llm(
            row.get("question", ""), 
            row.get("llm_answer", ""), 
            retrieved_list, 
            chunk_df
        )
        
        if corrected_id != -1:
            new_target_chunk_id = corrected_id
            
            # Tính toán lại chỉ số nếu tìm thấy target mới
            if new_target_chunk_id in retrieved_list:
                new_hit_rate = 1.0
                rank = retrieved_list.index(new_target_chunk_id) + 1
                mrr = 1.0 / rank
                recall_preservation_rate = 1.0
            else:
                # Trường hợp LLM trả về ID nhưng ID đó vẫn không nằm trong top k retrieved (hiếm gặp)
                new_hit_rate = 0.0
                rank = 0
                mrr = 0.0
                
    except Exception as e:
            print(f"⚠️ Lỗi khi gọi LLM: {e}")

    return pd.Series([new_hit_rate, new_target_chunk_id, rank, mrr, recall_preservation_rate], 
                     index=['hit_rate', 'target_chunk_id', 'rank', 'mrr', 'recall_preservation_rate'])

def calculate_metrics(df: pd.DataFrame, df_chunk: pd.DataFrame):
    try:
        df['is_processed'] = False
        
        if 'hit_rate' in df.columns:
            # --- FIX QUAN TRỌNG NHẤT ---
            # 1. Đảm bảo hit_rate là dạng số để so sánh
            df['hit_rate'] = pd.to_numeric(df['hit_rate'], errors='coerce').fillna(0)
            
            # 2. Tạo mask so sánh với số 0 (không phải chuỗi "0")
            # Lọc những dòng hit_rate = 0 VÀ has_answer = True
            mask = (df['hit_rate'] == 0) & (df['has_answer'] == True)
            
            print(f"Số lượng dòng cần tính lại: {mask.sum()}")

            if mask.any():
                target_cols = ['hit_rate', 'target_chunk_id', 'rank', 'mrr', 'recall_preservation_rate']
                
                # Lấy danh sách index của các dòng cần xử lý
                indices_to_process = df[mask].index
                total = len(indices_to_process)
                
                print(f"Bắt đầu xử lý {total} dòng theo cơ chế vòng lặp...")

                # DUYỆT QUA TỪNG DÒNG (LOOP) THAY VÌ APPLY
                for idx, i in enumerate(indices_to_process):
                    try:
                        # Lấy row hiện tại
                        row = df.loc[i]
                        
                        # Gọi hàm tính toán logic
                        result_series = cal_hit_rate(row, df_chunk)
                        
                        # Cập nhật kết quả ngay lập tức vào DataFrame gốc tại index tương ứng
                        df.loc[i, target_cols] = result_series
                        df.loc[i, 'is_processed'] = True
                        
                        # In tiến độ (Progress logging)
                        if (idx + 1) % 1 == 0: # In mỗi dòng để dễ theo dõi
                             print(f"✅ Đã xử lý xong dòng index {i} ({idx + 1}/{total})")

                    except Exception as row_error:
                        print(f"❌ Lỗi tại dòng index {i}: {row_error}")
                        # Continue để không dừng chương trình nếu 1 dòng lỗi
                        continue
                
        return df

    except KeyboardInterrupt:
        print("\n⛔ [STOP] User stopped.")
        return df
    except Exception as e:
        print(f"\n❌ [ERROR]: {str(e)}")
        import traceback
        traceback.print_exc()
        return df
# =============================================================================
# 6. MAIN ORCHESTRATOR (HÀM CHẠY CHÍNH)
# =============================================================================

def main():
    try:
        # --- CẤU HÌNH ĐƯỜNG DẪN ---
        PATH_CONFIG = {
            'vector_meta': 'data/vector_store/vectorized_metadata.json',
            'dim_chunk': 'dashboard/dim_chunk.csv',
            'log_folder': 'logs',
            'fact_query': 'dashboard/fact_rag_query.csv',
            'ground_truth': 'dashboard/dim_query_ground_truth.csv'
        }

        # BƯỚC 1: Xử lý dim_chunk (nếu có file nguồn)
        if os.path.exists(PATH_CONFIG['vector_meta']):
            raw_json = load_json_file(PATH_CONFIG['vector_meta'])
            df_chunk = process_dim_chunk(raw_json)
            if df_chunk is not None:
                save_dataframe_to_csv(df_chunk, PATH_CONFIG['dim_chunk'])
        else:
            print(f"⚠️ Không tìm thấy {PATH_CONFIG['vector_meta']}. Bỏ qua bước tạo dim_chunk.")

        # BƯỚC 2: Xử lý Logs -> Fact Query
        gt_map, total_docs = load_ground_truth_map(PATH_CONFIG['ground_truth'])
        raw_logs = process_log_files(PATH_CONFIG['log_folder'], gt_map, total_docs, df_chunk,PATH_CONFIG['fact_query'])
    
        df_result = pd.DataFrame(raw_logs)
        df_result = clean_processed_logs(df_result)
        # df_result = calculate_metrics(df_result, df_chunk)
        
        if not df_result.empty:
            save_dataframe_to_csv(df_result, PATH_CONFIG['fact_query'])
        else:
            print("⚠️ Không có dữ liệu log hợp lệ để lưu.")
            
    except KeyboardInterrupt:
        print("\n⛔ [STOP] Dừng chương trình khi đang xử lý DataFrame.")
        if raw_logs:
             print("💾 Đang lưu dữ liệu thô...")
             df_temp = pd.DataFrame(raw_logs)
             save_dataframe_to_csv(df_temp, PATH_CONFIG['fact_query'])
             
    except Exception as e:
        print(f"❌ [ERROR] Lỗi khi xử lý DataFrame: {e}")
        if raw_logs:
             df_temp = pd.DataFrame(raw_logs)
             save_dataframe_to_csv(df_temp, PATH_CONFIG['fact_query'])

    # BƯỚC 3: Render Dashboard (nếu file tồn tại)
    if os.path.exists(PATH_CONFIG['fact_query']):
        df_chunk = load_csv_file(PATH_CONFIG['dim_chunk'])
        df_fact = load_csv_file(PATH_CONFIG['fact_query'])
        df_gt = load_csv_file(PATH_CONFIG['ground_truth'])
        
        # if df_fact is not None and df_chunk is not None:
        #     create_dashboard_report(df_chunk, df_fact, df_gt)
    else:
        pass
        # st.warning(f"Chưa có file kết quả: {PATH_CONFIG['fact_query']}")

if __name__ == "__main__":
    main()