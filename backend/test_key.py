# # backend/test_key.py

# from dotenv import load_dotenv
# import os

# print("---- LOADING ENV ----")
# load_dotenv()

# api_key = os.getenv("OPENAI_API_KEY")

# print("\n---- KEY CHECK ----")
# if not api_key:
#     print("❌ No API key found — check your .env file.")
#     exit()

# print("Key length    :", len(api_key))
# print("Key starts with:", api_key[:8])

# # Groq keys start with gsk_
# if not api_key.startswith("gsk_"):
#     print("❌ This is NOT a Groq key (should start with 'gsk_')")
#     exit()

# print("\n---- API CALL TEST (GROQ) ----")

# from openai import OpenAI

# # Groq uses OpenAI SDK but a DIFFERENT base URL
# client = OpenAI(
#     api_key=api_key,
#     base_url="https://api.groq.com/openai/v1"
# )

# try:
#     response = client.chat.completions.create(
#         model="llama3-70b-groq",   # Free high-quality model
#         messages=[{"role": "user", "content": "Hello from Groq!"}],
#         max_tokens=20
#     )
#     print("✅ SUCCESS! Groq says:", response.choices[0].message.content)

# except Exception as e:
#     print("❌ API ERROR:", e)
