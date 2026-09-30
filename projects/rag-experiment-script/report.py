# outputs/ 폴더 아래 모든 실험의 summary.json을 모아서 비교 표를 출력하는 모듈

import json                # json 파일을 읽기 위한 표준 라이브러리
from pathlib import Path   # 폴더/파일 경로를 다루는 표준 라이브러리 객체

# 표에 출력할 컬럼 이름들 (왼쪽부터 순서대로)
# generation 관련 4개 컬럼(인용정확 ~ 생성시간ms)은 build_report()에서 필요할 때만 뒤에 덧붙인다
BASE_COLUMNS = [
    "실험명", "page_hit_1", "page_hit_3", "page_hit_5",
    "file_hit_1", "mrr", "임베딩호출", "LLM호출", "소요시간(초)",
]
GENERATION_COLUMNS = ["인용정확", "정답인용", "Judge평균", "생성시간ms"]


def build_report(result_dir="outputs"):
    # result_dir 아래에 있는 모든 실험의 summary.json을 찾아서 한 줄씩 정리한 표를 만들고 출력한다
    base = Path(result_dir)

    if not base.exists():
        # outputs 폴더 자체가 없으면(아직 실험을 한 번도 안 돌렸으면) 에러 대신 안내 메시지만 출력
        print(f"'{result_dir}' 폴더가 없습니다. 먼저 실험(runner.py)을 실행해서 결과를 만들어주세요.")
        return

    summary_paths = sorted(base.glob("*/summary.json"))
    # base.glob("*/summary.json") -> outputs 바로 아래 폴더들 각각에 있는 summary.json을 전부 찾는다

    if not summary_paths:
        print(f"'{result_dir}' 안에 summary.json이 하나도 없습니다. 실험 결과가 아직 없습니다.")
        return

    all_data = []   # 각 실험의 summary.json 내용(dict)을 그대로 담아둔다 (generation 유무 판단에 재사용)
    for path in summary_paths:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)   # summary.json 내용을 dict로 읽어온다
        data.setdefault("experiment_name", path.parent.name)   # 이름이 없으면 폴더 이름으로 대신한다
        all_data.append(data)

    # 실험 중 하나라도 "generation" 블록을 가지고 있으면, 표에 generation 컬럼 4개를 추가한다
    has_generation = any("generation" in data for data in all_data)
    columns = BASE_COLUMNS + GENERATION_COLUMNS if has_generation else BASE_COLUMNS

    rows = []   # 표에 들어갈 한 줄(실험 하나)씩 담을 리스트
    for data in all_data:
        quality = data.get("quality", {})
        cost = data.get("cost", {})
        time_info = data.get("time", {})

        row = [
            data["experiment_name"],
            f"{quality.get('page_hit_1', 0):.3f}",
            f"{quality.get('page_hit_3', 0):.3f}",
            f"{quality.get('page_hit_5', 0):.3f}",
            f"{quality.get('file_hit_1', 0):.3f}",
            f"{quality.get('mrr', 0):.3f}",
            str(cost.get("embedding_requests", 0)),
            str(cost.get("llm_requests", 0)),
            f"{time_info.get('total_sec', 0):.1f}",
        ]

        if has_generation:
            generation = data.get("generation")   # 이 실험이 생성 단계를 안 돌렸으면 None
            if generation is None:
                # 생성을 안 돌린 실험은 표에서 "-"로 표시해서 값이 아예 없다는 것을 분명히 한다
                row += ["-", "-", "-", "-"]
            else:
                row += [
                    f"{generation.get('valid_citation', 0):.3f}",
                    f"{generation.get('relevant_citation', 0):.3f}",
                    # judge_average는 run_judge까지 켰을 때만 있으므로, 없으면 "-"로 표시한다
                    f"{generation['judge_average']:.2f}" if "judge_average" in generation else "-",
                    f"{generation.get('generation_latency_ms', 0):.0f}",
                ]

        rows.append(row)

    # 실험명(각 row의 첫 번째 값) 기준으로 정렬해서 항상 같은 순서로 보이게 한다
    rows.sort(key=lambda r: r[0])

    _print_table(columns, rows)


def _print_table(columns, rows):
    # 컬럼 이름과 값들의 폭을 맞춰서 보기 좋게 정렬된 표를 콘솔에 출력한다
    all_rows = [columns] + rows   # 헤더도 폭 계산에 포함시키기 위해 맨 위에 추가

    # 각 컬럼(세로줄)마다 그 컬럼에서 가장 긴 문자열의 길이를 구한다
    widths = []
    for col_index in range(len(columns)):
        widths.append(max(len(row[col_index]) for row in all_rows))

    def format_row(row):
        # 각 칸을 해당 컬럼 폭만큼 왼쪽 정렬(ljust)로 채워서 " | "로 이어붙인다
        return " | ".join(cell.ljust(widths[i]) for i, cell in enumerate(row))

    header_line = format_row(columns)
    print(header_line)
    print("-" * len(header_line))   # 헤더 밑에 구분선을 긋는다
    for row in rows:
        print(format_row(row))


if __name__ == "__main__":
    # python report.py 로 직접 실행했을 때만 동작 (다른 파일에서 import할 때는 실행 안 됨)
    build_report()
