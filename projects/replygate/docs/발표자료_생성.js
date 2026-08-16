// ReplyGate 발표 슬라이드 생성기
//
// 실행: node 발표자료_생성.js <출력경로.pptx>   (npm i pptxgenjs 필요)
//
// ⚠️ PowerPoint 에서 슬라이드를 직접 손대기 시작하면 그때부터는 .pptx 가 원본이다.
//    이 스크립트를 다시 돌리면 손댄 내용이 사라진다. 큰 구조를 바꿀 때만 여기를 고칠 것.
// 팔레트는 프로젝트 대시보드에서 그대로 가져왔다 — 발표와 산출물의 색이 같아진다.

const pptx = require('pptxgenjs');
const p = new pptx();
p.layout = 'LAYOUT_WIDE';                 // 13.3 x 7.5
const W = 13.333, H = 7.5;

const C = {
  bg:    '0E1117',
  card:  '1B2230',
  soft:  '161B24',
  line:  '2A3444',
  fg:    'E6EDF6',
  dim:   '8B98AB',
  blue:  '4F9CF9',
  ok:    '37C98B',
  warn:  'F0B429',
  bad:   'F2617A',
  purp:  'A78BFA',
};
const F = 'Malgun Gothic';

const NAME = '김민석';

// ── 공통 헬퍼 ───────────────────────────────────────────────
function slide(dark = true) {
  const s = p.addSlide();
  s.background = { color: dark ? C.bg : C.soft };
  return s;
}

function title(s, text, sub) {
  s.addText(text, {
    x: 0.7, y: 0.45, w: W - 1.4, h: 0.72, margin: 0,
    fontFace: F, fontSize: 32, bold: true, color: C.fg, align: 'left',
  });
  if (sub) {
    s.addText(sub, {
      x: 0.7, y: 1.16, w: W - 1.4, h: 0.36, margin: 0,
      fontFace: F, fontSize: 14, color: C.dim, align: 'left',
    });
  }
}

function card(s, o) {
  s.addShape(p.ShapeType.roundRect, {
    x: o.x, y: o.y, w: o.w, h: o.h, rectRadius: 0.09,
    fill: { color: o.fill || C.card },
    line: { color: o.border || C.line, width: 1 },
  });
}

function pageNo(s, n) {
  s.addText(String(n), {
    x: W - 1.0, y: H - 0.62, w: 0.5, h: 0.3, margin: 0,
    fontFace: F, fontSize: 10, color: C.dim, align: 'right',
  });
}

// 배지 원 — 카드에서 쓰던 🔴 ⚪ 📋 ⚠️ 어휘를 슬라이드 전반의 모티프로 쓴다
function badge(s, x, y, glyph, col, d) {
  const dia = d || 0.42;
  s.addShape(p.ShapeType.ellipse, {
    x, y, w: dia, h: dia,
    fill: { color: C.soft }, line: { color: col, width: 1.5 },
  });
  s.addText(glyph, {
    x, y, w: dia, h: dia, margin: 0,
    fontFace: F, fontSize: 13, color: col, align: 'center', valign: 'middle', bold: true,
  });
}

let N = 0;
const num = () => ++N;

// ══════════════════════════════════════════════════════════
// 1. 표지
// ══════════════════════════════════════════════════════════
{
  const s = slide();
  s.addText('ReplyGate', {
    x: 0.9, y: 2.12, w: 9.6, h: 1.16, margin: 0,
    fontFace: F, fontSize: 60, bold: true, color: C.fg,
  });
  s.addText('AI가 쓰고, 사람이 승인해서 보내는 고객 응대 자동화', {
    x: 0.9, y: 3.28, w: 10.6, h: 0.5, margin: 0,
    fontFace: F, fontSize: 21, color: C.blue,
  });
  s.addText('AI를 빠르게 만드는 것보다, 통제 가능하게 만드는 것이 실무의 문제다', {
    x: 0.9, y: 3.92, w: 11.0, h: 0.42, margin: 0,
    fontFace: F, fontSize: 14, color: C.dim, italic: true,
  });

  card(s, { x: 0.9, y: 5.05, w: 6.6, h: 1.32 });
  s.addText([
    { text: '멀티캠퍼스 KDT AI캠퍼스  ·  AI에이전트 엔지니어 트랙', options: { breakLine: true, color: C.fg, fontSize: 13, bold: true } },
    { text: '2주차 미니프로젝트  ·  개인  ·  2026. 08', options: { color: C.dim, fontSize: 12 } },
  ], { x: 1.18, y: 5.24, w: 6.1, h: 0.6, margin: 0, fontFace: F, lineSpacing: 20 });
  s.addText(NAME, {
    x: 1.18, y: 5.86, w: 6.1, h: 0.34, margin: 0,
    fontFace: F, fontSize: 15, bold: true, color: C.blue,
  });

  badge(s, 10.6, 5.28, '🔴', C.bad, 0.5);
  badge(s, 11.24, 5.28, '⚪', C.dim, 0.5);
  badge(s, 11.88, 5.28, '📋', C.blue, 0.5);
  s.addText('검토 카드의 배지', {
    x: 10.3, y: 5.9, w: 2.4, h: 0.3, margin: 0,
    fontFace: F, fontSize: 10, color: C.dim, align: 'center',
  });
  s.addNotes('제목만 읽고 바로 3번 슬라이드로 넘어간다. 자기소개는 길게 하지 않는다.');
}

// ══════════════════════════════════════════════════════════
// 2. 목차
// ══════════════════════════════════════════════════════════
{
  const s = slide(); const n = num();
  title(s, '목차');
  const items = [
    ['01', '문제 정의', '환각이 그대로 고객에게 간다'],
    ['02', '해결 구조와 설계', 'Human-in-the-Loop'],
    ['03', '시스템 · 기술 스택 · 일정', ''],
    ['04', '시연', '라이브 데모'],
    ['05', '측정 — 효과가 있었나', 'RAG vs 베이스라인'],
    ['06', '한계와 트러블슈팅', ''],
    ['07', '회고와 향후 확장', ''],
  ];
  items.forEach((it, i) => {
    const col = i < 4 ? 0 : 1;
    const row = i < 4 ? i : i - 4;
    const x = 0.9 + col * 6.1, y = 1.85 + row * 1.08;
    s.addText(it[0], {
      x, y, w: 0.8, h: 0.5, margin: 0,
      fontFace: F, fontSize: 24, bold: true, color: C.blue,
    });
    s.addText(it[1], {
      x: x + 0.85, y: y + 0.02, w: 4.6, h: 0.36, margin: 0,
      fontFace: F, fontSize: 17, bold: true, color: C.fg,
    });
    if (it[2]) s.addText(it[2], {
      x: x + 0.85, y: y + 0.4, w: 4.6, h: 0.3, margin: 0,
      fontFace: F, fontSize: 12, color: C.dim,
    });
  });
  pageNo(s, n);
}

