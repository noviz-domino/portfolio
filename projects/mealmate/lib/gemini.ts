import { GoogleGenAI } from '@google/genai'

// gemini-2.5-flash는 새로 발급한 키(신규 프로젝트)에서는 더 이상 호출이 안 된다
// (모델 목록에는 남아 있지만 실제 생성 요청은 404). gemini-3.5-flash로 교체.
export const MODEL = 'gemini-3.5-flash'

function getAI() {
  if (!process.env.GEMINI_API_KEY) throw new Error('GEMINI_API_KEY is missing')
  return new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY })
}

export async function generateJson({
  systemInstruction,
  contents,
  responseSchema,
}: {
  systemInstruction: string
  contents: string
  responseSchema: unknown
}) {
  const ai = getAI()
  const result = await ai.models.generateContent({
    model: MODEL,
    contents,
    config: {
      systemInstruction,
      temperature: 0.7,
      maxOutputTokens: 8192,
      responseMimeType: 'application/json',
      responseSchema,
      thinkingConfig: { thinkingBudget: 0 },
    },
  })
  const text = result.text
  if (!text) throw new Error('EMPTY_AI_RESPONSE')
  return JSON.parse(text)
}