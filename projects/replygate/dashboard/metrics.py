# -*- coding: utf-8 -*-
"""지표 집계.

두 종류를 다룬다.

- **운영 지표** — `문의` 시트에서 실시간으로 집계. 지금 파이프라인이 어떻게 돌고 있는가.
- **실험 결과** — `eval/측정_검수표.tsv` 에서 집계. RAG가 실제로 효과가 있었는가.

실험 결과를 대시보드에 함께 올리는 이유는 발표 시나리오 때문이다. 데모로 파이프라인을
보여준 뒤 "그래서 이게 효과가 있느냐"로 마무리하는데, 그 답이 다른 화면에 있으면 흐름이 끊긴다.
"""

import csv
import io
import os

from sheets import parse_ts, now_kst

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REVIEW_PATH = os.path.join(ROOT, "eval", "측정_검수표.tsv")

STATUS_ORDER = ["접수됨", "분석중", "승인대기", "수정중", "발송완료", "처리실패"]
CATEGORY_ORDER = ["환불", "배송", "교환반품", "불량AS", "회원적립금", "기타"]

# 아직 담당자 손을 떠나지 않은 상태. 상황판 상단에 남는다.
ACTIVE_STATUS = ["접수됨", "분석중", "승인대기", "수정중"]


def _truthy(v):
    return str(v).strip().upper() in ("TRUE", "T", "1", "Y", "YES")


def _int(v, default=0):
    try:
        return int(float(str(v).strip()))
    except (TypeError, ValueError):
        return default


def _pct(n, d):
    return round(100.0 * n / d, 1) if d else None


# ------------------------------------------------------------------ 운영 지표
def operational(rows):
    total = len(rows)

    status_counts = {s: 0 for s in STATUS_ORDER}
    category_counts = {c: 0 for c in CATEGORY_ORDER}
    sentiment_counts = {"불만": 0, "일반": 0}
    lookup_true = lookup_known = 0
    insufficient = 0
    clause_freq = {}

    sent_rows = []
    for r in rows:
        st = r.get("status", "").strip()
        if st in status_counts:
            status_counts[st] += 1
        elif st:
            status_counts.setdefault(st, 0)
            status_counts[st] += 1

        cat = r.get("category", "").strip()
        if cat:
            category_counts.setdefault(cat, 0)
            category_counts[cat] += 1

        sen = r.get("sentiment", "").strip()
        if sen:
            sentiment_counts.setdefault(sen, 0)
            sentiment_counts[sen] += 1

        # needs_lookup 은 선택 컬럼이다. 시트에 없으면 집계에서 통째로 빠진다.
        if "needs_lookup" in r and str(r.get("needs_lookup", "")).strip():
            lookup_known += 1
            if _truthy(r["needs_lookup"]):
                lookup_true += 1

        if _truthy(r.get("insufficient_info", "")):
            insufficient += 1

        for cid in [c.strip() for c in r.get("cited_clauses", "").split(",") if c.strip()]:
            clause_freq[cid] = clause_freq.get(cid, 0) + 1

        if st == "발송완료":
            sent_rows.append(r)

    # 1차 승인률 — 발송된 건 중 수정 0회로 나간 비율. 이 시스템의 주 지표다.
    sent_n = len(sent_rows)
    first_pass = sum(1 for r in sent_rows if _int(r.get("revision_count", 0)) == 0)

    # 평균 수정 횟수
    rev_values = [_int(r.get("revision_count", 0)) for r in sent_rows]
    avg_rev = round(sum(rev_values) / len(rev_values), 2) if rev_values else None

    # 평균 처리 시간 (접수 → 발송). 파싱 실패한 건은 제외한다.
    durations = []
    for r in sent_rows:
        t0 = parse_ts(r.get("타임스탬프", ""))
        t1 = parse_ts(r.get("sent_at", "")) or parse_ts(r.get("status_at", ""))
        if t0 and t1 and t1 >= t0:
            durations.append((t1 - t0).total_seconds())
    avg_sec = round(sum(durations) / len(durations)) if durations else None

    active = sum(status_counts.get(s, 0) for s in ACTIVE_STATUS)

    top_clauses = sorted(clause_freq.items(), key=lambda kv: (-kv[1], kv[0]))[:8]

    return {
        "total": total,
        "active": active,
        "sent": sent_n,
        "first_pass_rate": _pct(first_pass, sent_n),
        "first_pass_n": first_pass,
        "avg_revisions": avg_rev,
        "avg_seconds": avg_sec,
        "avg_seconds_n": len(durations),
        "status": [{"name": s, "count": status_counts.get(s, 0)} for s in STATUS_ORDER
                   if s in status_counts],
        "category": [{"name": c, "count": n} for c, n in
                     sorted(category_counts.items(), key=lambda kv: (-kv[1], kv[0])) if n or c in CATEGORY_ORDER],
        "sentiment": [{"name": s, "count": n} for s, n in sentiment_counts.items()],
        "needs_lookup": ({"true": lookup_true, "known": lookup_known}
                         if lookup_known else None),
        "insufficient": insufficient,
        "top_clauses": [{"id": c, "count": n} for c, n in top_clauses],
    }


