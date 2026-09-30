"""최상위 그래프 — 사용자 요청을 보고 필요한 에이전트만 골라 순서대로 실행한다.

흐름:
    [사용자 입력] → 라우터 → 고른 에이전트들을 차례로 → [응답]

라우터는 "어떤 역할이 필요한가"만 판단한다.
"장부냐 추계냐" 같은 세무 도메인 판별은 조사 에이전트 안에서 한다.
라우터가 도메인을 알기 시작하면 다른 주제로 확장할 수 없게 된다.
"""

from typing import Literal

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, RetryPolicy
from pydantic import BaseModel, Field

from agents.planning import planning_agent
from agents.research.graph import research_agent
from agents.review import review_agent
from llm import get_structured_llm
from state import AgentName, MainState

# 노드가 실패하면 자동으로 다시 시도한다.
# 무료 티어에서 429(요청 한도 초과)가 나면 잠깐 기다렸다 재시도하면 대개 통과한다.
# backoff_factor=2.0 → 대기 시간이 1초, 2초, 4초로 늘어난다 (지수 백오프).
NODE_RETRY = RetryPolicy(
    max_attempts=3,
    initial_interval=1.0,
    backoff_factor=2.0,
    max_interval=10.0,
    jitter=True,      # 대기 시간에 약간의 무작위를 섞어, 여러 요청이 동시에 재시도하는 것을 막는다
)


class RouteDecision(BaseModel):
    """라우터가 LLM에게서 받아올 판단 결과의 형태.

    with_structured_output에 이 클래스를 넘기면, LLM이 자유 문장 대신
    이 형태에 맞는 객체를 돌려준다. 문자열을 파싱할 필요가 없어진다.
    """

    agents: list[AgentName] = Field(
        description="실행할 에이전트를 실행 순서대로 나열한다. 여러 개면 research → planning → review 순서를 지킨다."
    )
    skip_research: bool = Field(
        description="사용자가 '추가 조사 없이', '조사하지 말고'처럼 조사를 명시적으로 거부했으면 true. 그냥 조사가 필요 없어 보이는 것뿐이면 false."
    )
    reason: str = Field(description="이렇게 고른 이유를 한 문장으로")


ROUTER_SYSTEM = """너는 사용자 요청을 보고 어떤 담당자에게 넘길지 정하는 배정 담당이다.

담당자는 셋이다.
- research(조사): 사용자의 상황을 파악하고, 무엇이 적용되는지 알아낸다.
  예) "나 신고 대상이야?", "뭐가 필요한지 알려줘", "내 상황 좀 파악해줘"
- planning(기획): 준비할 것들의 목록과 일정을 만든다.
  예) "준비 목록 만들어줘", "언제까지 뭘 해야 해?"
- review(검토): 이미 있는 내용을 점검해서 빠진 것이나 문제를 찾는다.
  예) "내가 쓴 거 봐줘", "이 지출 괜찮아?", "빠진 거 없나 확인해줘", "이거 되나?"

규칙
1. 요청에 필요한 담당자만 고른다. 불필요한 담당자를 넣지 않는다.
2. "조사하지 말고", "추가 조사 없이" 같은 말이 있으면 research를 빼라.
3. 여러 담당자가 필요하면 반드시 research → planning → review 순서로 나열한다.
4. 앞선 대화에서 이미 파악한 내용이 있고 사용자가 그것을 이어받는 요청을 하면,
   중복해서 research를 다시 넣지 않아도 된다.
5. **사용자가 구체적인 항목·내용·초안을 제시하면서 판단이나 점검을 요구하면
   review를 반드시 포함한다.** 상황 파악이 먼저 필요해 보여도 research만으로 끝내지 말고
   research → review로 이어라. 판단을 요구받았는데 파악만 하고 끝내면 요청에 답하지 못한 것이다.
"""


def build_router_llm():
    """라우터 전용 LLM을 만든다. 분류 결과를 RouteDecision 형태로 받는다."""
    return get_structured_llm(RouteDecision)


