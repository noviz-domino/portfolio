"""
P2 초안 생성 품질 모델 비교

같은 프롬프트를 여러 모델에 던져 초안 품질을 나란히 본다.
케이스 2개:
  ① 정상   — 정책 조항으로 답할 수 있는 문의. 수치를 정확히 인용하는지 본다.
  ② 함정   — 정책에 없는 주제(해외배송). insufficient_info=true 로 빠지는지 본다.

실행:  python compare_models.py
결과는 화면 출력 + eval/모델비교_결과.md 로 저장된다.
"""

import json
import os
import urllib.error
import urllib.request

BASE = "https://generativelanguage.googleapis.com"

API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
if not API_KEY:
    API_KEY = input("Gemini API 키: ").strip()

MODELS = [
    "gemini-3.6-flash",        # 현재 사용 중 (RPD 20)
    "gemini-3.5-flash-lite",   # 후보 A (RPD 500)
    "gemini-3.1-flash-lite",   # 후보 B (RPD 500)
]

TONE = {
    "불만": "첫 문장에서 불편에 대해 사과한다. 변명을 앞세우지 않는다. 처리 일정과 보상 가능 여부를 먼저 제시하고 사유는 뒤에 짧게 붙인다.",
    "중립": "사과 없이 바로 본론. 요청한 정보를 순서대로 제시하고 간결하게 끝낸다.",
    "단순문의": "친절하고 짧게. 필요하면 확인 경로(마이페이지 등)를 함께 안내한다.",
}

CASES = [
    {
        "id": "정상 · 환불 지연",
        "name": "김민석",
        "category": "환불",
        "sentiment": "불만",
        "content": "일주일 전에 반품 신청했는데 아직 환불이 안 됐어요. 언제까지 기다려야 하나요?",
        "clauses": (
            "[RF-09] 회수 후 환불 처리 — 반품 상품이 물류센터에 도착한 날로부터 영업일 기준 2일 이내에 "
            "검수가 완료되고, 검수 통과 시 환불 처리 소요 기간에 따라 환급됩니다.\n"
            "[RF-02] 환불 처리 소요 기간 — 환불 승인 후 영업일 기준 3일 이내에 결제 수단으로 환급됩니다. "
            "카드사 사정에 따라 카드 취소는 최대 영업일 기준 5일이 추가로 소요될 수 있습니다.\n"
            "[RF-13] 지연 시 문의 — 환불 신청 후 영업일 기준 7일이 지나도 처리되지 않은 경우 "
            "고객센터로 문의하시면 우선 처리해 드립니다."
        ),
        "expect": "RF-09 2일 / RF-02 3일·5일 / RF-13 7일 을 정확히 인용. 없는 수치 금지. insufficient_info=false",
    },
    {
        "id": "함정 · 해외배송",
        "name": "이수진",
        "category": "배송",
        "sentiment": "중립",
        "content": "미국으로도 보내주시나요? 해외 배송비는 얼마고 며칠 걸리나요?",
        "clauses": (
            "[DL-01] 기본 배송 기간 — 결제 완료 후 영업일 기준 1~3일 이내 출고되며, "
            "출고 후 1~2일 이내 수령하실 수 있습니다.\n"
            "[DL-03] 도서산간 추가 배송비 — 제주도는 3,000원, 그 외 도서산간 지역은 5,000원의 "
            "추가 배송비가 발생합니다.\n"
            "[DL-02] 배송비 — 주문 금액 50,000원 이상 무료배송, 미만인 경우 3,000원입니다."
        ),
        "expect": "정책에 해외배송이 없음. insufficient_info=true 로 두고 '확인 후 안내' 로 답해야 정답. "
                  "국내 배송 기간·배송비를 해외에 적용하면 환각.",
    },
]

SCHEMA = {
    "type": "object",
    "properties": {
        "subject": {"type": "string"},
        "body": {"type": "string"},
        "cited_clauses": {"type": "array", "items": {"type": "string"}},
        "insufficient_info": {"type": "boolean"},
    },
    "required": ["subject", "body", "cited_clauses", "insufficient_info"],
}


