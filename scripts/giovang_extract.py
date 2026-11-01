
import asyncio
from pathlib import Path
from urllib.parse import urlparse
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent
SOURCE_FILE = ROOT / "config" / "giovang_url.txt"
OUTPUT_FILE = ROOT / "giovang.m3u"

# Hai trang trận đấu bạn đã cung cấp, dùng làm trang kiểm tra dự phòng.
TEST_PAGES = [
    "https://giovang.love/truc-tiep-golden-state-valkyries-vs-atlanta-dream-01-11-21091573",
    "https://giovang.love/truc-tiep-houston-rockets-vs-oklahoma-city-thunder-01-11-34888277",
]

def is_m3u8(url):
    try:
        parsed = urlparse(url)
        return (
            parsed.scheme in ("http", "https")
            and ".m3u8" in (parsed.path + parsed.query).lower()
        )
    except Exception:
        return False


async def main():
    homepage = "https://giovang.love/"

    if SOURCE_FILE.exists():
        value = SOURCE_FILE.read_text(encoding="utf-8").strip()
        if value.startswith("http"):
            homepage = value

    found = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            ignore_https_errors=True
        )

        page = await context.new_page()

        async def inspect_page(url, title):
            streams = set()

            def capture(request):
                if is_m3u8(request.url):
                    streams.add(request.url)

            page.on("request", capture)

            try:
                print(f"Dang mo: {title}")
                await page.goto(
                    url,
                    wait_until="domcontentloaded",
                    timeout=60000
                )
                await page.wait_for_timeout(15000)

                # Kiểm tra các iframe được nhúng trong trang.
                frames = page.frames
                for frame in frames:
                    try:
                        frame_url = frame.url
                        if frame_url.startswith("http"):
                            await frame.wait_for_timeout(3000)
                    except Exception:
                        pass

            except Exception as e:
                print(f"Loi khi mo {url}: {e}")

            finally:
                page.remove_listener("request", capture)

            for stream in streams:
                found[stream] = title

            print(f"Tim thay {len(streams)} luong M3U8")

        # Mở trang chủ và lấy các đường dẫn trận đấu.
        try:
            await page.goto(
                homepage,
                wait_until="domcontentloaded",
                timeout=60000
            )
            await page.wait_for_timeout(8000)

            links = await page.locator("a").evaluate_all(
                """els => els.map(a => a.href)
                .filter(h => h.includes('/truc-tiep-'))"""
            )

            match_pages = list(dict.fromkeys(links))[:30]

        except Exception as e:
            print(f"Khong doc duoc danh sach tran: {e}")
            match_pages = []

        # Nếu trang chủ không tìm thấy trận, dùng hai trang kiểm tra.
        if not match_pages:
            match_pages = TEST_PAGES

        for url in match_pages:
            title = urlparse(url).path.split("/")[-1]
            await inspect_page(url, title)

        await browser.close()

    lines = ["#EXTM3U"]

    for stream, title in found.items():
        lines.append(f"#EXTINF:-1,{title}")
        lines.append(stream)

    OUTPUT_FILE.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8"
    )

    print("--------------------------------")
    print(f"TONG CONG: {len(found)} luong M3U8")
    print(f"Da tao: {OUTPUT_FILE}")
    print("--------------------------------")


if __name__ == "__main__":
    asyncio.run(main())
