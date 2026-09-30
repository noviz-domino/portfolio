# 검색 결과를 바탕으로 실제 답변을 "생성"하고, 그 답변의 품질을 LLM으로 "채점"하는 모듈
# runner.py의 evaluate_case()가 검색을 마친 뒤에 이 모듈의 함수들을 순서대로 호출한다.

import time          # LLM 호출 사이 대기(sleep)와 소요 시간 측정에 사용
from pathlib import Path   # 프롬프트 파일 경로를 다루는 표준 라이브러리 객체

from langchain_google_genai import ChatGoogleGenerativeAI   # 답변 생성/채점에 쓰는 채팅 LLM
from pydantic import BaseModel, Field                        # LLM 출력의 형식을 강제하는 스키마

import pipeline   # retry_on_429 등 재시도/공용 함수를 재사용하기 위해 import


class GroundedAnswer(BaseModel):
    # LLM이 답변을 생성할 때 이 형식으로만 답하도록 강제하는 스키마 (runner.RelevanceScore와 같은 패턴)
    answer: str = Field(description="검색 문맥을 근거로 작성한 답변")
    citations: list[str] = Field(description="답변에 사용한 문서 파일명 목록")


class JudgeScore(BaseModel):
    # LLM이 생성된 답변을 채점할 때 이 형식으로만 답하도록 강제하는 스키마
    # ge=1, le=10 -> 점수가 1 이상 10 이하가 아니면 pydantic이 자동으로 에러를 내준다
    correctness: int = Field(ge=1, le=10, description="기준 정답과 비교했을 때 사실관계가 얼마나 정확한지 (1~10)")
    completeness: int = Field(ge=1, le=10, description="기준 정답에 필요한 내용을 빠짐없이 담았는지 (1~10)")
    groundedness: int = Field(ge=1, le=10, description="답변 내용이 검색 문맥으로 뒷받침되는지, 문맥에 없는 말을 지어내지 않았는지 (1~10)")
    citation_accuracy: int = Field(ge=1, le=10, description="인용한 파일이 실제로 답변의 근거가 맞는지 (1~10)")
    reason: str = Field(description="위 네 항목을 각각 왜 그렇게 채점했는지, 감점 이유는 무엇인지")


def load_prompt(path):
    # 프롬프트 템플릿 파일(.txt)을 읽어서 문자열로 돌려준다
    prompt_path = Path(path)   # 문자열 경로를 Path 객체로 바꿔서 exists() 등을 쓸 수 있게 한다

    if not prompt_path.exists():
        # 파일이 없을 때 파이썬 기본 에러 대신, 어떤 경로가 문제인지 한국어로 알려준다
        raise FileNotFoundError(f"프롬프트 파일을 찾을 수 없습니다: {prompt_path} (evaluation.prompt_path 설정을 확인하세요)")

    return prompt_path.read_text(encoding="utf-8")   # encoding="utf-8" -> 한글이 깨지지 않게 읽는다


def build_context(docs, context_k):
    # 검색된 문서(docs) 중 앞의 context_k개만 골라서, LLM에게 줄 하나의 문맥 문자열로 합친다
    selected = docs[:context_k]   # 슬라이싱 -> 검색 순위 상위 context_k개만 사용 (비용/토큰 통제)

    pieces = []   # 문서 하나씩 "[출처: ...] + 본문" 형태로 만들어 담을 리스트
    for doc in selected:
        source = doc.metadata["source"]     # 파일명 (예: "a.pdf")
        page_no = doc.metadata["page_no"]   # 사람이 읽기 쉬운 1부터 시작하는 페이지 번호
        # 출처(파일명·페이지)를 본문 앞에 함께 넣어야, LLM이 나중에 citations에 어떤 파일을
        # 인용했는지 정확히 답할 수 있다. 출처 없이 본문만 주면 LLM이 파일명을 지어낼 수 있다.
        pieces.append(f"[출처: {source} p.{page_no}]\n{doc.page_content}")

    return "\n\n".join(pieces)   # 문서 사이에 빈 줄을 하나씩 넣어서 하나의 큰 문자열로 합친다


