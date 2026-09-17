"""피싱 URL 피드 2종 확보 — PhishTank · Tranco, 캐시 우선.

PhishTank 벌크 CSV는 익명 다운로드가 되지만 **rate limit이 빡빡하다**(429).
이미 받아둔 파일이 있으면 절대 다시 받지 않는다.

🟡 **둘 다 받을 때마다 값이 다르다.** 인용할 때 수신 날짜를 병기해야 한다.

사용:
    uv run python scripts/fetch_phishing_feeds.py --list   # 목록만
    uv run python scripts/fetch_phishing_feeds.py          # 둘 다 받기
"""
from __future__ import annotations

import argparse
import io
import sys
import zipfile
from pathlib import Path

import requests

DATA = Path(__file__).resolve().parent.parent / "data"

SOURCES = {
    # 양성 — 피싱 URL + submission_time (시간 분할에 필요)
    "phishtank.csv": "https://data.phishtank.com/data/online-valid.csv",
    # 음성 — 인기 도메인 순위 (307 리다이렉트라 allow_redirects 필수)
    "top-1m.csv": "https://tranco-list.eu/top-1m.csv.zip",
}

MIN_BYTES = 100_000  # 429 응답이 236바이트라 크기로 걸러낸다


def fetch(name: str, url: str) -> Path:
    dest = DATA / name
    if dest.exists() and dest.stat().st_size > MIN_BYTES:
        print(f"  캐시 사용  {name}  ({dest.stat().st_size / 1e6:.1f} MB)")
        return dest

    print(f"  다운로드   {name}  <- {url}")
    resp = requests.get(url, timeout=180, allow_redirects=True)
    resp.raise_for_status()

    if len(resp.content) < MIN_BYTES:
        raise RuntimeError(
            f"{name}: 응답이 너무 작다 ({len(resp.content)}B). "
            f"rate limit일 가능성이 높다 — 잠시 후 재시도.\n"
            f"  응답 앞부분: {resp.content[:200]!r}"
        )

    if url.endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(resp.content)) as z:
            inner = z.namelist()[0]
            dest.write_bytes(z.read(inner))
    else:
        dest.write_bytes(resp.content)

    print(f"             -> {dest} ({dest.stat().st_size / 1e6:.1f} MB)")
    return dest


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", action="store_true", help="내려받지 않고 목록만")
    args = ap.parse_args()

    if args.list:
        print(f"\n데이터 위치: {DATA}\n")
        for name, url in SOURCES.items():
            print(f"  {name:<16} <- {url}")
        print("\n🟡 받을 때마다 값이 다르다 — 인용 시 수신 날짜 병기\n")
        return 0

    DATA.mkdir(exist_ok=True)
    print("피싱 URL 피드 확보 (PhishTank · Tranco)")
    ok = True
    for name, url in SOURCES.items():
        try:
            fetch(name, url)
        except Exception as exc:  # noqa: BLE001
            print(f"  실패      {name}: {exc}", file=sys.stderr)
            ok = False
    return 0 if ok else 1


# UCI SMS Spam(228번)은 원래 이 파일 아래에 미사용 상수로 남아 있었다.
# 지금은 `scripts/fetch_mail.py sms-spam`이 받는다.

if __name__ == "__main__":
    raise SystemExit(main())
