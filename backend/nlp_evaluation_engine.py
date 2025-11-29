"""
NLP Evaluation Engine - Phase 2 (Content + Delivery)
Improved: gibberish detection + safer semantic scoring
"""

from typing import List, Dict, Tuple
import logging
from functools import lru_cache
import re
# Minimum number of words for scoring content
MIN_WORDS_FOR_SCORE = 8

# Delay heavy imports until init
semantic_model = None
nlp = None
_util = None
_models_initialized = False

# Setup module logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nlp_eval_engine")

# -----------------------------
# Lazy model initialization
# -----------------------------
def init_models(force: bool = False):
    """
    Initialize heavy NLP models. Safe to call multiple times.
    Call this from FastAPI startup or before the first evaluation.
    """
    global semantic_model, nlp, _util, _models_initialized
    if _models_initialized and not force:
        return

    try:
        # Local imports to avoid import-time failures
        from sentence_transformers import SentenceTransformer, util
        import spacy

        logger.info("Loading SentenceTransformer model (compact)...")
        # compact paraphrase model — fast and good for semantic similarity
        semantic_model = SentenceTransformer("paraphrase-MiniLM-L6-v2")
        _util = util

        logger.info("Loading spaCy model en_core_web_sm...")
        nlp = spacy.load("en_core_web_sm")

        _models_initialized = True
        logger.info("NLP models initialized successfully.")
    except Exception as e:
        logger.exception("Failed to initialize NLP models: %s", e)
        # Re-raise so caller (startup) can decide to fail fast
        raise

def _ensure_models():
    if not _models_initialized:
        init_models()

# -----------------------------
# Utility / Helpers
# -----------------------------
def _safe_float(x: float) -> float:
    try:
        return float(x)
    except Exception:
        return 0.0

def _map_cosine_to_01(cos_val: float) -> float:
    v = (cos_val + 1.0) / 2.0
    v = max(0.0, min(1.0, v))
    return round(v, 3)

# -----------------------------
# Gibberish guard
# -----------------------------
def is_gibberish(text: str) -> bool:
    if not text or not isinstance(text, str):
        return True

    s = text.strip()

    # TOO SHORT
    if len(s) < 5:
        return True

    # WORD COUNT
    words = re.findall(r"[a-zA-Z]{3,}", s)
    if len(words) < 3:
        return True

    # REPEATED CHARACTERS (aaaaffffjjj)
    if re.search(r"(.)\1{3,}", s.lower()):
        return True

    # HIGH NON-LETTER RATIO
    letters = re.findall(r"[a-zA-Z]", s)
    ratio = len(letters) / max(1, len(s))
    if ratio < 0.35:
        return True

    return False

# -----------------------------
# PhraseMatcher cache / builder
# -----------------------------
@lru_cache(maxsize=1024)
def _build_phrase_matcher_cached(keywords_tuple: Tuple[str, ...]):
    """
    Build and cache a PhraseMatcher for a tuple of keywords.
    Must be called only after models are initialized.
    """
    # Ensure models are loaded
    _ensure_models()
    from spacy.matcher import PhraseMatcher  # local import

    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    patterns = [nlp.make_doc(k) for k in keywords_tuple if k]
    if patterns:
        matcher.add("KEYWORDS", patterns)
    return matcher

def _normalize_keywords(keywords: List[str]) -> Tuple[str, ...]:
    return tuple(sorted({k.strip().lower() for k in (keywords or []) if isinstance(k, str) and k.strip()}))

