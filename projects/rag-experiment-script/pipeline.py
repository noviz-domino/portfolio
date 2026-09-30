# 임베딩 API 호출, 벡터스토어(Chroma) 생성, retriever 생성 등
# "실제 검색 엔진을 만드는" 부분을 전부 담당하는 모듈

import time                    # 배치 사이 대기(sleep)에 사용
from pathlib import Path       # 파일 경로를 다루는 표준 라이브러리 객체

import chromadb                                                    # 벡터 DB(Chroma) 클라이언트
from langchain_chroma import Chroma                                 # LangChain에서 Chroma를 다루는 래퍼(wrapper)
from langchain_community.document_loaders import PyPDFLoader        # PDF를 페이지 단위 Document로 읽어주는 로더
from langchain_community.retrievers import BM25Retriever            # 키워드 기반 검색기(BM25 알고리즘)
from langchain_classic.retrievers import EnsembleRetriever           # 여러 retriever를 섞어서 쓰는 하이브리드 검색기
from langchain_google_genai import GoogleGenerativeAIEmbeddings      # 구글 Gemini 임베딩 모델
from langchain_text_splitters import RecursiveCharacterTextSplitter  # 긴 텍스트를 청크 단위로 자르는 도구

# kiwipiepy(한국어 형태소 분석기)는 bm25/hybrid 전략에서만 쓰이므로 여기서 import하지 않는다.
# 파일 맨 위에서 import하면 그 라이브러리가 없을 때 similarity/mmr 실험조차 실행이 안 되기 때문에,
# 실제로 필요한 kiwi_tokenize() 함수 안에서 import한다(지연 임포트, lazy import).


def build_embeddings(cfg):
    # 임베딩 모델을 만들면서, 429(요청 과다) 발생 시 SDK가 알아서 재시도하도록 클라이언트를 교체한다.
    # 10번 노트북의 "429 exhausted 해결" 셀과 같은 방식이며, 우리가 직접 만든 retry_on_429보다
    # 나은 점은 (1) 이 클라이언트를 쓰는 모든 호출에 자동 적용되어 감싸는 걸 빼먹을 위험이 없고
    # (2) jitter로 재시도 시점을 흩어서 여러 요청이 동시에 다시 몰리는 것을 막는다는 점이다.
    from google import genai
    from google.genai.types import HttpOptions, HttpRetryOptions

    embeddings = GoogleGenerativeAIEmbeddings(model=cfg["models"]["embedding"])
    retry = cfg["pacing"]
    embeddings.client = genai.Client(
        http_options=HttpOptions(
            retry_options=HttpRetryOptions(
                attempts=retry.get("retry_attempts", 10),      # 최초 요청 포함 총 시도 횟수
                initial_delay=retry.get("retry_initial_sec", 2.0),  # 첫 재시도 전 대기
                max_delay=retry.get("retry_max_sec", 120.0),   # 대기 시간 상한
                exp_base=2,                                     # 2초 → 4초 → 8초 순으로 증가
                jitter=1.0,                                     # 대기에 무작위 지연을 섞어 요청을 분산
            )
        ),
    )
    return embeddings


class CostCounter:
    # 실험 하나를 진행하는 동안 API 호출 횟수/토큰 수를 누적해서 세는 클래스

    def __init__(self):
        # 인스턴스가 만들어질 때 카운터를 전부 0으로 초기화한다
        self.embedding_requests = 0   # 임베딩 API를 몇 번 호출했는지
        self.embedding_tokens = 0     # 임베딩에 쓰인 토큰 수 (추정치, 실제 API 응답값이 아님)
        self.llm_requests = 0         # LLM(생성/채점/rerank) API를 몇 번 호출했는지
        self.llm_tokens = 0           # LLM에 쓰인 토큰 수 (추정치)

    def add_embedding(self, requests=1, tokens=0):
        # 임베딩 호출 1건이 끝날 때마다 호출해서 누적한다
        self.embedding_requests += requests
        self.embedding_tokens += tokens

    def add_llm(self, requests=1, tokens=0):
        # LLM 호출 1건이 끝날 때마다 호출해서 누적한다
        self.llm_requests += requests
        self.llm_tokens += tokens

    def as_dict(self):
        # 누적된 4개 값을 summary.json에 바로 넣을 수 있는 dict 형태로 반환
        return {
            "embedding_requests": self.embedding_requests,
            "embedding_tokens": self.embedding_tokens,
            "llm_requests": self.llm_requests,
            "llm_tokens": self.llm_tokens,
        }


