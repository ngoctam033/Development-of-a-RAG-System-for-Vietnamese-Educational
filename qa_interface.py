# qa_interface.py
# ------------------------------------------------------------
# CLI Hỏi-Đáp dùng Hybrid Retrieval (FAISS + BM25 + Reranker)
# Ưu tiên toàn bộ vấn đề về CHƯƠNG TRÌNH ĐÀO TẠO
# - Trích từ/cụm từ khóa bằng KeywordExtractor (VN/EN) cho MỌI câu hỏi giáo dục
# - Boost passage theo TRỌNG SỐ keyword/phrase (domain > n-gram > token)
# - Cắt context an toàn (MAX_CONTEXT_CHARS)
# - Hiển thị lỗi LLM rõ ràng
# - Debug bật/tắt qua SHOW_DEBUG
# ------------------------------------------------------------
import os
import sys
import numpy as np

# (tuỳ chọn) đọc .env nếu bạn muốn set API key qua file .env
try:
    from dotenv import load_dotenv  # pip install python-dotenv
    load_dotenv()
except Exception:
    pass

# Bảo đảm in Unicode ra terminal (Windows thường cần)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from config.prompt_templates import PROMPT_QA
from config.pipeline_config import FAISS_INDEX_PATH
from rag_pipeline.indexes.faiss_store import FaissStore
from rag_pipeline.retrieval.bm25_store import BM25Store
from rag_pipeline.retrieval.retriever import HybridRetriever
from rag_pipeline.generation.llm import GeminiGenerator
from rag_pipeline.retrieval.keyword_extractor import KeywordExtractor


# =========================================
# Helpers: Load corpus
# =========================================
def load_corpus_texts_and_metas(faiss_store: FaissStore):
    """
    Ưu tiên load từ .npy nếu có (nhanh và chắc chắn).
    Nếu không có, fallback lấy từ faiss_store.meta (yêu cầu lúc build đã nhét text vào meta).
    """
    texts_path_candidates = [
        FAISS_INDEX_PATH + ".texts.npy",
        FAISS_INDEX_PATH + ".text.npy",
    ]
    metas_path_candidates = [
        FAISS_INDEX_PATH + ".metas.npy",   # khuyến nghị dùng tên này khi build
        FAISS_INDEX_PATH + ".meta.npy",    # fallback cho bản cũ
    ]

    texts = None
    metas = None

    for p in texts_path_candidates:
        if os.path.exists(p):
            texts = np.load(p, allow_pickle=True).tolist()
            break

    for p in metas_path_candidates:
        if os.path.exists(p):
            metas = np.load(p, allow_pickle=True).tolist()
            break

    # Fallback: lấy từ meta đã lưu cùng index (nếu build kèm text)
    if texts is None:
        texts = []
        for m in getattr(faiss_store, "meta", []):
            if isinstance(m, dict):
                if "text" in m and isinstance(m["text"], str):
                    texts.append(m["text"])
                elif "chunk_text" in m and isinstance(m["chunk_text"], str):
                    texts.append(m["chunk_text"])
                else:
                    texts.append("")
            else:
                texts.append("")
    if metas is None:
        metas = getattr(faiss_store, "meta", [])

    return texts, metas


# =========================================
# Boosting theo KeywordExtractor
# =========================================
def _boost_score(text: str, header: str, doc: str, weight_map: dict) -> float:
    """
    Cộng điểm theo TRỌNG SỐ mỗi keyword/cụm nếu xuất hiện trong text/header/doc.
    - domain phrase (2.5) > n-gram (2.0) > token (1.0)
    - Ưu tiên text > header > doc (nhân hệ số nhỏ để phân tầng nhẹ)
    """
    s_text = (text or "").lower()
    s_head = (header or "").lower()
    s_doc  = (doc or "").lower()
    score = 0.0
    for k, w in weight_map.items():
        if k in s_text:
            score += w * 1.0
        if k in s_head:
            score += w * 0.5
        if k in s_doc:
            score += w * 0.25
    return score


def build_context(passages, corpus_texts, corpus_meta, kw_pairs):
    """
    Biến các đoạn top-k thành context + danh sách nguồn (để in ra),
    có sắp xếp ưu tiên theo keyword/phrase + trọng số từ KeywordExtractor.
    """
    weight_map = {k.lower(): float(w) for k, w in (kw_pairs or [])}

    scored = []
    for p in passages:
        idx = p["idx"]
        text = corpus_texts[idx] if 0 <= idx < len(corpus_texts) else ""
        md = corpus_meta[idx] if 0 <= idx < len(corpus_meta) else {}
        header = ""
        doc = ""
        if isinstance(md, dict):
            header = md.get("header_path") or md.get("section_title") or md.get("section") or ""
            doc = (md.get("doc_name") or md.get("file_name") or md.get("document_name") or md.get("source") or "")
        boost = _boost_score(text, header, doc, weight_map)
        scored.append((boost, p, text, header, doc))

    # Sắp xếp: boost giảm dần, rồi theo rerank_score giảm dần
    scored.sort(key=lambda x: (x[0], float(x[1].get("rerank_score", 0.0))), reverse=True)

    lines = []
    sources = []
    for _, p, text, header, doc in scored:
        lines.append(f"- ({doc or 'không rõ tài liệu'} | {header})\n{text}\n")
        sources.append({
            "doc": doc or "(không rõ tài liệu)",
            "path": header or "(không rõ mục)",
            "score": round(float(p.get("rerank_score", 0.0)), 3),
        })

    context = "\n".join(lines)
    return context, sources