def route_request(state: MainState) -> Command[Literal["research", "planning", "review", "__end__"]]:
    """요청을 분류해 실행할 에이전트 대기열을 만들고, 첫 번째 에이전트로 넘긴다.

    Command는 "State를 이렇게 바꾸고(update), 다음은 여기로 가라(goto)"를
    한 번에 돌려주는 객체다. 라우팅 함수와 매핑 딕셔너리를 따로 두지 않아도 된다.
    """
    # 앞 턴에서 어떤 에이전트가 되물어서 끊긴 상태라면, 이번 입력은 그 질문에 대한 답이다.
    # 분류할 필요가 없으므로 LLM을 부르지 않고 곧장 돌려보낸다. (호출 1회 절약)
    pending = state.get("pending_agent")
    if pending:
        print(f"  [router] {pending} 이어서 진행 (되물음에 대한 답변)")
        return Command(
            update={
                "pending_agent": None,
                "executed_agents": [],
                # todo_agents는 건드리지 않는다. 끊긴 시점의 대기열이 그대로 남아 있다.
            },
            goto=pending,
        )

    router = build_router_llm()

    # 마지막 사용자 메시지가 이번에 판단할 요청이다
    latest_message = state["messages"][-1]

    try:
        decision = router.invoke(
            [
                ("system", ROUTER_SYSTEM),
                ("human", latest_message.text),
            ]
        )
        agents = decision.agents
        skip_research = decision.skip_research
        reason = decision.reason
    except Exception as error:
        # LLM 호출은 네트워크를 타므로 실패할 수 있다.
        # 프로그램을 죽이는 대신 조사부터 시키고 사용자에게 알린다.
        print(f"  [router] 분류 실패({type(error).__name__}) — 조사부터 진행합니다")
        agents = ["research"]
        skip_research = False
        reason = "분류 호출 실패로 기본 경로 사용"

    if not agents:
        # 세 담당자 중 아무도 필요 없다고 판단한 경우
        return Command(
            update={
                "messages": [("ai", "조사·기획·검토 중 무엇이 필요한지 조금 더 구체적으로 알려주세요.")],
                "todo_agents": [],
                "executed_agents": [],
            },
            goto=END,
        )

    skip_note = " (조사 생략 요청)" if skip_research else ""
    print(f"  [router] {' → '.join(agents)}{skip_note}  ({reason})")

    return Command(
        update={
            "todo_agents": agents,
            "skip_research": skip_research,
            # Checkpointer가 State를 다음 차례까지 들고 있으므로,
            # 실행 이력과 되돌리기 횟수는 매 요청마다 비워줘야 이번 차례 기준으로 센다
            "executed_agents": [],
            "revision_count": 0,
        },
        goto=agents[0],
    )


def build_graph():
    """노드와 엣지를 연결하고 그래프를 컴파일한다."""
    builder = StateGraph(MainState)

    # retry_policy는 노드 단위로 건다. 그 노드만 다시 돌리므로
    # 앞에서 이미 끝난 작업을 처음부터 반복하지 않는다.
    builder.add_node("router", route_request, retry_policy=NODE_RETRY)
    builder.add_node("research", research_agent, retry_policy=NODE_RETRY)
    builder.add_node("planning", planning_agent, retry_policy=NODE_RETRY)
    builder.add_node("review", review_agent, retry_policy=NODE_RETRY)

    builder.add_edge(START, "router")
    # router와 각 에이전트는 Command로 다음 목적지를 스스로 정하므로
    # add_conditional_edges나 add_edge를 따로 걸지 않는다.

    # InMemorySaver: 대화 내용을 메모리에 저장해 같은 thread_id면 이어서 기억한다.
    # 프로그램을 끄면 사라진다 (영구 저장이 필요하면 SqliteSaver 등으로 교체).
    checkpointer = InMemorySaver()

    return builder.compile(checkpointer=checkpointer)
