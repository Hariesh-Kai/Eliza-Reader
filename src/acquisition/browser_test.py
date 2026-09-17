from playwright.sync_api import sync_playwright


URL = "https://novelarrow.com/chapter/losing-money-to-be-a-tycoon/chapter1-wealth-conversion-system"


def main():

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True
        )

        page = browser.new_page(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/139.0.0.0 Safari/537.36"
            )
        )

        print("Opening webpage...")

        response = page.goto(
            URL,
            wait_until="domcontentloaded",
            timeout=60000
        )

        print("Status:", response.status if response else "Unknown")

        print("Title:", page.title())

        print("Reading page content...")

        html = page.content()

        print("HTML size:", len(html))

        with open(
            "page.html",
            "w",
            encoding="utf-8"
        ) as file:
            file.write(html)

        print("Saved webpage to page.html")

        browser.close()


if __name__ == "__main__":
    main()