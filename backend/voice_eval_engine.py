"""
Voice Evaluation Engine - Phase 2 (Acoustic + NLP Delivery)
Authors: Buddy & Team
"""

import librosa
import numpy as np
import soundfile as sf
import speech_recognition as sr
from transformers import pipeline
import logging
import spacy
import textstat
from collections import Counter

# ==================== SETUP ==================== #

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("voice_eval_engine")

nlp = spacy.load("en_core_web_sm")

# -----------------------------
# Helper: Safe float conversion
# -----------------------------
def _safe_float(x):
    try:
        return float(x)
    except Exception:
        return 0.0

# =========================================================
# 1️⃣ AUDIO FEATURE EXTRACTION
# =========================================================
def extract_acoustic_features(audio_path: str):
    """Extract pitch, energy, tempo, and pause-based metrics."""
    try:
        y, sr_ = librosa.load(audio_path, sr=16000)
        duration = librosa.get_duration(y=y, sr=sr_)

        # Fundamental frequency estimation
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr_)
        pitch_values = pitches[pitches > 0]
        pitch_mean = np.mean(pitch_values) if pitch_values.size else 0
        pitch_std = np.std(pitch_values) if pitch_values.size else 0

        # Energy (loudness proxy)
        rms = np.mean(librosa.feature.rms(y=y))

        # Speech tempo estimation
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr_)

        # Detect silence portions (potential pauses)
        intervals = librosa.effects.split(y, top_db=35)
        speech_dur = sum([(end - start) / sr_ for start, end in intervals])
        pause_ratio = max(0.0, min(1.0, 1 - (speech_dur / duration)))

        return {
            "duration": round(duration, 2),
            "pitch_mean": round(_safe_float(pitch_mean), 2),
            "pitch_std": round(_safe_float(pitch_std), 2),
            "energy": round(_safe_float(rms), 3),
            "tempo": round(_safe_float(tempo), 2),
            "pause_ratio": round(pause_ratio, 3)
        }

    except Exception as e:
        logger.exception("Error extracting features: %s", e)
        return {}

# =========================================================
# 2️⃣ EMOTION DETECTION
# =========================================================
def detect_emotion(audio_path: str):
    """Classify vocal emotion using pretrained transformer (HuggingFace)."""
    try:
        emo_pipe = pipeline("audio-classification", model="superb/hubert-base-superb-er")
        result = emo_pipe(audio_path)
        top = max(result, key=lambda x: x["score"])
        return {"emotion": top["label"], "emotion_conf": round(float(top["score"]), 3)}
    except Exception as e:
        logger.warning("Emotion detection failed: %s", e)
        return {"emotion": "neutral", "emotion_conf": 0.5}

# =========================================================
# 3️⃣ SPEECH-TO-TEXT
# =========================================================
def transcribe_audio(audio_path: str):
    """Convert speech to text using SpeechRecognition."""
    r = sr.Recognizer()
    with sr.AudioFile(audio_path) as src:
        audio = r.record(src)
    try:
        text = r.recognize_google(audio)
        return text
    except Exception as e:
        logger.warning("Transcription failed: %s", e)
        return ""

# =========================================================
# 4️⃣ VOICE METRICS SCORING
# =========================================================
def compute_voice_scores(features: dict):
    """Compute tone, fluency, and stability scores."""
    if not features:
        return {"tone": 0.0, "fluency": 0.0, "stability": 0.0}

    pitch_var = min(1.0, features.get("pitch_std", 0.0) / 80)
    energy_score = min(1.0, features.get("energy", 0.0) * 8)
    tempo_score = 1.0 - min(1.0, abs(features.get("tempo", 0.0) - 120) / 120)
    pause_penalty = 1.0 - features.get("pause_ratio", 0.0)

    tone_score = round((pitch_var + energy_score + tempo_score) / 3, 3)
    fluency = round((tempo_score * 0.5 + pause_penalty * 0.5), 3)
    stability = round(1.0 - abs(tempo_score - pitch_var), 3)

    return {
        "tone": tone_score,
        "fluency": fluency,
        "stability": stability
    }

# =========================================================
# 5️⃣ NLP ENHANCEMENTS: FILLERS + REPETITIONS + TEXT FLUENCY
# =========================================================

FILLERS = [
    "uh", "um", "like", "you know", "i mean", "sort of", "kind of", 
    "basically", "actually", "literally", "so", "right"
]

def detect_fillers(text):
    words = text.lower().split()
    fillers_found = [w for w in words if w in FILLERS]
    return fillers_found, len(fillers_found)

