import json
from pathlib import Path


# ============================================================
# ELIZA READER
# Delivery Planner V1
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

INTERPRETATION_FILE = Path("data/analysis/chapter_interpretation.json")
CHARACTERS_FILE = Path("data/analysis/characters.json")
OUTPUT_FILE = Path("data/planning/delivery_plan_v1.json")


# ------------------------------------------------------------
# Default delivery settings
# ------------------------------------------------------------

DEFAULT_DELIVERY = {
    "speed": 1.0,
    "pitch": 0,
    "volume": 1.0,
    "emotion": "neutral",
    "emphasis": "normal",
}


# ------------------------------------------------------------
# Segment-type defaults
# ------------------------------------------------------------

TYPE_DELIVERY = {
    "NARRATION": {
        "speed": 1.0,
        "pitch": 0,
        "volume": 1.0,
        "emotion": "neutral",
        "emphasis": "normal",
    },

    "DIALOGUE": {
        "speed": 1.0,
        "pitch": 0,
        "volume": 1.0,
        "emotion": "conversational",
        "emphasis": "normal",
    },

    "SYSTEM": {
        "speed": 0.95,
        "pitch": 0,
        "volume": 1.0,
        "emotion": "neutral",
        "emphasis": "normal",
    },
}


# ------------------------------------------------------------
# Punctuation-based delivery
# ------------------------------------------------------------

def analyze_punctuation(text):
    """
    Analyze punctuation conservatively.

    Punctuation provides delivery hints, but does not automatically
    determine strong emotion.
    """

    text = text.strip()

    result = {
        "sentence_ending": "none",
        "question": False,
        "exclamation": False,
        "ellipsis": False,
        "comma_present": False,
        "quote_present": False,
        "delivery_hint": "normal",
    }

    if not text:
        return result

    # Punctuation presence
    result["question"] = "?" in text
    result["exclamation"] = "!" in text
    result["ellipsis"] = "..." in text or "…" in text
    result["comma_present"] = "," in text

    result["quote_present"] = any(
        mark in text
        for mark in ['"', "'", "“", "”", "‘", "’"]
    )

    # --------------------------------------------------------
    # Determine actual sentence ending
    # --------------------------------------------------------

    if text.endswith(("?!", "!?")):
        result["sentence_ending"] = "question_exclamation"

    elif text.endswith("?"):
        result["sentence_ending"] = "question"

    elif text.endswith("!"):
        result["sentence_ending"] = "exclamation"

    elif text.endswith(("...", "…")):
        result["sentence_ending"] = "ellipsis"

    elif text.endswith("."):
        result["sentence_ending"] = "period"

    elif text.endswith(":"):
        result["sentence_ending"] = "colon"

    elif text.endswith(";"):
        result["sentence_ending"] = "semicolon"

    # --------------------------------------------------------
    # Conservative delivery hints
    # --------------------------------------------------------

    if result["sentence_ending"] == "question_exclamation":
        result["delivery_hint"] = "surprised_question"

    elif result["sentence_ending"] == "question":
        result["delivery_hint"] = "questioning"

    elif result["sentence_ending"] == "exclamation":
        result["delivery_hint"] = "emphasis"

    elif result["sentence_ending"] == "ellipsis":
        result["delivery_hint"] = "hesitant"

    elif result["sentence_ending"] == "colon":
        result["delivery_hint"] = "anticipation"

    elif result["sentence_ending"] == "semicolon":
        result["delivery_hint"] = "connected"

    else:
        result["delivery_hint"] = "normal"

    return result

# ------------------------------------------------------------
# Emotion inference
# ------------------------------------------------------------
def infer_emotion(segment_type, punctuation, text):
    """
    Conservative emotion inference.

    Emotion is only assigned when the text provides a reasonably
    strong delivery signal.
    """

    # System messages stay neutral.
    if segment_type == "SYSTEM":
        return "neutral"

    hint = punctuation["delivery_hint"]

    if hint == "surprised_question":
        return "surprised"

    if hint == "hesitant":
        return "hesitant"

    # A normal question is not automatically an emotion.
    # It is simply delivered with a questioning tone.
    if hint == "questioning":
        return "questioning"

    # A single ! means emphasis, not necessarily excitement.
    if hint == "emphasis":
        return (
            "conversational"
            if segment_type == "DIALOGUE"
            else "neutral"
        )

    if hint == "anticipation":
        return "anticipatory"

    return (
        "conversational"
        if segment_type == "DIALOGUE"
        else "neutral"
    )


# ------------------------------------------------------------
# Speed inference
# ------------------------------------------------------------
def infer_speed(segment_type, punctuation):

    speed = TYPE_DELIVERY.get(
        segment_type,
        DEFAULT_DELIVERY
    )["speed"]

    ending = punctuation["sentence_ending"]

    # Keep speed adjustments subtle.
    if ending == "question":
        speed *= 0.98

    elif ending == "question_exclamation":
        speed *= 0.95

    elif ending == "exclamation":
        speed *= 1.02

    elif ending == "ellipsis":
        speed *= 0.92

    return round(speed, 2)

# ------------------------------------------------------------
# Emphasis inference
# ------------------------------------------------------------

