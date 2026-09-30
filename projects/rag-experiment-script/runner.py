# 실험 하나를 실제로 실행하는 모듈
# 흐름: 정답 데이터 읽기 -> 이미 한 문항 건너뛰기 -> 검색기 준비 -> 문항별 평가 -> 집계 저장
# 중간에 중단돼도 이어서 실행할 수 있도록, 문항 하나를 끝낼 때마다 즉시 파일에 기록한다.

import json          # JSON 읽기/쓰기
import time          # 소요 시간 측정과 대기
from pathlib import Path

from langchain_google_genai import ChatGoogleGenerativeAI   # rerank에서 문서를 채점할 LLM
from pydantic import BaseModel, Field                       # LLM 출력의 형식을 강제하는 스키마

import generation    # 답변 생성 / 인용 검사 / LLM 채점 함수들
import metrics       # 우리가 만든 지표 계산 함수들
import pipeline      # 코퍼스 준비 / 벡터스토어 / 검색기 / 비용 계수기


class RelevanceScore(BaseModel):
    # LLM이 문서 하나를 채점할 때 이 형식으로만 답하도록 강제하는 스키마
    score: int = Field(ge=1, le=10, description="질문과 이 문서의 관련성 점수(1~10)")
    reason: str = Field(description="그 점수를 준 이유")


