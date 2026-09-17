import re
from typing import List, Dict, Optional

from character_memory import CharacterMemory


# ============================================================
# ELIZA READER
# Speaker Detector V2
#
# Purpose:
#   Detect the speaker of dialogue and connect the result
#   to persistent character memory.
#
# Output:
#   Speaker
#   Character ID
#   Confidence
#   Reason
#   Voice ID
#
# IMPORTANT:
#   This system does NOT invent speakers.
# ============================================================


UNKNOWN = "UNKNOWN"

HIGH = "HIGH"
MEDIUM = "MEDIUM"
LOW = "LOW"


# ============================================================
# Speech attribution verbs
# ============================================================

SPEECH_VERBS = (
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
)


# ============================================================
# Character extraction
# ============================================================

def find_characters_in_text(
    text: str,
    memory: CharacterMemory
) -> List[Dict]:
    """
    Find registered characters appearing in text.

    Returns character records rather than just names.
    """

    found = []

    lowered = text.lower()

    for character in memory.list_characters():

        name = character["name"]

        if name.lower() in lowered:

            found.append(character)

            continue

        for alias in character.get(
            "aliases",
            []
        ):

            if alias.lower() in lowered:

                found.append(character)

                break

    return found


# ============================================================
# Explicit speaker detection
# ============================================================

def detect_explicit_speaker(
    text: str,
    memory: CharacterMemory
) -> Optional[Dict]:
    """
    Detect explicit speech attribution.

    Examples:

        Pei Qian said...

        Pei Qian asked...

        ... Pei Qian replied.

    """

    lowered = text.lower()

    for character in memory.list_characters():

        name = character["name"]

        names_to_check = [
            name
        ] + character.get(
            "aliases",
            []
        )

        for candidate_name in names_to_check:

            escaped_name = re.escape(
                candidate_name
            )

            for verb in SPEECH_VERBS:

                pattern = (
                    rf"\b{escaped_name}\s+"
                    rf"{verb}\b"
                )

                if re.search(
                    pattern,
                    lowered,
                    re.IGNORECASE
                ):

                    return character

    return None


# ============================================================
# Nearby character detection
# ============================================================

def detect_nearby_character(
    previous_segments: List[Dict],
    next_segments: List[Dict],
    memory: CharacterMemory
) -> Optional[Dict]:
    """
    Search nearby narration for a single known character.

    We only accept the result when exactly one registered
    character is found in the relevant context.
    """

    # --------------------------------------------------------
    # Previous narration
    # --------------------------------------------------------

    for segment in reversed(
        previous_segments[-2:]
    ):

        if segment.get("type") != "NARRATION":
            continue

        characters = find_characters_in_text(
            segment.get("text", ""),
            memory
        )

        if len(characters) == 1:

            return characters[0]

    # --------------------------------------------------------
    # Next narration
    # --------------------------------------------------------

    for segment in next_segments[:2]:

        if segment.get("type") != "NARRATION":
            continue

        characters = find_characters_in_text(
            segment.get("text", ""),
            memory
        )

        if len(characters) == 1:

            return characters[0]

    return None


# ============================================================
# Speaker detection
# ============================================================

def detect_speaker(
    dialogue_text: str,
    previous_segments: List[Dict],
    next_segments: List[Dict],
    memory: CharacterMemory
) -> Dict:
    """
    Detect speaker and connect to character memory.
    """

    # --------------------------------------------------------
    # 1. Explicit attribution
    # --------------------------------------------------------

    character = detect_explicit_speaker(
        dialogue_text,
        memory
    )

    if character:

        return {
            "speaker": character["name"],
            "character_id": CharacterMemory.make_character_id(
                character["name"]
            ),
            "confidence": HIGH,
            "reason": "Explicit speech attribution",
            "voice_id": character["voice"].get(
                "voice_id"
            )
        }

    # --------------------------------------------------------
    # 2. Nearby narration
    # --------------------------------------------------------

    character = detect_nearby_character(
        previous_segments,
        next_segments,
        memory
    )

    if character:

        return {
            "speaker": character["name"],
            "character_id": CharacterMemory.make_character_id(
                character["name"]
            ),
            "confidence": MEDIUM,
            "reason": "Character found in nearby narration",
            "voice_id": character["voice"].get(
                "voice_id"
            )
        }

    # --------------------------------------------------------
    # 3. Unknown
    # --------------------------------------------------------

    return {
        "speaker": UNKNOWN,
        "character_id": None,
        "confidence": LOW,
        "reason": "No reliable speaker evidence",
        "voice_id": None
    }


