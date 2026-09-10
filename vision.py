import os
from google import genai
import pyautogui
import time
from PIL import Image

# ---------------- Gemini ----------------

# Load the key from an environment variable instead of hardcoding it.
# Set it once in your terminal / system env:
#   setx GEMINI_API_KEY "your-key-here"   (Windows, then restart terminal)
#   export GEMINI_API_KEY="your-key-here" (macOS/Linux)
API_KEY = "AQ.Ab8RN6JmbCzbw6v"

if not API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY environment variable is not set. "
        "Set it before running Jarvis."
    )

client = genai.Client(api_key=API_KEY)

# ---------------- Screenshot ----------------

def capture_screen():
    screenshot = pyautogui.screenshot()
    screenshot.save("screen.png")
    return "screen.png"


# ---------------- Vision ----------------

def analyze_screen(prompt):

    print("Preparing to analyze screen...")

    time.sleep(5)  # Give user time to prepare the screen

    image_path = capture_screen()

    image = Image.open(image_path)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[prompt, image],
    )

    return response.text
