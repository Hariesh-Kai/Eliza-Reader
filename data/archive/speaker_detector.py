import re
from typing import List, Dict, Optional


# ============================================================
# ELIZA READER
# Speaker Detector V1
#
# Input:
#   analyzed_story_v2.txt
#
# Purpose:
#   Detect the likely speaker of dialogue segments.
#
# Output:
#   Speaker name
#   Confidence
#   Reason
#
# IMPORTANT:
#   This version does NOT guess when evidence is weak.
# ============================================================


UNKNOWN = "UNKNOWN"

HIGH = "HIGH"
MEDIUM = "MEDIUM"
LOW = "LOW"


# ============================================================
# Character registry
# ============================================================

KNOWN_CHARACTERS = {
    "pei qian": "Pei Qian",
}


# ============================================================
# Character name detection
# ============================================================

def find_character_names(text: str) -> List[str]:
    """
    Find known character names appearing in a piece of text.
    """

    found = []

    lowered = text.lower()

    for key, display_name in KNOWN_CHARACTERS.items():

        if key in lowered:
            found.append(display_name)

    return found


# ============================================================
# Explicit speech attribution
# ============================================================

def detect_explicit_speaker(text: str) -> Optional[str]:
    """
    Detect patterns such as:

        Pei Qian said, "Hello."

        "Hello," Pei Qian said.

        Pei Qian asked.

        Pei Qian shouted.

    Only known characters are considered.
    """

    if not text:
        return None

    # --------------------------------------------------------
    # Character BEFORE speech
    # --------------------------------------------------------

    before_patterns = [
        r"\b(Pei Qian)\s+said\b",
        r"\b(Pei Qian)\s+asked\b",
        r"\b(Pei Qian)\s+replied\b",
        r"\b(Pei Qian)\s+answered\b",
        r"\b(Pei Qian)\s+shouted\b",
        r"\b(Pei Qian)\s+exclaimed\b",
        r"\b(Pei Qian)\s+whispered\b",
        r"\b(Pei Qian)\s+cried\b",
        r"\b(Pei Qian)\s+called\b",
        r"\b(Pei Qian)\s+muttered\b",
    ]

    for pattern in before_patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:
            return "Pei Qian"

    # --------------------------------------------------------
    # Character AFTER speech
    # --------------------------------------------------------

    after_patterns = [
        r"\b(Pei Qian)\s+said\b",
        r"\b(Pei Qian)\s+asked\b",
        r"\b(Pei Qian)\s+replied\b",
        r"\b(Pei Qian)\s+answered\b",
        r"\b(Pei Qian)\s+shouted\b",
        r"\b(Pei Qian)\s+exclaimed\b",
        r"\b(Pei Qian)\s+whispered\b",
        r"\b(Pei Qian)\s+cried\b",
        r"\b(Pei Qian)\s+muttered\b",
    ]

    for pattern in after_patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:
            return "Pei Qian"

    return None


# ============================================================
# Nearby narration detection
# ============================================================

def detect_nearby_character(
    previous_segments: List[Dict],
    next_segments: List[Dict]
) -> Optional[str]:
    """
    Look at nearby narration.

    Example:

        Pei Qian looked at the screen.

        "What's going on?!"

    The nearby narration contains Pei Qian.

    We only use a very small context window.
    """

    # --------------------------------------------------------
    # First inspect the immediately previous segment.
    # --------------------------------------------------------

    for segment in reversed(previous_segments[-2:]):

        if segment.get("type") != "NARRATION":
            continue

        names = find_character_names(
            segment.get("text", "")
        )

        if len(names) == 1:
            return names[0]

    # --------------------------------------------------------
    # Then inspect the next segment.
    # --------------------------------------------------------

    for segment in next_segments[:2]:

        if segment.get("type") != "NARRATION":
            continue

        names = find_character_names(
            segment.get("text", "")
        )

        if len(names) == 1:
            return names[0]

    return None


# ============================================================
# Speaker detection
# ============================================================

