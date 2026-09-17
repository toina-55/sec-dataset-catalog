"""공개 데이터 확보 — 캐시 우선.

PhishTank 벌크 CSV는 익명 다운로드가 되지만 **rate limit이 빡빡하다**(429).
이미 받아둔 파일이 있으면 절대 다시 받지 않는다.
"""
from __future__ import annotations

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
    DATA.mkdir(exist_ok=True)
    print("공개 데이터 확보")
    ok = True
    for name, url in SOURCES.items():
        try:
            fetch(name, url)
        except Exception as exc:  # noqa: BLE001
            print(f"  실패      {name}: {exc}", file=sys.stderr)
            ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

# 추가 데이터 (2026-08-27)
#   sms-spam.tsv — UCI SMS Spam Collection 228번. 5,574건, 라벨+텍스트 2열.
#   Kaggle 미러는 로그인이 필요하지만 UCI 원본은 인증 없이 받힌다.
EXTRA = {
    "sms-spam.tsv": "https://archive.ics.uci.edu/static/public/228/sms+spam+collection.zip",
}
