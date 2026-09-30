"""API 키를 담은 .env를 읽어 환경 변수로 올린다.

.env 위치를 한 곳에서만 정하기 위해 따로 뒀다. 파일마다 경로를 적으면
한 군데만 고쳐도 나머지가 어긋난다.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# 이 파일은 src/ 안에 있으므로, 두 단계 올라가면 프로젝트 루트다
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_env() -> None:
    """.env를 찾아 읽는다.

    기본 위치는 프로젝트 루트의 .env다.
    다른 곳에 두었다면 환경 변수 TAX_PREP_ENV에 그 경로를 넣으면 된다.

        set TAX_PREP_ENV=D:\\keys\\my.env     (Windows)
        export TAX_PREP_ENV=~/keys/my.env     (macOS/Linux)
    """
    env_path = os.getenv("TAX_PREP_ENV") or PROJECT_ROOT / ".env"
    load_dotenv(dotenv_path=env_path)
