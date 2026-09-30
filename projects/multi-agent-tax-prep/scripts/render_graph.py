"""그래프 구조를 이미지 파일로 저장한다.

LangGraph가 그려주는 Mermaid 다이어그램을 PNG로 받아 JPG로 변환한다.
LLM을 호출하지 않으므로 API 비용이 들지 않는다. (그래프를 조립만 하고 실행은 안 함)

실행:
    python scripts/render_graph.py
"""

import sys
from io import BytesIO
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# src 폴더를 import 경로에 추가한다. scripts/에서 실행하므로 이 줄이 없으면 graph를 못 찾는다.
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from env import load_env  # noqa: E402  (sys.path를 손본 뒤에 import해야 한다)
from graph import build_graph  # noqa: E402

load_env()

OUTPUT_DIR = PROJECT_ROOT / "docs"
OUTPUT_DIR.mkdir(exist_ok=True)


def main() -> None:
    graph = build_graph()

    # draw_mermaid_png()는 mermaid.ink 서버에 그림을 요청하므로 인터넷이 필요하다
    png_bytes = graph.get_graph().draw_mermaid_png()

    png_path = OUTPUT_DIR / "graph.png"
    png_path.write_bytes(png_bytes)
    print(f"PNG 저장: {png_path}")

    try:
        from PIL import Image
    except ImportError:
        print("Pillow가 없어 JPG 변환을 건너뜁니다. 설치: pip install Pillow")
        return

    image = Image.open(BytesIO(png_bytes))

    # JPG는 투명 배경을 지원하지 않는다. 흰 배경을 깔고 그 위에 합성한다.
    if image.mode in ("RGBA", "LA", "P"):
        image = image.convert("RGBA")
        background = Image.new("RGB", image.size, (255, 255, 255))
        background.paste(image, mask=image.split()[-1])  # 알파 채널을 마스크로 사용
        image = background
    else:
        image = image.convert("RGB")

    jpg_path = OUTPUT_DIR / "graph.jpg"
    image.save(jpg_path, "JPEG", quality=95)
    print(f"JPG 저장: {jpg_path}")


if __name__ == "__main__":
    main()
