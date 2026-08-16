/* ReplyGate 대시보드 프런트.
   SSE 로 스냅샷을 받아 화면을 갱신한다. 라이브러리는 쓰지 않는다.
   SSE 가 끊기면 폴링으로 자동 강등되고, 복구되면 다시 SSE 로 올라간다.

   **DOM 을 통째로 갈아끼우지 않는다.** 카드마다 inquiry_id 로 요소를 재사용하고
   내용이 실제로 달라진 것만 고친다. 매번 innerHTML 을 새로 쓰면 등장 애니메이션이
   다시 재생돼 화면이 깜박이고, CSS transition 도 동작하지 않는다. */

const STATUS_COLS = ['접수됨', '분석중', '승인대기', '수정중', '발송완료'];

const $ = (id) => document.getElementById(id);
const esc = (s) => String(s == null ? '' : s)
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

/* 내용이 같으면 건드리지 않는다. 이 한 줄이 깜박임의 대부분을 없앤다. */
function setHTML(el, html) {
  if (el && el.dataset.h !== html) { el.innerHTML = html; el.dataset.h = html; }
}

/* ─────────────────────────── 표시 헬퍼 ─────────────────────────── */

function fmtDuration(sec) {
  if (sec == null) return '—';
  if (sec < 60) return sec + '초';
  const m = Math.floor(sec / 60);
  if (m < 60) return m + '분';
  const h = Math.floor(m / 60);
  return h + '시간 ' + (m % 60) + '분';
}

function fmtAge(sec) {
  if (sec == null) return '';
  if (sec < 60) return '방금';
  const m = Math.floor(sec / 60);
  if (m < 60) return m + '분 전';
  const h = Math.floor(m / 60);
  if (h < 24) return h + '시간 전';
  return Math.floor(h / 24) + '일 전';
}

function pct(v) { return v == null ? '—' : v.toFixed(1) + '%'; }

/* 텔레그램 카드와 같은 배지를 쓴다. 두 화면의 표기가 다르면 담당자가 헷갈린다. */
function badges(t) {
  const out = [t.sentiment === '불만' ? '🔴' : '⚪'];
  if (t.insufficient) out.push('⚠️');
  if (t.needs_lookup) out.push('📋');
  return out.join('');
}

/* ─────────────────────────── 상황판 ─────────────────────────── */

const cols = {};                       // status -> {list, count, empty}
const tickets = new Map();             // inquiry_id -> element

function ensureColumns(names) {
  const boardEl = $('board');
  const sig = names.join('|');
  if (boardEl.dataset.sig === sig) return;

  boardEl.dataset.sig = sig;
  boardEl.style.gridTemplateColumns = `repeat(${names.length}, minmax(210px, 1fr))`;
  boardEl.innerHTML = names.map((s) => `
    <div class="col" data-status="${esc(s)}">
      <div class="col-head"><span>${esc(s)}</span><span class="col-count">0</span></div>
      <div class="col-list"></div>
      <div class="empty">비어 있음</div>
    </div>`).join('');

  tickets.clear();
  Object.keys(cols).forEach((k) => delete cols[k]);
  Array.from(boardEl.children).forEach((colEl, i) => {
    cols[names[i]] = {
      list: colEl.querySelector('.col-list'),
      count: colEl.querySelector('.col-count'),
      empty: colEl.querySelector('.empty'),
    };
  });
}

function ticketInner(t) {
  const rev = t.revisions > 0 ? `<span class="t-rev">수정 ${t.revisions}회</span>` : '<span></span>';
  // 조항 ID는 각각 눌러서 원문을 볼 수 있다. 근거를 표시하는 이유가 검증이라서다.
  const cited = (t.cited || []).length
    ? '<div style="margin-bottom:6px">📎 ' + t.cited.map((c) =>
        `<button class="chip" data-clause="${esc(c)}" data-id="${esc(t.inquiry_id)}">${esc(c)}</button>`
      ).join('') + '</div>'
    : '';
  return `<div class="t-top">
      <span>${badges(t)}</span>
      ${t.category ? `<span class="t-cat">[${esc(t.category)}]</span>` : ''}
      <span class="t-name">${esc(t.name)}</span>
    </div>
    <div class="t-sum">${esc(t.summary || '분석 대기 중…')}</div>
    ${cited}
    <div class="t-foot">
      <span class="t-id">${esc(t.inquiry_id)}</span>
      ${rev}
      <span class="t-age"></span>
    </div>`;
}

