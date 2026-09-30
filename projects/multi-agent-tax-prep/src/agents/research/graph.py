"""조사 에이전트 — 사용자의 소득 상황을 파악해 신고 의무와 신고 방식을 판별한다.

흐름
    ① 추출 (LLM)   대화에서 소득 정보를 구조화된 형태로 뽑아낸다
    ② 판정 (파이썬) 뽑아낸 값을 기준선과 비교한다. 숫자 비교는 코드가 정확하다
    ③ 서술 (LLM)   판정 결과를 사람이 읽을 문장으로 풀어낸다

LLM은 자연어를 다루는 앞뒤 두 단계만 맡고, 가운데 판정은 순수 파이썬이 한다.
"""

from typing import Literal

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.types import Command
from pydantic import BaseModel, Field

from agents.research.judgement import describe as describe_method
from agents.research.judgement import judge_filing_method
from agents.research.obligation import IncomeProfile
from agents.research.obligation import describe as describe_obligation
from agents.research.obligation import judge_filing_obligation
from agents.research.prompts import EXTRACT_PROMPT, NARRATE_PROMPT
from llm import get_llm, get_structured_llm
from state import MainState, ask_user, handoff

ResearchGoto = Literal["planning", "review", "__end__"]

# 업종을 판단할 수 없을 때 기본으로 가정하는 그룹.
# 프리랜서 대부분이 다군에 속하므로 가장 덜 틀리는 선택이다.
DEFAULT_GROUP = "다군"


class ExtractedProfile(BaseModel):
    """대화에서 뽑아낼 사용자의 소득 정보.

    모르는 값은 기본값(0 또는 빈 문자열)을 그대로 둔다. 지어내지 않는 게 중요하다.
    """

    business_type: str = Field(
        default="", description="업종이나 하는 일. 예: 프리랜서 개발자, 카페 운영. 모르면 빈 문자열"
    )
    business_group: str = Field(
        default="", description="업종 그룹. 가군/나군/다군 중 하나. 판단이 안 되면 빈 문자열"
    )
    is_professional: bool = Field(
        default=False, description="변호사·회계사·세무사·의사 등 전문직 사업자인가"
    )
    has_business_income: bool = Field(
        default=False, description="사업소득이 있는가. 3.3%를 떼고 받는 프리랜서도 포함한다"
    )
    employment_workplaces: int = Field(default=0, description="근로소득을 받은 직장 수")
    employment_settled_together: bool = Field(
        default=True, description="여러 직장의 소득을 합산해 연말정산했는가"
    )
    financial_income: int = Field(default=0, description="이자·배당 합계 (원)")
    other_income_amount: int = Field(default=0, description="기타소득금액 (원). 수입에서 필요경비를 뺀 금액")
    private_pension: int = Field(default=0, description="사적연금 수령액 (원)")
    housing_rental_revenue: int = Field(default=0, description="주택임대 총수입금액 (원)")
    withheld_tax: int = Field(default=0, description="이미 원천징수로 떼인 세액 (원). 3.3% 떼인 금액 등")
    revenue_prev_year: int = Field(default=0, description="직전연도 사업 수입금액 (원). 모르면 0")
    revenue_this_year: int = Field(default=0, description="당해연도 사업 수입금액 (원). 모르면 0")


def format_conversation(messages: list) -> str:
    """대화 기록을 LLM에게 넘길 하나의 글로 만든다.

    앞선 턴에서 말한 내용도 추출 대상이다. 사용자가 "프리랜서예요"라고 먼저 말하고
    다음 턴에 "4천만원쯤 벌었어요"라고 하면, 둘을 합쳐야 판정할 수 있다.
    """
    lines = []
    for message in messages:
        if isinstance(message, HumanMessage):
            lines.append(f"사용자: {message.text}")
        elif isinstance(message, AIMessage):
            lines.append(f"시스템: {message.text}")
    return "\n".join(lines)


