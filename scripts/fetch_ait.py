"""AIT 계열 공개 데이터 확보 — Zenodo API 경유, 캐시 우선.

AIT(Austrian Institute of Technology)가 낸 한 계열의 로그 데이터셋들이다.
같은 테스트베드 8개(fox · harrison · russellmitchell · santos · shaw · wardbeck ·
wheeler · wilson)에서 나왔고, 가공 단계만 다르다.

    원본 로그(LDS) ──▶ 넷플로(NDS) ──▶ IDS 알럿(ADS)

🔴 라이선스가 갈린다. 원본 로그만 **비영리(NC)** 다.
   파생본 셋(NDS · ADS · CLUE)은 저작자 표시만 하면 된다.
   이 프로젝트는 유상 용역이므로 기본값은 **CC BY 셋만** 받는다.

사용:
    uv run python 시나리오/fetch_ait.py                # 기본 3종 (약 1.0 GB)
    uv run python 시나리오/fetch_ait.py nds            # 하나만
    uv run python 시나리오/fetch_ait.py nds --testbed fox,wilson
    uv run python 시나리오/fetch_ait.py --list         # 내려받지 않고 목록만
    uv run python 시나리오/fetch_ait.py lds --allow-nc # 🔴 비영리 데이터
"""
from __future__ import annotations

import argparse
import hashlib
import shutil
import sys
import zipfile
from pathlib import Path

import requests

DATA = Path(__file__).resolve().parent.parent / "data"
API = "https://zenodo.org/api/records/{}"
TESTBEDS = ("fox", "harrison", "russellmitchell", "santos",
            "shaw", "wardbeck", "wheeler", "wilson")

DATASETS = {
    "nds": {
        "record": 13168643,
        "name": "AIT Netflow Data Set",
        "dest": "ait_nds",
        "license": "CC BY 4.0",
        "nc": False,
        "요건": "3 — 이상 트래픽",
        "왜": "라벨된 넷플로. **테스트베드 8개**라 규칙이 다른 망에서도 서는지 잴 수 있고, "
              "**데이터 반출(DNSteal)이 라벨로 있다** — CIC-IDS2017에서 36건뿐이던 축이다.",
        "cite": "Landauer et al., AIT Netflow Data Set (Zenodo, 2024)",
    },
    "ads": {
        "record": 8263181,
        "name": "AIT Alert Data Set",
        "dest": "ait_ads",
        "license": "CC BY 4.0",
        "nc": False,
        "요건": "6 — 보안장비 이상동작 · 정규화 실습",
        "왜": "IDS 3종(Suricata · Wazuh · AMiner) 알럿 265만 건. **포맷이 서로 다르고** "
              "정상 행위에서 나온 오탐이 섞여 있다 — 필드명 정합 문제의 실물이다.",
        "cite": "Landauer, Skopik, Wurzenberger, AIT Alert Data Set (Zenodo, 2023)",
    },
    "clue": {
        "record": 7119953,
        "name": "CLUE-LDS (Cloud-based UEBA Log Data Set)",
        "dest": "clue_lds",
        "license": "CC BY 4.0",
        "nc": False,
        "요건": "4 — 내부유출 이상징후",
        "왜": "**실제 사용자** 5,000명 · 5년(1,910일) · 5,000만 건. 요건서의 "
              "*'사용자별 3개월 평균×3'* 을 백분위수와 맞대려면 **분포가 실제여야 한다** — "
              "합성 데이터는 분포를 설계한 사람이 만든 것이라 근거가 안 된다.",
        "cite": "Landauer et al., CLUE-LDS (Zenodo, 2022)",
    },
    "lds": {
        "record": 19483937,
        "name": "AIT Log Data Set V2.1",
        "dest": "ait_lds_v21",
        "license": "CC BY-NC-SA 4.0",
        "nc": True,
        "only": lambda key: key.endswith("_no-pcaps.zip"),   # pcap 제외본만
        "요건": "5 · 6 — 메일(exim) · 감사 로그",
        "왜": "원본 로그. Apache·auth·DNS·VPN·audit·Suricata·exim·syslog. "
              "🔴 **비영리 조항이 붙어 있어 기본값에서 뺐다.**",
        "cite": "Landauer et al., AIT Log Data Set V2.1 (Zenodo, 2026)",
    },
}
DEFAULT = ["nds", "ads", "clue"]