function renderBoard(cards) {
  const grouped = {};
  STATUS_COLS.forEach((s) => { grouped[s] = []; });
  const extra = [];
  cards.forEach((c) => {
    if (grouped[c.status]) grouped[c.status].push(c);
    else extra.push(c);                        // 처리실패 등 예외 상태
  });

  const names = STATUS_COLS.slice();
  if (extra.length) { grouped['처리실패'] = extra; names.push('처리실패'); }
  ensureColumns(names);

  const seen = new Set();

  names.forEach((status) => {
    const col = cols[status];
    const list = grouped[status] || [];
    col.count.textContent = list.length;
    col.empty.hidden = list.length > 0;

    list.forEach((t, idx) => {
      seen.add(t.inquiry_id);
      let el = tickets.get(t.inquiry_id);

      if (!el) {                               // 새 문의 — 이때만 등장 애니메이션
        el = document.createElement('div');
        el.className = 'ticket';
        tickets.set(t.inquiry_id, el);
      }

      setHTML(el, ticketInner(t));
      el.dataset.status = t.status;
      el.dataset.movedAt = t.moved_at || '';
      paintAge(el);

      // 상태가 바뀌어 다른 컬럼으로 옮겨온 경우에만 강조한다.
      if (el.parentElement !== col.list) {
        const moving = el.parentElement !== null;
        col.list.appendChild(el);
        if (moving) {
          el.classList.remove('moved');
          void el.offsetWidth;                 // 애니메이션 재시작
          el.classList.add('moved');
        }
      } else if (col.list.children[idx] !== el) {
        col.list.insertBefore(el, col.list.children[idx] || null);
      }
    });
  });

  tickets.forEach((el, id) => {                // 시트에서 사라진 행 정리
    if (!seen.has(id)) { el.remove(); tickets.delete(id); }
  });
}

/* 경과 시간은 서버가 아니라 브라우저가 계산한다.
   서버가 매초 밀어주게 하면 그 자체가 깜박임의 원인이 된다. */
function paintAge(el) {
  const iso = el.dataset.movedAt;
  const span = el.querySelector('.t-age');
  if (!span) return;
  if (!iso) { span.textContent = ''; return; }
  const sec = Math.max(0, Math.floor((Date.now() - new Date(iso).getTime()) / 1000));
  const txt = fmtAge(sec);
  if (span.textContent !== txt) span.textContent = txt;
}

setInterval(() => tickets.forEach(paintAge), 20000);

/* ─────────────────────────── 운영 지표 ─────────────────────────── */

function kpi(label, value, unit, sub, hero) {
  return `<div class="kpi${hero ? ' hero' : ''}">
    <div class="kpi-label">${esc(label)}</div>
    <div class="kpi-value">${esc(value)}${unit ? `<span class="unit">${esc(unit)}</span>` : ''}</div>
    ${sub ? `<div class="kpi-sub">${esc(sub)}</div>` : ''}
  </div>`;
}

function renderKpis(op) {
  setHTML($('kpis'), [
    kpi('총 문의', op.total, '건'),
    kpi('진행 중', op.active, '건', '승인 전 단계'),
    kpi('1차 승인률', pct(op.first_pass_rate), '',
        op.sent ? `수정 0회 ${op.first_pass_n} / 발송 ${op.sent}` : '발송 건 없음', true),
    kpi('평균 처리 시간', fmtDuration(op.avg_seconds), '',
        op.avg_seconds_n ? `발송 ${op.avg_seconds_n}건 기준` : '발송 건 없음'),
    // 값이 없을 때 단위를 붙이면 "—회" 가 된다. 단위는 값이 있을 때만.
    kpi('평균 수정 횟수', op.avg_revisions == null ? '—' : op.avg_revisions,
        op.avg_revisions == null ? '' : '회'),
    kpi('정책 미커버', op.insufficient, '건', 'insufficient_info'),
  ].join(''));
}

function bars(items, color) {
  const max = Math.max(1, ...items.map((i) => i.count));
  if (!items.length) return '<div class="empty">데이터 없음</div>';
  return '<div class="bars">' + items.map((i) => `
    <div class="bar-row">
      <span class="bar-name" title="${esc(i.name)}">${esc(i.name)}</span>
      <span class="bar-track">
        <span class="bar-fill" style="width:${(i.count / max * 100).toFixed(1)}%${
          color ? `;background:${color}` : ''}"></span>
      </span>
      <span class="bar-val">${i.count}</span>
    </div>`).join('') + '</div>';
}

