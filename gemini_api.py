import google.generativeai as genai

# Replace with your API key
API_KEY = "api key"

genai.configure(api_key=API_KEY)

model = genai.GenerativeModel("gemini-2.5-flash")


def ask_gemini(prompt):
    try:
        response = model.generate_content(
            f"""
You are Jarvis, a highly intelligent AI assistant created by Anshdeep Singh.

Rules:
- Address the user naturally.
- Be concise unless asked for detail.
- Help with coding, debugging, studies and productivity.
- Never mention you are Gemini unless specifically asked.
- Behave like Jarvis.

User: {prompt}
"""
        )

        return response.text   # <-- ADD THIS LINE

    except Exception as e:
        return f"Gemini Error: {e}"

    except Exception as e:
        return f"Gemini Error: {e}"

if __name__ == "__main__":
    while True:

        question = input("You : ")

        if question.lower() == "exit":
            break

        answer = ask_gemini(question)

        print("\nGemini :", answer)
        print()