def _files(record: int) -> list[dict]:
    r = requests.get(API.format(record), timeout=60)
    r.raise_for_status()
    return r.json()["files"]


def _md5(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


RETRIES = 4          # Zenodo는 큰 파일에서 간헐적으로 끊긴다
CHUNK = 1 << 20


def _download(url: str, dest: Path, size: int, checksum: str) -> None:
    """이어받기 + 재시도. 중간에 끊겨도 받은 데까지는 버리지 않는다."""
    if dest.exists() and dest.stat().st_size == size:
        print(f"      캐시  {dest.name}")
        return
    tmp = dest.with_suffix(dest.suffix + ".part")

    for attempt in range(1, RETRIES + 1):
        done = tmp.stat().st_size if tmp.exists() else 0
        if done > size:                      # 이상한 잔여물은 버린다
            tmp.unlink(); done = 0
        if done == size:
            break
        headers = {"Range": f"bytes={done}-"} if done else {}
        try:
            with requests.get(url, stream=True, timeout=(30, 120), headers=headers) as r:
                # 206이면 이어받기가 먹혔다. 200이면 서버가 처음부터 다시 준다
                if done and r.status_code == 200:
                    tmp.unlink(missing_ok=True); done = 0
                r.raise_for_status()
                with tmp.open("ab" if done else "wb") as f:
                    for chunk in r.iter_content(CHUNK):
                        f.write(chunk)
                        done += len(chunk)
                        print(f"\r      받는 중  {dest.name}  {done/1e6:7.1f} / {size/1e6:.1f} MB "
                              f"({done/size*100 if size else 0:5.1f}%)", end="", flush=True)
            print()
            break
        except (requests.RequestException, OSError) as e:
            print(f"\n      🟡 {dest.name} {attempt}/{RETRIES}회차 끊김 ({type(e).__name__}) "
                  f"— {done/1e6:.1f} MB 까지 받아 뒀다. 이어서 재시도")
            if attempt == RETRIES:
                raise

    want = checksum.split(":", 1)[-1]
    got = _md5(tmp)
    if got != want:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"{dest.name}: md5 불일치 (기대 {want}, 실제 {got}). "
                           f"받다 만 파일을 지웠으니 다시 실행하면 처음부터 받는다")
    tmp.rename(dest)


def _unzip(zpath: Path, out: Path) -> None:
    """zip을 전개한다. 안에 최상위 폴더가 하나뿐이면 그 한 겹을 벗긴다.

    벗기지 않으면 `data/ait_ads/ait_ads/...` 처럼 같은 이름이 두 번 나온다.
    """
    marker = out / ".extracted"
    if marker.exists():
        print(f"      전개됨  {out.relative_to(DATA)}/")
        return
    with zipfile.ZipFile(zpath) as z:
        names = [n for n in z.namelist()
                 if not n.startswith("__MACOSX") and not n.endswith("/")]
        tops = {n.split("/", 1)[0] for n in names}
        strip = len(tops) == 1 and all("/" in n for n in names)
        out.mkdir(parents=True, exist_ok=True)
        for n in names:
            rel = n.split("/", 1)[1] if strip else n
            target = out / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            with z.open(n) as src, target.open("wb") as dst:
                shutil.copyfileobj(src, dst)
    marker.touch()
    print(f"      전개함  {out.relative_to(DATA)}/  ({len(names)}개)")


def _write_source_note(root: Path, spec: dict) -> None:
    """repo README 규칙 — 데이터셋마다 라이선스·이용조건을 폴더에 남긴다."""
    (root / "출처.md").write_text(
        f"# {spec['name']}\n\n"
        f"- **Zenodo**: https://zenodo.org/records/{spec['record']}\n"
        f"- **라이선스**: {spec['license']}"
        f"{'  🔴 **비영리(NonCommercial)** — 유상 용역 산출물에 쓰기 전 확인 필요' if spec['nc'] else ''}\n"
        f"- **인용**: {spec['cite']}\n"
        f"- **관련 요건**: {spec['요건']}\n\n"
        f"{spec['왜']}\n\n"
        f"> 받은 방법: `uv run python 시나리오/fetch_ait.py`\n",
        encoding="utf-8")


