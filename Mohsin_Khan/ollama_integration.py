import requests
import json
import time

BANKING_KEYWORDS = [
    "account", "loan", "card", "balance",
    "transfer", "bank", "interest", "emi",
    "credit", "debit", "kyc", "upi", "cheque",
    "deposit", "fd", "rd", "branch", "ifsc",
    "transaction", "payment", "savings", "checking",
    "mortgage", "investment", "fintech", "wallet",
    "rate", "rates", "support", "customer", "care",
    "help", "contact", "helpline", "number", "call",
    "document", "required", "identity", "proof", "open"
]

def is_banking_query(user_input):
    """
    Checks if the user's input contains any banking-related keywords.
    """
    input_lower = user_input.lower()
    return any(word in input_lower for word in BANKING_KEYWORDS)

def get_ollama_response(prompt, history=None, model="llama3:latest"):
    """
    Fetches a response from a local Ollama instance with improved timeout and error handling.
    """
    url = "http://127.0.0.1:11434/api/chat"
    
    messages = []
    
    system_prompt = """You are BankBot, a professional banking assistant.
You ONLY answer banking-related questions.
If the question is not related to banking, politely refuse.
Never answer questions about politics, sports, entertainment, coding, or personal advice.
Please provide clear, professional, and helpful responses."""

    messages.append({"role": "system", "content": system_prompt})
    
    if history:
        for msg in history[-5:]: 
            if msg.get("role") and msg.get("content"):
                messages.append({"role": msg["role"], "content": msg["content"]})
    
    messages.append({"role": "user", "content": prompt})
    
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "top_p": 0.9,
            "num_predict": 1000
        }
    }
    
    try:
        response = requests.post(url, json=payload, timeout=90)
        response.raise_for_status()
        data = response.json()
        return data.get("message", {}).get("content", "")
    except Exception as e:
        print(f"Ollama Error: {e}")
        if model == "llama3:latest":
            return get_ollama_response(prompt, history, model="llama3")
        return None

def stream_ollama_response(prompt, history=None, model="llama3:latest"):
    """
    Yields chunks of the response from a local Ollama instance for streaming.
    """
    url = "http://127.0.0.1:11434/api/chat"
    
    messages = []
    
    system_prompt = """You are BankBot, a professional banking assistant.
You ONLY answer banking-related questions.
If the question is not related to banking, politely refuse.
Never answer questions about politics, sports, entertainment, coding, or personal advice.
Please provide clear, professional, and helpful responses."""

    messages.append({"role": "system", "content": system_prompt})
    
    if history:
        for msg in history[-5:]: 
            if msg.get("role") and msg.get("content"):
                messages.append({"role": msg["role"], "content": msg["content"]})
    
    messages.append({"role": "user", "content": prompt})
    
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "options": {
            "temperature": 0.1,
            "top_p": 0.9,
            "num_predict": 1000
        }
    }
    
    try:
        response = requests.post(url, json=payload, timeout=90, stream=True)
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line:
                chunk = json.loads(line)
                if 'message' in chunk and 'content' in chunk['message']:
                    yield chunk['message']['content']
                if chunk.get('done'):
                    break
    except Exception as e:
        print(f"Ollama Stream Error: {e}")
        if model == "llama3:latest":
            yield from stream_ollama_response(prompt, history, model="llama3")
        else:
            yield None

def rewrite_banking_response(predefined_answer):
    """
    Uses Ollama to rewrite a predefined FAQ response for a more professional finish.
    """
    prompt = f"Rewrite this banking answer to be complete and detailed according to all formal rules:\n\n{predefined_answer}"
    return get_ollama_response(prompt)
