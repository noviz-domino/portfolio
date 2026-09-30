# 작업 지시 02 — RAG 코어

## 목표

검색 기능을 구현해 `/api/ask`가 실제 문서를 근거로 답변하고 **인용을 반환**하게
한다. 01단계에서 `citations`는 항상 빈 배열이었다.

에이전트(LangGraph)는 03단계 범위다. 이 단계는 **단방향 파이프라인**으로 만든다.

```
질의 → 하이브리드 검색 → (선택) 리랭킹 → 컨텍스트 구성 → LLM → 답변 + 인용
```

## 사전 조건

- 작업 디렉토리 `/home/user/Desktop/ML`, 브랜치 `main`, 작업트리 깨끗함
- [설계.md](../설계.md)의 "문서 처리", "검색" 절을 먼저 읽을 것
- [작업일지.md](../작업일지.md)의 01단계 인계사항을 읽을 것
- `uv`는 `~/.local/bin/uv`에 있다. PATH에 없으면 추가할 것
- 명령은 `backend/` 에서 `uv run ...` 으로 실행
- `langchain-core`는 **1.x 계열**이다. v0.3 예제를 그대로 베끼지 말 것

## 할 일

### 1. 의존성 추가
`rank-bm25`, `langchain-chroma`, `langchain-huggingface`, `sentence-transformers`,
`pymupdf`. 리랭킹용 추가 패키지가 필요하면 함께 넣는다.

> 이 기기는 Raspberry Pi 5(aarch64)다. 설치가 오래 걸린다. 출력은 파일로
> 리다이렉트하고 실패했을 때만 확인할 것.

### 2. 조문 단위 청킹 (`backend/app/rag/chunking.py`)

설계.md의 방침을 구현한다.

1. 정규식으로 `제N조`, `제N조의M` 경계를 찾아 조 단위로 1차 분할
2. 한 조가 `chunk_size`를 넘으면 `RecursiveCharacterTextSplitter`로 2차 분할하되,
   같은 조라는 메타데이터를 유지
3. 조 경계를 찾지 못하면 전부 재귀 분할기로 처리 (일반 문서 대응)

각 청크에 메타데이터를 붙인다: `source`, `page`, `article`, `chunk_id`.
`article`은 추출 실패 시 `None`.

`chunk_size`, `chunk_overlap`을 설정 항목으로 추가한다 (기본 500 / 100).

### 3. 인제스트 (`backend/app/rag/ingest.py`)

- `settings.pdf_path` 아래 PDF를 PyMuPDF로 로드 → 청킹 → 임베딩 → Chroma 저장
- 저장 위치는 `settings.vector_store_dir`
- **재실행 안전성**: 이미 인제스트된 상태에서 다시 돌려도 중복 적재되지 않아야
  한다. 간단하게는 기존 컬렉션을 지우고 다시 만드는 방식도 허용한다. 택한 방식을
  작업일지에 적을 것.
- CLI로 실행할 수 있게 한다 (예: `uv run python -m app.rag.ingest`).
- 01단계에서 발견된 경로 버그를 반복하지 말 것. 경로는 반드시
  `settings.pdf_path` / `settings.vector_store_dir` 를 쓴다.

### 4. 하이브리드 검색 (`backend/app/rag/retrieval.py`)

두 경로를 각각 구성하고 RRF로 융합한다.

- **Dense**: Chroma + bge-m3
- **Sparse**: BM25 (`rank-bm25`). 인제스트한 청크로 인덱스를 만든다
- **융합**: RRF, `k=60`

```
score(d) = Σ_i  1 / (k + rank_i(d))
```

각 경로에서 상위 N개(기본 20)를 가져와 융합한 뒤, 최종 `settings.retrieval_k`개를
반환한다. 융합 상수와 후보 수는 상수로 두되 의미를 주석으로 남길 것.

