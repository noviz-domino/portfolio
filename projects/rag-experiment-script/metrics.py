# 검색(retrieval) 품질을 측정하는 지표 함수 모음
# docs: retriever가 반환한 Document 리스트, case: golden set의 문항 하나(dict)


def file_hit_at_k(docs, case, k):
    # 상위 k개 문서 중에 "정답 파일"이 하나라도 있으면 1, 없으면 0
    return int(any(doc.metadata["source"] == case["target_file_name"] for doc in docs[:k]))
    # docs[:k] -> 리스트 슬라이싱, 앞에서부터 k개만 잘라낸다
    # any(...) -> 괄호 안 제너레이터 중 하나라도 True면 True를 반환
    # int(True/False) -> 1/0으로 변환해서 나중에 평균(비율) 계산이 쉽게 만든다


def page_hit_at_k(docs, case, k):
    # 상위 k개 문서 중에 "정답 파일 + 정답 페이지"가 정확히 일치하는 게 있으면 1, 없으면 0
    return int(any(
        doc.metadata["source"] == case["target_file_name"]
        and doc.metadata["page_no"] == case["target_page_no"]
        for doc in docs[:k]
    ))
    # file_hit_at_k보다 더 엄격한 기준: 파일명뿐 아니라 페이지 번호까지 맞아야 정답 인정


def reciprocal_rank(docs, case):
    # MRR(Mean Reciprocal Rank) 계산에 쓰는 "역순위" 하나를 구한다
    for rank, doc in enumerate(docs, start=1):
        # enumerate(docs, start=1) -> (순위, 문서) 쌍을 1등부터 순서대로 뽑아준다
        if (
            doc.metadata["source"] == case["target_file_name"]
            and doc.metadata["page_no"] == case["target_page_no"]
        ):
            return 1 / rank
            # 정답을 몇 번째 순위에서 처음 찾았는지에 따라 1/순위를 반환
            # 1등에서 찾으면 1.0, 2등이면 0.5, 3등이면 0.333... 식으로 점점 작아진다
    return 0.0
    # 끝까지 못 찾았으면(정답이 검색 결과에 아예 없으면) 0.0