// ══════════════════════════════════════════════════════════
// 3. 문제 ① — 실물
// ══════════════════════════════════════════════════════════
{
  const s = slide(); const n = num();
  title(s, '이 답변이 그대로 고객에게 갔다면', 'AI가 정책 문서 없이 쓴 실제 출력물 · 평가셋 EV-17');

  card(s, { x: 0.7, y: 1.78, w: 7.5, h: 2.4, border: C.bad });
  s.addText([
    { text: '“지연에 대한 보상으로 온마켓에서 현금처럼 사용하실 수 있는\n', options: { fontSize: 16, color: C.fg, breakLine: false } },
    { text: '적립금 5,000원을 지급해 드렸습니다.', options: { fontSize: 19, color: C.bad, bold: true } },
    { text: '”', options: { fontSize: 16, color: C.fg } },
  ], { x: 1.02, y: 2.2, w: 6.9, h: 1.6, margin: 0, fontFace: F, lineSpacing: 32, valign: 'top' });

  const pts = [
    ['정책에 그 금액이 없다', '보상 규정은 주문 금액의 5% (DL-07)'],
    ['과거형으로 단정했다', '하지도 않은 일을 “드렸습니다”'],
    ['문장이 자연스럽다', '읽는 사람이 틀린 줄 모른다'],
  ];
  pts.forEach((t, i) => {
    const y = 1.85 + i * 0.8;
    badge(s, 8.62, y + 0.05, String(i + 1), C.bad, 0.38);
    s.addText(t[0], { x: 9.14, y: y + 0.0, w: 3.6, h: 0.32, margin: 0, fontFace: F, fontSize: 14, bold: true, color: C.fg });
    s.addText(t[1], { x: 9.14, y: y + 0.32, w: 3.6, h: 0.34, margin: 0, fontFace: F, fontSize: 11, color: C.dim });
  });

  card(s, { x: 0.7, y: 4.62, w: 11.93, h: 1.0, fill: C.soft, border: C.line });
  s.addText('오타가 아니라 분쟁입니다. 그리고 아무도 검토하지 않으면 그대로 발송됩니다.', {
    x: 1.02, y: 4.9, w: 11.3, h: 0.46, margin: 0,
    fontFace: F, fontSize: 17, bold: true, color: C.warn,
  });

  s.addText('LLM은 “환불은 영업일 기준 7일 이내에 처리됩니다” 같은 문장을 규정이 14일이어도 자연스럽게 생성한다.', {
    x: 0.7, y: 5.94, w: 11.93, h: 0.36, margin: 0, fontFace: F, fontSize: 12, color: C.dim,
  });
  pageNo(s, n);
  s.addNotes('설명하기 전에 5초 정도 읽게 둔다. 그다음 세 가지를 순서대로 짚는다.');
}

// ══════════════════════════════════════════════════════════
// 4. 문제 ② — 환각의 비용
// ══════════════════════════════════════════════════════════
{
  const s = slide(); const n = num();
  title(s, '틀리면 회사가 손해를 본다', '베이스라인이 실제로 쓴 답변 두 건');

  const cases = [
    { id: 'EV-42', said: '“소멸된 적립금은 확인 즉시\n전액 복구 조치될 예정입니다”', real: '정책상 복원 불가 (MB-07)', tag: '없는 권한을 행사했다' },
    { id: 'EV-50', said: '“오늘 중으로 해지 수수료\n면제 처리를 완료해 드리겠습니다”', real: '가입 당시 안내 누락을 인정', tag: '회사 귀책을 AI가 시인했다' },
  ];
  cases.forEach((c, i) => {
    const x = 0.7 + i * 6.2;
    card(s, { x, y: 1.8, w: 5.73, h: 2.72 });
    s.addText(c.id, { x: x + 0.3, y: 2.0, w: 2.0, h: 0.3, margin: 0, fontFace: F, fontSize: 12, bold: true, color: C.bad });
    s.addText(c.said, { x: x + 0.3, y: 2.36, w: 5.1, h: 0.86, margin: 0, fontFace: F, fontSize: 14, color: C.fg, lineSpacing: 22 });
    s.addText('실제 정책', { x: x + 0.3, y: 3.34, w: 2.0, h: 0.26, margin: 0, fontFace: F, fontSize: 10, color: C.dim });
    s.addText(c.real, { x: x + 0.3, y: 3.58, w: 5.1, h: 0.3, margin: 0, fontFace: F, fontSize: 13, bold: true, color: C.ok });
    s.addText(c.tag, { x: x + 0.3, y: 3.98, w: 5.1, h: 0.3, margin: 0, fontFace: F, fontSize: 12, color: C.warn, italic: true });
  });

  card(s, { x: 0.7, y: 4.82, w: 11.93, h: 1.42, fill: C.soft });
  s.addText('그렇다고 사람이 처음부터 쓰면', {
    x: 1.02, y: 5.0, w: 5.0, h: 0.32, margin: 0, fontFace: F, fontSize: 13, bold: true, color: C.dim,
  });
  s.addText([
    { text: '문의 한 건당 5~10분', options: { fontSize: 20, bold: true, color: C.fg } },
    { text: '   ·   반복 유형이 대부분인데 매번 규정을 찾는다   ·   자동화의 의미가 없다', options: { fontSize: 13, color: C.dim } },
  ], { x: 1.02, y: 5.42, w: 11.3, h: 0.44, margin: 0, fontFace: F });
  pageNo(s, n);
}