# ------------------------------------------------------------------ 상황판
def board(rows, limit=40):
    """상황판 카드 목록. 방금 움직인 건이 위로 온다."""
    cards = []
    now = now_kst()
    for r in rows:
        iid = r.get("inquiry_id", "").strip()
        if not iid:
            continue                                 # 아직 n8n 이 집어가지 않은 행
        moved = parse_ts(r.get("status_at", "")) or parse_ts(r.get("타임스탬프", ""))
        received = parse_ts(r.get("타임스탬프", ""))
        cards.append({
            "inquiry_id": iid,
            "name": r.get("이름", "").strip(),
            "category": r.get("category", "").strip(),
            "sentiment": r.get("sentiment", "").strip(),
            "needs_lookup": _truthy(r.get("needs_lookup", "")) if r.get("needs_lookup") else False,
            "insufficient": _truthy(r.get("insufficient_info", "")),
            "summary": r.get("summary", "").strip(),
            "status": r.get("status", "").strip() or "접수됨",
            "revisions": _int(r.get("revision_count", 0)),
            "cited": [c.strip() for c in r.get("cited_clauses", "").split(",") if c.strip()],
            "moved_at": moved.isoformat() if moved else None,
            "age_seconds": int((now - moved).total_seconds()) if moved else None,

            # 상세 보기용 원문. 요약은 핵심을 고르지만 판단에는 원문이 필요할 때가 있다.
            # 이메일 등 고객 정보도 담당자 화면이므로 그대로 싣는다.
            # 무대 투사 대비는 화면의 "발표 모드" 토글로 가린다.
            "content": r.get("문의내용", "").strip(),
            "email": r.get("이메일", "").strip(),
            "order_no": r.get("주문번호", "").strip(),
            "consent": r.get("개인정보 수집 동의", "").strip(),
            "search_query": r.get("search_query", "").strip(),
            "body": r.get("final_body", "").strip(),
            "handler_note": r.get("handler_note", "").strip(),
            "draft_id": r.get("draft_id", "").strip(),
            "received_at": received.isoformat() if received else None,
            "sent_at": (parse_ts(r.get("sent_at", "")).isoformat()
                        if parse_ts(r.get("sent_at", "")) else None),
        })

    # status_at 이 없는 건은 뒤로 보낸다.
    cards.sort(key=lambda c: (c["moved_at"] is None, c["moved_at"] or ""), reverse=True)
    # reverse=True 로 정렬하면 None 그룹이 앞으로 오므로 다시 갈라 붙인다.
    dated = [c for c in cards if c["moved_at"]]
    undated = [c for c in cards if not c["moved_at"]]
    dated.sort(key=lambda c: c["moved_at"], reverse=True)
    return (dated + undated)[:limit]


# ------------------------------------------------------------------ 실험 결과
_experiment_cache = {"mtime": None, "data": None}


def experiment():
    """평가셋 측정의 결론을 읽어온다.

    `eval/측정_검수표.tsv` 하나만 본다. 승인 판정과 수치 오류가 모두 이 파일에 있어
    run_eval.py 의 채점 로직을 대시보드에 복제하지 않아도 된다.
    파일이 없으면 None 을 돌려주고 화면에서 해당 패널을 숨긴다.
    """
    if not os.path.exists(REVIEW_PATH):
        return None

    mtime = os.path.getmtime(REVIEW_PATH)
    if _experiment_cache["mtime"] == mtime:
        return _experiment_cache["data"]

    with io.open(REVIEW_PATH, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))

    conds = {}
    for cond in ("RAG", "베이스라인"):
        sub = [r for r in rows if (r.get("조건") or "").strip() == cond]
        if not sub:
            continue
        judged = [r for r in sub if (r.get("승인여부(O/X)") or "").strip().upper() in ("O", "X")]
        approved = [r for r in judged if (r.get("승인여부(O/X)") or "").strip().upper() == "O"]

        traps = [r for r in sub if (r.get("함정") or "").strip().upper() == "TRUE"]
        trap_clean = [r for r in traps if not (r.get("정답과다른수치") or "").strip()]

        # `정답과다른수치` 는 쉼표로 구분된 값 목록이다. 건수와 값 개수를 따로 센다.
        # **함정 문항은 제외한다** — 정답 조항이 없어 대조 기준이 다르다.
        # eval/측정결과.md 의 "수치 정확률(정상 45건)" 과 같은 모집단이어야
        # 무대에서 두 화면의 숫자가 어긋나지 않는다.
        normal = [r for r in sub if (r.get("함정") or "").strip().upper() != "TRUE"]
        bad_rows = [r for r in normal if (r.get("정답과다른수치") or "").strip()]
        bad_values = sum(len([v for v in (r.get("정답과다른수치") or "").split(",") if v.strip()])
                         for r in bad_rows)

        conds[cond] = {
            "total": len(sub),
            "judged": len(judged),
            "approved": len(approved),
            "approval_rate": _pct(len(approved), len(judged)),
            "normal_total": len(normal),
            "bad_number_rows": len(bad_rows),
            "bad_number_values": bad_values,
            "trap_total": len(traps),
            "trap_no_number": len(trap_clean),
        }

    if not conds.get("RAG") or not conds["RAG"]["judged"]:
        return None

    # 1차 승인률이 수치 정확률의 재탕이 아니라는 근거. 발표에서 쓰는 숫자다.
    x_rows = [r for r in rows if (r.get("승인여부(O/X)") or "").strip().upper() == "X"]
    x_without_number = sum(1 for r in x_rows if not (r.get("정답과다른수치") or "").strip())

    data = {
        "conditions": conds,
        "x_total": len(x_rows),
        "x_without_number": x_without_number,
        "source": "eval/측정_검수표.tsv",
    }
    _experiment_cache.update({"mtime": mtime, "data": data})
    return data
