# sec-dataset-catalog

보안 로그·이상탐지 연구에서 실제로 써본 **공개 데이터셋 카탈로그**. 각 데이터셋이 무엇이고, 규모·라벨이 어떤지, 어디서 어떻게 받는지를 정리한다.

**이 저장소가 하는 일 / 안 하는 일**

- ✅ 데이터셋 설명, 라이선스, **받는 스크립트**를 공유한다
- ❌ **데이터 파일 자체는 커밋·재배포하지 않는다.** `scripts/`의 스크립트가 각자 원출처(Zenodo·GitHub·AWS Open Data 등)에서 직접 받아온다 — 이 저장소는 "어디서 어떻게 받는지"만 알려준다
- ⚠️ 라이선스는 **원출처 기준**이다. 아래 표의 라이선스 표기를 반드시 확인하고, 상업적 이용이 걸린 경우 원문 약관을 직접 재확인할 것

## 카탈로그 (17종)

받는 명령은 전부 저장소 루트에서 `uv run python scripts/<명령>` 형태로 실행한다. 받은 파일은 `data/` 아래에 쌓이고, 캐시 우선이라 다시 실행해도 이미 있는 건 건너뛴다.

| 데이터셋 | 무엇 | 규모 | 라벨 | 라이선스 | 받는 법 |
| --- | --- | --- | --- | --- | --- |
| **CIC-IDS2017** | 네트워크 플로우 통계 | 283만 행 | ✅ 14종 | 원 배포처 미명시 | `fetch_weblogs.py cicids2017` |
| **AIT-NDS** | 넷플로 (테스트베드 8개) | 346만 플로우 | ✅ | CC BY 4.0 | `fetch_ait.py nds` |
| **CSE-CIC-IDS2018** | 네트워크 플로우 (분산 공격) | 794만 행/일 | ✅ | AWS Open Data (인용 요구) | `fetch_ids2018.py` |
| **Splunk 검색 튜토리얼** | 웹·인증·판매 로그 (합성) | 요청 39,532 | ❌ | Splunk 공식 자료 (공개) | `fetch_weblogs.py splunk-tutorial` |
| **NASA-HTTP** | 웹 액세스 로그 (실제) | 189만 건 · 28일 | ❌ | Internet Traffic Archive (공개) | `fetch_weblogs.py nasa` |
| **OWASP ModSecurity** | WAF 감사 로그 (실제) | 142,705건 · 30일 | ✅ 룰 ID | CC BY 4.0 | `fetch_weblogs.py owasp` |
| **LogHub** | 시스템 로그 벤치마크 | 2,000줄 × 5종 | 🟡 BGL만 | 공개 (학술 인용) | `fetch_weblogs.py loghub` |
| **AIT-ADS** | IDS 알럿 3종 (Suricata·Wazuh·AMiner) | 265만 건 | ✅ | CC BY 4.0 | `fetch_ait.py ads` |
| **SMD** | 서버 28대 다변량 시계열 | 28대 × 지표 38 | ✅ + 원인 지표 | MIT | `fetch_smd.py` |
| **CERT r4.2** | 내부자 위협 (합성) | http만 2,843만 행 | ✅ 인사이더 70명 | ⚠️ CC BY 4.0 **+ 최종사용자 동의** | `fetch_cert.py` |
| **CLUE-LDS** | 클라우드 사용자 행위 (실제) | 5,000만 건 · 5년 | ❌ | CC BY 4.0 | `fetch_ait.py clue` |
| **Nazario Phishing** | 피싱 메일 원문 | 481통 (2025) | ✅ 전부 피싱 | CC BY 4.0 | `fetch_mail.py nazario` |
| **SpamAssassin** `easy_ham_2` | 정상 메일 원문 | 1,401통 (2003) | ✅ 전부 정상 | Apache 공개 코퍼스 | `fetch_mail.py spamassassin` |
| **Enron Email** | 기업 사서함 아카이브 | 151 사서함 · 443MB | ❌ | 공개 | `fetch_mail.py enron` |
| **UCI SMS Spam** | 문자 스팸/정상 | 5,574건 | ✅ 이진 | CC BY 4.0 | `fetch_mail.py sms-spam` |
| **PhishTank** | 피싱 URL 피드 | 7.3만 행 | ✅ | 공개 (rate limit) | `fetch_phishing_feeds.py` |
| **Tranco top-1m** | 도메인 인기 순위 | 100만 | — | 공개 | `fetch_phishing_feeds.py` |

