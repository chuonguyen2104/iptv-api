
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
SOURCE_FILE = ROOT / "config" / "giovang_streams.txt"
OUTPUT_FILE = ROOT / "giovang.m3u"


def valid_m3u8(url):
    parsed = urlparse(url.strip())
    return (
        parsed.scheme in ("http", "https")
        and parsed.netloc
        and ".m3u8" in parsed.path.lower()
    )


def main():
    if not SOURCE_FILE.exists():
        SOURCE_FILE.parent.mkdir(parents=True, exist_ok=True)
        SOURCE_FILE.write_text(
            "# Mỗi dòng theo định dạng: Tên kênh|Link M3U8\n",
            encoding="utf-8"
        )
        print("Đã tạo file config/giovang_streams.txt")
        return

    lines = ["#EXTM3U"]
    count = 0

    for raw in SOURCE_FILE.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()

        if not raw or raw.startswith("#"):
            continue

        if "|" not in raw:
            print(f"Bỏ qua dòng không hợp lệ: {raw}")
            continue

        name, url = raw.split("|", 1)
        name = name.strip()
        url = url.strip()

        if not name or not valid_m3u8(url):
            print(f"Bỏ qua link không hợp lệ: {name}")
            continue

        lines.append(f"#EXTINF:-1,{name}")
        lines.append(url)
        count += 1

    OUTPUT_FILE.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8"
    )

    print(f"Đã tạo {OUTPUT_FILE.name}: {count} kênh")


if __name__ == "__main__":
    main()

