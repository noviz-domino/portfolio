# Kim Minseok

**AI Agent Engineer (entry level)** · Seoul, South Korea

I build LLM applications, focusing on **output validation and human approval steps that make LLMs safe to put into real services**.

| | |
|:--|:--|
| **Email** | [noviz2025@gmail.com](mailto:noviz2025@gmail.com) |
| **GitHub** | [noviz-domino](https://github.com/noviz-domino) |
| **LinkedIn** | [kim-min-seok-domino](https://www.linkedin.com/in/kim-min-seok-domino/) |
| **Website** | [noviz-domino.github.io](https://noviz-domino.github.io/) |
| **Now** | Samsung Multicampus AI Agent Engineer Track (Jul 2026 – Jan 2027) |

[Live demos](#live-demos) · [About](#about) · [Highlights](#highlights) · [Projects](#projects) · [Other projects](#other-projects) · [Skills](#skills) · [Education](#education) · [Certificates & awards](#certificates--awards) · [한국어](README.md)

---

## Live demos

| Project | What it is | Link |
|:--|:--|:--|
| **Financial AI agent** | Conversational banking that runs only after approval | [Web demo](https://noviz-bank.duckdns.org) |
| **englishWordApp** | TOEIC vocabulary Android app | [Google Play](https://play.google.com/store/apps/details?id=com.voca.englishwordapp) |
| **mealmate** | AI weekly meal planner | [Web demo](https://mealmate-inky.vercel.app) |
| **go-eat** | Rural restaurant log · demo account `test1@goeat.test` / `test1234` | [Web demo](https://go-eat-noviz.vercel.app) |
| **data-value-sandbox** | Simulation measuring which data makes events predictable | [Web demo](https://noviz-domino.github.io/data-value-sandbox/) |
| **cosmic-grazer** | Browser bullet-hell game | [Play](https://noviz-domino.github.io/cosmic-grazer/) |

All demos run on fictional data. Demos on free-tier servers may take a few seconds on first load.

---

## About

I majored in Computer Information Security and am now in the Samsung Multicampus AI Agent Engineer Track, learning **LLMs, RAG and multi-agent systems** through projects built around finance-domain problems.

LLMs can invent plausible numbers. So in every project I **split the work between what the LLM does and what code and people do**, then check that the boundary holds with evaluation sets and scenario tests. I also document failed attempts and the reasons behind design changes.

Beyond AI agents, I have built and run an Android app published on Google Play and two deployed Next.js web services on my own. When a project needs something I don't know yet, I learn it and see the work through.

---

## Highlights

| Result | What it measures | Project |
|:--|:--|:--|
| **34% → 94%** | First-pass approval rate of AI reply drafts after adding RAG; numeric accuracy 43.8% → 96.0% | replygate · 50-case eval set |
| **47 / 47** | Dialogue scenarios passed with the ledger intact, including insufficient balance, save failures and AI server outages | langgraph-financial-agent |
| **188 → 4 calls** | Daily LLM calls after filtering, a daily cap and batch summaries, to stay inside the free API quota | n8n-finance-news-briefing |
| **Google Play** | Android app rewritten in Kotlin + Compose; quiz logic pinned with 25 JUnit tests | englishWordApp |

---

## Projects

*Most recent first. All are solo projects.*

### langgraph-financial-agent · Conversational banking AI agent
`Sep 2026` · Course assignment · **Complete, deployed**

Understands requests like "send ₩100,000 from living expenses to savings" and handles balance lookups, transfers and card locks. Anything that changes money or card state runs only after the user approves it.

- **Design** - The LLM is used only in the node that interprets what the user said. Balance math, checks, storage and reply text are all code, so no number passes through the LLM.
- **Safeguards** - A LangGraph `interrupt` pauses execution until approval, and a save happens only after 10 integrity rules pass, replacing the ledger atomically.
- **Verification** - 47 dialogue scenarios, including failure cases, run automatically and all pass; 27 design changes are logged with their reasons.
- **Problem solved** - Even when told not to in the prompt, the LLM sometimes invented the source account. I changed the rule so that code validates the LLM's answer instead of relying on the prompt.

`LangGraph` `LangChain` `Gemini` `FastAPI` `Python 3.13` `Oracle Cloud`

| Transfer request → approval card | Balances after approval |
|:--:|:--:|
| <img src="projects/langgraph-financial-agent/docs/images/02-confirm.png" alt="Transfer approval card" width="400" /> | <img src="projects/langgraph-financial-agent/docs/images/03-done.png" alt="Balances after approval" width="400" /> |

[Live demo](https://noviz-bank.duckdns.org) · [Repository](https://github.com/noviz-domino/langgraph-financial-agent) · [Design change log (KR)](projects/langgraph-financial-agent/docs/설계변경기록.md)

### legal_secretary · Labor-law RAG assistant that cites the article
`Sep – Nov 2024` capstone, `Sep 2026 –` rebuild · Graduation thesis topic · **Rebuild: stage 3 of 6**

Answers legal questions by finding the relevant statute articles and citing them. I built the 2024 capstone version alone, from planning to development and infrastructure, and am now rebuilding it from the ground up.

- **Why rebuild** - The design claimed "legal documents are sensitive, so we use a local LLM", but in practice questions were leaving through an external tunnel. I found that gap myself.
- **Retrieval** - To avoid missing exact expressions like "Labor Standards Act, Article 56", documents are split at article boundaries and keyword (BM25) and semantic (vector) search are combined.
- **Response** - Citations are streamed (SSE) before the answer, so users are not left waiting even on a slow free-tier API (measured 8.8 s).

`FastAPI` `LangChain` `Chroma` `BM25` `bge-m3` `SSE`

[Code](projects/legal_secretary/) · [Rebuild plan (KR)](projects/legal_secretary/docs/리빌딩계획.md)

### mealmate · AI weekly meal planner from what's in your fridge
`Aug – Sep 2026` · **Deployed, live demo**

Enter your ingredients and the AI generates a weekly meal plan and shopping list; recipes for each meal are generated on demand.

- **Output validation** - Even after enforcing the output format with a schema, the structure is checked again and regenerated once on failure.
- **Allergies** - Derived ingredients are blocked too, so someone avoiding milk never gets condensed milk or cream.
- **Security** - Per-user data isolation with Supabase RLS. About 3,200 lines of TypeScript, built in 3 days.

`Next.js 16` `React 19` `TypeScript` `Supabase` `Gemini` `Vercel`

| Public plans | Generated plan | Recipe on demand |
|:--:|:--:|:--:|
| <img src="projects/mealmate/docs/screenshots/01-홈-공개식단.png" width="240" /> | <img src="projects/mealmate/docs/screenshots/05-AI가만든식단.png" width="240" /> | <img src="projects/mealmate/docs/screenshots/06-AI가만든조리법.png" width="240" /> |

[Live demo](https://mealmate-inky.vercel.app) · [Code](projects/mealmate/)

### replygate · Customer support automation with AI drafts and human approval
`Aug 2026` · Course mini project · **Complete, measured**

When a customer inquiry arrives, the AI drafts a reply grounded in company policy documents, and the email is sent only after a staff member approves it in Telegram.

- **Design** - Because wrong numbers (refund fees, shipping deadlines) cause disputes, I added a human approval step instead of auto-sending.
- **Results** - On a 50-case evaluation set, first-pass approval rose from 34% to 94% and numeric accuracy from 43.8% to 96.0%. The set includes 5 trap questions with no answer in the policy.
- **Problem solved** - One sentiment class was never selected. The cause was two criteria mixed into one; splitting them into two axes gave 98% / 92% accuracy.

`n8n` `Gemini` `RAG` `FastAPI` `Telegram Bot`

<img src="projects/replygate/docs/screenshots/텔레그램-정책충돌-감지.png" alt="Telegram approval card flagging a conflict between the operator's instruction and policy" width="320" />

[Code](projects/replygate/) · [Evaluation design](projects/replygate/eval/)

### englishWordApp · TOEIC vocabulary Android app
`Jun – Aug 2026` · **Published on Google Play**

Study with meanings hidden, resume progress, TTS pronunciation, a mistake notebook and multiple-choice quizzes. 1,222 words.

- **Rewrite** - Fixed the problems of my earlier Java version (meanings always visible, stray quotes in 835 of 1,225 rows, progress lost on screen rotation) by rewriting it in Kotlin + Compose.
- **Quality** - Quiz logic is extracted into pure functions pinned with 25 JUnit tests, and study position is restored even after the app process is killed.

`Kotlin` `Jetpack Compose` `JUnit` `Android`

| Home | Study | Quiz |
|:--:|:--:|:--:|
| <img src="projects/englishWordApp/docs/brand/play-store/capture/main.png" width="200" /> | <img src="projects/englishWordApp/docs/brand/play-store/capture/word.png" width="200" /> | <img src="projects/englishWordApp/docs/brand/play-store/capture/game.png" width="200" /> |

[Google Play](https://play.google.com/store/apps/details?id=com.voca.englishwordapp) · [Code](projects/englishWordApp/)

---

## Other projects

| Period | Project | Stack | Link |
|:--|:--|:--|:--|
| Sep 2026 | **multi-agent-tax-prep** - Multi-agent helper for Korean income tax filing (research · planning · review); 57 tests without LLM calls | LangGraph · Gemini | [Code](projects/multi-agent-tax-prep/) |
| Sep 2026 | **rag-experiment-script** - RAG experiment comparing chunking, retrieval and reranking over 20 configs; hybrid Page Hit@1 0.943 (baseline 0.886) | LangChain · Chroma · BM25 | [Code](projects/rag-experiment-script/) |
| Aug – Sep 2026 | **personal-budget-ai-agent** - Natural-language budgeting agent with 7 tools | Gemini Function Calling | [Code](projects/personal-budget-ai-agent/) |
| Aug – Sep 2026 | **go-eat** - Rural restaurant log web app, built under an 8-hour limit | Next.js · Supabase | [Demo](https://go-eat-noviz.vercel.app) · [Code](projects/go-eat/) |
| Aug 2026 | **n8n-finance-news-briefing** - Automated financial news digest; daily API calls 188 → 4 | n8n · Gemini · Discord | [Code](projects/n8n-finance-news-briefing/) |
| Aug 2026 | **n8n-voc-analysis-agent** - Automatic customer feedback classification and urgent alerts | n8n · Gemini · Sheets | [Code](projects/n8n-voc-analysis-agent/) |
| Jul – Aug 2026 | **cosmic-grazer** - Single-HTML-file bullet-hell survivor game | Vanilla JS · Canvas2D | [Play](https://noviz-domino.github.io/cosmic-grazer/) · [Code](projects/cosmic-grazer/) |
| Jul 2026 | **god-of-diplomacy** - Gemini-powered political and diplomatic text RPG | FastAPI · Gemini | [Code](projects/god-of-diplomacy/) |
| Apr – Sep 2026 | **data-value-sandbox** - Measuring which data makes events predictable, in a synthetic world; target inference top-1 51.5% (3.81× baseline) | deck.gl · Jupyter | [Demo](https://noviz-domino.github.io/data-value-sandbox/) · [Repo](https://github.com/noviz-domino/data-value-sandbox) |
| Dec 2021 | **GTD terror prediction model** - Global Terrorism Database analysis and prediction (2-person team) | Python · Scikit-learn | [Repo](https://github.com/noviz-domino/gtd-terror-analysis-project) |

---

## Skills

| Area | Used in projects |
|:--|:--|
| **AI / Agent** | LangGraph · LangChain · Gemini API · Function Calling · Structured Output · n8n |
| **RAG / Retrieval** | Chroma · BM25 · Hybrid retrieval (RRF) · Reranking · Evaluation set design |
| **Backend** | FastAPI · Flask · Supabase · PostgreSQL · MySQL |
| **Frontend / Mobile** | Next.js · React · Tailwind CSS · Jetpack Compose |
| **Languages** | Python · C · TypeScript · JavaScript · Kotlin |
| **Infra / Tools** | Git · GitHub Actions · Vercel · Oracle Cloud · Ollama · Linux · Claude Code |
| *Studied, not yet used in a project* | *Java · PyTorch · TensorFlow · Alibaba Cloud* |

---

## Education

**Samsung Multicampus · AI Agent Engineer Track, Cohort 1** · `Jul 2026 – Jan 2027` · *in progress*
984 hours · a program built around developing financial AI services

| Module | Topic | Related work |
|:--|:--|:--|
| 1 | LLMs, prompt engineering, n8n | replygate · n8n-voc-analysis-agent · n8n-finance-news-briefing |
| 2 | Python AI web development, LangChain | personal-budget-ai-agent · rag-experiment-script |
| 3 | LangGraph, MCP, multi-agent systems | langgraph-financial-agent · multi-agent-tax-prep |
| 4 – 6 | RAG system design · production (Docker, AWS, CI/CD) · capstone | *upcoming* |

**Woosong University** · Computer Information Security · `Mar 2017 – Mar 2026` · completed coursework

**Beijing Institute of Technology** · Joint degree program · `Mar 2019 – Jan 2024` · withdrew · team projects with international members

Daily study notes: [TIL repository](https://github.com/noviz-domino/TIL)

---

## Certificates & awards

| When | |
|:--|:--|
| Military service | **1st place, C4I system operations** - Commendation from the Brigadier General, ROK Army Signal School |
| Mar 2026 | TOEIC 545 |
| Held | Ultralight vehicle pilot, Class 1 (drone) |
| In progress | Engineer Information Processing · Engineer Information Security (practical exams) |

Military service: completed (ROK Army).

---

This repository collects each project's source code and design documents under `projects/`. Most original repositories are private, so the copies here have sensitive data removed. How I work with AI coding tools is described in [docs/agent-workflow.md](docs/agent-workflow.md).

<sub>Last updated 2026-09-30 · [Change log (KR)](docs/CHANGELOG.md)</sub>