def retry_on_429(func, max_retries, first_wait_sec=10):
    # func()를 실행하고, 429(요청 과다) 에러가 나면 대기 시간을 2배씩 늘려가며 재시도한다
    wait_sec = first_wait_sec   # 이번에 실패하면 몇 초 기다릴지 (재시도할 때마다 2배로 커진다)
    for attempt in range(1, max_retries + 1):
        # range(1, max_retries + 1) -> 1번째 시도부터 max_retries번째 시도까지 반복
        try:
            return func()
            # 성공하면 바로 결과를 반환하고 함수를 끝낸다
        except Exception as e:
            # "429"나 "RESOURCE_EXHAUSTED"라는 문자열이 에러 메시지에 있으면 API 한도 초과로 판단
            is_rate_limit = ("429" in str(e)) or ("RESOURCE_EXHAUSTED" in str(e))
            if not is_rate_limit:
                raise
                # 한도 초과가 아닌 다른 에러(예: 코드 버그)는 재시도하지 않고 즉시 그대로 올린다
            if attempt == max_retries:
                raise
                # 마지막 시도에서도 실패했다면 더 이상 기다리지 않고 에러를 그대로 올린다
            print(f"429 에러 발생 (시도 {attempt}/{max_retries}), {wait_sec}초 대기 후 재시도합니다.")
            time.sleep(wait_sec)   # 지정된 초만큼 실행을 멈춘다
            wait_sec *= 2          # 다음에 또 실패하면 대기 시간을 2배로 늘린다 (지수 백오프)


def load_and_chunk(cfg):
    # 설정(cfg)에 적힌 PDF 폴더를 읽어서 페이지 단위로 로드한 뒤, 지정된 크기로 청크를 나눈다
    pdf_dir = Path(cfg["data"]["pdf_dir"])   # 문자열 경로를 Path 객체로 바꿔서 다루기 쉽게 만든다

    page_documents = []   # 모든 PDF의 모든 페이지를 담을 빈 리스트
    for pdf_path in sorted(pdf_dir.glob("*.pdf")):
        # pdf_dir.glob("*.pdf") -> 폴더 안의 .pdf 파일들을 찾아준다, sorted()로 항상 같은 순서 보장
        pages = PyPDFLoader(pdf_path).load()   # PDF 한 개를 페이지 단위 Document 리스트로 읽는다
        for page in pages:
            # 전체 경로 대신 파일명만 남긴다 (예: "C:/.../a.pdf" -> "a.pdf")
            page.metadata["source"] = Path(page.metadata["source"]).name
            # PyPDFLoader의 page 번호는 0부터 시작하므로 사람이 읽기 편하게 1부터 시작하도록 +1
            page.metadata["page_no"] = page.metadata["page"] + 1
        page_documents.extend(pages)   # extend -> 리스트 안의 원소들을 낱개로 풀어서 뒤에 이어붙인다

    # 청크 크기(size)와 겹침(overlap)은 cfg에서 읽어온 값을 그대로 사용한다
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=cfg["chunk"]["size"],
        chunk_overlap=cfg["chunk"]["overlap"],
    )
    documents = splitter.split_documents(page_documents)   # 페이지들을 작은 청크들로 잘게 나눈다

    # EnsembleRetriever(hybrid 전략)가 청크를 구분할 때 쓸 고유 id를 각 청크에 붙인다
    for index, doc in enumerate(documents):
        source = doc.metadata["source"]
        page_no = doc.metadata["page_no"]
        doc.metadata["chunk_id"] = f"{source}:{page_no}:{index}"
        # f"{...}" -> f-string, 문자열 안에 변수 값을 그대로 끼워 넣는 문법

    return documents


