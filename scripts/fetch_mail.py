"""메일·문자 데이터 4종 확보 — 원출처 직접 다운로드, 캐시 우선.

피싱 메일 원문(Nazario) · 정상 메일 원문(SpamAssassin) · 짧은 텍스트 대조군(UCI SMS
Spam) · 기업 사서함 구조(Enron).

    uv run python scripts/fetch_mail.py --list                  # 목록만
    uv run python scripts/fetch_mail.py nazario spamassassin    # 골라서
    uv run python scripts/fetch_mail.py --all                   # 전부 (약 0.46 GB)

🔴 **Enron은 443 MB다.** `--all`에 들어가 있으니 용량을 보고 실행할 것.
🟡 Nazario 2025 수집분에는 **수집 측 rspamd의 판정 헤더가 남아 있다.** 헤더 기반
   피처를 쓰면 정답이 새어 들어간다 — 본문·URL 축만 쓰거나 해당 헤더를 지워야 한다.
"""
from __future__ import annotations

import argparse
import shutil
import tarfile
import zipfile
from pathlib import Path

import requests

DATA = Path(__file__).resolve().parent.parent / "data"
UA = {"User-Agent": "Mozilla/5.0 (compatible; sec-dataset-catalog)"}

DATASETS = {
    "nazario": {
        "name": "Nazario Phishing Corpus (2025 수집분)",
        "size": "19 MB",
        "license": "CC BY 4.0 (배포처 LICENSE.txt)",
        "왜": "**실제 피싱 메일 원문** 481통. 표시명/도메인 불일치, 본문 URL 호스트까지 "
              "원문 그대로 남아 있다.",
        "files": [("https://monkey.org/~jose/phishing/phishing-2025",
                   "nazario-phishing-2025.mbox")],
    },
    "spamassassin": {
        "name": "SpamAssassin easy_ham_2 (정상 메일)",
        "size": "1 MB",
        "license": "Apache SpamAssassin Public Corpus — 공개",
        "왜": "피싱과 맞댈 **정상 메일 원문** 1,401통. 🔴 2003년 자료이고 개인 메일 "
              "성격이라 *조직 안에서 누가 누구에게* 는 볼 수 없다 — 그건 Enron 쪽이다.",
        "files": [("https://spamassassin.apache.org/old/publiccorpus/"
                   "20030228_easy_ham_2.tar.bz2", "sa-ham.tar.bz2")],
        "unpack": ("tar", "sa-ham.tar.bz2", "."),
    },
    "sms-spam": {
        "name": "UCI SMS Spam Collection",
        "size": "0.2 MB",
        "license": "UCI ML Repository — 공개 (CC BY 4.0)",
        "왜": "**본문만 있는 짧은 텍스트**의 대조군. 메일이 아니라 문자이고 대량 살포형이라 "
              "표적형과는 다르다 — 규칙이 형식에 얼마나 기대고 있는지 드러난다.",
        "files": [("https://archive.ics.uci.edu/static/public/228/sms+spam+collection.zip",
                   "sms-spam.zip")],
        "unpack": ("zip-pick", "sms-spam.zip", "SMSSpamCollection:sms-spam.tsv"),
    },
    "enron": {
        "name": "Enron Email Dataset (2015-05-07 판)",
        "size": "443 MB",
        "license": "공개 (미 연방에너지규제위원회 공개 자료 기반)",
        "왜": "**실제 기업의 사서함 151개가 통째로** 있는 거의 유일한 공개 자료. "
              "발신 패턴·수신자 관계의 정상 기준선을 세울 수 있다.",
        "files": [("https://www.cs.cmu.edu/~enron/enron_mail_20150507.tar.gz",
                   "enron.tar.gz")],
        # 압축 해제는 기본값에서 뺐다 — 풀면 2.6 GB · 파일 50만 개다.
    },
}


def _download(url: str, dest: Path) -> None:
    if dest.exists() and dest.stat().st_size > 0:
        print(f"    건너뜀 (이미 있음)  {dest.name}")
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    with requests.get(url, headers=UA, stream=True, timeout=180) as r:
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


def _unpack(kind: str, src: Path, spec: str) -> None:
    if kind == "tar":
        dest = DATA / spec
        with tarfile.open(src) as t:
            names = t.getnames()
            top = DATA / names[0].split("/")[0]
            if top.exists() and any(top.iterdir()):
                print(f"    건너뜀 (이미 풀림)  {top.name}/")
                return
            t.extractall(dest, filter="data")
        print(f"    ✅ 풀었음  {top}/  ({len(names)}개)")
    elif kind == "zip-pick":
        member, out_rel = spec.split(":")
        out = DATA / out_rel
        if out.exists() and out.stat().st_size > 0:
            print(f"    건너뜀 (이미 풀림)  {out.name}")
            return
        with zipfile.ZipFile(src) as z, z.open(member) as fi, out.open("wb") as fo:
            shutil.copyfileobj(fi, fo)
        print(f"    ✅ 풀었음  {out}  ({out.stat().st_size / 1e6:.1f} MB)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("keys", nargs="*", help=f"{' · '.join(DATASETS)}")
    ap.add_argument("--all", action="store_true", help="전부 받기 (Enron 443 MB 포함)")
    ap.add_argument("--list", action="store_true", help="내려받지 않고 목록만")
    args = ap.parse_args()

    if args.list or (not args.keys and not args.all):
        print(f"\n데이터 위치: {DATA}\n")
        for key, spec in DATASETS.items():
            print(f"  {key:<14} {spec['size']:>8}  {spec['name']}")
            print(f"  {'':<14} {'':>8}  [{spec['license']}]")
        print("\n사용:  uv run python scripts/fetch_mail.py <key> [<key> ...]")
        print("       uv run python scripts/fetch_mail.py --all      # Enron 443 MB 포함\n")
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
            kind, src, arg = spec["unpack"]
            _unpack(kind, DATA / src, arg)

    print(f"\n✅ 끝. 받은 곳: {DATA}")


if __name__ == "__main__":
    main()