> **17종 전부 스크립트로 받는다.** 브라우저로 직접 받아야 하는 것은 없다.
>
> 🟡 **피드형(PhishTank · Tranco)은 받을 때마다 값이 다르다.** 인용할 때 수신 날짜를 병기해야 한다.

## 시작하기

```bash
git clone https://github.com/lamacodes/sec-dataset-catalog
cd sec-dataset-catalog
uv sync

# 뭐가 있는지부터 — 어느 스크립트든 --list 는 받지 않고 목록만 보여준다
uv run python scripts/fetch_weblogs.py --list
uv run python scripts/fetch_mail.py --list
uv run python scripts/fetch_ait.py --list

# 받기
uv run python scripts/fetch_weblogs.py nasa loghub
uv run python scripts/fetch_mail.py --all          # Enron 443MB 포함
```

| 스크립트 | 담당 |
| --- | --- |
| `fetch_weblogs.py` | CIC-IDS2017 · Splunk 튜토리얼 · NASA-HTTP · OWASP ModSecurity · LogHub |
| `fetch_mail.py` | Nazario · SpamAssassin · UCI SMS Spam · Enron |
| `fetch_ait.py` | AIT-NDS · AIT-ADS · CLUE-LDS (+ `lds`는 비영리 조항이라 기본값에서 제외) |
| `fetch_cert.py` | CERT r1 · r4.2 |
| `fetch_ids2018.py` | CSE-CIC-IDS2018 |
| `fetch_phishing_feeds.py` | PhishTank · Tranco |

---

## 네트워크 플로우

### CIC-IDS2017
캐나다 사이버보안 연구소(University of New Brunswick)가 2017년 공개한 네트워크 침입탐지 벤치마크. 월요일 정상 트래픽 + 화~금 공격(브루트포스·DoS/DDoS·웹공격·Infiltration·봇넷·포트스캔) 주입 구조. `CICFlowMeter`로 추출한 84열 플로우 통계.
- **규모**: 283만 행, 라벨 14종(공격 비율 19.7%)
- **일자 구성**: 07-03(월) 공격 0건 **← 기준선** · 07-04 Patator · 07-05 DoS 4종 + Heartbleed · 07-06 Web Attack + Infiltration · 07-07 DDoS + PortScan + Bot
- **출처**: 원 배포처는 폼 제출이 필요해 **HuggingFace 미러**를 쓴다 (84열 parquet + 79열 CSV 비교용)
- **받는 법**: `uv run python scripts/fetch_weblogs.py cicids2017` (0.37 GB)

### AIT-NDS (넷플로)
오스트리아 AIT가 침입탐지 연구용으로 만든 8개 독립 테스트베드(wardbeck·santos·wilson·shaw·fox·wheeler·harrison·russellmitchell)의 넷플로 파생본. 원본(AIT-LDS)과 달리 **CC BY 4.0**이라 재배포에 제약이 없다.
- **규모**: 346만 플로우, 테스트베드별 기저율 5.17%~45.28%
- **왜 쓰나**: 테스트베드가 8개라 **규칙이 다른 망에서도 서는지** 잴 수 있다. 데이터 반출(DNSteal)이 라벨로 있다 — CIC-IDS2017에서 36건뿐이던 축이다
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
Splunk사 공식 SPL 학습용 합성 데이터(가상 온라인 쇼핑몰 Buttercup Games의 웹서버·인증·판매 로그).
- **규모**: 웹 액세스 39,532건(www1~3 합), 고유 IP 182, 세션 5,297
- **왜 쓰나**: **세션 ID와 User-Agent가 있다** — NASA-HTTP(Common Log Format)에 없는 세션 축은 여기서만 본다
- **출처**: docs.splunk.com 공식 튜토리얼, 공개
- **받는 법**: `uv run python scripts/fetch_weblogs.py splunk-tutorial` (11 MB)
- **주의**: 🟢 내용은 고정이라 건수·구조는 재현된다(2026-09-07 재수신 대조 전 항목 일치). 🟡 **단 타임스탬프는 받는 시점 기준으로 다시 매겨진다** — 절대 날짜를 쓰는 분석은 재현되지 않는다

