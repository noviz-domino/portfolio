# 법률 비서 시스템 (RAG 기반 AI 법률 검색)

RAG(검색 증강 생성) 기술을 기반으로, 법률 전문가와 일반 사용자 모두가 법률 문서를
검색하고 관련 답변을 받을 수 있도록 돕는 시스템입니다. 대규모 언어 모델(LLM)과
검색 증강 생성을 결합해 근거 있는 답변을 제공합니다.

2024년 2학기 캡스톤 프로젝트로 제작했습니다.

> ### ⚠ 현재 리빌딩 진행 중
>
> `main` 브랜치는 전면 재구축 중이라 **아래 문서의 실행 방법(Flask·uwsgi·app.ini)은
> 더 이상 유효하지 않습니다.** 재구축이 끝나면 이 문서를 전면 갱신합니다.
>
> - 2024년 캡스톤 제출 원본: 태그 [`v1.0-capstone`](../../tree/v1.0-capstone)
>   또는 브랜치 [`legacy-2024`](../../tree/legacy-2024)
> - 재구축 배경과 계획: [docs/리빌딩계획.md](docs/리빌딩계획.md)
> - 기술 설계: [docs/설계.md](docs/설계.md)
> - 진행 기록: [docs/작업일지.md](docs/작업일지.md)

```
질문: "근로기준법에 따른 초과근무수당 기준은 무엇인가요?"
  → PDF에서 관련 조항 검색 → 검색 결과를 근거로 LLM이 답변 생성
```

---

## 주요 기능

**법률 문서 검색 및 요약** — 입력한 질문에 적합한 법률 정보를 검색하고 요약된
답변을 생성합니다.

**PDF 문서 처리** — PDF를 로드해 텍스트를 추출하고 벡터화하여 빠른 검색이
가능하도록 구성했습니다.

**RAG 시스템 적용** — 검색된 문서를 바탕으로 LLM이 자연스러운 답변을 생성합니다.

**웹 기반 사용자 인터페이스** — Flask 웹 애플리케이션으로 질문 입력과 답변 출력
환경을 제공합니다.

---

## 아키텍처

이 프로젝트의 핵심 제약은 **로컬 하드웨어가 라즈베리파이라 8B 규모의 LLM을 직접
돌릴 수 없다**는 점이었습니다. 유료 GPU 인스턴스나 상용 API를 쓰지 않고, Colab의
무료 GPU를 ngrok으로 터널링해 이 문제를 우회했습니다.

```
┌─────────────────────────────┐         ┌──────────────────────────┐
│  라즈베리파이 (로컬)         │         │  Google Colab (무료 GPU) │
│                             │         │                          │
│  Flask 웹앱                 │         │  Ollama                  │
│    ├─ 임베딩 (bge-m3, CPU)  │  HTTPS  │    └─ llama3.1-korean:8b │
│    ├─ Chroma 벡터 검색      │ ──────► │       (T4 / CUDA)        │
│    └─ ChatOllama 클라이언트 │  ngrok  │                          │
└─────────────────────────────┘  터널   └──────────────────────────┘
          ▲
          │ duckdns + 포트포워딩
          │
      외부 사용자
```

무거운 LLM 추론은 Colab GPU에 맡기고, 로컬에서는 임베딩 생성과 벡터 검색처럼
상대적으로 가벼운 작업만 수행합니다. Flask 앱 입장에서는 `ChatOllama`의
`base_url`만 원격을 가리킬 뿐이라, **마치 로컬 모델을 호출하듯 코드를 작성**할 수
있다는 것이 이 구조의 이점입니다.

### 구성 요소

| 구성 요소 | 사용 기술 | 실행 위치 |
|---|---|---|
| 웹 프레임워크 | Flask + uwsgi | 로컬 |
| 문서 로더 | PyMuPDF | 로컬 |
| 텍스트 분할 | RecursiveCharacterTextSplitter (500자 / 100자 중첩) | 로컬 |
| 임베딩 | BAAI/bge-m3 (CPU) | 로컬 |
| 벡터 저장소 | Chroma | 로컬 |
| LLM | benedict/linkbricks-llama3.1-korean:8b | Colab GPU |
| 터널링 | ngrok | Colab |
| 외부 공개 | duckdns + 공유기 포트포워딩 | 로컬 네트워크 |

