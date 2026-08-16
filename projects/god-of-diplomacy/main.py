import os

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

app = FastAPI()
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

MODEL = "gemini-3.5-flash"

SYSTEM_INSTRUCTION = """당신은 2026년 8월 대한민국 대통령의 정치·외교 상호작용을 이끄는 'Game Master'다.

[연출 및 작성 규칙]
1. 플레이어는 대한민국 대통령.
2. 플레이어의 지시에 따라 미·중·일·북 등 주변국 정상의 생생한 반응, 대화(" "), 과장되고 스펙터클한 국제정세 파동을 몰입감 있게 작성. (1~3문장 이내)
3. 상황의 긴장감과 유머, 극적인 연출을 적극 활용.
4. 플레이어의 행동으로 인해 국정 지표에 의미 있는 변화 발생시 답변 맨 마지막 줄에 아래 형식을 선택적으로 제공:
   [지표변화: 지지율(+-N), 경제(+-N), 정치력(+-N)]
"""


class Stats(BaseModel):
    지지율: int
    경제: int
    정치력: int


class TurnRequest(BaseModel):
    stats: Stats
    lastSituation: str
    userInput: str


@app.get("/")
def index():
    return FileResponse("index.html")


@app.post("/api/turn")
def turn(req: TurnRequest):
    user_input = req.userInput.strip()
    if not user_input:
        return {"text": "(대통령님, 지시 없이는 상황이 진행되지 않습니다. 명령을 내려주세요.)"}

    prompt = f"""[현재 지표]
지지율: {req.stats.지지율}
경제: {req.stats.경제}
정치력: {req.stats.정치력}

[직전 상황]
{req.lastSituation}

[대통령의 지시]
{user_input}
"""

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(system_instruction=SYSTEM_INSTRUCTION),
        )
        return {"text": response.text}
    except Exception as e:
        return {"text": f"(상황실 통신 장애로 응답을 받지 못했습니다: {e})"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
