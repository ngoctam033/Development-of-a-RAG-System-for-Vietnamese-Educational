import json
import pandas as pd
import os
import csv
import re
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
# Cấu hình trang Dashboard
st.set_page_config(layout="wide", page_title="RAG System Evaluation Dashboard")
def load_data(dim_chunk_path, fact_query_path, gt_path):
    """
    Hàm load dữ liệu từ 3 file CSV.
    """
    try:
        # Load Dim Chunk
        df_chunk = pd.read_csv(dim_chunk_path)
        
        # Load Fact Query (File kết quả chạy pipeline)
        # Lưu ý: File này dùng tab separated như logic trước đó
        df_fact = pd.read_csv(fact_query_path, sep='\t')
        
        # Load Ground Truth
        df_gt = pd.read_csv(gt_path)
        
        return df_chunk, df_fact, df_gt
    except Exception as e:
        st.error(f"Lỗi khi load dữ liệu: {e}")
        return None, None, None

def create_dashboard_report(df_chunk, df_fact, df_gt):
    """
    Hàm chính để render dashboard.
    """
    st.title("📊 RAG System Evaluation Dashboard")
    st.markdown("---")

    # --- TIỀN XỬ LÝ DỮ LIỆU ---
    # Merge thông tin Chunk vào Fact để biết Header Path của Target Chunk
    # df_fact['target_chunk_id'] = pd.to_numeric(df_fact['target_chunk_id'], errors='coerce')
    # df_chunk['chunk_index'] = pd.to_numeric(df_chunk['chunk_index'], errors='coerce')
    
    df_merged = pd.merge(
        df_fact, 
        df_chunk[['chunk_index', 'chapter_title', 'header_path']], 
        left_on='target_chunk_id', 
        right_on='chunk_index', 
        how='left'
    )
    
    # Tách dữ liệu theo Pipeline Type
    pipelines = df_fact['pipeline_type'].unique()
    
    # =========================================================================
    # 🟦 PANEL GROUP 1 – OVERVIEW (EXECUTIVE)
    # =========================================================================
    st.header("🟦 PANEL 1: OVERVIEW (EXECUTIVE)")
    
    # Tính KPI tổng hợp
    kpi_df = df_fact.groupby('pipeline_type').agg({
        'hit_rate': 'mean', # Tương đương Recall
        'mrr': 'mean',
        'crr': 'mean',
        'retrieved_chunks_count': 'mean'
    }).reset_index()

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Recall Comparison")
        fig_recall = px.bar(
            kpi_df, x='pipeline_type', y='hit_rate', 
            color='pipeline_type', 
            text_auto='.2%',
            title="Recall Hit Rate by Pipeline",
            labels={'hit_rate': 'Recall (Hit Rate)'}
        )
        st.plotly_chart(fig_recall, use_container_width=True)
        
    with col2:
        st.subheader("MRR Comparison")
        fig_mrr = px.bar(
            kpi_df, x='pipeline_type', y='mrr', 
            color='pipeline_type', 
            text_auto='.2f',
            title="Mean Reciprocal Rank (MRR)",
            labels={'mrr': 'MRR Score'}
        )
        st.plotly_chart(fig_mrr, use_container_width=True)

    # =========================================================================
    # 🟦 PANEL GROUP 2 – RETRIEVAL EFFECTIVENESS
    # =========================================================================
    st.markdown("---")
    st.header("🟦 PANEL 2: RETRIEVAL EFFECTIVENESS")
    
    tab1, tab2, tab3 = st.tabs(["Metrics Distribution", "Candidate Reduction", "Header Analysis"])
    
    with tab1:
        col_mrr_dist, col_rank_dist = st.columns(2)
        
        with col_mrr_dist:
            fig_mrr_box = px.box(
                df_fact, x='pipeline_type', y='mrr', points="all",
                title="MRR Distribution (Độ ổn định của kết quả)",
                color='pipeline_type'
            )
            st.plotly_chart(fig_mrr_box, use_container_width=True)
            
        with col_rank_dist:
            # Chỉ lấy những trường hợp tìm thấy (Rank > 0)
            df_hits = df_fact[df_fact['rank'] > 0]
            fig_rank = px.box(
                df_hits, x='pipeline_type', y='rank', points="all",
                title="Rank Distribution of Correct Chunks (Thấp hơn là tốt hơn)",
                color='pipeline_type'
            )
            fig_rank.update_yaxes(autorange="reversed") # Rank 1 nằm trên cao
            st.plotly_chart(fig_rank, use_container_width=True)

    with tab2:
        col_crr, col_count = st.columns(2)
        with col_crr:
            fig_crr = px.violin(
                df_fact, x='pipeline_type', y='crr', box=True,
                title="Candidate Reduction Ratio (CRR)",
                color='pipeline_type'
            )
            st.plotly_chart(fig_crr, use_container_width=True)
        
        with col_count:
            fig_count = px.histogram(
                df_fact, x='retrieved_chunks_count', color='pipeline_type', barmode='overlay',
                title="Candidate Count Distribution (Số lượng chunk tìm thấy)"
            )
            st.plotly_chart(fig_count, use_container_width=True)

    with tab3:
        st.subheader("Header-path Hit Heatmap (Top 10 Chapters)")
        # Phân tích xem Chapter nào được tìm thấy nhiều nhất (True Positives)
        # Chỉ tính những dòng có hit_rate = 1
        df_hits_only = df_merged[df_merged['hit_rate'] == 1]
        
        if not df_hits_only.empty:
            header_stats = df_hits_only.groupby(['chapter_title', 'pipeline_type']).size().reset_index(name='count')
            # Lấy top 10 chapter phổ biến
            top_chapters = header_stats.groupby('chapter_title')['count'].sum().nlargest(10).index
            header_stats_top = header_stats[header_stats['chapter_title'].isin(top_chapters)]
            
            fig_heatmap = px.density_heatmap(
                header_stats_top, x='pipeline_type', y='chapter_title', z='count',
                title="Hit Count by Chapter Title",
                text_auto=True
            )
            st.plotly_chart(fig_heatmap, use_container_width=True)
        else:
            st.info("Chưa có dữ liệu Hit (Recall = 0) để vẽ Heatmap.")

    # =========================================================================
    # 🟦 PANEL GROUP 3 – ANSWER QUALITY (Placeholder metrics)
    # =========================================================================
    # Do dữ liệu hiện tại chưa có 'Answer Score', ta sẽ dùng 'Rank' làm proxy
    st.markdown("---")
    st.header("🟦 PANEL 3: ANSWER QUALITY (Proxy Metrics)")
    st.caption("*Lưu ý: Dữ liệu hiện tại chưa bao gồm Answer Score/Faithfulness. Biểu đồ dưới đây sử dụng Rank (Vị trí tìm thấy) như một chỉ số chất lượng thay thế.*")

    col_q1, col_q2 = st.columns(2)
    with col_q1:
        # Rank càng nhỏ (gần 1) thì chất lượng context càng cao
        rank_avg = df_hits.groupby('pipeline_type')['rank'].mean().reset_index()
        fig_rank_bar = px.bar(
            rank_avg, x='pipeline_type', y='rank', color='pipeline_type',
            title="Average Rank of Correct Chunk (Lower is Better)",
            text_auto='.2f'
        )
        st.plotly_chart(fig_rank_bar, use_container_width=True)
        
    with col_q2:
        # Recall Preservation Rate
        fig_rpr = px.pie(
            df_fact, names='pipeline_type', values='recall_preservation_rate',
            title="Total Recall Preservation Share"
        )
        st.plotly_chart(fig_rpr, use_container_width=True)

    # =========================================================================
    # 🟦 PANEL GROUP 4 – TRADE-OFF ANALYSIS (Efficiency)
    # =========================================================================
    st.markdown("---")
    st.header("🟦 PANEL 4: TRADE-OFF ANALYSIS")
    
    col_to1, col_to2 = st.columns(2)
    
    with col_to1:
        # Scatter: Retrieved Count vs MRR
        # Xem xét xem việc lấy nhiều chunk có giúp tăng MRR không
        fig_scatter = px.scatter(
            df_fact, x='retrieved_chunks_count', y='mrr', color='pipeline_type',
            title="Trade-off: Retrieved Count vs MRR",
            trendline="ols" # Thêm đường xu hướng
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
        
    with col_to2:
        # Phân tích Failure Cases (Miss Recall)
        # Những case có hit_rate = 0
        miss_df = df_fact[df_fact['hit_rate'] == 0]
        if not miss_df.empty:
            miss_count = miss_df.groupby('pipeline_type').size().reset_index(name='miss_count')
            fig_miss = px.bar(
                miss_count, x='pipeline_type', y='miss_count', color='pipeline_type',
                title="Number of Failed Queries (Zero Recall)",
                text_auto=True
            )
            st.plotly_chart(fig_miss, use_container_width=True)
        else:
            st.success("Tuyệt vời! Không có Failure Case nào.")

    # =========================================================================
    # 🟦 PANEL GROUP 5 – A/B COMPARISON (KEY)
    # =========================================================================
    st.markdown("---")
    st.header("🟦 PANEL 5: A/B COMPARISON TABLE (KEY CONCLUSION)")
    
    # Tạo bảng so sánh Pivot
    pivot_table = df_fact.groupby('pipeline_type').agg({
        'hit_rate': 'mean',
        'mrr': 'mean',
        'rank': lambda x: x[x>0].mean(), # Chỉ tính rank của những case tìm thấy
        'retrieved_chunks_count': 'mean',
        'crr': 'mean'
    }).reset_index()
    
    # Đổi tên cột cho đẹp
    pivot_table.columns = ['Pipeline', 'Recall (Hit Rate)', 'MRR', 'Avg Rank (Correct)', 'Avg Retrieved Count', 'CRR']
    
    # Tính Delta (metadata vs baseline) nếu có đủ 2 loại
    if len(pivot_table) == 2:
        # Giả sử dòng 0 là baseline, dòng 1 là metadata (hoặc ngược lại tùy dữ liệu)
        # Sắp xếp để baseline lên trước (thường là a-z)
        pivot_table = pivot_table.sort_values('Pipeline')
        
        baseline = pivot_table.iloc[0]
        metadata = pivot_table.iloc[1]
        
        delta_row = {
            'Pipeline': 'Δ (Delta)',
            'Recall (Hit Rate)': f"{metadata['Recall (Hit Rate)'] - baseline['Recall (Hit Rate)']:.2%}",
            'MRR': f"{metadata['MRR'] - baseline['MRR']:.4f}",
            'Avg Rank (Correct)': f"{metadata['Avg Rank (Correct)'] - baseline['Avg Rank (Correct)']:.2f}",
            'Avg Retrieved Count': f"{metadata['Avg Retrieved Count'] - baseline['Avg Retrieved Count']:.1f}",
            'CRR': f"{metadata['CRR'] - baseline['CRR']:.2%}"
        }
        pivot_table = pd.concat([pivot_table, pd.DataFrame([delta_row])], ignore_index=True)

    # Format hiển thị
    st.dataframe(
        pivot_table.style.highlight_max(axis=0, color='lightgreen', subset=['Recall (Hit Rate)', 'MRR', 'CRR']),
        use_container_width=True
    )
    
    st.info("📌 **Kết luận:** Bảng trên thể hiện sự chênh lệch hiệu suất giữa các Pipeline. Recall và MRR cao hơn là tốt hơn. Avg Rank thấp hơn là tốt hơn.")
def create_dim_chunk(json_data):
    """
    Hàm chuyển đổi list dictionary thành DataFrame (bảng dim_chunk)
    """
    try:
        # Bước 1: Tạo DataFrame ban đầu từ dữ liệu gốc
        df_raw = pd.DataFrame(json_data)
        
        # Bước 2: Xử lý cột 'metadata' (đang là dạng dict)
        # Sử dụng json_normalize để "làm phẳng" (flatten) cột metadata thành các cột riêng
        # Nếu cột metadata không tồn tại hoặc bị lỗi, cần xử lý ngoại lệ
        if 'metadata' in df_raw.columns:
            df_metadata = pd.json_normalize(df_raw['metadata'])
            
            # Bước 3: Ghép cột 'content' với các cột metadata đã làm phẳng
            # axis=1 nghĩa là ghép theo chiều dọc (cột)
            # drop cột metadata cũ đi để tránh trùng lặp
            dim_chunk = pd.concat([df_raw.drop(columns=['metadata']), df_metadata], axis=1)
        else:
            dim_chunk = df_raw

        # (Tuỳ chọn) Đổi tên cột hoặc sắp xếp lại cột cho đẹp nếu cần
        # Ưu tiên đưa các cột quan trọng lên đầu nếu chúng tồn tại
        priority_cols = ['chunk_index', 'document_name', 'content'] 
        existing_priority_cols = [c for c in priority_cols if c in dim_chunk.columns]
        other_cols = [c for c in dim_chunk.columns if c not in existing_priority_cols]
        
        dim_chunk = dim_chunk[existing_priority_cols + other_cols]

        return dim_chunk

    except Exception as e:
        print(f"Có lỗi xảy ra trong quá trình chuyển đổi dữ liệu: {e}")
        return None
def parse_log_by_separator(file_path):
    """
    Hàm đọc file log và phân tách thành các block dựa trên dòng phân cách.
    Dòng phân cách chứa chuỗi: '=================================================='
    Mỗi block được lưu thành dict {"raw": "nội dung log"}
    """
    blocks = []
    current_block_lines = []
    
    # Chuỗi đặc trưng để nhận diện dòng phân cách
    separator_marker = "rag_pipeline - INFO - [main.py:13] - =================================================="
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            # Kiểm tra xem dòng hiện tại có phải là dòng phân cách không
            if separator_marker in line:
                # Nếu đang có nội dung tích lũy (current_block_lines không rỗng), 
                # thì đóng gói nó lại thành 1 block hoàn chỉnh
                if current_block_lines:
                    # Ghép các dòng lại thành 1 chuỗi text
                    block_content = "".join(current_block_lines).strip()
                    if block_content: # Chỉ thêm nếu nội dung không rỗng
                        blocks.append({"raw": block_content})
                    
                # Reset biến tích lũy để bắt đầu block mới
                # (Dòng separator bị bỏ qua, không đưa vào nội dung raw)
                current_block_lines = [] 
            else:
                # Nếu không phải dòng phân cách, thêm dòng vào block hiện tại
                current_block_lines.append(line)
        
        # Xử lý phần còn lại sau dòng phân cách cuối cùng (nếu có)
        if current_block_lines:
            block_content = "".join(current_block_lines).strip()
            if block_content:
                blocks.append({"raw": block_content})
        
    return blocks
def save_to_csv(data, output_path):
    # Lấy header từ phần tử đầu tiên
    fieldnames = data[0].keys()
    
    with open(output_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
        # SỬ DỤNG delimiter='\t' (Tab) thay vì dấu phẩy mặc định
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, delimiter='\t')
        
        writer.writeheader()
        writer.writerows(data)

def processing_log_folder(folder_path):
    """
    Hàm nhận vào đường dẫn folder, xử lý log, đọc ground truth và tính toán các metrics:
    Recall@K, Hit Rate@K, MRR, Average Rank (cho từng dòng), CRR, Recall Preservation Rate.
    """
    # --- 1. Đọc file CSV Ground Truth bằng Pandas ---
    ground_truth_path = 'dashboard/dim_query_ground_truth.csv'
    
    # Dictionary để tra cứu nhanh: Question -> True Chunk Index
    gt_map = {}
    total_docs_in_corpus = 0 

    if os.path.exists(ground_truth_path):
        try:
            # Đọc file CSV
            df_gt = pd.read_csv(ground_truth_path, encoding='utf-8')
            
            # Tạo map: key là câu hỏi (strip space), value là chunk_index (int)
            # Giả sử cột Question và Chunk_index tồn tại
            if 'Question' in df_gt.columns and 'Chunk_index' in df_gt.columns:
                # Loại bỏ dòng trống hoặc lỗi
                df_gt = df_gt.dropna(subset=['Question', 'Chunk_index'])
                
                for _, row in df_gt.iterrows():
                    q_text = str(row['Question']).strip()
                    try:
                        c_idx = int(row['Chunk_index'])
                        gt_map[q_text] = c_idx
                        # Cập nhật max chunk index làm ước lượng cho total corpus size 
                        # (Nếu không có số chính xác, đây là cách ước lượng tốt nhất từ dữ liệu có sẵn)
                        if c_idx > total_docs_in_corpus:
                            total_docs_in_corpus = c_idx
                    except ValueError:
                        continue
            
            print(f"Đã load Ground Truth: {len(gt_map)} câu hỏi. Total Corpus ước tính: {total_docs_in_corpus}")

        except Exception as e:
            print(f"Lỗi khi đọc file CSV ground truth: {e}")
            total_docs_in_corpus = 1000 # Fallback default nếu lỗi
    else:
        print(f"Cảnh báo: Không tìm thấy file tại {ground_truth_path}")
        total_docs_in_corpus = 1000 # Fallback default

    # --- 2. Xử lý Log và Tính Metrics ---
    raw_data_list = [] 
    
    if os.path.exists(folder_path):
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            
            if os.path.isfile(file_path):
                file_blocks = parse_log_by_separator(file_path)
                
                for item in file_blocks:
                    raw_text = item.get("raw", "")
                    
                    # A. Trích xuất Question
                    question_content = ""
                    match_q = re.search(r'Question:\s*(.*)', raw_text)
                    if match_q:
                        question_content = match_q.group(1).strip()
                        item["question"] = question_content
                    
                    # B. Xác định pipeline_type
                    if "[pipeline_6.py:26]" in raw_text:
                        item["pipeline_type"] = "metadata"
                    else:
                        item["pipeline_type"] = "base line"

                    # C. Trích xuất danh sách Chunk Index được retrieve (theo thứ tự xuất hiện trong log)
                    # Pattern tìm "chunk_index": <số>
                    # Log in ra dạng: "chunk_index": 587
                    retrieved_chunks = []
                    matches_chunks = re.findall(r'"chunk_index":\s*(\d+)', raw_text)
                    if matches_chunks:
                        # Chuyển sang int
                        retrieved_chunks = [int(c) for c in matches_chunks]
                    
                    item["retrieved_chunks_count"] = len(retrieved_chunks)
                    item["retrieved_chunks_list"] = str(retrieved_chunks) # Lưu dạng string để xem

                    # D. Tính toán Metrics (Nếu tìm thấy câu hỏi trong Ground Truth)
                    target_chunk_id = gt_map.get(question_content)
                    item["target_chunk_id"] = target_chunk_id if target_chunk_id is not None else -1

                    # Khởi tạo giá trị mặc định
                    rank = 0
                    mrr = 0.0
                    is_hit = 0 # Đây chính là Recall@K (với K = số lượng retrieve) cho 1 query
                    
                    if target_chunk_id is not None and len(retrieved_chunks) > 0:
                        if target_chunk_id in retrieved_chunks:
                            # Rank bắt đầu từ 1
                            rank = retrieved_chunks.index(target_chunk_id) + 1
                            mrr = 1.0 / rank
                            is_hit = 1
                        else:
                            rank = 0 # Không tìm thấy
                            mrr = 0.0
                            is_hit = 0
                    
                    # Gán các metrics vào item
                    item["rank"] = rank
                    item["mrr"] = mrr
                    item["hit_rate"] = is_hit # Hit Rate của query này (1 hoặc 0)
                    item["recall"] = is_hit   # Recall của query này (1 hoặc 0)
                    
                    # Candidate Reduction Ratio (CRR)
                    # Công thức: 1 - (Số lượng chunk giữ lại / Tổng số chunk)
                    # CRR càng cao nghĩa là bộ lọc càng hiệu quả (giảm nhiều không gian tìm kiếm)
                    if total_docs_in_corpus > 0:
                        crr = 1.0 - (len(retrieved_chunks) / total_docs_in_corpus)
                    else:
                        crr = 0.0
                    item["crr"] = crr

                    # Recall Preservation Rate
                    # Tỷ lệ recall được bảo toàn sau bước retrieve. 
                    # Với 1 query và 1 ground truth, nếu tìm thấy (hit) thì là 100%, không thì 0%.
                    # Nó tương đương với Recall/Hit Rate ở cấp độ row này.
                    item["recall_preservation_rate"] = 1.0 if is_hit else 0.0

                    # E. Dọn dẹp
                    if "raw" in item:
                        del item["raw"]
                    
                    # Chỉ thêm item nếu có Question (đã trích xuất được)
                    if "question" in item: 
                        raw_data_list.append(item)
    
    # --- 3. Chuyển đổi sang DataFrame ---
    return raw_data_list

# --- CHẠY CHƯƠNG TRÌNH ---
def main():
    # --- CẤU HÌNH ĐƯỜNG DẪN ---
    input_file_path = 'data/vector_store/vectorized_metadata.json' 
    dim_chunk_file_path = 'dashboard/dim_chunk.csv'
    log_folder = 'logs'
    fact_rag_query_file_path = 'dashboard/fact_rag_query.csv'
    
    with open(input_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    df_dim_chunk = create_dim_chunk(data)

    if df_dim_chunk is not None:
        # Xuất ra file CSV
        df_dim_chunk.to_csv(dim_chunk_file_path, index=False, encoding='utf-8')
    fact_rag_query = processing_log_folder(log_folder)


    save_to_csv(fact_rag_query,fact_rag_query_file_path)
    # Kiểm tra file tồn tại
    if os.path.exists(fact_rag_query_file_path):
        chunk_df, fact_df, gt_df = load_data(dim_chunk_file_path, fact_rag_query_file_path, 'dashboard/dim_query_ground_truth.csv')
        
        if fact_df is not None:
            create_dashboard_report(chunk_df, fact_df, gt_df)
    else:
        st.warning(f"Chưa tìm thấy file kết quả: {fact_rag_query_file_path}. Hãy chạy script xử lý log trước.")

if __name__ == "__main__":
    main()