// ══════════════════════════════════════════════════════════
// 5. 해결 구조
// ══════════════════════════════════════════════════════════
{
  const s = slide(); const n = num();
  title(s, '해결 구조', '실무가 쓰는 방식 — Human-in-the-Loop');

  const steps = [
    { t: 'AI 초안 생성', d: '정책 문서를 근거로\n답변을 쓴다', c: C.blue },
    { t: '사람의 검토·승인', d: '휴대폰 텔레그램에서\n버튼 하나로', c: C.warn },
    { t: '최종 발송', d: '승인된 것만\nGmail로 나간다', c: C.ok },
  ];
  steps.forEach((st, i) => {
    const x = 0.7 + i * 4.28;
    card(s, { x, y: 1.9, w: 3.68, h: 1.86, border: st.c });
    badge(s, x + 0.3, 2.14, String(i + 1), st.c, 0.42);
    s.addText(st.t, { x: x + 0.84, y: 2.18, w: 2.6, h: 0.34, margin: 0, fontFace: F, fontSize: 16, bold: true, color: st.c });
    s.addText(st.d, { x: x + 0.3, y: 2.74, w: 3.1, h: 0.8, margin: 0, fontFace: F, fontSize: 12.5, color: C.dim, lineSpacing: 19 });
    if (i < 2) s.addText('▶', { x: x + 3.72, y: 2.62, w: 0.5, h: 0.4, margin: 0, fontFace: F, fontSize: 16, color: C.line, align: 'center' });
  });

  card(s, { x: 0.7, y: 4.06, w: 11.93, h: 0.94, fill: C.soft, border: C.blue });
  s.addText('AI를 빠르게 만드는 것보다, 통제 가능하게 만드는 것이 실무의 문제다', {
    x: 1.02, y: 4.28, w: 11.3, h: 0.46, margin: 0, fontFace: F, fontSize: 19, bold: true, color: C.blue,
  });

  s.addText('이 프로젝트는 이 구조를 무료 도구 조합만으로 구현하고, “통제 가능하게 만들면서도 실제로 빨라졌는가”를 숫자로 증명한다.', {
    x: 0.7, y: 5.24, w: 11.93, h: 0.36, margin: 0, fontFace: F, fontSize: 13, color: C.dim,
  });
  pageNo(s, n);
}

// ══════════════════════════════════════════════════════════
// 6. 프로젝트 개요
// ══════════════════════════════════════════════════════════
{
  const s = slide(); const n = num();
  title(s, '프로젝트 개요');

  card(s, { x: 0.7, y: 1.72, w: 11.93, h: 1.24, border: C.blue });
  s.addText('고객 문의가 접수되면 AI가 사내 정책 문서를 근거로 답변 초안을 작성하고,\n담당자가 텔레그램에서 검토·수정·승인한 뒤에만 메일이 발송되는 시스템', {
    x: 1.02, y: 1.94, w: 11.3, h: 0.84, margin: 0, fontFace: F, fontSize: 16, color: C.fg, lineSpacing: 26,
  });

  const stats = [
    { v: '0원', l: '운영 비용', c: C.ok },
    { v: '7일', l: '개발 기간', c: C.blue },
    { v: '70', l: '정책 조항', c: C.purp },
    { v: '50건', l: '평가셋', c: C.warn },
  ];
  stats.forEach((st, i) => {
    const x = 0.7 + i * 3.03;
    card(s, { x, y: 3.2, w: 2.78, h: 1.5 });
    s.addText(st.v, { x, y: 3.44, w: 2.78, h: 0.6, margin: 0, fontFace: F, fontSize: 32, bold: true, color: st.c, align: 'center' });
    s.addText(st.l, { x, y: 4.1, w: 2.78, h: 0.3, margin: 0, fontFace: F, fontSize: 12, color: C.dim, align: 'center' });
  });

  const meta = [
    ['적용 도메인', '이커머스 쇼핑몰 CS'],
    ['형태', '개인 프로젝트'],
    ['주 지표', '1차 승인률 (수정 없이 발송 가능한 초안의 비율)'],
  ];
  meta.forEach((m, i) => {
    const y = 5.0 + i * 0.44;
    s.addText(m[0], { x: 0.7, y, w: 2.2, h: 0.34, margin: 0, fontFace: F, fontSize: 12.5, color: C.dim });
    s.addText(m[1], { x: 2.95, y, w: 9.6, h: 0.34, margin: 0, fontFace: F, fontSize: 13, color: C.fg });
  });
  pageNo(s, n);
}

// ══════════════════════════════════════════════════════════
// 7. 시스템 아키텍처
// ══════════════════════════════════════════════════════════
{
  const s = slide(); const n = num();
  title(s, '시스템 아키텍처', 'n8n과 대시보드는 직접 통신하지 않는다 — 구글 시트를 공용 저장소로 둔다');

  const boxes = [
    { x: 0.7,  y: 1.9,  w: 2.3, h: 0.86, t: '고객', d: 'Google Forms', c: C.dim },
    { x: 3.34, y: 1.9,  w: 2.3, h: 0.86, t: 'Google Sheets', d: '상태 · 이력', c: C.ok },
    { x: 5.98, y: 1.9,  w: 3.5, h: 0.86, t: 'n8n 워크플로우', d: '분류 → RAG → 초안 생성', c: C.blue },
    { x: 9.82, y: 1.9,  w: 2.8, h: 0.86, t: 'Gmail 초안', d: '임시보관함 저장', c: C.dim },
  ];
  boxes.forEach(b => {
    card(s, { x: b.x, y: b.y, w: b.w, h: b.h, border: b.c });
    s.addText(b.t, { x: b.x, y: b.y + 0.13, w: b.w, h: 0.3, margin: 0, fontFace: F, fontSize: 13.5, bold: true, color: b.c, align: 'center' });
    s.addText(b.d, { x: b.x, y: b.y + 0.45, w: b.w, h: 0.28, margin: 0, fontFace: F, fontSize: 10.5, color: C.dim, align: 'center' });
  });
  [3.02, 5.66, 9.5].forEach(x => s.addText('▶', { x, y: 2.16, w: 0.32, h: 0.34, margin: 0, fontFace: F, fontSize: 13, color: C.line, align: 'center' }));

  card(s, { x: 5.98, y: 3.12, w: 6.64, h: 1.5, border: C.warn });
  s.addText('담당자 (휴대폰 · 텔레그램)', { x: 6.3, y: 3.3, w: 6.0, h: 0.3, margin: 0, fontFace: F, fontSize: 13.5, bold: true, color: C.warn });
  s.addText([
    { text: '✅ 발송 승인', options: { fontSize: 13, bold: true, color: C.ok, breakLine: true } },
    { text: '✏️ 수정 요청 → 자연어 지시 → AI 재작성 → 재검토 (승인까지 반복)', options: { fontSize: 12, color: C.dim } },
  ], { x: 6.3, y: 3.66, w: 6.0, h: 0.8, margin: 0, fontFace: F, lineSpacing: 20 });

  card(s, { x: 0.7, y: 3.12, w: 4.94, h: 1.5, border: C.purp });
  s.addText('FastAPI 대시보드 (로컬)', { x: 1.02, y: 3.3, w: 4.4, h: 0.3, margin: 0, fontFace: F, fontSize: 13.5, bold: true, color: C.purp });
  s.addText([
    { text: '실시간 상황판 (SSE)', options: { fontSize: 12, color: C.dim, breakLine: true } },
    { text: '지표 집계 · 시트 읽기 전용', options: { fontSize: 12, color: C.dim } },
  ], { x: 1.02, y: 3.66, w: 4.4, h: 0.7, margin: 0, fontFace: F, lineSpacing: 20 });

  card(s, { x: 0.7, y: 4.96, w: 11.93, h: 0.9, fill: C.soft });
  s.addText('이 결정으로 외부 공개 URL(ngrok 등)이 불필요해지고, 발표 당일 네트워크 장애로 데모가 죽을 위험이 사라진다.', {
    x: 1.02, y: 5.18, w: 11.3, h: 0.44, margin: 0, fontFace: F, fontSize: 13.5, color: C.fg,
  });
  pageNo(s, n);
}