def detect_repetitions(text, phrase_len=2):
    words = text.lower().split()
    phrases = [' '.join(words[i:i+phrase_len]) for i in range(len(words)-phrase_len+1)]
    repeats = {p: c for p, c in Counter(phrases).items() if c > 1}
    return repeats, len(repeats)

def evaluate_text_fluency(text):
    """Simple NLP-based text fluency using readability and structure."""
    try:
        readability = textstat.flesch_reading_ease(text)
        sentences = list(nlp(text).sents)
        avg_len = np.mean([len(s.text.split()) for s in sentences]) if sentences else 1
        fluency_score = max(0, min(1, (readability / 100) * (25 / avg_len)))
        return round(fluency_score, 3)
    except Exception as e:
        logger.warning("Fluency evaluation failed: %s", e)
        return 0.0

# =========================================================
# 6️⃣ MASTER VOICE + TEXT EVALUATION
# =========================================================
def evaluate_voice(audio_path: str):
    """Main entry: returns complete acoustic + NLP analysis."""
    feats = extract_acoustic_features(audio_path)
    scores = compute_voice_scores(feats)
    emo = detect_emotion(audio_path)
    transcript = transcribe_audio(audio_path)

    # ---- NLP Enhancements ---- #
    fillers, filler_count = detect_fillers(transcript)
    repetitions, repetition_count = detect_repetitions(transcript)
    text_fluency = evaluate_text_fluency(transcript)

    return {
        **feats,
        **scores,
        **emo,
        "transcript": transcript,
        "fillers": fillers,
        "repetitions": repetitions,
        "text_fluency": text_fluency,
        "filler_count": filler_count,
        "repetition_count": repetition_count
    }

# =========================================================
# 7️⃣ FEEDBACK + OVERALL SCORING
# =========================================================
def generate_voice_feedback(metrics: dict) -> dict:
    fluency = metrics.get("fluency", 0)
    stability = metrics.get("stability", 0)
    tone = metrics.get("tone", 0)
    tempo = metrics.get("tempo", 90)
    pause_ratio = metrics.get("pause_ratio", 0.3)
    emotion = metrics.get("emotion", "neutral")
    energy = metrics.get("energy", 0.004)
    text_fluency = metrics.get("text_fluency", 0)
    filler_count = metrics.get("filler_count", 0)
    repetition_count = metrics.get("repetition_count", 0)

    # Ideal ranges
    ideal_tempo = 100
    ideal_pause_ratio = 0.25

    # Normalize sub-scores
    tempo_score = max(0, 1 - abs(tempo - ideal_tempo) / ideal_tempo)
    pause_score = max(0, 1 - abs(pause_ratio - ideal_pause_ratio) / 0.5)
    energy_score = min(1, energy * 500)

    # NLP penalties
    filler_penalty = min(1, filler_count * 0.05)
    repetition_penalty = min(1, repetition_count * 0.1)

    overall_score = (
        0.2 * fluency +
        0.15 * stability +
        0.15 * tone +
        0.1 * text_fluency +
        0.1 * tempo_score +
        0.1 * pause_score +
        0.1 * energy_score -
        0.05 * filler_penalty -
        0.05 * repetition_penalty
    ) * 10

    overall_score = round(max(min(overall_score, 10.0), 0), 1)

    # Generate feedback text
    feedback = []
    if filler_count > 3:
        feedback.append("Try to avoid using fillers like 'uh' or 'um'.")
    if repetition_count > 1:
        feedback.append("You repeated certain phrases — aim for more concise answers.")
    if text_fluency < 0.5:
        feedback.append("Sentence structure could be smoother; practice coherent delivery.")
    if fluency < 0.6:
        feedback.append("Improve overall flow and rhythm.")
    if pause_ratio > 0.4:
        feedback.append("Reduce long pauses for better confidence.")
    if tone < 0.5:
        feedback.append("Add more variation in tone for engagement.")
    else:
        feedback.append("Tone and clarity were good.")
    
    feedback_text = " ".join(feedback)

    return {
        "voice_score": overall_score,
        "voice_feedback": feedback_text
    }

# =========================================================
# 🔍 LOCAL TEST
# =========================================================
if __name__ == "__main__":
    path = "sample_audio.wav"
    metrics = evaluate_voice(path)
    result = generate_voice_feedback(metrics)

    print("\nVOICE EVALUATION REPORT:")
    for k, v in metrics.items():
        print(f"{k:<15}: {v}")

    print("\nVOICE FEEDBACK SUMMARY:")
    print(f"Score: {result['voice_score']}/10")
    print(f"Feedback: {result['voice_feedback']}")
