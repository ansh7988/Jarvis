from google import genai




# Replace with your API key
API_KEY = "Api"
client = genai.Client(api_key=API_KEY)
import re

def clean_for_speech(text):
    """
    Removes Markdown and formatting symbols so Jarvis speaks naturally.
    """

    # Remove code blocks
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)

    # Remove inline code
    text = re.sub(r"`([^`]*)`", r"\1", text)

    # Convert markdown links:
    # [OpenAI](https://...) -> OpenAI
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)

    # Remove markdown headings
    text = re.sub(r"^#+\s*", "", text, flags=re.MULTILINE)

    # Remove bullets
    text = re.sub(r"^\s*[-*•]\s*", "", text, flags=re.MULTILINE)

    # Remove bold / italic markers
    text = text.replace("**", "")
    text = text.replace("*", "")
    text = text.replace("__", "")
    text = text.replace("_", "")

    # Remove > quote markers
    text = re.sub(r"^\s*>\s*", "", text, flags=re.MULTILINE)

    # Remove extra blank lines
    text = re.sub(r"\n{2,}", "\n", text)

    # Collapse multiple spaces
    text = re.sub(r"[ \t]+", " ", text)

    return text.strip()

def ask_gemini(prompt):
    try:

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"""
You are Jarvis, a highly intelligent AI assistant created by AnshDeep Singh.

Rules:
- Address the user naturally.
- Be concise unless asked for detail.
- Help with coding, debugging, studies and productivity.
- Never mention you are Gemini unless specifically asked.
- Behave like Jarvis.

User:
{prompt}
"""
        )

        return clean_for_speech(response.text)

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
