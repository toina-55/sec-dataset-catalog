"""CSE-CIC-IDS2018 확보 — AWS Open Data 공개 버킷(서명 불필요), 캐시 우선.

CIC(캐나다 사이버보안 연구소)와 CSE가 2018년에 만든 침입탐지 데이터셋이다.
피해 조직이 **5개 부서 · PC 420대 · 서버 30대**이고 공격자는 AWS의 여러 대라,
CIC-IDS2017이 못 주던 **분산(N:N) 공격 표본**과 **목적지 장비 구분**이 있다.

🔴 **가공본 CSV 10개 중 `Thuesday-20-02-2018` 하나에만 IP 열이 있다.**
   (`Flow ID` · `Src IP` · `Src Port` · `Dst IP` — 나머지 9개는 `Dst Port`부터 시작한다)
   출발지 IP 없이는 *"단일 및 대역 IP 과접근"* 을 잴 수 없으므로 기본값은 그 파일 하나다.
   그날이 마침 **DDoS-LOIC-HTTP · DDoS-LOIC-UDP** 날이라 분산 공격이 들어 있다.

사용:
    uv run python scripts/fetch_ids2018.py --list     # 목록만 (IP 열 유무 표시)
    uv run python scripts/fetch_ids2018.py            # 기본 1개 (약 4.05 GB)
    uv run python scripts/fetch_ids2018.py --all      # 🔴 10개 전부 (약 6.89 GB)
"""
from __future__ import annotations

import argparse
import re
import urllib.parse
from pathlib import Path

import requests

DATA = Path(__file__).resolve().parent.parent / "data"
DEST = DATA / "ids2018"
BUCKET = "https://cse-cic-ids2018.s3.amazonaws.com"
PREFIX = "Processed Traffic Data for ML Algorithms/"

# 이 파일에만 IP 열이 있다 — 출발지 기준 집계가 되는 유일한 날
WITH_IP = "Thuesday-20-02-2018_TrafficForML_CICFlowMeter.csv"
SCHEDULE = {
    "Wednesday-14-02-2018": "FTP·SSH 무차별 대입",
    "Thursday-15-02-2018": "DoS GoldenEye · Slowloris",
    "Friday-16-02-2018": "DoS SlowHTTPTest · Hulk",
    "Thuesday-20-02-2018": "🎯 **DDoS LOIC-HTTP · LOIC-UDP** (IP 열 있음)",
    "Wednesday-21-02-2018": "DDoS LOIC-UDP · HOIC",
    "Thursday-22-02-2018": "웹 무차별 대입 · XSS · SQL 삽입",
    "Friday-23-02-2018": "웹 공격 (이어서)",
    "Wednesday-28-02-2018": "Infiltration",
    "Thursday-01-03-2018": "Infiltration (이어서)",
    "Friday-02-03-2018": "봇넷 (Zeus · Ares)",
}
CHUNK = 1 << 20
RETRIES = 4


def _listing() -> list[tuple[str, int]]:
    r = requests.get(BUCKET, params={"list-type": "2", "prefix": PREFIX}, timeout=60)
    r.raise_for_status()
    pat = r"<Key>([^<]+)</Key>\s*<LastModified>[^<]+</LastModified>\s*<ETag>[^<]+</ETag>\s*<Size>(\d+)</Size>"
    return [(k, int(s)) for k, s in re.findall(pat, r.text) if k.endswith(".csv")]


def _download(key: str, size: int) -> Path:
    dest = DEST / Path(key).name
    if dest.exists() and dest.stat().st_size == size:
        print(f"      캐시  {dest.name}")
        return dest
    url = f"{BUCKET}/{urllib.parse.quote(key)}"
    tmp = dest.with_suffix(dest.suffix + ".part")

    for attempt in range(1, RETRIES + 1):
        done = tmp.stat().st_size if tmp.exists() else 0
        if done > size:
            tmp.unlink(); done = 0
        if done == size:
            break
        headers = {"Range": f"bytes={done}-"} if done else {}
        try:
            with requests.get(url, stream=True, timeout=(30, 180), headers=headers) as r:
                if done and r.status_code == 200:
                    tmp.unlink(missing_ok=True); done = 0
                r.raise_for_status()
                with tmp.open("ab" if done else "wb") as f:
                    for chunk in r.iter_content(CHUNK):
                        f.write(chunk)
                        done += len(chunk)
                        print(f"\r      받는 중  {dest.name}  {done/1e9:5.2f} / {size/1e9:.2f} GB "
                              f"({done/size*100:5.1f}%)", end="", flush=True)
            print()
            break
        except (requests.RequestException, OSError) as e:
            print(f"\n      🟡 {attempt}/{RETRIES}회차 끊김 ({type(e).__name__}) "
                  f"— {done/1e9:.2f} GB 까지 받아 뒀다. 이어서 재시도")
            if attempt == RETRIES:
                raise
    tmp.rename(dest)
    return dest


def _write_source_note(got: list[str]) -> None:
    (DEST / "출처.md").write_text(
        "# CSE-CIC-IDS2018\n\n"
        "- **출처**: https://registry.opendata.aws/cse-cic-ids2018/ "
        "(원 배포처 https://www.unb.ca/cic/datasets/ids-2018.html)\n"
        "- **라이선스**: AWS Open Data 공개 버킷 · 인용 요구(CIC/CSE)\n"
        "- **인용**: Sharafaldin, Lashkari, Ghorbani, *Toward Generating a New Intrusion "
        "Detection Dataset and Intrusion Traffic Characterization*, ICISSP 2018\n"
        "- **관련 요건**: 3 — 이상 트래픽 (분산 공격 · 목적지 장비 구분)\n\n"
        "피해 조직이 **5개 부서 · PC 420대 · 서버 30대**다. CIC-IDS2017(단일 망·공격자 1대)이 못 주던 "
        "**N:N 분산 공격**과 **목적지 장비/구간 구분**이 여기 있다.\n\n"
        "🔴 **가공본 CSV 10개 중 `Thuesday-20-02-2018` 하나에만 IP 열이 있다.** "
        "나머지는 `Dst Port`부터 시작해서 출발지 기준 집계를 할 수 없다.\n\n"
        f"받은 파일: {', '.join(got)}\n\n"
        "> 받은 방법: `uv run python scripts/fetch_ids2018.py`\n",
        encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--all", action="store_true", help="🔴 10개 전부 (약 6.89 GB)")
    ap.add_argument("--list", action="store_true", help="내려받지 않고 목록만")
    args = ap.parse_args()

    files = _listing()
    if args.list:
        print(f"{'파일':46s} {'크기':>9s}  IP열  그날의 공격")
        for key, size in sorted(files):
            name = Path(key).name
            day = name.replace("_TrafficForML_CICFlowMeter.csv", "")
            print(f"{name:46s} {size/1e9:7.2f} GB  "
                  f"{'✅' if name == WITH_IP else '🔴':4s} {SCHEDULE.get(day, '')}")
        return

    DEST.mkdir(parents=True, exist_ok=True)
    targets = files if args.all else [(k, s) for k, s in files if Path(k).name == WITH_IP]
    got = []
    for key, size in sorted(targets):
        day = Path(key).name.replace("_TrafficForML_CICFlowMeter.csv", "")
        print(f"\n── {day}  [{size/1e9:.2f} GB]  {SCHEDULE.get(day, '')}")
        got.append(_download(key, size).name)

    _write_source_note(got)
    print(f"\n✅ 받은 곳: {DEST}")


if __name__ == "__main__":
    main()