// ══════════════════════════════════════════════════════════
// 8. 주요 기능
// ══════════════════════════════════════════════════════════
{
  const s = slide(); const n = num();
  title(s, '주요 기능');

  const fs = [
    ['🏷️', '유형 · 감정 분류', '6종 유형 + 감정(불만/일반) + 주문 조회 필요 여부', C.blue],
    ['🔍', '정책 근거 검색 (RAG)', '문의를 임베딩해 70개 조항 중 상위 3개를 찾는다', C.purp],
    ['✍️', '초안 생성 + 근거 인용', '검색된 조항 밖의 수치는 쓰지 못하게 한다', C.ok],
    ['📱', '텔레그램 승인 · 수정 루프', '버튼 2개. 자연어로 수정 지시, 승인까지 반복', C.warn],
    ['⚠️', '정책 충돌 감지', '검토자 지시가 정책과 어긋나면 경고를 띄운다', C.bad],
    ['📊', '대시보드 · 실시간 상황판', '상태 흐름과 운영 지표를 읽기 전용으로 집계', C.dim],
  ];
  fs.forEach((f, i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = 0.7 + col * 6.2, y = 1.72 + row * 1.42;
    card(s, { x, y, w: 5.73, h: 1.2 });
    badge(s, x + 0.28, y + 0.36, f[0], f[3], 0.48);
    s.addText(f[1], { x: x + 0.92, y: y + 0.24, w: 4.6, h: 0.32, margin: 0, fontFace: F, fontSize: 15, bold: true, color: C.fg });
    s.addText(f[2], { x: x + 0.92, y: y + 0.62, w: 4.6, h: 0.44, margin: 0, fontFace: F, fontSize: 11.5, color: C.dim });
  });

  s.addText('전체 기능 명세 F1~F17은 docs/기획서.md 에 정리되어 있다.', {
    x: 0.7, y: 6.12, w: 11.93, h: 0.3, margin: 0, fontFace: F, fontSize: 11, color: C.dim,
  });
  pageNo(s, n);
}

// ══════════════════════════════════════════════════════════
// 9. 설계에서 신경 쓴 것
// ══════════════════════════════════════════════════════════
{
  const s = slide(); const n = num();
  title(s, '설계에서 신경 쓴 것', '만들지 않기로 한 것도 설계다');

  const items = [
    ['승인 창구는 하나로', '웹 승인 기능을 일부러 만들지 않았다. 만드는 순간 “휴대폰만으로 완결된다”는 차별점이 스스로 무너진다.', C.warn],
    ['근거를 함께 띄운다', '초안이 인용한 조항 ID를 카드에 표시해 담당자가 3초 만에 검증한다. 이게 없으면 승인은 형식이 된다.', C.ok],
    ['분류를 두 축으로', '감정(불만/일반)과 주문 조회 필요 여부는 직교하는 별개의 축이다. 처음엔 하나로 묶었다가 측정 결과 분리했다.', C.purp],
    ['양방향 검증', 'AI의 실수는 사람이 막고, 사람의 실수는 AI가 잡는다. 검토자 지시가 정책과 어긋나면 경고하되 막지는 않는다.', C.bad],
  ];
  items.forEach((it, i) => {
    const col = i % 2, row = Math.floor(i / 2);
    const x = 0.7 + col * 6.2, y = 1.85 + row * 2.12;
    card(s, { x, y, w: 5.73, h: 1.9, border: it[2] });
    s.addText(it[0], { x: x + 0.32, y: y + 0.26, w: 5.1, h: 0.36, margin: 0, fontFace: F, fontSize: 17, bold: true, color: it[2] });
    s.addText(it[1], { x: x + 0.32, y: y + 0.74, w: 5.1, h: 0.96, margin: 0, fontFace: F, fontSize: 12.5, color: C.dim, lineSpacing: 20 });
  });
  pageNo(s, n);
}

// ══════════════════════════════════════════════════════════
// 10. 기술 스택 · 개발 일정
// ══════════════════════════════════════════════════════════
{
  const s = slide(); const n = num();
  title(s, '기술 스택과 개발 일정');

  card(s, { x: 0.7, y: 1.78, w: 5.73, h: 4.4 });
  s.addText('기술 스택', { x: 1.02, y: 1.98, w: 5.1, h: 0.34, margin: 0, fontFace: F, fontSize: 17, bold: true, color: C.blue });
  const stack = [
    ['오케스트레이션', 'n8n (Cloud)'],
    ['LLM', 'Gemini 3.5 Flash Lite'],
    ['임베딩', 'gemini-embedding-001 (768차원)'],
    ['벡터 검색', '시트 저장 + 코사인 유사도'],
    ['문의 접수', 'Google Forms + Sheets'],
    ['메일', 'Gmail API'],
    ['담당자 UI', 'Telegram Bot'],
    ['대시보드', 'FastAPI + SSE'],
  ];
  stack.forEach((t, i) => {
    const y = 2.46 + i * 0.44;
    s.addText(t[0], { x: 1.02, y, w: 1.95, h: 0.32, margin: 0, fontFace: F, fontSize: 11.5, color: C.dim });
    s.addText(t[1], { x: 3.02, y, w: 3.3, h: 0.32, margin: 0, fontFace: F, fontSize: 12, color: C.fg });
  });
  s.addText('전부 무료 티어 · 총 운영 비용 0원', {
    x: 1.02, y: 5.92, w: 5.1, h: 0.3, margin: 0, fontFace: F, fontSize: 12, bold: true, color: C.ok,
  });

  card(s, { x: 6.9, y: 1.78, w: 5.73, h: 4.4 });
  s.addText('개발 일정 (7일)', { x: 7.22, y: 1.98, w: 5.1, h: 0.34, margin: 0, fontFace: F, fontSize: 17, bold: true, color: C.purp });
  const days = [
    ['D1', '기술 리스크 검증', C.ok],
    ['D2', '기본 파이프라인 관통', C.ok],
    ['D3', '텔레그램 승인', C.ok],
    ['D4', '수정 루프 + RAG', C.ok],
    ['D5', '평가셋 구축 + 1차 측정', C.ok],
    ['D6', '대시보드 + 상황판', C.ok],
    ['D7', '발표 준비', C.warn],
  ];
  days.forEach((d, i) => {
    const y = 2.5 + i * 0.5;
    s.addShape(p.ShapeType.roundRect, {
      x: 7.22, y, w: 0.62, h: 0.34, rectRadius: 0.06,
      fill: { color: C.soft }, line: { color: d[2], width: 1 },
    });
    s.addText(d[0], { x: 7.22, y, w: 0.62, h: 0.34, margin: 0, fontFace: F, fontSize: 11, bold: true, color: d[2], align: 'center', valign: 'middle' });
    s.addText(d[1], { x: 7.98, y: y + 0.02, w: 4.4, h: 0.3, margin: 0, fontFace: F, fontSize: 12.5, color: C.fg });
  });
  s.addText('D4가 가장 무거웠다 — 정책 문서 6종 작성·적재와 수정 루프가 겹친다.', {
    x: 7.22, y: 5.92, w: 5.1, h: 0.3, margin: 0, fontFace: F, fontSize: 11, color: C.dim,
  });
  pageNo(s, n);
}

