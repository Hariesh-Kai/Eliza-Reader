
import json
import re
from pathlib import Path
from typing import Dict, List


INPUT_FILE = "analyzed_story_v3.txt"
CHARACTER_FILE = "characters.json"
OUTPUT_FILE = "character_context_v2.json"


# ============================================================
# CHARACTER MEMORY
# ============================================================

def load_characters() -> Dict:
    """
    Load known characters from characters.json.

    Expected structure:

    {
        "characters": {
            "pei_qian": {
                "name": "Pei Qian",
                ...
            }
        }
    }
    """

    path = Path(CHARACTER_FILE)

    if not path.exists():
        raise FileNotFoundError(
            f"Could not find {CHARACTER_FILE}"
        )

    with open(
        path,
        "r",
        encoding="utf-8"
    ) as f:
        data = json.load(f)

    return data.get(
        "characters",
        {}
    )


# ============================================================
# STORY LOADER
# ============================================================

def load_story() -> List[Dict]:
    """
    Read analyzed_story_v3.txt.

    Supports:

        SEGMENT [001]
        PARAGRAPH [001]
        [NARRATION]

        Story text

    and:

        SEGMENT [002]
        PARAGRAPH [002]
        [DIALOGUE]

        Dialogue text
    """

    path = Path(INPUT_FILE)

    if not path.exists():
        raise FileNotFoundError(
            f"Could not find {INPUT_FILE}"
        )

    lines = path.read_text(
        encoding="utf-8"
    ).splitlines()

    segments = []

    current_segment = None
    current_paragraph = None
    current_type = None
    current_text = []

    def flush_segment():

        nonlocal current_text

        if (
            current_segment is not None
            and current_paragraph is not None
            and current_type is not None
            and current_text
        ):

            text = " ".join(
                line.strip()
                for line in current_text
                if line.strip()
            )

            if text:

                segments.append({
                    "segment_index": current_segment - 1,
                    "segment_number": current_segment,
                    "paragraph": current_paragraph,
                    "type": current_type,
                    "text": text,
                })

        current_text = []

    for line in lines:

        line = line.strip()

        if not line:
            continue

        # ----------------------------------------------------
        # SEGMENT
        # ----------------------------------------------------

        match = re.fullmatch(
            r"SEGMENT\s+\[(\d+)\]",
            line,
            flags=re.IGNORECASE
        )

        if match:

            flush_segment()

            current_segment = int(
                match.group(1)
            )

            current_paragraph = None
            current_type = None

            continue

        # ----------------------------------------------------
        # PARAGRAPH
        # ----------------------------------------------------

        match = re.fullmatch(
            r"PARAGRAPH\s+\[(\d+)\]",
            line,
            flags=re.IGNORECASE
        )

        if match:

            current_paragraph = int(
                match.group(1)
            )

            continue

        # ----------------------------------------------------
        # TYPE
        # ----------------------------------------------------

        match = re.fullmatch(
            r"\[(NARRATION|DIALOGUE|SYSTEM|UNKNOWN)\]",
            line,
            flags=re.IGNORECASE
        )

        if match:

            current_type = match.group(1).upper()

            continue

        # ----------------------------------------------------
        # TEXT
        # ----------------------------------------------------

        if current_type is not None:

            current_text.append(line)

    flush_segment()

    return segments


# ============================================================
# TEXT UTILITIES
# ============================================================

def name_in_text(
    name: str,
    text: str
) -> bool:
    """
    Check whether a character name appears in text.
    """

    return re.search(
        rf"\b{re.escape(name)}\b",
        text,
        flags=re.IGNORECASE
    ) is not None


def get_aliases(
    character: Dict
) -> List[str]:

    aliases = character.get(
        "aliases",
        []
    )

    if not isinstance(
        aliases,
        list
    ):
        return []

    return [
        alias
        for alias in aliases
        if isinstance(alias, str)
        and alias.strip()
    ]


# ============================================================
# CHARACTER SCORING
# ============================================================

ACTION_WORDS = {
    "walked",
    "ran",
    "stood",
    "sat",
    "flipped",
    "looked",
    "checked",
    "tapped",
    "opened",
    "closed",
    "turned",
    "moved",
    "entered",
    "left",
    "continued",
    "started",
    "stopped",
    "filled",
    "pushed",
    "created",
    "made",
    "took",
    "held",
    "picked",
    "put",
    "read",
    "watched",
    "searched",
    "clicked",
    "typed",
    "asked",
    "answered",
}