### NASA-HTTP
1995년 NASA 케네디 우주센터 웹서버 실제 트래픽. 초기 웹 트래픽 연구의 고전 자료.
- **규모**: 189만 건(파싱 실패 8), 28일, 고유 IP 8.2만 / URL 7,243. 하루 요청 중앙값 64,671(27k~134k로 **5배 변동**)
- **왜 쓰나**: 합성이 아닌 실제 트래픽이라 Splunk 튜토리얼의 한계(UA가 IP마다 고르게 퍼진 랜덤 생성 티)가 없다
- **출처**: Internet Traffic Archive (ita.ee.lbl.gov), 공개, 계정 불필요
- **받는 법**: `uv run python scripts/fetch_weblogs.py nasa` (20 MB 압축 → 196 MB)
- **주의**: 🔴 **라벨이 없고 UA·세션 ID도 없다**(Common Log Format). 이상은 심어서 봐야 한다

### OWASP ModSecurity (WAF 감사 로그)
오픈소스 WAF ModSecurity + OWASP CRS가 실제 운영 중 남긴 감사 로그. 한 줄이 아니라 `-A--`~`-Z--` **섹션 구조**라 액세스 로그와 파싱 방식 자체가 다르다.
- **규모**: 142,705 트랜잭션, 30일(2025-07-27~08-25), 고유 출발지 IP 5,994
- **응답 코드**: 404 43.4% · 403 32.7% · 301 13.9% · 503 6.3% — **2xx가 0건**
- **상위 룰**: `930130` Restricted File Access 48,216 · `444444` BAD BOT 47,536
- **출처**: Zenodo 17178461, **CC BY 4.0**
- **받는 법**: `uv run python scripts/fetch_weblogs.py owasp` (29 MB 압축 → 380 MB)
  - 🟡 Zenodo는 `/records/.../files/` 경로가 403을 낸다. 스크립트는 **API의 `/api/records/<id>/files/<name>/content`** 를 쓴다 — 그쪽은 열려 있다
- **주의**: 🔴 **정상 트래픽이 없다.** 걸린 것만 남은 로그라 기저율·오탐률을 잴 수 없다. 스캐너·봇의 과접근 패턴을 보는 용도다. NASA와 합쳐서 기저율을 만들 수도 없다 — 서로 다른 사이트다

---

## 시스템·장비 로그

### LogHub
홍콩중문대 logpai 그룹이 만든 시스템 로그 벤치마크 모음(30여 종). 로그 파싱·이상탐지 연구 표준 벤치마크. 이 스크립트는 `_2k` 샘플 5종(OpenSSH·Apache·Linux·BGL·HealthApp)을 받는다.
- **규모**: 각 2,000줄. 기간은 제각각(SSH 4시간 ~ Linux 6주)
- **왜 쓰나**: 형식이 서로 다른 로그를 **같은 파서로 다룰 수 있나**를 보는 용도다. 볼 것은 내용이 아니라 구조
- **출처**: github.com/logpai/loghub, 공개
- **받는 법**: `uv run python scripts/fetch_weblogs.py loghub` (1 MB)
- **주의**: 🔴 **BGL 라벨을 성능 평가에 쓰면 안 된다.** 사람의 정/오탐 판정이 아니라 메시지 종류 분류라서 템플릿과 거의 1:1이다

