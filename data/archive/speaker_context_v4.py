import re
from pathlib import Path

from character_memory import CharacterMemory


INPUT_FILE = "analyzed_story_v2.txt"
OUTPUT_FILE = "speaker_analysis_v4.txt"
MEMORY_FILE = "characters.json"


# ============================================================
# CONFIGURATION
# ============================================================

SPEECH_VERBS = {
    "said",
    "asked",
    "replied",
    "answered",
    "shouted",
    "exclaimed",
    "whispered",
    "cried",
    "called",
    "muttered",
    "remarked",
    "continued",
    "added",
    "responded",
    "told",
}

# Narration patterns that strongly connect a character
# to an action/thought immediately around dialogue.
ACTION_WORDS = {
    "thought",
    "wondered",
    "realized",
    "decided",
    "considered",
    "contemplated",
    "exclaimed",
    "shouted",
    "asked",
    "said",
    "replied",
    "answered",
    "muttered",
    "whispered",
    "smiled",
    "laughed",
    "nodded",
    "looked",
    "felt",
}


# ============================================================
# LOAD STORY
# ============================================================

def load_story():

    path = Path(INPUT_FILE)

    if not path.exists():
        raise FileNotFoundError(
            f"Could not find {INPUT_FILE}"
        )

    text = path.read_text(
        encoding="utf-8"
    )

    segments = []

    blocks = re.split(
        r"\n\s*\n",
        text.strip()
    )

    current_paragraph = None

    for block in blocks:

        lines = block.strip().splitlines()

        if not lines:
            continue

        paragraph_id = None
        segment_type = None
        content = []

        for line in lines:

            line = line.strip()

            # Handle:
            # PARAGRAPH [014]
            match = re.search(
                r"PARAGRAPH\s+\[(\d+)\]",
                line,
                flags=re.IGNORECASE
            )

            if match:

                paragraph_id = match.group(1)

                cleaned = re.sub(
                    r"PARAGRAPH\s+\[\d+\]",
                    "",
                    line,
                    flags=re.IGNORECASE
                ).strip()

                if cleaned:
                    content.append(cleaned)

                continue

            # Handle:
            # [DIALOGUE]
            # [NARRATION]
            # [SYSTEM]
            if (
                line.startswith("[")
                and line.endswith("]")
            ):
                segment_type = (
                    line[1:-1].strip()
                )
                continue

            if line:
                content.append(line)

        if segment_type and content:

            segments.append({
                "paragraph": paragraph_id,
                "type": segment_type,
                "text": " ".join(content),
            })

    return segments


# ============================================================
# CHARACTER MEMORY
# ============================================================

def load_characters():

    memory = CharacterMemory(
        memory_file=MEMORY_FILE
    )

    characters = memory.list_characters()

    return memory, characters


# ============================================================
# CHARACTER MATCHING
# ============================================================

def find_character_mentions(
    text,
    characters
):

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
                + re.escape(alias.lower())
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
# EXPLICIT SPEAKER DETECTION
# ============================================================

def detect_explicit_speaker(
    text,
    characters
):

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

        for name_variant in names:

            name_variant = (
                name_variant.strip()
            )

            if not name_variant:
                continue

            for verb in SPEECH_VERBS:

                # Character + speech verb
                pattern = (
                    r"\b"
                    + re.escape(
                        name_variant.lower()
                    )
                    + r"\b"
                    r".{0,50}"
                    r"\b"
                    + re.escape(verb)
                    + r"\b"
                )

                if re.search(
                    pattern,
                    lower_text
                ):
                    return character

                # Speech verb + character
                pattern = (
                    r"\b"
                    + re.escape(verb)
                    + r"\b"
                    r".{0,50}"
                    r"\b"
                    + re.escape(
                        name_variant.lower()
                    )
                    + r"\b"
                )

                if re.search(
                    pattern,
                    lower_text
                ):
                    return character

    return None


# ============================================================
# CHARACTER ACTION DETECTION
# ============================================================