def collection_name(cfg):
    # Chroma 컬렉션 이름을 만든다. chunk.size / chunk.overlap 두 값에만 의존한다.
    # 이유: 청크 나누는 방식(크기/겹침)이 같으면 문서 조각(corpus)도 동일하므로,
    # 검색 전략(similarity/mmr/...)이나 k, rerank 여부가 달라도 임베딩 결과를 그대로 재사용할 수 있다.
    # 즉 실험마다 매번 새로 임베딩하지 않고 비용을 아끼기 위한 이름 규칙이다.
    size = cfg["chunk"]["size"]
    overlap = cfg["chunk"]["overlap"]
    return f"public_c{size}_o{overlap}"


def corpus_hash(documents):
    # 청크 본문을 전부 이어붙여 짧은 지문(hash)으로 요약한다.
    # 글자 하나만 달라져도 완전히 다른 값이 나오므로, PDF가 바뀌었는지 / 청킹 방식이 바뀌었는지를
    # 항목별로 검사하지 않고 "최종 결과물 하나"로 비교할 수 있다.
    import hashlib

    joined = "\n".join(doc.page_content for doc in documents)
    # encode()는 문자열을 바이트로 바꾼다(해시 함수는 바이트만 받는다)
    # hexdigest()[:12]는 결과 지문 중 앞 12자만 쓴다(전체는 32자, 구분용으로는 충분)
    return hashlib.md5(joined.encode("utf-8")).hexdigest()[:12]


def check_collection_identity(client, name, cfg, documents):
    # 저장된 컬렉션이 "지금 설정으로 만든 것"인지 확인한다.
    # 컬렉션 이름에는 청크 크기/겹침만 들어가므로, 임베딩 모델이 바뀌거나 문서 내용이 바뀐 것은
    # 이름과 개수만으로는 알 수 없다. 그래서 만들 때 기록해둔 메타데이터와 비교한다.
    # 반환값: (재사용 가능 여부, 사람이 읽을 이유)
    stored = client.get_collection(name).metadata or {}

    if not stored.get("embedding_model"):
        # 안전장치를 넣기 전에 만들어진 컬렉션에는 이 정보가 없다.
        # 이미 만들어진 임베딩을 버리면 재임베딩 비용이 크므로, 경고만 남기고 통과시킨다.
        return True, "메타데이터 없음(안전장치 도입 이전에 만들어진 컬렉션) - 검증 없이 재사용"

    if stored.get("embedding_model") != cfg["models"]["embedding"]:
        return False, (
            f"임베딩 모델이 다름: 저장된 값 {stored.get('embedding_model')} "
            f"vs 지금 설정 {cfg['models']['embedding']}"
        )

    now_hash = corpus_hash(documents)
    if stored.get("corpus_hash") != now_hash:
        return False, (
            f"문서 내용이 다름: 저장된 지문 {stored.get('corpus_hash')} vs 지금 지문 {now_hash}"
        )

    return True, "모델과 문서 지문이 모두 일치"


