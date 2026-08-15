import requests
import json

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJwbGF0Zm9ybV9pZCI6ImltdGl0aGFsIiwidGVuYW50X2lkIjoiZGVtb190ZW5hbnQiLCJ1c2VyX2lkIjoidTEiLCJ1c2VyX3JvbGUiOiJjb21wbGlhbmNlX21hbmFnZXIifQ.Ho9PreUT3UCeunepCgSUJatfI2akkAxuisZNzCK11Hc"

BASE = "http://127.0.0.1:8000/api/v1/chat"
headers = {"Authorization": f"Bearer {token}"}

# Q1
r1 = requests.post(BASE, headers=headers, json={
    "question": "How do I assign a control owner?"
})
answer1 = r1.json()["answer"]
print("Q1 ANSWER:", answer1)
print()

# Q2
conversation_history = [
    {"role": "user", "content": "How do I assign a control owner?"},
    {"role": "assistant", "content": answer1},
]

r2 = requests.post(BASE, headers=headers, json={
    "question": "What role do they need?",  
    "conversation_history": conversation_history,
})
print("Q2 ANSWER:", r2.json()["answer"])