def character_has_action_context(
    text,
    character
):

    name = character.get(
        "name",
        ""
    )

    if not name:
        return False

    lower_text = text.lower()
    lower_name = name.lower()

    if lower_name not in lower_text:
        return False

    for action in ACTION_WORDS:

        pattern = (
            r"\b"
            + re.escape(lower_name)
            + r"\b"
            r".{0,80}"
            r"\b"
            + re.escape(action)
            + r"\b"
        )

        if re.search(
            pattern,
            lower_text
        ):
            return True

        pattern_reverse = (
            r"\b"
            + re.escape(action)
            + r"\b"
            r".{0,80}"
            r"\b"
            + re.escape(lower_name)
            + r"\b"
        )

        if re.search(
            pattern_reverse,
            lower_text
        ):
            return True

    return False


# ============================================================
# LOCAL CONTEXT
# ============================================================

def find_nearby_character(
    dialogue_index,
    segments,
    characters
):

    evidence = {}

    # Look backward.
    start = max(
        0,
        dialogue_index - 3
    )

    for index in range(
        dialogue_index - 1,
        start - 1,
        -1
    ):

        segment = segments[index]

        if segment["type"] != "NARRATION":
            continue

        mentioned = find_character_mentions(
            segment["text"],
            characters
        )

        for character in mentioned:

            character_id = (
                CharacterMemory.make_character_id(
                    character["name"]
                )
            )

            if character_id not in evidence:

                evidence[character_id] = {
                    "character": character,
                    "score": 0,
                    "reasons": [],
                }

            distance = (
                dialogue_index - index
            )

            if distance == 1:
                evidence[
                    character_id
                ]["score"] += 4

                evidence[
                    character_id
                ]["reasons"].append(
                    "Character found in immediately preceding narration"
                )

            elif distance == 2:
                evidence[
                    character_id
                ]["score"] += 3

                evidence[
                    character_id
                ]["reasons"].append(
                    "Character found two segments before dialogue"
                )

            else:
                evidence[
                    character_id
                ]["score"] += 1

                evidence[
                    character_id
                ]["reasons"].append(
                    "Character found in nearby narration"
                )

            if character_has_action_context(
                segment["text"],
                character
            ):

                evidence[
                    character_id
                ]["score"] += 2

                evidence[
                    character_id
                ]["reasons"].append(
                    "Character performs an action or thought nearby"
                )

    # Look forward.
    end = min(
        len(segments),
        dialogue_index + 4
    )

    for index in range(
        dialogue_index + 1,
        end
    ):

        segment = segments[index]

        if segment["type"] != "NARRATION":
            continue

        mentioned = find_character_mentions(
            segment["text"],
            characters
        )

        for character in mentioned:

            character_id = (
                CharacterMemory.make_character_id(
                    character["name"]
                )
            )

            if character_id not in evidence:

                evidence[character_id] = {
                    "character": character,
                    "score": 0,
                    "reasons": [],
                }

            distance = (
                index - dialogue_index
            )

            if distance == 1:
                evidence[
                    character_id
                ]["score"] += 3

                evidence[
                    character_id
                ]["reasons"].append(
                    "Character found in immediately following narration"
                )

            else:
                evidence[
                    character_id
                ]["score"] += 1

                evidence[
                    character_id
                ]["reasons"].append(
                    "Character found in nearby following narration"
                )

    if not evidence:
        return None

    ranked = sorted(
        evidence.values(),
        key=lambda item: item["score"],
        reverse=True
    )

    return ranked


# ============================================================
# ACTIVE SPEAKER STATE
# ============================================================

class SpeakerState:

    def __init__(self):

        self.active_character = None
        self.last_explicit_character = None
        self.last_identified_character = None

    def set_active(
        self,
        character
    ):

        self.active_character = character

    def get_active(self):

        return self.active_character


# ============================================================
# ACTIVE CHARACTER EVIDENCE
# ============================================================

def active_speaker_evidence(
    state,
    dialogue_index,
    segments
):

    if state.active_character is None:
        return None

    character = state.active_character

    score = 0
    reasons = []

    # The active speaker gets continuity
    # only when there isn't another explicit
    # character competing for the dialogue.

    score += 2

    reasons.append(
        "Character is the current active speaker"
    )

    # Examine immediate preceding narration.
    if dialogue_index > 0:

        previous = segments[
            dialogue_index - 1
        ]

        if previous["type"] == "NARRATION":

            if character_has_action_context(
                previous["text"],
                character
            ):

                score += 3

                reasons.append(
                    "Active character performs an action/thought immediately before dialogue"
                )

    return {
        "character": character,
        "score": score,
        "reasons": reasons,
    }