// ══════════════════════════════════════════════════════════
// 11. 시연
// ══════════════════════════════════════════════════════════
{
  const s = slide(); const n = num();
  s.addText('시연', {
    x: 0.9, y: 1.5, w: 6.0, h: 0.9, margin: 0,
    fontFace: F, fontSize: 46, bold: true, color: C.fg,
  });
  s.addText('QR로 직접 문의를 남겨 주세요', {
    x: 0.9, y: 2.42, w: 6.0, h: 0.4, margin: 0,
    fontFace: F, fontSize: 17, color: C.blue,
  });

  const steps = [
    ['폼 제출', '청중이 직접 문의를 남긴다'],
    ['상황판', '접수됨 → 분석중 → 승인대기'],
    ['텔레그램 카드', '배지 · 근거 조항 · 문의 원문'],
    ['승인', '메일함을 확인해 보세요'],
    ['수정 루프', '정책과 다른 지시 → ⚠️ 경고'],
  ];
  steps.forEach((st, i) => {
    const y = 3.16 + i * 0.62;
    badge(s, 0.9, y, String(i + 1), C.blue, 0.4);
    s.addText(st[0], { x: 1.42, y: y + 0.01, w: 2.2, h: 0.32, margin: 0, fontFace: F, fontSize: 14, bold: true, color: C.fg });
    s.addText(st[1], { x: 3.6, y: y + 0.03, w: 4.0, h: 0.3, margin: 0, fontFace: F, fontSize: 12, color: C.dim });
  });

  card(s, { x: 8.5, y: 1.5, w: 4.13, h: 4.8, fill: C.soft, border: C.blue });
  s.addText('QR 코드', {
    x: 8.5, y: 3.3, w: 4.13, h: 0.4, margin: 0,
    fontFace: F, fontSize: 15, bold: true, color: C.dim, align: 'center',
  });
  s.addText('발표 전 구글 폼 QR 이미지로 교체', {
    x: 8.5, y: 3.74, w: 4.13, h: 0.34, margin: 0,
    fontFace: F, fontSize: 11, color: C.dim, align: 'center', italic: true,
  });
  pageNo(s, n);
  s.addNotes('폼 제출은 2~3명으로 제한한다. RPM 15라 분당 7~8건이 상한.\n카드가 1분 넘게 안 오면 미리 대기시켜둔 백업 건으로 진행한다.\n데모가 완전히 실패하면 당황하지 말고 측정 파트로 넘어간다. 결론은 숫자다.');
}

// ══════════════════════════════════════════════════════════
// 12. 측정 설계
// ══════════════════════════════════════════════════════════
{
  const s = slide(); const n = num();
  title(s, '측정 설계', '“RAG를 붙였습니다”가 아니라 “붙였더니 얼마나 나아졌습니다”를 말하기 위해');

  card(s, { x: 0.7, y: 1.85, w: 5.73, h: 2.0, border: C.bad });
  s.addText('베이스라인', { x: 1.02, y: 2.06, w: 5.1, h: 0.34, margin: 0, fontFace: F, fontSize: 18, bold: true, color: C.bad });
  s.addText('정책 문서 없이 Gemini가 일반 지식으로 답변을 생성한다', { x: 1.02, y: 2.5, w: 5.1, h: 0.6, margin: 0, fontFace: F, fontSize: 13, color: C.dim, lineSpacing: 20 });

  card(s, { x: 6.9, y: 1.85, w: 5.73, h: 2.0, border: C.ok });
  s.addText('RAG 적용', { x: 7.22, y: 2.06, w: 5.1, h: 0.34, margin: 0, fontFace: F, fontSize: 18, bold: true, color: C.ok });
  s.addText('정책 조항을 검색해 근거로 제시하고 생성한다 (실제 파이프라인과 동일)', { x: 7.22, y: 2.5, w: 5.1, h: 0.6, margin: 0, fontFace: F, fontSize: 13, color: C.dim, lineSpacing: 20 });

  s.addText('동일한 평가셋 50건을 두 조건으로 각각 측정', {
    x: 0.7, y: 4.02, w: 11.93, h: 0.36, margin: 0, fontFace: F, fontSize: 15, bold: true, color: C.fg, align: 'center',
  });

  const dist = [
    ['유형', '환불 12 · 배송 10 · 교환반품 8 · 불량AS 8 · 회원적립금 7 · 기타 5'],
    ['감정', '불만 15 · 일반 35'],
    ['난이도', '단일조항 30 · 복수조항 15 · 정보없음 5'],
    ['함정 5건', '정책 문서에 의도적으로 넣지 않은 주제. 지어내는지 본다'],
  ];
  dist.forEach((d, i) => {
    const y = 4.62 + i * 0.44;
    s.addText(d[0], { x: 0.7, y, w: 1.5, h: 0.32, margin: 0, fontFace: F, fontSize: 12, bold: true, color: i === 3 ? C.warn : C.dim });
    s.addText(d[1], { x: 2.3, y, w: 10.3, h: 0.32, margin: 0, fontFace: F, fontSize: 12.5, color: i === 3 ? C.warn : C.fg });
  });
  pageNo(s, n);
}

