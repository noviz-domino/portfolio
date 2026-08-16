"""
ReplyGate D1 — JSON 강제 출력 원인 진단

d1_verify.py 에서 형식 A/B 가 모두 실패했을 때 원인을 좁히기 위한 스크립트.
5가지 변형을 같은 모델에 순서대로 던지고, 실패 시 에러 본문을 그대로 출력한다.

실행:  python d1_verify2.py
모델을 직접 고르려면:  set GEMINI_MODEL=gemini-2.5-flash  (Windows CMD)
                       $env:GEMINI_MODEL="gemini-2.5-flash"  (PowerShell)
"""

import json
import os
import re
import urllib.error
import urllib.request

BASE = "https://generativelanguage.googleapis.com"

API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()
if not API_KEY:
    API_KEY = input("Gemini API 키를 붙여넣으세요: ").strip()


def request(path, payload=None):
    url = "{}/{}?key={}".format(BASE, path.lstrip("/"), API_KEY)
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"} if data else {}
    req = urllib.request.Request(url, data=data, headers=headers,
                                 method="POST" if data else "GET")
    try:
        with urllib.request.urlopen(req, timeout=60) as res:
            return True, json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return False, "HTTP {}\n{}".format(e.code, e.read().decode("utf-8", errors="replace"))
    except Exception as e:
        return False, "{}: {}".format(type(e).__name__, e)


# ------------------------------------------------------------ 모델 선택
ok, res = request("v1beta/models")
candidates = []
if ok:
    for m in res.get("models", []):
        name = m.get("name", "").replace("models/", "")
        methods = m.get("supportedGenerationMethods", []) or m.get("supportedActions", [])
        if "generateContent" in methods:
            candidates.append(name)

# 구버전 모델은 신규 사용자에게 404가 나므로 최신 flash 계열을 우선한다
PREFERRED = [
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3-flash-preview",
    "gemini-3.1-flash-lite",
    "gemini-flash-latest",
    "gemini-2.0-flash",
]

MODEL = os.environ.get("GEMINI_MODEL", "").strip()
if not MODEL:
    MODEL = next(
        (m for m in PREFERRED if m in candidates),
        next((n for n in candidates if "flash" in n), candidates[0] if candidates else "gemini-3.6-flash"),
    )

print("사용 가능한 생성 모델:")
for n in candidates:
    print("   -", n)
print("\n이번 테스트 모델:", MODEL)
print("(바꾸려면 환경변수 GEMINI_MODEL 설정)\n")


PROMPT = (
    "너는 이커머스 쇼핑몰의 CS 분류기다. 아래 고객 문의를 분류하라.\n\n"
    "문의: 지난주 화요일에 주문 취소했는데 아직도 환불이 안 들어왔어요. "
    "벌써 열흘째입니다. 언제까지 기다려야 하나요?\n\n"
    "category 는 환불/배송/교환반품/불량AS/회원적립금/기타 중 하나, "
    "sentiment 는 불만/중립/단순문의 중 하나로 판정하고 summary 는 한 문장으로 요약하라."
)

SCHEMA_LOWER = {
    "type": "object",
    "properties": {
        "category": {"type": "string"},
        "sentiment": {"type": "string"},
        "summary": {"type": "string"},
    },
    "required": ["category", "sentiment", "summary"],
}

SCHEMA_UPPER = {
    "type": "OBJECT",
    "properties": {
        "category": {"type": "STRING"},
        "sentiment": {"type": "STRING"},
        "summary": {"type": "STRING"},
    },
    "required": ["category", "sentiment", "summary"],
}

FENCE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$", re.IGNORECASE)


def extract_text(res):
    try:
        return res["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError):
        return None


def try_variant(label, payload):
    print("\n" + "-" * 60)
    print("[{}]".format(label))
    print("-" * 60)
    ok, res = request("v1beta/models/{}:generateContent".format(MODEL), payload)
    if not ok:
        print("요청 실패:")
        print(res[:1200])
        return False

    text = extract_text(res)
    if text is None:
        print("응답에 텍스트가 없음. 전체 응답:")
        print(json.dumps(res, ensure_ascii=False)[:1200])
        return False

    print("원문 응답:")
    print(repr(text[:400]))

    # 1차: 그대로 파싱
    try:
        parsed = json.loads(text)
        print("→ 그대로 JSON 파싱 성공")
    except json.JSONDecodeError:
        # 2차: 코드펜스 제거 후 파싱
        stripped = FENCE.sub("", text).strip()
        try:
            parsed = json.loads(stripped)
            print("→ 코드펜스 제거 후 파싱 성공  (★ 응답은 정상, 펜스만 문제였음)")
        except json.JSONDecodeError:
            print("→ 파싱 실패")
            return False

    print("   category :", parsed.get("category"))
    print("   sentiment:", parsed.get("sentiment"))
    print("   summary  :", parsed.get("summary"))
    return True


results = {}

results["A1 generationConfig + 소문자 스키마"] = try_variant(
    "A1  generationConfig.responseSchema (소문자 type)",
    {
        "contents": [{"parts": [{"text": PROMPT}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": SCHEMA_LOWER,
        },
    },
)

results["A2 generationConfig + 대문자 스키마"] = try_variant(
    "A2  generationConfig.responseSchema (대문자 TYPE)",
    {
        "contents": [{"parts": [{"text": PROMPT}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": SCHEMA_UPPER,
        },
    },
)

results["A3 responseMimeType만 (스키마 없음)"] = try_variant(
    "A3  responseMimeType 만 지정, 스키마 없음",
    {
        "contents": [{"parts": [{"text": PROMPT}]}],
        "generationConfig": {"responseMimeType": "application/json"},
    },
)

results["B  response_format"] = try_variant(
    "B   response_format (신형 문서 표기)",
    {
        "contents": [{"parts": [{"text": PROMPT}]}],
        "response_format": {
            "type": "text",
            "mime_type": "application/json",
            "schema": SCHEMA_LOWER,
        },
    },
)

results["C  프롬프트 유도 (폴백안)"] = try_variant(
    "C   프롬프트로만 유도 — 스키마 미사용 (폴백 방식)",
    {
        "contents": [
            {
                "parts": [
                    {
                        "text": PROMPT
                        + "\n\n반드시 아래 형태의 JSON 객체 하나만 출력하라. "
                        '설명, 인사말, 코드블록 표시 없이 JSON만 출력한다.\n'
                        '{"category": "...", "sentiment": "...", "summary": "..."}'
                    }
                ]
            }
        ]
    },
)


print("\n" + "=" * 60)
print("진단 결과")
print("=" * 60)
for k, v in results.items():
    print("{:38s} : {}".format(k, "성공" if v else "실패"))

print("\n해석 가이드")
print("  A2만 성공        → 스키마 타입을 대문자로 써야 함. n8n에서도 대문자로.")
print("  A3/C만 성공      → 스키마 강제는 불가. 프롬프트 유도 + 파싱 재시도로 간다.")
print("  전부 실패        → 모델을 바꿔서 재시도 (GEMINI_MODEL 환경변수).")
print("  '펜스만 문제였음' → 강제 출력은 되고 있고 파서에 펜스 제거만 넣으면 됨.")