# =========================================
# Gemini call wrapper
# =========================================
class GeminiRunner:
    """
    Bao lớp GeminiGenerator hiện có và linh hoạt gọi các method phổ biến:
    - generate_answer(prompt)
    - generate(prompt)
    - generate_content(prompt) (trả về .text)
    """
    def __init__(self, api_key: str):
        self.inner = GeminiGenerator(api_key)
        # để dòng debug in đúng tên model
        self.model_name = getattr(self.inner, "model_name", os.getenv("GEMINI_MODEL_NAME", "?"))

    def ask(self, prompt: str) -> str:
        # Thử các kiểu method thường gặp theo thứ tự
        if hasattr(self.inner, "generate_answer"):
            return self.inner.generate_answer(prompt)

        if hasattr(self.inner, "generate"):
            # Có dự án đặt tên là generate(...)
            return self.inner.generate(prompt)

        if hasattr(self.inner, "model"):
            # Nhiều repo trả về .model của Google Generative AI
            try:
                resp = self.inner.model.generate_content(prompt)
                if hasattr(resp, "text") and isinstance(resp.text, str):
                    return resp.text
                return str(resp)  # fallback
            except Exception as e:
                return f"[LLM error] {type(e).__name__}: {e}"

        return "[LLM error] Không tìm thấy phương thức gọi Gemini phù hợp. Hãy đảm bảo GeminiGenerator có generate_answer(prompt) hoặc generate(prompt)."


# =========================================
# Main CLI
# =========================================
def run_cli():
    # 0) Kiểm tra API key
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("⚠️  GEMINI_API_KEY/GOOGLE_API_KEY chưa được thiết lập.")
        return

    # 1) Load FAISS index
    if not os.path.exists(FAISS_INDEX_PATH):
        print(f"⚠️  Không tìm thấy FAISS index tại: {FAISS_INDEX_PATH}")
        print("👉 Hãy chạy `python main.py` để build index trước.")
        return

    faiss_store = FaissStore()
    faiss_store.load()

    # 2) Load corpus texts & metas
    corpus_texts, corpus_meta = load_corpus_texts_and_metas(faiss_store)

    # 3) BM25 + HybridRetriever
    bm25_store = BM25Store(corpus_texts)
    retriever = HybridRetriever(faiss_store, bm25_store, corpus_texts)

    # 4) LLM (Gemini)
    llm = GeminiRunner(api_key)

    # 5) CLI banner
    print("\n" + "=" * 64)
    print("🧠 HỆ THỐNG HỎI ĐÁP CHƯƠNG TRÌNH ĐÀO TẠO (Hybrid RAG)")
    print("Nhập 'exit' để thoát.")
    print("=" * 64)

    # Giới hạn context (có thể override bằng env MAX_CONTEXT_CHARS)
    try:
        max_chars = int(os.getenv("MAX_CONTEXT_CHARS", "12000"))
    except Exception:
        max_chars = 12000

    SHOW_DEBUG = os.getenv("SHOW_DEBUG", "1") == "1"
    # Khởi tạo KeywordExtractor 1 lần cho toàn phiên
    ke = KeywordExtractor()

    while True:
        try:
            question = input("\n❓ Hỏi: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nTạm biệt!")
            break

        if not question:
            continue
        if question.lower() in ("exit", "quit"):
            print("Tạm biệt!")
            break

        # 5.1) Retrieve (Hybrid + Reranker)
        try:
            top = retriever.search(question)
        except Exception as e:
            print(f"\n⚠️ Lỗi khi truy xuất: {e}")
            continue

        if not top:
            print("\nKhông tìm thấy thông tin trong tài liệu.")
            continue

        # 5.2) Trích keyword/phrase có trọng số & Build context + nguồn
        try:
            kw_pairs = ke.extract(question)  # [(keyword_or_phrase, weight)]
            context, sources = build_context(top, corpus_texts, corpus_meta, kw_pairs=kw_pairs)
        except Exception as e:
            print(f"\n⚠️ Lỗi khi dựng context: {e}")
            continue

        # Cắt bớt context an toàn cho LLM
        trimmed = False
        if len(context) > max_chars:
            context = context[:max_chars]
            trimmed = True

        # 5.3) Prompt và gọi Gemini
        prompt = PROMPT_QA.format(context=context, question=question)
        try:
            answer = llm.ask(prompt)  # có thể chứa "[LLM error]" hoặc "[LLM empty]"
        except Exception as e:
            print(f"\n⚠️ Lỗi khi gọi Gemini: {e}")
            continue

        # 5.4) In kết quả
        print("\n" + "-" * 56)
        print("📝 Câu trả lời:")
        print("-" * 56)
        if not isinstance(answer, str) or not answer.strip():
            print("[CLI] LLM trả về rỗng.")
        else:
            print(answer)
            if answer.startswith("[LLM error]"):
                print("\n👉 Gợi ý: kiểm tra tên model / version SDK hoặc đặt GEMINI_MODEL_NAME=models/gemini-2.5-flash")
            elif answer.startswith("[LLM empty]"):
                print("\n👉 Gợi ý: có thể do safety/độ dài context. Giảm MAX_CONTEXT_CHARS hoặc xem safety_settings trong llm.py")

        print("\n" + "-" * 56)
        print("🔍 Nguồn tham khảo:")
        print("-" * 56)
        for i, s in enumerate(sources, 1):
            doc = s.get("doc") or "(không rõ tài liệu)"
            path = s.get("path") or "(không rõ mục)"
            score = s.get("score")
            print(f"[{i}] {doc} | {path}  (rerank: {score})")
        print("-" * 56)

        if SHOW_DEBUG:
            print(f"[debug] passages={len(top)} | context_chars={len(context)}"
                  f" | model={getattr(llm, 'model_name', os.getenv('GEMINI_MODEL_NAME','?'))} | trimmed={trimmed}")


if __name__ == "__main__":
    run_cli()