# ============================================================
# SPEAKER DETECTION
# ============================================================

def detect_speaker(
    dialogue_index,
    segments,
    characters,
    state
):

    text = segments[
        dialogue_index
    ]["text"]

    # --------------------------------------------------------
    # 1. Explicit attribution
    # --------------------------------------------------------

    explicit = detect_explicit_speaker(
        text,
        characters
    )

    if explicit:

        state.set_active(
            explicit
        )

        state.last_explicit_character = (
            explicit
        )

        state.last_identified_character = (
            explicit
        )

        return {
            "speaker": explicit["name"],
            "character_id": (
                CharacterMemory.make_character_id(
                    explicit["name"]
                )
            ),
            "confidence": "HIGH",
            "reason": (
                "Explicit speaker attribution"
            ),
            "voice_id": (
                explicit.get(
                    "voice",
                    {}
                ).get(
                    "voice_id"
                )
            ),
        }

    # --------------------------------------------------------
    # 2. Nearby narration
    # --------------------------------------------------------

    nearby = find_nearby_character(
        dialogue_index,
        segments,
        characters
    )

    # --------------------------------------------------------
    # 3. Active speaker continuity
    # --------------------------------------------------------

    active = active_speaker_evidence(
        state,
        dialogue_index,
        segments
    )

    if active:

        active_id = (
            CharacterMemory.make_character_id(
                active["character"]["name"]
            )
        )

        found = False

        if nearby:

            for candidate in nearby:

                candidate_id = (
                    CharacterMemory.make_character_id(
                        candidate["character"]["name"]
                    )
                )

                if candidate_id == active_id:

                    candidate["score"] += (
                        active["score"]
                    )

                    candidate["reasons"].extend(
                        active["reasons"]
                    )

                    found = True
                    break

        if not found:

            if nearby is None:

                nearby = []

            nearby.append(
                active
            )

    # --------------------------------------------------------
    # 4. No evidence
    # --------------------------------------------------------

    if not nearby:

        return {
            "speaker": "UNKNOWN",
            "character_id": None,
            "confidence": "LOW",
            "reason": (
                "No reliable speaker evidence"
            ),
            "voice_id": None,
        }

    # --------------------------------------------------------
    # 5. Rank candidates
    # --------------------------------------------------------

    nearby.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    best = nearby[0]

    if len(nearby) > 1:

        second = nearby[1]

        # If two characters are too close,
        # do not guess.
        if (
            best["score"]
            - second["score"]
            < 2
        ):

            return {
                "speaker": "UNKNOWN",
                "character_id": None,
                "confidence": "LOW",
                "reason": (
                    "Multiple characters have competing "
                    "contextual evidence"
                ),
                "voice_id": None,
            }

    character = best[
        "character"
    ]

    score = best[
        "score"
    ]

    reasons = list(
        dict.fromkeys(
            best["reasons"]
        )
    )

    # --------------------------------------------------------
    # 6. Confidence
    # --------------------------------------------------------

    if score >= 8:
        confidence = "HIGH"

    elif score >= 5:
        confidence = "MEDIUM"

    elif score >= 3:
        confidence = "LOW"

    else:
        confidence = "LOW"

    if confidence == "LOW":

        return {
            "speaker": "UNKNOWN",
            "character_id": None,
            "confidence": "LOW",
            "reason": (
                "Context evidence is too weak"
            ),
            "voice_id": None,
        }

    # --------------------------------------------------------
    # 7. Update state
    # --------------------------------------------------------

    state.set_active(
        character
    )

    state.last_identified_character = (
        character
    )

    return {
        "speaker": character["name"],
        "character_id": (
            CharacterMemory.make_character_id(
                character["name"]
            )
        ),
        "confidence": confidence,
        "reason": "; ".join(
            reasons
        ),
        "voice_id": (
            character.get(
                "voice",
                {}
            ).get(
                "voice_id"
            )
        ),
    }


# ============================================================
# ANALYSIS
# ============================================================

