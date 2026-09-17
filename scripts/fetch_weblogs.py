"""웹·시스템 로그 5종 확보 — 원출처 직접 다운로드, 캐시 우선.

한 줄 = 한 요청인 **액세스 로그**(NASA · Splunk 튜토리얼), 섹션 구조인 **WAF 감사
로그**(OWASP ModSecurity), 플로우 통계(CIC-IDS2017), 시스템 로그 벤치마크(LogHub).

    uv run python scripts/fetch_weblogs.py --list        # 목록만
    uv run python scripts/fetch_weblogs.py nasa loghub   # 골라서
    uv run python scripts/fetch_weblogs.py --all         # 전부 (약 0.44 GB)

🟡 **Splunk 튜토리얼은 타임스탬프가 받는 시점 기준으로 다시 매겨진다.** 건수·구조는
   재현되지만 절대 날짜는 재현되지 않는다.
🟡 **Zenodo는 `/records/.../files/` 경로가 403을 낸다.** 여기서는 API의
   `/api/records/<id>/files/<name>/content` 를 쓴다 — 그쪽은 열려 있다.
"""
from __future__ import annotations

import argparse
import gzip
import shutil
import zipfile
from pathlib import Path

import requests

DATA = Path(__file__).resolve().parent.parent / "data"
UA = {"User-Agent": "Mozilla/5.0 (compatible; sec-dataset-catalog)"}

DATASETS = {
    "cicids2017": {
        "name": "CIC-IDS2017 (HuggingFace 미러)",
        "size": "0.37 GB",
        "license": "원 배포처 라이선스 미명시 (연구용 재배포 관행)",
        "왜": "침입탐지 벤치마크의 기준점. 라벨 14종 · 283만 행. "
              "원 배포처(UNB)는 폼 제출이 필요해 미러를 쓴다.",
        "files": [
            ("https://huggingface.co/datasets/rdpahalavan/CIC-IDS2017/resolve/main/"
             "Network-Flows/CICIDS_Flow.parquet", "cicids2017/CICIDS_Flow.parquet"),
            ("https://huggingface.co/datasets/c01dsnap/CIC-IDS2017/resolve/main/"
             "Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv",
             "cicids2017/Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv"),
        ],
    },
    "splunk-tutorial": {
        "name": "Splunk 검색 튜토리얼 데이터",
        "size": "11 MB",
        "license": "Splunk 공식 튜토리얼 자료 (공개)",
        "왜": "웹 액세스 로그 39,532건에 **세션 ID·User-Agent가 있다** — "
              "NASA-HTTP(Common Log Format)에 없는 세션 축을 여기서만 볼 수 있다.",
        "files": [("https://docs.splunk.com/images/Tutorial/tutorialdata.zip",
                   "tutorialdata.zip")],
        "unpack": ("zip", "tutorialdata.zip", "splunk_tutorial"),
    },
    "nasa": {
        "name": "NASA-HTTP (1995년 7월)",
        "size": "20 MB (압축) / 196 MB",
        "license": "Internet Traffic Archive — 공개",
        "왜": "**합성이 아닌 실제 트래픽** 189만 건 · 28일. 요일 주기가 4회 반복돼 "
              "기준선을 세울 수 있다. 🔴 라벨이 없다 — 이상은 심어서 본다.",
        "files": [("https://ita.ee.lbl.gov/traces/NASA_access_log_Jul95.gz",
                   "nasa_http/NASA_access_log_Jul95.gz")],
        "unpack": ("gunzip", "nasa_http/NASA_access_log_Jul95.gz",
                   "nasa_http/NASA_access_log_Jul95.log"),
    },
    "owasp": {
        "name": "OWASP ModSecurity 감사 로그",
        "size": "29 MB (압축) / 380 MB",
        "license": "CC BY 4.0",
        "왜": "실제 프로덕션 WAF가 **차단한** 트랜잭션 142,705건 · 30일. 룰 ID·severity가 "
              "붙어 있다. 🔴 2xx 응답이 0건 — 정상이 없어 기저율·오탐은 못 잰다.",
        "files": [("https://zenodo.org/api/records/17178461/files/owasp.zip/content",
                   "owasp.zip")],
        "unpack": ("zip", "owasp.zip", "owasp"),
    },
    "loghub": {
        "name": "LogHub 샘플 5종",
        "size": "1 MB",
        "license": "logpai/loghub — 공개 (학술 인용)",
        "왜": "형식이 제각각인 시스템 로그를 **같은 파서로 다룰 수 있나**를 보는 벤치마크. "
              "🔴 BGL 라벨은 사람의 정/오탐 판정이 아니라 메시지 종류라 성능 평가엔 못 쓴다.",
        "files": [
            (f"https://raw.githubusercontent.com/logpai/loghub/master/{d}/{d}_2k.log",
             f"loghub/{d}_2k.log")
            for d in ("OpenSSH", "Apache", "Linux", "BGL", "HealthApp")
        ],
    },
}


