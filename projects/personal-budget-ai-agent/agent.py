"""
개인 예산 관리 AI Agent - Agent 모듈

budget_manager.py 의 함수들을 Gemini의 도구로 등록하고,
사용자의 자연어 요청을 처리하는 Agent loop를 실행한다.

Function Calling 흐름
    사용자 질문
      -> 모델: "add_transaction을 이런 인자로 불러줘"  (function_call)
      -> 이 프로그램: 실제로 파이썬 함수 실행
      -> 모델에게 결과 전달                           (function_result)
      -> 모델: 결과를 읽고 사용자에게 보여줄 문장 작성

모델은 우리 함수를 직접 실행하지 못한다. "불러달라"고 요청할 뿐이고,
실행 권한은 항상 이 프로그램에 있다. 그래서 등록하지 않은 함수는 절대 실행되지 않는다.

실행: python agent.py
"""

import json
import os
import sys
from datetime import datetime

from dotenv import load_dotenv
from google import genai

from budget_manager import BudgetManager


# ======================================================================
# 콘솔 인코딩
# ======================================================================

# Windows 콘솔은 기본 인코딩이 cp949라, 이걸 안 바꾸면 두 가지가 깨진다.
#   1) input()으로 받는 한글이 깨져서 Gemini에 잘못된 JSON이 전송되고 400 에러가 난다.
#   2) print()가 이모지(🔧, ❌ 등)를 못 만나 UnicodeEncodeError로 프로그램이 죽는다.
# reconfigure()는 이미 열려 있는 stdin/stdout의 인코딩을 즉석에서 UTF-8로 바꾼다.
if sys.platform == "win32":
    sys.stdin.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")


# ======================================================================
# 환경 준비
# ======================================================================

# .env 파일을 읽어 환경변수로 올린다.
# 경로를 주지 않으면 현재 폴더부터 위로 올라가며 .env 를 찾는다.
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    # 키가 없으면 이후 모든 요청이 실패한다. 그때 나오는 에러는 알아보기 어려우므로
    # 여기서 분명한 문장으로 먼저 멈춘다.
    raise ValueError(".env 파일에 GEMINI_API_KEY를 설정해 주세요.")

# 두 번째 인자는 기본값이다. .env 에 GEMINI_MODEL 이 없어도 프로그램이 멈추지 않는다.
model = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

# Gemini와 통신할 창구. 한 번만 만들어 두고 계속 재사용한다.
client = genai.Client(api_key=api_key)

# 데이터를 실제로 들고 있는 객체. 인스턴스는 하나만 만든다.
manager = BudgetManager()


# ======================================================================
# 도구 schema
#   모델에게 주는 "함수 설명서". 모델은 우리 코드를 볼 수 없고 이것만 읽는다.
#   설명이 부실하면 엉뚱한 도구를 고르거나 이상한 인자를 만들어내므로,
#   schema 품질이 곧 Agent 품질이 된다.
#
#   - "name" 은 파이썬 함수 이름과 정확히 같아야 한다 (이 문자열로 함수를 찾는다)
#   - "description" 에는 "무엇을 하는지"가 아니라 "언제 쓰는지"를 쓴다
#   - "required" 에는 파이썬 함수에서 기본값이 없는 매개변수만 넣는다
# ======================================================================

EXPENSE_CATEGORIES = ", ".join(manager.expense_categories)
INCOME_CATEGORIES = ", ".join(manager.income_categories)

