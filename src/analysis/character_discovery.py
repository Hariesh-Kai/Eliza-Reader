import re
import json
from pathlib import Path
from typing import List, Dict

from src.analysis.character_memory import CharacterMemory


INPUT_FILE = "data/analysis/analyzed_story_v3.txt"
MEMORY_FILE = "data/analysis/characters.json"
OUTPUT_FILE = "data/analysis/character_context.json"


# ============================================================
# CONFIGURATION
# ============================================================

THOUGHT_WORDS = {
    "thought",
    "wondered",
    "realized",
    "decided",
    "considered",
    "contemplated",
    "felt",
    "remembered",
    "forgot",
    "knew",
    "understood",
    "believed",
    "imagined",
    "hoped",
    "pondered",
}

ACTION_WORDS = {
    "walked",
    "ran",
    "looked",
    "smiled",
    "laughed",
    "nodded",
    "stood",
    "sat",
    "turned",
    "opened",
    "closed",
    "picked",
    "held",
    "took",
    "put",
    "went",
    "returned",
    "entered",
    "left",
    "started",
    "began",
    "continued",
    "stared",
    "watched",
    "examined",
    "tapping",
    "flipped",
}

PERCEPTION_WORDS = {
    "saw",
    "heard",
    "noticed",
    "observed",
    "looked",
    "watched",
    "felt",
}

SELF_REFERENCE_WORDS = {
    "i",
    "me",
    "my",
    "mine",
    "myself",
}


# ============================================================
# LOAD ANALYZED STORY
# ============================================================

def load_story() -> List[Dict]:
    """
    Load analyzed_story_v2.txt.

    Expected format:

    SEGMENT [001]
    PARAGRAPH [001]
    [NARRATION]
    Story text

    SEGMENT [002]
    PARAGRAPH [001]
    [DIALOGUE]
    Dialogue text
    """

    path = Path(INPUT_FILE)

    if not path.exists():
        raise FileNotFoundError(
            f"Could not find {INPUT_FILE}"
        )

    text = path.read_text(
        encoding="utf-8"
    )

    lines = text.splitlines()

    segments = []

    current_segment = None
    current_paragraph = None
    current_type = None
    current_text = []

    def save_current_segment():

        nonlocal current_segment
        nonlocal current_paragraph
        nonlocal current_type
        nonlocal current_text

        if (
            current_segment is not None
            and current_type is not None
            and current_text
        ):

            clean_text = " ".join(
                line.strip()
                for line in current_text
                if line.strip()
            )

            if clean_text:

                segments.append({
                    "segment": current_segment,
                    "paragraph": current_paragraph,
                    "type": current_type,
                    "text": clean_text,
                })

        current_text = []

    for line in lines:

        stripped = line.strip()

        if not stripped:
            continue

        # ----------------------------------------------------
        # SEGMENT [XXX]
        # ----------------------------------------------------

        match = re.fullmatch(
            r"SEGMENT\s+\[(\d+)\]",
            stripped,
            flags=re.IGNORECASE
        )

        if match:

            save_current_segment()

            current_segment = int(
                match.group(1)
            )

            current_paragraph = None
            current_type = None
            current_text = []

            continue

        # ----------------------------------------------------
        # PARAGRAPH [XXX]
        # ----------------------------------------------------

        match = re.fullmatch(
            r"PARAGRAPH\s+\[(\d+)\]",
            stripped,
            flags=re.IGNORECASE
        )

        if match:

            current_paragraph = int(
                match.group(1)
            )

            continue

        # ----------------------------------------------------
        # SEGMENT TYPE
        # ----------------------------------------------------

        match = re.fullmatch(
            r"\[(NARRATION|DIALOGUE|SYSTEM|UNKNOWN)\]",
            stripped,
            flags=re.IGNORECASE
        )

        if match:

            current_type = (
                match.group(1).upper()
            )

            continue

        # ----------------------------------------------------
        # STORY TEXT
        # ----------------------------------------------------

        if current_type is not None:

            current_text.append(
                stripped
            )

    # Save final segment.
    save_current_segment()

    return segments
def load_characters():

    memory = CharacterMemory(
        memory_file=MEMORY_FILE
    )

    characters = memory.list_characters()

    return memory, characters


# ============================================================
# CHARACTER MENTIONS
# ============================================================

