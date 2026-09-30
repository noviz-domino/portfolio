"""소득 구성으로 종합소득세 신고 의무가 있는지 판정한다.

judgement.py가 "어떻게 신고하는가"(기장의무·경비율)를 본다면,
이 파일은 그 앞 단계인 "신고를 해야 하는가"를 본다.

obligation = 의무 (라틴어 obligare "묶다"에서 왔다. 법으로 묶여 있는 것)

LLM을 부르지 않는 순수 파이썬이다. 소득 금액을 기준선과 비교하는 일이라
코드가 하는 편이 정확하다.
"""

from dataclasses import dataclass, field

from config.thresholds import INCOME_THRESHOLDS, LATEST_YEAR


@dataclass
class IncomeProfile:
    """사용자의 소득 구성. LLM이 대화에서 뽑아내 채운다."""

    # 사업소득 (사업자등록 여부와 무관. 3.3% 떼고 받는 프리랜서도 사업소득이다)
    has_business_income: bool = False

    # 근로소득을 받은 직장 수. 2곳 이상인데 합산 연말정산을 안 했으면 신고 대상이 된다.
    # settle = 정산하다 (연말정산 = year-end settlement)
    employment_workplaces: int = 0
    employment_settled_together: bool = True

    financial_income: int = 0        # 이자·배당 합계
    other_income_amount: int = 0     # 기타소득'금액' (수입 - 필요경비). 수입금액이 아니다
    private_pension: int = 0         # 사적연금 (연금저축, 연금보험 등)
    housing_rental_revenue: int = 0  # 주택임대 총수입금액

    # 이미 원천징수로 떼인 세액. 3.3%로 떼인 프리랜서가 여기 해당한다.
    # withhold = 떼어두다, 보류하다 → withheld tax = 원천징수세액
    withheld_tax: int = 0


@dataclass
class FilingObligation:
    """신고 의무 판정 결과."""

    must_file: bool                                   # 신고 의무가 있는가
    reasons: list[str] = field(default_factory=list)  # 의무가 생긴 이유
    choices: list[str] = field(default_factory=list)  # 종합/분리를 고를 수 있는 항목
    refund_hint: str | None = None                    # 의무는 없지만 안 하면 손해인 경우
    assumptions: list[str] = field(default_factory=list)


def judge_filing_obligation(
    income: IncomeProfile,
    year: int = LATEST_YEAR,
) -> FilingObligation:
    """소득 구성을 보고 신고 의무 여부와 선택지를 판정한다.

    "안 해도 된다"와 "안 하면 손해다"는 다르다.
    신고 의무가 없어도 원천징수된 세액이 있으면 신고해야 환급받으므로,
    그 경우를 refund_hint로 따로 알린다.
    """
    if year not in INCOME_THRESHOLDS:
        raise ValueError(f"{year}년 귀속 기준선이 없습니다. thresholds.py에 추가하세요.")

    limits = INCOME_THRESHOLDS[year]
    reasons: list[str] = []
    choices: list[str] = []

    # --- 사업소득: 금액 하한이 없다. 1원이라도 있으면 신고 대상 ---
    if income.has_business_income:
        reasons.append("사업소득이 있습니다. 사업소득은 금액과 무관하게 신고 의무가 있습니다.")

    # --- 근로소득: 2곳 이상인데 합산 연말정산을 안 한 경우 ---
    if income.employment_workplaces >= 2 and not income.employment_settled_together:
        reasons.append(
            f"근로소득을 {income.employment_workplaces}곳에서 받았고 합산 연말정산을 하지 않았습니다."
        )

    # --- 금융소득: 2,000만원 "초과"면 종합과세 ---
    if income.financial_income > limits["financial_income"]:
        reasons.append(
            f"이자·배당 합계가 {limits['financial_income']:,}원을 넘어 금융소득종합과세 대상입니다."
        )

    # --- 기타소득: 300만원 초과면 종합과세 강제, 이하면 분리과세 선택 가능 ---
    if income.other_income_amount > limits["other_income"]:
        reasons.append(
            f"기타소득금액이 {limits['other_income']:,}원을 넘어 종합과세 대상입니다."
        )
    elif income.other_income_amount > 0:
        choices.append(
            f"기타소득금액이 {limits['other_income']:,}원 이하라 분리과세를 선택할 수 있습니다."
        )

    # --- 사적연금: 1,500만원 초과면 종합/분리 선택 ---
    if income.private_pension > limits["private_pension"]:
        choices.append(
            f"사적연금이 {limits['private_pension']:,}원을 넘어 종합과세와 분리과세 중 선택할 수 있습니다."
        )

    # --- 주택임대: 2,000만원 초과면 종합과세 강제, 이하면 14% 분리과세 선택 가능 ---
    if income.housing_rental_revenue > limits["housing_rental"]:
        reasons.append(
            f"주택임대 수입금액이 {limits['housing_rental']:,}원을 넘어 종합과세 대상입니다."
        )
    elif income.housing_rental_revenue > 0:
        choices.append(
            f"주택임대 수입금액이 {limits['housing_rental']:,}원 이하라 분리과세를 선택할 수 있습니다."
        )

    must_file = bool(reasons)

    # --- 의무는 없지만 안 하면 손해인 경우 ---
    refund_hint = None
    if not must_file and income.withheld_tax > 0:
        refund_hint = (
            f"신고 의무는 없지만 이미 원천징수된 세액이 {income.withheld_tax:,}원 있습니다. "
            "신고해야 정산되어 환급받을 수 있습니다."
        )

    assumptions = [
        f"{year}년 귀속 기준선으로 판정했습니다. 국세청 최신 고시 확인이 필요합니다."
    ]

    return FilingObligation(
        must_file=must_file,
        reasons=reasons,
        choices=choices,
        refund_hint=refund_hint,
        assumptions=assumptions,
    )


def describe(obligation: FilingObligation) -> str:
    """판정 결과를 사람이 읽을 문장으로 바꾼다."""
    lines = [f"- 신고 의무: {'있음' if obligation.must_file else '없음'}"]

    if obligation.reasons:
        lines.append("")
        lines.append("신고 대상인 이유")
        lines.extend(f"  · {reason}" for reason in obligation.reasons)

    if obligation.choices:
        lines.append("")
        lines.append("선택지가 있는 항목")
        lines.extend(f"  · {choice}" for choice in obligation.choices)

    if obligation.refund_hint:
        lines.append("")
        lines.append(f"※ {obligation.refund_hint}")

    if obligation.assumptions:
        lines.append("")
        lines.append("가정")
        lines.extend(f"  · {note}" for note in obligation.assumptions)

    return "\n".join(lines)
