"""신고 의무 판정 함수를 검증한다.

LLM을 부르지 않는 순수 파이썬 테스트다. API 비용 0원.

이 판정의 기준선은 전부 "초과"다. 앞서 만든 신고 방식 판정(judgement.py)은
"이상"이었으므로, 두 파일을 오가며 작업할 때 헷갈리기 쉽다.
그래서 경계값(기준선과 정확히 같은 금액)을 빠짐없이 넣는다.

실행:
    python scripts/test_obligation.py
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

sys.stdout.reconfigure(encoding="utf-8")

from agents.research.obligation import (  # noqa: E402
    IncomeProfile,
    describe,
    judge_filing_obligation,
)

results = []


def check(label: str, actual, expected) -> None:
    """기대값과 비교해 결과를 기록한다. 실패해도 멈추지 않고 끝까지 돌린다."""
    is_ok = actual == expected
    results.append(is_ok)
    print(f"  {'PASS' if is_ok else 'FAIL'}  {label}")
    if not is_ok:
        print(f"        기대: {expected}")
        print(f"        실제: {actual}")


print("=" * 60)
print("1. 사업소득 — 금액 하한이 없다")
print("-" * 60)

o = judge_filing_obligation(IncomeProfile(has_business_income=True))
check("프리랜서(3.3%) → 신고 의무 있음", o.must_file, True)

o = judge_filing_obligation(IncomeProfile())
check("아무 소득도 없음 → 신고 의무 없음", o.must_file, False)


print()
print("=" * 60)
print("2. 근로소득 — 직장 수와 합산 여부로 갈린다")
print("-" * 60)

o = judge_filing_obligation(IncomeProfile(employment_workplaces=1))
check("1곳 → 의무 없음", o.must_file, False)

o = judge_filing_obligation(
    IncomeProfile(employment_workplaces=2, employment_settled_together=True)
)
check("2곳이지만 합산 연말정산 완료 → 의무 없음", o.must_file, False)

o = judge_filing_obligation(
    IncomeProfile(employment_workplaces=2, employment_settled_together=False)
)
check("2곳 + 미합산 → 의무 있음", o.must_file, True)


print()
print("=" * 60)
print("3. 금융소득 경계 — 2,000만원 '초과'부터 (이상이 아니다)")
print("-" * 60)

o = judge_filing_obligation(IncomeProfile(financial_income=20_000_000))
check("정확히 2,000만원 → 의무 없음", o.must_file, False)

o = judge_filing_obligation(IncomeProfile(financial_income=20_000_001))
check("2,000만원 + 1원 → 의무 있음", o.must_file, True)


print()
print("=" * 60)
print("4. 기타소득 경계 — 300만원 이하면 분리과세를 고를 수 있다")
print("-" * 60)

o = judge_filing_obligation(IncomeProfile(other_income_amount=3_000_000))
check("정확히 300만원 → 의무 없음", o.must_file, False)
check("정확히 300만원 → 선택지 생김", len(o.choices), 1)

o = judge_filing_obligation(IncomeProfile(other_income_amount=3_000_001))
check("300만원 + 1원 → 의무 있음", o.must_file, True)

o = judge_filing_obligation(IncomeProfile(other_income_amount=0))
check("기타소득 0원 → 선택지 없음", len(o.choices), 0)


print()
print("=" * 60)
print("5. 주택임대 경계 — 2,000만원 이하면 14% 분리과세 선택 가능")
print("-" * 60)

o = judge_filing_obligation(IncomeProfile(housing_rental_revenue=20_000_000))
check("정확히 2,000만원 → 의무 없음 + 선택지", (o.must_file, len(o.choices)), (False, 1))

o = judge_filing_obligation(IncomeProfile(housing_rental_revenue=20_000_001))
check("2,000만원 + 1원 → 의무 있음", o.must_file, True)


print()
print("=" * 60)
print("6. 사적연금 — 1,500만원 초과면 종합/분리 선택")
print("-" * 60)

o = judge_filing_obligation(IncomeProfile(private_pension=15_000_000))
check("정확히 1,500만원 → 선택지 없음", len(o.choices), 0)

o = judge_filing_obligation(IncomeProfile(private_pension=15_000_001))
check("1,500만원 + 1원 → 선택지 생김", len(o.choices), 1)


print()
print("=" * 60)
print("7. '안 해도 된다'와 '안 하면 손해다'는 다르다")
print("-" * 60)

o = judge_filing_obligation(IncomeProfile(withheld_tax=1_320_000))
check("의무 없음 + 원천징수 있음 → 환급 안내", o.refund_hint is not None, True)

o = judge_filing_obligation(IncomeProfile())
check("의무 없음 + 원천징수 없음 → 안내 없음", o.refund_hint, None)

o = judge_filing_obligation(IncomeProfile(has_business_income=True, withheld_tax=1_320_000))
check("의무 있음이면 환급 안내는 따로 안 붙음", o.refund_hint, None)


print()
print("=" * 60)
print("8. 여러 소득이 겹치면 이유가 모두 쌓인다")
print("-" * 60)

o = judge_filing_obligation(
    IncomeProfile(
        has_business_income=True,
        financial_income=30_000_000,
        housing_rental_revenue=25_000_000,
    )
)
check("사업 + 금융 + 임대 → 이유 3개", len(o.reasons), 3)


print()
print("=" * 60)
print("9. 잘못된 입력은 막는다")
print("-" * 60)

try:
    judge_filing_obligation(IncomeProfile(), year=1999)
    check("기준선 없는 연도 → ValueError", "예외 없음", "ValueError")
except ValueError:
    check("기준선 없는 연도 → ValueError", "ValueError", "ValueError")


print()
print("=" * 60)
print("출력 예시 — 직장 다니면서 부업하는 N잡러")
print("-" * 60)
print(
    describe(
        judge_filing_obligation(
            IncomeProfile(
                has_business_income=True,
                employment_workplaces=1,
                other_income_amount=2_000_000,
                withheld_tax=990_000,
            )
        )
    )
)

print()
print("=" * 60)
print(f"결과: {sum(results)}/{len(results)} 통과")