def find_character_mentions(
    text: str,
    characters: List[Dict]
) -> List[Dict]:

    found = []

    lower_text = text.lower()

    for character in characters:

        names = []

        name = character.get(
            "name",
            ""
        ).strip()

        if name:
            names.append(name)

        names.extend(
            character.get(
                "aliases",
                []
            )
        )

        for alias in names:

            alias = alias.strip()

            if not alias:
                continue

            pattern = (
                r"\b"
                + re.escape(
                    alias.lower()
                )
                + r"\b"
            )

            if re.search(
                pattern,
                lower_text
            ):

                found.append(
                    character
                )

                break

    return found


# ============================================================
# SENTENCE SPLITTING
# ============================================================

def split_sentences(
    text: str
) -> List[str]:

    sentences = re.split(
        r"(?<=[.!?])\s+",
        text.strip()
    )

    return [
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
    ]


# ============================================================
# CHARACTER SCORING
# ============================================================

def score_character_in_sentence(
    sentence: str,
    character: Dict
):

    name = character.get(
        "name",
        ""
    ).strip()

    if not name:
        return 0, []

    lower_sentence = (
        sentence.lower()
    )

    lower_name = (
        name.lower()
    )

    if not re.search(
        r"\b"
        + re.escape(lower_name)
        + r"\b",
        lower_sentence
    ):
        return 0, []

    score = 2

    reasons = [
        "Character explicitly mentioned"
    ]

    # --------------------------------------------------------
    # Action evidence
    # --------------------------------------------------------

    for word in ACTION_WORDS:

        pattern = (
            r"\b"
            + re.escape(lower_name)
            + r"\b"
            r".{0,100}"
            r"\b"
            + re.escape(word)
            + r"\b"
        )

        if re.search(
            pattern,
            lower_sentence
        ):

            score += 2

            reasons.append(
                "Character is associated with an action"
            )

            break

    # --------------------------------------------------------
    # Thought evidence
    # --------------------------------------------------------

    for word in THOUGHT_WORDS:

        pattern = (
            r"\b"
            + re.escape(lower_name)
            + r"\b"
            r".{0,100}"
            r"\b"
            + re.escape(word)
            + r"\b"
        )

        if re.search(
            pattern,
            lower_sentence
        ):

            score += 4

            reasons.append(
                "Character is associated with internal thought"
            )

            break

    # --------------------------------------------------------
    # Perception evidence
    # --------------------------------------------------------

    for word in PERCEPTION_WORDS:

        pattern = (
            r"\b"
            + re.escape(lower_name)
            + r"\b"
            r".{0,100}"
            r"\b"
            + re.escape(word)
            + r"\b"
        )

        if re.search(
            pattern,
            lower_sentence
        ):

            score += 3

            reasons.append(
                "Character is associated with perception"
            )

            break

    return score, reasons


# ============================================================
# NARRATIVE FOCUS
# ============================================================

def analyze_narration_focus(
    segment: Dict,
    characters: List[Dict]
):

    text = segment["text"]

    sentences = split_sentences(
        text
    )

    scores = {}

    for sentence in sentences:

        mentioned = find_character_mentions(
            sentence,
            characters
        )

        for character in mentioned:

            character_id = (
                CharacterMemory.make_character_id(
                    character["name"]
                )
            )

            if character_id not in scores:

                scores[character_id] = {
                    "character": character,
                    "score": 0,
                    "reasons": [],
                    "sentences": [],
                }

            score, reasons = (
                score_character_in_sentence(
                    sentence,
                    character
                )
            )

            scores[
                character_id
            ]["score"] += score

            scores[
                character_id
            ]["reasons"].extend(
                reasons
            )

            scores[
                character_id
            ]["sentences"].append(
                sentence
            )

    if not scores:
        return []

    return sorted(
        scores.values(),
        key=lambda item: item["score"],
        reverse=True
    )


# ============================================================
# CONTEXT STATE
# ============================================================

