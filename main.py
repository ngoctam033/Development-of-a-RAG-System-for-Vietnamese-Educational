# main.py
"""
Build pipeline:
1) (Optional) Extract PDF -> Markdown (if processed data not found)
2) (Optional) Chunk Markdown -> chunks list (if chunk files not found)
3) Build FAISS index from chunks (text + metadata)
4) Save helper files: index.faiss, index.faiss.texts.npy, index.faiss.metas.npy
"""

import os
import json
import glob
from typing import List, Dict, Any

# --- Config ---
from config.pipeline_config import (
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    FAISS_INDEX_PATH,
)
from config.models_config import EMBEDDING_MODEL

# --- FAISS store ---
from rag_pipeline.indexes.faiss_store import FaissStore

# ---- Optional: try to use project extractors/chunkers if available ----
try:
    from rag_pipeline.extraction import pdf_extractor  # your project extractor
except Exception:
    pdf_extractor = None

try:
    from rag_pipeline.processing import chunking as project_chunking  # your project chunker
except Exception:
    project_chunking = None


# ========== Utilities ==========
DATA_DIR = "data"
RAW_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
VECTOR_DIR = os.path.dirname(FAISS_INDEX_PATH)
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(VECTOR_DIR, exist_ok=True)


def log(msg: str):
    print(f"[main] {msg}")


# ========== Fallback extract & chunk ==========
def fallback_extract_pdf_to_md(pdf_path: str, md_out_path: str) -> None:
    """Very light fallback using pymupdf4llm if project extractor is not present."""
    try:
        import pymupdf4llm
    except Exception as e:
        raise RuntimeError(
            "pymupdf4llm not installed and project extractor not found. "
            "Install it or ensure rag_pipeline.extraction.pdf_extractor is available."
        ) from e

    log(f"Extracting -> {os.path.basename(md_out_path)}")
    md_text = pymupdf4llm.to_markdown(pdf_path)
    with open(md_out_path, "w", encoding="utf-8") as f:
        f.write(md_text)


