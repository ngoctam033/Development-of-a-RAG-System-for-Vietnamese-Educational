import os
def get_questions_from_file(file_path="data_test.txt"):
    """
    Đọc file txt, tách từng dòng, loại bỏ khoảng trắng thừa 
    và trả về danh sách các câu hỏi.
    
    Args:
        file_path (str): Đường dẫn tới file cần đọc.
        
    Returns:
        list: Danh sách các câu hỏi (string). Trả về list rỗng nếu lỗi hoặc file trống.
    """
    questions_list = []

    # Kiểm tra xem file có tồn tại không để tránh lỗi
    if not os.path.exists(file_path):
        print(f"Lỗi: Không tìm thấy file tại đường dẫn: {file_path}")
        return []

    try:
        # Mở file với encoding='utf-8' để hỗ trợ tiếng Việt
        with open(file_path, 'r', encoding='utf-8') as file:
            # List comprehension: đọc dòng, strip() và chỉ lấy dòng có nội dung
            questions_list = [line.strip() for line in file if line.strip()]
            
        return questions_list

    except Exception as e:
        print(f"Đã xảy ra lỗi khi đọc file: {e}")
        return []