add_transaction_tool = {
    "type": "function",
    "name": "add_transaction",
    "description": (
        "사용자가 돈을 쓰거나 벌었다고 말할 때 수입 또는 지출 거래를 새로 등록합니다. "
        "예: '점심 12000원 썼어', '월급 300만원 들어왔어'"
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "transaction_type": {
                "type": "string",
                # enum 으로 값을 제한하면 모델이 "소비"나 "expense" 같은 걸 지어내지 못한다.
                "enum": ["수입", "지출"],
                "description": "거래 유형. 돈이 나갔으면 '지출', 들어왔으면 '수입'",
            },
            "category": {
                "type": "string",
                "description": f"카테고리. 지출: {EXPENSE_CATEGORIES} / 수입: {INCOME_CATEGORIES}",
            },
            "amount": {"type": "integer", "description": "금액(원). 0보다 큰 정수"},
            "date": {
                "type": "string",
                # 형식을 안 적으면 모델이 "8월 27일" 같은 값을 보내 검증에 걸린다.
                "description": "거래 날짜. YYYY-MM-DD 형식. 예: 2026-08-27",
            },
            "description": {
                "type": "string",
                "description": "거래 내용 메모. 예: 점심, 카페, 택시",
            },
        },
        "required": ["transaction_type", "category", "amount", "date"],
    },
}

search_transactions_tool = {
    "type": "function",
    "name": "search_transactions",
    "description": (
        "날짜, 기간, 카테고리, 설명 키워드로 거래를 검색합니다. "
        "조건은 원하는 것만 넣으면 되고, 여러 조건을 함께 쓰면 모두 만족하는 거래를 찾습니다. "
        "예: '8월에 식비로 쓴 거 보여줘', '카페에서 쓴 거 찾아줘'"
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "date": {"type": "string", "description": "특정 날짜. YYYY-MM-DD. 예: 2026-08-27"},
            "start_date": {"type": "string", "description": "기간 시작일. YYYY-MM-DD"},
            "end_date": {"type": "string", "description": "기간 종료일. YYYY-MM-DD"},
            "category": {
                "type": "string",
                "description": f"카테고리. 지출: {EXPENSE_CATEGORIES} / 수입: {INCOME_CATEGORIES}",
            },
            "keyword": {"type": "string", "description": "거래 설명에 포함된 단어. 예: 카페, 점심"},
        },
        # 파이썬 함수에서 전부 기본값이 있으므로 필수 항목이 없다.
        "required": [],
    },
}

update_transaction_tool = {
    "type": "function",
    "name": "update_transaction",
    "description": (
        "거래 ID를 알고 있을 때 그 거래의 금액, 카테고리, 설명, 날짜를 수정합니다. "
        # 이 한 문장이 "검색 -> 수정" 연속 도구 호출을 유도한다.
        # 모델에게 순서를 알려주지 않으면 ID를 지어내거나 사용자에게 되묻고 멈춘다.
        "ID를 모르면 먼저 search_transactions로 거래를 찾아 ID를 확인한 뒤 호출하세요. "
        "바꿀 항목만 넣으면 됩니다."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "transaction_id": {"type": "integer", "description": "수정할 거래의 ID"},
            "amount": {"type": "integer", "description": "새 금액(원)"},
            "category": {
                "type": "string",
                "description": f"새 카테고리. 지출: {EXPENSE_CATEGORIES} / 수입: {INCOME_CATEGORIES}",
            },
            "description": {"type": "string", "description": "새 설명"},
            "date": {"type": "string", "description": "새 날짜. YYYY-MM-DD"},
        },
        "required": ["transaction_id"],
    },
}

delete_transaction_tool = {
    "type": "function",
    "name": "delete_transaction",
    "description": (
        "거래 ID로 거래를 삭제합니다. "
        "ID를 모르면 먼저 search_transactions로 찾아 확인한 뒤 호출하세요."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "transaction_id": {"type": "integer", "description": "삭제할 거래의 ID"},
        },
        "required": ["transaction_id"],
    },
}

set_budget_tool = {
    "type": "function",
    "name": "set_budget",
    "description": (
        "특정 월의 지출 카테고리 예산을 설정합니다. 예산은 지출에만 설정할 수 있습니다. "
        "예: '이번 달 식비 예산을 30만원으로 설정해줘'"
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "month": {"type": "string", "description": "대상 월. YYYY-MM 형식. 예: 2026-08"},
            "category": {"type": "string", "description": f"지출 카테고리. {EXPENSE_CATEGORIES}"},
            "amount": {"type": "integer", "description": "예산 금액(원)"},
        },
        "required": ["month", "category", "amount"],
    },
}

