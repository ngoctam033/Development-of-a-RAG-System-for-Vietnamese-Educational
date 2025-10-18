# logging_config.py (tạo mới hoặc chèn vào nơi init logger)
import sys, logging
# RAG Pipeline Package
# Exports main components for easy import

from .extraction import pdf_extractor
from .processing import chunking, table_converter
from .vectorization import embedder
from .retrieval import search
from .generation import answer_generator

# Expose commonly used functions directly
from .extraction.pdf_extractor import get_all_files_in_folder, extract_pdf_pipeline
from .processing.chunking import chunk_markdown_file, analyze_chunk_statistics
from .vectorization.embedder import vectorize_chunks_pipeline, load_vectorized_data

logger = logging.getLogger("rag_pipeline")
logger.setLevel(logging.INFO)

# 1) Ghi file UTF-8 để không lỗi tiếng Việt/emoji
fh = logging.FileHandler("rag_pipeline.log", encoding="utf-8")
fh.setLevel(logging.INFO)
fh.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
logger.addHandler(fh)

# 2) Console handler: KHÔNG in emoji, chỉ ASCII
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
ch.setFormatter(logging.Formatter("%(name)s - %(levelname)s - %(message)s"))
logger.addHandler(ch)