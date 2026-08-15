from dotenv import load_dotenv
load_dotenv(".env")

from app.generation.orchestrator import generate_answer

result = generate_answer(
    "How do I assign a control owner?",
    platform_id="imtithal",
    tenant_id="demo_tenant",
)

print("ANSWER:")
print(result["answer"])
print()
print("GROUNDED:", result["grounded"])
print("NUM CITATIONS:", len(result["citations"]))