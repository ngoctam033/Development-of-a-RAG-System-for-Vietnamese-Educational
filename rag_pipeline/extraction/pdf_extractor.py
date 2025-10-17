import pymupdf4llm

import os
from typing import List, Dict

from config.pipeline_config import RAW_DATA_FOLDER_PATH
from utils.logger import default_logger as logger

#  Tạo hàm để lấy tất cả các file trong thư mục RAW_DATA_FOLDER_PATH
def get_all_files_in_folder(
    folder_path: str = RAW_DATA_FOLDER_PATH, 
    extensions: List[str] = ['.pdf']
) -> List[Dict[str, str]]:
    """
    Lấy tất cả các file trong thư mục với định dạng được chỉ định

    Args:
        folder_path: Đường dẫn đến thư mục cần quét
        extensions: Danh sách các phần mở rộng file cần lọc (mặc định: ['.pdf'])

    Returns:
        Danh sách các dictionary chứa thông tin về file:
            - 'path': Đường dẫn đầy đủ của file
            - 'name': Tên file (bao gồm phần mở rộng)
            - 'base_name': Tên file (không có phần mở rộng)
            - 'ext': Phần mở rộng của file
    """
    # Kiểm tra nếu thư mục không tồn tại
    if not os.path.exists(folder_path):
        logger.error(f"Thư mục không tồn tại: {folder_path}")
        return []

    # Khởi tạo danh sách kết quả
    files_info = []

    # Chuyển extensions sang chữ thường để so sánh không phân biệt hoa thường
    extensions_lower = [ext.lower() for ext in extensions]

    # Lặp qua tất cả các file trong thư mục
    for file_name in os.listdir(folder_path):
        # Lấy đường dẫn đầy đủ của file
        file_path = os.path.join(folder_path, file_name)

        # Kiểm tra nếu là file (không phải thư mục)
        if os.path.isfile(file_path):
            # Lấy phần mở rộng của file
            _, ext = os.path.splitext(file_name)

            # Kiểm tra nếu file có phần mở rộng nằm trong danh sách cần lọc
            if ext.lower() in extensions_lower:
                # Lấy tên file không có phần mở rộng
                base_name = os.path.splitext(file_name)[0]

                # Thêm thông tin file vào danh sách kết quả
                files_info.append({
                    'path': file_path,
                    'name': file_name,
                    'base_name': base_name,
                    'ext': ext
                })

    # Ghi log thông báo
    if len(files_info) > 0:
        logger.info(f"Tìm thấy {len(files_info)} file {', '.join(extensions)} trong thư mục {folder_path}")
    else:
        logger.warning(f"Không tìm thấy file {', '.join(extensions)} nào trong thư mục {folder_path}")

    return files_info

def extract_pdf_to_markdown(
    pdf_file_path: str,
    page_chunks: bool = False,
    write_images: bool = False,
    image_path: str = "./images/",
    dpi: int = 150,
    margins: tuple = (0, 50, 0, 50)
) -> Dict[str, any]:
    """
    Trích xuất nội dung PDF thành markdown sử dụng pymupdf4llm
    
    Args:
        pdf_file_path: Đường dẫn đến file PDF
        page_chunks: True = chia theo pages, False = toàn bộ document
        write_images: True nếu muốn extract images
        image_path: Thư mục lưu images (nếu write_images=True)
        dpi: DPI cho images
        margins: Crop margins (left, top, right, bottom)
        
    Returns:
        Dictionary chứa kết quả extraction:
            - 'success': True/False
            - 'data': List các page data hoặc None
            - 'error': Thông báo lỗi nếu có
            - 'char_count': Số ký tự được extract
    """
    logger.info(f"Bắt đầu extract PDF: {pdf_file_path}")
    
    try:
        # Extract document thành markdown
        markdown_text = pymupdf4llm.to_markdown(
            pdf_file_path,
            page_chunks=page_chunks,
            write_images=write_images,
            image_path=image_path,
            dpi=dpi,
            margins=margins
        )
        
        logger.info(f"Thành công extract {len(markdown_text):,} ký tự")
        
        # Tạo cấu trúc dữ liệu kết quả
        pdf_data = [{
            "page_number": "all" if not page_chunks else "chunks",
            "text": markdown_text,
            "source": pdf_file_path,
            "format": "markdown",
            "method": "pymupdf4llm",
            "char_count": len(markdown_text)
        }]
        
        return {
            'success': True,
            'data': pdf_data,
            'error': None,
            'char_count': len(markdown_text)
        }
        
    except Exception as e:
        error_msg = f"Lỗi khi extract PDF: {str(e)}"
        logger.error(error_msg)
        return {
            'success': False,
            'data': None,
            'error': error_msg,
            'char_count': 0
        }


