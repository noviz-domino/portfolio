"""신고 방식 판정 함수를 검증한다.

LLM을 부르지 않는 순수 파이썬 테스트다. API 비용 0원.

경계값(기준선과 정확히 같은 금액)을 반드시 포함한다.
"이상"으로 짜야 할 곳을 "초과"로 짜는 실수가 가장 흔하고, 경계값 없이는 안 걸린다.

실행:
    python scripts/test_judgement.py
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

sys.stdout.reconfigure(encoding="utf-8")

from agents.research.judgement import describe, judge_filing_method  # noqa: E402

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
print("1. 다군(프리랜서 대부분) — 수입 구간별 판정")
print("-" * 60)
# 다군 기준선: 복식부기 7,500만원 / 기준경비율 2,400만원

m = judge_filing_method(business_group="다군", revenue_prev_year=20_000_000)
check("2,000만원 → 간편장부", m.bookkeeping, "간편장부")
check("2,000만원 → 단순경비율", m.expense_rate, "단순경비율")

m = judge_filing_method(business_group="다군", revenue_prev_year=40_000_000)
check("4,000만원 → 간편장부", m.bookkeeping, "간편장부")
check("4,000만원 → 기준경비율", m.expense_rate, "기준경비율")

m = judge_filing_method(business_group="다군", revenue_prev_year=80_000_000)
check("8,000만원 → 복식부기", m.bookkeeping, "복식부기")
check("8,000만원 → 기준경비율", m.expense_rate, "기준경비율")


print()
print("=" * 60)
print("2. 경계값 — 기준선과 정확히 같은 금액은 '이상'이므로 위쪽으로 간다")
print("-" * 60)

m = judge_filing_method(business_group="다군", revenue_prev_year=75_000_000)
check("정확히 7,500만원 → 복식부기", m.bookkeeping, "복식부기")

m = judge_filing_method(business_group="다군", revenue_prev_year=74_999_999)
check("7,500만원 - 1원 → 간편장부", m.bookkeeping, "간편장부")

m = judge_filing_method(business_group="다군", revenue_prev_year=24_000_000)
check("정확히 2,400만원 → 기준경비율", m.expense_rate, "기준경비율")

m = judge_filing_method(business_group="다군", revenue_prev_year=23_999_999)
check("2,400만원 - 1원 → 단순경비율", m.expense_rate, "단순경비율")


print()
print("=" * 60)
print("3. 업종 그룹마다 기준선이 다르다 (같은 금액, 다른 결과)")
print("-" * 60)
# 1억원일 때: 가군(3억) 미만 → 간편장부 / 나군(1.5억) 미만 → 간편장부 / 다군(7,500만) 이상 → 복식부기

for group, expected in (("가군", "간편장부"), ("나군", "간편장부"), ("다군", "복식부기")):
    m = judge_filing_method(business_group=group, revenue_prev_year=100_000_000)
    check(f"{group} 1억원 → {expected}", m.bookkeeping, expected)


print()
print("=" * 60)
print("4. 전문직 — 수입금액과 무관하게 복식부기, 단순경비율 배제")
print("-" * 60)

m = judge_filing_method(business_group="다군", revenue_prev_year=10_000_000, is_professional=True)
check("전문직 1,000만원 → 복식부기", m.bookkeeping, "복식부기")
check("전문직 1,000만원 → 기준경비율", m.expense_rate, "기준경비율")


print()
print("=" * 60)
print("5. 신규사업자 — 직전연도 수입이 없으면 당해연도로 판정")
print("-" * 60)

m = judge_filing_method(business_group="다군", revenue_prev_year=None)
check("신규 → 간편장부", m.bookkeeping, "간편장부")

# 신규사업자의 경비율은 '기장의무 기준선'(다군 7,500만원)을 쓴다. 경비율 기준선이 아니다.
m = judge_filing_method(business_group="다군", revenue_prev_year=None, revenue_this_year=100_000_000)
check("신규 + 당해 1억 → 기준경비율", m.expense_rate, "기준경비율")

m = judge_filing_method(business_group="다군", revenue_prev_year=None, revenue_this_year=50_000_000)
check("신규 + 당해 5,000만원 → 단순경비율", m.expense_rate, "단순경비율")


print()
print("=" * 60)
print("6. 성실신고확인 — 당해연도 기준 (기장의무와 기준연도가 다르다)")
print("-" * 60)
# 다군 성실신고확인 기준: 당해연도 5억원

m = judge_filing_method(
    business_group="다군", revenue_prev_year=100_000_000, revenue_this_year=500_000_000
)
check("당해 5억 → 성실신고확인 대상", m.honest_filing_target, True)

m = judge_filing_method(
    business_group="다군", revenue_prev_year=600_000_000, revenue_this_year=400_000_000
)
check("직전 6억이어도 당해 4억이면 비대상", m.honest_filing_target, False)


print()
print("=" * 60)
print("7. 잘못된 입력은 막는다")
print("-" * 60)

try:
    judge_filing_method(business_group="라군", revenue_prev_year=10_000_000)
    check("없는 업종 그룹 → ValueError", "예외 없음", "ValueError")
except ValueError:
    check("없는 업종 그룹 → ValueError", "ValueError", "ValueError")

try:
    judge_filing_method(business_group="다군", revenue_prev_year=10_000_000, year=1999)
    check("기준선 없는 연도 → ValueError", "예외 없음", "ValueError")
except ValueError:
    check("기준선 없는 연도 → ValueError", "ValueError", "ValueError")


print()
print("=" * 60)
print("출력 예시 — 프리랜서 개발자, 직전연도 4,000만원")
print("-" * 60)
print(describe(judge_filing_method(business_group="다군", revenue_prev_year=40_000_000)))

print()
print("=" * 60)
print(f"결과: {sum(results)}/{len(results)} 통과")