get_budget_status_tool = {
    "type": "function",
    "name": "get_budget_status",
    "description": (
        "특정 월의 예산, 사용 금액, 남은 금액을 조회합니다. "
        "카테고리를 지정하지 않으면 예산이 설정된 모든 카테고리를 알려줍니다. "
        "예: '이번 달 식비 얼마나 남았어?'"
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "month": {"type": "string", "description": "조회할 월. YYYY-MM 형식. 예: 2026-08"},
            "category": {"type": "string", "description": f"조회할 지출 카테고리. {EXPENSE_CATEGORIES}"},
        },
        "required": ["month"],
    },
}

generate_monthly_report_tool = {
    "type": "function",
    "name": "generate_monthly_report",
    "description": (
        "특정 월의 거래 내역과 예산 현황을 Markdown 보고서 파일로 저장합니다. "
        "예: '8월 지출 내역을 파일로 저장해줘'"
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "month": {"type": "string", "description": "보고서를 만들 월. YYYY-MM 형식. 예: 2026-08"},
        },
        "required": ["month"],
    },
}

# 요청을 보낼 때 이 목록을 통째로 넘긴다. 여기 빠진 도구는 모델이 쓸 수 없다.
TOOLS = [
    add_transaction_tool,
    search_transactions_tool,
    update_transaction_tool,
    delete_transaction_tool,
    set_budget_tool,
    get_budget_status_tool,
    generate_monthly_report_tool,
]

# 모델은 "add_transaction" 이라는 문자열만 돌려준다.
# 문자열로는 함수를 실행할 수 없으므로 "이름 -> 실제 함수" 대응표가 필요하다.
# 이 표에 없는 이름은 실행되지 않으므로 안전장치 역할도 한다.
#
# 괄호를 붙이지 않는 것이 중요하다. manager.add_transaction() 이라고 쓰면
# 지금 실행해서 그 결과값이 담긴다. 괄호 없이 써야 "함수 자체"가 담긴다.
# manager. 에 붙여 담으면 **arguments 로 부를 때 self 가 자동으로 채워진다.
TOOL_FUNCTIONS = {
    "add_transaction": manager.add_transaction,
    "search_transactions": manager.search_transactions,
    "update_transaction": manager.update_transaction,
    "delete_transaction": manager.delete_transaction,
    "set_budget": manager.set_budget,
    "get_budget_status": manager.get_budget_status,
    "generate_monthly_report": manager.generate_monthly_report,
}


# ======================================================================
# 시스템 프롬프트
#   매 요청마다 함께 보내는 역할 설명서.
# ======================================================================

# 모델은 오늘이 며칠인지 모른다. "오늘 점심 먹었어"의 날짜를 채우려면 알려줘야 한다.
# 도구로 만들지 않는 이유: 항상 필요한 정보라서, 모델이 "물어볼까?"를 판단할 필요조차
# 없게 만드는 편이 안전하다. 도구로 두면 호출을 깜빡했을 때 날짜를 지어낸다.
#
# strftime 은 strptime 의 반대다 (f = format). %A 는 요일 이름이라
# "지난 주말" 같은 표현도 처리할 수 있게 된다.
today = datetime.now().strftime("%Y-%m-%d (%A)")

SYSTEM_INSTRUCTION = f"""당신은 개인 예산 관리 비서입니다.

[오늘 날짜]
오늘은 {today}입니다.
'오늘', '어제', '이번 달', '지난주' 같은 표현은 이 날짜를 기준으로 계산하세요.

[카테고리]
지출: {EXPENSE_CATEGORIES}
수입: {INCOME_CATEGORIES}
사용자의 표현을 위 카테고리 중 하나로 알맞게 분류하세요.
(예: '점심'·'커피' -> 식비, '택시'·'지하철' -> 교통비, '영화' -> 문화생활)

[작업 규칙]
1. 추측하지 말고 반드시 도구를 사용해 확인하세요.
   도구 결과에 없는 정보는 지어내지 말고 없다고 말하세요.
2. 거래를 수정하거나 삭제하려면 거래 ID가 필요합니다.
   사용자가 ID를 모르면 먼저 search_transactions로 찾으세요.
3. 검색 결과가 2건 이상이면 절대 임의로 고르지 마세요.
   찾은 거래들을 사용자에게 보여주고, 어떤 것인지 특정할 수 있는 조건
   (날짜, 금액, 설명 등)을 되물으세요.
4. 검색 결과가 0건이면 그 사실을 알리고, 조건을 바꿔볼 것을 제안하세요.
5. 도구가 ok=false를 반환하면 message 내용을 사용자가 이해하기 쉽게 설명하세요.
6. 금액은 12,000원처럼 천 단위 쉼표를 넣어 읽어주세요.
"""