function renderCharts(op) {
  setHTML($('chart-category'), bars(op.category.filter((c) => c.count > 0)));

  /* 감정과 조회 필요는 직교하는 두 축이다. 한 카드 안에 나란히 두어
     "하나의 3단계 분류가 아니다"가 화면에서도 드러나게 한다. */
  const axes = [];
  op.sentiment.forEach((s) => { if (s.count) axes.push({ name: '감정 · ' + s.name, count: s.count }); });
  if (op.needs_lookup) {
    axes.push({ name: '조회필요 · 예', count: op.needs_lookup.true });
    axes.push({ name: '조회필요 · 아니오', count: op.needs_lookup.known - op.needs_lookup.true });
  }
  setHTML($('chart-axes'), axes.length ? bars(axes, 'var(--purple)')
                                       : '<div class="empty">데이터 없음</div>');

  setHTML($('chart-clauses'),
          bars(op.top_clauses.map((c) => ({ name: c.id, count: c.count })), 'var(--ok)'));
}

/* ─────────────────────────── 실험 결과 ─────────────────────────── */

function renderExperiment(exp) {
  const panel = $('exp-panel');
  const rag = exp && exp.conditions && exp.conditions['RAG'];
  if (!rag) { panel.hidden = true; return; }
  panel.hidden = false;

  const base = exp.conditions['베이스라인'];

  const row = (cls, label, c) => `
    <div class="vs-row ${cls}">
      <div class="vs-head">
        <span class="vs-label">${esc(label)}</span>
        <span class="vs-num">${pct(c.approval_rate)}</span>
      </div>
      <div class="vs-track"><div class="vs-fill" style="width:${c.approval_rate || 0}%"></div></div>
      <div class="vs-note">수정 없이 발송 가능 ${c.approved} / ${c.judged}건</div>
    </div>`;

  const gap = base && rag.approval_rate != null && base.approval_rate != null
    ? (rag.approval_rate - base.approval_rate).toFixed(1) : null;

  const left = `<div class="card">
    <h3>1차 승인률 — 주 지표</h3>
    <div class="versus">
      ${row('vs-rag', 'RAG 적용', rag)}
      ${base ? row('vs-base', '베이스라인 (정책 없음)', base) : ''}
    </div>
    ${gap ? `<div class="callout" style="margin-top:14px">
      정책 문서를 근거로 주자 승인 가능한 초안이 <strong>${gap}%p</strong> 늘었다.
    </div>` : ''}
  </div>`;

  const right = `<div class="card">
    <h3>정답과 다른 수치 <span style="font-weight:400;opacity:.7">· 정상 ${rag.normal_total}건</span></h3>
    <div class="stat-line"><span class="k">RAG</span>
      <span class="v">${rag.bad_number_rows}건 · ${rag.bad_number_values}개</span></div>
    ${base ? `<div class="stat-line"><span class="k">베이스라인</span>
      <span class="v">${base.bad_number_rows}건 · ${base.bad_number_values}개</span></div>` : ''}
    <div class="stat-line"><span class="k">함정 ${rag.trap_total}건 · 수치 창작 없음</span>
      <span class="v">RAG ${rag.trap_no_number} / 베이스라인 ${base ? base.trap_no_number : '—'}</span></div>

    <div class="callout" style="margin-top:14px">
      승인 판정 <strong>X ${exp.x_total}건 중 ${exp.x_without_number}건</strong>은
      수치 오류가 아닌 사유였다 — 근거 없는 확약, 원인 창작, 정책 정면 위반.
      <strong>1차 승인률은 수치 정확률의 재탕이 아니다.</strong>
    </div>
  </div>`;

  setHTML($('experiment'), `<div class="exp-grid">${left}${right}</div>`);
}

/* ─────────────────────────── 연결 상태 ─────────────────────────── */

function setConn(cls, text) {
  const dot = $('conn-dot'), t = $('conn-text');
  if (dot.className !== 'dot ' + cls) dot.className = 'dot ' + cls;
  if (t.textContent !== text) t.textContent = text;
}

function renderSource(src) {
  const banner = $('banner');

  if (src.config_error) {
    setConn('down', '설정 필요');
    banner.hidden = false; banner.className = 'banner';
    if (banner.textContent !== src.config_error) banner.textContent = src.config_error;
    return;
  }

  if (!src.ok) {
    setConn('down', '시트 조회 실패');
    const msg = '시트를 읽지 못했습니다. 화면은 마지막으로 성공한 값으로 유지됩니다 — ' + (src.error || '');
    banner.hidden = false; banner.className = 'banner';
    if (banner.textContent !== msg) banner.textContent = msg;
    return;
  }

  banner.hidden = true;
  const stale = src.stale_seconds;
  if (stale != null && stale > 15) setConn('stale', '갱신 지연 ' + fmtAge(stale));
  else setConn('live', '실시간');
}

