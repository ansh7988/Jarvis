import google.generativeai as genai
import pyautogui
import time
from PIL import Image

# ---------------- Gemini ----------------

API_KEY = "new_api"

genai.configure(api_key=API_KEY)

model = genai.GenerativeModel("gemini-2.5-flash")


# ---------------- Screenshot ----------------

def capture_screen():
    screenshot = pyautogui.screenshot()
    screenshot.save("screen.png")
    return "screen.png"


# ---------------- Vision ----------------

def analyze_screen(prompt):

    print("Preparing to analyze screen...")

    time.sleep(5)   # Give user time to prepare the screen

    image_path = capture_screen()

    image = Image.open(image_path)


    response = model.generate_content([
        prompt,
        image
    ])

    return response.text


if __name__ == "__main__":

    print(analyze_screen())
