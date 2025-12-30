import os
import csv
from typing import List, Dict, Any

def get_questions_from_file(file_path="dashboard/dim_query_ground_truth.csv"):
    """
    Đọc file CSV, lấy các cột 'question' và 'true_churn',
    và trả về danh sách các dictionary.
    
    Args:
        file_path (str): Đường dẫn tới file cần đọc.
        
    Returns:
        list: Danh sách các dictionary với keys 'question' và 'true_churn'.
              Trả về list rỗng nếu lỗi hoặc file trống.
    """
    questions_list = []

    # Kiểm tra xem file có tồn tại không để tránh lỗi
    if not os.path.exists(file_path):
        print(f"Lỗi: Không tìm thấy file tại đường dẫn: {file_path}")
        return []

    try:
        # Mở file CSV với encoding='utf-8' để hỗ trợ tiếng Việt
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            # Đọc từng dòng và thêm vào danh sách
            questions_list = [
                {"question": row["Question"], "correct_chunk_id": int(row["Chunk_index"])}
                for row in reader
                if row.get("Question") and row.get("Chunk_index")
            ]
            
        return questions_list

    except Exception as e:
        print(f"Đã xảy ra lỗi khi đọc file: {e}")
        return []
def extract_header_paths(relevant_chunks: List[Dict[str, Any]]) -> str:
    """
    Trích xuất header_path từ các chunk và biểu diễn dưới dạng cấu trúc cây YAML rút gọn.

    Hàm này thực hiện:
    1. Lấy header_path từ metadata của mỗi chunk.
    2. Phân tách path thành các node (dựa trên dấu '>').
    3. Xây dựng cây phân cấp từ các node.
    4. Trả về chuỗi định dạng YAML thể hiện cấu trúc cây đó.

    Args:
        relevant_chunks (List[Dict[str, Any]]): Danh sách các chunk từ vector search.

    Returns:
        str: Cấu trúc cây header dưới dạng chuỗi YAML (để đưa vào Prompt cho LLM).
    """
    # 1. Xây dựng cây từ danh sách paths
    tree = {}
    
    if not relevant_chunks:
        return ""

    for chunk in relevant_chunks:
        if not isinstance(chunk, dict):
            continue

        metadata = chunk.get("metadata", {})
        if isinstance(metadata, dict):
            header_path = metadata.get("header_path", "")
            
            if header_path:
                # Tách chuỗi thành các phần, loại bỏ khoảng trắng thừa
                # Hỗ trợ cả ' > ' và '>'
                parts = [p.strip() for p in header_path.split('>')]
                parts = [p for p in parts if p] # Loại bỏ chuỗi rỗng
                
                # Chèn vào cây
                current_level = tree
                for part in parts:
                    if part not in current_level:
                        current_level[part] = {}
                    current_level = current_level[part]

    # 2. Hàm đệ quy để chuyển đổi cây thành chuỗi YAML
    def dict_to_yaml(node, depth=0):
        lines = []
        indent = "  " * depth  # 2 spaces indentation
        
        # Sắp xếp key để đảm bảo thứ tự nhất quán
        for key in sorted(node.keys()):
            # Thêm node hiện tại
            lines.append(f"{indent}{key}")
            
            # Đệ quy cho các node con (nếu có)
            if node[key]:
                lines.extend(dict_to_yaml(node[key], depth + 1))
        
        return lines

    # 3. Tạo kết quả
    yaml_lines = dict_to_yaml(tree)
    return "\n".join(yaml_lines)