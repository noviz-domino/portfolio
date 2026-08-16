"""
ReplyGate 평가셋 측정

같은 평가셋 50건을 두 조건으로 돌려 비교한다.
  베이스라인 : 정책 문서 없이 P4 로 답변 생성
  RAG        : P1 분류 → 조항 검색 → P2 생성 (워크플로우와 동일)

요청 본문은 n8n HTTP Request 노드와 동일하게 맞췄다. 모델도 같다.

실행
  $env:GEMINI_API_KEY="<키>"; python scripts/run_eval.py
  python scripts/run_eval.py --score      검수표를 읽어 1차 승인률까지 포함한 최종 리포트

산출물 (eval/)
  측정_원본.json        모든 응답 원본. 중단 시 여기서 이어서 실행한다
  측정_검수표.tsv        사람이 승인/수정을 표시하는 표
  측정결과.md           지표 리포트
"""

import argparse
import csv
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.request

BASE = "https://generativelanguage.googleapis.com"
GEN_MODEL = "gemini-3.5-flash-lite"
EMBED_MODEL = "gemini-embedding-001"
EMBED_DIM = 768

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLAUSES_TSV = os.path.join(ROOT, "data", "조항_시트.tsv")
EVALSET_TSV = os.path.join(ROOT, "data", "평가셋_50건.tsv")
EVAL_DIR = os.path.join(ROOT, "eval")
RAW_PATH = os.path.join(EVAL_DIR, "측정_원본.json")
EMB_CACHE = os.path.join(EVAL_DIR, "조항_임베딩_캐시.json")
REVIEW_PATH = os.path.join(EVAL_DIR, "측정_검수표.tsv")
REPORT_PATH = os.path.join(EVAL_DIR, "측정결과.md")

# RPM 15 이므로 생성 호출은 최소 4.3초 간격. 여유를 두어 4.5초.
GEN_INTERVAL = 4.5
EMBED_INTERVAL = 0.8

API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()

TONE = {
    "불만": "첫 문장에서 불편에 대해 사과한다. 변명을 앞세우지 않는다. 처리 일정과 보상 가능 여부를 먼저 제시하고 사유는 뒤에 짧게 붙인다.",
    "일반": "사과 없이 바로 본론. 요청한 정보를 순서대로 제시하고 간결하게 끝낸다.",
}

LOOKUP_HINT = (
    "이 문의는 고객의 특정 주문·계정을 확인해야 답이 완결된다. "
    "규정을 먼저 안내한 뒤, 마지막에 주문번호 등 확인에 필요한 정보를 정중히 요청하라."
)

P1_SCHEMA = {
    "type": "object",
    "properties": {
        "category": {"type": "string", "enum": ["환불", "배송", "교환반품", "불량AS", "회원적립금", "기타"]},
        "sentiment": {"type": "string", "enum": ["불만", "일반"]},
        "needs_order_lookup": {"type": "boolean"},
        "summary": {"type": "string"},
        "search_query": {"type": "string"},
    },
    "required": ["category", "sentiment", "needs_order_lookup", "summary", "search_query"],
}

P2_SCHEMA = {
    "type": "object",
    "properties": {
        "subject": {"type": "string"},
        "body": {"type": "string"},
        "cited_clauses": {"type": "array", "items": {"type": "string"}},
        "insufficient_info": {"type": "boolean"},
    },
    "required": ["subject", "body", "cited_clauses", "insufficient_info"],
}

P4_SCHEMA = {
    "type": "object",
    "properties": {"subject": {"type": "string"}, "body": {"type": "string"}},
    "required": ["subject", "body"],
}


# ------------------------------------------------------------------ API 호출
_last_gen = [0.0]
_last_emb = [0.0]


def _throttle(slot, interval):
    wait = interval - (time.time() - slot[0])
    if wait > 0:
        time.sleep(wait)
    slot[0] = time.time()