# -----------------------------
# Keyword matching score
# -----------------------------
def keyword_match_score(user_answer: str, target_keywords: List[str]) -> float:
     # ---------- Strong Full-Word Keyword Match ----------
    if not target_keywords:
        return 1.0

    # Clean text
    clean_answer = re.sub(r'[^a-zA-Z0-9\s]', ' ', (user_answer or "").lower()).strip()
    answer_words = clean_answer.split()

    # Very short answers → no keyword score
    if len(answer_words) < 3:
        return 0.0

    # Normalize expected keywords
    keywords = [k.lower().strip() for k in target_keywords if isinstance(k, str)]

    # Ignore 1–3 letter keywords that cause false matches
    keywords = [k for k in keywords if len(k) >= 4]

    if not keywords:
        return 0.0

    matched = 0
    for k in keywords:
        # FULL WORD MATCH ONLY → prevents random matching
        if re.search(rf"\b{k}\b", clean_answer):
            matched += 1

    score = matched / len(keywords)
    return round(score, 3)


# -----------------------------
# Semantic similarity
# -----------------------------
def semantic_similarity_score(user_answer: str, benchmark_answer: str) -> float:
    """
    Compute embedding cosine similarity and map to [0,1].
    Returns float in [0,1].
    """

    # 1️⃣ Reject very short answers early (less than 8 words)
    if not user_answer or len(user_answer.split()) < MIN_WORDS_FOR_SCORE:
        return 0.0

    # 2️⃣ Reject gibberish
    if is_gibberish(user_answer):
        return 0.0

    # 3️⃣ Reject empty benchmark
    if not benchmark_answer or not benchmark_answer.strip():
        return 0.0

    # 4️⃣ Compute semantic similarity safely
    _ensure_models()
    try:
        emb = semantic_model.encode([user_answer, benchmark_answer], convert_to_tensor=True, show_progress_bar=False)
        cos = _util.cos_sim(emb[0], emb[1]).item()
        return _map_cosine_to_01(cos)
    except Exception as e:
        logger.exception("Semantic similarity computation failed: %s", e)
        return 0.0

# -----------------------------
# Delivery analysis
# -----------------------------
import textstat  # safe to import at module scope; lightweight compared to models

def analyze_delivery(user_answer: str) -> Dict[str, float]:
    """
    Returns clarity, conciseness, confidence in 0..1
    """
    if not (user_answer and user_answer.strip()):
        return {"clarity": 0.0, "conciseness": 0.0, "confidence": 0.0}

    try:
        fk = _safe_float(textstat.flesch_kincaid_grade(user_answer))
        fog = _safe_float(textstat.gunning_fog(user_answer))
        clarity = 1.0 - min((fk + fog) / 30.0, 1.0)
        clarity = round(max(0.0, min(1.0, clarity)), 3)
    except Exception:
        clarity = 0.5

    words = len(user_answer.split())
    avg_sent_len = _safe_float(textstat.avg_sentence_length(user_answer) or 0.0)
    length_score = 1.0 - min(1.0, max(0.0, (words - 40) / 200.0))
    sentence_score = 1.0 - min(1.0, max(0.0, (avg_sent_len - 18) / 30.0))
    conciseness = round(max(0.0, min(1.0, 0.6 * length_score + 0.4 * sentence_score)), 3)

    lower = user_answer.lower()
    hedge_words = ["maybe", "perhaps", "i think", "i feel", "sort of", "kind of", "probably", "might", "could"]
    assertive_words = ["i led", "i implemented", "i designed", "i developed", "we built", "ensured", "delivered", "achieved", "confident"]
    hedges = sum(lower.count(h) for h in hedge_words)
    asserts = sum(lower.count(a) for a in assertive_words)
    confidence = (asserts + 0.5) / (hedges + asserts + 1.0)
    confidence = round(max(0.0, min(1.0, confidence)), 3)

    return {"clarity": clarity, "conciseness": conciseness, "confidence": confidence}