# ======================================================================
# 도구 실행과 출력
# ======================================================================

def execute_tool_call(step):
    """도구 하나를 안전하게 실행한다.

    모델이 보낸 인자가 우리 함수와 안 맞을 수 있다. 그대로 실행하면 예외가 나면서
    Agent 전체가 죽는다. 어떤 실패든 규약대로 {"ok": False, ...} 로 바꿔 돌려주면,
    루프는 결과를 한 가지 방법으로만 다루면 된다.
    """
    # .get 을 쓰는 이유: 모델이 등록되지 않은 이름을 보낼 수 있다.
    # TOOL_FUNCTIONS[step.name] 로 꺼내면 그때 KeyError 로 죽는다.
    tool_function = TOOL_FUNCTIONS.get(step.name)
    if tool_function is None:
        return {"ok": False, "error": "UNKNOWN_TOOL",
                "message": f"허용되지 않은 도구입니다: {step.name}"}

    try:
        # ** 는 {"a": 1, "b": 2} 를 a=1, b=2 형태로 풀어서 인자로 넣어준다.
        return tool_function(**step.arguments)
    except TypeError as error:
        # 인자 개수나 이름이 안 맞을 때
        return {"ok": False, "error": "INVALID_ARGUMENTS",
                "message": f"잘못된 인자: {error}"}
    except Exception as error:
        # 그 밖의 모든 에러. Exception 은 거의 모든 에러의 부모라서 맨 아래에 둔다.
        # 위에 두면 TypeError 도 여기서 잡혀버린다.
        return {"ok": False, "error": "TOOL_FAILED",
                "message": f"도구 실행 실패: {type(error).__name__}"}


def print_tool_call(step):
    """어떤 도구를 어떤 인자로 부르는지 콘솔에 보여준다."""
    print(f"🔧 [도구 호출] {step.name}")
    print(f"   인자: {step.arguments}")


def print_tool_result(result):
    """도구 실행 결과를 콘솔에 보여준다."""
    mark = "✅" if result.get("ok") else "❌"
    detail = result.get("message", "")
    if not result.get("ok"):
        detail = f"({result.get('error')}) {detail}"
    print(f"{mark} [실행 결과] {detail}\n")