def rerank_documents(cfg, query, docs, counter):
    # 검색된 문서들을 LLM이 하나씩 채점해서, 점수가 높은 순으로 다시 정렬한다.
    # 호출 수 = 후보 문서 수(top_n)이므로 문항당 top_n번의 LLM 호출이 발생한다.
    top_n = cfg["rerank"]["top_n"]
    max_retries = cfg["pacing"]["max_retries"]
    llm_sleep = cfg["pacing"]["llm_sleep_sec"]

    llm = ChatGoogleGenerativeAI(model=cfg["models"]["llm"])
    scorer = llm.with_structured_output(RelevanceScore)   # 답을 RelevanceScore 형식으로 받는다

    candidates = docs[:top_n]   # 후보를 top_n개로 제한 (LLM 비용을 통제하는 지점)
    scored = []
    for doc in candidates:
        prompt = (
            "다음 문서가 질문에 답하는 데 얼마나 관련 있는지 1~10점으로 평가하세요.\n\n"
            f"질문: {query}\n\n문서:\n{doc.page_content}"
        )
        # LLM 호출도 429가 날 수 있으므로 재시도로 감싼다
        result = pipeline.retry_on_429(lambda: scorer.invoke(prompt), max_retries)

        # 토큰 수는 실제 API 응답이 아니라 글자 수 기반 추정치다
        counter.add_llm(requests=1, tokens=len(prompt) // 2)
        scored.append((doc, result.score))

        time.sleep(llm_sleep)   # 분당 호출 한도(15회)를 넘지 않도록 대기

    # 점수가 높은 순으로 정렬 (reverse=True), key로 튜플의 두 번째 값(점수)을 기준 지정
    scored.sort(key=lambda pair: pair[1], reverse=True)
    return [doc for doc, score in scored]   # 문서만 뽑아서 새 순서로 반환


def load_cases(cfg, limit=None):
    # 정답 데이터(golden set)를 읽어서 평가할 문항 목록을 돌려준다
    golden_path = Path(cfg["data"]["golden_set"])
    cases = json.loads(golden_path.read_text(encoding="utf-8"))

    # case_indices가 있으면 "앞에서부터 N개"가 아니라 지정한 번호의 문항만 골라 쓴다.
    # 앞에서부터 자르면 쉬운 문항만 뽑혀서 점수가 만점에 붙어버리고(천장 효과),
    # 그러면 rerank처럼 순위를 고치는 기능의 효과를 측정할 수 없다.
    # .get()은 키가 없으면 오류 대신 None을 돌려주므로, 이 항목이 없는 기존 config도 그대로 동작한다.
    indices = cfg["evaluation"].get("case_indices")
    if indices:
        cases = [cases[i] for i in indices]   # 지정한 순서대로 문항을 뽑는다
        # 문항을 직접 골랐으므로 config의 개수 제한은 적용하지 않는다. --limit만 존중한다.
        return cases[:limit] if limit is not None else cases

    # LLM이 개입하는 실험(rerank 등)은 비용이 크므로 llm_limit(10문항)을, 그 외에는 retrieval_limit(35문항)을 쓴다
    uses_llm = cfg["rerank"]["enabled"] or cfg["evaluation"]["run_generation"] or cfg["evaluation"]["run_judge"]
    config_limit = cfg["evaluation"]["llm_limit"] if uses_llm else cfg["evaluation"]["retrieval_limit"]

    # 문항 수 제한: CLI의 --limit이 있으면 그것을 우선하고, 없으면 위에서 고른 config 값을 쓴다
    # (--limit은 "코드가 도는지 빠르게 확인"하는 용도라 config보다 우선순위가 높다)
    max_count = limit if limit is not None else config_limit
    if max_count is not None:
        cases = cases[:max_count]   # 앞에서부터 max_count개만 남긴다(슬라이싱)

    return cases


def load_done_questions(rows_path):
    # 이미 평가를 마친 문항의 질문 텍스트를 집합(set)으로 모아서 돌려준다.
    # 재실행할 때 이 집합에 있는 문항은 건너뛰므로, 중단 지점부터 이어서 진행할 수 있다.
    if not rows_path.exists():
        return set()   # 파일이 아직 없으면 "한 게 하나도 없다"는 뜻이므로 빈 집합

    done = set()
    # JSONL 형식: 한 줄에 JSON 하나. 줄 단위로 읽으면 파일 끝이 깨져 있어도 앞부분은 살릴 수 있다.
    for line in rows_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()          # 줄 앞뒤의 공백/줄바꿈 제거
        if not line:
            continue                 # 빈 줄은 건너뛴다
        try:
            row = json.loads(line)   # 한 줄을 딕셔너리로 변환
            done.add(row["question"])
        except json.JSONDecodeError:
            # 프로그램이 줄을 쓰던 도중에 강제 종료되면 마지막 줄이 깨질 수 있다.
            # 그 한 줄만 버리고 나머지는 그대로 사용한다.
            continue
    return done


def append_row(rows_path, row):
    # 문항 하나의 평가 결과를 파일 끝에 한 줄 추가한다(체크포인트).
    # "a" 모드 = append, 기존 내용을 지우지 않고 뒤에 이어 쓴다. ("w"는 파일을 덮어써서 쓰면 안 된다)
    with rows_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
        # ensure_ascii=False -> 한글이 \uXXXX로 깨지지 않고 그대로 저장된다


def add_generation(row, docs, case, cfg, counter):
    # evaluate_case()의 결과 딕셔너리(row)에 "답변 생성 + 채점" 관련 키들을 추가해서 돌려준다
    # run_generation이 꺼져 있으면 아무것도 하지 않고 row를 그대로 돌려준다 (기존 실험과 동일하게 동작)
    if not cfg["evaluation"]["run_generation"]:
        return row

    # 1) 검색된 문서(docs)를 근거로 실제 답변을 생성한다
    gen_result = generation.generate_answer(cfg, case["question"], docs, counter)
    row.update(gen_result)   # answer / citations / context_used / generation_latency_ms를 row에 합친다

    # 2) LLM 호출 없이, 인용이 규칙에 맞는지 검사한다 (비용 0)
    citation_result = generation.check_citations(gen_result["citations"], docs, case)
    row.update(citation_result)   # valid_citation / relevant_citation을 row에 합친다

    # 3) run_judge까지 켜져 있을 때만 LLM 채점을 추가로 돌린다 (run_generation만 켰을 때는 채점을 건너뛴다)
    if cfg["evaluation"]["run_judge"]:
        judge_result = generation.judge_answer(
            cfg,
            case["question"],
            case["target_answer"],       # 골든셋의 기준 정답
            gen_result["answer"],
            gen_result["context_used"],
            counter,
        )
        row.update(judge_result)   # judge_correctness 등 judge_ 접두사가 붙은 키들을 row에 합친다

    return row


def evaluate_case(retriever, case, cfg, counter):
    # 문항 하나를 검색하고 지표를 계산해서 결과 딕셔너리를 돌려준다
    k = cfg["search"]["k"]
    strategy = cfg["search"]["strategy"]
    max_retries = cfg["pacing"]["max_retries"]

    started = time.perf_counter()   # 검색 시작 시각
    # 검색도 429가 날 수 있으므로(질문을 벡터로 바꾸는 임베딩 호출이 들어감) 재시도로 감싼다
    docs = pipeline.retry_on_429(lambda: retriever.invoke(case["question"]), max_retries)
    latency_ms = (time.perf_counter() - started) * 1000   # 초 단위를 밀리초로

    # BM25는 벡터를 쓰지 않으므로 임베딩 호출이 없다. 그 외 전략은 질문 임베딩 1회가 발생한다.
    if strategy != "bm25":
        counter.add_embedding(requests=1, tokens=len(case["question"]) // 2)

    # rerank가 켜져 있으면 LLM이 문서를 다시 채점해서 순서를 바꾼다.
    # 지표는 docs의 순서를 보고 계산하므로, 이 재정렬이 page_hit@1 / MRR을 바꿀 수 있다.
    if cfg["rerank"]["enabled"]:
        docs = rerank_documents(cfg, case["question"], docs, counter)

    row = {
        "question": case["question"],
        "target_file_name": case["target_file_name"],
        "target_page_no": case["target_page_no"],
        # 검색 결과를 나중에 실패 원인 분석에 쓸 수 있도록 파일명·페이지만 남긴다
        "retrieved": [
            {"source": doc.metadata["source"], "page_no": doc.metadata["page_no"]}
            for doc in docs
        ],
        "file_hit_1": metrics.file_hit_at_k(docs, case, 1),
        "page_hit_1": metrics.page_hit_at_k(docs, case, 1),
        "page_hit_3": metrics.page_hit_at_k(docs, case, 3),
        "page_hit_5": metrics.page_hit_at_k(docs, case, 5),
        "reciprocal_rank": metrics.reciprocal_rank(docs, case),
        "latency_ms": latency_ms,
    }

    # run_generation이 켜져 있으면 답변 생성 + 인용 검사 + (옵션) LLM 채점 결과를 row에 추가한다
    row = add_generation(row, docs, case, cfg, counter)

    return row


def average(rows, key):
    # rows 안의 각 행에서 key 값을 모아 평균을 낸다 (행이 없으면 0.0)
    return sum(row[key] for row in rows) / len(rows) if rows else 0.0


def summarize(cfg, rows, counter, total_sec):
    # 문항별 결과(rows)를 하나의 요약 딕셔너리로 집계한다. report.py가 이 형식을 읽는다.
    summary = {
        "experiment_name": cfg["experiment_name"],
        "quality": {
            "file_hit_1": average(rows, "file_hit_1"),
            "page_hit_1": average(rows, "page_hit_1"),
            "page_hit_3": average(rows, "page_hit_3"),
            "page_hit_5": average(rows, "page_hit_5"),
            "mrr": average(rows, "reciprocal_rank"),   # 여러 문항의 RR 평균이 MRR이다
        },
        "cost": counter.as_dict(),
        "time": {
            "total_sec": total_sec,
            "avg_latency_ms": average(rows, "latency_ms"),
        },
        "count": len(rows),
    }

    # rows 중 하나라도 "valid_citation" 키를 가지고 있으면 생성/채점을 돌린 실험이라는 뜻이다.
    # any(...) -> 하나라도 True면 True. 옛날 실험(run_generation=false)의 rows에는 이 키가 아예 없으므로
    # 이 조건이 False가 되고, 그러면 "generation" 블록 자체를 만들지 않아 report.py가 그대로 동작한다.
    has_generation = any("valid_citation" in row for row in rows)
    if has_generation:
        # average()는 row[key]가 모든 row에 있다고 가정하므로, generation 관련 row만 따로 모아서 평균낸다
        gen_rows = [row for row in rows if "valid_citation" in row]
        summary["generation"] = {
            "valid_citation": average(gen_rows, "valid_citation"),       # bool의 평균 -> True 비율
            "relevant_citation": average(gen_rows, "relevant_citation"),
            "generation_latency_ms": average(gen_rows, "generation_latency_ms"),
        }

        # judge_answer까지 돈 row만 judge_ 관련 키를 갖고 있으므로 한 번 더 걸러서 평균낸다
        judge_rows = [row for row in gen_rows if "judge_average" in row]
        if judge_rows:
            summary["generation"]["judge_correctness"] = average(judge_rows, "judge_correctness")
            summary["generation"]["judge_completeness"] = average(judge_rows, "judge_completeness")
            summary["generation"]["judge_groundedness"] = average(judge_rows, "judge_groundedness")
            summary["generation"]["judge_citation_accuracy"] = average(judge_rows, "judge_citation_accuracy")
            summary["generation"]["judge_average"] = average(judge_rows, "judge_average")

    return summary


def run_experiment(cfg, limit=None, result_dir="outputs"):
    # 실험 하나를 처음부터 끝까지 실행한다
    started_all = time.perf_counter()
    counter = pipeline.CostCounter()   # 이 실험의 API 호출·토큰을 셀 계수기

    # 결과를 저장할 폴더를 만든다 (parents=True: 중간 폴더까지, exist_ok=True: 이미 있어도 오류 없음)
    out_dir = Path(result_dir) / cfg["experiment_name"]
    out_dir.mkdir(parents=True, exist_ok=True)
    rows_path = out_dir / "rows.jsonl"

    # 1) 평가할 문항 목록
    cases = load_cases(cfg, limit)

    # 2) 이미 끝낸 문항 확인 (체크포인트)
    done_questions = load_done_questions(rows_path)
    if done_questions:
        print(f"이미 끝난 문항 {len(done_questions)}개를 건너뜁니다.")
    todo = [case for case in cases if case["question"] not in done_questions]

    # 3) 코퍼스 준비
    documents = pipeline.load_and_chunk(cfg)
    print(f"청크 {len(documents)}개 준비 완료")

    # 4) 벡터스토어 준비 — BM25는 벡터를 쓰지 않으므로 만들지 않는다(임베딩 비용 0)
    if cfg["search"]["strategy"] == "bm25":
        vectorstore = None
        print("BM25 전략이므로 벡터스토어를 만들지 않습니다(임베딩 호출 없음)")
    else:
        vectorstore = pipeline.build_vectorstore(cfg, documents, counter)

    # 5) 검색기 준비
    retriever = pipeline.build_retriever(cfg, vectorstore, documents)

    # 6) 남은 문항을 하나씩 평가하고, 끝날 때마다 즉시 파일에 기록
    for index, case in enumerate(todo, start=1):
        row = evaluate_case(retriever, case, cfg, counter)
        append_row(rows_path, row)   # ← 여기서 바로 저장하므로 다음 문항에서 죽어도 이건 남는다
        print(f"[{index}/{len(todo)}] page_hit_5={row['page_hit_5']} ({row['latency_ms']:.0f}ms)")

    # 7) 집계 — 이번에 돌린 것뿐 아니라 이전에 기록된 문항까지 전부 다시 읽어서 평균을 낸다
    all_rows = []
    for line in rows_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            all_rows.append(json.loads(line))

    total_sec = time.perf_counter() - started_all
    summary = summarize(cfg, all_rows, counter, total_sec)

    (out_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n요약 저장: {out_dir / 'summary.json'}")
    return summary


def estimate_cost(cfg, limit=None):
    # --dry-run 용: API를 부르지 않고 예상 호출 수만 계산한다
    cases = load_cases(cfg, limit)
    strategy = cfg["search"]["strategy"]

    # 문서 임베딩: 이미 같은 청킹의 컬렉션이 저장돼 있으면 0번, 없으면 (청크 수 / 배치 크기)번
    documents = pipeline.load_and_chunk(cfg)
    batch_size = cfg["pacing"]["embed_batch_size"]
    if strategy == "bm25":
        doc_requests = 0
    else:
        # -(-a // b)는 a/b를 올림한 값 (예: 402개를 10개씩 -> 41번)
        doc_requests = -(-len(documents) // batch_size)

    # 질문 임베딩: BM25는 0번, 그 외는 문항 수만큼
    query_requests = 0 if strategy == "bm25" else len(cases)

    # LLM 호출: 문항 하나당 몇 번이 필요한지 단계별로 더한다.
    # (문항 수는 load_cases가 이미 llm_limit을 적용해 돌려주므로 len(cases)를 그대로 쓴다)
    per_case = 0
    if cfg["rerank"]["enabled"]:
        per_case += cfg["rerank"]["top_n"]      # rerank는 후보 문서를 하나씩 채점하므로 top_n번
    if cfg["evaluation"]["run_generation"]:
        per_case += 1                            # 답변 생성 1번
    if cfg["evaluation"]["run_judge"]:
        per_case += 1                            # 생성된 답변 채점 1번
    llm_requests = per_case * len(cases)

    return {
        "experiment_name": cfg["experiment_name"],
        "chunks": len(documents),
        "cases": len(cases),
        "embedding_requests_documents": doc_requests,
        "embedding_requests_queries": query_requests,
        "embedding_requests_total": doc_requests + query_requests,
        "llm_requests_per_case": per_case,   # 문항당 LLM 호출 수 (rerank + 생성 + 채점)
        "llm_requests": llm_requests,
        # LLM은 요청 간 대기가 있어 시간이 병목이므로 예상 소요 시간도 함께 알려준다
        "llm_estimated_minutes": round(llm_requests * (cfg["pacing"]["llm_sleep_sec"] + 2) / 60, 1),
    }
