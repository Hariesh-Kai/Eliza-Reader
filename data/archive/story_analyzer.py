import re
from typing import List, Dict


# ============================================================
# ELIZA READER
# Story Analyzer V1
#
# Input:
#   extracted_story.txt
#
# Output:
#   Each paragraph classified as:
#       NARRATION
#       DIALOGUE
#       SYSTEM
#       UNKNOWN
#
# IMPORTANT:
#   Original story text is NEVER modified.
# ============================================================


# ------------------------------------------------------------
# Classification labels
# ------------------------------------------------------------

NARRATION = "NARRATION"
DIALOGUE = "DIALOGUE"
SYSTEM = "SYSTEM"
UNKNOWN = "UNKNOWN"


# ------------------------------------------------------------
# Dialogue detection
# ------------------------------------------------------------

DIALOGUE_MARKERS = (
    '"',
    '"',
    '"',
    "'",
    "'",
    "‘",
    "「",
    "『",
)


def is_dialogue(text: str) -> bool:
    """
    Detect whether a paragraph is likely to contain dialogue.

    This is intentionally conservative.
    We do not try to determine the speaker yet.
    """

    text = text.strip()

    if not text:
        return False

    # Strong dialogue indicators
    if text.startswith(DIALOGUE_MARKERS):
        return True

    # Common dialogue patterns where narration precedes speech
    dialogue_patterns = [
        r'["“”].+["“”]',
        r'["“].+',
        r'.+["”]',
        r"^'.+'$",
        r"^‘.+’$",
        r"^「.+」$",
        r"^『.+』$",
    ]

    for pattern in dialogue_patterns:
        if re.search(pattern, text):
            return True

    return False


# ------------------------------------------------------------
# System-text detection
# ------------------------------------------------------------

def is_system(text: str) -> bool:
    """
    Detect system/interface-style text.

    Examples:
        <Binding of the Wealth Conversion System in progress...>
        <Binding success.>
        <Owner: Pei Qian>
        <Profit category:>
    """

    text = text.strip()

    if not text:
        return False

    # Text enclosed in angle brackets
    if text.startswith("<") and text.endswith(">"):
        return True

    # System-style text that begins with <
    if text.startswith("<"):
        return True

    # Common system notification patterns
    system_patterns = [
        r"^\[System\]",
        r"^System:",
        r"^SYSTEM:",
        r"^System\s",
        r"^Notification:",
        r"^Status:",
        r"^Owner:",
        r"^Profit category:",
        r"^Loss category:",
    ]

    for pattern in system_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True

    return False


# ------------------------------------------------------------
# Paragraph classification
# ------------------------------------------------------------

def classify_paragraph(text: str) -> str:
    """
    Classify one paragraph.

    Priority:
        SYSTEM
        DIALOGUE
        NARRATION
        UNKNOWN

    We check SYSTEM first because system text may contain
    punctuation that could otherwise look like dialogue.
    """

    text = text.strip()

    if not text:
        return UNKNOWN

    if is_system(text):
        return SYSTEM

    if is_dialogue(text):
        return DIALOGUE

    # For V1, ordinary non-empty story paragraphs are narration.
    if len(text) > 0:
        return NARRATION

    return UNKNOWN


# ------------------------------------------------------------
# Analyze complete story
# ------------------------------------------------------------

def analyze_story(story_text: str) -> List[Dict]:
    """
    Analyze the extracted story paragraph by paragraph.

    Returns a list like:

    [
        {
            "index": 1,
            "type": "NARRATION",
            "text": "2009?!"
        },
        ...
    ]

    The text is preserved exactly.
    """

    paragraphs = story_text.split("\n\n")

    results = []

    for index, paragraph in enumerate(paragraphs, start=1):

        # Preserve original paragraph text.
        original_text = paragraph.strip()

        if not original_text:
            continue

        classification = classify_paragraph(original_text)

        results.append({
            "index": index,
            "type": classification,
            "text": original_text,
        })

    return results


# ------------------------------------------------------------
# Print analysis
# ------------------------------------------------------------

def print_analysis(results: List[Dict]) -> None:
    """
    Print the analyzed story in a readable format.
    """

    print("\n" + "=" * 70)
    print("ELIZA READER - STORY ANALYSIS")
    print("=" * 70)

    counts = {
        NARRATION: 0,
        DIALOGUE: 0,
        SYSTEM: 0,
        UNKNOWN: 0,
    }

    for item in results:
        counts[item["type"]] += 1

    print(f"\nTotal paragraphs: {len(results)}")

    print(f"Narration : {counts[NARRATION]}")
    print(f"Dialogue  : {counts[DIALOGUE]}")
    print(f"System    : {counts[SYSTEM]}")
    print(f"Unknown   : {counts[UNKNOWN]}")

    print("\n" + "-" * 70)
    print("PARAGRAPH ANALYSIS")
    print("-" * 70)

    for item in results:
        print(
            f"\n[{item['index']:03d}] "
            f"{item['type']}"
        )

        print(item["text"])


# ------------------------------------------------------------
# Save structured analysis
# ------------------------------------------------------------

def save_analysis(results: List[Dict], output_file: str) -> None:
    """
    Save the analysis to a text file.

    Original story text is preserved.
    """

    with open(output_file, "w", encoding="utf-8") as file:

        for item in results:
            file.write(
                f"[{item['index']:03d}] "
                f"{item['type']}\n"
            )

            file.write(item["text"])
            file.write("\n\n")


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main():

    input_file = "extracted_story.txt"
    output_file = "analyzed_story.txt"

    print("=" * 70)
    print("ELIZA READER")
    print("Story Analyzer V1")
    print("=" * 70)

    print(f"\nReading: {input_file}")

    try:
        with open(input_file, "r", encoding="utf-8") as file:
            story_text = file.read()

    except FileNotFoundError:
        print(f"\nERROR: {input_file} was not found.")
        print("Run the story extractor first.")
        return

    if not story_text.strip():
        print("\nERROR: extracted_story.txt is empty.")
        return

    results = analyze_story(story_text)

    print_analysis(results)

    save_analysis(
        results,
        output_file
    )

    print("\n" + "=" * 70)
    print(f"Analysis saved to: {output_file}")
    print("=" * 70)


if __name__ == "__main__":
    main()