class ContextState:

    def __init__(self):

        self.current_focus = None
        self.focus_score = 0
        self.focus_streak = 0

    def update(
        self,
        ranked_candidates
    ):

        if not ranked_candidates:
            return self.current_focus

        best = ranked_candidates[0]

        # ----------------------------------------------------
        # Establish initial focus
        # ----------------------------------------------------

        if self.current_focus is None:

            if best["score"] >= 4:

                self.current_focus = (
                    best["character"]
                )

                self.focus_score = (
                    best["score"]
                )

                self.focus_streak = 1

            return self.current_focus

        current_id = (
            CharacterMemory.make_character_id(
                self.current_focus["name"]
            )
        )

        best_id = (
            CharacterMemory.make_character_id(
                best["character"]["name"]
            )
        )

        # ----------------------------------------------------
        # Same focus continues
        # ----------------------------------------------------

        if current_id == best_id:

            self.focus_score = (
                best["score"]
            )

            self.focus_streak += 1

            return self.current_focus

        # ----------------------------------------------------
        # Strong evidence for a new focus
        # ----------------------------------------------------

        if best["score"] >= 7:

            self.current_focus = (
                best["character"]
            )

            self.focus_score = (
                best["score"]
            )

            self.focus_streak = 1

        return self.current_focus


# ============================================================
# ANALYZE CHAPTER
# ============================================================

def analyze_chapter(
    segments,
    characters
):

    state = ContextState()

    results = []

    for index, segment in enumerate(
        segments
    ):

        if segment["type"] != "NARRATION":
            continue

        ranked = analyze_narration_focus(
            segment,
            characters
        )

        focus = state.update(
            ranked
        )

        candidate_info = []

        for candidate in ranked:

            candidate_info.append({
                "name": candidate[
                    "character"
                ]["name"],
                "score": candidate[
                    "score"
                ],
                "reasons": list(
                    dict.fromkeys(
                        candidate["reasons"]
                    )
                ),
            })

        results.append({
            "segment_index": index,
            "segment_number": segment[
                "segment"
            ],
            "paragraph": segment[
                "paragraph"
            ],
            "type": segment[
                "type"
            ],
            "text": segment[
                "text"
            ],
            "candidates": candidate_info,
            "current_focus": (
                focus["name"]
                if focus
                else None
            ),
            "focus_score": (
                state.focus_score
                if focus
                else 0
            ),
            "focus_streak": (
                state.focus_streak
                if focus
                else 0
            ),
        })

    return results


# ============================================================
# PRINT RESULTS
# ============================================================

def print_results(
    results
):

    print()
    print("=" * 70)
    print(
        "ELIZA READER - CHARACTER CONTEXT"
    )
    print("=" * 70)

    for result in results:

        if not result["candidates"]:
            continue

        print()

        print(
            f"PARAGRAPH "
            f"[{result['paragraph']:03d}]"
        )

        print(
            f"SEGMENT "
            f"[{result['segment_number']:03d}]"
        )

        print(
            f"Narration: "
            f"{result['text'][:180]}"
        )

        print()

        print(
            "Candidates:"
        )

        for candidate in result[
            "candidates"
        ]:

            print(
                f"  {candidate['name']}"
                f" | Score: "
                f"{candidate['score']}"
            )

            for reason in candidate[
                "reasons"
            ]:

                print(
                    f"      - {reason}"
                )

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


# ============================================================
# SAVE RESULTS
# ============================================================

def save_results(
    results
):

    output = {
        "source": INPUT_FILE,
        "characters": {},
        "segments": results,
    }

    for result in results:

        focus = result[
            "current_focus"
        ]

        if not focus:
            continue

        character_id = (
            CharacterMemory.make_character_id(
                focus
            )
        )

        if character_id not in output[
            "characters"
        ]:

            output[
                "characters"
            ][character_id] = {
                "name": focus,
                "segments": [],
            }

        output[
            "characters"
        ][character_id][
            "segments"
        ].append(
            result["segment_number"]
        )

    Path(
        OUTPUT_FILE
    ).write_text(
        json.dumps(
            output,
            indent=4,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    print()
    print(
        f"Context analysis saved to: "
        f"{OUTPUT_FILE}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("ELIZA READER")
    print("Character Context V1")
    print("=" * 70)

    print()

    print(
        f"Reading: {INPUT_FILE}"
    )

    segments = load_story()

    print(
        f"Loaded {len(segments)} segments."
    )

    memory, characters = (
        load_characters()
    )

    print(
        f"Loaded {len(characters)} "
        f"characters from memory."
    )

    results = analyze_chapter(
        segments,
        characters
    )

    print_results(
        results
    )

    save_results(
        results
    )


if __name__ == "__main__":
    main()