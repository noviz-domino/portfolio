# CLI 입구(entry point)
# 터미널에서 옵션을 받아, config를 읽고, 실험을 실행하거나 예상 비용만 계산한다.
#
# 사용 예:
#   python main.py --config configs/baseline.yaml --dry-run
#   python main.py --config configs/baseline.yaml --limit 3
#   python main.py --config configs/baseline.yaml

import argparse   # 터미널에서 넘어온 옵션(--config 등)을 읽어주는 표준 라이브러리
import json

import config     # YAML을 읽고 값이 올바른지 검증
import runner     # 실제 실험 실행 / 예상 비용 계산


def parse_args():
    # 이 프로그램이 어떤 옵션을 받을지 정의하고, 터미널에서 넘어온 값을 읽어서 돌려준다
    parser = argparse.ArgumentParser(description="RAG 실험 실행기")

    # required=True -> 이 옵션이 없으면 프로그램이 친절한 오류 메시지를 내고 종료한다
    parser.add_argument(
        "--config",
        required=True,
        help="실험 설정 파일 경로 (예: configs/baseline.yaml)",
    )
    # type=int -> 터미널에서 넘어온 "3"이라는 문자열을 숫자 3으로 바꿔준다
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="문항 수를 임시로 줄여서 실행 (코드가 끝까지 도는지 확인하는 smoke test용)",
    )
    # action="store_true" -> 값 없이 --dry-run 만 붙이면 True, 안 붙이면 False가 된다
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="API를 호출하지 않고 예상 호출 수만 계산해서 보여준다",
    )

    return parser.parse_args()


def main():
    args = parse_args()

    # config 파일을 읽고 검증한다 (여기서 .env의 API 키도 함께 불러온다)
    cfg = config.load_config(args.config)
    print(f"실험: {cfg['experiment_name']}  (config: {args.config})")

    if args.dry_run:
        # 하이픈이 있는 옵션(--dry-run)은 코드에서 언더스코어(args.dry_run)로 접근한다
        estimate = runner.estimate_cost(cfg, limit=args.limit)
        print("\n=== 예상 호출 수 (--dry-run, 실제 API 호출 없음) ===")
        print(json.dumps(estimate, ensure_ascii=False, indent=2))
        return   # 예상만 보여주고 실험은 실행하지 않고 끝낸다

    summary = runner.run_experiment(cfg, limit=args.limit)
    print("\n=== 실험 결과 요약 ===")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


# 이 파일을 python main.py 로 직접 실행했을 때만 main()을 부른다.
# (다른 파일에서 import할 때는 자동 실행되지 않게 막아주는 파이썬 관례)
if __name__ == "__main__":
    main()
