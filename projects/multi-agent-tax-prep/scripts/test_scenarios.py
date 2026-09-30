"""과제 검증 시나리오를 끝에서 끝까지 돌린다.

PRACTICE.md의 필수 조건을 실제 실행으로 확인한다.
  2번 — 요청에 따라 필요한 에이전트를 선택하는가
  3번 — 실행한 에이전트의 이름과 순서가 콘솔에 찍히는가
  4번 — 복합 요청에서 앞 단계 결과가 다음 에이전트에 전달되는가
  5번 — 같은 세션의 이전 대화를 기억해 후속 요청에 반영하는가

**LLM 호출이 발생한다.** 대략 20회 안팎이다.

실행:
    python scripts/test_scenarios.py
"""

import sys
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

sys.stdout.reconfigure(encoding="utf-8")

from env import load_env  # noqa: E402
from graph import build_graph  # noqa: E402

load_env()

# 출력이 길어서 앞부분만 보여준다. 전체를 보려면 이 값을 키우면 된다.
PREVIEW_CHARS = 100


def new_config() -> dict:
    """새 대화 세션을 연다. thread_id가 다르면 이전 대화를 기억하지 않는다."""
    return {
        "configurable": {"thread_id": str(uuid.uuid4())},
        "recursion_limit": 25,
        "max_concurrency": 3,
    }


def run(graph, config: dict, request: str) -> dict:
    """요청 하나를 실행하고 결과를 찍는다."""
    print(f"\n> {request}")
    print("-" * 60)

    result = graph.invoke({"messages": [("human", request)]}, config=config)

    executed = result.get("executed_agents", [])
    order = " → ".join(f"{i}. {name}" for i, name in enumerate(executed, start=1))
    print(f"\n[실행 순서] {order or '(없음)'}")

    labels = {
        "research": ("research_result", "조사 결과"),
        "planning": ("planning_result", "준비 목록"),
        "review": ("review_result", "검토 결과"),
    }
    for name in executed:
        key, label = labels[name]
        content = result.get(key, "")
        if content:
            preview = content[:PREVIEW_CHARS]
            suffix = " ..." if len(content) > PREVIEW_CHARS else ""
            print(f"\n■ {label}\n{preview}{suffix}")

    if not executed and result.get("messages"):
        print(result["messages"][-1].text)

    return result


def main() -> None:
    graph = build_graph()

    print("=" * 60)
    print("[1] 조사 단독 — 조건 2번")
    print("=" * 60)
    run(
        graph,
        new_config(),
        "실행 계획은 세우지 말고, 프리랜서 개발자인데 작년에 4천만원 벌었어. "
        "내가 신고 대상인지랑 뭐가 적용되는지만 알려줘.",
    )

    print()
    print("=" * 60)
    print("[2] 기획 단독 — 조사를 명시적으로 거부한 경우")
    print("=" * 60)
    run(
        graph,
        new_config(),
        "추가 조사 없이, 프리랜서 기준으로 종합소득세 준비 목록만 만들어줘.",
    )

    print()
    print("=" * 60)
    print("[3] 검토 단독 — 사용자가 직접 준 내용 (입구 B)")
    print("=" * 60)
    run(
        graph,
        new_config(),
        "프리랜서 개발자야. 작년에 노트북 200만원, 카페에서 작업하며 쓴 커피값, "
        "코딩 강의 50만원 썼는데 경비 되나?",
    )

    print()
    print("=" * 60)
    print("[4] 복합 — 조건 4번 (앞 단계 결과 전달)")
    print("=" * 60)
    run(
        graph,
        new_config(),
        "프리랜서 개발자인데 작년 수입 4천만원이야. 내 상황 파악하고 "
        "준비 목록 세운 뒤 검토해서 최종본 만들어줘.",
    )

    print()
    print("=" * 60)
    print("[5] 대화 기억 — 조건 5번 (같은 세션에서 후속 요청)")
    print("=" * 60)
    memory_config = new_config()
    run(graph, memory_config, "프리랜서 개발자인데 작년 수입 4천만원이야. 준비 목록 만들어줘.")
    run(graph, memory_config, "방금 목록에서 사무실 임차료 항목만 빼줘.")
    print("\n※ 후속 요청에서 소득유형·업종·수입을 다시 말하지 않았다.")
    print("   그래도 맥락이 유지되면 조건 5번 충족이다.")

    print()
    print("=" * 60)
    print("모든 시나리오 실행 완료")


if __name__ == "__main__":
    main()
