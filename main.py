from webpage_extractor import extract_story


def main():

    print("=" * 70)
    print("                         ELIZA READER")
    print("                    Web Story Extractor V2")
    print("=" * 70)

    url = input(
        "\nEnter the novel chapter URL: "
    ).strip()

    if not url:
        print("No URL provided.")
        return

    try:

        story_text, scored_blocks = extract_story(url)

        print("\n")
        print("=" * 70)
        print("                    EXTRACTED STORY")
        print("=" * 70)

        if not story_text:

            print(
                "\nNo likely story content was detected."
            )

        else:

            print("\n")
            print(story_text)

            with open(
                "extracted_story.txt",
                "w",
                encoding="utf-8",
            ) as file:
                file.write(story_text)

            print("\n")
            print("=" * 70)
            print("Extraction complete.")
            print("Saved to: extracted_story.txt")
            print("=" * 70)

    except Exception as error:

        print("\n")
        print("=" * 70)
        print("EXTRACTION FAILED")
        print("=" * 70)
        print(error)


if __name__ == "__main__":
    main()