/* ─────────────────────────── 상세 보기 ───────────────────────────
   요약은 대체로 핵심을 고르지만, 판단하려면 원문이 필요할 때가 있다.
   근거 조항은 특히 그렇다 — 원문을 봐야 인용이 맞는지 검증된다. */

const cards = new Map();               // inquiry_id -> 최신 카드 데이터
let clauseBook = {};                   // clause_id -> {doc, title, text}
let openId = null;                     // 열려 있는 상세의 inquiry_id
let focusClause = null;                // 강조할 조항 (조항 칩으로 열었을 때)

/* 발표 모드 — 화면을 투사할 때 개인정보만 가린다. 기본은 꺼짐(그대로 표시). */
const maskOn = () => $('mask-pii').checked;

function maskPII(v) {
  if (!v) return v;
  if (!maskOn()) return v;
  const at = v.indexOf('@');
  if (at > 0) return v.slice(0, Math.min(2, at)) + '•'.repeat(6) + v.slice(at);
  return v.slice(0, 1) + '•'.repeat(Math.max(2, v.length - 1));
}

$('mask-pii').checked = localStorage.getItem('rg-mask') === '1';
$('mask-pii').addEventListener('change', () => {
  localStorage.setItem('rg-mask', maskOn() ? '1' : '0');
  if (openId) paintDetail();
});

async function loadClauses() {
  try {
    const r = await fetch('/api/clauses');
    clauseBook = (await r.json()).clauses || {};
    if (openId) paintDetail();         // 열려 있으면 즉시 채운다
  } catch (e) { /* 없으면 상세에서 "원문을 불러오지 못했다"로 표시된다 */ }
}

function fmtWhen(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleString('ko-KR', { month: 'numeric', day: 'numeric',
                                     hour: '2-digit', minute: '2-digit' });
}

function sec(title, bodyHTML, quiet) {
  return `<div class="sec"><div class="sec-h">${esc(title)}</div>
    <div class="sec-body${quiet ? ' quiet' : ''}">${bodyHTML}</div></div>`;
}

function clauseBlock(id) {
  const c = clauseBook[id];
  const focus = id === focusClause ? ' focus' : '';
  if (!c) {
    return `<div class="clause missing${focus}">
      <div class="clause-h"><span class="clause-id">${esc(id)}</span></div>
      <div class="clause-text">조항 원문을 불러오지 못했습니다. <code>조항</code> 시트를 확인하세요.</div>
    </div>`;
  }
  return `<div class="clause${focus}">
    <div class="clause-h">
      <span class="clause-id">${esc(id)}</span>
      <span>${esc(c.title)}</span>
      <span class="clause-doc">${esc(c.doc)}</span>
    </div>
    <div class="clause-text">${esc(c.text)}</div>
  </div>`;
}