def has_no_information(profile: ExtractedProfile) -> bool:
    """소득에 관한 정보가 하나도 없는지 확인한다. 이 경우에만 되묻는다."""
    return not any(
        [
            profile.business_type,
            profile.has_business_income,
            profile.employment_workplaces,
            profile.financial_income,
            profile.other_income_amount,
            profile.private_pension,
            profile.housing_rental_revenue,
            profile.revenue_prev_year,
            profile.revenue_this_year,
        ]
    )


def research_agent(state: MainState) -> Command[ResearchGoto]:
    """상황을 조사해 State에 기록한 뒤 다음 에이전트로 넘긴다."""

    # --- ① 추출: 대화에서 구조화된 정보를 뽑아낸다 ---
    extractor = get_structured_llm(ExtractedProfile)
    conversation = format_conversation(state["messages"])

    profile = extractor.invoke(
        [
            ("system", EXTRACT_PROMPT),
            ("human", f"다음 대화에서 소득 정보를 뽑아줘.\n\n{conversation}"),
        ]
    )

    # 아무 정보도 없으면 추측하지 말고 되묻는다.
    # ask_user는 대기열을 유지한 채 턴을 끝내므로, 사용자가 답하면 여기로 돌아온다.
    if has_no_information(profile):
        return ask_user(
            state,
            "research",
            "상황을 파악하려면 몇 가지가 필요합니다.\n"
            "  ① 어떤 형태로 소득이 있으신가요? (프리랜서 / 사업자 / 직장인 + 부업 등)\n"
            "  ② 하시는 일이나 업종은 무엇인가요?\n"
            "  ③ 작년(직전연도) 수입이 대략 얼마였나요?",
        )

    print(f"  [research] 파악: {profile.business_type or '업종 미상'}")

    # --- ② 판정: 뽑아낸 값을 기준선과 비교한다 (LLM 호출 없음) ---
    obligation = judge_filing_obligation(
        IncomeProfile(
            has_business_income=profile.has_business_income,
            employment_workplaces=profile.employment_workplaces,
            employment_settled_together=profile.employment_settled_together,
            financial_income=profile.financial_income,
            other_income_amount=profile.other_income_amount,
            private_pension=profile.private_pension,
            housing_rental_revenue=profile.housing_rental_revenue,
            withheld_tax=profile.withheld_tax,
        )
    )

    group = profile.business_group if profile.business_group in ("가군", "나군", "다군") else DEFAULT_GROUP
    method = judge_filing_method(
        business_group=group,
        # 수입금액 0은 "모름"으로 본다. 판정 함수는 None을 신규사업자로 취급한다.
        revenue_prev_year=profile.revenue_prev_year or None,
        revenue_this_year=profile.revenue_this_year or None,
        is_professional=profile.is_professional,
    )

    if not profile.business_group:
        method.assumptions.insert(0, f"업종을 파악하지 못해 {DEFAULT_GROUP}으로 가정했습니다.")

    # --- ③ 서술: 판정 결과를 문장으로 풀어낸다 ---
    narrator = get_llm()
    judgement_summary = (
        f"[신고 의무 판정]\n{describe_obligation(obligation)}\n\n"
        f"[신고 방식 판정]\n{describe_method(method)}"
    )

    response = narrator.invoke(
        [
            ("system", NARRATE_PROMPT),
            (
                "human",
                f"사용자 상황: {profile.business_type or '업종 미상'}\n\n"
                f"아래는 이미 계산된 판정 결과다. 이 결과를 설명하고, "
                f"이 업종에서 챙길 만한 경비·공제 항목을 정리해줘.\n\n{judgement_summary}",
            ),
        ]
    )

    # 기획·검토가 읽을 수 있도록 구조화된 값도 함께 남긴다
    user_profile = {
        "business_type": profile.business_type,
        "business_group": group,
        "bookkeeping": method.bookkeeping,
        "expense_rate": method.expense_rate,
        "must_file": obligation.must_file,
    }

    return handoff(
        state,
        "research",
        {"research_result": response.text, "user_profile": user_profile},
    )
