"""CERT Insider Threat Test Dataset 확보 — figshare API 경유, 캐시 우선.

CMU/SEI가 낸 내부자 위협 합성 데이터셋이다. 릴리스(r1 ~ r6.2)마다 조직 규모와
기록 종류가 다르고, **정답(answers)은 r2부터 붙는다.**

    r1   1,000명 · 18개월 · http/logon/device/LDAP      정답 🔴 없음
    r4.2 1,000명 · 17개월 · + file(파일 복사 내용) · email(수신자·크기·첨부)   정답 ✅ 있음

🔴 r1에는 `file.csv`·`email.csv`가 없어서 요건 4의 조각 3(반출 용량)·4(개인정보 파일)를
   못 쟀다. r4.2가 그 둘과 **정답 라벨**을 함께 준다.

사용:
    uv run python scripts/fetch_cert.py --list          # 목록만
    uv run python scripts/fetch_cert.py                 # 기본 r4.2 + answers
    uv run python scripts/fetch_cert.py r4.2 --with-http  # 🔴 http.csv까지 (전개 용량 큼)
"""
from __future__ import annotations

import argparse
import hashlib
import tarfile
from pathlib import Path

import requests

DATA = Path(__file__).resolve().parent.parent / "data"
ARTICLE = "https://api.figshare.com/v2/articles/12841247"
DEST = DATA / "cert"

# 기본값에서 빼는 것 — 전개 용량이 가장 크고 요건 4에서 안 쓴다
HEAVY = ("http.csv",)

RELEASES = {
    "r1": "1,000명 · 18개월. 🔴 정답 없음 · file/email 없음 (이미 받아 둔 것)",
    "r4.2": "1,000명 · 17개월. ✅ 정답 있음 · **file.csv(파일 복사 내용) · email.csv(크기·첨부)**",
    "r5.2": "2,000명 · 18개월. r4.2와 같은 구성, 조직이 두 배",
    "answers": "릴리스별 정답(인사이더 명단·시나리오). r1용은 들어 있지 않다",
}
DEFAULT = ["r4.2", "answers"]
RETRIES = 4
CHUNK = 1 << 20


def _files() -> dict[str, dict]:
    r = requests.get(ARTICLE, timeout=60)
    r.raise_for_status()
    return {f["name"]: f for f in r.json()["files"]}


def _md5(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()


def _download(spec: dict, dest: Path) -> Path:
    """이어받기 + 재시도. 중간에 끊겨도 받은 데까지는 버리지 않는다."""
    size = spec["size"]
    if dest.exists() and dest.stat().st_size == size:
        print(f"      캐시  {dest.name}")
        return dest
    tmp = dest.with_suffix(dest.suffix + ".part")

    for attempt in range(1, RETRIES + 1):
        done = tmp.stat().st_size if tmp.exists() else 0
        if done > size:
            tmp.unlink(); done = 0
        if done == size:
            break
        headers = {"Range": f"bytes={done}-"} if done else {}
        try:
            with requests.get(spec["download_url"], stream=True,
                              timeout=(30, 180), headers=headers) as r:
                if done and r.status_code == 200:      # 서버가 이어받기를 안 받아준 경우
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
            print(f"\n      🟡 {dest.name} {attempt}/{RETRIES}회차 끊김 ({type(e).__name__}) "
                  f"— {done/1e9:.2f} GB 까지 받아 뒀다. 이어서 재시도")
            if attempt == RETRIES:
                raise

    want = spec.get("computed_md5") or spec.get("supplied_md5")
    if want:
        got = _md5(tmp)
        if got != want:
            tmp.unlink(missing_ok=True)
            raise RuntimeError(f"{dest.name}: md5 불일치 (기대 {want}, 실제 {got}). "
                               "받다 만 파일을 지웠으니 다시 실행하면 처음부터 받는다")
    tmp.rename(dest)
    return dest


def _extract(tar_path: Path, with_http: bool) -> None:
    """tar.bz2를 전개한다. 기본값은 http.csv를 빼고 전개한다(전개 용량이 가장 크다)."""
    out = DEST
    marker = out / f".extracted-{tar_path.name}"
    if marker.exists():
        print(f"      전개됨  {tar_path.name}")
        return
    skipped = 0
    with tarfile.open(tar_path, "r:bz2") as t:
        for m in t:
            if not with_http and Path(m.name).name in HEAVY:
                skipped += 1
                continue
            t.extract(m, out, filter="data")
    marker.touch()
    msg = f"      전개함  {tar_path.name}"
    if skipped:
        msg += f"  (http.csv {skipped}개는 건너뜀 — `--with-http`로 받는다)"
    print(msg)


def _write_source_note() -> None:
    (DEST / "출처.md").write_text(
        "# CERT Insider Threat Test Dataset\n\n"
        "- **출처**: https://kilthub.cmu.edu/articles/dataset/Insider_Threat_Test_Dataset/12841247\n"
        "- **라이선스**: CC BY 4.0 (+ ExactData 최종사용자 동의)\n"
        "- **인용**: Glasser & Lindauer, *Bridging the Gap: A Pragmatic Approach to "
        "Generating Insider Threat Data*, IEEE S&P Workshops 2013\n"
        "- **관련 요건**: 4 — 내부유출 이상징후\n\n"
        "🔴 **합성 데이터다.** 조직·사람·행위가 전부 생성된 것이고, 분포는 만든 사람이 정했다.\n\n"
        "| 릴리스 | 무엇이 다른가 |\n| --- | --- |\n"
        "| `r1/` | 1,000명 · 18개월. http · logon · device · LDAP. 🔴 **정답 없음** |\n"
        "| `r4.2/` | 1,000명 · 17개월. + **file.csv**(파일 복사 내용) · **email.csv**(수신자·크기·첨부). "
        "✅ 정답은 `answers/`에 있다 |\n\n"
        "> 받은 방법: `uv run python scripts/fetch_cert.py`\n"
        "> 기본값은 `http.csv`를 빼고 전개한다(전개 용량이 가장 크고 요건 4에서 안 쓴다). "
        "필요하면 `--with-http`.\n",
        encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("releases", nargs="*", default=DEFAULT,
                    help=f"기본값: {' '.join(DEFAULT)}")
    ap.add_argument("--list", action="store_true", help="내려받지 않고 목록만")
    ap.add_argument("--with-http", action="store_true",
                    help="🔴 http.csv까지 전개한다 (전개 용량이 크게 는다)")
    ap.add_argument("--keep-archive", action="store_true", help="전개 후 tar.bz2를 남긴다")
    args = ap.parse_args()

    files = _files()
    if args.list:
        print(f"{'파일':22s} {'크기':>10s}  설명")
        for name, spec in files.items():
            key = name.replace(".tar.bz2", "")
            print(f"{name:22s} {spec['size']/1e9:8.2f} GB  {RELEASES.get(key, '')}")
        return

    DEST.mkdir(parents=True, exist_ok=True)
    for rel in args.releases:
        name = f"{rel}.tar.bz2"
        if name not in files:
            raise SystemExit(f"🔴 {name} 이 목록에 없다. `--list` 로 확인한다")
        print(f"\n── {rel}  [{files[name]['size']/1e9:.2f} GB]  {RELEASES.get(rel, '')}")
        tar_path = _download(files[name], DEST / name)
        _extract(tar_path, args.with_http)
        if not args.keep_archive:
            tar_path.unlink(missing_ok=True)
            print(f"      압축본 삭제  {name}  (다시 받으려면 이 스크립트를 다시 돌린다)")

    _write_source_note()
    print(f"\n✅ 받은 곳: {DEST}")


if __name__ == "__main__":
    main()
