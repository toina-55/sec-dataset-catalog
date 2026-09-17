"""SMD (Server Machine Dataset) 확보 — GitHub raw 경유, 캐시 우선.

중국 인터넷 기업(원 논문엔 이름이 없다)의 서버 **28대**에서 5주간 뽑은 38개 지표
시계열이다. 요건 6의 hostperf(호스트 **1대**)가 못 주던 **장비 간 비교**가 여기 있다.

    train/               정상 구간만 (기준선 학습용)
    test/                이상이 섞인 구간
    test_label/          test와 같은 길이 — 0/1 (이상 여부)
    interpretation_label/ 이상 구간마다 **어느 지표(1~38)가 원인인지**까지

🔴 지표 이름이 없다(그냥 1~38번). 시간 간격도 원 논문 기준 "1분"으로 알려져 있을 뿐
   타임스탬프가 없다 — 행 번호가 곧 시간이다.

사용:
    uv run python 시나리오/fetch_smd.py --list    # 목록만
    uv run python 시나리오/fetch_smd.py           # 28대 전부 (약 0.49 GB)
    uv run python 시나리오/fetch_smd.py --machines machine-1-1,machine-2-3
"""
from __future__ import annotations

import argparse
from pathlib import Path

import requests

DATA = Path(__file__).resolve().parent.parent / "data"
DEST = DATA / "smd"
RAW = "https://raw.githubusercontent.com/NetManAIOps/OmniAnomaly/master/ServerMachineDataset"
API_TREE = "https://api.github.com/repos/NetManAIOps/OmniAnomaly/git/trees/master?recursive=1"

SUBDIRS = ("train", "test", "test_label", "interpretation_label")
GROUPS = {"1": 8, "2": 9, "3": 11}  # machine-<group>-<index>, 인덱스는 1부터


def _machine_names() -> list[str]:
    names = []
    for g, n in GROUPS.items():
        for i in range(1, n + 1):
            names.append(f"machine-{g}-{i}")
    return sorted(names)


def _download(url: str, dest: Path) -> None:
    if dest.exists() and dest.stat().st_size > 0:
        return
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    dest.write_bytes(r.content)


def _write_source_note() -> None:
    (DEST / "출처.md").write_text(
        "# SMD (Server Machine Dataset)\n\n"
        "- **출처**: https://github.com/NetManAIOps/OmniAnomaly (`ServerMachineDataset/`)\n"
        "- **라이선스**: MIT\n"
        "- **인용**: Su et al., *Robust Anomaly Detection for Multivariate Time Series through "
        "Stochastic Recurrent Neural Network*, KDD 2019\n"
        "- **관련 요건**: 6 — 보안장비 이상동작 (장비 간 비교)\n\n"
        "서버 **28대**(3개 그룹) · 5주 · 38개 지표(이름 없음, 이미 0~1로 정규화됨) · "
        "**이상 라벨 + 원인 지표까지** 있다.\n\n"
        "| 폴더 | 내용 |\n| --- | --- |\n"
        "| `train/` | 정상 구간만 |\n"
        "| `test/` | 이상이 섞인 구간 |\n"
        "| `test_label/` | test와 같은 길이, 0/1 |\n"
        "| `interpretation_label/` | `<시작>-<끝>:<지표번호,...>` — 이상 구간마다 원인 지표 |\n\n"
        "> 받은 방법: `uv run python 시나리오/fetch_smd.py`\n",
        encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--machines", help="쉼표로 구분 (기본: 28대 전부)")
    ap.add_argument("--list", action="store_true", help="내려받지 않고 목록만")
    args = ap.parse_args()

    all_names = _machine_names()
    if args.list:
        print(f"머신 {len(all_names)}대: {', '.join(all_names)}")
        return

    names = args.machines.split(",") if args.machines else all_names
    DEST.mkdir(parents=True, exist_ok=True)
    for sub in SUBDIRS:
        (DEST / sub).mkdir(exist_ok=True)

    for i, name in enumerate(names, 1):
        print(f"\r받는 중  {i}/{len(names)}  {name}", end="", flush=True)
        for sub in SUBDIRS:
            _download(f"{RAW}/{sub}/{name}.txt", DEST / sub / f"{name}.txt")
    print()

    _write_source_note()
    print(f"✅ 받은 곳: {DEST}  ({len(names)}대 × {len(SUBDIRS)}종)")


if __name__ == "__main__":
    main()
