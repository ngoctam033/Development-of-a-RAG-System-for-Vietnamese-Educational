import re
from typing import Any, Dict, List
from rag_pipeline.llm.llm import GeminiGenerator
from rag_pipeline.retrieval.search import search_similar
from rag_pipeline.question_analysis.keyword_extractor import extract_keywords
from rag_pipeline.retrieval.vector_store import load_vector_store
from config.llm_api_config import GEMINI_API_KEY
from rag_pipeline.chat_context import context_manager
from utils.logger import logger
from config.prompt_templates import PROMPT_TEMPLATES


def answer_question(
    question: str,
    chat_context_manager: context_manager.ChatContextManager,
    generator: GeminiGenerator = None,
    vector_store: Dict[str, Any] = None,
    top_k: int = 10,
    header_path_filter=None,
    related_docs=None
) -> Dict[str, Any]:
    """
    Answer a question using the RAG pipeline (functional version)
    Args:
        question (str): User's question
        vector_store (dict): Store returned by load_vector_store
        generator (GeminiGenerator): LLM generator for answer generation
        top_k (int): Number of similar documents to retrieve
        header_path_filter: Optional filter for document headers
        related_docs: Optional list of retrieved documents
    Returns:
        dict: Result containing question, answer and sources
    """
    # If not provided, extract keywords and search similar docs
    if header_path_filter is None:
        header_path_filter = extract_keywords(question)
    # If not generator provided
    if generator is None:
        generator = GeminiGenerator(api_key=GEMINI_API_KEY)  # Placeholder, should raise error or handle properly
    if vector_store is None:
        vector_store = load_vector_store()
    if related_docs is None:
        related_docs = search_similar(question, vector_store, top_k=top_k, header_path_filter=header_path_filter)

    # Build context from retrieved documents
    context = ""
    user_chat_history = chat_context_manager.get_user_questions()
    # print("User chat history:", user_chat_history)

    sources = []
    for i, doc in enumerate(related_docs):
        context += f"Tài liệu {i+1}:\n{doc['content']}\n\n"
        source_info = {
            "header_path": doc["metadata"]["header_path"],
            "similarity_score": f"{doc['similarity_score']:.2f}"
        }
        sources.append(source_info)

    # logger.info("Đang tạo câu trả lời dựa trên ngữ cảnh thu thập được...")
    # Generate answer using LLM
    answer = generator.generate_answer(question, context, user_chat_history, prompt_template=PROMPT_TEMPLATES["planning"])

    # Return complete result
    return {
        "question": question,
        "answer": answer,
        "sources": sources
    }


# ============================================================================
# BỔ SUNG: Hàm tách STEP → rút keyword → tạo đoạn text ngắn
# Kế thừa extract_keywords() từ rag_pipeline.question_analysis.keyword_extractor
# ============================================================================


def _norm_space(s: str) -> str:
    """Chuẩn hoá khoảng trắng cho gọn."""
    return re.sub(r"\s+", " ", s.strip())

def _split_steps(plan_text: str) -> List[Dict[str, Any]]:
    """
    Tách chuỗi có định dạng STEP/BƯỚC thành các step riêng.
    Hỗ trợ các biến thể nhãn: 'STEP', 'Step', 'BƯỚC', 'BUOC'.
    Ví dụ input:
        STEP 1: ...
        STEP 2 - ...
        BƯỚC 3: ...
    Trả về: [{"index": 1, "raw": "<nội dung step 1>"}, ...]
    """
    if not isinstance(plan_text, str) or not plan_text.strip():
        return []

    pattern = re.compile(
        r"""(?imx)
        ^\s*(?:step|b[uư]ớc|buoc)\s*   # từ khóa STEP/BƯỚC
        (\d+)\s*                       # số bước
        [:\-\–]\s*                     # phân cách ':' hoặc '-'/'–'
        (.*?)                          # nội dung step (non-greedy)
        (?=^\s*(?:step|b[uư]ớc|buoc)\s*\d+\s*[:\-\–]|\Z)  # tới step tiếp theo hoặc hết chuỗi
        """,
        re.DOTALL
    )

    steps: List[Dict[str, Any]] = []
    for m in pattern.finditer(plan_text):
        idx = int(m.group(1))
        raw = _norm_space(m.group(2))
        steps.append({"index": idx, "raw": raw})

    # Nếu không match pattern, coi toàn bộ là 1 step
    if not steps:
        steps = [{"index": 1, "raw": _norm_space(plan_text)}]

    steps.sort(key=lambda x: x["index"])
    return steps

