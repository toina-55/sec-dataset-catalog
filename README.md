# sec-dataset-catalog

보안 로그·이상탐지 연구에서 실제로 써본 **공개 데이터셋 카탈로그**. 각 데이터셋이 무엇이고, 규모·라벨이 어떤지, 어디서 어떻게 받는지를 정리한다.

**이 저장소가 하는 일 / 안 하는 일**

- ✅ 데이터셋 설명, 라이선스, 받는 방법(스크립트 또는 안내)을 공유한다
- ❌ **데이터 파일 자체는 커밋·재배포하지 않는다.** `scripts/`의 스크립트는 각자 원출처(Zenodo·GitHub·AWS Open Data 등)에서 직접 받아온다 — 이 저장소는 "어디서 어떻게 받는지"만 알려준다
- ⚠️ 라이선스는 **원출처 기준**이다. 아래 표의 라이선스 표기를 반드시 확인하고, 상업적 이용이 걸린 경우 원문 약관을 직접 재확인할 것

## 시작하기

```bash
git clone <이 repo>
cd sec-dataset-catalog
uv sync
uv run python scripts/fetch_ait.py --list      # 예시 — 다운로드 없이 목록만 보기
```

각 스크립트는 캐시 우선이라 다시 실행해도 이미 받은 파일은 건너뛴다. `--list`로 먼저 확인하고 받는 걸 권한다.

---

## 네트워크 플로우

### CIC-IDS2017
캐나다 사이버보안 연구소(University of New Brunswick)가 2017년 공개한 네트워크 침입탐지 벤치마크. 월요일 정상 트래픽 + 화~금 공격(브루트포스·DoS/DDoS·웹공격·Infiltration·봇넷·포트스캔) 주입 구조. `CICFlowMeter`로 추출한 84열 플로우 통계.
- **규모**: 283만 행, 라벨 14종(공격 비율 19.7%)
- **출처**: 원 배포처는 폼 제출 필요 — HuggingFace 미러 사용 권장
- **받는 법**: 수동 (HuggingFace `datasets` 라이브러리 또는 원 배포처 폼 제출)
- **라이선스**: 원 배포처 명시 없음, 연구용으로 널리 재배포됨

### AIT-NDS (넷플로)
오스트리아 AIT가 침입탐지 연구용으로 만든 8개 독립 테스트베드(wardbeck·santos·wilson·shaw·fox·wheeler·harrison·russellmitchell)의 넷플로 파생본. 원본(AIT-LDS)과 달리 **CC BY 4.0**이라 재배포에 제약이 없다.
- **규모**: 346만 플로우, 테스트베드별 기저율 5.17%~45.28%
- **출처**: Zenodo 13168643, **CC BY 4.0**
- **받는 법**: `uv run python scripts/fetch_ait.py nds`

### CSE-CIC-IDS2018
CIC-IDS2017 후속. 5개 부서·PC 420대·서버 30대 규모, 공격자도 AWS 위 여러 대 — **분산(N:N) 공격** 표본이 있다.
- **규모**: 하루치 794만 행(가공본 CSV 10개 중 IP 열이 있는 건 1개뿐)
- **출처**: AWS Open Data (registry.opendata.aws/cse-cic-ids2018), 인용 요구
- **받는 법**: `uv run python scripts/fetch_ids2018.py` (기본 1일치 약 4GB, `--all`로 10개 전부)

---

## 웹 요청 로그

### Splunk 검색 튜토리얼 데이터
Splunk사 공식 SPL 학습용 합성 데이터(가상 온라인 게임 사이트 웹서버·방화벽·메일서버 로그).
- **규모**: 요청 39,532건, 고유 IP 182
- **출처**: docs.splunk.com 공식 튜토리얼, 공개
- **받는 법**: 수동 — Splunk 공식 Search Tutorial 페이지에서 다운로드
- **주의**: 🟡 타임스탬프가 수신 시점 기준으로 재부여됨 — 절대 날짜 분석엔 안 맞음

### NASA-HTTP
1995년 NASA 케네디 우주센터 웹서버 실제 트래픽. 초기 웹 트래픽 연구의 고전 자료.
- **규모**: 189만 건, 28일, 고유 IP 8.2만. 라벨 없음
- **출처**: Internet Traffic Archive (ita.ee.lbl.gov), 공개, 계정 불필요
- **받는 법**: 수동 다운로드

### OWASP ModSecurity (WAF 감사 로그)
오픈소스 WAF ModSecurity + OWASP CRS가 실제 운영 중 남긴 감사 로그.
- **규모**: 약 14~15만 트랜잭션(집계 방식에 따라 갈림), 30일
- **출처**: Zenodo 17178461, **CC-BY 4.0**
- **받는 법**: 수동 — Zenodo 자동 다운로드가 막혀 있어 브라우저로 받아야 함

---

## 시스템·장비 로그

### LogHub
홍콩중문대 logpai 그룹이 만든 시스템 로그 벤치마크 모음(30여 종). 로그 파싱·이상탐지 연구 표준 벤치마크.
- **규모**: `_2k` 샘플 각 약 2,000줄 (OpenSSH·Apache·Linux·BGL·HealthApp 등)
- **출처**: github.com/logpai/loghub, 공개
- **받는 법**: 수동 — GitHub 저장소에서 직접

### SMD (Server Machine Dataset)
서버 28대 · 5주 다변량 시계열. 이상 구간마다 **원인 지표까지** 라벨된 드문 사례.
- **규모**: 28대 × 지표 38개, train/test 각 약 70만 행
- **출처**: github.com/NetManAIOps/OmniAnomaly, **MIT**
- **받는 법**: `uv run python scripts/fetch_smd.py`

