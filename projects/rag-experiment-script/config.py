# YAML 설정 파일을 읽고, 값이 올바른지 검사(validate)하는 모듈

from pathlib import Path         # 파일/폴더 존재 여부 확인에 사용
import yaml                      # YAML 파일을 파이썬 dict로 읽어주는 라이브러리
from dotenv import load_dotenv   # .env 파일 안의 환경변수(API 키 등)를 불러오는 함수

# .env 파일은 두 저장소(aim-ai-agent, aim-ai-agent-practice)의 한 단계 위, 항상 이 절대경로에 있다
load_dotenv(dotenv_path=r"C:\Users\HOME\Desktop\260811\.env")

REQUIRED_KEYS = ["experiment_name", "data", "models", "chunk", "search", "rerank", "evaluation", "pacing"]
VALID_STRATEGIES = ["similarity", "mmr", "bm25", "hybrid"]


def load_config(path):
    # YAML 설정 파일을 읽어서 dict로 반환하고, 형식이 잘못됐으면 바로 에러를 낸다
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)   # YAML 텍스트를 파이썬 dict/list/값으로 변환

    # 1) 최상위 필수 키가 전부 있는지 확인
    for key in REQUIRED_KEYS:
        if key not in cfg:
            raise ValueError(f"설정 파일에 필수 항목 '{key}'가 없습니다: {path}")

    # 2) search.strategy 값이 우리가 아는 4가지 중 하나인지 확인
    strategy = cfg["search"]["strategy"]
    if strategy not in VALID_STRATEGIES:
        raise ValueError(
            f"search.strategy 값이 잘못됐습니다: {strategy!r} (다음 중 하나여야 합니다: {VALID_STRATEGIES})"
        )

    # 3) 데이터 경로들이 실제로 존재하는지 확인 (오타로 인한 FileNotFoundError를 미리 막는다)
    pdf_dir = Path(cfg["data"]["pdf_dir"])
    if not pdf_dir.exists():
        raise ValueError(f"data.pdf_dir 경로가 존재하지 않습니다: {pdf_dir}")

    golden_set = Path(cfg["data"]["golden_set"])
    if not golden_set.exists():
        raise ValueError(f"data.golden_set 경로가 존재하지 않습니다: {golden_set}")

    # 4) 청크 크기가 겹침보다 커야 한다 (같거나 작으면 청크가 무한히 겹치거나 앞으로 못 나간다)
    if cfg["chunk"]["size"] <= cfg["chunk"]["overlap"]:
        raise ValueError(
            f"chunk.size({cfg['chunk']['size']})는 chunk.overlap({cfg['chunk']['overlap']})보다 커야 합니다"
        )

    return cfg