def analyze_speakers(
    segments,
    characters
):

    state = SpeakerState()

    results = []

    for index, segment in enumerate(
        segments
    ):

        # ----------------------------------------------------
        # Narration can establish the active character.
        # ----------------------------------------------------

        if segment["type"] == "NARRATION":

            mentioned = find_character_mentions(
                segment["text"],
                characters
            )

            # Only establish active character
            # when exactly one known character
            # is mentioned.
            if len(mentioned) == 1:

                character = mentioned[0]

                if character_has_action_context(
                    segment["text"],
                    character
                ):

                    state.set_active(
                        character
                    )

            continue

        # ----------------------------------------------------
        # Ignore system segments.
        # ----------------------------------------------------

        if segment["type"] != "DIALOGUE":
            continue

        result = detect_speaker(
            index,
            segments,
            characters,
            state
        )

        result["segment_index"] = index

        result["paragraph"] = (
            segment["paragraph"]
        )

        result["dialogue"] = (
            segment["text"]
        )

        results.append(
            result
        )

    return results


# ============================================================
# OUTPUT
# ============================================================

def print_results(
    results
):

    print()
    print("-" * 70)
    print("DIALOGUE SPEAKER ANALYSIS")
    print("-" * 70)

    for result in results:

        print()

        print(
            f"PARAGRAPH "
            f"[{result['paragraph']}]"
        )

        print(
            "[DIALOGUE]"
        )

        print(
            result["dialogue"]
        )

        print(
            f"Speaker      : "
            f"{result['speaker']}"
        )

        print(
            f"Character ID : "
            f"{result['character_id']}"
        )

        print(
            f"Confidence   : "
            f"{result['confidence']}"
        )

        print(
            f"Reason       : "
            f"{result['reason']}"
        )

        print(
            f"Voice ID     : "
            f"{result['voice_id']}"
        )


def save_results(
    results
):

    total = len(results)

    identified = sum(
        1
        for result in results
        if result["speaker"] != "UNKNOWN"
    )

    unknown = (
        total - identified
    )

    high = sum(
        1
        for result in results
        if result["confidence"] == "HIGH"
    )

    medium = sum(
        1
        for result in results
        if result["confidence"] == "MEDIUM"
    )

    low = sum(
        1
        for result in results
        if result["confidence"] == "LOW"
    )

    lines = [
        "=" * 70,
        "ELIZA READER - SPEAKER CONTEXT V4",
        "=" * 70,
        "",
        f"Dialogue segments : {total}",
        f"Identified        : {identified}",
        f"Unknown           : {unknown}",
        f"High confidence   : {high}",
        f"Medium confidence : {medium}",
        f"Low confidence    : {low}",
        "",
        "-" * 70,
        "DIALOGUE SPEAKER ANALYSIS",
        "-" * 70,
    ]

    for result in results:

        lines.extend([
            "",
            f"PARAGRAPH [{result['paragraph']}]",
            "[DIALOGUE]",
            result["dialogue"],
            f"Speaker      : {result['speaker']}",
            f"Character ID : {result['character_id']}",
            f"Confidence   : {result['confidence']}",
            f"Reason       : {result['reason']}",
            f"Voice ID     : {result['voice_id']}",
        ])

    Path(
        OUTPUT_FILE
    ).write_text(
        "\n".join(lines),
        encoding="utf-8"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("ELIZA READER")
    print("Speaker Context V4")
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

    print()
    print("=" * 70)
    print(
        "ELIZA READER - SPEAKER CONTEXT V4"
    )
    print("=" * 70)

    results = analyze_speakers(
        segments,
        characters
    )

    total = len(results)

    identified = sum(
        1
        for result in results
        if result["speaker"] != "UNKNOWN"
    )

    unknown = total - identified

    high = sum(
        1
        for result in results
        if result["confidence"] == "HIGH"
    )

    medium = sum(
        1
        for result in results
        if result["confidence"] == "MEDIUM"
    )

    low = sum(
        1
        for result in results
        if result["confidence"] == "LOW"
    )

    print()

    print(
        f"Dialogue segments : {total}"
    )

    print(
        f"Identified        : {identified}"
    )

    print(
        f"Unknown           : {unknown}"
    )

    print(
        f"High confidence   : {high}"
    )

    print(
        f"Medium confidence : {medium}"
    )

    print(
        f"Low confidence    : {low}"
    )

    print_results(
        results
    )

    save_results(
        results
    )

    print()

    print(
        f"Speaker analysis saved to: "
        f"{OUTPUT_FILE}"
    )


if __name__ == "__main__":
    main()