def generate_answer(cfg, question, docs, counter):
    # 검색된 문서(docs)를 근거로 실제 답변 하나를 LLM에게 생성시킨다
    prompt_path = cfg["evaluation"]["prompt_path"]   # 어떤 프롬프트 파일을 쓸지 (basic.txt / grounded.txt)
    context_k = cfg["evaluation"]["context_k"]        # 문맥에 넣을 검색 문서 개수
    max_retries = cfg["pacing"]["max_retries"]
    llm_sleep = cfg["pacing"]["llm_sleep_sec"]

    template = load_prompt(prompt_path)          # 프롬프트 템플릿 원문 텍스트
    context = build_context(docs, context_k)      # 문서들을 하나의 문맥 문자열로 합친 것

    # .format() 대신 .replace()를 쓰는 이유: 프롬프트 텍스트나 문맥 안에 { } 문자가
    # 그대로 들어있을 수 있는데, .format()은 그런 중괄호까지 자리표시자로 해석해서 에러를 낸다.
    prompt = template.replace("{question}", question).replace("{context}", context)

    llm = ChatGoogleGenerativeAI(model=cfg["models"]["llm"])
    generator = llm.with_structured_output(GroundedAnswer)   # 답을 GroundedAnswer 형식으로만 받는다

    started = time.perf_counter()   # 생성 시작 시각
    # 429(요청 과다) 에러가 나면 retry_on_429가 대기 후 재시도해준다
    result = pipeline.retry_on_429(lambda: generator.invoke(prompt), max_retries)
    latency_ms = (time.perf_counter() - started) * 1000   # 초 단위를 밀리초로 환산

    # 토큰 수는 실제 API 응답값이 아니라 "글자 수 // 2"로 어림잡은 추정치다 (한국어는 대략 2글자당 1토큰)
    counter.add_llm(requests=1, tokens=len(prompt) // 2)

    time.sleep(llm_sleep)   # 분당 호출 한도를 넘지 않도록 다음 호출 전에 대기

    return {
        "answer": result.answer,
        "citations": result.citations,
        "context_used": context,             # 나중에 실패 원인을 볼 때, 실제로 어떤 문맥을 줬는지 확인용
        "generation_latency_ms": latency_ms,
    }


def check_citations(citations, docs, case):
    # LLM 호출 없이, 규칙만으로 인용이 타당한지 검사한다 (비용이 들지 않는 채점)
    retrieved_sources = {doc.metadata["source"] for doc in docs}   # {} -> set, 검색된 문서들의 파일명 집합
    cited_sources = set(citations)   # LLM이 답변에서 인용했다고 한 파일명들의 집합

    # A <= B는 "집합 A가 집합 B의 부분집합인가"를 검사한다.
    # 즉 cited_sources <= retrieved_sources는 "인용한 파일명이 전부 실제 검색된 문서 안에 있는가"라는 뜻이다.
    valid_citation = len(cited_sources) > 0 and cited_sources <= retrieved_sources

    # 정답 파일(case["target_file_name"])이 인용 목록 안에 있는지 확인한다
    relevant_citation = case["target_file_name"] in cited_sources

    return {
        "valid_citation": valid_citation,
        "relevant_citation": relevant_citation,
    }


def judge_answer(cfg, question, expected_answer, answer, context, counter):
    # 생성된 답변을 LLM 심사위원(judge)에게 채점시킨다. rerank_documents와 같은 LLM 호출 패턴을 따른다.
    max_retries = cfg["pacing"]["max_retries"]
    llm_sleep = cfg["pacing"]["llm_sleep_sec"]

    llm = ChatGoogleGenerativeAI(model=cfg["models"]["llm"])
    judge = llm.with_structured_output(JudgeScore)   # 답을 JudgeScore 형식으로만 받는다

    prompt = (
        "다음 답변을 기준 정답과 검색 문맥에 비추어 채점하세요. "
        "각 항목은 1~10점이며, 감점 이유도 구체적으로 적으세요.\n\n"
        f"질문: {question}\n\n"
        f"기준 정답: {expected_answer}\n\n"
        f"생성된 답변: {answer}\n\n"
        f"검색 문맥:\n{context}"
    )

    # LLM 호출도 429가 날 수 있으므로 재시도로 감싼다
    result = pipeline.retry_on_429(lambda: judge.invoke(prompt), max_retries)

    # 토큰 수는 실제 API 응답이 아니라 글자 수 기반 추정치다
    counter.add_llm(requests=1, tokens=len(prompt) // 2)

    time.sleep(llm_sleep)   # 분당 호출 한도를 넘지 않도록 대기

    # 네 항목의 평균 점수. round(값, 2) -> 소수점 셋째 자리에서 반올림해서 둘째 자리까지 남긴다
    average = round(
        (result.correctness + result.completeness + result.groundedness + result.citation_accuracy) / 4,
        2,
    )

    # rows.jsonl에 검색 지표(page_hit_1 등)와 같이 저장되므로, 이름이 겹치지 않도록 judge_ 접두사를 붙인다
    return {
        "judge_correctness": result.correctness,
        "judge_completeness": result.completeness,
        "judge_groundedness": result.groundedness,
        "judge_citation_accuracy": result.citation_accuracy,
        "judge_reason": result.reason,
        "judge_average": average,
    }
