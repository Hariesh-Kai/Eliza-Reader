import re
from pathlib import Path

INPUT_FILE = "extracted_story.txt"
OUTPUT_FILE = "analyzed_story_v3.txt"


# ============================================================
# CLASSIFICATION
# ============================================================

def is_system(text: str) -> bool:
    """
    Detect system/interface text.
    """

    stripped = text.strip()

    # Explicit system-style brackets
    if (
        stripped.startswith("<")
        and stripped.endswith(">")
    ):
        return True

    system_patterns = [
        r"^Owner\s*:",
        r"^Profit category\s*:",
        r"^Loss category\s*:",
        r"^Binding.*System",
        r"^Binding success",
        r"^System Funds",
        r"^Personal Wealth",
        r"^Conversion Ratio",
        r"^Profit Conversion Ratio",
        r"^Loss Conversion Ratio",
        r"^Wealth Conversion System",
        r"^Wealth Conversion Rules",
        r"^Additional Rule",
        r"^Special Notice",
    ]

    for pattern in system_patterns:
        if re.search(
            pattern,
            stripped,
            flags=re.IGNORECASE
        ):
            return True

    return False


# ============================================================
# DIALOGUE DETECTION
# ============================================================

OPENING_QUOTES = (
    '"',
    "“",
    "‘",
    "'",
    "「",
    "『",
)

CLOSING_QUOTES = (
    '"',
    "”",
    "’",
    "」",
    "』",
)


def looks_like_embedded_quote(text: str, match) -> bool:
    """
    Determine whether a quoted section is probably an
    embedded quotation/phrase inside narration rather than
    spoken character dialogue.

    Example:

        Tengda represented Soaring in
        ‘Soaring to meteoric rises’.

    The quoted phrase is part of the narration and should
    remain narration.
    """

    start, end = match.span()

    before = text[:start].strip()
    after = text[end:].strip()

    # If there is no surrounding text, it is probably
    # standalone dialogue.
    if not before and not after:
        return False

    # --------------------------------------------------------
    # Common narration patterns where a quoted phrase is
    # embedded inside the sentence.
    # --------------------------------------------------------

    embedded_patterns = [
        r"\brepresented\s*$",
        r"\bcalled\s*$",
        r"\bnamed\s*$",
        r"\btitled\s*$",
        r"\bknown\s+as\s*$",
        r"\bmeaning\s*$",
        r"\bmeaning\s+of\s*$",
        r"\bphrase\s*$",
        r"\bterm\s*$",
        r"\bword\s*$",
        r"\bwords\s*$",
        r"\bslogan\s*$",
        r"\bmotto\s*$",
        r"\bcompany\s+name\s*$",
        r"\bname\s*$",
    ]

    for pattern in embedded_patterns:
        if re.search(
            pattern,
            before,
            flags=re.IGNORECASE
        ):
            return True

    # --------------------------------------------------------
    # A quoted phrase surrounded by ordinary sentence text
    # is usually not dialogue when it is very short.
    #
    # Example:
    #
    #     represented ‘Soaring to meteoric rises’.
    #
    # We do NOT apply this blindly to long quoted sentences,
    # because long sentences are much more likely to be
    # actual dialogue.
    # --------------------------------------------------------

    quoted_content = match.group(0).strip()

    inner = quoted_content[1:-1].strip()

    word_count = len(
        re.findall(r"\b[\w'-]+\b", inner)
    )

    if (
        before
        and after
        and word_count <= 6
    ):
        # If the quoted phrase is embedded in a sentence,
        # treat it as narration.
        return True

    return False


def split_dialogue_segments(text: str):
    """
    Split a paragraph into dialogue and narration segments.

    V3 improvements:
    - Preserves original paragraph text.
    - Handles dialogue followed by narration.
    - Handles malformed dialogue beginning with a quote.
    - Prevents short embedded quoted phrases from being
      incorrectly classified as character dialogue.
    """

    text = text.strip()

    if not text:
        return []

    # --------------------------------------------------------
    # System text
    # --------------------------------------------------------

    if is_system(text):
        return [
            ("SYSTEM", text)
        ]

    # --------------------------------------------------------
    # Find properly closed dialogue
    # --------------------------------------------------------

    pattern = (
        r'([“"][\s\S]*?[”"])'
        r'|'
        r"([‘'][\s\S]*?[’'])"
        r'|'
        r'([「][\s\S]*?[」])'
        r'|'
        r'([『][\s\S]*?[』])'
    )

    matches = list(
        re.finditer(
            pattern,
            text
        )
    )

    # --------------------------------------------------------
    # No proper dialogue found
    # --------------------------------------------------------

    if not matches:

        # If paragraph starts with a quote, treat the
        # complete paragraph as dialogue.
        if text.startswith(
            OPENING_QUOTES
        ):
            return [
                ("DIALOGUE", text)
            ]

        return [
            ("NARRATION", text)
        ]

    segments = []
    cursor = 0

    for match in matches:

        start, end = match.span()

        # ----------------------------------------------------
        # Narration before quoted section
        # ----------------------------------------------------

        before = text[
            cursor:start
        ].strip()

        # ----------------------------------------------------
        # Check whether this quoted section is actually
        # embedded narration rather than dialogue.
        # ----------------------------------------------------

        embedded_quote = looks_like_embedded_quote(
            text,
            match
        )

        if embedded_quote:

            # We don't split this quote out.
            #
            # Instead, continue searching. The complete
            # paragraph will be preserved as narration unless
            # a genuine dialogue section exists elsewhere.
            continue

        # ----------------------------------------------------
        # Narration before dialogue
        # ----------------------------------------------------

        if before:
            segments.append(
                ("NARRATION", before)
            )

        # ----------------------------------------------------
        # Dialogue
        # ----------------------------------------------------

        dialogue = match.group(0).strip()

        if dialogue:
            segments.append(
                ("DIALOGUE", dialogue)
            )

        cursor = end

    # --------------------------------------------------------
    # Important:
    #
    # If every quote was classified as embedded narration,
    # preserve the complete paragraph as narration.
    # --------------------------------------------------------

    if not segments:
        return [
            ("NARRATION", text)
        ]

    # --------------------------------------------------------
    # Narration after final dialogue
    # --------------------------------------------------------

    after = text[
        cursor:
    ].strip()

    if after:
        segments.append(
            ("NARRATION", after)
        )

    return segments