// ══════════════════════════════════════════════════════════
// 13. 측정 결과 ★
// ══════════════════════════════════════════════════════════
{
  const s = slide(); const n = num();
  title(s, '측정 결과');

  s.addChart(p.ChartType.bar, [
    { name: 'RAG 적용', labels: ['1차 승인률 (주 지표)', '수치 정확률'], values: [94.0, 96.0] },
    { name: '베이스라인', labels: ['1차 승인률 (주 지표)', '수치 정확률'], values: [34.0, 43.8] },
  ], {
    x: 0.7, y: 1.7, w: 7.5, h: 4.0,
    barDir: 'col', barGapWidthPct: 60,
    chartColors: [C.ok, C.bad],
    showTitle: false,
    showValue: true, dataLabelPosition: 'outEnd', dataLabelColor: C.fg,
    dataLabelFontFace: F, dataLabelFontSize: 14, dataLabelFormatCode: '0.0"%"',
    showLegend: true, legendPos: 'b', legendColor: C.dim, legendFontFace: F, legendFontSize: 12,
    catAxisLabelColor: C.fg, catAxisLabelFontFace: F, catAxisLabelFontSize: 12,
    valAxisLabelColor: C.dim, valAxisLabelFontFace: F, valAxisLabelFontSize: 10,
    valAxisMaxVal: 100, valAxisMinVal: 0,
    valGridLine: { color: C.line, size: 1 },
    catGridLine: { style: 'none' },
    plotArea: { fill: { color: C.bg } },
    chartArea: { fill: { color: C.bg } },
  });

  const kv = [
    ['1차 승인률', '94.0%', '34.0%', C.ok],
    ['수치 정확률', '96.0%', '43.8%', C.ok],
    ['정답과 다른 수치', '2개', '20개', C.blue],
    ['함정 5건 수치 창작', '0건', '1건', C.blue],
  ];
  card(s, { x: 8.6, y: 1.7, w: 4.03, h: 3.06 });
  s.addText('', { x: 8.6, y: 1.7, w: 0.01, h: 0.01 });
  s.addText([
    { text: '항목', options: { fontSize: 10, color: C.dim } },
  ], { x: 8.86, y: 1.88, w: 1.9, h: 0.24, margin: 0, fontFace: F });
  s.addText('RAG', { x: 10.72, y: 1.88, w: 0.86, h: 0.24, margin: 0, fontFace: F, fontSize: 10, color: C.ok, align: 'right' });
  s.addText('기준선', { x: 11.6, y: 1.88, w: 0.86, h: 0.24, margin: 0, fontFace: F, fontSize: 10, color: C.bad, align: 'right' });
  kv.forEach((r, i) => {
    const y = 2.24 + i * 0.6;
    s.addText(r[0], { x: 8.86, y, w: 1.9, h: 0.3, margin: 0, fontFace: F, fontSize: 11.5, color: C.fg });
    s.addText(r[1], { x: 10.72, y, w: 0.86, h: 0.3, margin: 0, fontFace: F, fontSize: 13, bold: true, color: C.ok, align: 'right' });
    s.addText(r[2], { x: 11.6, y, w: 0.86, h: 0.3, margin: 0, fontFace: F, fontSize: 13, color: C.bad, align: 'right' });
  });

  card(s, { x: 8.6, y: 4.98, w: 4.03, h: 1.32, fill: C.soft, border: C.ok });
  s.addText('+60.0%p', { x: 8.6, y: 5.14, w: 4.03, h: 0.5, margin: 0, fontFace: F, fontSize: 27, bold: true, color: C.ok, align: 'center' });
  s.addText('정책 근거를 주자 승인 가능한\n초안이 이만큼 늘었다', { x: 8.6, y: 5.66, w: 4.03, h: 0.5, margin: 0, fontFace: F, fontSize: 11, color: C.dim, align: 'center', lineSpacing: 15 });
  pageNo(s, n);
}

// ══════════════════════════════════════════════════════════
// 14. 지표 해석
// ══════════════════════════════════════════════════════════
{
  const s = slide(); const n = num();
  title(s, '숫자를 어떻게 읽을 것인가', '지표를 두 개 재는 의미가 있으려면');

  card(s, { x: 0.7, y: 1.8, w: 5.73, h: 2.5, border: C.blue });
  s.addText('1차 승인률은 수치 정확률의 재탕이 아니다', { x: 1.02, y: 2.0, w: 5.1, h: 0.62, margin: 0, fontFace: F, fontSize: 16, bold: true, color: C.blue, lineSpacing: 22 });
  s.addText([
    { text: 'X 36건 중 21건', options: { fontSize: 19, bold: true, color: C.fg, breakLine: true } },
    { text: '은 수치 오류가 아닌 사유였다 — 근거 없는 확약, 원인 창작, 정책 정면 위반.', options: { fontSize: 12.5, color: C.dim } },
  ], { x: 1.02, y: 2.72, w: 5.1, h: 1.2, margin: 0, fontFace: F, lineSpacing: 20 });

  card(s, { x: 6.9, y: 1.8, w: 5.73, h: 2.5, border: C.warn });
  s.addText('베이스라인이 34%나 나온 이유', { x: 7.22, y: 2.0, w: 5.1, h: 0.36, margin: 0, fontFace: F, fontSize: 16, bold: true, color: C.warn });
  s.addText('EV-37은 수리 기간 7~14일을 정책 없이 맞혔다. AI가 아무것도 못 맞춘 게 아니라, 일반 상식과 이 회사 정책이 우연히 겹칠 때만 맞았다.', {
    x: 7.22, y: 2.5, w: 5.1, h: 1.4, margin: 0, fontFace: F, fontSize: 12.5, color: C.dim, lineSpacing: 20,
  });

  card(s, { x: 0.7, y: 4.5, w: 11.93, h: 1.72, fill: C.soft });
  s.addText('판정 기준 — 담당자가 “수정 없이 발송”을 누르는가', { x: 1.02, y: 4.7, w: 11.3, h: 0.32, margin: 0, fontFace: F, fontSize: 14, bold: true, color: C.fg });
  const crit = ['정책 위반', '사실 창작', '근거 없는 확약', '질문 미응답'];
  crit.forEach((c, i) => {
    const x = 1.02 + i * 2.5;
    s.addShape(p.ShapeType.roundRect, { x, y: 5.16, w: 2.3, h: 0.42, rectRadius: 0.08, fill: { color: C.card }, line: { color: C.bad, width: 1 } });
    s.addText(c, { x, y: 5.16, w: 2.3, h: 0.42, margin: 0, fontFace: F, fontSize: 12, color: C.bad, align: 'center', valign: 'middle' });
  });
  s.addText('넷 중 하나라도 있으면 X · 어조와 군더더기는 통과 · 판정 근거를 100줄 전부 기록했다', {
    x: 1.02, y: 5.72, w: 11.3, h: 0.32, margin: 0, fontFace: F, fontSize: 12, color: C.dim,
  });
  pageNo(s, n);
}