def build_vectorstore(cfg, documents, counter):
    # PersistentClient -> 디스크에 저장되는 Chroma 클라이언트를 만든다 (재실행해도 데이터가 남아있음)
    client = chromadb.PersistentClient(path="chroma_db")
    name = collection_name(cfg)

    existing_names = [c.name for c in client.list_collections()]
    pending = documents   # 임베딩해야 할 문서. 기본은 전체이고, 아래에서 상황에 따라 줄어든다.

    if name in existing_names:
        stored = client.get_collection(name).count()   # 이미 저장된 문서 수

        if stored == len(documents):
            # 있어야 할 개수만큼 "전부" 들어있을 때만 완성된 것으로 보고 재사용한다.
            # count() > 0 으로만 판단하면 중단된 컬렉션을 완성본으로 착각해서,
            # 문서 일부가 빠진 상태로 실험이 돌아가면서도 오류가 나지 않는다.
            # (2026-09-07에 chunk-500이 390/552 상태로 재사용되어 결과가 오염된 사례)
            # 개수가 맞아도 "같은 모델·같은 문서로 만든 것인지" 한 번 더 확인한다.
            # 개수만 보면 모델을 바꾼 경우를 잡지 못한다(두 임베딩 모델의 차원이 같으면 오류도 안 남).
            reusable, reason = check_collection_identity(client, name, cfg, documents)
            if reusable:
                print(f"기존 컬렉션 '{name}' 재사용 (문서 {stored}개), 임베딩 생략 - {reason}")
                embeddings = build_embeddings(cfg)
                return Chroma(client=client, collection_name=name, embedding_function=embeddings)

            # 다른 조건으로 만들어진 컬렉션이므로 버리고 처음부터 다시 만든다
            print(f"컬렉션 '{name}'을 재사용할 수 없습니다 - {reason}")
            print("해당 컬렉션을 삭제하고 새로 임베딩합니다.")
            client.delete_collection(name)
            pending = documents

        if stored < len(documents):
            # 중간에 중단된 상태. 문서를 항상 같은 순서로 넣으므로 앞의 stored개는 이미 들어가 있다.
            # 따라서 documents[stored:] 만 이어서 임베딩하면 된다(비용 절약).
            print(f"부분 저장 감지: {stored}/{len(documents)}개. 남은 {len(documents) - stored}개만 이어서 임베딩합니다.")
            pending = documents[stored:]
        else:
            # 저장된 개수가 예상보다 많다면 다른 문서로 만들어진 컬렉션이므로 지우고 새로 만든다
            print(f"컬렉션 '{name}' 문서 수({stored})가 예상({len(documents)})보다 많아 삭제 후 재생성합니다.")
            client.delete_collection(name)

    # 여기까지 왔다면 (전체 또는 남은 일부를) 새로 임베딩해야 하는 경우
    embeddings = build_embeddings(cfg)
    vectorstore = Chroma(
        client=client,
        collection_name=name,
        embedding_function=embeddings,
        # 컬렉션을 처음 만들 때 "무엇으로 만든 것인지"를 함께 기록해둔다.
        # 다음 실행에서 check_collection_identity()가 이 값을 보고 재사용 여부를 판단한다.
        collection_metadata={
            "embedding_model": cfg["models"]["embedding"],
            "corpus_hash": corpus_hash(documents),
            "chunk_size": cfg["chunk"]["size"],
            "chunk_overlap": cfg["chunk"]["overlap"],
        },
    )

    batch_size = cfg["pacing"]["embed_batch_size"]     # 한 번에 임베딩할 문서 개수
    sleep_sec = cfg["pacing"]["embed_sleep_sec"]       # 배치 사이 대기 시간(분당 호출 수 제한 대응)
    max_retries = cfg["pacing"]["max_retries"]         # 429 재시도 최대 횟수
    total = len(pending)   # 전체가 아니라 "이번에 임베딩할 문서 수"

    for start in range(0, total, batch_size):
        # range(0, total, batch_size) -> 0, batch_size, batch_size*2, ... 처럼 batch_size씩 건너뛴다
        batch = pending[start:start + batch_size]   # 이번에 임베딩할 문서 묶음(슬라이싱)

        # 429가 나면 retry_on_429가 알아서 대기 후 재시도해준다
        retry_on_429(lambda: vectorstore.add_documents(batch), max_retries)

        # 토큰 수는 실제 API 응답이 아니라 "글자 수 // 2"로 어림잡은 추정치일 뿐이다 (한국어는 대략 2글자당 1토큰)
        estimated_tokens = sum(len(doc.page_content) // 2 for doc in batch)
        counter.add_embedding(requests=1, tokens=estimated_tokens)

        done = min(start + batch_size, total)
        print(f"임베딩 진행: {done}/{total}")

        if done < total:
            # 마지막 배치가 끝난 뒤에는 더 기다릴 필요가 없으므로 sleep을 건너뛴다
            time.sleep(sleep_sec)

    return vectorstore


# Kiwi 인스턴스는 모듈이 import되는 순간이 아니라, 실제로 bm25/hybrid를 쓸 때만 생성한다
# (모델 로딩 비용이 있으므로 similarity/mmr만 쓰는 실험은 이 비용을 치르지 않게 하기 위함)
_kiwi = None


def kiwi_tokenize(text):
    # 한국어 문장을 BM25가 쓸 수 있는 토큰(단어) 리스트로 바꾼다
    global _kiwi
    if _kiwi is None:
        # 이 함수가 처음 호출될 때만 라이브러리를 불러오고 객체를 만든다.
        # bm25/hybrid 실험을 하려면 먼저 pip install kiwipiepy 가 필요하다.
        from kiwipiepy import Kiwi
        _kiwi = Kiwi()   # 최초 호출 시에만 한 번 생성 (지연 생성, lazy loading)

    tokens = _kiwi.tokenize(text)   # 형태소 단위로 문장을 쪼갠다
    return [
        token.form.lower()
        for token in tokens
        # N(체언/명사류), V(용언/동사류), M(수식언), X(접사 등)으로 시작하거나
        # SL(외국어), SN(숫자)인 토큰만 남기고 조사/어미 등은 버린다
        if token.tag.startswith(("N", "V", "M", "X")) or token.tag in {"SL", "SN"}
    ]


def build_retriever(cfg, vectorstore, documents):
    # cfg의 search.strategy 값에 따라 서로 다른 종류의 retriever를 만들어 반환한다
    strategy = cfg["search"]["strategy"]
    k = cfg["search"]["k"]

    if strategy == "similarity":
        # 벡터 거리(코사인 유사도 등) 기준으로 가장 가까운 k개를 뽑는다
        return vectorstore.as_retriever(search_kwargs={"k": k})

    if strategy == "mmr":
        # MMR(Maximal Marginal Relevance) -> 관련성과 다양성을 함께 고려해서 뽑는다
        return vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": k,
                "fetch_k": cfg["search"]["mmr"]["fetch_k"],
                "lambda_mult": cfg["search"]["mmr"]["lambda_mult"],
            },
        )

    if strategy == "bm25":
        # 임베딩 API를 전혀 쓰지 않는 키워드 기반 검색기. 한국어 토큰화에 kiwi_tokenize를 사용한다
        return BM25Retriever.from_documents(documents, preprocess_func=kiwi_tokenize, k=k)

    if strategy == "hybrid":
        # 벡터 검색 + BM25 검색을 weights 비율로 섞는다
        vector_retriever = vectorstore.as_retriever(search_kwargs={"k": k})
        bm25_retriever = BM25Retriever.from_documents(documents, preprocess_func=kiwi_tokenize, k=k)
        return EnsembleRetriever(
            retrievers=[vector_retriever, bm25_retriever],
            weights=cfg["search"]["hybrid"]["weights"],
            id_key="chunk_id",   # load_and_chunk에서 각 청크에 붙여둔 고유 id를 기준으로 중복을 걸러낸다
        )

    # 위 4가지(similarity/mmr/bm25/hybrid) 중 어디에도 해당하지 않으면 설정 오류이므로 명확히 알려준다
    raise ValueError(f"알 수 없는 search.strategy 값입니다: {strategy!r} (similarity/mmr/bm25/hybrid 중 하나여야 합니다)")
