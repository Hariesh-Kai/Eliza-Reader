import re
from typing import List, Tuple

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/139.0.0.0 Safari/537.36"
)


REMOVE_TAGS = [
    "script",
    "style",
    "noscript",
    "svg",
    "canvas",
    "iframe",
    "form",
    "nav",
    "header",
    "footer",
    "aside",
]


UI_WORDS = {
    "home",
    "login",
    "sign in",
    "register",
    "menu",
    "search",
    "next chapter",
    "previous chapter",
    "subscribe",
    "advertisement",
    "comments",
    "comment",
    "share",
    "facebook",
    "twitter",
    "telegram",
    "discord",
    "privacy policy",
    "terms",
    "reader options",
    "font",
    "line height",
    "text brightness",
    "theme",
    "layout",
    "paragraphs",
    "reset all options",
}


def download_page(url: str) -> str:

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)

        page = browser.new_page(
            user_agent=USER_AGENT,
            viewport={
                "width": 1366,
                "height": 768,
            },
        )

        print("Opening webpage...")

        response = page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=60000,
        )

        if response is None:
            browser.close()
            raise RuntimeError("No response received.")

        print(f"Page status: {response.status}")
        print(f"Page title: {page.title()}")

        # Allow JavaScript content to finish rendering.
        page.wait_for_timeout(2000)

        html = page.content()

        browser.close()

        return html


def normalize_text(text: str) -> str:

    text = text.replace("\xa0", " ")

    text = re.sub(
        r"[ \t]+",
        " ",
        text,
    )

    text = re.sub(
        r"\n\s*\n+",
        "\n\n",
        text,
    )

    return text.strip()


def clean_html(html: str) -> BeautifulSoup:

    soup = BeautifulSoup(
        html,
        "lxml",
    )

    for tag_name in REMOVE_TAGS:

        for tag in soup.find_all(tag_name):
            tag.decompose()

    return soup


def count_words(text: str) -> int:

    return len(
        re.findall(
            r"\b\w+\b",
            text,
        )
    )


def count_sentences(text: str) -> int:

    return len(
        re.findall(
            r"[.!?]+",
            text,
        )
    )


def count_dialogue(text: str) -> int:

    return (
        text.count('"')
        + text.count("“")
        + text.count("”")
    )


def ui_penalty(text: str) -> float:

    lowered = text.lower()

    penalty = 0

    for word in UI_WORDS:

        if word in lowered:
            penalty += 1

    return penalty


def story_container_score(
    element,
    text: str,
) -> float:

    words = count_words(text)

    sentences = count_sentences(text)

    dialogue = count_dialogue(text)

    score = 0.0

    # ---------------------------------------------------------
    # Length
    # ---------------------------------------------------------

    if words >= 300:
        score += 3

    if words >= 500:
        score += 3

    if words >= 1000:
        score += 2

    # ---------------------------------------------------------
    # Sentence structure
    # ---------------------------------------------------------

    if sentences >= 10:
        score += 2

    if sentences >= 30:
        score += 2

    # ---------------------------------------------------------
    # Dialogue
    # ---------------------------------------------------------

    if dialogue >= 2:
        score += 1

    if dialogue >= 10:
        score += 1

    # ---------------------------------------------------------
    # Paragraph structure
    # ---------------------------------------------------------

    paragraphs = element.find_all("p")

    if len(paragraphs) >= 5:
        score += 2

    if len(paragraphs) >= 10:
        score += 2

    # ---------------------------------------------------------
    # Penalize UI
    # ---------------------------------------------------------

    score -= ui_penalty(text) * 1.5

    # ---------------------------------------------------------
    # Penalize giant page containers
    #
    # body/html often contain everything.
    # ---------------------------------------------------------

    if element.name in {"body", "html"}:
        score -= 5

    return score


def find_story_container(
    soup: BeautifulSoup,
):
    """
    Search for the DOM element that most likely contains
    the actual chapter.

    We intentionally examine containers rather than treating
    every paragraph/div as an independent story block.
    """

    candidates = []

    for element in soup.find_all(
        ["article", "main", "section", "div"]
    ):

        text = normalize_text(
            element.get_text(
                " ",
                strip=True,
            )
        )

        words = count_words(text)

        if words < 200:
            continue

        score = story_container_score(
            element,
            text,
        )

        candidates.append(
            (
                score,
                words,
                element,
            )
        )

    if not candidates:
        return None

    # Highest score first.
    candidates.sort(
        key=lambda item: (
            item[0],
            item[1],
        ),
        reverse=True,
    )

    best_score, best_words, best_element = candidates[0]

    print(
        f"Selected story container: "
        f"<{best_element.name}> "
        f"({best_words:,} words, "
        f"score={best_score:.2f})"
    )

    return best_element


