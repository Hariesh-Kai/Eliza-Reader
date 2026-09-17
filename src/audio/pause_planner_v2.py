import json
import re
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

INPUT_FILE = BASE_DIR / "chapter_interpretation.json"
OUTPUT_FILE = BASE_DIR / "pause_plan_v2.json"


# ---------------------------------------------------------
# Pause configuration
# ---------------------------------------------------------

PAUSE = {
    "sentence_comma": 0.12,
    "sentence_semicolon": 0.18,
    "sentence_colon": 0.18,

    "sentence_period": 0.28,
    "sentence_question": 0.42,
    "sentence_exclamation": 0.38,
    "sentence_question_exclamation": 0.52,
    "sentence_ellipsis": 0.48,

    "paragraph": 0.35,

    "dialogue_start": 0.38,
    "dialogue_end": 0.32,

    "system_start": 0.55,
    "system_end": 0.50,
}


# ---------------------------------------------------------
# Text analysis
# ---------------------------------------------------------

def analyze_text(text):
    """
    Analyze the ending punctuation of a segment.
    """

    text = text.strip()

    if not text:
        return {
            "ending": "none",
            "pause_after": 0.0
        }

    # Ellipsis
    if re.search(r"\.{3}$|…$", text):
        return {
            "ending": "ellipsis",
            "pause_after": PAUSE["sentence_ellipsis"]
        }

    # Question + exclamation
    if re.search(r"[?!]{2,}$", text):
        return {
            "ending": "question_exclamation",
            "pause_after": PAUSE["sentence_question_exclamation"]
        }

    # Question
    if text.endswith("?"):
        return {
            "ending": "question",
            "pause_after": PAUSE["sentence_question"]
        }

    # Exclamation
    if text.endswith("!"):
        return {
            "ending": "exclamation",
            "pause_after": PAUSE["sentence_exclamation"]
        }

    # Colon
    if text.endswith(":"):
        return {
            "ending": "colon",
            "pause_after": PAUSE["sentence_colon"]
        }

    # Semicolon
    if text.endswith(";"):
        return {
            "ending": "semicolon",
            "pause_after": PAUSE["sentence_semicolon"]
        }

    # Comma
    if text.endswith(","):
        return {
            "ending": "comma",
            "pause_after": PAUSE["sentence_comma"]
        }

    # Normal sentence
    if text.endswith("."):
        return {
            "ending": "period",
            "pause_after": PAUSE["sentence_period"]
        }

    return {
        "ending": "none",
        "pause_after": 0.15
    }


# ---------------------------------------------------------
# Boundary pause
# ---------------------------------------------------------

def get_boundary_pause(current, previous):
    """
    Determine the pause before the current segment.

    Priority:
    1. System transitions
    2. Dialogue transitions
    3. Paragraph boundaries
    4. Previous punctuation
    """

    if previous is None:
        return 0.0

    current_type = current["type"]
    previous_type = previous["type"]

    # -----------------------------------------------------
    # SYSTEM transitions
    # -----------------------------------------------------

    if current_type == "SYSTEM" and previous_type != "SYSTEM":
        return PAUSE["system_start"]

    if previous_type == "SYSTEM" and current_type != "SYSTEM":
        return PAUSE["system_end"]

    # Consecutive system lines should stay tight.
    if current_type == "SYSTEM" and previous_type == "SYSTEM":
        return 0.10

    # -----------------------------------------------------
    # DIALOGUE transitions
    # -----------------------------------------------------

    if current_type == "DIALOGUE" and previous_type != "DIALOGUE":
        return PAUSE["dialogue_start"]

    if previous_type == "DIALOGUE" and current_type != "DIALOGUE":
        return PAUSE["dialogue_end"]

    # Consecutive dialogue segments should flow naturally.
    if current_type == "DIALOGUE" and previous_type == "DIALOGUE":
        previous_analysis = analyze_text(previous["text"])

        if previous_analysis["ending"] in {
            "question_exclamation",
            "question",
            "exclamation",
            "ellipsis"
        }:
            return previous_analysis["pause_after"]

        return 0.15

    # -----------------------------------------------------
    # Paragraph boundary
    # -----------------------------------------------------

    if current.get("paragraph") != previous.get("paragraph"):
        return PAUSE["paragraph"]

    # -----------------------------------------------------
    # Same paragraph → punctuation controls pause
    # -----------------------------------------------------

    previous_analysis = analyze_text(previous["text"])

    return previous_analysis["pause_after"]


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():

    print("=" * 70)
    print("ELIZA READER")
    print("Pause Planner V2")
    print("=" * 70)
    print()

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    segments = data["segments"]

    print(f"Loaded {len(segments)} interpreted segments.")
    print()

    pause_plan = []

    previous = None
    total_pause = 0.0

    for segment in segments:

        pause_before = get_boundary_pause(
            segment,
            previous
        )

        punctuation = analyze_text(
            segment["text"]
        )

        entry = {
            "segment": segment["segment"],
            "paragraph": segment["paragraph"],
            "type": segment["type"],
            "text": segment["text"],

            "pause_before": round(
                pause_before,
                3
            ),

            "ending": punctuation["ending"],

            "pause_after": round(
                punctuation["pause_after"],
                3
            )
        }

        pause_plan.append(entry)

        total_pause += pause_before

        print(
            f"[{segment['segment']:03d}] "
            f"{segment['type']:<10} "
            f"Before: {pause_before:.2f}s "
            f"Ending: {punctuation['ending']}"
        )

        previous = segment

    output = {
        "version": "pause_v2",
        "total_segments": len(pause_plan),
        "total_pause_before": round(total_pause, 3),
        "segments": pause_plan
    }

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            output,
            f,
            indent=2,
            ensure_ascii=False
        )

    print()
    print("=" * 70)
    print("PAUSE PLANNING COMPLETE")
    print("=" * 70)
    print(f"Segments       : {len(pause_plan)}")
    print(f"Total pause    : {total_pause:.2f}s")
    print(f"Output         : {OUTPUT_FILE.name}")
    print()


if __name__ == "__main__":
    main()