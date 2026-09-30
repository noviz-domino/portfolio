"""라우터와 전제조건 검사가 제대로 동작하는지 확인한다.

에이전트는 아직 스텁이므로 내용은 검사하지 않는다.
확인 대상은 "어떤 에이전트가 어떤 순서로 실행됐는가" 하나다.

요청 하나당 LLM 호출 1회(라우터)만 발생한다. 에이전트는 스텁이라 호출하지 않는다.

실행:
    python scripts/test_router.py
"""

import sys
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# Windows 콘솔의 기본 인코딩이 UTF-8이 아니면 한글이 깨진다.
sys.stdout.reconfigure(encoding="utf-8")

from env import load_env  # noqa: E402
from graph import build_graph  # noqa: E402

load_env()

# (설명, 요청, 기대하는 실행 순서)
TEST_CASES = [
    # --- 요청과 담당자가 곧바로 맞아떨어지는 경우 ---
    (
        "조사 단독",
        "프리랜서인데 나 종합소득세 신고 대상이야?",
        ["research"],
    ),
    (
        "복합 (조사→기획→검토)",
        "내 상황 파악하고 준비 목록 세운 뒤 검토해서 최종본 만들어줘.",
        ["research", "planning", "review"],
    ),

    # --- 조사를 명시적으로 거부한 경우: 보충하지 않고 가정으로 진행 ---
    (
        "조사 거부 + 기획",
        "추가 조사 없이, 지금 아는 내용으로 준비 목록 만들어줘.",
        ["planning"],
    ),

    # --- 정보 없이 뒷단계부터 요청한 경우: 조사가 자동으로 앞에 붙어야 한다 ---
    (
        "정보 없이 검토부터 (자동 보충)",
        "노트북 200만원 썼는데 경비 되나?",
        ["research", "review"],
    ),
    (
        "정보 없이 기획부터 (자동 보충)",
        "신고 준비 목록 만들어줘.",
        ["research", "planning"],
    ),
]


def main() -> None:
    graph = build_graph()

    passed = 0

    for index, (label, request, expected) in enumerate(TEST_CASES, start=1):
        # 케이스마다 새 thread_id를 쓴다. 같은 세션이면 앞 대화가 분류에 영향을 준다.
        config = {
            "configurable": {"thread_id": str(uuid.uuid4())},
            "recursion_limit": 25,
        }

        print(f"\n{'=' * 60}")
        print(f"[{index}] {label}")
        print(f"    {request}")
        print("-" * 60)

        result = graph.invoke({"messages": [("human", request)]}, config=config)
        actual = result.get("executed_agents", [])

        is_ok = actual == expected
        passed += is_ok

        print(f"  기대: {' → '.join(expected)}")
        print(f"  실제: {' → '.join(actual) if actual else '(없음)'}")
        print(f"  {'PASS' if is_ok else 'FAIL'}")

    print(f"\n{'=' * 60}")
    print(f"결과: {passed}/{len(TEST_CASES)} 통과")


if __name__ == "__main__":
    main()