---

## 사용자 행위 로그

### CERT Insider Threat Test Dataset (r1, r4.2)
CMU SEI가 만든 내부자 위협 탐지 합성 데이터셋 시리즈. r1은 정답 없음, r4.2는 인사이더 70명 정답 + `file.csv`·`email.csv` 포함.
- **규모**: r4.2 기준 device·file·email·logon 각 수십만~수백만 행, `http.csv`는 2,843만 행(14.5GB)
- **출처**: CMU/SEI, kilthub 12841247
- **라이선스**: **CC BY 4.0 + ExactData 최종사용자 동의** — ⚠️ CC BY만 보고 판단하지 말 것. kilthub에서 직접 받을 때 동의하는 별도 이용약관이 있다. 이 저장소는 **원출처(kilthub)로 안내만** 하며, 실제 동의는 각자 kilthub에서 받을 때 진행된다
- **받는 법**: `uv run python scripts/fetch_cert.py` (기본 r4.2 + 정답, `--with-http`로 대용량 http.csv 포함)

### CLUE-LDS
실제 클라우드 스토리지 사용자 행위 로그. CERT와 달리 시뮬레이션이 아닌 **실사용자 실제 흔적**.
- **규모**: 5,000만 건, 이름 있는 사용자 920명, 5년
- **출처**: Zenodo 7119953, **CC BY 4.0**
- **받는 법**: 수동 — Zenodo에서 직접 (14.9GB 단일 JSON Lines)

---

## 메일·문서 원문

### Nazario Phishing Corpus
연구자 Jose Nazario가 공개해 온 실제 피싱 이메일 코퍼스.
- **규모**: 481통 (2025판)
- **출처**: Nazario Phishing Corpus, 연구용 공개
- **받는 법**: 수동

### SpamAssassin `easy_ham_2`
Apache SpamAssassin 프로젝트의 정상 메일(ham) 세트.
- **규모**: 1,401통 (2003)
- **출처**: Apache SpamAssassin, 공개
- **받는 법**: 수동

### Enron Email Dataset
2001년 엔론 사건으로 공개된 실제 기업 이메일. 조직 내 커뮤니케이션 구조가 통째로 남은 몇 안 되는 공개 자료.
- **규모**: 443MB, 151 사서함
- **출처**: cs.cmu.edu/~enron, 공개
- **받는 법**: 수동

---

## 참조 목록 (피드형 — 재수신 시 값이 바뀜)

### PhishTank
커뮤니티 기반 피싱 URL 신고·검증 피드.
- **출처**: PhishTank 공식 피드, 공개
- **받는 법**: `uv run python scripts/fetch_phishing_feeds.py` (rate limit 있음, 캐시 우선)
- **주의**: 🟡 수신 시점마다 값이 다르다 — 인용 시 수신 날짜 병기

### Tranco top-1m
조작에 강한 도메인 인기 순위 리스트(Le Pochat et al., NDSS 2019). "알려진 정상 도메인" 기준선으로 자주 쓰임.
- **출처**: Tranco 공식 리스트, 공개
- **받는 법**: `uv run python scripts/fetch_phishing_feeds.py`
- **주의**: 🟡 갱신됨

### UCI SMS Spam Collection
영문 SMS 스팸/정상 이진 분류 데이터셋.
- **규모**: 5,572건, 정상:스팸 약 87:13
- **출처**: UCI ML Repository, 공개
- **받는 법**: 수동

---

## Splunk 관련

### Splunk Machine Learning Toolkit (MLTK) — lookups
Splunk 공식 MLTK 앱에 예제·튜토리얼용으로 동봉된 lookup 51종(보안·IT운영·일반 비즈니스 지표 혼합).
- **출처**: Splunk MLTK 앱 (Splunkbase, 무료)
- **라이선스**: ⚠️ **Splunk 앱 라이선스 하위** — 앱 자체를 Splunkbase에서 받아 설치하는 방식으로만 접근할 것을 권한다. 이 저장소는 lookup 파일을 별도로 재배포하지 않는다
- **받는 법**: Splunkbase에서 Machine Learning Toolkit 앱 설치 → `$SPLUNK_HOME/etc/apps/Splunk_ML_Toolkit/lookups/`

---

## 검토했으나 포함하지 않음

| 데이터셋 | 사유 |
| --- | --- |
| **ThreatFox** (abuse.ch) | API는 "fair use 무료"만 명시, 사이트 일반 약관엔 상업적 이용 금지 조항 — 라이선스가 불명확해 제외 |
| **KISA WAF 침해사고 샘플** | 배포 조건 미기재, 접근 경로(배포처 URL) 미보존 — 재현 불가능해 제외. KISA C-TAS(ctas.krcert.or.kr) 가입 후 정식 경로로 재확인 가능 |
| **AIT-LDS v2.1 (원본)** | **CC BY-NC-SA 4.0 (비영리)** — 상업적 이용 불가. 대신 파생본(AIT-NDS·AIT-ADS·CLUE-LDS, 전부 CC BY 4.0) 사용 |
| **AIT-LDS v1.1 / Kyoushi** | 구판 + 비영리 라이선스, 위와 동일 사유 |
| **CAM-LDS** | CC BY 4.0으로 라이선스는 문제없으나, 정상 트래픽 시뮬레이션 없이 공격만 캡처돼 이상탐지 평가(기저율 필요)엔 부적합해 미확보 |

## 변경 이력

- 2026-09-17: 신설. `kbdc-poc` 프로젝트에서 실사용 검증된 데이터셋 카탈로그를 분리 — 데이터 파일 자체는 옮기지 않고 카탈로그+fetch 스크립트만 공개.
