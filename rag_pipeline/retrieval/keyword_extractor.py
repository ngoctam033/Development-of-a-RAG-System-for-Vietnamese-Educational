# retrieval/keyword_extractor.py
import re
from typing import List, Tuple, Iterable, Dict

class KeywordExtractor:
    """
    Trích xuất từ/cụm từ khóa cho domain Giáo dục/Chương trình đào tạo.
    - Tổng quát cho mọi câu hỏi giáo dục (CTĐT, CĐR, tín chỉ, tiên quyết, mô tả học phần, thời lượng, phân bổ, đối sánh…).
    - Chuẩn hóa: lower + loại ký tự thừa.
    - Chuẩn hóa từ vựng qua SYNONYMS (VN/EN -> dạng chuẩn).
    - Nhận diện cụm từ domain (n-grams) + từ đơn.
    - Trả về [(keyword_or_phrase, weight)], weight ∈ {2.5 (domain phrase), 2.0 (n-gram ý nghĩa), 1.0 (token đơn)}.
    - Có thể mở rộng bằng tham số extra_domain_phrases / extra_synonyms khi khởi tạo.
    """

    # Stopwords tổng quát (giáo dục)
    VI_STOPWORDS = {
        "và","hoặc","của","trong","với","là","có","không","những","các","được","cho","về",
        "đến","tại","nào","gì","bao","nhiêu","môn","học","ngành","khoa","bộ","môn","hệ",
        "trình","độ","chi","tiết","mục","tiêu","chuẩn","đầu","ra","kiến","thức","khoa","học",
        "tự","nhiên","tín","chỉ","bắt","buộc","tự","chọn","phần","iii","ii","i","năm","học",
        "học","kỳ","yêu","cầu","thời","gian","liên","hệ","đại","học","cao","đẳng","đào","tạo"
    }
    EN_STOPWORDS = {
        "the","and","or","of","in","for","to","is","are","a","an","on","with","about","how",
        "what","which","does","do","have","has","credit","course","subject","module","program",
        "curriculum","learning","outcomes","knowledge","science","natural","compulsory","elective",
        "section","part","year","semester","requirement","time","hours"
    }

    # Cụm từ domain “xuyên suốt” mọi câu hỏi giáo dục (có thể mở rộng)
    DEFAULT_DOMAIN_PHRASES = [
        # khung/chương trình
        "chương trình đào tạo", "khung chương trình", "kế hoạch đào tạo",
        "ma trận học phần", "sơ đồ khối kiến thức",
        # học phần/mô tả/tiên quyết
        "mô tả học phần", "học phần tiên quyết", "học phần tương đương", "học phần tự chọn",
        # chuẩn đầu ra/đối sánh/đánh giá
        "chuẩn đầu ra", "đối sánh chương trình", "bảng đối sánh", "chuẩn đầu ra học phần",
        # khối kiến thức/số tín chỉ
        "khối kiến thức", "số tín chỉ", "khối lượng tín chỉ", "phân bổ tín chỉ",
        # tổ chức giảng dạy/đánh giá
        "hình thức đánh giá", "phương pháp giảng dạy",
    ]

    # Đồng bộ từ vựng (VN/EN) về dạng chuẩn: áp dụng “toàn từ”
    DEFAULT_SYNONYMS = {
        # chương trình
        "ctdt": "chương trình đào tạo",
        "ct đt": "chương trình đào tạo",
        "chuong trinh dao tao": "chương trình đào tạo",
        "curriculum": "chương trình đào tạo",
        "program": "chương trình đào tạo",

        # chuẩn đầu ra
        "cdr": "chuẩn đầu ra",
        "learning outcomes": "chuẩn đầu ra",
        "outcomes": "chuẩn đầu ra",

        # học phần
        "course description": "mô tả học phần",
        "module description": "mô tả học phần",
        "prerequisite": "học phần tiên quyết",
        "prerequisites": "học phần tiên quyết",
        "equivalent": "học phần tương đương",
        "elective": "học phần tự chọn",

        # tín chỉ
        "credits": "số tín chỉ",
        "credit": "số tín chỉ",

        # khối kiến thức
        "knowledge block": "khối kiến thức",
        "knowledge blocks": "khối kiến thức",

        # một số môn hay gặp (mẫu; có thể mở rộng)
        "linear algebra": "đại số",   # ví dụ chuẩn hóa về “đại số”
        "probability": "xác suất",
        "statistics": "thống kê",
    }

    def __init__(
        self,
        extra_domain_phrases: Iterable[str] = (),
        extra_synonyms: Dict[str, str] = None,
        include_default_domain_phrase: bool = True,
        always_include_ctdt_phrase: bool = True,
        ngram_max: int = 3,
    ):
        """
        - extra_domain_phrases: thêm cụm domain riêng của trường/khoa (ví dụ: "chuẩn đầu ra cơ sở", "ma trận PLO-CLO")
        - extra_synonyms: bổ sung synonym/alias (dict)
        - include_default_domain_phrase: có dùng bộ DEFAULT_DOMAIN_PHRASES không
        - always_include_ctdt_phrase: luôn đưa "chương trình đào tạo" vào kết quả (weight 2.5)
        - ngram_max: tối đa n-gram sinh (2 hoặc 3 là hợp lý)
        """
        self.include_default_domain_phrase = include_default_domain_phrase
        self.always_include_ctdt_phrase = always_include_ctdt_phrase
        self.ngram_max = max(2, min(int(ngram_max), 5))

        self.domain_phrases = set()
        if include_default_domain_phrase:
            self.domain_phrases.update(self.DEFAULT_DOMAIN_PHRASES)
        if extra_domain_phrases:
            self.domain_phrases.update(extra_domain_phrases)

        self.synonyms = dict(self.DEFAULT_SYNONYMS)
        if extra_synonyms:
            self.synonyms.update(extra_synonyms)

    @staticmethod
    def _normalize(text: str) -> str:
        text = (text or "").lower()
        text = re.sub(r"[^a-z0-9à-ỹ\s&]+", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _apply_synonyms(self, s: str) -> str:
        out = s
        # thay thế dạng toàn từ; sắp xếp key theo độ dài giảm dần để tránh “ăn” lẫn
        for k in sorted(self.synonyms.keys(), key=len, reverse=True):
            v = self.synonyms[k]
            out = re.sub(rf"\b{re.escape(k)}\b", v, out)
        return out

    def _tokenize(self, s: str) -> List[str]:
        toks = s.split()
        # lọc stopwords VN/EN
        toks = [t for t in toks if t not in self.VI_STOPWORDS and t not in self.EN_STOPWORDS]
        return toks

    def _gen_ngrams(self, toks: List[str]) -> List[str]:
        ngrams = []
        for n in range(2, self.ngram_max + 1):
            for i in range(len(toks) - n + 1):
                ng = " ".join(toks[i:i+n])
                # bỏ n-grams quá ngắn về mặt ký tự
                if len(ng) >= 4:
                    ngrams.append(ng)
        return ngrams

    def extract(self, question: str) -> List[Tuple[str, float]]:
        """
        Trả về list [(keyword_or_phrase, weight)], tổng quát cho mọi câu hỏi giáo dục.
        Quy tắc trọng số:
          - 2.5: domain phrase (có trong domain_phrases) xuất hiện trong câu
          - 2.0: n-gram sinh ra từ câu (2–3 từ) có ý nghĩa
          - 1.0: token đơn lẻ
        Ngoài ra, nếu bật always_include_ctdt_phrase và chưa có, thêm "chương trình đào tạo" (2.5).
        """
        q = self._normalize(question)
        q = self._apply_synonyms(q)

        # 1) domain phrases xuất hiện trong câu
        domain_hits = []
        for ph in self.domain_phrases:
            phn = self._normalize(ph)
            if phn and phn in q:
                domain_hits.append(phn)

        # 2) n-grams và tokens
        toks = self._tokenize(q)
        ngrams = self._gen_ngrams(toks)

        results: List[Tuple[str, float]] = []
        seen = set()

        # domain phrases (2.5)
        for ph in domain_hits:
            if ph not in seen:
                results.append((ph, 2.5))
                seen.add(ph)

        # meaningful n-grams (2.0)
        for ng in ngrams:
            if ng not in seen:
                results.append((ng, 2.0))
                seen.add(ng)

        # tokens (1.0)
        for tk in toks:
            if len(tk) >= 2 and tk not in seen:
                results.append((tk, 1.0))
                seen.add(tk)

        # luôn thêm “chương trình đào tạo” nếu muốn
        if self.always_include_ctdt_phrase and "chương trình đào tạo" not in seen:
            results.insert(0, ("chương trình đào tạo", 2.5))
            seen.add("chương trình đào tạo")

        return results
