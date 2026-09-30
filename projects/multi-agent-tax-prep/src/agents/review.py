"""검토 에이전트 — 빠뜨린 항목을 찾아내고, 필요하면 기획에게 다시 시킨다.

검토 대상이 들어오는 입구가 둘이다.
  A. 기획이 만든 준비물 목록 (state["planning_result"])  — 복합 요청의 마지막 단계
  B. 사용자가 직접 준 지출 내역·초안 (state["messages"])  — "이 지출 경비 되나?"

검토가 끝난 뒤 갈 수 있는 길도 둘이다.
  - 내 선에서 고칠 수 있다 → 고친 최종본을 내보내고 종료
  - 계획 자체가 잘못됐다   → 기획에게 되돌려 다시 짜게 한다 (사이클, 최대 1회)
"""

from typing import Literal

from langgraph.types import Command
from pydantic import BaseModel, Field

from llm import get_structured_llm
from state import MainState, handoff, request_research

ReviewGoto = Literal["research", "planning", "__end__"]

# 기획을 되돌릴 수 있는 최대 횟수.
# 검토와 기획이 서로 만족하지 못하고 무한히 주고받는 것을 막는다.
# main.py의 recursion_limit이 그 위를 받치는 안전망이고, 이쪽은 업무 규칙이다.
MAX_REVISIONS = 1


class ReviewResult(BaseModel):
    """검토 결과. 구조화된 출력으로 받아 사이클 판단까지 한 번에 처리한다."""

    issues: list[str] = Field(
        default_factory=list, description="빠졌거나 확인이 필요한 항목. 없으면 빈 목록"
    )
    final: str = Field(
        description="지적사항을 반영해 개선한 최종본. 검토 대상이 목록이면 보완된 목록을, "
        "지출 내역이면 항목별 판단을 적는다."
    )
    needs_replan: bool = Field(
        default=False,
        description="계획의 전제 자체가 틀려서 처음부터 다시 짜야 하는 경우에만 true. "
        "예를 들어 단순경비율 대상인데 경비 증빙을 잔뜩 요구하는 목록이 왔을 때. "
        "항목 몇 개를 보태면 되는 수준이면 false.",
    )


# --- 범용 층: 역할 정의 (도메인이 바뀌어도 그대로 쓴다) ---
REVIEW_ROLE = """너는 작성된 내용을 점검해 빠진 것과 문제를 찾아내는 검토 담당이다.

원칙
- 빠진 것을 찾는 데 집중한다. 칭찬이나 총평은 쓰지 않는다.
- 지적만 하고 끝내지 않는다. 지적사항을 반영한 최종본까지 만든다.
- 확인이 필요한 항목은 "확인하세요"로 쓰고, 단정하지 않는다.
"""

# --- 도메인 층: 세무 지식 ---
REVIEW_DOMAIN = """참고 지식 — 종합소득세에서 자주 빠지는 것

절차
- 홈택스에서 종합소득세를 신고해도 지방소득세는 위택스에서 따로 신고해야 한다. 빠뜨리면 가산세가 붙는다.
- 거래처가 지급명세서를 제출하지 않으면 내 수입이 홈택스에 안 잡힌다. 직접 확인해야 한다.

증빙
- 사업 관련 지출이 건당 3만원을 넘으면 적격증빙이 필요하다. 간이영수증은 적격증빙이 아니다.
- 현금영수증은 '지출증빙용'으로 받아야 한다. '소득공제용'으로 받으면 경비로 쓸 수 없다.
- 사업용 신용카드를 홈택스에 등록하지 않으면 사용내역이 자동 수집되지 않는다.

소득 유형에 따른 차이
- 근로소득자에게는 필요경비라는 개념이 없다. 신용카드 사용액 소득공제로 간다.
- 사업소득자에게는 신용카드 사용액 소득공제가 없다. 대신 필요경비로 처리한다.

개별 지출을 판단할 때
- "경비로 인정됩니다"라고 단정하지 않는다. "경비로 볼 여지가 있습니다"로 쓰고,
  필요한 증빙과 주의점을 함께 적는다.
- 최종 인정 여부는 사업 관련성에 대한 개별 판단이 필요하다는 점을 밝힌다.
- 세액이나 환급액은 절대 계산하지 않는다.
"""

REVIEW_PROMPT = REVIEW_ROLE + "\n" + REVIEW_DOMAIN


def review_agent(state: MainState) -> Command[ReviewGoto]:
    """검토 결과를 State에 기록하고, 다시 짜야 하면 기획으로 되돌린다."""

    # 전제조건: 소득 유형을 알아야 판단할 수 있다.
    # 예를 들어 "노트북 200만원 경비 되나?"는 상대가 누구냐에 따라 답이 정반대다.
    #   사업소득자 → 필요경비 가능성 있음
    #   근로소득자 → 필요경비라는 개념 자체가 없음 (신용카드 소득공제로 감)
    research = state.get("research_result")
    if not research:
        if not state.get("skip_research"):
            return request_research(state, "review")
        print("  [review] 조사 없이 진행 — 가정을 명시합니다")
        research = "(조사를 수행하지 않았습니다.)"

    print("  [review] 검토 중...")

    # 입구 A(기획 결과)가 있으면 그것을, 없으면 입구 B(사용자가 준 내용)를 검토 대상으로 삼는다
    plan = state.get("planning_result")
    if plan:
        target_label = "기획 담당이 작성한 준비물 목록"
        target = plan
    else:
        target_label = "사용자가 직접 제시한 내용"
        target = state["messages"][-1].text

    reviewer = get_structured_llm(ReviewResult)
    result = reviewer.invoke(
        [
            ("system", REVIEW_PROMPT),
            (
                "human",
                f"아래 내용을 검토해줘.\n\n"
                f"[파악된 상황]\n{research}\n\n"
                f"[검토 대상 — {target_label}]\n{target}",
            ),
        ]
    )

    # 지적사항과 최종본을 하나의 글로 합친다
    parts = []
    if result.issues:
        parts.append("■ 확인이 필요한 항목")
        parts.extend(f"  ⚠ {issue}" for issue in result.issues)
        parts.append("")
    parts.append("■ 개선된 최종본")
    parts.append(result.final)
    review_text = "\n".join(parts)

    revision_count = state.get("revision_count", 0)

    if result.needs_replan and revision_count < MAX_REVISIONS:
        print(f"  [review] 계획을 다시 짜야 합니다 → planning으로 되돌림 ({revision_count + 1}/{MAX_REVISIONS})")
        return Command(
            update={
                "review_result": review_text,
                "revision_count": revision_count + 1,
                # 기획을 다시 돌린 뒤 검토로 돌아오도록 대기열을 새로 깐다
                "todo_agents": ["planning", "review"],
                "executed_agents": state["executed_agents"] + ["review"],
            },
            goto="planning",
        )

    return handoff(state, "review", {"review_result": review_text})
