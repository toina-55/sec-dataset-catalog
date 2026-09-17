"""데이터셋 17종 받는 단일 진입점 — 어느 것이든 여기서 받습니다.

    uv run python fetch.py --list              # 17종 목록 + 용량
    uv run python fetch.py nasa loghub         # 골라서
    uv run python fetch.py --group 메일        # 묶음으로
    uv run python fetch.py --all               # 전부 (약 11.3 GB, 확인을 묻습니다)
    uv run python fetch.py nasa --dry-run      # 실행할 명령만 보기

실제 다운로드는 `scripts/` 아래 6개 스크립트가 합니다. 이 파일은 **어느 key가 어느
스크립트의 어느 인자인지**만 알고 넘깁니다 — 스크립트들은 각각 원출처(Zenodo · figshare ·
AWS Open Data · GitHub raw)의 사정이 달라 한 파일로 합치면 읽기 어려워집니다.

받은 파일은 전부 `data/` 아래에 쌓이고, 모든 스크립트가 캐시 우선이라 다시 실행해도
이미 받은 건 건너뜁니다.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SCRIPTS = ROOT / "scripts"

# key: (이름, 묶음, 내려받는 용량 GB, 라이선스, 스크립트, 인자)
#   "multi": 같은 스크립트에 key를 여러 개 붙여 한 번에 실행할 수 있습니다
REGISTRY = {
    "cicids2017": {
        "name": "CIC-IDS2017", "group": "네트워크", "gb": 0.37,
        "license": "원 배포처 미명시",
        "script": "fetch_weblogs.py", "arg": "cicids2017", "multi": True},
    "ait-nds": {
        "name": "AIT-NDS (넷플로)", "group": "네트워크", "gb": 0.27,
        "license": "CC BY 4.0",
        "script": "fetch_ait.py", "arg": "nds", "multi": True},
    "ids2018": {
        "name": "CSE-CIC-IDS2018", "group": "네트워크", "gb": 4.05,
        "license": "AWS Open Data (인용 요구)",
        "script": "fetch_ids2018.py", "flags": []},
    "splunk-tutorial": {
        "name": "Splunk 검색 튜토리얼", "group": "웹 로그", "gb": 0.011,
        "license": "Splunk 공식 자료 (공개)",
        "script": "fetch_weblogs.py", "arg": "splunk-tutorial", "multi": True},
    "nasa": {
        "name": "NASA-HTTP", "group": "웹 로그", "gb": 0.021,
        "license": "Internet Traffic Archive (공개)",
        "script": "fetch_weblogs.py", "arg": "nasa", "multi": True},
    "owasp": {
        "name": "OWASP ModSecurity", "group": "웹 로그", "gb": 0.030,
        "license": "CC BY 4.0",
        "script": "fetch_weblogs.py", "arg": "owasp", "multi": True},
    "loghub": {
        "name": "LogHub 샘플 5종", "group": "시스템·장비", "gb": 0.001,
        "license": "공개 (학술 인용)",
        "script": "fetch_weblogs.py", "arg": "loghub", "multi": True},
    "ait-ads": {
        "name": "AIT-ADS (IDS 알럿)", "group": "시스템·장비", "gb": 0.10,
        "license": "CC BY 4.0",
        "script": "fetch_ait.py", "arg": "ads", "multi": True},
    "smd": {
        "name": "SMD (서버 28대)", "group": "시스템·장비", "gb": 0.49,
        "license": "MIT",
        "script": "fetch_smd.py", "flags": []},
    "cert": {
        "name": "CERT r4.2 (+정답)", "group": "사용자 행위", "gb": 4.82,
        "license": "⚠️ CC BY 4.0 + 최종사용자 동의",
        "script": "fetch_cert.py", "flags": []},
    "clue": {
        "name": "CLUE-LDS", "group": "사용자 행위", "gb": 0.64,
        "license": "CC BY 4.0",
        "script": "fetch_ait.py", "arg": "clue", "multi": True},
    "nazario": {
        "name": "Nazario Phishing", "group": "메일", "gb": 0.019,
        "license": "CC BY 4.0",
        "script": "fetch_mail.py", "arg": "nazario", "multi": True},
    "spamassassin": {
        "name": "SpamAssassin easy_ham_2", "group": "메일", "gb": 0.001,
        "license": "Apache 공개 코퍼스",
        "script": "fetch_mail.py", "arg": "spamassassin", "multi": True},
    "enron": {
        "name": "Enron Email", "group": "메일", "gb": 0.443,
        "license": "공개",
        "script": "fetch_mail.py", "arg": "enron", "multi": True},
    "sms-spam": {
        "name": "UCI SMS Spam", "group": "메일", "gb": 0.0002,
        "license": "CC BY 4.0",
        "script": "fetch_mail.py", "arg": "sms-spam", "multi": True},
    "phishtank": {
        "name": "PhishTank 🟡", "group": "피드", "gb": 0.015,
        "license": "공개 (rate limit)",
        "script": "fetch_phishing_feeds.py", "flags": []},
    "tranco": {
        "name": "Tranco top-1m 🟡", "group": "피드", "gb": 0.023,
        "license": "공개",
        "script": "fetch_phishing_feeds.py", "flags": []},
}

GROUPS = ("네트워크", "웹 로그", "시스템·장비", "사용자 행위", "메일", "피드")


def show_list() -> None:
    print(f"\n데이터 위치: {ROOT / 'data'}\n")
    for group in GROUPS:
        print(f"  [{group}]")
        for key, s in REGISTRY.items():
            if s["group"] != group:
                continue
            gb = f"{s['gb']:.2f} GB" if s["gb"] >= 0.01 else "< 0.01 GB"
            print(f"    {key:<17} {gb:>10}   {s['name']}  [{s['license']}]")
        print()
    total = sum(s["gb"] for s in REGISTRY.values())
    print(f"  전부 받으면 약 {total:.1f} GB\n")
    print("  🟡 피드형(phishtank · tranco)은 받을 때마다 값이 다릅니다 — 인용 시 수신 날짜를 병기해 주세요")
    print("  ⚠️ cert는 받는 쪽(kilthub)에서 별도 최종사용자 동의를 거칩니다\n")


def plan(keys: list[str]) -> list[tuple[str, list[str]]]:
    """key 목록을 실제 실행할 (스크립트, 인자) 목록으로 바꿉니다. 같은 스크립트는 묶습니다."""
    calls: list[tuple[str, list[str]]] = []
    for key in keys:
        s = REGISTRY[key]
        script = s["script"]
        if s.get("multi"):
            for i, (sc, args) in enumerate(calls):
                if sc == script:
                    calls[i] = (sc, args + [s["arg"]])
                    break
            else:
                calls.append((script, [s["arg"]]))
        else:
            flags = list(s.get("flags", []))
            if (script, flags) not in calls:
                calls.append((script, flags))
    return calls


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("keys", nargs="*", help="받을 데이터셋 key (--list 로 확인하세요)")
    ap.add_argument("--all", action="store_true", help="17종 전부 (약 11.3 GB)")
    ap.add_argument("--group", action="append", metavar="이름",
                    help=f"묶음 단위로 받기: {' · '.join(GROUPS)}")
    ap.add_argument("--list", action="store_true", help="받지 않고 목록만")
    ap.add_argument("--dry-run", action="store_true", help="실행할 명령만 보여줍니다")
    ap.add_argument("-y", "--yes", action="store_true", help="용량 확인 질문 건너뛰기")
    args = ap.parse_args()

    keys = list(args.keys)
    if args.group:
        unknown_g = [g for g in args.group if g not in GROUPS]
        if unknown_g:
            print(f"🔴 모르는 묶음: {', '.join(unknown_g)}", file=sys.stderr)
            print(f"   쓸 수 있는 묶음: {' · '.join(GROUPS)}", file=sys.stderr)
            return 2
        keys += [k for k, s in REGISTRY.items() if s["group"] in args.group]
    if args.all:
        keys = list(REGISTRY)

    if args.list or not keys:
        show_list()
        print("사용:  uv run python fetch.py <key> [<key> ...]")
        print("       uv run python fetch.py --group 메일")
        print("       uv run python fetch.py --all\n")
        return 0

    unknown = [k for k in keys if k not in REGISTRY]
    if unknown:
        print(f"🔴 모르는 key: {', '.join(unknown)}  (--list 로 확인하세요)", file=sys.stderr)
        return 2

    seen: dict[str, None] = dict.fromkeys(keys)   # 중복 제거, 순서 유지
    keys = list(seen)
    calls = plan(keys)
    total = sum(REGISTRY[k]["gb"] for k in keys)

    print(f"\n받을 것 {len(keys)}종 · 약 {total:.2f} GB")
    for k in keys:
        print(f"  · {k:<17} {REGISTRY[k]['name']}")
    print(f"\n실행할 명령 {len(calls)}개:")
    for script, a in calls:
        print(f"  $ python scripts/{script} {' '.join(a)}".rstrip())

    if args.dry_run:
        return 0

    if total >= 1.0 and not args.yes:
        try:
            answer = input(f"\n{total:.1f} GB를 받습니다. 계속할까요? [y/N] ").strip().lower()
        except EOFError:
            answer = ""
        if answer not in ("y", "yes"):
            print("중단했습니다.")
            return 1

    failed: list[str] = []
    for script, a in calls:
        print(f"\n{'=' * 60}\n▶ scripts/{script} {' '.join(a)}\n{'=' * 60}")
        rc = subprocess.call([sys.executable, str(SCRIPTS / script), *a])
        if rc != 0:
            failed.append(script)
            print(f"🔴 실패 (종료 코드 {rc}): {script}", file=sys.stderr)

    if failed:
        print(f"\n🔴 {len(failed)}개 실패: {', '.join(failed)} — 다시 실행하면 "
              f"받은 건 건너뛰고 실패한 것만 다시 받습니다", file=sys.stderr)
        return 1
    print(f"\n✅ 끝. 받은 곳: {ROOT / 'data'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
