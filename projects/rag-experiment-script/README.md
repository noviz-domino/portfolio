# RAG 실험 스크립트

작성일: 2026-09-07

RAG 파이프라인의 설정(청크 크기, 검색 전략, k, rerank, 프롬프트 등)을 **코드가 아닌 외부 config 파일로**
관리하고, config를 바꿔가며 반복 실행해 결과를 비교할 수 있는 실험 장치다.

설계 근거와 실험 해석은 `2026-09-07 RAG 실험 설계 계획서.md`에 정리했다.

---

## 1. 실행 준비

```bash
pip install pyyaml kiwipiepy rank_bm25
```

- `kiwipiepy`, `rank_bm25`는 **BM25/Hybrid 전략에서만** 필요하다.
  (`pipeline.py`가 지연 임포트하므로, similarity/mmr만 쓸 경우 없어도 동작한다)

`.env` 파일에 Gemini API 키가 필요하다. `config.py`가 아래 경로에서 읽는다.

```
C:\Users\HOME\Desktop\260811\.env      # GEMINI_API_KEY=...
```

**첨부된 결과를 재현하려면 벡터 저장소를 새로 만들어야 한다.** `chroma_db/` 폴더는 용량이 커서(34MB)
제출본에서 제외했다. 코드와 PDF가 있으면 자동으로 재생성되지만, 청크 402개 기준 **임베딩 API 402회**가 든다.

---

## 2. 실행 방법

실행 위치는 이 폴더여야 한다. config의 경로가 `../data/public`처럼 이 폴더 기준 상대 경로다.

```bash
# ① 예상 비용 확인 (API 호출 없음)
python main.py --config configs/baseline.yaml --dry-run

# ② 3문항만 돌려 코드가 끝까지 도는지 확인 (smoke test)
python main.py --config configs/baseline.yaml --limit 3

# ③ 전체 실행
python main.py --config configs/baseline.yaml

# ④ 모든 실험 결과를 표로 비교
python report.py
```

### CLI 옵션

| 옵션 | 용도 |
|---|---|
| `--config` | 사용할 실험 설정 파일 (필수) |
| `--limit N` | 문항 수를 임시로 N개로 줄여 실행 (smoke test용) |
| `--dry-run` | API를 호출하지 않고 예상 호출 수·토큰·소요 시간만 계산 |

`--limit`을 config가 아닌 CLI에 둔 이유: 문항을 줄인 것은 실험 설계가 아니라 개발 중 확인이므로,
config에 기록으로 남으면 "이 실험은 3문항이었다"는 오해를 만든다.

---

## 3. 파일 구조

```
main.py         CLI 입구. 옵션을 받아 실행 순서만 지시
config.py       YAML 읽기 + 값 검증 (.env 로드 포함)
pipeline.py     PDF 로드 · 청킹 · 벡터저장소 · 검색기 생성, 비용 계수기, 429 재시도
metrics.py      File Hit@k / Page Hit@k / MRR 계산
runner.py       문항 반복 · 체크포인트 저장 · 비용 집계 · rerank
generation.py   답변 생성 · 인용 검사 · LLM-as-Judge 채점
report.py       실험 결과를 표로 비교
configs/        실험 설정 20개
prompts/        답변 생성 프롬프트 2종 (basic / grounded)
outputs/        실험별 결과
```

파일을 나눈 기준은 줄 수가 아니라 **"바뀌는 이유가 다른가"** 다.
`metrics.py`는 정답 형식이 바뀔 때, `pipeline.py`는 새 검색 전략을 추가할 때,
`main.py`는 CLI 옵션을 늘릴 때만 바뀐다.

---

## 4. config 항목

```yaml
experiment_name: baseline        # 결과가 outputs/<이 이름>/ 에 저장된다

data:
  pdf_dir: ../data/public
  golden_set: ../data/public/public_paragraph_golden_set.json

models:
  embedding: gemini-embedding-2
  llm: gemini-3.5-flash-lite

chunk:
  size: 700                      # 청크 하나의 최대 글자 수
  overlap: 100                   # 앞 청크와 겹치는 글자 수

search:
  strategy: similarity           # similarity | mmr | bm25 | hybrid
  k: 5                           # 검색해서 LLM에 넘길 문서 수
  mmr:
    fetch_k: 20                  # 후보를 20개 뽑아 그중 다양성을 고려해 k개 선택
    lambda_mult: 0.5             # 1에 가까울수록 관련성 우선
  hybrid:
    weights: [0.5, 0.5]          # [벡터검색, BM25] 가중치

rerank:
  enabled: false                 # true면 검색 결과를 LLM으로 재정렬
  top_n: 5                       # LLM 호출 수 = 문항 수 × 이 값

evaluation:
  retrieval_limit: 35            # 검색 지표에 쓸 문항 수
  llm_limit: 10                  # LLM이 개입하는 실험의 문항 수(비용 통제)
  run_generation: false          # true면 검색 결과로 답변을 생성
  run_judge: false               # true면 생성한 답변을 LLM이 채점
  context_k: 5                   # 답변 생성 프롬프트에 넣을 문서 수
  prompt_path: prompts/grounded.txt
  # case_indices: [0, 1, 18, 20] # (선택) 앞에서부터 자르지 않고 문항을 직접 지정

pacing:
  embed_batch_size: 10
  embed_sleep_sec: 12            # 배치 간 대기 (무료 티어 분당 토큰 한도 대응)
  llm_sleep_sec: 5               # LLM 호출 간 대기 (분당 15회 한도의 80%)
  max_retries: 5
```

---

## 5. 결과 파일

```
outputs/<experiment_name>/
  rows.jsonl     문항별 상세 결과 (한 줄에 문항 하나)
  summary.json   품질 · 비용 · 시간 집계
```