def build_prompt(case):
    return "\n".join([
        '너는 이커머스 쇼핑몰 "온마켓"의 고객 응대 담당자다.',
        "아래 고객 문의에 대한 답변 이메일 초안을 작성하라.",
        "",
        "■ 절대 규칙",
        "1. 아래 [정책 근거]에 적혀 있지 않은 수치·기간·금액·조건은 절대 쓰지 마라.",
        "   기억하고 있는 일반적인 쇼핑몰 관행을 끌어와서는 안 된다.",
        "2. [정책 근거]로 답할 수 없는 문의라면, 답을 지어내지 말고",
        '   insufficient_info 를 true 로 두고 "담당 부서 확인 후 안내드리겠습니다"로 작성하라.',
        "3. 실제로 인용한 조항의 ID만 cited_clauses 에 넣어라. 참고만 하고 쓰지 않은 조항은 넣지 마라.",
        "",
        "■ 어조 지침 (sentiment = {})".format(case["sentiment"]),
        TONE[case["sentiment"]],
        "",
        "■ 작성 형식",
        "- 인사 → 본문 → 마무리 순서",
        "- 존댓말, 400자 내외",
        "- 정책 조항을 그대로 복사하지 말고 이 고객의 상황에 맞춰 풀어 쓴다",
        "- 조항 ID(RF-01 등)는 본문에 노출하지 않는다",
        '- 서명은 "온마켓 고객센터 드림"',
        '- 고객 이름은 "{}" 이다'.format(case["name"]),
        "",
        "■ 고객 문의",
        case["content"],
        "",
        "■ 문의 유형",
        case["category"],
        "",
        "■ 정책 근거",
        case["clauses"],
    ])


def call(model, prompt):
    url = "{}/v1beta/models/{}:generateContent?key={}".format(BASE, model, API_KEY)
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": SCHEMA,
        },
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as res:
            data = json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"_error": "HTTP {} — {}".format(e.code, e.read().decode("utf-8", errors="replace")[:300])}
    except Exception as e:
        return {"_error": "{}: {}".format(type(e).__name__, e)}

    try:
        text = data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError):
        return {"_error": "응답 구조 이상: " + json.dumps(data, ensure_ascii=False)[:300]}

    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"_error": "JSON 파싱 실패: " + text[:300]}


lines = ["# P2 초안 생성 — 모델 품질 비교", ""]

for case in CASES:
    header = "## {}".format(case["id"])
    print("\n" + "=" * 70)
    print(header)
    print("=" * 70)
    print("문의:", case["content"])
    print("기대:", case["expect"])

    lines += [header, "", "**문의:** {}".format(case["content"]), "",
              "**기대 동작:** {}".format(case["expect"]), ""]

    prompt = build_prompt(case)

    for model in MODELS:
        print("\n" + "-" * 70)
        print("[{}]".format(model))
        print("-" * 70)
        r = call(model, prompt)

        if "_error" in r:
            print("실패:", r["_error"])
            lines += ["### {}".format(model), "", "```", "실패: " + r["_error"], "```", ""]
            continue

        body = r.get("body", "")
        cited = r.get("cited_clauses", [])
        insuf = r.get("insufficient_info")

        print("insufficient_info :", insuf)
        print("cited_clauses     :", ", ".join(cited) if cited else "(없음)")
        print("subject           :", r.get("subject", ""))
        print("본문 {}자".format(len(body)))
        print(body)

        lines += [
            "### {}".format(model), "",
            "- `insufficient_info`: **{}**".format(insuf),
            "- `cited_clauses`: {}".format(", ".join(cited) if cited else "(없음)"),
            "- 제목: {}".format(r.get("subject", "")),
            "- 본문 길이: {}자".format(len(body)),
            "", "```", body, "```", "",
        ]

os.makedirs("eval", exist_ok=True)
with open(os.path.join("eval", "모델비교_결과.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print("\n\n저장 완료: eval/모델비교_결과.md")