# ============================================================
# Analyze complete story
# ============================================================

def analyze_speakers(
    story: List[Dict],
    memory: CharacterMemory
) -> List[Dict]:
    """
    Analyze every dialogue segment and connect it to
    character memory.
    """

    results = []

    for paragraph_index, paragraph in enumerate(
        story
    ):

        segments = paragraph.get(
            "segments",
            []
        )

        processed_segments = []

        for segment_index, segment in enumerate(
            segments
        ):

            segment_copy = dict(segment)

            if segment.get("type") == "DIALOGUE":

                previous_segments = []

                next_segments = []

                # --------------------------------------------
                # Same paragraph context
                # --------------------------------------------

                previous_segments.extend(
                    segments[:segment_index]
                )

                next_segments.extend(
                    segments[segment_index + 1:]
                )

                # --------------------------------------------
                # Previous paragraph context
                # --------------------------------------------

                if not previous_segments:

                    if paragraph_index > 0:

                        previous_segments.extend(
                            story[
                                paragraph_index - 1
                            ].get(
                                "segments",
                                []
                            )
                        )

                # --------------------------------------------
                # Next paragraph context
                # --------------------------------------------

                if not next_segments:

                    if paragraph_index + 1 < len(story):

                        next_segments.extend(
                            story[
                                paragraph_index + 1
                            ].get(
                                "segments",
                                []
                            )
                        )

                speaker_info = detect_speaker(
                    segment.get("text", ""),
                    previous_segments,
                    next_segments,
                    memory
                )

                segment_copy.update(
                    speaker_info
                )

                # --------------------------------------------
                # Record dialogue only when a real character
                # has been identified.
                # --------------------------------------------

                if speaker_info["character_id"]:

                    memory.record_dialogue(
                        speaker_info["character_id"],
                        speaker_info["confidence"]
                    )

            else:

                segment_copy.update({
                    "speaker": None,
                    "character_id": None,
                    "confidence": None,
                    "reason": None,
                    "voice_id": None
                })

            processed_segments.append(
                segment_copy
            )

        results.append({
            "paragraph_index": paragraph.get(
                "paragraph_index"
            ),
            "original_text": paragraph.get(
                "original_text",
                ""
            ),
            "segments": processed_segments
        })

    return results


# ============================================================
# Statistics
# ============================================================

def calculate_statistics(
    results: List[Dict]
) -> Dict:

    statistics = {
        "TOTAL_DIALOGUE": 0,
        "IDENTIFIED": 0,
        "UNKNOWN": 0,
        "HIGH": 0,
        "MEDIUM": 0,
        "LOW": 0,
    }

    for paragraph in results:

        for segment in paragraph["segments"]:

            if segment["type"] != "DIALOGUE":
                continue

            statistics[
                "TOTAL_DIALOGUE"
            ] += 1

            if segment.get(
                "character_id"
            ):

                statistics[
                    "IDENTIFIED"
                ] += 1

            else:

                statistics[
                    "UNKNOWN"
                ] += 1

            confidence = segment.get(
                "confidence"
            )

            if confidence in (
                HIGH,
                MEDIUM,
                LOW
            ):

                statistics[
                    confidence
                ] += 1

    return statistics


# ============================================================
# Print results
# ============================================================

def print_results(
    results: List[Dict]
) -> None:

    statistics = calculate_statistics(
        results
    )

    print("\n" + "=" * 70)
    print("ELIZA READER - SPEAKER DETECTION V2")
    print("=" * 70)

    print(
        f"\nDialogue segments : "
        f"{statistics['TOTAL_DIALOGUE']}"
    )

    print(
        f"Identified        : "
        f"{statistics['IDENTIFIED']}"
    )

    print(
        f"Unknown           : "
        f"{statistics['UNKNOWN']}"
    )

    print(
        f"High confidence   : "
        f"{statistics['HIGH']}"
    )

    print(
        f"Medium confidence : "
        f"{statistics['MEDIUM']}"
    )

    print(
        f"Low confidence    : "
        f"{statistics['LOW']}"
    )

    print("\n" + "-" * 70)
    print("DIALOGUE SPEAKER ANALYSIS")
    print("-" * 70)

    for paragraph in results:

        for segment in paragraph["segments"]:

            if segment["type"] != "DIALOGUE":
                continue

            print(
                f"\nPARAGRAPH "
                f"[{paragraph['paragraph_index']:03d}]"
            )

            print(
                "[DIALOGUE]"
            )

            print(
                segment["text"]
            )

            print(
                f"Speaker      : "
                f"{segment['speaker']}"
            )

            print(
                f"Character ID : "
                f"{segment['character_id']}"
            )

            print(
                f"Confidence   : "
                f"{segment['confidence']}"
            )

            print(
                f"Reason       : "
                f"{segment['reason']}"
            )

            print(
                f"Voice ID     : "
                f"{segment['voice_id']}"
            )