def display_extraction_info(extraction_result: Dict[str, any]) -> None:
    """
    Hiển thị thông tin về kết quả extraction
    
    Args:
        extraction_result: Kết quả từ hàm extract_pdf_to_markdown
    """
    if not extraction_result['success']:
        logger.error(f"Extraction thất bại: {extraction_result['error']}")
        return
    
    data = extraction_result['data'][0]
    logger.info("Thông tin extraction:")
    logger.info(f"   Format: {data['format']}")
    logger.info(f"   Method: {data['method']}")
    logger.info(f"   Total characters: {data['char_count']:,}")


def display_text_preview(text: str, preview_length: int = 500) -> None:
    """
    Hiển thị preview của text được extract
    
    Args:
        text: Text cần preview
        preview_length: Độ dài preview (mặc định: 500 ký tự)
    """
    logger.info(f"Preview ({preview_length} ký tự đầu):")
    logger.info("=" * 70)
    preview_text = text[:preview_length]
    logger.info(preview_text)
    if len(text) > preview_length:
        logger.info("...")
    logger.info("=" * 70)


def save_markdown_to_file(pdf_data_list: List[Dict[str, any]], output_file_path: str) -> bool:
    """
    Lưu markdown data ra file
    
    Args:
        pdf_data_list: List chứa data các page
        output_file_path: Đường dẫn file output
        
    Returns:
        True nếu thành công, False nếu thất bại
    """
    logger.info(f"Lưu markdown vào file: {output_file_path}")
    
    try:
        with open(output_file_path, "w", encoding="utf-8") as output_file:
            for i, page_data in enumerate(pdf_data_list):
                # Ghi text của page
                output_file.write(page_data["text"])
                
                # Ghi separator nếu không phải page cuối
                if i < len(pdf_data_list) - 1:
                    output_file.write("\n\n---\n\n")
        
        logger.info(f"Thành công lưu file: {output_file_path}")
        return True
        
    except Exception as e:
        error_msg = f"Lỗi khi lưu file: {str(e)}"
        logger.error(error_msg)
        return False


def display_completion_summary(input_path: str, output_path: str, char_count: int) -> None:
    """
    Hiển thị tóm tắt hoàn thành quá trình extraction
    
    Args:
        input_path: Đường dẫn file input
        output_path: Đường dẫn file output  
        char_count: Số ký tự đã extract
    """
    logger.info("=" * 70)
    logger.info("✅ EXTRACTION HOÀN TẤT")
    logger.info("=" * 70)
    logger.info(f"   Input:  {input_path}")
    logger.info(f"   Output: {output_path}")
    logger.info(f"   Chars:  {char_count:,}")
    logger.info("=" * 70)


def extract_pdf_pipeline(pdf_file_path: str, output_file_path: str) -> bool:
    """
    Pipeline hoàn chỉnh để extract PDF thành markdown file
    
    Args:
        pdf_file_path: Đường dẫn đến file PDF
        output_file_path: Đường dẫn file markdown output
        
    Returns:
        True nếu thành công, False nếu thất bại
    """
    # Bước 1: Extract PDF
    extraction_result = extract_pdf_to_markdown(pdf_file_path)
    
    if not extraction_result['success']:
        logger.error("Pipeline thất bại ở bước extraction")
        return False
    
    # Bước 2: Hiển thị thông tin
    display_extraction_info(extraction_result)
    
    # Bước 3: Hiển thị preview
    pdf_data = extraction_result['data'][0]
    display_text_preview(pdf_data['text'])
    
    # Bước 4: Lưu ra file
    save_success = save_markdown_to_file(extraction_result['data'], output_file_path)
    
    if not save_success:
        logger.error("Pipeline thất bại ở bước lưu file")
        return False
    
    # Bước 5: Hiển thị tóm tắt
    display_completion_summary(
        pdf_file_path, 
        output_file_path, 
        extraction_result['char_count']
    )
    
    return True