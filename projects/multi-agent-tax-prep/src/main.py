"""대화형 진입점 — 사용자 입력을 반복해서 받고 그래프의 응답을 출력한다.

한 번 실행하는 동안은 같은 thread_id를 쓰므로, 앞서 나눈 대화를 기억한 채
후속 요청을 처리한다. ("방금 목록에서 임차료만 빼줘" 같은 요청이 통한다)
"""

import uuid

from env import load_env
from graph import build_graph

EXIT_COMMANDS = {"quit", "exit", "q", "종료", "나가기"}

# 그래프가 돌 수 있는 최대 스텝 수. 조건식 버그로 무한루프가 돌면 여기서 끊긴다.
# 업무 규칙(검토 최대 2회)과는 다른 층위의 안전망이다.
RECURSION_LIMIT = 25

# 조사 에이전트가 worker를 병렬로 돌릴 때 동시 실행 개수.
# 한꺼번에 던지면 무료 티어의 분당 요청 한도에 걸려 429가 난다.
MAX_CONCURRENCY = 3

# 실행 결과를 화면에 찍을 때 쓸 이름표
RESULT_LABELS = {
    "research": ("research_result", "조사 결과"),
    "planning": ("planning_result", "준비 목록"),
    "review": ("review_result", "검토 결과"),
}


def print_response(result: dict) -> None:
    """실행된 에이전트의 이름·순서와 각 산출물을 출력한다."""
    executed = result.get("executed_agents", [])

    if executed:
        # 과제 조건: 실제 실행한 에이전트의 이름과 호출 순서를 확인할 수 있게 출력
        order = " → ".join(f"{i}. {name}" for i, name in enumerate(executed, start=1))
        print(f"\n[실행 순서] {order}")

    print("-" * 60)

    for name in executed:
        state_key, label = RESULT_LABELS[name]
        content = result.get(state_key)
        if content:
            print(f"\n■ {label}")
            print(content)

    # 라우터가 아무도 고르지 않은 경우엔 안내 메시지가 messages에 들어 있다
    if not executed and result.get("messages"):
        print(result["messages"][-1].text)

    print("-" * 60)


def main() -> None:
    load_env()

    graph = build_graph()

    # thread_id는 대화 세션을 구분하는 열쇠다. 이번 실행 내내 같은 값을 쓴다.
    config = {
        "configurable": {"thread_id": str(uuid.uuid4())},
        "recursion_limit": RECURSION_LIMIT,
        "max_concurrency": MAX_CONCURRENCY,
    }

    print("=" * 60)
    print("종합소득세 신고 준비 도우미")
    print(f"종료하려면 {', '.join(sorted(EXIT_COMMANDS))} 중 하나를 입력하세요.")
    print("=" * 60)

    while True:
        try:
            user_input = input("\n무엇을 도와드릴까요? > ").strip()
        except (KeyboardInterrupt, EOFError):
            # Ctrl+C나 Ctrl+D로 빠져나갈 때 에러 대신 정상 종료로 처리한다
            print("\n종료합니다.")
            break

        if not user_input:
            continue

        if user_input.lower() in EXIT_COMMANDS:
            print("종료합니다.")
            break

        try:
            result = graph.invoke(
                {"messages": [("human", user_input)]},
                config=config,
            )
        except Exception as error:
            # 실패해도 루프를 유지한다. 한 번 실패했다고 프로그램이 죽으면
            # 사용자는 처음부터 다시 입력해야 한다.
            print(f"\n처리 중 문제가 발생했습니다: {type(error).__name__}: {error}")
            continue

        print_response(result)


if __name__ == "__main__":
    main()
