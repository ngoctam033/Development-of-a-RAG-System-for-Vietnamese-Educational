import os
import tempfile
from vision_parse import VisionParser
from src.core.base import BaseComponent
from src.database.minio_storage import MinIOStorage
from src.utils.logger import logger
from src.utils.minio_path_manager import MinIOPathManager
from src.config.configs import VISION_PARSE_CONFIG, GeminiApiKeyRotator

class Extractor(BaseComponent):
    """
    Component for extracting content from PDF files and converting to Markdown
    using the VisionParser library.
    """

    def __init__(self, name: str = "Extractor", config: dict = None):
        super().__init__(name, config or {})
        self.storage = MinIOStorage()
        self.api_key_rotator = GeminiApiKeyRotator()

    def fetch_pdf(self, bucket_name: str, filename: str, category: str = "raw") -> bytes:
        """
        Task 1: Download a PDF file from MinIO.
        """
        try:
            object_name = MinIOPathManager.get_path(category, filename)
            pdf_bytes = self.storage.download_object(bucket_name, object_name)
            
            logger.info(
                "Successfully fetched PDF file '%s/%s'. Size: %d bytes.",
                bucket_name, object_name, len(pdf_bytes)
            )
            return pdf_bytes
            
        except Exception as e:
            logger.error("Failed to fetch PDF file: %s", str(e))
            raise e

    def _get_vision_parser(self) -> VisionParser:
        """
        Helper method to initialize VisionParser based on configuration.
        """
        mode = VISION_PARSE_CONFIG.get("mode", "gemini")
        
        if mode == "gemini":
            config = VISION_PARSE_CONFIG["gemini"]
            logger.info("Initializing VisionParser in 'gemini' mode.")
            return VisionParser(
                model_name=config["model_name"],
                api_key=self.api_key_rotator.get_next_key(),
                temperature=config["temperature"],
                top_p=config["top_p"],
                image_mode="url",
                detailed_extraction=config["detailed_extraction"],
                enable_concurrency=True
            )
        elif mode == "local":
            config = VISION_PARSE_CONFIG["local"]
            logger.info("Initializing VisionParser in 'local' (Ollama) mode.")
            return VisionParser(
                model_name=config["model_name"],
                temperature=config["temperature"],
                top_p=config["top_p"],
                num_ctx=config["num_ctx"],
                image_mode="base64",
                detailed_extraction=config["detailed_extraction"],
                ollama_config=config["ollama_config"],
                enable_concurrency=True
            )
        else:
            raise ValueError(f"Unsupported VisionParse mode: {mode}")

    def convert_to_markdown(self, pdf_bytes: bytes, filename: str) -> str:
        """
        Task 2: Convert PDF content to Markdown using VisionParser.
        """
        logger.info("Starting Vision Parse extraction for file: %s", filename)
        
        # VisionParser.convert_pdf requires a file path, so we save bytes to a temp file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
            tmp_path = tmp_file.name
            tmp_file.write(pdf_bytes)
            
        try:
            parser = self._get_vision_parser()
            # convert_pdf returns a list of markdown content (one per page)
            markdown_pages = parser.convert_pdf(tmp_path)
            
            # Combine pages into a single markdown string
            full_markdown = "\n\n".join(markdown_pages)
            
            logger.info("Successfully converted PDF to Markdown using VisionParser.")
            return full_markdown
            
        except Exception as e:
            logger.error("Vision Parse conversion failed: %s", str(e))
            raise e
        finally:
            # Clean up temporary file
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def save_markdown(self, bucket_name: str, filename: str, markdown_content: str, category: str = "intermediate") -> bool:
        """
        Task 3: Save the extracted Markdown content back to MinIO.
        """
        try:
            # Change extension to .md
            md_filename = filename.rsplit('.', 1)[0] + '.md'
            object_name = MinIOPathManager.get_path(category, md_filename)
            
            success = self.storage.upload_object(
                bucket_name, 
                object_name, 
                markdown_content.encode('utf-8')
            )
            
            if success:
                logger.info("Successfully saved Markdown to '%s/%s'.", bucket_name, object_name)
            return success
            
        except Exception as e:
            logger.error("Failed to save Markdown: %s", str(e))
            return False

    def run(self):
        """Standard run method implementation."""
        logger.info("Extractor run method called.")
        pass