THOUGHT_WORDS = {
    "thought",
    "thoughts",
    "wondered",
    "pondered",
    "contemplated",
    "realized",
    "understood",
    "considered",
    "decided",
    "believed",
    "knew",
    "imagined",
    "remembered",
    "forgot",
    "felt",
}


PERCEPTION_WORDS = {
    "looked",
    "watched",
    "saw",
    "heard",
    "noticed",
    "observed",
    "felt",
    "realizing",
    "realized",
}


def score_character(
    name: str,
    text: str
) -> Dict:

    text_lower = text.lower()

    score = 0
    reasons = []

    # --------------------------------------------------------
    # Explicit character mention
    # --------------------------------------------------------

    if name_in_text(
        name,
        text
    ):

        score += 2

        reasons.append(
            "Character explicitly mentioned"
        )

    # --------------------------------------------------------
    # Action association
    # --------------------------------------------------------

    action_found = any(
        re.search(
            rf"\b{re.escape(word)}\b",
            text_lower
        )
        for word in ACTION_WORDS
    )

    if (
        action_found
        and name_in_text(name, text)
    ):

        score += 2

        reasons.append(
            "Character is associated with an action"
        )

    # --------------------------------------------------------
    # Internal thought
    # --------------------------------------------------------

    thought_found = any(
        re.search(
            rf"\b{re.escape(word)}\b",
            text_lower
        )
        for word in THOUGHT_WORDS
    )

    if (
        thought_found
        and name_in_text(name, text)
    ):

        score += 4

        reasons.append(
            "Character is associated with internal thought"
        )

    # --------------------------------------------------------
    # Perception
    # --------------------------------------------------------

    perception_found = any(
        re.search(
            rf"\b{re.escape(word)}\b",
            text_lower
        )
        for word in PERCEPTION_WORDS
    )

    if (
        perception_found
        and name_in_text(name, text)
    ):

        score += 3

        reasons.append(
            "Character is associated with perception"
        )

    return {
        "name": name,
        "score": score,
        "reasons": reasons,
    }


# ============================================================
# CANDIDATE DETECTION
# ============================================================

def find_candidates(
    text: str,
    characters: Dict
) -> List[Dict]:

    candidates = []

    for character in characters.values():

        if not isinstance(
            character,
            dict
        ):
            continue

        name = character.get(
            "name"
        )

        if not name:
            continue

        candidate = score_character(
            name,
            text
        )

        if candidate["score"] > 0:

            candidates.append(
                candidate
            )

    candidates.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return candidates


# ============================================================
# FOCUS RESOLUTION
# ============================================================

def resolve_focus(
    candidates: List[Dict],
    current_focus: str | None,
    current_score: int,
    current_streak: int
):

    # --------------------------------------------------------
    # No candidate
    #
    # IMPORTANT:
    # V2 keeps the existing focus instead of resetting it.
    # --------------------------------------------------------

    if not candidates:

        if current_focus:

            return (
                current_focus,
                current_score,
                current_streak
            )

        return (
            None,
            0,
            0
        )

    best = candidates[0]

    best_name = best["name"]
    best_score = best["score"]

    # --------------------------------------------------------
    # Same character remains the focus
    # --------------------------------------------------------

    if (
        current_focus
        and best_name.lower()
        == current_focus.lower()
    ):

        return (
            current_focus,
            best_score,
            current_streak + 1
        )

    # --------------------------------------------------------
    # New candidate
    #
    # Require meaningful evidence before switching focus.
    # --------------------------------------------------------

    if best_score >= 4:

        return (
            best_name,
            best_score,
            1
        )

    # --------------------------------------------------------
    # Weak evidence for a new character:
    # keep the existing focus.
    # --------------------------------------------------------

    if current_focus:

        return (
            current_focus,
            current_score,
            current_streak
        )

    # --------------------------------------------------------
    # No established focus yet.
    # --------------------------------------------------------

    return (
        None,
        0,
        0
    )