# Minimum number of words for scoring content
MIN_WORDS_FOR_SCORE = 8
def is_meaningless_strict(answer: str) -> bool:
    """
    Returns True for:
    - Single letters/numbers
    - Short sequences (like 'd', '2', '8i', 's', 'x')
    - Mostly gibberish
    """
    if not answer or not answer.strip():
        return True

    answer = answer.strip()

    # 1️⃣ Reject very short answers by word count
    words = answer.split()
    if len(words) < 2:   # even 1 word → zero
        return True

    # 2️⃣ Reject single letters or digits
    if all(re.fullmatch(r'[a-zA-Z0-9]{1,2}', w) for w in words):
        return True

    # 3️⃣ Reject answers that are only numbers or symbols
    if re.fullmatch(r'[\d\W]+', answer):
        return True

    # 4️⃣ Reject mostly random short words
    short_alpha_words = [w for w in words if re.fullmatch(r'[a-zA-Z]{1,4}', w)]
    if len(short_alpha_words) == len(words):
        return True

    # 5️⃣ Use existing gibberish function
    if is_gibberish(answer):
        return True

    return False

# -----------------------------
# Unified evaluation
# -----------------------------
def evaluate_answer(
    user_answer: str,
    benchmark_answer: str,
    question_keywords: List[str] = None,
    weights: Dict[str, float] = None
) -> Dict:

    # --------------------------------------------------
    # 0. HARD REJECT: meaningless, one-word, low-effort
    # --------------------------------------------------
    if is_meaningless_strict(user_answer):
        return {
            "semantic_score": 0.0,
            "keyword_score": 0.0,
            "content_score": 0.0,
            "clarity": 0.0,
            "conciseness": 0.0,
            "confidence": 0.0,
            "coherence": 0.0,
            "structure_score": 0.0,
            "final_score": 0.0,
            "feedback": (
                "Answer is too short or lacks meaningful content. "
                "Write 2–4 complete sentences explaining the concept clearly."
            )
        }

    # --------------------------------------------------
    # 1. Default weights (balanced for technical Q&A)
    # --------------------------------------------------
    W = {
        "semantic": 0.45,
        "keyword": 0.30,
        "structure": 0.10,
        "coherence": 0.10,
        "delivery": 0.05
    }

    if weights:
        W.update(weights)

    # --------------------------------------------------
    # 2. Semantic similarity (0–1)
    # --------------------------------------------------
    semantic = semantic_similarity_score(user_answer, benchmark_answer)

    # --------------------------------------------------
    # 3. Keyword coverage score (0–1)
    # --------------------------------------------------
    keyword = keyword_match_score(user_answer, question_keywords or [])

    # --------------------------------------------------
    # 4. Structural score (Definition → Explanation → Example)
    # --------------------------------------------------
    structure_score = 0.0
    ua_lower = user_answer.lower()

    if any(w in ua_lower for w in ["is defined as", "refers to", "means"]):
        structure_score += 0.33
    if any(w in ua_lower for w in ["for example", "for instance", "e.g"]):
        structure_score += 0.33
    if len(user_answer.split()) > 25:
        structure_score += 0.34

    structure_score = min(1.0, round(structure_score, 3))

    # --------------------------------------------------
    # 5. Coherence Score (logical flow)
    # --------------------------------------------------
    coherence = 0.0
    try:
        doc = nlp(user_answer)
        if len(list(doc.sents)) >= 2:
            coherence = 1.0 if doc.has_annotation("SENT_START") else 0.7
    except:
        coherence = 0.5

    coherence = round(coherence, 3)

    # --------------------------------------------------
    # 6. Delivery scoring (clarity, conciseness, confidence)
    # --------------------------------------------------
    delivery = analyze_delivery(user_answer)

    # Combine
    delivery_score = round(
        0.5 * delivery["clarity"] +
        0.3 * delivery["conciseness"] +
        0.2 * delivery["confidence"],
        3
    )

    # --------------------------------------------------
    # 7. Final content score (0–1)
    # --------------------------------------------------
    content = (
        W["semantic"] * semantic +
        W["keyword"] * keyword +
        W["structure"] * structure_score +
        W["coherence"] * coherence
    )

    content = round(content, 3)

    # --------------------------------------------------
    # 8. Final combined score (0–1)
    # --------------------------------------------------
    overall_raw = content * (1 - W["delivery"]) + delivery_score * W["delivery"]

    # NORMALIZE so score NEVER exceeds 1.0
    final = max(0.0, min(overall_raw, 1.0))

    # --------------------------------------------------
    # 9. Generate human-readable feedback
    # --------------------------------------------------
    fb = []

    # Semantic feedback
    if semantic < 0.35:
        fb.append("Your answer does not align well with the expected concept.")
    elif semantic < 0.6:
        fb.append("Your explanation is partially correct but misses core ideas.")

    # Keyword feedback
    if keyword < 0.4:
        fb.append("Try including more domain-specific terms.")

    # Structure feedback
    if structure_score < 0.5:
        fb.append("Improve structure: define → explain → give example.")

    # Coherence feedback
    if coherence < 0.5:
        fb.append("Improve logical flow between sentences.")

    # Delivery feedback
    if delivery["clarity"] < 0.5:
        fb.append("Simplify language and remove long/complex sentences.")
    if delivery["confidence"] < 0.4:
        fb.append("Use more assertive phrasing (e.g., 'I built', 'I used', 'This method works by').")

    if not fb:
        fb.append("Strong, clear, and well-structured answer.")

    final_feedback = " ".join(fb)

    # --------------------------------------------------
    # 10. Final output
    # --------------------------------------------------
    return {
        "semantic_score": semantic,
        "keyword_score": keyword,
        "structure_score": structure_score,
        "coherence": coherence,
        "clarity": delivery["clarity"],
        "conciseness": delivery["conciseness"],
        "confidence": delivery["confidence"],
        "delivery_score": delivery_score,
        "content_score": content,
        "final_score": round(final, 3),
        "feedback": final_feedback
    }


