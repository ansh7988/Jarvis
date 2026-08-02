from google import genai
import pyautogui
import time
from PIL import Image

# ---------------- Gemini ----------------

API_KEY = "Api"

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
        model="gemini-2.5")
