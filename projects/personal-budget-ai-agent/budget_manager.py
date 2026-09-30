"""
개인 예산 관리 AI Agent - 데이터 관리 모듈

거래 내역과 예산을 관리하는 순수 Python 로직.
이 파일은 Gemini를 전혀 모른다. 그래서 Agent 없이도 단독으로 테스트할 수 있고,
문제가 생겼을 때 "함수가 잘못됐는지, Agent 연결이 잘못됐는지"를 분리해서 확인할 수 있다.

여기의 도구 함수들은 agent.py 에서 Gemini의 도구로 등록된다.
"""

import json
from datetime import datetime


class BudgetManager:
    """거래 내역과 예산을 함께 관리하는 클래스.

    거래 목록, 다음 ID, 카테고리 목록, 예산을 여러 함수가 공유해야 하므로
    전역 변수로 흩어두지 않고 하나의 클래스로 묶었다.
    """

    def __init__(self, data_file="data.json"):
        # 저장할 파일 이름. 매개변수로 뺀 이유는 테스트할 때
        # BudgetManager("test_data.json") 처럼 실제 데이터와 분리하기 위해서다.
        self.data_file = data_file

        # 거래 딕셔너리들이 쌓이는 리스트.
        self.transactions = []

        # 다음 거래에 부여할 번호. 등록할 때마다 1씩 증가시킨다.
        # 이 값을 저장/복원하지 않으면 재실행 시 ID가 1부터 다시 시작해 번호가 겹친다.
        self.next_id = 1

        # 카테고리를 파일 상단 상수가 아니라 인스턴스 속성으로 둔 이유:
        # 나중에 "카테고리 추가" 기능을 붙이면 리스트에 append 하고 저장만 하면 되도록.
        # 상수로 두면 실행 중에 바꿔도 JSON에 저장되지 않아 재실행하면 사라진다.
        self.expense_categories = ["식비", "교통비", "주거비", "문화생활", "기타"]
        self.income_categories = ["월급", "용돈", "부수입", "기타"]

        # {"2026-08": {"식비": 300000}} 형태의 2단계 딕셔너리.
        # 월별로 다른 예산을 세울 수 있어야 해서 월을 바깥 열쇠로 두었다.
        self.budgets = {}

        # 저장된 파일이 있으면 복원한다. 없으면 위의 기본값 그대로 시작한다.
        self._load()

    # ==================================================================
    # 검증 헬퍼
    #   이름 앞의 _ 는 "클래스 내부에서만 쓰는 보조 함수"라는 파이썬 관례다.
    #   Gemini에는 도구로 등록하지 않는다.
    #
    #   여러 도구 함수가 똑같은 검사를 반복하므로 한 곳에 모아두었다.
    #   에러가 날 수 있는 처리(int, strptime)를 여기서 try로 감싸두면,
    #   이를 호출하는 쪽은 try 없이 if 문만으로 안전하게 검사할 수 있다.
    # ==================================================================

    def _validate_amount(self, amount):
        """금액을 검사하면서 정수로 변환한다. 잘못된 값이면 None을 돌려준다.

        LLM은 금액을 12000 / "12000" / 12000.0 중 아무 형태로나 보낼 수 있다.
        저장할 때 정수로 통일해두지 않으면 나중에 합계를 구할 때 깨진다.

        검사 결과(True/False)가 아니라 변환된 값을 돌려주는 이유는,
        부르는 쪽에서 검사와 변환을 한 번에 끝낼 수 있게 하기 위해서다.
        """
        try:
            # int("12000.5")는 에러가 나지만 float을 한 번 거치면 통과한다.
            # 그래서 float -> int 순서여야 세 가지 형태를 모두 처리할 수 있다.
            value = int(float(amount))
        except (TypeError, ValueError):
            # ValueError: 값이 이상할 때 (int("사과"))
            # TypeError : 타입 자체가 안 맞을 때 (int(None))
            return None

        # 0원짜리 거래나 마이너스 지출은 의미가 없으므로 거절한다.
        if value <= 0:
            return None

        return value

    def _validate_date(self, date_str):
        """'YYYY-MM-DD' 형식이고 실제로 존재하는 날짜인지 검사한다."""
        try:
            # strptime = string parse time. 문자열을 날짜로 해석해 본다.
            # 형식이 다르거나 2026-02-30 처럼 없는 날짜면 ValueError가 난다.
            # 자릿수를 직접 세는 것보다 정확하고 윤년까지 알아서 처리해준다.
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except (ValueError, TypeError):
            return False

    def _validate_month(self, month_str):
        """'YYYY-MM' 형식인지 검사한다. 예산은 월 단위로 관리하므로 따로 필요하다.

        참고: %m 은 자릿수를 강제하지 않아 "2026-8"도 통과한다.
        실제로 걸러지는 것은 13월처럼 없는 값이거나, 뒤에 일자까지 붙어 형식이 안 맞는 경우다.
        """
        try:
            datetime.strptime(month_str, "%Y-%m")
            return True
        except (ValueError, TypeError):
            return False

    def _validate_category(self, category, transaction_type):
        """거래 유형에 맞는 카테고리인지 검사한다.

        지출에 "월급"을 쓰거나 수입에 "식비"를 쓰는 것을 막아야 하므로,
        유형에 따라 서로 다른 목록을 본다.
        """
        if transaction_type == "지출":
            return category in self.expense_categories

        if transaction_type == "수입":
            return category in self.income_categories

        # 유형 자체가 잘못됐다면 카테고리도 유효할 수 없다.
        # 이 갈래를 빠뜨리면 함수가 아무것도 반환하지 않고 끝나 None이 나온다.
        return False

    # ==================================================================
    # 저장 / 불러오기
    #   데이터를 바꾸는 도구들은 작업이 끝날 때마다 _save()를 부른다.
    #   사용자가 "저장해줘"라고 말할 필요 없이 자동으로 유지되게 하기 위해서다.
    # ==================================================================

    def _save(self):
        """현재 상태를 JSON 파일에 저장한다."""
        # 흩어져 있는 self.~ 값들을 하나의 딕셔너리로 모아야 파일 하나로 저장할 수 있다.
        # next_id 를 빠뜨리면 재실행 시 ID가 1부터 다시 시작해 기존 거래와 번호가 겹친다.
        data = {
            "transactions": self.transactions,
            "next_id": self.next_id,
            "expense_categories": self.expense_categories,
            "income_categories": self.income_categories,
            "budgets": self.budgets,
        }

        # with 를 쓰면 도중에 에러가 나도 파일이 반드시 닫힌다.
        # encoding 과 ensure_ascii 를 빠뜨리면 한글이 깨지거나 식비 처럼 저장된다.
        # indent=2 는 사람이 파일을 열어봤을 때 읽을 수 있게 해준다.
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load(self):
        """저장된 JSON 파일에서 상태를 복원한다. 파일이 없으면 아무것도 하지 않는다."""
        try:
            with open(self.data_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except FileNotFoundError:
            # 첫 실행에는 파일이 없다. 이건 오류가 아니라 정상 상황이므로
            # 기본값 그대로 두고 조용히 끝낸다.
            return
        except json.JSONDecodeError:
            # 파일이 손상된 경우. 프로그램이 죽는 대신 기본값으로 시작한다.
            print(f"경고: {self.data_file} 을 읽을 수 없어 빈 상태로 시작합니다.")
            return

        # .get(열쇠, 기본값) 을 쓰면 예전에 저장한 파일에 그 항목이 없어도 에러가 나지 않는다.
        self.transactions = data.get("transactions", [])
        self.next_id = data.get("next_id", 1)
        self.expense_categories = data.get("expense_categories", self.expense_categories)
        self.income_categories = data.get("income_categories", self.income_categories)
        self.budgets = data.get("budgets", {})

    # ==================================================================
    # 도구 함수
    #   Gemini에 등록되어 호출될 함수들.
    #   모두 {"ok": ..., "data"/"error": ..., "message": ...} 형식으로 반환한다.
    #   반환 형식을 통일해두면 Agent loop가 결과를 한 가지 방법으로만 처리할 수 있다.
    # ==================================================================

    def add_transaction(self, transaction_type, category, amount, date, description=""):
        """수입 또는 지출 거래를 등록한다.

        description에만 기본값을 준 이유: 메모는 없을 수도 있으므로 LLM이 생략하고
        호출할 수 있어야 한다. 반대로 금액/날짜/카테고리는 없으면 거래가 성립하지 않으므로
        기본값을 주지 않아, LLM이 사용자에게 되묻도록 유도한다.
        """
        # 1) 거래 유형부터 검사한다.
        #    아래 카테고리 검사가 이 값을 보고 어느 목록을 볼지 정하기 때문에 순서가 중요하다.
        if transaction_type not in ("수입", "지출"):
            return {"ok": False, "error": "INVALID_TYPE",
                    "message": "거래 유형은 '수입' 또는 '지출'이어야 합니다."}

        # 2) 금액 검사 + 정수 변환
        value = self._validate_amount(amount)
        if value is None:
            return {"ok": False, "error": "INVALID_AMOUNT",
                    "message": "금액은 0보다 큰 숫자여야 합니다."}

        # 3) 날짜 형식 검사
        #    형식이 통일돼야 검색(문자열 비교)과 월별 집계(startswith)가 동작한다.
        if not self._validate_date(date):
            return {"ok": False, "error": "INVALID_DATE",
                    "message": "날짜는 YYYY-MM-DD 형식이어야 합니다. 예: 2026-08-27"}

        # 4) 카테고리 검사
        #    오류 메시지에 사용 가능한 목록을 함께 담아주면 LLM이 스스로 고쳐 다시 호출할 수 있다.
        if not self._validate_category(category, transaction_type):
            if transaction_type == "지출":
                allowed = ", ".join(self.expense_categories)
            else:
                allowed = ", ".join(self.income_categories)
            return {"ok": False, "error": "INVALID_CATEGORY",
                    "message": f"'{category}'는 {transaction_type} 카테고리가 아닙니다. "
                               f"사용 가능: {allowed}"}

        # 5) 검사를 모두 통과했으므로 이제 실제로 저장할 데이터를 만든다.
        #    검사를 먼저 다 끝내고 저장하는 순서여야, 잘못된 데이터가 목록에 남지 않는다.
        #    amount 자리에는 원래 받은 값이 아니라 2)에서 변환된 value를 넣어야 한다.
        transaction = {
            "id": self.next_id,
            "type": transaction_type,   # 매개변수 이름과 키 이름이 다르다.
                                        # type은 파이썬 내장 함수 이름이라 매개변수로 쓰지 않았다.
            "category": category,
            "amount": value,
            "description": description,
            "date": date,
        }

        # 6) 목록에 넣고 다음 번호로 넘긴다.
        self.transactions.append(transaction)
        self.next_id += 1
        self._save()

        # 7) message에 ID를 넣어두면 사용자가 번호를 알 수 있어
        #    이후 "1번 거래 수정해줘" 같은 대화가 가능해진다.
        return {
            "ok": True,
            "data": transaction,
            "message": f"[{transaction['id']}] {date} {category} {transaction_type} "
                       f"{value:,}원을 등록했습니다.",
        }

    def search_transactions(self, date=None, start_date=None, end_date=None,
                            category=None, keyword=None):
        """조건에 맞는 거래를 검색한다.

        매개변수가 전부 기본값 None인 이유: 사용자는 "8월에 식비 쓴 거"처럼
        조건 일부만 말한다. None은 "이 조건은 쓰지 않는다"는 표시가 된다.
        빈 문자열은 "빈 값으로 검색"인지 "조건 없음"인지 구분되지 않아 쓰지 않았다.
        """
        # 원본 self.transactions를 건드리면 데이터가 사라지므로
        # 조건을 통과한 것만 담을 새 리스트를 만든다.
        results = []

        for t in self.transactions:
            # 조건에 맞는 것을 찾기보다, 맞지 않는 것을 continue로 걸러내는 편이
            # 조건이 늘어나도 코드가 단순하다.

            if date is not None:
                # 특정 날짜를 콕 집은 요청이 더 구체적이므로 기간보다 우선한다.
                if t["date"] != date:
                    continue
            else:
                # 날짜 형식이 "YYYY-MM-DD"로 고정이라 문자열 비교만으로 순서 판정이 된다.
                # (자릿수가 항상 같으므로 사전순 = 날짜순)
                if start_date is not None and t["date"] < start_date:
                    continue
                if end_date is not None and t["date"] > end_date:
                    continue

            if category is not None and t["category"] != category:
                continue

            # 키워드는 정확히 같은지가 아니라 포함되어 있는지를 본다.
            # 양쪽을 소문자로 낮추면 영어가 섞여도 대소문자를 무시하고 찾을 수 있다.
            if keyword is not None and keyword.lower() not in t["description"].lower():
                continue

            results.append(t)

        # 날짜 오름차순, 같은 날짜면 ID 오름차순.
        # key에 튜플을 주면 앞의 값으로 먼저, 같으면 뒤의 값으로 정렬한다.
        results.sort(key=lambda t: (t["date"], t["id"]))

        # 결과가 0건이어도 "검색은 성공했고 결과가 없을 뿐"이므로 ok는 True다.
        # 여기서 False를 주면 LLM이 오류가 났다고 오해한다.
        if results:
            message = f"조건에 맞는 거래 {len(results)}건을 찾았습니다."
        else:
            message = "조건에 맞는 거래가 없습니다."

        # count를 따로 담는 이유: LLM이 "여러 건이니 되물어야겠다"를 즉시 판단할 수 있게.
        return {
            "ok": True,
            "data": {"count": len(results), "transactions": results},
            "message": message,
        }

    def update_transaction(self, transaction_id, amount=None, category=None,
                           description=None, date=None):
        """거래의 금액/카테고리/설명/날짜를 수정한다. 주어진 항목만 바꾼다.

        transaction_type은 수정 대상에 없다. 수입을 지출로 바꾸는 것은 사실상
        다른 거래이므로 삭제 후 재등록이 올바른 방법이다.
        """
        # 1) LLM이 ID를 "3"처럼 문자열로 보낼 수 있다.
        #    3 == "3"은 False라서 변환하지 않으면 있는 거래도 못 찾는다.
        try:
            transaction_id = int(transaction_id)
        except (TypeError, ValueError):
            # 숫자로 바꿀 수 없는 값이 왔다는 건 그런 거래가 존재할 수 없다는 뜻이다.
            return {"ok": False, "error": "NOT_FOUND",
                    "message": f"거래 ID가 올바르지 않습니다: {transaction_id}"}

        # 2) ID로 거래를 찾는다.
        #    리스트에는 "3번을 바로 꺼내는" 기능이 없으므로 처음부터 훑는다.
        #    ID는 유일하므로 찾는 즉시 break로 반복을 끝낸다.
        target = None
        for t in self.transactions:
            if t["id"] == transaction_id:
                target = t
                break

        if target is None:
            return {"ok": False, "error": "NOT_FOUND",
                    "message": f"{transaction_id}번 거래를 찾을 수 없습니다."}

        # 3) 수정할 항목이 하나도 없으면 거절한다.
        #    이 검사가 없으면 아무것도 안 바꾸고 "수정했습니다"라고 답하게 된다.
        if amount is None and category is None and description is None and date is None:
            return {"ok": False, "error": "NOTHING_TO_UPDATE",
                    "message": "수정할 항목이 없습니다. "
                               "금액, 카테고리, 설명, 날짜 중 하나 이상을 알려주세요."}

        # 4) 주어진 값들을 먼저 전부 검사한다. 아직 고치지 않는다.
        #    검사와 수정을 섞으면 중간에 실패했을 때
        #    금액만 바뀌고 날짜는 안 바뀐 반쪽짜리 거래가 남는다.
        new_amount = None
        if amount is not None:
            new_amount = self._validate_amount(amount)
            if new_amount is None:
                return {"ok": False, "error": "INVALID_AMOUNT",
                        "message": "금액은 0보다 큰 숫자여야 합니다."}

        if date is not None and not self._validate_date(date):
            return {"ok": False, "error": "INVALID_DATE",
                    "message": "날짜는 YYYY-MM-DD 형식이어야 합니다. 예: 2026-08-27"}

        if category is not None and not self._validate_category(category, target["type"]):
            # 수정할 때는 유형을 받지 않으므로, 이 거래가 원래 무엇이었는지를 기준으로 검사한다.
            if target["type"] == "지출":
                allowed = ", ".join(self.expense_categories)
            else:
                allowed = ", ".join(self.income_categories)
            return {"ok": False, "error": "INVALID_CATEGORY",
                    "message": f"'{category}'는 {target['type']} 카테고리가 아닙니다. "
                               f"사용 가능: {allowed}"}

        # 5) 고치기 전 상태를 복사해 둔다.
        #    리스트에서 꺼낸 딕셔너리는 원본을 가리키는 이름표다.
        #    before = target 이라고 쓰면 수정하는 순간 before도 함께 바뀌어
        #    "5,000원 → 4,500원"이 "4,500원 → 4,500원"이 되어버린다.
        before = target.copy()

        # 6) 주어진 항목만 반영한다. None인 항목은 "안 바꾼다"는 뜻이다.
        #    무엇이 어떻게 바뀌었는지 문장으로 모아두면 message가 풍부해진다.
        changes = []
        if new_amount is not None:
            target["amount"] = new_amount
            changes.append(f"금액 {before['amount']:,}원 → {new_amount:,}원")
        if category is not None:
            target["category"] = category
            changes.append(f"카테고리 {before['category']} → {category}")
        if description is not None:
            target["description"] = description
            changes.append(f"설명 '{before['description']}' → '{description}'")
        if date is not None:
            target["date"] = date
            changes.append(f"날짜 {before['date']} → {date}")

        self._save()

        # 7) before/after를 함께 주면 무엇이 어떻게 바뀌었는지 정확히 설명할 수 있다.
        return {
            "ok": True,
            "data": {"before": before, "after": target.copy()},
            "message": f"[{transaction_id}]번 거래를 수정했습니다. " + ", ".join(changes),
        }

    def delete_transaction(self, transaction_id):
        """거래를 삭제한다. 구조는 update_transaction과 거의 같다."""
        try:
            transaction_id = int(transaction_id)
        except (TypeError, ValueError):
            return {"ok": False, "error": "NOT_FOUND",
                    "message": f"거래 ID가 올바르지 않습니다: {transaction_id}"}

        target = None
        for t in self.transactions:
            if t["id"] == transaction_id:
                target = t
                break

        if target is None:
            return {"ok": False, "error": "NOT_FOUND",
                    "message": f"{transaction_id}번 거래를 찾을 수 없습니다."}

        # 삭제한 내용을 알려주려면 지우기 전에 복사해 두어야 한다.
        # 지운 뒤에는 확인할 방법이 없다.
        removed = target.copy()
        self.transactions.remove(target)
        self._save()

        # next_id 는 되돌리지 않는다. 지운 번호를 재사용하면
        # 예전 대화에 나온 ID가 다른 거래를 가리키게 된다.
        return {
            "ok": True,
            "data": removed,
            "message": f"[{removed['id']}] {removed['date']} {removed['category']} "
                       f"{removed['amount']:,}원 거래를 삭제했습니다.",
        }

    def set_budget(self, month, category, amount):
        """특정 월의 카테고리별 예산을 설정한다. 이미 있으면 덮어쓴다."""
        # 1) 월 형식 검사.
        #    "2026-8"로 저장한 예산을 "2026-08"로 조회하면 못 찾으므로 형식을 고정해야 한다.
        if not self._validate_month(month):
            return {"ok": False, "error": "INVALID_MONTH",
                    "message": "월은 YYYY-MM 형식이어야 합니다. 예: 2026-08"}

        # 2) 예산은 "이만큼만 쓰자"는 뜻이라 수입에는 의미가 없다.
        #    유형을 "지출"로 고정해서 검사하면 "월급 예산 300만원" 같은 요청을 막을 수 있다.
        if not self._validate_category(category, "지출"):
            allowed = ", ".join(self.expense_categories)
            return {"ok": False, "error": "INVALID_CATEGORY",
                    "message": f"예산은 지출 카테고리에만 설정할 수 있습니다. 사용 가능: {allowed}"}

        # 3) 금액 검사 + 정수 변환.
        #    나중에 remaining = budget - spent 를 계산하려면 예산도 정수여야 한다.
        value = self._validate_amount(amount)
        if value is None:
            return {"ok": False, "error": "INVALID_AMOUNT",
                    "message": "예산은 0보다 큰 숫자여야 합니다."}

        # 4) budgets는 딕셔너리 안의 딕셔너리다.
        #    바깥 열쇠(월)가 없는 상태에서 self.budgets[month][category]로 접근하면
        #    KeyError가 나므로, 없으면 빈 딕셔너리를 먼저 만들어야 한다.
        if month not in self.budgets:
            self.budgets[month] = {}
        self.budgets[month][category] = value
        self._save()

        return {
            "ok": True,
            "data": {"month": month, "category": category, "amount": value},
            "message": f"{month} {category} 예산을 {value:,}원으로 설정했습니다.",
        }

    def get_budget_status(self, month, category=None):
        """예산 대비 사용 금액과 남은 금액을 계산해서 알려준다.

        사용액은 따로 저장해두지 않고 부를 때마다 계산한다.
        저장해두면 거래가 수정·삭제될 때마다 같이 고쳐야 해서 금방 어긋나지만,
        매번 세면 항상 정확하다.
        """
        # 1) 월 형식 검사
        if not self._validate_month(month):
            return {"ok": False, "error": "INVALID_MONTH",
                    "message": "월은 YYYY-MM 형식이어야 합니다. 예: 2026-08"}

        # 2) 그 달의 예산을 꺼낸다.
        #    예산을 세우지 않았는데 "남은 금액"을 말할 수는 없다.
        #    조용히 0으로 처리하면 사용자가 예산을 세운 줄 착각하므로 오류로 분명히 알린다.
        #    .get 을 쓰면 열쇠가 없어도 KeyError 대신 None 이 나온다.
        month_budgets = self.budgets.get(month)
        if not month_budgets:
            return {"ok": False, "error": "NO_BUDGET_SET",
                    "message": f"{month}에 설정된 예산이 없습니다."}

        # 3) 계산할 카테고리 목록을 정한다.
        #    카테고리를 지정한 경우와 안 한 경우를 각각 처리하면 코드가 두 벌이 된다.
        #    "대상 목록"으로 통일해두면 아래 반복문 하나로 둘 다 처리된다.
        if category is not None:
            if category not in month_budgets:
                return {"ok": False, "error": "NO_BUDGET_SET",
                        "message": f"{month} {category} 예산이 설정되어 있지 않습니다."}
            targets = [category]
        else:
            targets = list(month_budgets.keys())

        # 4) 카테고리마다 사용액을 계산한다.
        items = []
        for cat in targets:
            budget = month_budgets[cat]

            spent = 0
            for t in self.transactions:
                # type 검사를 빠뜨리면 그 달 월급이 식비 사용액에 더해져
                # "예산을 293만원 초과했습니다" 같은 엉뚱한 답이 나온다.
                if (t["type"] == "지출"
                        and t["category"] == cat
                        and t["date"].startswith(month)):
                    spent += t["amount"]

            items.append({
                "category": cat,
                "budget": budget,
                "spent": spent,
                # 음수를 그대로 둔다. 0으로 막으면 얼마나 초과했는지 알려줄 수 없다.
                "remaining": budget - spent,
                # round 를 안 하면 37.333333333333336 같은 값이 그대로 읽힌다.
                "usage_rate": round(spent / budget * 100, 1),
                # 별도 키로 주면 LLM이 경고 문구를 붙이기 쉬워진다.
                "over_budget": spent > budget,
            })

        # 5) 카테고리가 여러 개일 수 있으므로 리스트에 담는다.
        #    하나만 조회해도 리스트 형태로 통일하면 LLM이 결과를 읽는 방법이 항상 같아진다.
        lines = []
        for item in items:
            if item["over_budget"]:
                lines.append(f"{item['category']}: 예산 {item['budget']:,}원 중 "
                             f"{item['spent']:,}원 사용, {-item['remaining']:,}원 초과")
            else:
                lines.append(f"{item['category']}: 예산 {item['budget']:,}원 중 "
                             f"{item['spent']:,}원 사용, {item['remaining']:,}원 남음")

        return {
            "ok": True,
            "data": {"month": month, "items": items},
            "message": f"{month} 예산 현황 — " + " / ".join(lines),
        }

    def generate_monthly_report(self, month):
        """월별 거래 내역을 Markdown 보고서 파일로 저장한다."""
        if not self._validate_month(month):
            return {"ok": False, "error": "INVALID_MONTH",
                    "message": "월은 YYYY-MM 형식이어야 합니다. 예: 2026-08"}

        # 그 달 거래만 모은다. 하나도 없으면 빈 파일을 만드는 대신 알려준다.
        targets = [t for t in self.transactions if t["date"].startswith(month)]
        if not targets:
            return {"ok": False, "error": "NO_DATA",
                    "message": f"{month}에 거래 내역이 없습니다."}

        targets.sort(key=lambda t: (t["date"], t["id"]))

        income = sum(t["amount"] for t in targets if t["type"] == "수입")
        expense = sum(t["amount"] for t in targets if t["type"] == "지출")

        # 문자열을 + 로 계속 이어붙이면 읽기 어렵고 느리다.
        # 리스트에 한 줄씩 담았다가 마지막에 join 으로 합치는 편이 낫다.
        year, mon = month.split("-")
        lines = [f"# {year}년 {mon}월 거래 보고서", ""]

        lines += ["## 요약", "",
                  f"- 총 수입: {income:,}원",
                  f"- 총 지출: {expense:,}원",
                  f"- 잔액: {income - expense:,}원", ""]

        # 이미 만들어 둔 기능을 다시 쓰는 것이 같은 계산을 또 짜는 것보다 낫다.
        status = self.get_budget_status(month)
        if status["ok"]:
            lines += ["## 예산 현황", "",
                      "| 카테고리 | 예산 | 사용 | 남음 | 사용률 |",
                      "|---|---|---|---|---|"]
            for item in status["data"]["items"]:
                lines.append(f"| {item['category']} | {item['budget']:,} | {item['spent']:,} | "
                             f"{item['remaining']:,} | {item['usage_rate']}% |")
            lines.append("")

        lines += ["## 거래 내역", "",
                  "| ID | 날짜 | 유형 | 카테고리 | 금액 | 설명 |",
                  "|---|---|---|---|---|---|"]
        for t in targets:
            lines.append(f"| {t['id']} | {t['date']} | {t['type']} | {t['category']} | "
                         f"{t['amount']:,} | {t['description']} |")

        filename = f"report_{month}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return {
            "ok": True,
            "data": {"filename": filename, "count": len(targets),
                     "income": income, "expense": expense, "balance": income - expense},
            "message": f"{month} 보고서를 {filename} 파일로 저장했습니다. "
                       f"거래 {len(targets)}건, 수입 {income:,}원, 지출 {expense:,}원",
        }