def detect_speaker(
    dialogue_text: str,
    previous_segments: List[Dict],
    next_segments: List[Dict]
) -> Dict:
    """
    Determine the likely speaker.

    Returns:

        {
            "speaker": "Pei Qian",
            "confidence": "HIGH",
            "reason": "Explicit speech attribution"
        }

    or:

        {
            "speaker": "UNKNOWN",
            "confidence": "LOW",
            "reason": "No reliable speaker evidence"
        }
    """

    # --------------------------------------------------------
    # Method 1: Explicit attribution
    # --------------------------------------------------------

    explicit_speaker = detect_explicit_speaker(
        dialogue_text
    )

    if explicit_speaker:

        return {
            "speaker": explicit_speaker,
            "confidence": HIGH,
            "reason": "Explicit speech attribution"
        }

    # --------------------------------------------------------
    # Method 2: Nearby narration
    # --------------------------------------------------------

    nearby_speaker = detect_nearby_character(
        previous_segments,
        next_segments
    )

    if nearby_speaker:

        return {
            "speaker": nearby_speaker,
            "confidence": MEDIUM,
            "reason": "Character found in nearby narration"
        }

    # --------------------------------------------------------
    # No reliable evidence
    # --------------------------------------------------------

    return {
        "speaker": UNKNOWN,
        "confidence": LOW,
        "reason": "No reliable speaker evidence"
    }


# ============================================================
# Analyze complete story
# ============================================================

def analyze_speakers(
    story: List[Dict]
) -> List[Dict]:
    """
    Add speaker information to dialogue segments.
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
                # Previous segments in same paragraph
                # --------------------------------------------

                previous_segments.extend(
                    segments[:segment_index]
                )

                # --------------------------------------------
                # Next segments in same paragraph
                # --------------------------------------------

                next_segments.extend(
                    segments[segment_index + 1:]
                )

                # --------------------------------------------
                # If there isn't enough context inside the
                # paragraph, use neighboring paragraphs.
                # --------------------------------------------

                if not previous_segments:

                    if paragraph_index > 0:

                        previous_segments.extend(
                            story[
                                paragraph_index - 1
                            ].get("segments", [])
                        )

                if not next_segments:

                    if paragraph_index + 1 < len(story):

                        next_segments.extend(
                            story[
                                paragraph_index + 1
                            ].get("segments", [])
                        )

                speaker_info = detect_speaker(
                    segment.get("text", ""),
                    previous_segments,
                    next_segments
                )

                segment_copy.update(
                    speaker_info
                )

            else:

                segment_copy.update({
                    "speaker": None,
                    "confidence": None,
                    "reason": None
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
        "PEI_QIAN": 0,
        "UNKNOWN": 0,
        "HIGH": 0,
        "MEDIUM": 0,
        "LOW": 0,
    }

    for paragraph in results:

        for segment in paragraph["segments"]:

            if segment["type"] != "DIALOGUE":
                continue

            statistics["TOTAL_DIALOGUE"] += 1

            speaker = segment.get(
                "speaker"
            )

            confidence = segment.get(
                "confidence"
            )

            if speaker == "Pei Qian":
                statistics["PEI_QIAN"] += 1

            elif speaker == UNKNOWN:
                statistics["UNKNOWN"] += 1

            if confidence in statistics:
                statistics[confidence] += 1

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
    print("ELIZA READER - SPEAKER DETECTION V1")
    print("=" * 70)

    print(
        f"\nDialogue segments : "
        f"{statistics['TOTAL_DIALOGUE']}"
    )

    print(
        f"Pei Qian          : "
        f"{statistics['PEI_QIAN']}"
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
                f"[DIALOGUE]"
            )

            print(
                segment["text"]
            )

            print(
                f"Speaker    : "
                f"{segment['speaker']}"
            )

            print(
                f"Confidence : "
                f"{segment['confidence']}"
            )

            print(
                f"Reason     : "
                f"{segment['reason']}"
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
                        f"Confidence: "
                        f"{segment['confidence']}\n"
                    )

                    file.write(
                        f"Reason: "
                        f"{segment['reason']}\n"
                    )

                file.write("\n")

            file.write("\n")


# ============================================================
# Load V2 analysis
# ============================================================

def load_analyzed_story(
    input_file: str
) -> List[Dict]:

    """
    Reconstruct the structure produced by
    story_analyzer_v2.py.

    Expected format:

        PARAGRAPH [001]
        [NARRATION]
        text

        PARAGRAPH [002]
        [DIALOGUE]
        text
    """

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

        # --------------------------------------------
        # New paragraph
        # --------------------------------------------

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

        # --------------------------------------------
        # Segment type
        # --------------------------------------------

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

        # --------------------------------------------
        # Ignore empty lines
        # --------------------------------------------

        if not stripped:
            continue

        # --------------------------------------------
        # Story text
        # --------------------------------------------

        if current_type is not None:

            current_text.append(
                line
            )

    # Flush final segment
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
    output_file = "speaker_analysis.txt"

    print("=" * 70)
    print("ELIZA READER")
    print("Speaker Detector V1")
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

    if not story:

        print(
            "\nERROR: No story data found."
        )

        return

    print(
        f"Loaded {len(story)} paragraphs."
    )

    results = analyze_speakers(
        story
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