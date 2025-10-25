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
from .question_analysis.keyword_extractor import extract_keywords
from .retrieval.vector_store import load_vector_store
from .retrieval.search import search_similar
from .generation.answer_generator import answer_question