# ============================================================
# LOAD STORY
# ============================================================

def load_story():

    path = Path(
        INPUT_FILE
    )

    if not path.exists():
        raise FileNotFoundError(
            f"Could not find {INPUT_FILE}"
        )

    text = path.read_text(
        encoding="utf-8"
    )

    # The extractor separates paragraphs using blank lines.
    paragraphs = re.split(
        r"\n\s*\n",
        text.strip()
    )

    cleaned = []

    for paragraph in paragraphs:

        paragraph = paragraph.strip()

        if paragraph:
            cleaned.append(
                paragraph
            )

    return cleaned


# ============================================================
# ANALYZE STORY
# ============================================================

def analyze_story(
    paragraphs
):

    results = []

    segment_number = 1

    for paragraph_number, paragraph in enumerate(
        paragraphs,
        start=1
    ):

        segments = split_dialogue_segments(
            paragraph
        )

        for segment_type, text in segments:

            results.append({
                "segment_number": segment_number,
                "paragraph_number": paragraph_number,
                "type": segment_type,
                "text": text,
            })

            segment_number += 1

    return results


# ============================================================
# SAVE ANALYSIS
# ============================================================

def save_analysis(
    results
):

    output = []

    for item in results:

        output.append(
            f"SEGMENT [{item['segment_number']:03d}]"
        )

        output.append(
            f"PARAGRAPH [{item['paragraph_number']:03d}]"
        )

        output.append(
            f"[{item['type']}]"
        )

        output.append(
            item["text"]
        )

        output.append("")

    Path(
        OUTPUT_FILE
    ).write_text(
        "\n".join(output),
        encoding="utf-8"
    )


# ============================================================
# STATISTICS
# ============================================================

def print_statistics(
    results
):

    narration = sum(
        1
        for item in results
        if item["type"] == "NARRATION"
    )

    dialogue = sum(
        1
        for item in results
        if item["type"] == "DIALOGUE"
    )

    system = sum(
        1
        for item in results
        if item["type"] == "SYSTEM"
    )

    unknown = sum(
        1
        for item in results
        if item["type"] == "UNKNOWN"
    )

    paragraphs = len(
        set(
            item["paragraph_number"]
            for item in results
        )
    )

    print()

    print("=" * 70)
    print("CHARACTER / STORY ANALYZER V3")
    print("=" * 70)

    print()

    print(
        f"Total paragraphs : {paragraphs}"
    )

    print(
        f"Total segments   : {len(results)}"
    )

    print(
        f"Narration        : {narration}"
    )

    print(
        f"Dialogue         : {dialogue}"
    )

    print(
        f"System           : {system}"
    )

    print(
        f"Unknown          : {unknown}"
    )

    print()

    print(
        f"Saved to         : {OUTPUT_FILE}"
    )


# ============================================================
# SHOW IMPORTANT SPLITS
# ============================================================

def show_dialogue_splits(
    results
):

    print()

    print("=" * 70)
    print("DIALOGUE SPLITS")
    print("=" * 70)

    current_paragraph = None

    for item in results:

        if item["paragraph_number"] == current_paragraph:
            continue

        current_paragraph = (
            item["paragraph_number"]
        )

        paragraph_items = [
            result
            for result in results
            if result["paragraph_number"]
            == current_paragraph
        ]

        if len(paragraph_items) <= 1:
            continue

        print()

        print(
            f"PARAGRAPH "
            f"[{current_paragraph:03d}]"
        )

        for result in paragraph_items:

            print(
                f"\n[{result['type']}]"
            )

            print(
                result["text"]
            )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 70)
    print("ELIZA READER")
    print("Story Analyzer V3")
    print("=" * 70)

    print()

    print(
        f"Reading: {INPUT_FILE}"
    )

    paragraphs = load_story()

    print(
        f"Loaded {len(paragraphs)} paragraphs."
    )

    results = analyze_story(
        paragraphs
    )

    print_statistics(
        results
    )

    show_dialogue_splits(
        results
    )

    save_analysis(
        results
    )


if __name__ == "__main__":
    main()