### AIT-ADS (알럿 데이터셋)
AIT 테스트베드에서 IDS 3종(Suricata · Wazuh · AMiner)이 낸 알럿. 같은 사건을 서로 다른 도구가 어떻게 다르게 적는지가 통째로 남아 있다.
- **규모**: 265만 건
- **왜 쓰나**: **포맷이 서로 다르고** 정상 행위에서 나온 오탐이 섞여 있다 — 필드명 정합(정규화) 문제의 실물이다
- **출처**: Zenodo 8263181, **CC BY 4.0**
- **받는 법**: `uv run python scripts/fetch_ait.py ads`

### SMD (Server Machine Dataset)
서버 28대 · 5주 다변량 시계열. 이상 구간마다 **원인 지표까지** 라벨된 드문 사례.
- **규모**: 28대 × 지표 38개, train/test 각 약 70만 행
- **출처**: github.com/NetManAIOps/OmniAnomaly, **MIT**
- **받는 법**: `uv run python scripts/fetch_smd.py`
- **주의**: 🔴 지표 이름도 타임스탬프도 없다 — 지표는 1~38번, 행 번호가 곧 시간이다

---

## 사용자 행위 로그

### CERT Insider Threat Test Dataset (r1, r4.2)
CMU SEI가 만든 내부자 위협 탐지 합성 데이터셋 시리즈. r1은 정답 없음, r4.2는 인사이더 70명 정답 + `file.csv`·`email.csv` 포함.
- **규모**: r4.2 기준 device·file·email·logon 각 수십만~수백만 행, `http.csv`는 2,843만 행(14.5GB)
- **라이선스**: **CC BY 4.0 + ExactData 최종사용자 동의** — ⚠️ CC BY만 보고 판단하지 말 것. kilthub에서 직접 받을 때 동의하는 별도 이용약관이 있다. 이 저장소는 **원출처(kilthub)로 안내만** 하며, 실제 동의는 각자 kilthub에서 받을 때 진행된다
- **받는 법**: `uv run python scripts/fetch_cert.py` (기본 r4.2 + 정답, `--with-http`로 대용량 http.csv 포함)

### CLUE-LDS
실제 클라우드 스토리지 사용자 행위 로그. CERT와 달리 시뮬레이션이 아닌 **실사용자 실제 흔적**이다.
- **규모**: 5,000만 건, 사용자 5,000명(이름 있는 사용자 920명), 5년(1,910일)
- **왜 쓰나**: *"사용자별 3개월 평균 × 3"* 같은 기준을 백분위수와 맞대려면 **분포가 실제여야 한다**. 합성 데이터의 분포는 설계한 사람이 만든 것이라 근거가 못 된다
- **출처**: Zenodo 7119953, **CC BY 4.0**
- **받는 법**: `uv run python scripts/fetch_ait.py clue` (0.64 GB 압축 → 14.9GB 단일 JSON Lines)

---

## 메일·문서 원문

### Nazario Phishing Corpus
연구자 Jose Nazario가 공개해 온 실제 피싱 이메일 코퍼스. 연도별 mbox로 나뉘며 스크립트는 2025 수집분을 받는다.
- **규모**: 481통 (2025)
- **출처**: monkey.org/~jose/phishing/, **CC BY 4.0**(배포처 `LICENSE.txt`)
- **받는 법**: `uv run python scripts/fetch_mail.py nazario` (19 MB)
- **주의**: 🟡 **수집 측 rspamd의 판정 헤더가 남아 있다.** 헤더 기반 피처를 쓰면 정답이 새어 들어간다 — 본문·URL 축만 쓰거나 해당 헤더를 지울 것

