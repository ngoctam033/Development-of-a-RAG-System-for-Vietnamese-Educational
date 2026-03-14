import json

from src.database.minio_storage import MinIOStorage
from src.utils.logger import logger
from src.utils.minio_path_manager import MinIOPathManager


class ProcessorTasks:
    """
    Contains the task methods for the Markdown-to-JSON conversion pipeline.
    Each method corresponds to an Airflow task and uses MinIOStorage
    for interacting with MinIO object storage.
    """

    def __init__(self):
        self.storage = MinIOStorage()

    def fetch_markdown(self, bucket_name: str, filename: str, category: str = "intermediate") -> str:
        """
        Task 1: Download a Markdown file from MinIO and return its content as a string.

        Args:
            bucket_name: Name of the MinIO bucket.
            filename: Name of the file to fetch.
            category: Directory category in MinIO (default: 'intermediate').

        Returns:
            The Markdown file content as a string.
        """
        try:
            # Lấy đường dẫn chuẩn từ PathManager
            object_name = MinIOPathManager.get_path(category, filename)
            
            # Tận dụng phương thức download_object đã có trong MinIOStorage
            data_bytes = self.storage.download_object(bucket_name, object_name)
            
            # Giải mã bytes sang string
            content = data_bytes.decode('utf-8')
            
            # In log thông báo thành công kèm kích thước file
            logger.info(
                "Successfully fetched Markdown file '%s/%s'. Size: %d characters.",
                bucket_name, object_name, len(content)
            )
            return content
            
        except Exception as e:
            # In log thông báo thất bại kèm lỗi
            logger.error(
                "Failed to fetch Markdown file '%s/%s'. Error: %s",
                bucket_name, (MinIOPathManager.DIR_STRUCTURE.get(category) + filename) if MinIOPathManager.validate_category(category) else filename, str(e)
            )
            raise e

    def _extract_header_info(self, line: str) -> tuple[int, str]:
        """Extract header level and text from a Markdown line."""
        if line.startswith("#"):
            count = 0
            for char in line:
                if char == "#":
                    count += 1
                else:
                    break
            text = line[count:].strip().replace("**", "")
            return count, text
        return 0, ""

    def parse_markdown_to_dict(self, markdown_content: str, file_title: str) -> dict:
        """
        Phân tích cấu trúc phân cấp của file markdown và trả về dict dạng cây.
        
        Args:
            markdown_content: Nội dung markdown đầy đủ.
            file_title: Tên file (sử dụng làm gốc của header_path).
            
        Returns:
            Dict biểu diễn cấu trúc phân cấp các headers và nội dung.
        """
        lines = markdown_content.split('\n')
        
        # 1. Tìm title (H1 đầu tiên)
        doc_title = "Untitled"
        for line in lines:
            level, text = self._extract_header_info(line)
            if level == 1:
                doc_title = text
                break

        # 2. Xây dựng cây phân cấp
        root = {"children": [], "content": ""}
        stack = [(0, root)]
        
        for line in lines:
            level, text = self._extract_header_info(line)
            if level > 0:
                # Tạo node mới
                node = {
                    "title": text,
                    "level": level,
                    "content": "",
                    "children": [],
                    "metadata": {}
                }
                # Tìm parent phù hợp
                while stack and stack[-1][0] >= level:
                    stack.pop()
                
                if stack:
                    parent = stack[-1][1]
                    parent["children"].append(node)
                    stack.append((level, node))
            else:
                # Thêm nội dung vào node hiện tại
                if len(stack) > 1:
                    stack[-1][1]["content"] += line + '\n'
                else:
                    root["content"] += line + '\n'

        # 3. Chuyển đổi cây sang định dạng mapping section_n / section_n_m
        def build_recursive_dict(nodes, prefix="section", path_prefix=""):
            result = {}
            for i, node in enumerate(nodes, 1):
                key = f"{prefix}_{i}"
                
                # Tạo header_path bằng cách nối tên file_title và các title con
                current_title = node["title"]
                header_path = f"{path_prefix} > {current_title}" if path_prefix else current_title
                
                # Cập nhật metadata
                node["metadata"]["header_path"] = header_path
                
                section_data = {
                    "title": current_title,
                    "content": node["content"].strip(),
                    "metadata": node["metadata"]
                }
                
                if node["children"]:
                    # Sử dụng key hiện tại làm prefix và header_path hiện tại làm path_prefix cho con
                    children_dict = build_recursive_dict(node["children"], key, header_path)
                    section_data.update(children_dict)
                
                result[key] = section_data
            return result

        # Khởi tạo build_recursive_dict với file_title làm path_prefix gốc
        sections_dict = build_recursive_dict(root["children"], path_prefix=file_title)

        return {
            "title": doc_title,
            "content": sections_dict
        }

    def flatten_hierarchical_dict(self, nested_dict: dict) -> list[dict]:
        """
        Chuyển đổi cấu trúc dict lồng nhau thành list các dict phẳng (flat list).
        
        Args:
            nested_dict: Dict có cấu trúc cây (field 'content' từ parse_markdown_to_dict).
            
        Returns:
            List các dictionary riêng lẻ cho từng section.
        """
        flat_list = []

        def recurse(current_dict):
            # Lọc ra các key là section (ví dụ section_1, section_1_1)
            # Dựa trên quy tắc đặt tên ở Task 12: prefix_i
            for key, value in current_dict.items():
                if key.startswith("section"):
                    # Tạo bản sao của section data (excluding nested sections)
                    section_item = {
                        "id": key,
                        "title": value.get("title"),
                        "content": value.get("content"),
                        "metadata": value.get("metadata")
                    }
                    flat_list.append(section_item)
                    
                    # Tiếp tục đệ quy vào chính value này để tìm các sub-section lồng bên trong
                    recurse(value)

        recurse(nested_dict)
        return flat_list

    def convert_to_json(self, markdown_content: str, file_title: str) -> str:
        """
        Task 2: Parse Markdown content, flatten it into a list of sections,
        and return it as a formatted JSON string.

        Args:
            markdown_content: Raw Markdown string to be converted.
            file_title: Tên file để đưa vào header_path.

        Returns:
            A pretty-printed JSON string containing a list of section dictionaries.
        """
        # 1. Parse sang cấu trúc cây
        hierarchical_dict = self.parse_markdown_to_dict(markdown_content, file_title)
        
        # 2. Flatten cấu trúc cây trong field 'content' thành list
        flattened_list = self.flatten_hierarchical_dict(hierarchical_dict["content"])
        
        # 3. Thêm dấu tab (indent=4) và xuống dòng để dễ nhìn kết quả
        formatted_json = json.dumps(flattened_list, indent=4, ensure_ascii=False)
        
        logger.info("Successfully converted Markdown to flat list of sections and formatted as JSON.")
        return formatted_json

    def save_json(self, bucket_name: str, filename: str, data, category: str = "processed") -> bool:
        """
        Task 3: Serialize a dictionary to JSON and upload it to MinIO.

        Args:
            bucket_name: Name of the MinIO bucket.
            filename: Name of the file to save (e.g., 'sample.json').
            data: Dictionary or JSON string to be uploaded.
            category: Directory category in MinIO (default: 'processed').

        Returns:
            True if the upload was successful.
        """
        try:
            # Lấy đường dẫn chuẩn từ PathManager
            object_name = MinIOPathManager.get_path(category, filename)
            
            # Nếu data là dict, chuyển sang json string trước
            if isinstance(data, dict):
                content = json.dumps(data, indent=4, ensure_ascii=False)
            else:
                content = str(data)
                
            # Chuyển string sang bytes để upload
            content_bytes = content.encode('utf-8')
            
            # Tận dụng MinIOStorage để upload
            success = self.storage.upload_object(bucket_name, object_name, content_bytes)
            
            if success:
                logger.info("Successfully saved JSON to '%s/%s'.", bucket_name, object_name)
            return success
            
        except Exception as e:
            logger.error("Failed to save JSON to '%s'. Error: %s", filename, str(e))
            return False