"""기획 에이전트 — 준비할 자료 목록과 마감 역산 일정을 만든다.

조사 결과가 있으면 판별된 신고 방식에 맞춰 목록이 달라진다.
단순경비율이면 경비 증빙 항목이 통째로 빠지고, 복식부기면 전부 필요하다.
"""

from typing import Literal

from langgraph.types import Command

from llm import get_llm
from state import MainState, handoff, request_research

PlanningGoto = Literal["research", "review", "__end__"]

# --- 범용 층: 역할 정의 (도메인이 바뀌어도 그대로 쓴다) ---
PLANNING_ROLE = """너는 파악된 상황을 바탕으로 실행 계획을 세우는 기획 담당이다.

원칙
- 무엇을, 어디서, 언제까지 해야 하는지가 드러나게 쓴다.
- 조사 결과에 없는 내용을 지어내지 않는다.
- 추정한 조건은 '가정' 항목에 따로 적는다.
"""

# --- 도메인 층: 세무 지식 ---
PLANNING_DOMAIN = """참고 지식 — 종합소득세 준비

신고 일정
- 종합소득세 확정신고: 5월 1일 ~ 5월 31일
- 지급명세서는 3~4월에 홈택스에 쌓인다. 거래처가 제출하지 않으면 내 수입이 안 잡힌다.
- 홈택스에 종합소득세 신고를 마쳐도 지방소득세는 위택스에서 따로 신고해야 한다.

신고 방식별로 필요한 것
- 단순경비율 추계: 경비 증빙 불필요. 소득공제·세액공제 증빙만 모은다.
- 기준경비율 추계: 주요경비 3종(매입비용·임차료·인건비) 증빙 + 주요경비지출명세서
- 간편장부: 간편장부 + 총수입금액 및 필요경비명세서 + 전체 경비 증빙
- 복식부기: 재무상태표 + 손익계산서 + 조정계산서 + 전체 경비 증빙

자주 놓치는 것
- 사업용 신용카드를 홈택스에 등록하지 않으면 사용내역이 자동 수집되지 않는다.
- 현금영수증은 '소득공제용'이 아니라 '지출증빙용'으로 받아야 경비로 쓸 수 있다.
- 노란우산공제 납입증명서는 중소기업중앙회에서 따로 받아야 한다.

출력 형식
- 준비물은 표로 정리한다. 열은 '항목 | 어디서 | 언제까지 | 왜 필요한가'로 한다.
- 표 다음에 마감 역산 일정을 간단히 적는다.
- 세액이나 환급액은 절대 계산하지 않는다.
- 마지막에 '가정' 항목을 두고 추정한 조건을 적는다.
"""

PLANNING_PROMPT = PLANNING_ROLE + "\n" + PLANNING_DOMAIN


def planning_agent(state: MainState) -> Command[PlanningGoto]:
    """준비물 목록을 만들고 State에 기록한 뒤 다음 에이전트로 넘긴다."""

    # 전제조건: 신고 방식을 알아야 목록을 만들 수 있다.
    # 단순경비율이면 경비 증빙이 통째로 빠지고, 장부 기장이면 전부 필요하다.
    # 모르는 채로 목록을 만들면 절반은 틀린 목록이 된다.
    research = state.get("research_result")
    if not research:
        if not state.get("skip_research"):
            return request_research(state, "planning")
        # 사용자가 조사를 거부했으면 조사로 보내지 않는다.
        print("  [planning] 조사 없이 진행 — 가정을 명시합니다")
        research = "(조사를 수행하지 않았습니다. 일반적인 경우를 가정해야 합니다.)"

    print("  [planning] 준비 목록 작성 중...")

    # 이번 턴에 사용자가 실제로 요청한 문장. 여기에 추가 조건이 담겨 있을 수 있다.
    request = state["messages"][-1].text

    planner = get_llm()
    response = planner.invoke(
        [
            ("system", PLANNING_PROMPT),
            (
                "human",
                f"사용자 요청: {request}\n\n"
                f"아래는 조사 담당이 파악한 결과다. 이 결과에 맞는 준비물 목록과 일정을 만들어줘.\n\n"
                f"{research}",
            ),
        ]
    )

    return handoff(state, "planning", {"planning_result": response.text})
