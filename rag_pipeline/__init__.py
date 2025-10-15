# RAG Pipeline Package
# Exports main components for easy import

from .extraction import pdf_extractor
from .processing import chunking, table_converter
from .vectorization import embedder
from .retrieval import search
from .generation import answer_generator

# Expose commonly used functions directly
from .extraction.pdf_extractor import get_all_files_in_folder
from .processing.chunking import chunk_text
from .vectorization.embedder import embed_documents
from .retrieval.search import search_documents
from .generation.answer_generator import generate_answer