def fetch(key: str, testbeds: list[str] | None, keep_zip: bool) -> None:
    spec = DATASETS[key]
    root = DATA / spec["dest"]
    root.mkdir(parents=True, exist_ok=True)
    print(f"\n── {key}  {spec['name']}  [{spec['license']}]")

    files = _files(spec["record"])
    if "only" in spec:
        files = [f for f in files if spec["only"](f["key"])]
    if testbeds:
        files = [f for f in files
                 if any(f["key"].startswith(t) for t in testbeds)
                 or not any(f["key"].startswith(t) for t in TESTBEDS)]

    total = sum(f["size"] for f in files)
    print(f"   파일 {len(files)}개 · {total/1e9:.2f} GB")

    # zip이 하나뿐인 레코드는 root에 바로 편다. 여럿이면 zip 이름으로 나눈다
    # (넷플로는 테스트베드별로 8개라 나뉘어야 한다).
    zips = [f for f in files if f["key"].endswith(".zip")]
    flat = len(zips) == 1

    for f in sorted(files, key=lambda x: x["key"]):
        is_zip = f["key"].endswith(".zip")
        out = (root if flat else root / Path(f["key"]).stem) if is_zip else None

        # 🔴 내려받기 전에 먼저 본다 — 전개가 끝났으면 zip을 다시 받을 이유가 없다.
        # (전개 후 zip을 지우므로 파일 크기 캐시만으로는 걸러지지 않는다)
        if is_zip and (out / ".extracted").exists():
            print(f"      전개됨  {out.relative_to(DATA)}/")
            continue
        if not is_zip and (root / f["key"]).exists() \
                and (root / f["key"]).stat().st_size == f["size"]:
            print(f"      캐시  {f['key']}")
            continue

        zdir = root / "_zip"
        zdir.mkdir(exist_ok=True)
        zpath = zdir / f["key"]
        _download(f["links"]["self"], zpath, f["size"], f["checksum"])
        if is_zip:
            _unzip(zpath, out)
            if not keep_zip:
                zpath.unlink()
        else:
            shutil.copy2(zpath, root / f["key"])
    if not keep_zip:
        shutil.rmtree(root / "_zip", ignore_errors=True)
    _write_source_note(root, spec)


def show_list() -> None:
    print("데이터셋 목록 (크기는 Zenodo 기준)\n")
    for key, spec in DATASETS.items():
        files = _files(spec["record"])
        if "only" in spec:
            files = [f for f in files if spec["only"](f["key"])]
        size = sum(f["size"] for f in files)
        mark = "🔴 NC" if spec["nc"] else "  ✅ "
        star = " ★기본" if key in DEFAULT else ""
        print(f"{mark} {key:5s} {size/1e9:6.2f} GB  요건 {spec['요건']}{star}")
        print(f"        {spec['name']}  [{spec['license']}]")
    print(f"\n기본값: {' '.join(DEFAULT)}")


def main() -> int:
    ap = argparse.ArgumentParser(description="AIT 계열 공개 데이터 확보")
    ap.add_argument("keys", nargs="*", default=None, choices=[*DATASETS, []],
                    help=f"받을 데이터셋 (기본 {' '.join(DEFAULT)})")
    ap.add_argument("--testbed", help="쉼표 구분 테스트베드 이름 (nds·lds 에만 해당)")
    ap.add_argument("--allow-nc", action="store_true",
                    help="🔴 비영리 라이선스 데이터셋을 받는다")
    ap.add_argument("--keep-zip", action="store_true", help="전개 후 zip을 남긴다")
    ap.add_argument("--list", action="store_true", help="목록만 출력")
    a = ap.parse_args()

    if a.list:
        show_list()
        return 0

    keys = a.keys or DEFAULT
    blocked = [k for k in keys if DATASETS[k]["nc"] and not a.allow_nc]
    if blocked:
        print(f"🔴 {' '.join(blocked)} 는 비영리(NonCommercial) 라이선스다.")
        print("   유상 용역 산출물에 쓰기 전에 확인이 필요하다.")
        print("   그래도 받으려면 --allow-nc 를 붙인다.")
        return 2

    tb = [t.strip() for t in a.testbed.split(",")] if a.testbed else None
    if tb and (bad := [t for t in tb if t not in TESTBEDS]):
        print(f"🔴 없는 테스트베드: {' '.join(bad)}\n   가능: {' '.join(TESTBEDS)}")
        return 2

    DATA.mkdir(exist_ok=True)
    ok = True
    for k in keys:
        try:
            fetch(k, tb, a.keep_zip)
        except Exception as e:                                  # noqa: BLE001
            print(f"\n🔴 {k} 실패: {e}")
            ok = False
    print("\n완료" if ok else "\n일부 실패")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