def write_log(turn, step, result):
    """도구 호출 기록을 agent.log 파일에 한 줄씩 남긴다.

    "a"(append) 모드로 열어야 기존 내용 뒤에 이어 쓴다.
    "w" 로 열면 실행할 때마다 앞의 기록이 전부 지워진다.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = (f"{now} | turn={turn} | {step.name} | "
            f"{json.dumps(step.arguments, ensure_ascii=False)} | ok={result.get('ok')}\n")
    with open("agent.log", "a", encoding="utf-8") as f:
        f.write(line)


# ======================================================================
# Agent loop
# ======================================================================

def run_agent(user_input, max_turns=5):
    """사용자 요청 하나를 끝까지 처리한다.

    도구를 한 번만 부르면 끝나는 요청도 있지만,
    "8월 27일 카페 금액을 4500원으로 수정해줘" 같은 요청은
    검색 -> 수정 두 단계가 필요하다.
    모델은 첫 번째 결과를 받아본 뒤에야 두 번째 호출을 만들 수 있으므로,
    "도구 요청이 더 없을 때까지" 반복해야 한다.

    max_turns 를 두는 이유: 없으면 모델이 계속 도구를 부를 때
    비용과 시간이 무한히 늘어난다. 이 프로젝트에서 가장 긴 작업이 2단계라 5면 충분하다.
    """
    # 첫 턴은 사용자 문장이 입력이고, 두 번째부터는 도구 결과가 입력이 된다.
    next_input = user_input
    previous_interaction_id = None
    logs = []

    print("─" * 55)

    for turn in range(1, max_turns + 1):
        # 첫 턴에는 previous_interaction_id 가 없다.
        # 조건에 따라 항목을 넣거나 빼야 하므로 딕셔너리로 조립한 뒤 ** 로 푼다.
        request = {
            "model": model,
            "input": next_input,
            "tools": TOOLS,
            "system_instruction": SYSTEM_INSTRUCTION,
            # 대화 상태를 서버에 저장한다. 이어가려면 필요하다.
            "store": True,
        }
        if previous_interaction_id is not None:
            request["previous_interaction_id"] = previous_interaction_id

        interaction = client.interactions.create(**request)

        # 응답은 여러 step 으로 나뉘어 온다. 그중 도구 호출 요청만 골라낸다.
        function_calls = [s for s in interaction.steps if s.type == "function_call"]

        # 도구 요청이 없다는 건 모델이 할 일을 다 하고 최종 답변을 냈다는 뜻이다.
        if not function_calls:
            print("─" * 55)
            return {"ok": True, "answer": interaction.output_text,
                    "turns": turn, "tool_logs": logs}

        next_input = []
        for step in function_calls:
            print_tool_call(step)
            result = execute_tool_call(step)
            print_tool_result(result)
            write_log(turn, step, result)

            logs.append({"turn": turn, "tool": step.name,
                         "arguments": step.arguments, "result": result})

            next_input.append({
                "type": "function_result",
                "name": step.name,
                # 모델이 보낸 id 와 같아야 한다. 어긋나면
                # 모델이 어느 호출의 결과인지 알 수 없다.
                "call_id": step.id,
                # 결과는 문자열로 바꿔서 보낸다.
                # 파일이 아니라 문자열이므로 s 가 붙은 dumps 를 쓴다.
                "result": [{"type": "text",
                            "text": json.dumps(result, ensure_ascii=False)}],
            })

        # 다음 턴에서 방금 대화를 이어가도록 기억해 둔다.
        previous_interaction_id = interaction.id

    # for 가 끝까지 돌았다 = 한도를 다 썼는데도 안 끝났다.
    print("─" * 55)
    return {"ok": False, "answer": None, "turns": max_turns,
            "tool_logs": logs, "error": "최대 반복 횟수를 초과했습니다."}


# ======================================================================
# 실행 진입점
# ======================================================================

def main():
    print("=" * 55)
    print("  개인 예산 관리 비서")
    print("=" * 55)
    print("  자연어로 말씀해 주세요.")
    print("    예) 오늘 점심으로 12000원 썼어")
    print("        8월에 식비로 쓴 거 보여줘")
    print("        이번 달 식비 예산을 30만원으로 설정해줘")
    print("        이번 달 식비 얼마나 남았어?")
    print()
    print("  종료하려면 '종료' 를 입력하세요.")
    print("=" * 55)

    while True:
        user_input = input("\n나: ").strip()

        if user_input in ("종료", "exit", "quit"):
            print("종료합니다.")
            break

        # 빈 입력은 무시하고 다시 받는다.
        if not user_input:
            continue

        try:
            result = run_agent(user_input)
        except Exception as error:
            # 통신 오류 등으로 죽지 않도록 마지막 안전망을 둔다.
            print(f"❌ 요청 처리 중 오류가 발생했습니다: {type(error).__name__}: {error}")
            continue

        if result["ok"]:
            print(f"💬 {result['answer']}")
        else:
            print(f"❌ {result['error']}")


# 이 파일을 직접 실행했을 때만 main()이 돌아간다.
# 다른 파일에서 import 할 때는 실행되지 않는다.
# 이게 없으면 import 하는 순간 대화창이 켜져버린다.
if __name__ == "__main__":
    main()