def fallback_chunk_markdown(md_text: str, doc_name: str) -> List[Dict[str, Any]]:
    """Simple header-based chunker with sliding overlap on paragraphs."""
    import re
    parts = re.split(r"(^#+ .+$)", md_text, flags=re.MULTILINE)
    sections = []
    cur_head = ""
    buf = []
    for p in parts:
        if p.strip().startswith("#"):
            if buf:
                sections.append((cur_head, "\n".join(buf).strip()))
                buf = []
            cur_head = p.strip()
        else:
            buf.append(p)
    if buf:
        sections.append((cur_head, "\n".join(buf).strip()))

    chunks = []
    for head, body in sections:
        paras = [x.strip() for x in body.split("\n\n") if x.strip()]
        if not paras:
            continue
        step = max(1, max(len(paras) // 20, 1))  # coarse split
        overlap = 1
        for i in range(0, len(paras), step):
            win = paras[i : i + step + overlap]
            text = "\n\n".join(win).strip()
            if not text:
                continue
            chunks.append({
                "text": text,
                "meta": {
                    "doc_name": doc_name,
                    "header_path": head.replace("#", "").strip() if head else "",
                    "section_title": head.replace("#", "").strip() if head else "",
                }
            })
    return chunks


# ========== Load or Build Chunks ==========
def load_existing_chunks() -> List[Dict[str, Any]]:
    """
    Look for existing processed chunk JSONs.
    Accepted file patterns:
      - data/processed/*_chunks.json
      - data/processed/all_chunks*.json
    Each file should be a list of {text, meta} dicts.
    """
    paths = []
    paths.extend(glob.glob(os.path.join(PROCESSED_DIR, "*_chunks.json")))
    paths.extend(glob.glob(os.path.join(PROCESSED_DIR, "all_chunks*.json")))
    all_chunks: List[Dict[str, Any]] = []
    for p in paths:
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            for c in data:
                text = c.get("text") or c.get("content") or ""
                meta = c.get("meta") or c.get("metadata") or {}
                if text:
                    all_chunks.append({"text": text, "meta": meta})
        except Exception as e:
            log(f"Skip invalid chunk file: {p} ({e})")
    return all_chunks


def build_chunks_from_markdown() -> List[Dict[str, Any]]:
    """Use project chunker if available, else fallback; expects data/processed/*.md."""
    md_files = glob.glob(os.path.join(PROCESSED_DIR, "*.md"))
    if not md_files:
        return []

    chunks: List[Dict[str, Any]] = []
    if project_chunking and hasattr(project_chunking, "chunk_markdown_text"):
        for md in md_files:
            with open(md, "r", encoding="utf-8") as f:
                text = f.read()
            doc_name = os.path.basename(md).replace(".md", "")
            cs = project_chunking.chunk_markdown_text(
                text=text,
                chunk_size=CHUNK_SIZE,
                chunk_overlap=CHUNK_OVERLAP,
                doc_name=doc_name,
            )
            for c in cs:
                chunks.append({
                    "text": c.get("text") or c.get("content") or "",
                    "meta": c.get("meta") or c.get("metadata") or {},
                })
    else:
        for md in md_files:
            with open(md, "r", encoding="utf-8") as f:
                text = f.read()
            doc_name = os.path.basename(md).replace(".md", "")
            chunks.extend(fallback_chunk_markdown(text, doc_name))
    return chunks


def extract_pdfs_to_markdown_if_needed():
    """If no processed .md exists, try to extract from PDFs in data/raw."""
    md_files = glob.glob(os.path.join(PROCESSED_DIR, "*.md"))
    if md_files:
        return

    pdfs = []
    pdfs.extend(glob.glob(os.path.join(RAW_DIR, "*.pdf")))
    pdfs.extend(glob.glob(os.path.join(RAW_DIR, "*.PDF")))
    if not pdfs:
        log("No PDFs found in data/raw. Skipping extraction.")
        return

    log(f"Found {len(pdfs)} PDF(s). Extracting to Markdown...")
    for pdf in pdfs:
        base = os.path.splitext(os.path.basename(pdf))[0]
        md_out = os.path.join(PROCESSED_DIR, f"{base}.md")
        if os.path.exists(md_out):
            continue
        if pdf_extractor and hasattr(pdf_extractor, "pdf_to_markdown"):
            log(f"Extracting (project) -> {os.path.basename(md_out)}")
            pdf_extractor.pdf_to_markdown(pdf, md_out)
        else:
            fallback_extract_pdf_to_md(pdf, md_out)


def build_faiss_from_chunks(chunks: List[Dict[str, Any]]):
    """Build FAISS index + persist meta/texts helpers."""
    import numpy as np

    texts: List[str] = []
    metas: List[Dict[str, Any]] = []
    for c in chunks:
        t = c.get("text") or c.get("content") or ""
        if not t:
            continue
        md = c.get("meta") or c.get("metadata") or {}

        # ensure minimal metadata (điền doc_name nếu thiếu)
        doc = (
            md.get("doc_name") or md.get("file_name") or md.get("document_name")
            or md.get("source") or md.get("pdf_name") or "Tài liệu chương trình đào tạo"
        )
        md = {
            **md,
            "text": t,
            "doc_name": doc,
            "embedding_model": EMBEDDING_MODEL,
        }

        texts.append(t)
        metas.append(md)

    if not texts:
        raise RuntimeError("No chunks to index. Please ensure processed chunks exist.")

    log(f"Building FAISS (n={len(texts)}) with model: {EMBEDDING_MODEL}")
    store = FaissStore()
    store.build(texts, metas)

    # Also save helper arrays for quick loading from CLI
    np.save(FAISS_INDEX_PATH + ".texts.npy", np.array(texts, dtype=object))
    np.save(FAISS_INDEX_PATH + ".metas.npy", np.array(metas, dtype=object))

    log(f"✅ Saved: {FAISS_INDEX_PATH}")
    log(f"✅ Saved: {FAISS_INDEX_PATH}.texts.npy")
    log(f"✅ Saved: {FAISS_INDEX_PATH}.metas.npy")


# ========== Main flow ==========
def main():
    log("Start pipeline")

    # 1) Extract PDFs -> Markdown (only if needed)
    extract_pdfs_to_markdown_if_needed()

    # 2) Load or build chunks
    chunks = load_existing_chunks()
    if chunks:
        log(f"Loaded existing chunks: {len(chunks)}")
    else:
        log("No chunk JSON found. Building chunks from Markdown...")
        chunks = build_chunks_from_markdown()
        log(f"Built chunks: {len(chunks)}")
        out_json = os.path.join(PROCESSED_DIR, "all_chunks_combined.json")
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)
        log(f"Saved combined chunks -> {out_json}")

    if not chunks:
        raise RuntimeError(
            "No chunks available. Please add PDFs to data/raw or provide processed chunk JSONs."
        )

    # 3) Build FAISS index
    build_faiss_from_chunks(chunks)

    log("🎉 RAG PIPELINE HOÀN TẤT (FAISS index ready)")


if __name__ == "__main__":
    main()