def _download(url: str, dest: Path) -> None:
    if dest.exists() and dest.stat().st_size > 0:
        print(f"    건너뜀 (이미 있음)  {dest.name}")
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    with requests.get(url, headers=UA, stream=True, timeout=120) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        done = 0
        with tmp.open("wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):
                f.write(chunk)
                done += len(chunk)
                bar = f"{done / 1e6:.0f} MB" + (f" / {total / 1e6:.0f} MB" if total else "")
                print(f"\r    받는 중  {dest.name}  {bar}   ", end="", flush=True)
    tmp.rename(dest)
    print(f"\r    ✅ {dest.name}  ({dest.stat().st_size / 1e6:.1f} MB)        ")


def _unpack(kind: str, src: Path, dest: Path) -> None:
    if kind == "zip":
        if dest.exists() and any(dest.iterdir()):
            print(f"    건너뜀 (이미 풀림)  {dest.name}/")
            return
        dest.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(src) as z:
            z.extractall(dest)
        print(f"    ✅ 풀었음  {dest}/")
    elif kind == "gunzip":
        if dest.exists() and dest.stat().st_size > 0:
            print(f"    건너뜀 (이미 풀림)  {dest.name}")
            return
        with gzip.open(src, "rb") as fi, dest.open("wb") as fo:
            shutil.copyfileobj(fi, fo)
        print(f"    ✅ 풀었음  {dest}  ({dest.stat().st_size / 1e6:.1f} MB)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("keys", nargs="*", help=f"{' · '.join(DATASETS)}")
    ap.add_argument("--all", action="store_true", help="전부 받기")
    ap.add_argument("--list", action="store_true", help="내려받지 않고 목록만")
    args = ap.parse_args()

    if args.list or (not args.keys and not args.all):
        print(f"\n데이터 위치: {DATA}\n")
        for key, spec in DATASETS.items():
            print(f"  {key:<16} {spec['size']:>18}  {spec['name']}")
            print(f"  {'':<16} {'':>18}  [{spec['license']}]")
        print("\n사용:  uv run python scripts/fetch_weblogs.py <key> [<key> ...]")
        print("       uv run python scripts/fetch_weblogs.py --all\n")
        return

    keys = list(DATASETS) if args.all else args.keys
    unknown = [k for k in keys if k not in DATASETS]
    if unknown:
        raise SystemExit(f"모르는 key: {', '.join(unknown)}  (--list 로 확인)")

    for key in keys:
        spec = DATASETS[key]
        print(f"\n▶ {key} — {spec['name']}  [{spec['license']}]")
        for url, rel in spec["files"]:
            _download(url, DATA / rel)
        if "unpack" in spec:
            kind, src, dest = spec["unpack"]
            _unpack(kind, DATA / src, DATA / dest)

    print(f"\n✅ 끝. 받은 곳: {DATA}")


if __name__ == "__main__":
    main()