### SpamAssassin `easy_ham_2`
Apache SpamAssassin 프로젝트의 정상 메일(ham) 세트. 피싱과 맞댈 정상 쪽으로 쓴다.
- **규모**: 1,401통 (2003)
- **출처**: spamassassin.apache.org/old/publiccorpus/, 공개
- **받는 법**: `uv run python scripts/fetch_mail.py spamassassin` (1 MB)
- **주의**: 🔴 2003년 자료이고 **개인 메일 성격**이라 "조직 안에서 누가 누구에게 얼마나 보내나"는 볼 수 없다 — 그 축은 Enron이다

### Enron Email Dataset
2001년 엔론 사건으로 공개된 실제 기업 이메일. 조직 내 커뮤니케이션 구조가 통째로 남은 몇 안 되는 공개 자료.
- **규모**: 443MB(압축), 151 사서함, 43만+ 통 (2015-05-07 판)
- **왜 쓰나**: 발신 패턴·수신자 관계의 **정상 기준선**을 세울 수 있는 유일한 공개 자료
- **출처**: cs.cmu.edu/~enron, 공개
- **받는 법**: `uv run python scripts/fetch_mail.py enron` (443 MB — 스크립트는 받기만 하고 풀지 않는다. 풀면 2.6GB·파일 50만 개)

### UCI SMS Spam Collection
영문 SMS 스팸/정상 이진 분류 데이터셋.
- **규모**: 5,574건, 정상:스팸 약 87:13
- **왜 쓰나**: **본문만 있는 짧은 텍스트**의 대조군. 규칙이 메일 형식(헤더·도메인)에 얼마나 기대고 있었는지가 드러난다
- **출처**: UCI ML Repository (dataset 228), 공개
- **받는 법**: `uv run python scripts/fetch_mail.py sms-spam` (0.2 MB)
- **주의**: 🟡 메일이 아니라 문자이고, 대량 살포형이라 표적형(BEC)과는 성격이 다르다

---

## 참조 목록 (피드형 — 재수신 시 값이 바뀜)

### PhishTank
커뮤니티 기반 피싱 URL 신고·검증 피드.
- **규모**: 7.3만 행 (수신 시점에 따라 다름)
- **출처**: PhishTank 공식 피드, 공개
- **받는 법**: `uv run python scripts/fetch_phishing_feeds.py` (rate limit 있음, 캐시 우선)
- **주의**: 🟡 수신 시점마다 값이 다르다 — 인용 시 수신 날짜 병기

### Tranco top-1m
조작에 강한 도메인 인기 순위 리스트(Le Pochat et al., NDSS 2019). "알려진 정상 도메인" 기준선으로 자주 쓰인다.
- **규모**: 1,000,000
- **출처**: Tranco 공식 리스트, 공개
- **받는 법**: `uv run python scripts/fetch_phishing_feeds.py`
- **주의**: 🟡 매일 갱신된다

## 변경 이력

- 2026-09-17: `fetch_weblogs.py`·`fetch_mail.py` 신설 — 카탈로그 표 추가하면서 "받는 법: 수동" 9건을 재확인한 결과, **원출처 직접 다운로드가 되는데 스크립트가 없었을 뿐**이었다. OWASP는 Zenodo `/records/` 경로만 403이고 API `/content` 경로는 열려 있다. CLUE-LDS는 `fetch_ait.py clue`로 이미 받을 수 있었는데 "수동"으로 잘못 적혀 있었다. Nazario 라이선스도 배포처 `LICENSE.txt` 확인 후 CC BY 4.0으로 정정. AIT-ADS 항목 추가. **스크립트로 못 받는 Splunk MLTK(앱 동봉 파일)와 "검토했으나 포함하지 않음" 목록은 뺐다** — 이 저장소는 받을 수 있는 것만 싣는다(17종).
- 2026-09-17: 신설. `kbdc-poc` 프로젝트에서 실사용 검증된 데이터셋 카탈로그를 분리 — 데이터 파일 자체는 옮기지 않고 카탈로그+fetch 스크립트만 공개.