def _post(path, payload, tries=4):
    url = "{}/{}?key={}".format(BASE, path, API_KEY)
    data = json.dumps(payload).encode("utf-8")
    for attempt in range(tries):
        req = urllib.request.Request(
            url, data=data, headers={"Content-Type": "application/json"}, method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as res:
                return json.loads(res.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            if e.code == 429 and attempt < tries - 1:
                back = 20 * (attempt + 1)
                print("    429 — {}초 후 재시도".format(back))
                time.sleep(back)
                continue
            raise RuntimeError("HTTP {} — {}".format(e.code, body[:400]))
        except Exception as e:
            if attempt < tries - 1:
                time.sleep(5)
                continue
            raise RuntimeError("{}: {}".format(type(e).__name__, e))


def generate(prompt, schema):
    _throttle(_last_gen, GEN_INTERVAL)
    res = _post(
        "v1beta/models/{}:generateContent".format(GEN_MODEL),
        {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": schema,
            },
        },
    )
    text = res["candidates"][0]["content"]["parts"][0]["text"]
    text = re.sub(r"^\s*```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```\s*$", "", text).strip()
    return json.loads(text)


def embed(text, task_type):
    _throttle(_last_emb, EMBED_INTERVAL)
    res = _post(
        "v1beta/models/{}:embedContent".format(EMBED_MODEL),
        {
            "model": "models/{}".format(EMBED_MODEL),
            "content": {"parts": [{"text": text}]},
            "taskType": task_type,
            "outputDimensionality": EMBED_DIM,
        },
    )
    return res["embedding"]["values"]


# ------------------------------------------------------------------ 데이터 적재
def read_tsv(path):
    with open(path, encoding="utf-8") as f:
        rows = list(csv.reader(f, delimiter="\t"))
    header = rows[0]
    out = []
    for r in rows[1:]:
        if not r or not r[0].strip():
            continue
        r = r + [""] * (len(header) - len(r))
        out.append(dict(zip(header, r)))
    return out


def load_clauses():
    rows = read_tsv(CLAUSES_TSV)
    return [
        {"clause_id": r["clause_id"].strip(), "doc": r["doc"], "title": r["title"], "text": r["text"]}
        for r in rows
        if r.get("clause_id", "").strip()
    ]


def clause_embeddings(clauses):
    """조항 임베딩을 만들거나 캐시에서 읽는다. 워크플로우 00 과 동일한 방식."""
    if os.path.exists(EMB_CACHE):
        with open(EMB_CACHE, encoding="utf-8") as f:
            cache = json.load(f)
        if len(cache) == len(clauses):
            print("조항 임베딩 캐시 사용 ({}건)".format(len(cache)))
            return cache

    print("조항 임베딩 생성 중 ({}건)...".format(len(clauses)))
    cache = {}
    for i, c in enumerate(clauses, 1):
        text = "[{}] {}\n{}".format(c["doc"], c["title"], c["text"])
        cache[c["clause_id"]] = embed(text, "RETRIEVAL_DOCUMENT")
        if i % 10 == 0:
            print("  {}/{}".format(i, len(clauses)))
    os.makedirs(EVAL_DIR, exist_ok=True)
    with open(EMB_CACHE, "w", encoding="utf-8") as f:
        json.dump(cache, f)
    return cache


def cosine(a, b):
    dot = na = nb = 0.0
    for x, y in zip(a, b):
        dot += x * y
        na += x * x
        nb += y * y
    d = math.sqrt(na) * math.sqrt(nb)
    return 0.0 if d == 0 else dot / d


# ------------------------------------------------------------------ 프롬프트
def p1_prompt(content):
    return "\n".join([
        '너는 이커머스 쇼핑몰 "온마켓"의 고객 문의 분류기다.', "",
        "아래 고객 문의를 읽고 네 가지를 판정하라.", "",
        "1. category — 다음 중 하나",
        "   환불 / 배송 / 교환반품 / 불량AS / 회원적립금 / 기타", "",
        "2. sentiment — 다음 중 하나",
        "   불만 : 손해·지연·부당함을 호소하거나 항의하는 문의. 어조가 정중해도 해당한다",
        "   일반 : 그 외. 정보를 묻거나 처리를 요청하는 문의", "",
        "3. needs_order_lookup — true 또는 false",
        "   이 문의에 제대로 답하려면 이 고객의 특정 주문·계정을 조회해야 하는가.",
        '   true  : "제 환불이 왜 아직인가요", "주소를 바꾸고 싶어요" 처럼 이 고객의 건을 봐야 답이 되는 문의',
        '   false : "환불은 며칠 걸리나요" 처럼 규정만 안내하면 답이 끝나는 문의',
        "   sentiment 와는 독립이다. 불만이면서 false 일 수도 있고, 일반이면서 true 일 수도 있다.", "",
        "4. summary — 담당자가 3초 안에 파악할 수 있는 한 문장 요약 (40자 이내)", "",
        "5. search_query — 사내 정책 문서에서 근거 조항을 찾기 위한 검색 문장.",
        "   고객의 구어체를 정책 문서에서 쓰는 용어로 바꿔 한 문장으로 작성하라.",
        '   예) "돈이 안 들어왔어요" → "환불 처리 소요 기간과 지연 시 문의 절차"', "",
        "판정 규칙",
        "- 여러 유형이 섞여 있으면 고객이 가장 해결받고 싶어 하는 것을 고른다.",
        '- 어조가 정중해도 손해나 지연을 호소하면 "불만"으로 본다.',
        "- 추측하지 말고 문의에 적힌 내용만으로 판정한다.", "",
        "고객 문의:", content,
    ])


def p2_prompt(content, category, sentiment, retrieved, name="김민석", needs_lookup=False):
    return "\n".join([
        '너는 이커머스 쇼핑몰 "온마켓"의 고객 응대 담당자다.',
        "아래 고객 문의에 대한 답변 이메일 초안을 작성하라.", "",
        "■ 절대 규칙",
        "1. 아래 [정책 근거]에 적혀 있지 않은 수치·기간·금액·조건은 절대 쓰지 마라.",
        "   기억하고 있는 일반적인 쇼핑몰 관행을 끌어와서는 안 된다.",
        "2. [정책 근거]로 답할 수 없는 문의라면, 답을 지어내지 말고",
        '   insufficient_info 를 true 로 두고 "담당 부서 확인 후 안내드리겠습니다"로 작성하라.',
        "3. 실제로 인용한 조항의 ID만 cited_clauses 에 넣어라. 참고만 하고 쓰지 않은 조항은 넣지 마라.", "",
        "■ 어조 지침 (sentiment = {})".format(sentiment),
        TONE.get(sentiment, TONE["일반"]),
        LOOKUP_HINT if needs_lookup else "", "",
        "■ 작성 형식",
        "- 인사 → 본문 → 마무리 순서",
        "- 존댓말, 400자 내외",
        "- 정책 조항을 그대로 복사하지 말고 이 고객의 상황에 맞춰 풀어 쓴다",
        "- 조항 ID(RF-01 등)는 본문에 노출하지 않는다",
        '- 서명은 "온마켓 고객센터 드림"',
        '- 고객 이름은 "{}" 이다'.format(name), "",
        "■ 고객 문의", content, "",
        "■ 문의 유형", category, "",
        "■ 정책 근거", retrieved,
    ])


def p4_prompt(content, sentiment, name="김민석"):
    return "\n".join([
        '너는 이커머스 쇼핑몰 "온마켓"의 고객 응대 담당자다.',
        "아래 고객 문의에 대한 답변 이메일 초안을 작성하라.", "",
        "■ 어조 지침 (sentiment = {})".format(sentiment),
        TONE.get(sentiment, TONE["일반"]), "",
        "■ 작성 형식",
        "- 인사 → 본문 → 마무리 순서",
        "- 존댓말, 400자 내외",
        '- 서명은 "온마켓 고객센터 드림"',
        '- 고객 이름은 "{}" 이다'.format(name), "",
        "■ 고객 문의", content,
    ])


# ------------------------------------------------------------------ 수치 검사
UNIT = r"(?:일|원|%|퍼센트|개월|년|시간|시|건|회|장|배|만원|천원)"
RANGE_RE = re.compile(r"(\d[\d,]*)\s*[~∼-]\s*(\d[\d,]*)\s*(" + UNIT + ")")
NUM_RE = re.compile(r"(\d[\d,]*)\s*(" + UNIT + ")")


def _norm(num, unit):
    return num.replace(",", "") + unit.replace("퍼센트", "%")


def numeric_tokens(text):
    """본문의 수치를 '숫자+단위' 토큰으로 뽑는다. 1~3일 은 1일·3일 로 분해한다."""
    text = text or ""
    out = []
    for a, b, unit in RANGE_RE.findall(text):
        out.append(_norm(a, unit))
        out.append(_norm(b, unit))
    for num, unit in NUM_RE.findall(RANGE_RE.sub(" ", text)):
        out.append(_norm(num, unit))
    return out


def grounded_ratio(body, source_text):
    """본문의 수치 토큰 중 근거 텍스트에도 존재하는 비율.

    부분 문자열이 아니라 토큰 집합으로 비교한다. 정책 어딘가에 우연히 같은
    숫자가 있다고 통과시키면 환각을 놓친다.
    """
    toks = numeric_tokens(body)
    if not toks:
        return None, [], []
    src = set(numeric_tokens(source_text))
    ok, bad = [], []
    for t in toks:
        (ok if t in src else bad).append(t)
    return len(ok) / len(toks), ok, bad


def gold_text(case, by_id):
    """해당 문의의 정답 조항 원문. 함정 건은 빈 문자열."""
    ids = [x.strip() for x in (case.get("정답_조항") or "").split(",") if x.strip()]
    return "\n".join(
        "[{}] {} — {}".format(by_id[i]["clause_id"], by_id[i]["title"], by_id[i]["text"])
        for i in ids if i in by_id
    )


# ------------------------------------------------------------------ 측정 실행
def run(limit=None):
    if not API_KEY:
        sys.exit("환경변수 GEMINI_API_KEY 가 필요합니다.")

    clauses = load_clauses()
    by_id = {c["clause_id"]: c for c in clauses}
    embs = clause_embeddings(clauses)
    cases = read_tsv(EVALSET_TSV)
    if limit:
        cases = cases[:limit]
        print("시험 실행 — 앞 {}건만 처리".format(limit))

    os.makedirs(EVAL_DIR, exist_ok=True)
    results = {}
    if os.path.exists(RAW_PATH):
        with open(RAW_PATH, encoding="utf-8") as f:
            results = json.load(f)
        print("이어서 실행 — 완료 {}건".format(len(results)))

    total = len(cases)
    for i, case in enumerate(cases, 1):
        eid = case["eval_id"]
        if eid in results:
            continue
        content = case["문의내용"]
        print("[{}/{}] {} — {}".format(i, total, eid, content[:28]))

        rec = {"eval_id": eid, "문의내용": content}

        # --- RAG 조건
        p1 = generate(p1_prompt(content), P1_SCHEMA)
        rec["p1"] = p1

        qv = embed(p1["search_query"], "RETRIEVAL_QUERY")
        scored = sorted(
            ((cosine(qv, embs[c["clause_id"]]), c) for c in clauses),
            key=lambda x: -x[0],
        )[:3]
        top = [c for _, c in scored]
        retrieved = "\n".join("[{}] {} — {}".format(c["clause_id"], c["title"], c["text"]) for c in top)
        rec["retrieved"] = [c["clause_id"] for c in top]
        rec["scores"] = ["{}:{:.3f}".format(c["clause_id"], s) for s, c in scored]

        rec["rag"] = generate(
            p2_prompt(content, p1["category"], p1["sentiment"], retrieved,
                      needs_lookup=p1.get("needs_order_lookup") is True),
            P2_SCHEMA,
        )

        # --- 베이스라인 조건 (분류는 RAG 것을 재사용해 조건 차이를 프롬프트로 한정)
        rec["base"] = generate(p4_prompt(content, p1["sentiment"]), P4_SCHEMA)

        # 수치 검사는 리포트 단계에서 한다. 지표를 고쳐도 API를 다시 부르지 않기 위해.
        results[eid] = rec
        with open(RAW_PATH, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

    print("\n측정 완료 — {}건".format(len(results)))
    write_review(cases, results, by_id)
    report(cases, results, by_id)


# ------------------------------------------------------------------ 검수표
def write_review(cases, results, by_id):
    """1차 승인률은 사람이 판단해야 한다. 표시할 표를 만든다."""
    head = ["eval_id", "조건", "함정", "문의내용", "초안본문", "인용조항", "insufficient",
            "정답과다른수치", "승인여부(O/X)", "비고"]
    lines = ["\t".join(head)]
    for case in cases:
        r = results.get(case["eval_id"])
        if not r:
            continue
        gold = gold_text(case, by_id)
        is_trap = case["함정여부"].strip().upper() == "TRUE"
        for cond, key in (("RAG", "rag"), ("베이스라인", "base")):
            d = r.get(key, {})
            _, _, bad = grounded_ratio(d.get("body", ""), gold)
            lines.append("\t".join([
                r["eval_id"], cond, "TRUE" if is_trap else "",
                r["문의내용"].replace("\t", " "),
                (d.get("body", "") or "").replace("\t", " ").replace("\n", " "),
                ",".join(d.get("cited_clauses", []) or []),
                str(d.get("insufficient_info", "")),
                ",".join(bad),
                "", "",
            ]))
    with open(REVIEW_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("검수표 작성: {}".format(os.path.relpath(REVIEW_PATH, ROOT)))


def read_review():
    if not os.path.exists(REVIEW_PATH):
        return {}
    out = {}
    for r in read_tsv(REVIEW_PATH):
        v = r.get("승인여부(O/X)", "").strip().upper()
        if v in ("O", "X"):
            out[(r["eval_id"], r["조건"])] = v
    return out


# ------------------------------------------------------------------ 리포트
def pct(n, d):
    return "—" if not d else "{:.1f}% ({}/{})".format(100.0 * n / d, n, d)


def report(cases, results, by_id):
    review = read_review()
    by_case = {c["eval_id"]: c for c in cases}

    cat_ok = sen_ok = look_ok = n_cls = 0
    cite_exact = cite_recall_n = cite_recall_d = 0
    normal = trap = 0
    rag_avoid = 0
    rag_trap_flagged = base_trap_num = rag_trap_num = 0
    rag_ratio_sum = rag_ratio_n = 0.0
    base_ratio_sum = base_ratio_n = 0.0
    rag_retr_sum = rag_retr_n = 0.0
    rag_bad_total = base_bad_total = 0

    rows = []
    for eid, r in sorted(results.items()):
        c = by_case.get(eid)
        if not c:
            continue
        is_trap = c["함정여부"].strip().upper() == "TRUE"
        p1 = r.get("p1_v2") or r.get("p1", {})
        rag = r.get("rag", {})

        n_cls += 1
        if p1.get("category") == c["정답_category"]:
            cat_ok += 1
        if p1.get("sentiment") == c["정답_sentiment"]:
            sen_ok += 1
        if "정답_조회필요" in c:
            gold_look = c["정답_조회필요"].strip().upper() == "TRUE"
            if (p1.get("needs_order_lookup") is True) == gold_look:
                look_ok += 1

        insuf = rag.get("insufficient_info") is True
        cited = set(x.strip() for x in (rag.get("cited_clauses") or []) if x.strip())

        if is_trap:
            trap += 1
            if not insuf:
                rag_trap_flagged += 1
            if numeric_tokens(rag.get("body", "")):
                rag_trap_num += 1
            if numeric_tokens(r.get("base", {}).get("body", "")):
                base_trap_num += 1
        else:
            normal += 1
            gold = set(x.strip() for x in c["정답_조항"].split(",") if x.strip())
            if insuf:
                rag_avoid += 1
            if cited == gold:
                cite_exact += 1
            cite_recall_n += len(cited & gold)
            cite_recall_d += len(gold)

        # 수치 검사는 "이 질문의 정답 조항" 기준으로 한다.
        # 정책 전체와 대조하면 그럴듯한 숫자가 어딘가에 우연히 존재해 환각을 놓친다.
        gold = gold_text(c, by_id)
        rag_bad = base_bad = []
        if not is_trap and gold:
            rr, _, rag_bad = grounded_ratio(rag.get("body", ""), gold)
            if rr is not None:
                rag_ratio_sum += rr
                rag_ratio_n += 1
            br, _, base_bad = grounded_ratio(r.get("base", {}).get("body", ""), gold)
            if br is not None:
                base_ratio_sum += br
                base_ratio_n += 1
        rag_bad_total += len(rag_bad)
        base_bad_total += len(base_bad)

        # 보조 지표: 검색해서 실제로 건네준 조항에 충실했는가
        retr = "\n".join(
            "[{}] {} — {}".format(by_id[i]["clause_id"], by_id[i]["title"], by_id[i]["text"])
            for i in r.get("retrieved", []) if i in by_id
        )
        fr, _, _ = grounded_ratio(rag.get("body", ""), retr)
        if fr is not None:
            rag_retr_sum += fr
            rag_retr_n += 1

        rows.append((eid, c, r, is_trap, insuf, cited, rag_bad))

    ap_rag = [v for (e, cond), v in review.items() if cond == "RAG"]
    ap_base = [v for (e, cond), v in review.items() if cond == "베이스라인"]

    L = []
    L += ["# 평가셋 측정 결과", "",
          "- 평가셋: 50건 (함정 {}건 / 정상 {}건)".format(trap, normal),
          "- 모델: `{}` · 임베딩 `{}` ({}차원)".format(GEN_MODEL, EMBED_MODEL, EMBED_DIM),
          "- 요청 본문은 n8n 워크플로우와 동일", ""]

    two_axis = any("needs_order_lookup" in (r.get("p1_v2") or {}) for r in results.values())
    L += ["## 1. 분류 성능", ""]
    if two_axis:
        L += ["감정과 조회 필요 여부를 **직교하는 두 축**으로 분리해 판정한다. "
              "초기에는 `불만/중립/단순문의` 3단계 하나로 묶었으나, 두 개념을 1차원에 눌러 담은 "
              "설계 오류였다. 경위는 `docs/개발일지.md` 참조.", ""]
    L += ["| 축 | 정확도 |", "|---|---|",
          "| 문의 유형 (6종) | {} |".format(pct(cat_ok, n_cls)),
          "| 감정 ({}) | {} |".format("불만/일반" if two_axis else "3단계", pct(sen_ok, n_cls))]
    if two_axis:
        L.append("| 주문 조회 필요 (T/F) | {} |".format(pct(look_ok, n_cls)))
    L.append("")

    if two_axis:
        for axis, gold_key, get in (
            ("감정", "정답_sentiment", lambda p: p.get("sentiment", "-")),
            ("조회 필요", "정답_조회필요",
             lambda p: "TRUE" if p.get("needs_order_lookup") is True else "FALSE"),
        ):
            L += ["**{} 축 — 정답별 정확도**".format(axis), "",
                  "| 정답 | 정확도 | 판정 분포 |", "|---|---|---|"]
            golds = sorted({x[1][gold_key].strip() for x in rows})
            for g in golds:
                tot = [x for x in rows if x[1][gold_key].strip() == g]
                dist = {}
                for x in tot:
                    p = get(x[2].get("p1_v2") or x[2].get("p1", {}))
                    dist[p] = dist.get(p, 0) + 1
                L.append("| {} | {} | {} |".format(
                    g, pct(dist.get(g, 0), len(tot)),
                    ", ".join("{} {}".format(k, v) for k, v in sorted(dist.items(), key=lambda kv: -kv[1]))))
            L.append("")
        L += ["> 이전 측정 결과는 `eval/측정결과_v1_구정의.md`(3단계 초기 정의)와 "
              "`eval/측정결과_v2_정의개정.md`(3단계 개정 정의)에 보존되어 있다.", ""]

    L += ["## 2. 근거 인용 (정상 {}건)".format(normal), "",
          "| 지표 | 결과 |", "|---|---|",
          "| 인용 조항 완전 일치율 | {} |".format(pct(cite_exact, normal)),
          "| 정답 조항 재현율 | {} |".format(pct(cite_recall_n, cite_recall_d)), ""]

    L += ["## 3. 환각과 회피 — 이 실험의 핵심", "",
          "### 3-1. 수치 정확률 (정상 {}건)".format(normal),
          "",
          "본문에 등장한 수치(일·원·% 등)가 **그 질문의 정답 조항에 실제로 있는 값인지** 검사했다. "
          "정책 문서 전체와 대조하면 그럴듯한 숫자가 어딘가에 우연히 존재해 환각을 놓친다.",
          "",
          "| 조건 | 평균 수치 정확률 | 정답과 다른 수치 총 개수 |", "|---|---|---|",
          "| RAG | {} | {}개 |".format(
              "—" if not rag_ratio_n else "{:.1f}%".format(100 * rag_ratio_sum / rag_ratio_n), rag_bad_total),
          "| 베이스라인 | {} | {}개 |".format(
              "—" if not base_ratio_n else "{:.1f}%".format(100 * base_ratio_sum / base_ratio_n), base_bad_total),
          "",
          "> 베이스라인은 정책을 **받지 못한 상태**에서 답한다. 여기서 맞은 수치는 사전학습에서 온 "
          "일반적 관행이거나 우연이며, 이 회사의 정책이라는 근거가 없다.",
          "",
          "**보조 지표 — 검색 충실도:** RAG 본문의 수치 중 실제로 건네준 검색 조항에 있던 비율 {}. "
          "이 값이 낮으면 프롬프트의 '정책 근거 밖의 수치 금지' 규칙이 지켜지지 않는다는 뜻이다.".format(
              "—" if not rag_retr_n else "**{:.1f}%**".format(100 * rag_retr_sum / rag_retr_n)),
          ""]

    L += ["### 3-2. 함정 {}건 — 정책에 답이 없는 문의".format(trap), "",
          "| 지표 | 결과 |", "|---|---|",
          "| RAG · `insufficient_info=false` 로 답한 건 | {} |".format(pct(rag_trap_flagged, trap)),
          "| RAG · 본문에 수치를 쓴 건 | {} |".format(pct(rag_trap_num, trap)),
          "| 베이스라인 · 본문에 수치를 쓴 건 | {} |".format(pct(base_trap_num, trap)),
          "",
          "> 플래그만으로는 부족하다. 플래그를 `true` 로 두고도 본문에서 사실을 창작한 사례가 "
          "모델 비교 실험에서 확인됐다. **최종 환각 판정은 검수표의 본문을 보고 사람이 확정한다.**",
          ""]

    L += ["### 3-3. 과도한 회피 (정상 {}건)".format(normal), "",
          "| 지표 | 결과 |", "|---|---|",
          "| 정책으로 답할 수 있는데 회피한 건 | {} |".format(pct(rag_avoid, normal)),
          "",
          "> 환각률과 함께 봐야 한다. 환각률만 재면 **아무것도 답하지 않는 모델이 만점**을 받는다.",
          ""]

    L += ["## 4. 1차 승인률 (사람 판정)", ""]
    if not review:
        L += ["아직 검수 전이다. `eval/측정_검수표.tsv` 의 `승인여부(O/X)` 를 채운 뒤",
              "`python scripts/run_eval.py --score` 를 실행하면 이 항목이 채워진다.", ""]
    else:
        L += ["| 조건 | 1차 승인률 |", "|---|---|",
              "| RAG | {} |".format(pct(ap_rag.count("O"), len(ap_rag))),
              "| 베이스라인 | {} |".format(pct(ap_base.count("O"), len(ap_base))), ""]

    L += ["## 5. 케이스별 상세", "",
          "| ID | 유형 | 정답/판정 | 감정 | 정답 조항 | 인용 조항 | insuf | 정답과다른수치 |",
          "|---|---|---|---|---|---|---|---|"]
    for eid, c, r, is_trap, insuf, cited, rag_bad in rows:
        p1 = r.get("p1_v2") or r.get("p1", {})
        mark = "" if p1.get("category") == c["정답_category"] else " ⚠"
        bad = ",".join(rag_bad) or "-"
        L.append("| {} | {}{} | {} → {} | {} → {} | {} | {} | {} | {} |".format(
            eid, "함정" if is_trap else "정상", mark,
            c["정답_category"], p1.get("category", "-"),
            c["정답_sentiment"], p1.get("sentiment", "-"),
            c["정답_조항"] or "-", ",".join(sorted(cited)) or "-",
            "T" if insuf else "F", bad))
    L.append("")

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print("리포트 작성: {}".format(os.path.relpath(REPORT_PATH, ROOT)))


def reclassify():
    """P1 분류만 다시 돌린다. 감정 라벨 정의를 개정했을 때 사용.

    결과는 p1_v2 에 저장하고 기존 p1 은 남겨둔다. 초안(rag/base)은 건드리지 않으므로
    호출은 건당 1회, 총 50회로 끝난다.
    """
    if not API_KEY:
        sys.exit("환경변수 GEMINI_API_KEY 가 필요합니다.")
    with open(RAW_PATH, encoding="utf-8") as f:
        results = json.load(f)
    cases = read_tsv(EVALSET_TSV)

    todo = [c for c in cases if c["eval_id"] in results and "p1_v2" not in results[c["eval_id"]]]
    print("재분류 대상 {}건".format(len(todo)))
    for i, c in enumerate(todo, 1):
        eid = c["eval_id"]
        print("[{}/{}] {}".format(i, len(todo), eid))
        results[eid]["p1_v2"] = generate(p1_prompt(c["문의내용"]), P1_SCHEMA)
        with open(RAW_PATH, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

    clauses = load_clauses()
    by_id = {c["clause_id"]: c for c in clauses}
    write_review(cases, results, by_id)
    report(cases, results, by_id)


def score_only():
    with open(RAW_PATH, encoding="utf-8") as f:
        results = json.load(f)
    cases = read_tsv(EVALSET_TSV)
    clauses = load_clauses()
    report(cases, results, {c["clause_id"]: c for c in clauses})


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--score", action="store_true", help="검수표를 반영해 리포트만 다시 생성")
    ap.add_argument("--limit", type=int, default=None, help="앞 N건만 시험 실행")
    ap.add_argument("--reclassify", action="store_true", help="P1 분류만 다시 실행 (감정 정의 개정 후)")
    args = ap.parse_args()
    if args.reclassify:
        reclassify()
    elif args.score:
        score_only()
    else:
        run(args.limit)