> 임베딩만 CPU를 쓰는 이유 등 파이프라인 단계별 상세 설명은
> [docs/구현노트.md](docs/구현노트.md)를 참고하세요.

---

## 실행 방법

### 1. Colab에서 Ollama 서버 띄우기

Colab에 접속해 GPU를 **T4**로 설정하고, 아래 코드를 실행합니다. 본인의 ngrok
토큰이 필요합니다. 설치에 5~7분 정도 걸립니다.

```python
!curl https://ollama.ai/install.sh | sh

!echo 'debconf debconf/frontend select Noninteractive' | sudo debconf-set-selections
!sudo apt-get update && sudo apt-get install -y cuda-drivers

!pip install pyngrok
```

```python
from pyngrok import ngrok

token = '본인의 엔그록 토큰'
ngrok.set_auth_token(token)
```

```python
import os
import asyncio

# 시스템 NVIDIA 라이브러리를 찾도록 LD_LIBRARY_PATH 설정
os.environ.update({'LD_LIBRARY_PATH': '/usr/lib64-nvidia'})

async def run_process(cmd):
    print('>>> starting', *cmd)
    p = await asyncio.subprocess.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    async def pipe(lines):
        async for line in lines:
            print(line.strip().decode('utf-8'))

    await asyncio.gather(pipe(p.stdout), pipe(p.stderr))

from IPython.display import clear_output
clear_output()

# ngrok은 11434 포트를 사용하므로 해당 포트를 열고, 필요한 모델을 설치한다.
await asyncio.gather(
    run_process(['ollama', 'serve']),
    run_process(['ngrok', 'http', '--log', 'stderr', '11434',
                 '--host-header="localhost:11434"']),
    run_process(['ollama', 'pull', 'benedict/linkbricks-llama3.1-korean:8b']),
)
```

실행하면 `https://xxxx-xx-xx-xx-xx.ngrok-free.app` 형태의 URL이 출력됩니다.

> **주의:** ngrok URL은 Colab 세션을 새로 열 때마다 바뀝니다. 세션이 끊기면 아래
> 설정을 새 URL로 갱신해야 합니다.

### 2. 의존성 설치

```bash
pip install -r requirements.txt
```

### 3. 엔드포인트 설정

`app.ini`의 `env` 항목을 1단계에서 받은 URL로 수정합니다. URL 끝에 슬래시를 붙이면
요청 경로가 어긋나므로 붙이지 않습니다.

```ini
env = OLLAMA_BASE_URL=https://발급받은-주소.ngrok-free.app
```

직접 실행할 때는 환경변수로 넘겨도 됩니다.

```bash
export OLLAMA_BASE_URL=https://발급받은-주소.ngrok-free.app
```

### 4. 서버 실행

```bash
uwsgi --ini app.ini
```

개발 중에는 Flask 개발 서버로도 띄울 수 있습니다.

```bash
python app.py
```

브라우저에서 `http://localhost:5000` 으로 접속합니다.

> HTML·CSS·Python을 수정했다면 서버를 `Ctrl+C`로 내렸다가 다시 띄워야 하고,
> 브라우저는 `Ctrl+Shift+R`(또는 `Ctrl+F5`)로 강제 새로고침해야 캐시 때문에 변경이
> 반영되지 않는 문제를 피할 수 있습니다.

---

## 외부 접속 구성 (선택)

로컬 네트워크 밖에서 접속하게 하려면 무료 DNS 서비스와 공유기 포트포워딩이
필요합니다. 본 프로젝트는 duckdns를 사용했습니다.

개발 환경이 **고정 IP를 쓸 수 없는 환경**이라 동적 IP를 사용했고, 공유기 IP를
5분마다 duckdns 서버에 갱신하면서 해당 IP로 들어오는 포트를 라즈베리파이의 내부
할당 IP로 포워딩했습니다. 그래서 접속 주소에 포트를 따로 지정합니다.

```
외부 요청  →  공유기 공인 IP:50000
           →  (포트포워딩)
           →  라즈베리파이 내부 IP:5000  (내부 IP는 매번 바뀜)
```