# -----------------------------
# Example usage (for quick local test)
# -----------------------------
if __name__ == "__main__":
    # Ensure models are initialized before testing
    init_models()
    ua = "I implemented a REST API using Flask. I designed endpoints, added validation, and used PostgreSQL for persistence. We deployed via Docker and CI/CD."
    ba = "Build a REST API: design endpoints, validation, database (Postgres), containerize with Docker, and deploy with CI/CD pipelines."
    kw = ["REST API", "Flask", "PostgreSQL", "Docker", "CI/CD", "endpoints", "validation"]

    tests = [
        ("ssjk", ba, kw),
        ("load balancing distributes traffic across servers","Load balancing distributes incoming network traffic across multiple servers for reliability and efficiency.",
         ["load balancing", "traffic", "servers", "efficiency"]),
        (ua, ba, kw)
    ]

    for user_text, benchmark, kwords in tests:
        res = evaluate_answer(user_text, benchmark, question_keywords=kwords)
        print("INPUT:", user_text)
        print(res)
        print("-" * 60)

# --------------------------------------------------------
# Bias-Free Multi-Answer Evaluation (Order-Independent)
# --------------------------------------------------------
import random

def evaluate_answers_bias_free(
    answers: List[str],
    benchmark_answer: str,
    question_keywords: List[str]
):
    """
    Removes ordering bias:
    1. Shuffle answers randomly.
    2. Evaluate each with your existing evaluate_answer().
    3. Restore original order.
    4. Return scores in original order.
    """

    # 1. copy original list
    original_order = answers[:]

    # 2. shuffle for unbiased scoring
    shuffled = answers[:]
    random.shuffle(shuffled)

    # 3. evaluate all shuffled answers
    temp_results = {}
    for ans in shuffled:
        temp_results[ans] = evaluate_answer(
            user_answer=ans,
            benchmark_answer=benchmark_answer,
            question_keywords=question_keywords
        )

    # 4. restore original order
    final_scores = [temp_results[a] for a in original_order]

    return final_scores