# ============================================================
# Save results
# ============================================================

def save_results(
    results: List[Dict],
    output_file: str
) -> None:

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as file:

        for paragraph in results:

            file.write(
                f"PARAGRAPH "
                f"[{paragraph['paragraph_index']:03d}]\n"
            )

            for segment in paragraph["segments"]:

                file.write(
                    f"[{segment['type']}]\n"
                )

                file.write(
                    segment["text"]
                )

                file.write("\n")

                if segment["type"] == "DIALOGUE":

                    file.write(
                        f"Speaker: "
                        f"{segment['speaker']}\n"
                    )

                    file.write(
                        f"Character ID: "
                        f"{segment['character_id']}\n"
                    )

                    file.write(
                        f"Confidence: "
                        f"{segment['confidence']}\n"
                    )

                    file.write(
                        f"Reason: "
                        f"{segment['reason']}\n"
                    )

                    file.write(
                        f"Voice ID: "
                        f"{segment['voice_id']}\n"
                    )

                file.write("\n")

            file.write("\n")


# ============================================================
# Load Story Analyzer V2 output
# ============================================================

def load_analyzed_story(
    input_file: str
) -> List[Dict]:

    with open(
        input_file,
        "r",
        encoding="utf-8"
    ) as file:

        lines = [
            line.rstrip("\n")
            for line in file
        ]

    paragraphs = []

    current_paragraph = None
    current_type = None
    current_text = []

    def flush_segment():

        nonlocal current_type
        nonlocal current_text

        if (
            current_paragraph is not None
            and current_type is not None
            and current_text
        ):

            text = "\n".join(
                current_text
            ).strip()

            if text:

                current_paragraph[
                    "segments"
                ].append({
                    "type": current_type,
                    "text": text
                })

        current_type = None
        current_text = []

    for line in lines:

        stripped = line.strip()

        paragraph_match = re.match(
            r"PARAGRAPH\s+\[(\d+)\]",
            stripped,
            re.IGNORECASE
        )

        if paragraph_match:

            flush_segment()

            if current_paragraph is not None:

                paragraphs.append(
                    current_paragraph
                )

            current_paragraph = {
                "paragraph_index": int(
                    paragraph_match.group(1)
                ),
                "original_text": "",
                "segments": []
            }

            continue

        type_match = re.match(
            r"\[(NARRATION|DIALOGUE|SYSTEM|UNKNOWN)\]",
            stripped,
            re.IGNORECASE
        )

        if type_match:

            flush_segment()

            current_type = (
                type_match.group(1).upper()
            )

            continue

        if not stripped:
            continue

        if current_type is not None:

            current_text.append(
                line
            )

    flush_segment()

    if current_paragraph is not None:

        paragraphs.append(
            current_paragraph
        )

    return paragraphs


# ============================================================
# MAIN
# ============================================================

def main():

    input_file = "analyzed_story_v2.txt"
    output_file = "speaker_analysis_v2.txt"

    print("=" * 70)
    print("ELIZA READER")
    print("Speaker Detector V2")
    print("=" * 70)

    print(
        f"\nReading: {input_file}"
    )

    try:

        story = load_analyzed_story(
            input_file
        )

    except FileNotFoundError:

        print(
            f"\nERROR: {input_file} was not found."
        )

        print(
            "Run story_analyzer_v2.py first."
        )

        return

    memory = CharacterMemory()

    print(
        f"Loaded {len(story)} paragraphs."
    )

    print(
        f"Loaded "
        f"{len(memory.list_characters())} "
        f"characters from memory."
    )

    results = analyze_speakers(
        story,
        memory
    )

    print_results(
        results
    )

    save_results(
        results,
        output_file
    )

    print("\n" + "=" * 70)

    print(
        f"Speaker analysis saved to: "
        f"{output_file}"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()