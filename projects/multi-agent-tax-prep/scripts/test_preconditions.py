"""전제조건 검사와 대기열 동작을 확인한다.

**LLM 호출이 전혀 없다.** API 비용 0원.

에이전트가 LLM을 부르기 전에 되돌아 나오는 경로(전제조건 검사)와,
대기열을 다루는 함수(handoff / ask_user / request_research)만 다룬다.
LLM을 부르는 본체 동작은 scripts/test_router.py에서 확인한다.

라우터가 알아서 research를 붙여주면 전제조건 검사는 실행되지 않으므로,
그 안전망이 살아 있는지는 여기서만 확인할 수 있다.

실행:
    python scripts/test_preconditions.py
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

sys.stdout.reconfigure(encoding="utf-8")

from agents.planning import planning_agent  # noqa: E402
from agents.review import review_agent  # noqa: E402
from state import ask_user, handoff, request_research  # noqa: E402

END = "__end__"

results = []


def make_state(**overrides) -> dict:
    """테스트용 State를 만든다. 필요한 값만 덮어쓴다."""
    state = {
        "messages": [],
        "todo_agents": [],
        "executed_agents": [],
        "pending_agent": None,
        "revision_count": 0,
        "user_profile": None,
        "skip_research": False,
        "research_result": "",
        "planning_result": "",
        "review_result": "",
    }
    state.update(overrides)
    return state


def check(label: str, actual, expected) -> None:
    """기대값과 비교해 결과를 기록한다. 실패해도 멈추지 않고 끝까지 돌린다."""
    is_ok = actual == expected
    results.append(is_ok)
    print(f"  {'PASS' if is_ok else 'FAIL'}  {label}")
    if not is_ok:
        print(f"        기대: {expected}")
        print(f"        실제: {actual}")


print("=" * 60)
print("1. 정보가 없는데 조사를 거부하지 않았다 → LLM을 부르기 전에 조사로 보낸다")
print("-" * 60)

command = planning_agent(make_state(todo_agents=["planning"]))
check("planning이 research로 보낸다", command.goto, "research")
check("대기열 맨 앞에 research가 끼워진다", command.update["todo_agents"], ["research", "planning"])

command = review_agent(make_state(todo_agents=["review"]))
check("review가 research로 보낸다", command.goto, "research")
check("대기열 맨 앞에 research가 끼워진다", command.update["todo_agents"], ["research", "review"])


print()
print("=" * 60)
print("2. handoff — 자기를 빼고 다음 차례로 넘긴다")
print("-" * 60)

state = make_state(todo_agents=["research", "planning", "review"])
command = handoff(state, "research", {"research_result": "조사 완료"})
check("다음은 planning", command.goto, "planning")
check("대기열에서 자기를 뺀다", command.update["todo_agents"], ["planning", "review"])
check("실행 이력에 자기를 남긴다", command.update["executed_agents"], ["research"])
check("산출물을 기록한다", command.update["research_result"], "조사 완료")

state = make_state(todo_agents=["review"])
command = handoff(state, "review", {"review_result": "검토 완료"})
check("혼자면 끝으로 간다", command.goto, END)


print()
print("=" * 60)
print("3. request_research — 조사를 대기열 맨 앞에 끼워넣는다")
print("-" * 60)

state = make_state(todo_agents=["planning", "review"])
command = request_research(state, "planning")
check("research로 간다", command.goto, "research")
check("자기는 대기열에 남는다", command.update["todo_agents"], ["research", "planning", "review"])
check("실행 이력에는 안 남는다 (아직 일을 안 했으므로)", "executed_agents" in command.update, False)


print()
print("=" * 60)
print("4. ask_user — 대기열을 유지한 채 턴만 끝낸다")
print("-" * 60)

state = make_state(todo_agents=["research", "planning"])
command = ask_user(state, "research", "작년 수입이 얼마였나요?")
check("턴이 끝난다", command.goto, END)
check("돌아올 자리를 남긴다", command.update["pending_agent"], "research")
check("대기열은 건드리지 않는다", "todo_agents" in command.update, False)


print()
print("=" * 60)
print(f"결과: {sum(results)}/{len(results)} 통과")
