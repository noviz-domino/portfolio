"""그래프 전체가 공유하는 State와, 에이전트 간 인계(handoff) 헬퍼.

State를 별도 모듈로 두는 이유: graph.py와 각 에이전트가 서로를 import하면
순환 참조(circular import)가 난다. 공통으로 쓰는 타입만 여기에 모아둔다.
"""

from typing import Annotated, Literal, TypedDict

from langgraph.graph import END
from langgraph.graph.message import add_messages
from langgraph.types import Command

# 라우터가 고를 수 있는 에이전트 이름.
# 이 문자열은 그래프에 등록하는 노드 이름과 반드시 같아야 한다.
AgentName = Literal["research", "planning", "review"]


class MainState(TypedDict):
    """노드들이 공유하는 데이터 보관함.

    한 노드가 여기에 결과를 넣으면 다음 노드가 꺼내 쓴다.
    이 구조 덕분에 "앞 단계 결과를 다음 에이전트에 전달"이 자연스럽게 해결된다.
    """

    # Annotated[list, add_messages] = 이 필드는 덮어쓰지 말고 "이어붙여라"는 표시.
    # add_messages는 LangGraph가 주는 reducer(누적 함수)로, 대화 기록을 쌓는다.
    messages: Annotated[list, add_messages]

    todo_agents: list[AgentName]      # 아직 실행하지 않은 에이전트 대기열 (맨 앞이 지금 차례)
    executed_agents: list[AgentName]  # 실제로 실행한 순서 (콘솔 출력용)

    # 에이전트가 사용자에게 되물어서 턴이 끊긴 경우, 다음 턴에 돌아갈 자리.
    # 이게 있으면 라우터는 LLM을 부르지 않고 곧장 그 에이전트로 보낸다.
    pending_agent: AgentName | None

    # 검토가 기획을 되돌린 횟수. 둘이 무한히 핑퐁하는 것을 막는다.
    revision_count: int

    # 조사가 파악한 사용자 정보 (소득 유형, 업종, 직전연도 수입 등).
    # 기획·검토는 이걸 읽어서 일한다.
    user_profile: dict | None

    # 사용자가 "추가 조사 없이"처럼 조사를 명시적으로 거부했는가.
    # True면 정보가 없어도 조사로 보내지 않고, 가정을 명시하고 진행한다.
    skip_research: bool

    research_result: str              # 조사 에이전트 산출물
    planning_result: str              # 기획 에이전트 산출물
    review_result: str                # 검토 에이전트 산출물


def handoff(state: MainState, current: AgentName, updates: dict) -> Command:
    """현재 에이전트를 끝내고 대기열의 다음 에이전트로 넘긴다.

    handoff = (업무를) 넘겨주다. 멀티 에이전트에서 한 에이전트가 다음 에이전트에게
    제어권을 넘기는 것을 부르는 표준 용어다.

    Args:
        state: 현재 State
        current: 방금 일을 마친 에이전트 이름
        updates: State에 기록할 산출물 (예: {"research_result": "..."})
    """
    # 대기열의 맨 앞이 자기 자신이므로 잘라낸다
    remaining = state["todo_agents"][1:]

    # 남은 게 있으면 그 첫 번째로, 없으면 그래프를 끝낸다
    goto = remaining[0] if remaining else END

    return Command(
        update={
            **updates,                                              # 산출물 기록
            "todo_agents": remaining,                               # 대기열 갱신
            "executed_agents": state["executed_agents"] + [current],  # 실행 이력에 추가
        },
        goto=goto,
    )


def request_research(state: MainState, current: AgentName) -> Command:
    """일하는 데 필요한 정보가 없을 때, 조사를 먼저 시키고 자기에게 돌아오게 한다.

    대기열 맨 앞에 research를 끼워넣는다. 현재 에이전트는 그 뒤에 그대로 남아 있으므로,
    조사가 끝나고 handoff하면 자연스럽게 여기로 돌아온다.

    executed_agents에는 기록하지 않는다. 아직 자기 일을 한 게 아니기 때문이다.

    Args:
        state: 현재 State
        current: 정보가 부족해 조사를 요청하는 에이전트 이름
    """
    print(f"  [{current}] 판단에 필요한 정보가 없습니다 → research를 먼저 실행합니다")

    return Command(
        update={"todo_agents": ["research"] + state["todo_agents"]},
        goto="research",
    )


def ask_user(state: MainState, current: AgentName, question: str) -> Command:
    """판단에 필요한 정보가 없을 때, 사용자에게 되묻고 이번 턴을 끝낸다.

    handoff와 달리 대기열(todo_agents)을 건드리지 않는다. 자기 차례를 유지한 채
    pending_agent에 자기 이름을 남겨두면, 다음 턴에 라우터가 이를 보고
    LLM 호출 없이 곧장 여기로 돌려보낸다.

    Args:
        state: 현재 State
        current: 되묻는 에이전트 이름
        question: 사용자에게 보여줄 질문
    """
    return Command(
        update={
            "messages": [("ai", question)],
            "pending_agent": current,
            "executed_agents": state["executed_agents"] + [current],
        },
        goto=END,
    )