> **한국어 BM25 주의**: 공백 기준 토크나이즈만 하면 조사 때문에 매칭이 나빠진다.
> 형태소 분석기(konlpy 등)는 설치 부담이 크므로, 우선 간단한 정규화(공백 분리 +
> 조사 제거 수준)로 구현하고 한계를 작업일지에 기록할 것. 과하게 파고들지 말 것.

### 5. 리랭킹 (`backend/app/rag/rerank.py`)

`BAAI/bge-reranker-v2-m3` 크로스 인코더로 재정렬. `settings.rerank_enabled`가
`False`면 **모델을 로드조차 하지 않아야 한다** (파이에서 로딩만으로도 느리다).
기본값 `False` 유지.

### 6. 서비스 계층 연결 (`backend/app/services.py`)

`answer_question`이 검색 → 컨텍스트 구성 → LLM 호출 → 인용 반환까지 하도록 한다.

- 프롬프트는 `backend/app/prompts/legal_qa.txt` 사용. 필요하면 인용 지시를
  추가하되, 원본 의도를 크게 바꾸지 말 것
- 응답의 `citations`를 설계.md 스키마대로 채운다
  (`source`, `page`, `article`, `snippet`)
- 벡터스토어가 비어 있으면 명확한 에러 메시지를 반환한다 (스택 트레이스 금지)

### 7. 테스트 (`backend/tests/`)

`fake` 백엔드로 키 없이 전부 통과해야 한다.

- 청킹: 조문 경계 분할이 의도대로 되는지, 메타데이터가 붙는지
  (짧은 합성 텍스트로 테스트. 실제 PDF에 의존하지 말 것)
- RRF: 두 개의 순위 리스트를 넣었을 때 융합 순위가 기대대로 나오는지
  (순수 함수로 분리해 테스트 가능하게 만들 것)
- API: `/api/ask`가 `citations`를 채워 반환하는지

### 8. 작업일지

`docs/작업일지.md`에 "2단계" 섹션을 추가한다. 1단계와 같은 형식:
한 일 / 결정과 이유 / 막혔던 지점과 해결 / 다음 단계 주의사항.

BM25 한국어 처리의 한계, 인제스트 재실행 방식, 실측한 인제스트 소요 시간을
반드시 포함할 것.

## 완료 판정 기준

실제로 실행해 확인할 것.

1. `uv run python -m app.rag.ingest` — `data/pdf`의 PDF가 인제스트되고,
   생성된 청크 수와 소요 시간이 출력된다
2. 인제스트를 두 번 연속 실행해도 청크 수가 늘어나지 않는다
3. `uv run pytest` — 전부 통과
4. `uv run ruff check .` — 통과
5. 서버 기동 후 `POST /api/ask` 에 `{"question":"연장근로 수당은 어떻게 계산하나요?"}`
   를 보내면 `citations`가 **1개 이상** 채워져 돌아온다
6. 반환된 인용의 `source`·`page`가 실제 PDF의 내용과 대응한다 (한 건이라도 눈으로 확인)
7. 위 전부 API 키 없이 동작한다

## 금지 사항

- **커밋하지 말 것.** 검토 후 상위에서 커밋한다.
- LangGraph, 에이전트 루프, 질의 재작성, 환각 검증을 만들지 말 것 (03단계)
- 프론트엔드·스트리밍을 만들지 말 것 (05단계)
- `docs/` 의 기존 문서를 수정하지 말 것 (`작업일지.md` 추가 기록만 허용)
- `archive/` 를 건드리지 말 것
- 형태소 분석기 도입 등 무거운 의존성을 임의로 추가하지 말 것

## 보고 형식

**300단어 이내**로 보고할 것.

1. 완료 판정 기준 7개 각각의 통과 여부 (실행 명령과 결과 요약)
2. 변경된 파일 목록
3. 설계와 다르게 구현한 부분과 그 이유
4. 인제스트 소요 시간과 생성된 청크 수
5. 막힌 것 / 03단계에 넘기는 주의사항