# ============================================================
# ANALYZE CONTEXT
# ============================================================

def analyze_context(
    segments,
    characters
):

    results = []

    current_focus = None
    current_score = 0
    current_streak = 0

    for segment in segments:

        text = segment["text"]
        segment_type = segment["type"]

        # ----------------------------------------------------
        # SYSTEM TEXT MUST NOT CHANGE NARRATIVE FOCUS
        # ----------------------------------------------------

        if segment_type == "SYSTEM":

            candidates = []

            result = {
                "segment_index": segment[
                    "segment_index"
                ],
                "segment_number": segment[
                    "segment_number"
                ],
                "paragraph": segment[
                    "paragraph"
                ],
                "type": segment_type,
                "text": text,
                "candidates": candidates,
                "current_focus": current_focus,
                "focus_score": current_score,
                "focus_streak": current_streak,
            }

            results.append(result)

            continue

        # ----------------------------------------------------
        # NARRATION / DIALOGUE
        # ----------------------------------------------------

        candidates = find_candidates(
            text,
            characters
        )

        (
            new_focus,
            new_score,
            new_streak
        ) = resolve_focus(
            candidates,
            current_focus,
            current_score,
            current_streak
        )

        # ----------------------------------------------------
        # Focus persistence
        # ----------------------------------------------------

        current_focus = new_focus
        current_score = new_score
        current_streak = new_streak

        result = {
            "segment_index": segment[
                "segment_index"
            ],
            "segment_number": segment[
                "segment_number"
            ],
            "paragraph": segment[
                "paragraph"
            ],
            "type": segment_type,
            "text": text,
            "candidates": candidates,
            "current_focus": current_focus,
            "focus_score": current_score,
            "focus_streak": current_streak,
        }

        results.append(result)

    return results


# ============================================================
# SAVE CONTEXT
# ============================================================

def save_context(
    results,
    characters
):

    character_summary = {}

    for key, character in characters.items():

        name = character.get(
            "name"
        )

        if not name:
            continue

        focused_segments = [
            result["segment_index"]
            for result in results
            if result["current_focus"]
            and result["current_focus"].lower()
            == name.lower()
        ]

        character_summary[key] = {
            "name": name,
            "segments": focused_segments,
        }

    output = {
        "source": INPUT_FILE,
        "version": "Character Context V2",
        "characters": character_summary,
        "segments": results,
    }

    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            output,
            f,
            indent=4,
            ensure_ascii=False
        )


# ============================================================
# PRINT RESULTS

def print_results(
    results
):

    print()

    print("=" * 70)
    print("ELIZA READER - CHARACTER CONTEXT V2")
    print("=" * 70)

    for result in results:

        print()

        print(
            f"SEGMENT "
            f"[{result['segment_number']:03d}]"
        )

        print(
            f"PARAGRAPH "
            f"[{result['paragraph']:03d}]"
        )

        print(
            f"[{result['type']}]"
        )

        print(
            result["text"]
        )

        # ----------------------------------------------------
        # Candidates
        # ----------------------------------------------------

        candidates = result[
            "candidates"
        ]

        if candidates:

            print()
            print("Candidates:")

            for candidate in candidates:

                print(
                    f"  {candidate['name']} "
                    f"| Score: {candidate['score']}"
                )

                for reason in candidate[
                    "reasons"
                ]:

                    print(
                        f"      - {reason}"
                    )

        # ----------------------------------------------------
        # Current context
        # ----------------------------------------------------

        print()

        print(
            f"Current focus : "
            f"{result['current_focus']}"
        )

        print(
            f"Focus score   : "
            f"{result['focus_score']}"
        )

        print(
            f"Focus streak  : "
            f"{result['focus_streak']}"
        )

    print()



# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("ELIZA READER")
    print("Character Context V2")
    print("=" * 70)

    print()

    print(
        f"Reading: {INPUT_FILE}"
    )

    segments = load_story()

    characters = load_characters()

    print(
        f"Loaded {len(segments)} segments."
    )

    print(
        f"Loaded {len(characters)} characters from memory."
    )

    results = analyze_context(
        segments,
        characters
    )

    print_results(
        results
    )

    save_context(
        results,
        characters
    )

    print(
        f"Context analysis saved to: "
        f"{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()
