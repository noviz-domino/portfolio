from app.rag.retrieval import reciprocal_rank_fusion, simple_korean_tokenize


def test_rrf_agreement_boosts_shared_top_result():
    dense = ["a", "b", "c"]
    sparse = ["a", "c", "b"]
    fused = reciprocal_rank_fusion([dense, sparse], k=60)
    fused_ids = [doc_id for doc_id, _ in fused]

    # "a"가 두 경로 모두에서 1위이므로 융합 결과에서도 1위여야 한다.
    assert fused_ids[0] == "a"


def test_rrf_document_only_in_one_list_still_scored():
    dense = ["a", "b"]
    sparse = ["c"]
    fused = reciprocal_rank_fusion([dense, sparse], k=60)
    fused_ids = {doc_id for doc_id, _ in fused}
    assert fused_ids == {"a", "b", "c"}


def test_rrf_matches_manual_formula():
    dense = ["x", "y"]
    sparse = ["y", "x"]
    k = 60
    fused = dict(reciprocal_rank_fusion([dense, sparse], k=k))

    expected_x = 1 / (k + 1) + 1 / (k + 2)
    expected_y = 1 / (k + 2) + 1 / (k + 1)
    assert fused["x"] == expected_x
    assert fused["y"] == expected_y


def test_simple_korean_tokenize_strips_common_josa():
    tokens = simple_korean_tokenize("연장근로는 제56조에 따라 계산한다")
    assert "제56조" in tokens or "제56조에" in tokens
    assert any(t.startswith("연장근로") for t in tokens)
