const MODEL = "gemini-flash-lite-latest";

// 목록 카드에 보여줄 한두 줄 요약을 만든다.
// 실패해도 맛집 저장 자체는 계속되어야 하므로, 여기서는 예외를 던지지 않고 null을 돌려준다.
export async function summarizeMemo(memo: string): Promise<string | null> {
  const trimmed = memo.trim();

  if (!trimmed) {
    return null;
  }

  const apiKey = process.env.GEMINI_API_KEY;

  if (!apiKey) {
    return null;
  }

  const prompt = `다음은 사용자가 맛집에 대해 적어둔 메모다. 목록 화면 카드에 넣을 한 줄 요약을 만들어줘.

규칙:
- 한 문장, 20자 안팎으로 짧게.
- 존댓말 말고 평서체로.
- 현금 여부·마감 시간처럼 가장 중요한 정보 하나만 남기고 나머지는 과감히 생략해.
- 원본에 없는 내용을 지어내지 마.
- 설명하지 말고 요약 문장만 출력해.

메모: ${trimmed}`;

  try {
    const res = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/${MODEL}:generateContent?key=${apiKey}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          contents: [{ parts: [{ text: prompt }] }],
        }),
      },
    );

    if (!res.ok) {
      return null;
    }

    const data = await res.json();
    const text = data.candidates?.[0]?.content?.parts?.[0]?.text?.trim();

    return text || null;
  } catch {
    return null;
  }
}
