import os
import csv

def get_questions_from_file(file_path="data_test.csv"):
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
                {"question": row["question"], "true_churn": int(row["true_churn"])}
                for row in reader
                if row.get("question") and row.get("true_churn")
            ]
            
        return questions_list

    except Exception as e:
        print(f"Đã xảy ra lỗi khi đọc file: {e}")
        return []