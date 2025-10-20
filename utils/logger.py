"""
Module cấu hình logging cho toàn bộ dự án
"""
import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger(logger_name='rag_pipeline', log_dir='logs', level=logging.INFO):
    """
    Thiết lập logger với cấu hình tiêu chuẩn
    
    Args:
        logger_name: Tên của logger
        log_dir: Thư mục lưu trữ file log
        level: Mức độ logging (mặc định: logging.INFO)
        
    Returns:
        Logger đã được cấu hình
    """
    # Đảm bảo thư mục log tồn tại
    os.makedirs(log_dir, exist_ok=True)
    
    # Tạo logger
    logger = logging.getLogger(logger_name)
    
    # Kiểm tra xem logger đã được cấu hình chưa để tránh duplicate
    if logger.hasHandlers():
        return logger
        
    logger.setLevel(level)
    
    # Định dạng log chi tiết (thêm thông tin file và dòng lệnh)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )
    
    # Handler cho file (với rotation)
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, f'{logger_name}.log'), 
        maxBytes=10*1024*1024,  # 10 MB
        backupCount=5
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    
    # Handler cho console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    
    # Thêm handlers vào logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Logger mặc định cho toàn bộ dự án
logger = setup_logger()