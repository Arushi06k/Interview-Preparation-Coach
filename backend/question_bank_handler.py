
import json
import random
import logging
from pathlib import Path
from difflib import get_close_matches
from typing import List, Dict, Optional

LOG = logging.getLogger("question_bank_handler")
logging.basicConfig(level=logging.INFO)

QUESTION_BANK_PATH = Path("question_bank.json")

# In-memory question store
_question_bank: List[Dict] = []


# -------------------- Loading Utilities --------------------
def load_questions_from_file(path: Optional[Path] = None) -> None:
    """
    Load the question bank into memory. Supports:
      - top-level list of question dicts
      - dict with "questions": [...]
      - list of JSON strings
    """
    global _question_bank
    p = path or QUESTION_BANK_PATH
    try:
        with open(p, "r", encoding="utf-8") as f:
            data = json.load(f)

        # case: list of JSON strings
        if isinstance(data, list) and data and isinstance(data[0], str):
            data = [json.loads(item) for item in data]

        # case: wrapped dict
        if isinstance(data, dict) and "questions" in data:
            data = data["questions"]

        if not isinstance(data, list):
            LOG.warning("Question bank file loaded but not a list; coercing to empty list.")
            data = []

        _question_bank = data
        LOG.info("Loaded %d questions from %s", len(_question_bank), p)
    except FileNotFoundError:
        LOG.error("question_bank.json not found at %s", p)
        _question_bank = []
    except Exception as e:
        LOG.exception("Failed to load question bank: %s", e)
        _question_bank = []


# -------------------- Helper Utils --------------------
def _normalize(s: Optional[str]) -> Optional[str]:
    return s.strip().lower() if isinstance(s, str) and s.strip() else None


def available_domains() -> List[str]:
    """Return sorted unique domain names present in the bank (original case)."""
    return sorted({q.get("domain", "") for q in _question_bank if q.get("domain")})


def available_difficulties() -> List[str]:
    """Return sorted unique difficulty levels present in the bank (original case)."""
    return sorted({q.get("difficulty", "") for q in _question_bank if q.get("difficulty")})


def _filter_exact(domain: Optional[str], difficulty: Optional[str]) -> List[Dict]:
    """Exact (case-insensitive) filter on domain and/or difficulty."""
    dn = _normalize(domain)
    diffn = _normalize(difficulty)
    out: List[Dict] = []
    for q in _question_bank:
        qdom = _normalize(q.get("domain"))
        qdiff = _normalize(q.get("difficulty"))
        if dn and diffn:
            if qdom == dn and qdiff == diffn:
                out.append(q)
        elif dn:
            if qdom == dn:
                out.append(q)
        elif diffn:
            if qdiff == diffn:
                out.append(q)
        else:
            out.append(q)
    return out


def _safe_sample(qs: List[Dict], n: int) -> List[Dict]:
    """Return up to n random items from qs (non-destructive)."""
    if not qs:
        return []
    if len(qs) <= n:
        return qs.copy()
    return random.sample(qs, n)