function paintDetail() {
  const t = cards.get(openId);
  if (!t) return;

  setHTML($('detail-title'), `
    <div class="d-title">${badges(t)} ${t.category ? `[${esc(t.category)}] ` : ''}${esc(t.name)}</div>
    <div class="d-meta">${esc(t.inquiry_id)} · ${esc(t.status)}${
      t.revisions ? ` · 수정 ${t.revisions}회` : ''} · 접수 ${esc(fmtWhen(t.received_at))}</div>`);

  const factRow = (pairs) => pairs
    .map(([k, v]) => `<div class="fact"><b>${esc(k)}</b>${esc(v)}</div>`).join('');

  const customer = factRow([
    ['이름', t.name || '—'],
    ['이메일', maskPII(t.email) || '—'],
    ['주문번호', t.order_no || '미입력'],
    ['개인정보 동의', t.consent ? '있음' : '—'],
  ]);

  const analysis = factRow([
    ['유형', t.category || '—'],
    ['감정', t.sentiment || '—'],
    ['주문 조회 필요', t.needs_lookup ? '예' : '아니오'],
    ['정책 미커버', t.insufficient ? '예' : '아니오'],
  ]);

  const history = factRow([
    ['접수', fmtWhen(t.received_at)],
    ['최근 상태 변경', fmtWhen(t.moved_at)],
    ['발송', t.sent_at ? fmtWhen(t.sent_at) : '—'],
    ['수정 횟수', String(t.revisions)],
  ]);

  const parts = [
    `<div class="sec"><div class="sec-h">고객 정보</div><div class="facts">${customer}</div></div>`,
    sec('고객 문의 원문', esc(t.content || '(원문이 비어 있습니다)'), !t.content),
    `<div class="sec"><div class="sec-h">AI 분석</div><div class="facts">${analysis}</div></div>`,
  ];

  if (t.search_query) {
    parts.push(sec('정책 검색에 쓴 문장', esc(t.search_query)));
  }

  parts.push(sec('AI 초안' + (t.status === '발송완료' ? ' (발송된 본문)' : ''),
                 esc(t.body || '아직 생성되지 않았습니다.'), !t.body));

  if (t.handler_note) {
    parts.push(sec('담당자 수정 지시', esc(t.handler_note)));
  }

  parts.push(`<div class="sec"><div class="sec-h">근거 조항 ${
    (t.cited || []).length ? `(${t.cited.length}개)` : ''}</div>${
    (t.cited || []).length
      ? t.cited.map(clauseBlock).join('')
      : '<div class="sec-body quiet">인용된 조항이 없습니다. 정책으로 답할 수 없는 문의였을 수 있습니다.</div>'
  }</div>`);

  parts.push(`<div class="sec"><div class="sec-h">처리 이력</div><div class="facts">${history}</div></div>`);

  parts.push(`<div class="privacy-note">Gmail 초안 ID <code>${esc(t.draft_id || '—')}</code>${
    maskOn() ? ' · 발표 모드가 켜져 있어 개인정보가 가려져 있습니다' : ''}</div>`);

  setHTML($('detail-body'), parts.join(''));
}

function openDetail(id, clause) {
  if (!cards.has(id)) return;
  openId = id;
  focusClause = clause || null;
  $('overlay').hidden = false;
  paintDetail();
  if (clause) {
    const el = $('detail-body').querySelector('.clause.focus');
    if (el) el.scrollIntoView({ block: 'center' });
  }
}

function closeDetail() {
  openId = null; focusClause = null;
  $('overlay').hidden = true;
}

$('board').addEventListener('click', (e) => {
  const chip = e.target.closest('[data-clause]');
  if (chip) { openDetail(chip.dataset.id, chip.dataset.clause); return; }
  const card = e.target.closest('.ticket');
  if (card) {
    const id = card.querySelector('.t-id')?.textContent.trim();
    if (id) openDetail(id, null);
  }
});

$('detail-close').addEventListener('click', closeDetail);
$('overlay').addEventListener('click', (e) => { if (e.target === $('overlay')) closeDetail(); });
document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && openId) closeDetail(); });

/* ─────────────────────────── 렌더 진입점 ─────────────────────────── */

function render(p) {
  renderSource(p.source);

  cards.clear();
  (p.board || []).forEach((c) => cards.set(c.inquiry_id, c));
  // 상세를 열어둔 채 상태가 바뀌면 내용도 같이 갱신된다.
  if (openId) { if (cards.has(openId)) paintDetail(); else closeDetail(); }

  renderBoard(p.board || []);
  renderKpis(p.operational);
  renderCharts(p.operational);
  renderExperiment(p.experiment);
  $('served').textContent = '마지막 갱신 ' +
    new Date(p.served_at).toLocaleTimeString('ko-KR');
}

/* ─────────────────────────── 수신 ─────────────────────────── */

let pollTimer = null;

function startPolling() {
  if (pollTimer) return;
  const tick = async () => {
    try {
      const [m, b] = await Promise.all([
        fetch('/api/metrics').then((r) => r.json()),
        fetch('/api/board').then((r) => r.json()),
      ]);
      render({ ...m, board: b.board, served_at: new Date().toISOString() });
    } catch (e) {
      setConn('down', '서버 연결 끊김');
    }
  };
  tick();
  pollTimer = setInterval(tick, 3000);
}

function stopPolling() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
}

function connect() {
  const es = new EventSource('/api/stream');

  es.addEventListener('snapshot', (ev) => {
    stopPolling();                       // SSE 가 살아 있으면 폴링은 멈춘다
    try { render(JSON.parse(ev.data)); } catch (e) { /* 다음 스냅샷에서 복구된다 */ }
  });

  es.onerror = () => {
    // EventSource 는 스스로 재연결한다. 그동안은 폴링으로 화면을 살려둔다.
    setConn('stale', '재연결 중…');
    startPolling();
  };
}

connect();
loadClauses();
