import json
import pandas as pd
import os
import csv
import re

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
    """
    Hàm lưu list[dict] thành file CSV.
    """
    fieldnames = data[0].keys()
    
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        writer.writerows(data)

def processing_log_folder(folder_path):
    """
    Hàm nhận vào đường dẫn folder và đếm tổng số dòng của tất cả các file trong đó.
    """
    data = []
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        
        if os.path.isfile(file_path):
            # 1. Lấy các block log từ file
            file_blocks = parse_log_by_separator(file_path)
            
            valid_blocks = []
            for item in file_blocks:
                raw_text = item.get("raw")
                match = re.search(r'Question:\s*(.*)', raw_text)
                
                if match:
                    # match.group(1) là phần nội dung nằm trong dấu ngoặc (.*)
                    question_content = match.group(1).strip()
                    item["question"] = question_content
                # --- LOGIC MỚI: Xác định pipeline_type ---
                if "[pipeline_6.py:26]" in raw_text:
                    item["pipeline_type"] = "metadata"
                else:
                    item["pipeline_type"] = "base line"

                del item["raw"]
                if item: 
                    valid_blocks.append(item)
            data.extend(valid_blocks)          
    return data
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

if __name__ == "__main__":
    main()