# -------------------- Public Selection API --------------------
def select_questions(
    domain: Optional[str],
    difficulty: Optional[str],
    num_questions: int = 8,
    *,
    allow_relaxed: bool = True,
    allow_fuzzy: bool = True,
    allow_fallback: bool = True,
) -> Dict:
    """
    Robust selection strategy returning both questions and meta diagnostics.

    Returns structure:
      {
        "questions": [ {id, domain, difficulty, question, keywords, ...}, ... ],
        "meta": {
          requested_domain, requested_difficulty, matched_count,
          relaxed_used, fuzzy_suggestions, fuzzy_used, fallback_used,
          available_domains, available_difficulties
        }
      }
    """
    meta = {
        "requested_domain": domain,
        "requested_difficulty": difficulty,
        "matched_count": 0,
        "relaxed_used": False,
        "fuzzy_suggestions": [],
        "fuzzy_used": False,
        "fallback_used": False,
        "available_domains": available_domains(),
        "available_difficulties": available_difficulties(),
    }

    if not _question_bank:
        LOG.warning("Question bank empty when select_questions called.")
        return {"questions": [], "meta": meta}

    # 1) exact match
    matched = _filter_exact(domain, difficulty)
    LOG.info("Exact matched count=%d for domain=%s difficulty=%s", len(matched), domain, difficulty)

    # 2) relaxed: try domain-only if none found
    if not matched and allow_relaxed and domain:
        matched = _filter_exact(domain, None)
        meta["relaxed_used"] = bool(matched)
        LOG.info("Relaxed matched count=%d (ignored difficulty) for domain=%s", len(matched), domain)

    # 3) fuzzy domain suggestions if still nothing
    fuzzy_candidates: List[str] = []
    if not matched and allow_fuzzy and domain:
        pool = [d.lower() for d in meta["available_domains"]]
        matches = get_close_matches(domain.lower(), pool, n=3, cutoff=0.6)
        if matches:
            canonical_map = {d.lower(): d for d in meta["available_domains"]}
            fuzzy_candidates = [canonical_map[m] for m in matches if m in canonical_map]
            meta["fuzzy_suggestions"] = fuzzy_candidates
            LOG.info("Fuzzy suggestions for '%s' => %s", domain, fuzzy_candidates)

            # Try fuzzy candidates in order
            for cand in fuzzy_candidates:
                cand_matched = _filter_exact(cand, difficulty)
                if cand_matched:
                    matched = cand_matched
                    meta["fuzzy_used"] = True
                    LOG.info("Fuzzy candidate '%s' matched %d", cand, len(matched))
                    break

            # If still none, try first fuzzy candidate ignoring difficulty
            if not matched and fuzzy_candidates:
                matched = _filter_exact(fuzzy_candidates[0], None)
                meta["fuzzy_used"] = bool(matched)
                LOG.info("Fuzzy candidate (ignore difficulty) matched %d", len(matched))

    # 4) final fallback sampling
    if not matched and allow_fallback:
        meta["fallback_used"] = True
        # prefer questions with requested difficulty if available
        prefer = _filter_exact(None, difficulty) or _question_bank
        sample_pool = prefer if prefer else _question_bank
        # sample a pool, then later we'll sample the final set
        matched = _safe_sample(sample_pool, min(len(sample_pool), num_questions * 3))
        LOG.warning("No matches found for domain=%s difficulty=%s — using fallback sample size=%d", domain, difficulty, len(matched))
    
    # If questions is mistakenly inside a list, flatten it


    # finalize selection to requested size
    selected = _safe_sample(matched, num_questions) if matched else []
    
    meta["matched_count"] = len(matched)
    # Ensure selected questions are simple dicts with expected keys for frontend
    questions_out = []
    for q in selected:
        questions_out.append({
            "id": q.get("id"),
            "domain": q.get("domain"),
            "difficulty": q.get("difficulty"),
            "question": q.get("question"),
            "keywords": q.get("keywords") or q.get("keywords_list") or q.get("keywords_str") or []
        })

    return {"questions": questions_out, "meta": meta}


# -------------------- Keyword similarity (interview flow) --------------------
def similarity_score(keywords1: Optional[List[str]], keywords2: Optional[List[str]]) -> float:
    """
    Compute keyword overlap similarity in [0.0, 1.0].
    Accepts lists or comma-separated strings.
    """
    def to_list(k):
        if not k:
            return []
        if isinstance(k, str):
            return [t.strip().lower() for t in k.split(",") if t.strip()]
        if isinstance(k, (list, tuple)):
            return [str(t).strip().lower() for t in k if str(t).strip()]
        return []

    s1 = set(to_list(keywords1))
    s2 = set(to_list(keywords2))
    if not s1 or not s2:
        return 0.0
    return len(s1.intersection(s2)) / max(len(s1), len(s2))


def get_next_question(current_question: Dict, remaining_questions: List[Dict]) -> Optional[Dict]:
    """
    Pick next question from remaining_questions with highest keyword similarity
    to current_question. Falls back to None if none available.
    """
    if not current_question or not remaining_questions:
        return None

    cur_keys = current_question.get("keywords") or current_question.get("keywords_str") or ""
    best = None
    best_score = -1.0
    for q in remaining_questions:
        cand_keys = q.get("keywords") or q.get("keywords_str") or ""
        score = similarity_score(cur_keys, cand_keys)
        if score > best_score:
            best_score = score
            best = q
    return best


# -------------------- Initialize on import --------------------
try:
    load_questions_from_file()
except Exception:
    LOG.exception("Initial question bank load failed.")