def _keywords_from_text(text: str, topn: int = 6) -> List[str]:
    """
    Dùng extract_keywords nhưng lọc sạch cho gọn:
      - bỏ markdown/ký hiệu
      - loại từ quá dài/quá ngắn
      - bỏ cụm boilerplate thường gặp trong CTĐT
      - khử trùng lặp, giữ thứ tự
    """
    MAX_LEN = 40
    MIN_LEN = 2
    BOILERPLATE = [
        "chương trình đào tạo", "chuong trinh dao tao",
        "phụ lục", "phu luc", "bảng", "bang", "chương", "chuong", "mục", "muc",
        "bộ giao thông vận tải", "bo giao thong van tai",
        "trường đh giao thông vận tải", "truong dh giao thong van tai",
        "tp. hồ chí minh", "tp ho chi minh", "chuẩn đầu ra", "chuan dau ra",
        "i. giới thiệu chương trình", "gioi thieu chuong trinh",
    ]

    try:
        kws = extract_keywords(text)
    except Exception:
        kws = []

    # -> list[str]
    if isinstance(kws, (list, tuple, set)):
        out = list(kws)
    elif isinstance(kws, dict):
        out = list(kws.get("keywords") or kws.get("terms") or [])
    elif isinstance(kws, str):
        out = [kws]
    else:
        out = []

    def clean(s: str) -> str:
        if not isinstance(s, str):
            return ""
        s = re.sub(r"\*\*|__|[_`~>|#•\[\]\(\)]", " ", s)
        s = re.sub(r"\s+", " ", s).strip()
        return s

    def is_boiler(s: str) -> bool:
        ls = s.lower()
        if sum(ch.isupper() for ch in s) >= 0.7 * max(1, len(s)):  # gần như toàn UPPER
            return True
        if any(p in ls for p in BOILERPLATE):
            return True
        if sum(ch.isdigit() for ch in s) >= 0.5 * max(1, len(s)):   # toàn số
            return True
        return False

    seen, uniq = set(), []
    for k in out:
        c = clean(k)
        if not c or len(c) > MAX_LEN or len(c) <= MIN_LEN:
            continue
        if is_boiler(c):
            continue
        lk = c.lower()
        if lk not in seen:
            uniq.append(c)
            seen.add(lk)

    return uniq[:topn]

def steps_to_keyword_texts(plan_text: str, topn_per_step: int = 6, join_with: str = ", ") -> Dict[str, Any]:
    """
    API CHÍNH (bổ sung):
      Input: chuỗi có 'STEP 1: ...', 'STEP 2: ...', ...
      Output:
        {
          "steps": [
            {"index": 1, "raw": "...", "keywords": ["...","..."], "text": "kw1, kw2"},
            ...
          ],
          "summary_text": "STEP 1 — kw1, kw2\nSTEP 2 — kwA, kwB\n..."
        }

    - "text": đoạn text ngắn cho mỗi step (nối keywords bằng join_with).
    - Nếu step không trích được keyword, fallback dùng raw rút gọn.
    - Không ảnh hưởng tới answer_question(); bạn gọi hàm này khi cần hiển thị/log các bước.
    """
    steps = _split_steps(plan_text)
    lines: List[str] = []

    for s in steps:
        kws = _keywords_from_text(s["raw"], topn=topn_per_step)
        if kws:
            short = join_with.join(kws)
        else:
            # Fallback: rút gọn raw
            raw = s["raw"]
            short = (raw[:147] + "...") if len(raw) > 150 else raw

        s["keywords"] = kws
        s["text"] = short
        lines.append(f"STEP {s['index']} — {short}")

    return {
        "steps": steps,
        "summary_text": "\n".join(lines)
    }

# step_pack["summary_text"] -> chuỗi gọn để in ra màn hình / log
# step_pack["steps"] -> danh sách {index, raw, keywords, text} nếu cần dùng chi tiết

# ====== STEP → KEYWORDS PAYLOAD (for pipeline) ===============================

def build_step_keywords_payload(plan_text: str, topn_per_step: int = 6) -> Dict[str, Any]:
    """
    Tạo payload cho pipeline từ chuỗi kế hoạch có 'STEP 1:', 'STEP 2:', ...
    Trả về cả:
      - summary_text: dùng hiển thị (human-readable)
      - steps: list các step có mảng keywords (machine-readable)
               + text ngắn gọn và query_string đề xuất
    """
    # Tận dụng hàm đã có: steps_to_keyword_texts(plan_text, ...)
    parsed = steps_to_keyword_texts(plan_text, topn_per_step=topn_per_step)

    machine_steps: List[Dict[str, Any]] = []
    for s in parsed["steps"]:
        kw_list = s.get("keywords") or []        # luôn là list[str]
        short_text = s.get("text", "")           # human-readable
        # query string đề xuất cho retrieval: ưu tiên keywords, fallback text
        query_string = " ".join(kw_list) if kw_list else short_text

        machine_steps.append({
            "index": s["index"],                 # 1, 2, 3, ...
            "text": short_text,                  # hiển thị
            "keywords": kw_list,                 # <-- mảng keywords cho pipeline
            "query_string": query_string,        # gợi ý câu query mở rộng
        })

    return {
        "summary_text": parsed["summary_text"],  # block "STEP 1 — ...\nSTEP 2 — ..."
        "steps": machine_steps                  
    }


