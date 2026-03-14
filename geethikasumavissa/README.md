# 🏦 BankBot AI – Banking FAQ Chatbot

## 📌 Overview

**BankBot AI** is an intelligent banking assistant built using **Python, Streamlit, and Ollama (Phi-3 LLM)**.
It helps users quickly get answers to common banking questions such as account balance, loans, ATM cards, and net banking.

The chatbot first checks a **bank knowledge library (JSON)** for predefined answers.
If the question is banking-related but not found in the library, it uses an **AI model (Phi-3 via Ollama)** to generate a response.

The system also includes **user authentication, conversation history, chat management, and a financial dashboard**.

---

# 🚀 Features

### 1️⃣ AI Banking Assistant

* Uses **Phi-3 LLM via Ollama** for intelligent responses.
* Provides **clear and concise banking answers**.
* Generates answers for queries not present in the knowledge base.

### 2️⃣ Banking Knowledge Library

* Predefined banking FAQs stored in `bank_library.json`.
* Faster responses for common queries like:

  * Balance check
  * Loan information
  * Net banking
  * Credit score
  * ATM card requests

### 3️⃣ Banking Domain Restriction

* The chatbot only answers **banking-related questions**.
* Non-banking queries return:

```
Please ask banking related questions only.
```

### 4️⃣ User Authentication System

Users can:

* Create accounts
* Login securely
* Access personal conversations

User data is stored in:

```
users.json
```

### 5️⃣ Chat Management

Users can manage conversations with:

* 🆕 Create new chats
* 📌 Pin important chats
* ✏ Rename chats
* 🗑 Delete chats
* 📜 View chat history

### 6️⃣ Smart Chat Titles

Chat titles are automatically generated based on the **first user message**.

Example:

```
User message: "How to check balance?"
Chat title: "How To Check Balance?"
```

### 7️⃣ Quick Banking Actions

Users can instantly access common services:

* 💰 Check balance
* 📄 Loan information
* ☎ Customer support

### 8️⃣ Banking Dashboard

A simple financial dashboard shows:

* Account balance
* Active loans
* Credit score
* Balance growth chart
* Expense distribution chart

---

# 🛠 Tech Stack

| Technology   | Purpose                       |
| ------------ | ----------------------------- |
| Python       | Backend logic                 |
| Streamlit    | Web interface                 |
| Ollama       | Local LLM inference           |
| Phi-3 Model  | AI response generation        |
| JSON         | Knowledge base & user storage |
| Scikit-learn | Text similarity processing    |
| Matplotlib   | Dashboard charts              |

---

# 📂 Project Structure

```
BankBot-AI/
│
├── bankbot_app.py        # Main Streamlit application
├── bank_library.json     # Banking FAQ knowledge base
├── users.json            # User accounts and chat history
├── README.md             # Project documentation
```

---

# ⚙️ Installation

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/geethikasumavissa/BankBot-AI.git
cd BankBot-AI
```

### 2️⃣ Install Required Libraries

```bash
pip install streamlit ollama scikit-learn matplotlib
```

### 3️⃣ Install Ollama

Download and install Ollama:

https://ollama.com

Then pull the Phi-3 model:

```bash
ollama pull phi3
```

---

# ▶️ Running the Application

Run the Streamlit app:

```bash
streamlit run bankbot_app.py
```

The application will open in your browser:

```
http://localhost:8501
```

---

# 👥 User Workflow

1️⃣ Create an account
2️⃣ Login to the system
3️⃣ Start a new chat
4️⃣ Ask banking questions
5️⃣ View responses from the knowledge base or AI model
6️⃣ Manage chats (pin, rename, delete)

---

# 🔒 Data Storage

User information is stored locally in:

```
users.json
```

Stored data includes:

* Username
* Password
* Conversations
* Chat titles
* Pinned chats

---

# 📊 Example Banking Questions

You can ask:

```
How to check balance?
What loans are available?
How to apply for ATM card?
What is the interest rate?
How to reset net banking password?
```

---

# 🧠 AI Model

BankBot uses:

**Phi-3 LLM via Ollama**

Advantages:

* Runs locally
* Fast responses
* No external API required
* Privacy-friendly

---

# 🎯 Future Improvements

Possible enhancements:

* Secure password hashing
* Real bank API integration
* Voice-based banking assistant
* Multi-language support
* Advanced financial analytics
* Database storage instead of JSON

---

# 👨‍💻 Team

Developed as part of a **Banking AI Chatbot Project**.
Project: Capital Bank AI Assistant
Internship: Infosys Springboard
Team Members:
* Vissa Geethika Suma
* Lokeshkanna
* Nithin Singh
* Sushant Pawar
* Aakash
* Moshin Khan

---

# 📜 License

This project is for **educational and research purposes**.