이 구성으로 라즈베리파이 로컬 5000번 포트에 열린 웹서버를 외부에서 접근할 수
있습니다. 포트포워딩은 공유기 모델마다 설정 화면이 다르므로 검색해서 맞추면 됩니다.

> 캡스톤 기간 중에는 `wsrag.duckdns.org:50000`으로 운영했으나, 2024-12-13 이후
> 종료되어 현재는 접속되지 않습니다. 사용하려면 본인 도메인을 설정해야 합니다.

비용을 들일 수 있다면 웹서버와 GPU 인스턴스를 결제해 쓰는 편이 운영은 훨씬
편합니다. 이 프로젝트는 상용 API를 쓰지 않고 직접 구축하는 것을 목표로 했기에
무료 인프라만으로 구성했습니다.

---

## 설정 항목

환경변수로 주입합니다. 괄호 안은 기본값입니다.

| 환경변수 | 설명 |
|---|---|
| `OLLAMA_BASE_URL` | Colab에서 서빙 중인 Ollama 엔드포인트 (`http://localhost:11434`) |
| `OLLAMA_MODEL` | 사용할 LLM (`benedict/linkbricks-llama3.1-korean:8b`) |
| `EMBEDDING_MODEL` | 임베딩 모델 (`BAAI/bge-m3`) |

---

## 사용법

웹 페이지에서 법률 관련 질문을 입력합니다.

> 예: "근로기준법에 따른 초과근무수당 기준은 무엇인가요?"

AI가 관련 법령 및 문서를 검색해 요약된 답변을 제공합니다. 응답 시간이 2분 이상
초과한다면 새로고침해 주세요.

### 화면

| 경로 | 설명 |
|---|---|
| `/` | 질문 입력 화면 |
| `/get_answer` | 질의 처리 후 답변 출력 (POST) |
| `/random_exam` | 시험 문제 PDF에서 무작위 페이지를 뽑아 출력 |

질문 입력 화면

![image](https://github.com/user-attachments/assets/c263034f-727b-473e-bdc2-341f9b36380b)

응답 화면

![image](https://github.com/user-attachments/assets/ede5f8de-dbcc-4191-93d7-9d3b055b8919)

디자인 변경 전 초기 화면

![image](https://github.com/user-attachments/assets/cf043d36-430b-47e4-83f6-9991f23579af)

---

## 디렉토리 구조

```
.
├── app.py              # Flask 앱 + RAG 파이프라인
├── app.ini             # uwsgi 설정
├── requirements.txt
├── pdf_data/           # 원본 PDF (지식 베이스 및 시험 문제)
│   ├── testpdf.pdf     # 지식 베이스로 사용하는 법률 문서
│   └── exampdf.pdf     # 랜덤 출제용 시험 문제
├── rag_temp/
│   └── template.txt    # LLM 프롬프트 템플릿
├── vector_store/       # Chroma 벡터 DB (pdf_data로부터 생성, git 제외)
├── templates/          # Jinja2 HTML 템플릿
├── static/             # CSS, JS
├── docs/
│   └── 구현노트.md      # RAG 파이프라인 상세 설명
└── archive/            # 개발 과정에서 사용한 노트북 (이력 보관)
```

`vector_store/`는 저장소에 포함하지 않습니다. 없으면 최초 실행 시 `pdf_data/`의
PDF로부터 자동 생성되며, 임베딩 계산에 시간이 걸립니다.

---

## 알려진 제약

- Colab 세션이 끊기면 답변 생성이 실패합니다. 무료 GPU 사용 시간 제한과 ngrok URL
  변경을 매번 처리해야 하는 것이 이 구조의 가장 큰 운영상 부담입니다.
- 지식 베이스 PDF가 `pdf_data/testpdf.pdf`로 고정되어 있습니다. 문서를 바꾸려면
  `vector_store/`를 지우고 다시 생성해야 합니다.
- 업로드 기능이 없어 PDF 교체는 파일을 직접 갈아끼우는 방식으로만 가능합니다.

---

## 라이센스

MIT License

코드 사용에 대한 모든 활동에 대해 작성자는 책임지지 않습니다.

---

## 작성자

24년 2학기 캡스톤2

김민석

기획·개발·인프라 구성·문서화 전 과정을 단독으로 수행했습니다.
