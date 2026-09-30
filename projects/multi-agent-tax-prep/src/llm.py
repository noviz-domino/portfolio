"""LLM 객체를 만드는 곳.

모델 이름을 파일마다 적으면 바꿀 때 한 군데를 빠뜨린다. 여기 한 곳만 둔다.

temperature는 넘기지 않는다. gemini-3.5-flash-lite는 샘플링 설정을 고정값으로 쓰기 때문에
지정해도 무시되고, 코드에 남겨두면 "적용되고 있다"고 오해하게 된다.
"""

from langchain_google_genai import ChatGoogleGenerativeAI

MODEL_NAME = "gemini-3.5-flash-lite"


def get_llm() -> ChatGoogleGenerativeAI:
    """일반 텍스트 생성용 LLM."""
    return ChatGoogleGenerativeAI(model=MODEL_NAME)


def get_structured_llm(schema):
    """구조화된 출력을 돌려주는 LLM.

    schema로 넘긴 Pydantic 클래스 형태에 맞춰 응답이 온다.
    자유 문장을 받아 파싱할 필요가 없어진다.
    """
    return get_llm().with_structured_output(schema)