def infer_emphasis(segment_type, punctuation):

    ending = punctuation["sentence_ending"]

    if ending == "question_exclamation":
        return "strong"

    if ending == "exclamation":
        return "moderate"

    if ending == "question":
        return "moderate"

    if ending == "ellipsis":
        return "soft"

    return "normal"

# ------------------------------------------------------------
# Build delivery instruction
# ------------------------------------------------------------

def build_delivery(segment):
    segment_type = segment.get("type", "NARRATION")
    text = segment.get("text", "")

    punctuation = analyze_punctuation(text)

    base = TYPE_DELIVERY.get(
        segment_type,
        DEFAULT_DELIVERY
    )

    emotion = infer_emotion(
        segment_type,
        punctuation,
        text
    )

    speed = infer_speed(
        segment_type,
        punctuation
    )

    emphasis = infer_emphasis(
        segment_type,
        punctuation
    )

    delivery = {
        "speed": speed,
        "pitch": base["pitch"],
        "volume": base["volume"],
        "emotion": emotion,
        "emphasis": emphasis,

        "punctuation": punctuation,

        "delivery_reason": (
            f"{segment_type.lower()} delivery; "
            f"punctuation={punctuation['delivery_hint']}"
        ),
    }

    return delivery


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main():

    print("=" * 70)
    print("ELIZA READER")
    print("Delivery Planner V1")
    print("=" * 70)
    print()

    # --------------------------------------------------------
    # Load interpretation
    # --------------------------------------------------------

    if not INTERPRETATION_FILE.exists():
        raise FileNotFoundError(
            f"Missing: {INTERPRETATION_FILE}"
        )

    with open(
        INTERPRETATION_FILE,
        "r",
        encoding="utf-8"
    ) as f:
        interpretation = json.load(f)

    segments = interpretation.get("segments", [])

    print(f"Loaded {len(segments)} interpreted segments.")

    # --------------------------------------------------------
    # Load characters
    # --------------------------------------------------------

    characters = {}

    if CHARACTERS_FILE.exists():

        with open(
            CHARACTERS_FILE,
            "r",
            encoding="utf-8"
        ) as f:
            character_data = json.load(f)

        characters = character_data.get(
            "characters",
            {}
        )

    print(f"Loaded {len(characters)} characters.")
    print()

    # --------------------------------------------------------
    # Build delivery plan
    # --------------------------------------------------------

    delivery_segments = []

    counts = {
        "NARRATION": 0,
        "DIALOGUE": 0,
        "SYSTEM": 0,
        "UNKNOWN": 0,
    }

    for segment in segments:

        segment_type = segment.get(
            "type",
            "UNKNOWN"
        )

        counts[segment_type] = (
            counts.get(segment_type, 0) + 1
        )

        delivery = build_delivery(segment)

        result = {
            "segment": segment.get("segment"),
            "paragraph": segment.get("paragraph"),
            "type": segment_type,
            "text": segment.get("text", ""),

            "character": segment.get("character"),
            "character_id": segment.get("character_id"),

            "speaker": segment.get("speaker"),
            "speaker_confidence": segment.get(
                "speaker_confidence"
            ),
            "speaker_method": segment.get(
                "speaker_method"
            ),

            "narrative_focus": segment.get(
                "narrative_focus"
            ),

            "delivery": delivery,
        }

        delivery_segments.append(result)

    # --------------------------------------------------------
    # Final document
    # --------------------------------------------------------

    output = {
        "version": "delivery_v1",

        "source": {
            "interpretation": str(
                INTERPRETATION_FILE.name
            ),
            "characters": str(
                CHARACTERS_FILE.name
            ),
        },

        "rules": {
            "story_text_modified": False,
            "strong_emotion_inference": False,
            "voice_gender_inferred": False,
        },

        "statistics": {
            "total_segments": len(delivery_segments),
            "narration": counts.get("NARRATION", 0),
            "dialogue": counts.get("DIALOGUE", 0),
            "system": counts.get("SYSTEM", 0),
            "unknown": counts.get("UNKNOWN", 0),
        },

        "segments": delivery_segments,
    }

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            output,
            f,
            ensure_ascii=False,
            indent=2
        )

    # --------------------------------------------------------
    # Preview
    # --------------------------------------------------------

    print("Delivery plan created.")
    print()

    print(
        f"Narration : {counts.get('NARRATION', 0)}"
    )
    print(
        f"Dialogue  : {counts.get('DIALOGUE', 0)}"
    )
    print(
        f"System    : {counts.get('SYSTEM', 0)}"
    )
    print(
        f"Unknown   : {counts.get('UNKNOWN', 0)}"
    )

    print()
    print("-" * 70)
    print("DELIVERY PREVIEW")
    print("-" * 70)

    for segment in delivery_segments[:15]:

        d = segment["delivery"]

        print(
            f"[{segment['segment']:03d}] "
            f"{segment['type']:<10} "
            f"Speed: {d['speed']:.2f} "
            f"Emotion: {d['emotion']:<14} "
            f"Emphasis: {d['emphasis']}"
        )

    print()
    print("=" * 70)
    print("DELIVERY PLANNING COMPLETE")
    print("=" * 70)
    print()
    print(f"Output : {OUTPUT_FILE.name}")


if __name__ == "__main__":
    main()