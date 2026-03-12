# Capital Bank AI Assistant

> Intelligent Banking Chatbot with Local LLM Inference  
> **Infosys Springboard Internship — Batch 13** | Mentor: Rojar

**Team:** Lokeshkanna • Nithin Singh • Sushant Pawar • Aakash • Moshin Khan • Vissa Geethika Suma

---

## Overview

Capital Bank AI Assistant is an intelligent chatbot built for automated banking customer support. It runs entirely **on-premise using Ollama** — no cloud dependency — and uses a SQLite + JSON FAQ knowledge base for accurate, domain-specific responses.

---

## Problem Statement

Modern banking customer support faces several key challenges:

- **High Call Volume** — Banks struggle to handle thousands of daily queries efficiently
- **Data Privacy Risks** — Cloud-based chatbots expose sensitive financial data to third parties
- **High Operational Cost** — 24/7 human agents and cloud APIs are expensive to maintain
- **Slow Response Time** — Network latency and queuing delays frustrate customers
- **Limited Domain Focus** — Generic AI chatbots answer irrelevant non-banking questions
- **No Offline Support** — Internet dependency causes failures in low-connectivity environments

---

## Project Objectives

1. **Local AI Deployment** — Deploy Phi-3 LLM via Ollama for offline, private inference
2. **Domain Restriction** — Limit responses strictly to banking-related queries
3. **Knowledge Retrieval (RAG)** — Combine FAQ database with generative AI for accurate answers
4. **Secure Chat System** — User authentication with SQLite-backed session management
5. **Professional UI** — Streamlit-based interface with PDF export capability

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend UI | Streamlit |
| Database | SQLite |
| Core Language | Python |
| Local LLM Runtime | Ollama |
| Conversational Model | Phi-3 |

---

## System Architecture

```
Presentation Layer   →   Application Layer   →   Data Layer   →   AI Layer
─────────────────────────────────────────────────────────────────────────────
Streamlit Web App        Auth Logic               SQLite DB        Ollama Runtime
Login & Chat UI          Session Manager          Users/Sessions   Phi-3 LLM Model
Sidebar Navigation       Prompt Builder           Chat History     System Prompt
PDF Export               FAQ Retriever            FAQ Sections     RAG Pipeline
```

---

## How It Works

```
User Query → Topic Filter → FAQ Retrieval → Prompt Builder → Phi-3 LLM → Response
```

- Queries are filtered using 15+ banking keywords
- Matched FAQs are retrieved from SQLite (structured by category: Account, UPI, Loans, etc.)
- A prompt is constructed combining FAQ context + user query
- Phi-3 generates a grounded, domain-specific response

---

## Key Features

- **Local LLM via Ollama** — Phi-3 model runs fully on-device
- **RAG Pipeline** — FAQ retrieval combined with generative reasoning
- **Domain Filtering** — Banking-only keyword validation
- **SQLite Storage** — Users, sessions, and chat history
- **PDF Export** — Download full conversation transcripts
- **Generalisation** — Answers intent, not just exact keyword match

---

## Usage

```python
import ollama

def ask_ollama(prompt):
    response = ollama.chat(
        model="phi3",
        messages=[{"role": "user", "content": prompt}]
    )
    return response["message"]["content"]
```

**Customer Journey:**
1. Login → 2. Ask a Banking Question → 3. AI Responds Instantly → 4. Export Chat as PDF

---

## Advantages

| Metric | Benefit |
|--------|---------|
| 100% Data Privacy | All data stays on-premise — no external exposure |
| ₹0 API Cost | Zero cloud API costs, no per-query billing |
| 24/7 Availability | Functions without internet connectivity |
| < 1s Latency | Local inference eliminates network delays |
| Enterprise Ready | Designed for internal banking deployment |

---

## Limitations & Known Issues

| Issue | Resolution |
|-------|-----------|
| Large model download | One-time setup; stored locally after first pull |
| Hardware requirements | Phi-3 chosen for small size & good performance |
| Limited model capability | RAG supplements knowledge where LLM falls short |
| Keyword matching errors | AI model refines context; longer matches prioritised |
| Prompt tuning needed | System prompt engineered for banking tone & safety |
| Schema migration issues | Auto-migration logic added for DB column changes |

---

## Future Roadmap

| Phase | Enhancement |
|-------|------------|
| Phase 1 | Voice Interface — Speech-to-text for accessibility |
| Phase 2 | Multilingual Support — Hindi, Tamil, and regional languages |
| Phase 3 | Analytics Dashboard — Usage metrics & response quality tracking |
| Phase 4 | Mobile App — React Native companion application |
| Phase 5 | Advanced RAG — Vector embeddings for semantic search |

---

## Conclusion

Capital Bank AI Assistant demonstrates a secure, intelligent, and cost-effective approach to banking automation:

- ✔ Local LLM deployment with Ollama & Phi-3 ensures data privacy
- ✔ RAG pipeline combines structured FAQs with generative reasoning
- ✔ Banking-only filtering guarantees domain-specific responses
- ✔ Scalable blueprint for enterprise AI in financial institutions
