<div align="center">

[![Visit Portfolio Site](https://img.shields.io/badge/Visit_Portfolio_Site-noviz--domino.github.io-14B8A6?style=for-the-badge&logo=googlechrome&logoColor=white&labelColor=0F766E)](https://noviz-domino.github.io/)

# Kim Minseok

### AI Agent Engineer · Entry level

**I connect LLMs to real services - safely.**<br/>
I design output validation and human approval steps, splitting the work between what the LLM does and what code and people do.

[![Email](https://img.shields.io/badge/noviz2025@gmail.com-EA4335?style=flat-square&logo=gmail&logoColor=white)](mailto:noviz2025@gmail.com)
[![GitHub](https://img.shields.io/badge/noviz--domino-181717?style=flat-square&logo=github&logoColor=white)](https://github.com/noviz-domino)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-0A66C2?style=flat-square&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/kim-min-seok-domino/)
[![Website](https://img.shields.io/badge/Portfolio_Site-0F766E?style=flat-square&logo=googlechrome&logoColor=white)](https://noviz-domino.github.io/)
[![TIL](https://img.shields.io/badge/TIL-555555?style=flat-square&logo=github&logoColor=white)](https://github.com/noviz-domino/TIL)

📍 Seoul, South Korea &nbsp;·&nbsp; 🎓 Samsung Multicampus AI Agent Engineer Track (Jul 2026 – Jan 2027)

[Live demos](#-live-demos) · [About](#-about) · [Highlights](#-highlights) · [Projects](#-projects) · [Other projects](#-other-projects) · [Skills](#-skills) · [Education](#-education) · [Certificates & awards](#-certificates--awards) · [한국어](README.md)

</div>

---

## 🚀 Live demos

Things you can click and try right now. All run on fictional data.

<div align="center">

[![Financial AI agent](https://img.shields.io/badge/Financial_AI_agent-Web_demo-1F2328?style=for-the-badge&logo=langchain&logoColor=white&labelColor=1C3C3C)](https://noviz-bank.duckdns.org)
[![englishWordApp](https://img.shields.io/badge/englishWordApp-Google_Play-1F2328?style=for-the-badge&logo=googleplay&logoColor=white&labelColor=34A853)](https://play.google.com/store/apps/details?id=com.voca.englishwordapp)
[![mealmate](https://img.shields.io/badge/mealmate-Web_demo-1F2328?style=for-the-badge&logo=vercel&logoColor=white&labelColor=000000)](https://mealmate-inky.vercel.app)

[![go-eat](https://img.shields.io/badge/go--eat-Web_demo-1F2328?style=for-the-badge&logo=supabase&logoColor=white&labelColor=3FCF8E)](https://go-eat-noviz.vercel.app)
[![data-value-sandbox](https://img.shields.io/badge/data--value--sandbox-Web_demo-1F2328?style=for-the-badge&logo=github&logoColor=white&labelColor=0F766E)](https://noviz-domino.github.io/data-value-sandbox/)
[![cosmic-grazer](https://img.shields.io/badge/cosmic--grazer-Play-1F2328?style=for-the-badge&logo=javascript&logoColor=white&labelColor=7C4DCC)](https://noviz-domino.github.io/cosmic-grazer/)

</div>

> go-eat demo account `test1@goeat.test` / `test1234` · Demos on free-tier servers may take a few seconds on first load.

---

## 👋 About

I majored in Computer Information Security and am now in the Samsung Multicampus AI Agent Engineer Track, learning **LLMs, RAG and multi-agent systems** through projects built around finance-domain problems. Beyond AI agents, I have built and run an Android app published on Google Play and two deployed Next.js web services on my own.

<table>
<tr>
<td width="33%" valign="top">

**🧭 LLMs at the entrance only**

The LLM interprets what people say. Calculation, validation and storage are done in code, so numbers never pass through the model.

</td>
<td width="33%" valign="top">

**✋ A human can stop it**

Wherever money moves or a message reaches a customer, there is an approval step. Controllable beats fast.

</td>
<td width="33%" valign="top">

**📏 Measure, then claim**

Instead of "it got better", I keep numbers from evaluation sets and scenarios, and record failures and the reasons behind design changes.

</td>
</tr>
</table>

---

## 🏆 Highlights

<div align="center">

| First-pass approval | Dialogue scenarios | Daily API calls | Shipped app |
|:--:|:--:|:--:|:--:|
| **34% → 94%** | **47 / 47** passed | **188 → 4** | **Google Play** |
| replygate · with RAG<br/>numeric accuracy 43.8% → 96.0% | financial agent<br/>failure cases included, ledger intact | news digest<br/>free-tier limits | englishWordApp<br/>25 JUnit tests |

</div>

---

## 📂 Projects

*Most recent first · all solo projects*

### 1. langgraph-financial-agent · Conversational banking AI agent

`Sep 2026` · Course assignment · ✅ **Complete · deployed**

![LangGraph](https://img.shields.io/badge/LangGraph-1C3C3C?style=flat-square&logo=langchain&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini-8E75B2?style=flat-square&logo=googlegemini&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python_3.13-3776AB?style=flat-square&logo=python&logoColor=white)
![Oracle Cloud](https://img.shields.io/badge/Oracle_Cloud-F80000?style=flat-square&logo=oracle&logoColor=white)

Understands requests like "send ₩100,000 from living expenses to savings" and handles balance lookups, transfers and card locks. Anything that changes money or card state runs only after the user approves it.

- **Design** - The LLM is used only in the node that interprets what the user said. Balance math, checks, storage and reply text are all code, so no number passes through the LLM.
- **Safeguards** - A LangGraph `interrupt` pauses execution until approval, and a save happens only after 10 integrity rules pass, replacing the ledger atomically.
- **Verification** - 47 dialogue scenarios, including failure cases, run automatically and all pass; 27 design changes are logged with their reasons.
- **Problem solved** - Even when told not to in the prompt, the LLM sometimes invented the source account. I changed the rule so that code validates the LLM's answer instead of relying on the prompt.

| Transfer request → approval card | Balances after approval |
|:--:|:--:|
| <img src="projects/langgraph-financial-agent/docs/images/02-confirm.png" alt="Transfer approval card" width="400" /> | <img src="projects/langgraph-financial-agent/docs/images/03-done.png" alt="Balances after approval" width="400" /> |

🔗 [Try it live](https://noviz-bank.duckdns.org) · 📂 [Repository](https://github.com/noviz-domino/langgraph-financial-agent) · 📄 [Design change log (KR)](projects/langgraph-financial-agent/docs/설계변경기록.md)

<br/>

### 2. legal_secretary · Labor-law RAG assistant that cites the article

`Sep – Nov 2024` capstone → `Sep 2026 –` rebuild · Graduation thesis topic · 🚧 **Rebuild: stage 3 of 6**

![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=flat-square&logo=langchain&logoColor=white)
![Chroma](https://img.shields.io/badge/Chroma-FF6446?style=flat-square)
![BM25](https://img.shields.io/badge/BM25_+_Vector-555555?style=flat-square)
![SSE](https://img.shields.io/badge/SSE_Streaming-555555?style=flat-square)

Answers legal questions by finding the relevant statute articles and citing them. I built the 2024 capstone version alone, from planning to development and infrastructure, and am now rebuilding it from the ground up.

- **Why rebuild** - The design claimed "legal documents are sensitive, so we use a local LLM", but in practice questions were leaving through an external tunnel. I found that gap myself.
- **Retrieval** - To avoid missing exact expressions like "Labor Standards Act, Article 56", documents are split at article boundaries and keyword (BM25) and semantic (vector) search are combined.
- **Response** - Citations are streamed (SSE) before the answer, so users are not left waiting even on a slow free-tier API (measured 8.8 s).

📂 [Code](projects/legal_secretary/) · 📄 [Rebuild plan (KR)](projects/legal_secretary/docs/리빌딩계획.md)

<br/>

### 3. mealmate · AI weekly meal planner from what's in your fridge

`Aug – Sep 2026` · ✅ **Deployed · live demo**

![Next.js](https://img.shields.io/badge/Next.js_16-000000?style=flat-square&logo=nextdotjs&logoColor=white)
![React](https://img.shields.io/badge/React_19-61DAFB?style=flat-square&logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=flat-square&logo=typescript&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-3FCF8E?style=flat-square&logo=supabase&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini-8E75B2?style=flat-square&logo=googlegemini&logoColor=white)

Enter your ingredients and the AI generates a weekly meal plan and shopping list; recipes for each meal are generated on demand.

- **Output validation** - Even after enforcing the output format with a schema, the structure is checked again and regenerated once on failure.
- **Allergies** - Derived ingredients are blocked too, so someone avoiding milk never gets condensed milk or cream.
- **Security** - Per-user data isolation with Supabase RLS. About 3,200 lines of TypeScript, built in 3 days.

| Public plans | Generated plan | Recipe on demand |
|:--:|:--:|:--:|
| <img src="projects/mealmate/docs/screenshots/01-홈-공개식단.png" width="240" /> | <img src="projects/mealmate/docs/screenshots/05-AI가만든식단.png" width="240" /> | <img src="projects/mealmate/docs/screenshots/06-AI가만든조리법.png" width="240" /> |

🔗 [Live demo](https://mealmate-inky.vercel.app) · 📂 [Code](projects/mealmate/)

<br/>

### 4. replygate · Customer support automation with AI drafts and human approval

`Aug 2026` · Course mini project · ✅ **Complete · measured**

![n8n](https://img.shields.io/badge/n8n-EA4B71?style=flat-square&logo=n8n&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini-8E75B2?style=flat-square&logo=googlegemini&logoColor=white)
![RAG](https://img.shields.io/badge/RAG-000000?style=flat-square)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram_Bot-26A5E4?style=flat-square&logo=telegram&logoColor=white)

When a customer inquiry arrives, the AI drafts a reply grounded in company policy documents, and the email is sent only after a staff member approves it in Telegram.

- **Design** - Because wrong numbers (refund fees, shipping deadlines) cause disputes, I added a human approval step instead of auto-sending.
- **Results** - On a 50-case evaluation set, first-pass approval rose from 34% to 94% and numeric accuracy from 43.8% to 96.0%. The set includes 5 trap questions with no answer in the policy.
- **Problem solved** - One sentiment class was never selected. The cause was two criteria mixed into one; splitting them into two axes gave 98% / 92% accuracy.

<img src="projects/replygate/docs/screenshots/텔레그램-정책충돌-감지.png" alt="Telegram approval card flagging a conflict between the operator's instruction and policy" width="320" />

📂 [Code](projects/replygate/) · 📄 [Evaluation design](projects/replygate/eval/)

<br/>

### 5. englishWordApp · TOEIC vocabulary Android app

`Jun – Aug 2026` · ✅ **Published on Google Play**

![Kotlin](https://img.shields.io/badge/Kotlin-7F52FF?style=flat-square&logo=kotlin&logoColor=white)
![Compose](https://img.shields.io/badge/Jetpack_Compose-4285F4?style=flat-square&logo=jetpackcompose&logoColor=white)
![Android](https://img.shields.io/badge/Android-34A853?style=flat-square&logo=android&logoColor=white)
![JUnit](https://img.shields.io/badge/JUnit_25_tests-25A162?style=flat-square&logo=junit5&logoColor=white)

Study with meanings hidden, resume progress, TTS pronunciation, a mistake notebook and multiple-choice quizzes. 1,222 words.

- **Rewrite** - Fixed the problems of my earlier Java version (meanings always visible, stray quotes in 835 of 1,225 rows, progress lost on screen rotation) by rewriting it in Kotlin + Compose.
- **Quality** - Quiz logic is extracted into pure functions pinned with 25 JUnit tests, and study position is restored even after the app process is killed.

| Home | Study | Quiz |
|:--:|:--:|:--:|
| <img src="projects/englishWordApp/docs/brand/play-store/capture/main.png" width="200" /> | <img src="projects/englishWordApp/docs/brand/play-store/capture/word.png" width="200" /> | <img src="projects/englishWordApp/docs/brand/play-store/capture/game.png" width="200" /> |

📱 [View on Google Play](https://play.google.com/store/apps/details?id=com.voca.englishwordapp) · 📂 [Code](projects/englishWordApp/)

---

## 📦 Other projects

<table>
<thead>
<tr><th>Period</th><th>Project</th><th>Stack</th><th>Links</th></tr>
</thead>
<tbody>

<tr><td colspan="4"><b>🤖 AI agents · LLM</b></td></tr>
<tr><td>Sep 2026</td><td><b>multi-agent-tax-prep</b><br/>Multi-agent helper for Korean income tax filing (research · planning · review) · 57 tests without LLM calls</td><td>LangGraph · Gemini</td><td><a href="projects/multi-agent-tax-prep/">Code</a></td></tr>
<tr><td>Sep 2026</td><td><b>rag-experiment-script</b><br/>RAG experiment comparing chunking, retrieval and reranking over 20 configs · hybrid Page Hit@1 0.943 (baseline 0.886)</td><td>LangChain · Chroma · BM25</td><td><a href="projects/rag-experiment-script/">Code</a></td></tr>
<tr><td>Aug – Sep 2026</td><td><b>personal-budget-ai-agent</b><br/>Natural-language budgeting agent with 7 tools</td><td>Gemini Function Calling</td><td><a href="projects/personal-budget-ai-agent/">Code</a></td></tr>
<tr><td>Aug 2026</td><td><b>n8n-finance-news-briefing</b><br/>Automated financial news digest · daily API calls 188 → 4</td><td>n8n · Gemini · Discord</td><td><a href="projects/n8n-finance-news-briefing/">Code</a></td></tr>
<tr><td>Aug 2026</td><td><b>n8n-voc-analysis-agent</b><br/>Automatic customer feedback classification and urgent alerts</td><td>n8n · Gemini · Sheets</td><td><a href="projects/n8n-voc-analysis-agent/">Code</a></td></tr>
<tr><td>Jul 2026</td><td><b>god-of-diplomacy</b><br/>Gemini-powered political and diplomatic text RPG</td><td>FastAPI · Gemini</td><td><a href="projects/god-of-diplomacy/">Code</a></td></tr>

<tr><td colspan="4"><b>📱 Web · apps</b></td></tr>
<tr><td>Aug – Sep 2026</td><td><b>go-eat</b><br/>Rural restaurant log web app, built under an 8-hour limit</td><td>Next.js · Supabase</td><td><a href="https://go-eat-noviz.vercel.app">Demo</a> · <a href="projects/go-eat/">Code</a></td></tr>

<tr><td colspan="4"><b>📊 Data · games</b></td></tr>
<tr><td>Jul – Aug 2026</td><td><b>cosmic-grazer</b><br/>Single-HTML-file bullet-hell survivor game</td><td>Vanilla JS · Canvas2D</td><td><a href="https://noviz-domino.github.io/cosmic-grazer/">Play</a> · <a href="projects/cosmic-grazer/">Code</a></td></tr>
<tr><td>Apr – Sep 2026</td><td><b>data-value-sandbox</b><br/>Measuring which data makes events predictable, in a synthetic world · target inference top-1 51.5% (3.81× baseline)</td><td>deck.gl · Jupyter</td><td><a href="https://noviz-domino.github.io/data-value-sandbox/">Demo</a> · <a href="https://github.com/noviz-domino/data-value-sandbox">Repo</a></td></tr>
<tr><td>Dec 2021</td><td><b>GTD terror prediction model</b><br/>Global Terrorism Database analysis and prediction (2-person team)</td><td>Python · Scikit-learn</td><td><a href="https://github.com/noviz-domino/gtd-terror-analysis-project">Repo</a></td></tr>

</tbody>
</table>

---

## 🧰 Skills

| Area | Used in projects |
|:--|:--|
| **AI / Agent** | ![LangGraph](https://img.shields.io/badge/LangGraph-1C3C3C?style=flat-square&logo=langchain&logoColor=white) ![LangChain](https://img.shields.io/badge/LangChain-1C3C3C?style=flat-square&logo=langchain&logoColor=white) ![Gemini](https://img.shields.io/badge/Gemini_API-8E75B2?style=flat-square&logo=googlegemini&logoColor=white) ![n8n](https://img.shields.io/badge/n8n-EA4B71?style=flat-square&logo=n8n&logoColor=white) ![Function Calling](https://img.shields.io/badge/Function_Calling-555555?style=flat-square) ![Structured Output](https://img.shields.io/badge/Structured_Output-555555?style=flat-square) |
| **RAG / Retrieval** | ![Chroma](https://img.shields.io/badge/Chroma-FF6446?style=flat-square) ![BM25](https://img.shields.io/badge/BM25-555555?style=flat-square) ![Hybrid](https://img.shields.io/badge/Hybrid_RRF-555555?style=flat-square) ![Reranking](https://img.shields.io/badge/Reranking-555555?style=flat-square) ![Eval](https://img.shields.io/badge/Eval_set_design-555555?style=flat-square) |
| **Backend** | ![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white) ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white) ![Flask](https://img.shields.io/badge/Flask-000000?style=flat-square&logo=flask&logoColor=white) ![Supabase](https://img.shields.io/badge/Supabase-3FCF8E?style=flat-square&logo=supabase&logoColor=white) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white) ![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=flat-square&logo=mysql&logoColor=white) |
| **Frontend / Mobile** | ![Next.js](https://img.shields.io/badge/Next.js-000000?style=flat-square&logo=nextdotjs&logoColor=white) ![React](https://img.shields.io/badge/React-61DAFB?style=flat-square&logo=react&logoColor=black) ![TypeScript](https://img.shields.io/badge/TypeScript-3178C6?style=flat-square&logo=typescript&logoColor=white) ![Tailwind](https://img.shields.io/badge/Tailwind_CSS-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white) ![Kotlin](https://img.shields.io/badge/Kotlin-7F52FF?style=flat-square&logo=kotlin&logoColor=white) ![Compose](https://img.shields.io/badge/Jetpack_Compose-4285F4?style=flat-square&logo=jetpackcompose&logoColor=white) |
| **Infra / Tools** | ![Git](https://img.shields.io/badge/Git-F05032?style=flat-square&logo=git&logoColor=white) ![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=flat-square&logo=githubactions&logoColor=white) ![Vercel](https://img.shields.io/badge/Vercel-000000?style=flat-square&logo=vercel&logoColor=white) ![Oracle Cloud](https://img.shields.io/badge/Oracle_Cloud-F80000?style=flat-square&logo=oracle&logoColor=white) ![Ollama](https://img.shields.io/badge/Ollama-000000?style=flat-square&logo=ollama&logoColor=white) ![Linux](https://img.shields.io/badge/Linux-FCC624?style=flat-square&logo=linux&logoColor=black) ![Claude Code](https://img.shields.io/badge/Claude_Code-D97757?style=flat-square&logo=anthropic&logoColor=white) |
| *Studied, not yet used in a project* | ![Java](https://img.shields.io/badge/Java-AAAAAA?style=flat-square&logo=openjdk&logoColor=white) ![PyTorch](https://img.shields.io/badge/PyTorch-AAAAAA?style=flat-square&logo=pytorch&logoColor=white) ![TensorFlow](https://img.shields.io/badge/TensorFlow-AAAAAA?style=flat-square&logo=tensorflow&logoColor=white) ![Alibaba Cloud](https://img.shields.io/badge/Alibaba_Cloud-AAAAAA?style=flat-square&logo=alibabacloud&logoColor=white) |

---

## 🎓 Education

**Samsung Multicampus · AI Agent Engineer Track, Cohort 1** · `Jul 2026 – Jan 2027` · 🟢 in progress<br/>
984 hours · a program built around developing financial AI services

| Module | Topic | Related work |
|:--:|:--|:--|
| ✅ 1 | LLMs, prompt engineering, n8n | replygate · n8n-voc-analysis-agent · n8n-finance-news-briefing |
| ✅ 2 | Python AI web development, LangChain | personal-budget-ai-agent · rag-experiment-script |
| ✅ 3 | LangGraph, MCP, multi-agent systems | langgraph-financial-agent · multi-agent-tax-prep |
| ⏳ 4 – 6 | RAG system design · production (Docker, AWS, CI/CD) · capstone | *upcoming* |

| Period | School | |
|:--|:--|:--|
| Mar 2017 – Mar 2026 | **Woosong University** · Computer Information Security | Completed coursework |
| Mar 2019 – Jan 2024 | **Beijing Institute of Technology** · Joint degree program | Withdrew · team projects with international members |

Daily study notes are in the [TIL repository](https://github.com/noviz-domino/TIL).

---

## 🏅 Certificates & awards

| When | |
|:--|:--|
| 🥇 Military service | **1st place, C4I system operations** - Commendation from the Brigadier General, ROK Army Signal School |
| 📝 Mar 2026 | TOEIC 545 |
| 🚁 Held | Ultralight vehicle pilot, Class 1 (drone) |
| 📚 In progress | Engineer Information Processing · Engineer Information Security (practical exams) |

Military service: completed (ROK Army).

---

<div align="center">

### 📬 Contact

[![Email](https://img.shields.io/badge/noviz2025@gmail.com-EA4335?style=for-the-badge&logo=gmail&logoColor=white)](mailto:noviz2025@gmail.com)
[![GitHub](https://img.shields.io/badge/noviz--domino-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/noviz-domino)
[![Website](https://img.shields.io/badge/Portfolio_Site-0F766E?style=for-the-badge&logo=googlechrome&logoColor=white)](https://noviz-domino.github.io/)

This repository collects each project's source code and design documents under `projects/`. Most original repositories are private, so the copies here have sensitive data removed.<br/>
How I work with AI coding tools: [docs/agent-workflow.md](docs/agent-workflow.md)

<sub>Last updated 2026-09-30 · <a href="docs/CHANGELOG.md">Change log (KR)</a></sub>

</div>