// ══════════════════════════════════════════════════════════
// 15. 측정이 설계를 바꿨다 ★
// ══════════════════════════════════════════════════════════
{
  const s = slide(); const n = num();
  title(s, '측정이 설계를 바꿨다', '감정 분류 — 세 번의 측정');

  const rows = [
    ['v1', '3단계 초기 정의', '56.0%', '중립 0/20 — 한 번도 안 골랐다', C.bad],
    ['v2', '정의를 다듬었다', '84.0%', '중립 0/7 — 라벨만 옮긴 가짜 개선', C.warn],
    ['v3', '두 축으로 분리', '98.0%', '조회필요 축이 독립 지표가 됐다', C.ok],
  ];
  rows.forEach((r, i) => {
    const y = 1.82 + i * 1.0;
    card(s, { x: 0.7, y, w: 11.93, h: 0.86, border: r[4] });
    s.addText(r[0], { x: 1.0, y: y + 0.22, w: 0.7, h: 0.4, margin: 0, fontFace: F, fontSize: 17, bold: true, color: r[4] });
    s.addText(r[1], { x: 1.8, y: y + 0.26, w: 3.0, h: 0.34, margin: 0, fontFace: F, fontSize: 14, color: C.fg });
    s.addText(r[2], { x: 5.0, y: y + 0.18, w: 1.5, h: 0.48, margin: 0, fontFace: F, fontSize: 22, bold: true, color: r[4], align: 'right' });
    s.addText(r[3], { x: 6.9, y: y + 0.26, w: 5.5, h: 0.34, margin: 0, fontFace: F, fontSize: 12.5, color: C.dim });
  });

  card(s, { x: 0.7, y: 4.92, w: 11.93, h: 1.42, fill: C.soft, border: C.purp });
  s.addText('클래스가 학습 불가능했던 게 아니라 잘못 놓여 있었다', {
    x: 1.02, y: 5.1, w: 11.3, h: 0.34, margin: 0, fontFace: F, fontSize: 16, bold: true, color: C.purp,
  });
  s.addText('감정과 “주문 조회가 필요한가”는 직교하는 두 축인데 하나의 enum에 눌러 담았다.\n독립된 축을 주자 바로 살아났고, 쓰이지 않던 클래스는 카드의 📋 배지라는 실제 기능이 됐다.', {
    x: 1.02, y: 5.5, w: 11.3, h: 0.66, margin: 0, fontFace: F, fontSize: 12.5, color: C.dim, lineSpacing: 20,
  });
  pageNo(s, n);
  s.addNotes('v2를 숨기지 않는 것이 핵심이다. 라벨을 모델이 이미 답하던 쪽으로 옮겨서 오른 숫자였고 중립은 여전히 0이었다. 이걸 개선이라고 보고했으면 자기기만이다.\n클래스별로 쪼개봤기 때문에 0/7을 발견했고 거기서 구조 문제에 도달했다.');
}

// ══════════════════════════════════════════════════════════
// 16. 한계
// ══════════════════════════════════════════════════════════
{
  const s = slide(); const n = num();
  title(s, 'RAG를 붙여도 환각은 남는다', '한계를 먼저 말한다');

  card(s, { x: 0.7, y: 1.85, w: 11.93, h: 2.28, border: C.warn });
  s.addText('EV-12 · 함정 문항 (기프트카드 환불 — 정책에 없는 주제)', {
    x: 1.02, y: 2.08, w: 11.3, h: 0.32, margin: 0, fontFace: F, fontSize: 13, bold: true, color: C.warn,
  });
  s.addText([
    { text: 'insufficient_info = true', options: { fontSize: 15, bold: true, color: C.ok, breakLine: true } },
    { text: '“정보가 부족하다”는 플래그는 정확히 달았다.', options: { fontSize: 12.5, color: C.dim, breakLine: true } },
    { text: '\n', options: { fontSize: 6, breakLine: true } },
    { text: '그런데 본문에서는 — “환불이 승인되면 결제하셨던 기프트카드 수단으로 다시 환급이 진행됩니다”', options: { fontSize: 14, bold: true, color: C.bad } },
  ], { x: 1.02, y: 2.5, w: 11.3, h: 1.4, margin: 0, fontFace: F, lineSpacing: 22 });

  const two = [
    ['5 / 5', '플래그 기준 함정 회피', C.ok],
    ['4 / 5', '본문 기준 함정 회피', C.bad],
  ];
  two.forEach((t, i) => {
    const x = 0.7 + i * 3.1;
    card(s, { x, y: 4.36, w: 2.86, h: 1.34 });
    s.addText(t[0], { x, y: 4.54, w: 2.86, h: 0.5, margin: 0, fontFace: F, fontSize: 26, bold: true, color: t[2], align: 'center' });
    s.addText(t[1], { x, y: 5.08, w: 2.86, h: 0.44, margin: 0, fontFace: F, fontSize: 11.5, color: C.dim, align: 'center' });
  });

  card(s, { x: 7.0, y: 4.36, w: 5.63, h: 1.34, fill: C.soft, border: C.blue });
  s.addText('그래서 사람 승인을 뺄 수 없다', { x: 7.32, y: 4.56, w: 5.0, h: 0.34, margin: 0, fontFace: F, fontSize: 15, bold: true, color: C.blue });
  s.addText('환각을 줄이는 것과 없애는 것은 다르다. HITL은 성능이 좋아져도 남아야 하는 구조다.', {
    x: 7.32, y: 4.96, w: 5.0, h: 0.6, margin: 0, fontFace: F, fontSize: 12, color: C.dim, lineSpacing: 18,
  });
  pageNo(s, n);
}

