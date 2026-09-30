"""업종과 수입금액으로 신고 방식을 판정한다.

LLM을 부르지 않는 순수 파이썬이다. 숫자 비교는 코드가 100% 정확하지만
LLM은 자릿수가 커지면 틀리기 때문에, 판정만 떼어 여기로 옮겼다.

LLM이 하는 일은 "카페 운영해요" 같은 문장에서 업종 그룹과 금액을 뽑아내는 것까지고,
뽑아낸 값을 기준선과 비교하는 것은 이 파일이 한다.

judge = 판정하다 (재판관 judge와 같은 어원. 기준에 비추어 결정한다는 뜻)
"""

from dataclasses import dataclass, field

from config.thresholds import GROUP_EXAMPLES, LATEST_YEAR, THRESHOLDS


@dataclass
class FilingMethod:
    """신고 방식 판정 결과.

    dataclass는 "값을 담는 용도의 클래스"를 짧게 쓰게 해주는 파이썬 기능이다.
    __init__을 직접 쓰지 않아도 필드 정의만으로 생성자가 만들어진다.
    """

    bookkeeping: str            # "복식부기" 또는 "간편장부"
    expense_rate: str           # "기준경비율" 또는 "단순경비율"
    honest_filing_target: bool  # 성실신고확인 대상인가
    basis_year: int             # 어느 귀속연도 기준선을 썼는가

    # 판정 과정에서 세운 가정. 출력할 때 그대로 사용자에게 보여준다.
    # field(default_factory=list)는 "기본값을 빈 리스트로" 라는 뜻이다.
    # 그냥 = [] 로 쓰면 모든 인스턴스가 같은 리스트를 공유하는 버그가 난다.
    assumptions: list[str] = field(default_factory=list)


def judge_filing_method(
    *,                                   # * 뒤의 인자는 반드시 이름을 붙여서 넘겨야 한다
    business_group: str,                 # "가군" / "나군" / "다군"
    revenue_prev_year: int | None,       # 직전연도 수입금액. 신규사업자면 None
    revenue_this_year: int | None = None,  # 당해연도 수입금액 (성실신고확인 판정용)
    is_professional: bool = False,       # 변호사·회계사·의사 등 전문직 사업자인가
    year: int = LATEST_YEAR,             # 어느 귀속연도 기준선을 쓸 것인가
) -> FilingMethod:
    """기장의무·경비율·성실신고확인 대상 여부를 한 번에 판정한다.

    인자를 키워드 전용(* 뒤)으로 둔 이유: 숫자 인자가 여러 개라
    위치로 넘기면 revenue_prev_year와 revenue_this_year를 바꿔 넣기 쉽다.
    이름을 강제하면 호출부만 읽어도 무엇을 넘겼는지 보인다.
    """
    if business_group not in GROUP_EXAMPLES:
        raise ValueError(f"알 수 없는 업종 그룹입니다: {business_group}")

    if year not in THRESHOLDS:
        raise ValueError(f"{year}년 귀속 기준선이 없습니다. thresholds.py에 추가하세요.")

    limits = THRESHOLDS[year]
    assumptions: list[str] = []

    # 직전연도 수입금액이 없으면 신규사업자로 본다.
    # 별도 플래그를 두지 않고 값의 유무로 판단하면, 둘이 어긋나는 상황이 애초에 없다.
    is_new_business = revenue_prev_year is None

    # --- ① 기장의무 판정 (직전연도 수입금액 기준) ---
    if is_professional:
        # 전문직은 수입금액과 무관하게 복식부기 의무자다
        bookkeeping = "복식부기"
        assumptions.append("전문직 사업자는 수입금액과 무관하게 복식부기 의무자로 판정했습니다.")
    elif is_new_business:
        bookkeeping = "간편장부"
        assumptions.append("직전연도 수입금액이 없어 신규사업자로 보고 간편장부 대상으로 판정했습니다.")
    elif revenue_prev_year >= limits["double_entry"][business_group]:
        bookkeeping = "복식부기"
    else:
        bookkeeping = "간편장부"

    # --- ② 경비율 판정 (추계신고를 선택할 경우에만 의미가 있다) ---
    if is_professional:
        # 전문직은 단순경비율 적용 대상에서 제외된다
        expense_rate = "기준경비율"
        assumptions.append("전문직 사업자는 단순경비율 적용 대상에서 제외됩니다.")
    elif is_new_business:
        # 신규사업자 특칙: 직전연도 수입이 없으므로 당해연도 수입으로 판정하되,
        # 이때 쓰는 기준선은 경비율 기준선이 아니라 기장의무 기준선이다. (헷갈리기 쉬운 지점)
        if revenue_this_year is None:
            expense_rate = "단순경비율"
            assumptions.append(
                "신규사업자이고 당해연도 수입금액도 모르는 상태라 단순경비율로 가정했습니다."
            )
        elif revenue_this_year >= limits["double_entry"][business_group]:
            expense_rate = "기준경비율"
            assumptions.append("신규사업자라 당해연도 수입금액을 기준으로 경비율을 판정했습니다.")
        else:
            expense_rate = "단순경비율"
            assumptions.append("신규사업자라 당해연도 수입금액을 기준으로 경비율을 판정했습니다.")
    elif revenue_prev_year >= limits["standard_expense"][business_group]:
        expense_rate = "기준경비율"
    else:
        expense_rate = "단순경비율"

    # --- ③ 성실신고확인 대상 판정 (당해연도 수입금액 기준) ---
    # ①②와 기준연도가 다르다. 같은 변수를 재사용하면 바로 버그가 된다.
    if revenue_this_year is None:
        honest_filing_target = False
        assumptions.append(
            "당해연도 수입금액을 몰라 성실신고확인 대상이 아닌 것으로 가정했습니다."
        )
    else:
        honest_filing_target = revenue_this_year >= limits["honest_filing"][business_group]

    assumptions.append(f"{year}년 귀속 기준선으로 판정했습니다. 국세청 최신 고시 확인이 필요합니다.")

    return FilingMethod(
        bookkeeping=bookkeeping,
        expense_rate=expense_rate,
        honest_filing_target=honest_filing_target,
        basis_year=year,
        assumptions=assumptions,
    )


def describe(method: FilingMethod) -> str:
    """판정 결과를 사람이 읽을 문장으로 바꾼다. 프롬프트에 끼워 넣을 때도 쓴다."""
    lines = [
        f"- 기장의무: {method.bookkeeping} 대상",
        f"- 추계신고 시 경비율: {method.expense_rate}",
        f"- 성실신고확인 대상: {'예' if method.honest_filing_target else '아니오'}",
    ]
    if method.assumptions:
        lines.append("")
        lines.append("가정")
        lines.extend(f"  · {note}" for note in method.assumptions)
    return "\n".join(lines)