def extract_paragraphs(container) -> List[str]:
    """
    Extract story paragraphs from the selected container
    without altering or judging the novel's content.

    At this stage the container has already been identified
    as the most likely story region. Preserve short lines,
    dialogue, system messages, numbers, headings inside the
    story, and unusual formatting.
    """

    paragraphs = []

    for paragraph in container.find_all("p"):

        text = normalize_text(
            paragraph.get_text(
                " ",
                strip=True,
            )
        )

        if not text.strip():
            continue

        paragraphs.append(text)

    return paragraphs


def extract_text_nodes(container) -> List[str]:
    """
    Fallback for websites where the story is not inside <p>.
    """

    texts = []

    for element in container.find_all(
        ["div", "span"]
    ):

        # Don't take nested elements that contain
        # many other elements.
        if len(element.find_all(["div", "p", "section"])) > 5:
            continue

        text = normalize_text(
            element.get_text(
                " ",
                strip=True,
            )
        )

        if count_words(text) < 5:
            continue

        if ui_penalty(text) >= 2:
            continue

        texts.append(text)

    return texts


def remove_duplicates(
    blocks: List[str],
) -> List[str]:

    result = []
    seen = set()

    for block in blocks:

        key = re.sub(
            r"\s+",
            " ",
            block.lower(),
        ).strip()

        if key in seen:
            continue

        seen.add(key)

        result.append(block)

    return result



def extract_story(url: str):

    print("\nDownloading webpage using browser...")

    html = download_page(url)

    print(
        f"Rendered HTML size: "
        f"{len(html):,} characters"
    )

    with open(
        "page.html",
        "w",
        encoding="utf-8",
    ) as file:

        file.write(html)

    print(
        "Saved rendered webpage to page.html"
    )

    soup = clean_html(html)

    print("\nSearching for story container...")

    container = find_story_container(soup)

    if container is None:

        print(
            "Could not identify a story container."
        )

        return "", []

    print(
        "Extracting paragraphs..."
    )

    paragraphs = extract_paragraphs(
        container
    )

    print(
        f"Paragraphs found: "
        f"{len(paragraphs)}"
    )

    # ---------------------------------------------------------
    # Fallback
    # ---------------------------------------------------------

    if len(paragraphs) < 5:

        print(
            "Not enough <p> elements. "
            "Trying text-node extraction..."
        )

        paragraphs = extract_text_nodes(
            container
        )

    paragraphs = remove_duplicates(
        paragraphs
    )

    paragraphs = remove_chapter_metadata(
        paragraphs
    )

    print(
        f"Final paragraphs: "
        f"{len(paragraphs)}"
    )

    story_text = "\n\n".join(
        paragraphs
    )

    story_text = normalize_text(
        story_text
    )

    scored_blocks = [
        (
            paragraph,
            story_container_score(
                container,
                paragraph,
            ),
        )
        for paragraph in paragraphs
    ]

    return story_text, scored_blocks


def remove_chapter_metadata(
        paragraphs: List[str],
    ) -> List[str]:
        """
        Remove website/chapter metadata appearing before
        the actual story begins.

        Once the story starts, preserve every paragraph.
        """

        for index, paragraph in enumerate(paragraphs):

            text = paragraph.strip()

            if re.fullmatch(
                r"\d{4}[?!.,]*",
                text,
            ):
                removed = paragraphs[:index]

                if removed:
                    print(
                        f"Removed {len(removed)} "
                        "metadata paragraphs:"
                    )

                    for item in removed:
                        print(f"  - {item}")

                print(
                    f"Story begins with: {text}"
                )

                return paragraphs[index:]

        print(
            "WARNING: Story beginning was not "
            "confidently detected."
        )

        return paragraphs

if __name__ == "__main__":

    url = input(
        "Enter the novel chapter URL: "
    ).strip()

    if not url:

        print("No URL provided.")

    else:

        try:

            story, blocks = extract_story(
                url
            )

            print("\n")
            print("=" * 70)
            print("EXTRACTED STORY")
            print("=" * 70)

            print(story)

            with open(
                "extracted_story.txt",
                "w",
                encoding="utf-8",
            ) as file:

                file.write(story)

            print("\n")
            print("=" * 70)
            print(
                "Saved to: extracted_story.txt"
            )
            print("=" * 70)

        except Exception as error:

            print("\nExtraction failed:")
            print(error)

