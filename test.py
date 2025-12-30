import json
import pandas as pd
from sentence_transformers import SentenceTransformer, util
import torch

def process_matching():
    # 1. Cấu hình đường dẫn file
    json_path = 'data/vector_store/vectorized_metadata.json'
    csv_path = 'dashboard/dim_query_ground_truth.csv'
    output_csv_path = 'dashboard/dim_query_ground_truth_updated.csv'

    print("Đang đọc dữ liệu...")
    
    # 2. Đọc file JSON (Kho dữ liệu gốc)
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy file {json_path}")
        return

    # Trích xuất list header_path và chunk_index từ JSON
    # Lưu ý: Chúng ta cần đảm bảo header_path là string, nếu null thì gán chuỗi rỗng
    kb_headers = []
    kb_indices = []
    
    for item in json_data:
        meta = item.get('metadata', {})
        header = meta.get('header_path', "")
        idx = meta.get('chunk_index', -1)
        
        if header: # Chỉ lấy những dòng có header
            kb_headers.append(str(header))
            kb_indices.append(idx)

    # 3. Đọc file CSV (File cần đối chiếu)
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy file {csv_path}")
        return

    # Lấy list header_path từ CSV
    # Giả sử tên cột trong CSV là 'Header_path' dựa trên file mẫu bạn đưa
    if 'Header_path' not in df.columns:
        print("Lỗi: Không tìm thấy cột 'Header_path' trong file CSV")
        return
        
    query_headers = df['Header_path'].fillna("").astype(str).tolist()

    print(f"Số lượng mẫu trong JSON: {len(kb_headers)}")
    print(f"Số lượng mẫu trong CSV: {len(query_headers)}")

    # 4. Khởi tạo model Embedding
    # Sử dụng model đa ngôn ngữ để hỗ trợ tốt tiếng Việt
    print("Đang tải model embedding (có thể mất chút thời gian lần đầu)...")
    model = SentenceTransformer('AITeamVN/Vietnamese_Embedding')

    # 5. Encode (Tạo vector)
    print("Đang tạo embedding cho dữ liệu JSON...")
    kb_embeddings = model.encode(kb_headers, convert_to_tensor=True, show_progress_bar=True)

    print("Đang tạo embedding cho dữ liệu CSV...")
    query_embeddings = model.encode(query_headers, convert_to_tensor=True, show_progress_bar=True)

    # 6. Tính toán độ tương đồng (Cosine Similarity)
    print("Đang tính toán độ tương đồng và tìm header giống nhất...")
    # util.cos_sim trả về ma trận [num_query x num_kb]
    cosine_scores = util.cos_sim(query_embeddings, kb_embeddings)

    # 7. Tìm Top 1 và gán Chunk Index
    matched_chunk_indices = []
    matched_scores = []
    matched_header_texts = [] # (Tùy chọn) Lưu lại text gốc để kiểm tra

    for i in range(len(query_headers)):
        # Tìm index của điểm số cao nhất trong hàng i
        best_match_idx = torch.argmax(cosine_scores[i]).item()
        best_score = cosine_scores[i][best_match_idx].item()
        
        # Lấy chunk_index tương ứng từ list gốc của JSON
        found_chunk_index = kb_indices[best_match_idx]
        found_header_text = kb_headers[best_match_idx]

        matched_chunk_indices.append(found_chunk_index)
        matched_scores.append(best_score)
        matched_header_texts.append(found_header_text)

    # 8. Cập nhật vào DataFrame
    # Lưu vào cột 'chunk_index' (ghi đè hoặc tạo mới theo yêu cầu)
    # Ở đây tôi tạo cột mới 'predicted_chunk_index' để bạn dễ so sánh, 
    # sau đó bạn có thể đổi tên nếu muốn ghi đè hoàn toàn.
    
    # Ghi đè cột Chunk_index cũ theo yêu cầu của bạn:
    df['Chunk_index'] = matched_chunk_indices
    
    # (Tùy chọn) Lưu thêm thông tin để debug/kiểm tra độ chính xác
    df['similarity_score'] = matched_scores
    df['matched_header_source'] = matched_header_texts

    # 9. Lưu file mới
    df.to_csv(output_csv_path, index=False, encoding='utf-8-sig')
    print(f"Hoàn tất! File đã được lưu tại: {output_csv_path}")

if __name__ == "__main__":
    process_matching()