"""
ReplyGate D1 리스크 검증 스크립트

확인 항목
  1. 내 API 키로 쓸 수 있는 모델 목록
  2. JSON 강제 출력 (형식 A: generationConfig.responseSchema)
  3. JSON 강제 출력 (형식 B: response_format)
  4. 임베딩 엔드포인트 동작 여부 (RAG 가능 여부)

실행:  python d1_verify.py
키는 환경변수 GEMINI_API_KEY 에서 읽고, 없으면 입력받는다.
"""

import json
import os
import urllib.error
import urllib.request

BASE = "https://generativelanguage.googleapis.com"

API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
if not API_KEY:
    API_KEY = input("Gemini API 키를 붙여넣으세요: ").strip()


def request(path, payload=None, method=None):
    """Gemini API 호출. (성공여부, 응답 또는 에러문자열) 반환"""
    url = "{}/{}?key={}".format(BASE, path.lstrip("/"), API_KEY)
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(
        url, data=data, headers=headers, method=method or ("POST" if data else "GET")
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as res:
            return True, json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return False, "HTTP {} — {}".format(e.code, body[:500])
    except Exception as e:  # 네트워크 등
        return False, "{}: {}".format(type(e).__name__, e)


def section(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


# ---------------------------------------------------------------- 1. 모델 목록
section("[1] 사용 가능한 모델 조회")

ok, res = request("v1beta/models")
generate_models, embed_models = [], []

if not ok:
    print("실패:", res)
    print("→ 키가 잘못됐거나 API가 활성화되지 않았을 수 있습니다.")
else:
    for m in res.get("models", []):
        name = m.get("name", "").replace("models/", "")
        methods = m.get("supportedGenerationMethods", []) or m.get(
            "supportedActions", []
        )
        if "generateContent" in methods:
            generate_models.append(name)
        if "embedContent" in methods:
            embed_models.append(name)

    print("생성 가능 모델 {}개:".format(len(generate_models)))
    for n in generate_models:
        print("   -", n)
    print("\n임베딩 가능 모델 {}개:".format(len(embed_models)))
    for n in embed_models:
        print("   -", n)

# 테스트에 쓸 모델 고르기 (flash 계열 우선, 없으면 첫 번째)
TEST_MODEL = next(
    (n for n in generate_models if "flash" in n and "lite" not in n),
    generate_models[0] if generate_models else "gemini-2.5-flash",
)
EMBED_MODEL = embed_models[0] if embed_models else "text-embedding-004"
print("\n→ 테스트에 사용할 생성 모델:", TEST_MODEL)
print("→ 테스트에 사용할 임베딩 모델:", EMBED_MODEL)


# ------------------------------------------------- 실제 CS 문의로 분류 테스트
PROMPT = (
    "너는 이커머스 쇼핑몰의 CS 분류기다. 아래 고객 문의를 분류하라.\n\n"
    "문의: 지난주 화요일에 주문 취소했는데 아직도 환불이 안 들어왔어요. "
    "벌써 열흘째입니다. 언제까지 기다려야 하나요?\n\n"
    "category 는 환불/배송/교환반품/불량AS/회원적립금/기타 중 하나, "
    "sentiment 는 불만/중립/단순문의 중 하나로 판정하고 summary 는 한 문장으로 요약하라."
)

SCHEMA = {
    "type": "object",
    "properties": {
        "category": {"type": "string"},
        "sentiment": {"type": "string"},
        "summary": {"type": "string"},
    },
    "required": ["category", "sentiment", "summary"],
}


def show_json_result(ok, res, label):
    if not ok:
        print("실패:", res)
        return False
    try:
        text = res["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError):
        print("응답 구조가 예상과 다릅니다:")
        print(json.dumps(res, ensure_ascii=False)[:800])
        return False
    print("원문 응답:", text.strip()[:400])
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        print("→ {}: 응답이 순수 JSON이 아님 (파싱 실패)".format(label))
        return False
    print("→ {}: JSON 파싱 성공".format(label))
    print("   category :", parsed.get("category"))
    print("   sentiment:", parsed.get("sentiment"))
    print("   summary  :", parsed.get("summary"))
    return True


# ------------------------------------------- 2. 형식 A (generationConfig 방식)
section("[2] JSON 강제 출력 — 형식 A (generationConfig.responseSchema)")

ok, res = request(
    "v1beta/models/{}:generateContent".format(TEST_MODEL),
    {
        "contents": [{"parts": [{"text": PROMPT}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": SCHEMA,
        },
    },
)
form_a = show_json_result(ok, res, "형식 A")


# ---------------------------------------------- 3. 형식 B (response_format 방식)
section("[3] JSON 강제 출력 — 형식 B (response_format)")

ok, res = request(
    "v1beta/models/{}:generateContent".format(TEST_MODEL),
    {
        "contents": [{"parts": [{"text": PROMPT}]}],
        "response_format": {
            "type": "text",
            "mime_type": "application/json",
            "schema": SCHEMA,
        },
    },
)
form_b = show_json_result(ok, res, "형식 B")


# ------------------------------------------------------ 4. 임베딩 (RAG 가능성)
section("[4] 임베딩 엔드포인트 (RAG 가능 여부)")

ok, res = request(
    "v1beta/models/{}:embedContent".format(EMBED_MODEL),
    {
        "model": "models/{}".format(EMBED_MODEL),
        "content": {"parts": [{"text": "환불은 수령일로부터 14일 이내에 신청할 수 있습니다."}]},
    },
)
if ok:
    vec = res.get("embedding", {}).get("values", [])
    print("성공. 벡터 차원:", len(vec))
    print("앞 5개 값:", [round(v, 4) for v in vec[:5]])
    embed_ok = True
else:
    print("실패:", res)
    embed_ok = False


# ------------------------------------------------------------------- 결과 요약
section("D1 검증 결과 요약")

print("모델 조회        :", "OK" if generate_models else "실패")
print("JSON 형식 A      :", "OK" if form_a else "실패")
print("JSON 형식 B      :", "OK" if form_b else "실패")
print("임베딩(RAG)      :", "OK" if embed_ok else "실패")

print("\n판단:")
if form_a or form_b:
    print("  JSON 강제 출력이 되므로 유형·감정 분기를 스키마로 안전하게 처리할 수 있습니다.")
    print("  n8n에서는 성공한 형식을 HTTP Request 노드 본문에 그대로 넣으면 됩니다.")
else:
    print("  JSON 강제 출력이 실패했습니다. 프롬프트로 JSON을 유도하고,")
    print("  파싱 실패 시 1회 재시도 + 폴백(기타/중립) 로직을 반드시 넣어야 합니다.")

if embed_ok:
    print("  임베딩이 동작하므로 RAG 설계를 그대로 진행할 수 있습니다.")
else:
    print("  임베딩이 실패했습니다. 정책 문서를 프롬프트에 직접 넣는 방식으로 축소해야 합니다.")

print("\n※ 분당/일당 요청 한도는 API로 조회되지 않습니다.")
print("  https://aistudio.google.com/rate-limit 에서 직접 확인하세요.")