// ══════════════════════════════════════════════════════════
// 17. 트러블슈팅
// ══════════════════════════════════════════════════════════
{
  const s = slide(); const n = num();
  title(s, '트러블슈팅', '정상 경로만 따라가는 검증으로는 안 나오는 결함');

  card(s, { x: 0.7, y: 1.8, w: 11.93, h: 1.5, border: C.bad });
  s.addText('발송이 끝난 건의 옛 텔레그램 카드에서 “수정 요청”을 눌렀더니 그대로 먹혔다', {
    x: 1.02, y: 2.02, w: 11.3, h: 0.36, margin: 0, fontFace: F, fontSize: 17, bold: true, color: C.fg,
  });
  s.addText('상태가 수정중으로 되돌아가 재작성이 돌았고, 그대로 승인했으면 같은 고객에게 메일이 두 번 나갔다.', {
    x: 1.02, y: 2.48, w: 11.3, h: 0.36, margin: 0, fontFace: F, fontSize: 13, color: C.dim,
  });
  s.addText('승인 경로에는 중복 방어가 있었는데, 수정 경로에는 없었다.', {
    x: 1.02, y: 2.84, w: 11.3, h: 0.34, margin: 0, fontFace: F, fontSize: 13.5, bold: true, color: C.bad,
  });

  const flow = [
    ['승인 경로', '콜백 → 문의 읽기 → 대상 조회 → [발송완료면 차단] → 발송', C.ok, '방어 있음'],
    ['수정 경로 (기존)', '콜백 → 상태: 수정중', C.bad, '검사 없이 바로 씀'],
    ['수정 경로 (수정 후)', '콜백 → 문의 읽기(가드) → 판정 → [발송완료면 차단]', C.ok, '같은 구조를 복제'],
  ];
  flow.forEach((f, i) => {
    const y = 3.5 + i * 0.84;
    card(s, { x: 0.7, y, w: 11.93, h: 0.7, border: f[2] });
    s.addText(f[0], { x: 1.02, y: y + 0.18, w: 2.5, h: 0.34, margin: 0, fontFace: F, fontSize: 12.5, bold: true, color: f[2] });
    s.addText(f[1], { x: 3.6, y: y + 0.18, w: 6.6, h: 0.34, margin: 0, fontFace: F, fontSize: 12, color: C.fg });
    s.addText(f[3], { x: 10.3, y: y + 0.18, w: 2.0, h: 0.34, margin: 0, fontFace: F, fontSize: 11, color: C.dim, align: 'right' });
  });

  s.addText('사람은 언제든 과거 UI를 다시 만진다 — HITL 시스템에서는 그게 설계 전제여야 한다.', {
    x: 0.7, y: 6.14, w: 11.93, h: 0.34, margin: 0, fontFace: F, fontSize: 13, bold: true, color: C.warn,
  });
  pageNo(s, n);
}

// ══════════════════════════════════════════════════════════
// 18. 회고 · 향후 확장
// ══════════════════════════════════════════════════════════
{
  const s = slide(); const n = num();
  title(s, '회고와 향후 확장');

  card(s, { x: 0.7, y: 1.78, w: 7.3, h: 4.4 });
  s.addText('배운 것', { x: 1.02, y: 1.98, w: 6.7, h: 0.34, margin: 0, fontFace: F, fontSize: 17, bold: true, color: C.ok });
  const learn = [
    ['측정하지 않았으면 쓰이지 않는 클래스를 그대로 안고 발표했을 것이다', '숫자가 오른 것과 나아진 것은 다르다. 클래스별로 쪼개 봐야 보인다'],
    ['제약이 설계를 이끌었다', '무료 티어 RPD 20이라는 벽을 만나 모델 비교 실험을 했고, 그 실험이 환각 한 건을 미리 잡았다'],
    ['정상 경로만 검증하면 놓친다', '사용자가 엉뚱한 버튼을 눌러서 발견된 결함이 있었다'],
  ];
  learn.forEach((l, i) => {
    const y = 2.5 + i * 1.24;
    badge(s, 1.02, y, String(i + 1), C.ok, 0.38);
    s.addText(l[0], { x: 1.56, y: y - 0.02, w: 6.2, h: 0.56, margin: 0, fontFace: F, fontSize: 13.5, bold: true, color: C.fg, lineSpacing: 19 });
    s.addText(l[1], { x: 1.56, y: y + 0.56, w: 6.2, h: 0.5, margin: 0, fontFace: F, fontSize: 11.5, color: C.dim, lineSpacing: 17 });
  });

  card(s, { x: 8.4, y: 1.78, w: 4.23, h: 4.4 });
  s.addText('향후 확장', { x: 8.72, y: 1.98, w: 3.6, h: 0.34, margin: 0, fontFace: F, fontSize: 17, bold: true, color: C.purp });
  const next = [
    '주문 DB 연동 — 📋 배지가 그 진입점',
    '승인 이력을 프롬프트 개선에 활용',
    '수정 지시 매칭을 텔레그램 답장으로',
    '다채널 확장 (카카오톡·인스타 DM)',
    '담당자별 배정과 협업',
  ];
  next.forEach((t, i) => {
    const y = 2.56 + i * 0.68;
    s.addText('▪', { x: 8.72, y, w: 0.24, h: 0.3, margin: 0, fontFace: F, fontSize: 12, color: C.purp });
    s.addText(t, { x: 9.0, y: y - 0.02, w: 3.4, h: 0.56, margin: 0, fontFace: F, fontSize: 12, color: C.fg, lineSpacing: 17 });
  });
  pageNo(s, n);
}

// ══════════════════════════════════════════════════════════
// 19. 마무리
// ══════════════════════════════════════════════════════════
{
  const s = slide();
  s.addText('AI를 빠르게 만드는 것보다,\n통제 가능하게 만드는 것이 실무의 문제다', {
    x: 0.9, y: 1.9, w: 11.5, h: 1.6, margin: 0,
    fontFace: F, fontSize: 32, bold: true, color: C.fg, lineSpacing: 46,
  });
  s.addText('그리고 통제 가능하게 만들면서도 실제로 빨라졌는지를 숫자로 확인했다', {
    x: 0.9, y: 3.6, w: 11.5, h: 0.4, margin: 0,
    fontFace: F, fontSize: 16, color: C.dim,
  });

  card(s, { x: 0.9, y: 4.34, w: 5.5, h: 1.2, border: C.ok });
  s.addText([
    { text: '94.0%', options: { fontSize: 30, bold: true, color: C.ok } },
    { text: '   vs   ', options: { fontSize: 15, color: C.dim } },
    { text: '34.0%', options: { fontSize: 22, color: C.bad } },
  ], { x: 1.22, y: 4.56, w: 4.9, h: 0.5, margin: 0, fontFace: F });
  s.addText('1차 승인률 · RAG vs 베이스라인', { x: 1.22, y: 5.1, w: 4.9, h: 0.3, margin: 0, fontFace: F, fontSize: 11, color: C.dim });

  s.addText('감사합니다', {
    x: 7.2, y: 4.42, w: 5.2, h: 0.6, margin: 0,
    fontFace: F, fontSize: 26, bold: true, color: C.fg, align: 'right',
  });
  s.addText('github.com/noviz-domino/replygate', {
    x: 7.2, y: 5.06, w: 5.2, h: 0.34, margin: 0,
    fontFace: F, fontSize: 12, color: C.blue, align: 'right',
  });
  s.addText(NAME, {
    x: 7.2, y: 5.42, w: 5.2, h: 0.3, margin: 0,
    fontFace: F, fontSize: 11, color: C.dim, align: 'right',
  });
}

p.writeFile({ fileName: process.argv[2] })
  .then(f => console.log('created:', f, '| slides:', N + 2));