`rows.jsonl`은 **체크포인트 역할도 한다.** 문항 하나가 끝날 때마다 즉시 한 줄을 추가하므로,
중간에 중단돼도 재실행하면 이미 처리한 문항을 건너뛰고 이어서 진행한다.
단, 코퍼스를 바꾼 뒤에는 이 파일을 삭제해야 재채점된다(체크포인트는 "어느 문항"만 기억하고
"어떤 코퍼스로" 처리했는지는 모른다).

---

## 6. 실험 결과 (2026-09-07 실측, 20개)

```
실험명               | page_hit_1 | page_hit_3 | page_hit_5 | file_hit_1 | mrr   | 임베딩 | LLM | 시간(초) | 인용정확 | 정답인용 | Judge평균
baseline          | 0.886      | 0.914      | 0.943      | 0.971      | 0.907 | 32    | 0   | 55.2    | -     | -     | -
baseline-10       | 1.000      | 1.000      | 1.000      | 1.000      | 1.000 | 10    | 0   | 45.7    | -     | -     | -
chunk-1000        | 0.829      | 0.914      | 0.943      | 0.971      | 0.872 | 66    | 0   | 496.9   | -     | -     | -
chunk-1000-bm25   | 0.857      | 0.943      | 0.943      | 0.943      | 0.895 | 0     | 0   | 42.8    | -     | -     | -
chunk-1000-hybrid | 0.886      | 0.943      | 0.943      | 0.971      | 0.910 | 35    | 0   | 62.6    | -     | -     | -
chunk-1000-mmr    | 0.829      | 0.914      | 0.914      | 0.971      | 0.871 | 35    | 0   | 56.6    | -     | -     | -
chunk-500         | 0.857      | 0.943      | 0.943      | 0.971      | 0.895 | 52    | 0   | 284.3   | -     | -     | -
chunk-500-bm25    | 0.886      | 0.943      | 0.943      | 0.971      | 0.914 | 0     | 0   | 43.5    | -     | -     | -
chunk-500-hybrid  | 0.943      | 0.943      | 0.943      | 1.000      | 0.943 | 35    | 0   | 63.0    | -     | -     | -
chunk-500-mmr     | 0.857      | 0.914      | 0.914      | 0.971      | 0.886 | 35    | 0   | 56.9    | -     | -     | -
gen-hybrid        | 1.000      | 1.000      | 1.000      | 1.000      | 1.000 | 10    | 20  | 207.6   | 1.000 | 1.000 | 9.95
gen-similarity    | 1.000      | 1.000      | 1.000      | 1.000      | 1.000 | 10    | 20  | 201.5   | 1.000 | 1.000 | 9.70
hard-baseline     | 0.600      | 0.700      | 0.800      | 0.900      | 0.675 | 10    | 0   | 43.9    | -     | -     | -
hard-rerank       | 0.800      | 0.800      | 0.800      | 1.000      | 0.800 | 10    | 50  | 370.4   | -     | -     | -
k-10              | 0.886      | 0.914      | 0.943      | 0.971      | 0.907 | 35    | 0   | 56.6    | -     | -     | -
k-3               | 0.886      | 0.914      | 0.914      | 0.971      | 0.900 | 35    | 0   | 56.1    | -     | -     | -
rerank-on         | 1.000      | 1.000      | 1.000      | 1.000      | 1.000 | 8     | 40  | 308.2   | -     | -     | -
search-bm25       | 0.886      | 0.914      | 0.943      | 0.971      | 0.907 | 0     | 0   | 43.2    | -     | -     | -
search-hybrid     | 0.886      | 0.943      | 0.943      | 0.971      | 0.910 | 35    | 0   | 62.8    | -     | -     | -
search-mmr        | 0.886      | 0.914      | 0.943      | 0.971      | 0.907 | 35    | 0   | 57.3    | -     | -     | -
```

### ⚠️ 비교군이 세 개로 나뉘어 있다

같은 표에 있어도 **문항 구성이 다른 실험끼리는 비교할 수 없다.**

| 비교군 | 실험 | 용도 |
|---|---|---|
| 35문항 | baseline, chunk-*, k-*, search-* | 청킹 · 전략 · k 비교 |
| 앞 10문항 | baseline-10, rerank-on | 천장 효과로 **측정 실패**한 시도 (기록으로 남김) |
| 난이도 균형 10문항 | hard-baseline, hard-rerank | rerank 효과를 실제로 측정 |
| 생성 10문항 | gen-similarity, gen-hybrid | 답변 품질 비교 |

### 주요 결론

- **최고 조합: `chunk 500 + hybrid`** — Page Hit@1 0.943, MRR 0.943, File Hit@1 1.000
- **가성비 최고: `chunk 500 + BM25`** — MRR 0.914로 baseline(0.907)보다 높은데 **임베딩 호출 0회**, 43.5초
- **청크와 전략은 상호작용한다** — 청크 700에서 hybrid의 이득은 거의 없지만(0.907→0.910),
  청크 500에서는 크다(0.895→0.943). 한 번에 하나만 바꾸는 방식으로는 볼 수 없는 효과다.
- **k는 5가 적절** — k=10은 baseline과 모든 수치가 동일(이득 0), k=3은 Page Hit@5에서 손실
- **rerank는 이론상 최대치를 달성했으나 비용이 정당화되지 않는다** — Page Hit@1 0.600→0.800으로
  개선 가능했던 2문항을 모두 고쳤지만, 문항당 소요 시간이 4.4초 → 37초가 됐다

자세한 해석과 실험 과정에서 발견한 문제(예산 계산 오류, 부분 저장 캐시 버그, 천장 효과)는 계획서 참조.
