from unittest import result

import speech_recognition as sr # type: ignore
import os
import datetime
import webbrowser
import pywhatkit
import wikipedia
import pyautogui
import pyjokes
import psutil
import random
import time
import requests
import smtplib
import pygame
import getpass
import threading
from gemini_ai import ask_gemini
from memory import remember, recall
from voice import speak, stop_speaking, is_speaking
from vision import analyze_screen



# import eel
# eel.init("web")
api_key = "weathe_key"
JARVIS_PASSWORD = "pass_key"

#Notes folder
NOTES_FOLDER = "Jarvis_Notes.txt"
EMAIL_ADDRESS= "anshdeep7988@gmail.com"
EMAIL_PASSWORD = "email_passkey"

gui_window = None
active = False
# Only one thread may use the microphone at a time. Without this, the
# continuous GUI listening loop and a command that itself needs to listen
# again (e.g. "write a note") can both try to open the mic at once, which
# crashes PyAudio with "OSError: Invalid error code".
mic_lock = threading.Lock()

def set_gui(window):
    global gui_window
    gui_window = window
#Status file fucntion

def update_status(status):
    with open("status.txt", "w") as file:
        file.write(status)

#Jarvis  startup sound 
def play_startup_sound():
    pygame.mixer.init()
    pygame.mixer.music.load("sounds/startup.mp3")
    pygame.mixer.music.play()

def play_scan_sound():
    pygame.mixer.init()
    pygame.mixer.music.load("sounds/scan.mp3")
    pygame.mixer.music.play()

# To make the assistant speak, you can use the following code snippet. This code initializes the text-to-speech engine and defines a function to convert text to speech.


# To wish the user based on the time of day, you can use the following code snippet. This code checks the current hour and greets the user accordingly.

def wishMe():
    hour = datetime.datetime.now().hour

    if 0 <= hour < 12:
        speak(random.choice(morning_quotes))

    elif 12 <= hour < 18:
        speak("Good Afternoon!")

    else:
        speak("Good Evening!")

    speak("System check !")
    speak("Hello Sir....  , I am Jarvis. Please tell me how may I help you")
 # Function for email
def sendEmail(receiver, message):

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()

    server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)

    server.sendmail(
        EMAIL_ADDRESS,
        receiver,
        message
    )

    server.quit()

email_contacts = {"Anshdeep Singh": "anshdeep7988@gmail.com","dad": "anshbatra1992@gmail.com"}


english_jokes = [
    "Why don't programmers like nature? It has too many bugs.",

    "Why did the computer go to the doctor? Because it caught a virus.",

    "I told my computer I needed a break. It said, no problem, I'll go to sleep.",

    "Why was the math book sad? Because it had too many problems.",

    "Why don't skeletons fight each other? They don't have the guts.",

    "My boss told me to have a good day, so I went home.",

    "Why did the student eat his homework? Because the teacher said it was a piece of cake.",

    "Name the kind of tree you can hold in your hand? A palm tree!",


    "Parallel lines have so much in common. It's a shame they'll never meet."
]

responses = [
    "Always ready, sir.",
    "At your service, sir.",
    "Ready for your next command, sir."
]

morning_quotes = [
    "Good morning, sir. Every expert was once a beginner. Let's build something amazing today.",
    "Rise and shine, sir. Small consistent efforts create extraordinary results.",
    "Good morning. Today is another opportunity to become a better version of yourself.",
    "Wake up, sir. Your future is built by what you do today, not tomorrow.",
    "Good morning. Stay focused, stay disciplined, and success will follow.",
    "Remember, sir. Consistency beats talent when talent doesn't work hard.",
    "Today is a fresh start. Let's make it productive.",
    "Keep learning, keep building, and never stop improving.",
    "Great things take time, sir. Every line of code you write makes you a better engineer.",
    "Good morning, sir. Your only competition is the person you were yesterday."
]


contacts = {"myself": "+91 9023143111", "brother": "+91 8054143121", "mom": "+91 8054143121", "dad": "+91 8288827818"}

# To take voice commands from the user, you can use the following code snippet. This code listens for audio input and converts it to text using Google's speech recognition API.

def takeCommand():

    r = sr.Recognizer()

    with mic_lock:
        with sr.Microphone() as source:
            update_status("LISTENING...")
            print("Listening")
            r.pause_threshold = 2
            audio = r.listen(source)

    try:
        update_status("PROCESSING")
        print("Recognizing...")
        query = r.recognize_google(audio, language='en-in')
        print(f"User said: {query}\n")
        return query

    except Exception as e:
        update_status("IDLE")
        print("Say that again please...")
        return "None"


def listen_for_stop_word(timeout=1, phrase_time_limit=2):
    """Short, quick listen used only to catch 'stop' / 'stop jarvis' while
    Jarvis is speaking. Uses a short timeout so it never blocks for long,
    and stays completely separate from the normal takeCommand() flow.
    Returns True if a stop word was heard, False otherwise (including on
    timeout or unrecognized speech)."""
    r = sr.Recognizer()
    try:
        with mic_lock:
            with sr.Microphone() as source:
                r.pause_threshold = 0.5
                audio = r.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)

        query = r.recognize_google(audio, language='en-in').lower()
        return "stop" in query

    except Exception:
        return False
    
    
# def start_jarvis():
#     pass
def process_gui_command(query):
    global active
    
    query = query.lower()
    print(f"Processing command: {query}")

    if "solve this error" in query or "fix this error" in query:

        if gui_window:
            gui_window.response_label.setText("🐞 DETECTING ERROR...")

        speak("Certainly sir. Analyzing the error on your screen.")

        play_scan_sound()

        error_prompt = """
    You are Jarvis.

    Analyze the screenshot.

    Your task is ONLY to identify programming errors or compiler/runtime errors.

    If an error is present:
    1. Explain what the error means.
    2. Explain why it happened.
    3. Give the exact steps to fix it.

    If no error exists, simply reply:

    'I don't detect any programming error on the screen, sir.'

    Keep the answer under 120 words.
    """

        result = analyze_screen(error_prompt)

        print("\n========== GEMINI RESPONSE ==========\n")
        print(result)
        print("\n=====================================\n")
        speak(result)

        if gui_window:
            gui_window.response_label.setText("✓ ERROR ANALYZED")

        return True


    elif (
        "analyze my screen" in query
        or "analyse my screen" in query
        or "analyze screen" in query
        or "analyse screen" in query
        or "what's on my screen" in query
        or "explain my screen" in query
        or "explain screen" in query
    ):
        if gui_window:
            gui_window.response_label.setText("🔍 PREPARING SCREEN...")
        speak("Certainly sir. You have five seconds to prepare your screen.")

        play_scan_sound()      # 🔊 Add this line
        if gui_window:
            gui_window.response_label.setText("🧠 ANALYZING...")
        screen_prompt = """
    You are Jarvis.

    Analyze everything visible on the screen.

    Describe the important information naturally.

    Keep the answer under 120 words.
    """

        try:
            result = analyze_screen(screen_prompt)
        except Exception as e:
            print(e)
            speak("Sorry sir, the Gemini API limit has been reached. Please try again later.")
            return True
        print(result)

        speak(result)
        if gui_window:
            gui_window.response_label.setText("READY")

        if gui_window:
            gui_window.response_label.setText("✓ SCREEN ANALYZED")

        return True

        # Exit anytime
    if "goodbye " in query or"good bye jarvis" in query or "goodbye jarvis" in query or "good bye" in query:
        speak("Goodbye Sir...Take care")
        time.sleep(5)
        return False
    
    if "open youtube" in query:
        speak("Opening YouTube")
        webbrowser.open("https://www.youtube.com")

    elif "open google" in query:
        speak("Opening Google")
        time.sleep(0.6)
        webbrowser.open("https://www.google.com")

    elif "open notepad" in query:
        speak("Opening Notepad")
        os.system("notepad")

    elif "open calculator" in query:
        speak("Opening Calculator")
        os.system("calc")

    elif "open windows" in query:
        speak("Opening Command Prompt")
        os.system("start cmd")

    elif "open chat gpt" in query:
        speak("Opening ChatGPT")
        webbrowser.open("https://chat.openai.com/")

    elif "open chrome" in query:
        speak("Opening Google Chrome")
        os.system("start chrome")

    elif "open spotify" in query:
        speak("Opening Spotify")
        webbrowser.open("https://www.spotify.com/")

    elif"open whatsapp" in query:
        speak("Opening WhatsApp")
        webbrowser.open("https://web.whatsapp.com/")

    elif "open linkedin" in query:
        speak("Opening LinkedIn")
        print("Opening LinkedIn...")
        webbrowser.open("https://linkedin.com/")
    

    elif "open github" in query:
        speak("Opening GitHub")
        webbrowser.open("https://www.github.com/")

    elif "open ums" in query or"open lPU UMS" in query or "UMS" in query or "ums" in query:
        speak("Opening UMS")
        webbrowser.open("https://ums.lpu.in/lpuums/")

    elif "open jio hotstar" in query or "jio hotstart" in query or "hotstar" in query:
        speak("Opening JioHotstar")
        webbrowser.open("https://www.hotstar.com/in/home")

    elif "play" in query:
        song = query.replace("play", "")
        speak(f"Playing {song}")
        pywhatkit.playonyt(song)

    #Tell about your developer
    elif ("who is your developer" in query or "who made you" in query or "who created you" in query or "who developed you" in query or "developer" in query):
        speak("I was created by Anshdeep Singh . He is continuously improving me with new features and capabilities.")

    #How's everything going
    elif "how are you" in query:
        speak("All systems are operating normally, sir. I am ready to assist you with whatever you need.")

    #Are u ready ?
    elif "are you ready" in query:
        speak(random.choice(responses))

    #To get the current time, you can use the following code snippet. This code listens for the command "time" and responds with the current time.

    elif "time" in query:
        strTime = datetime.datetime.now().strftime("%I:%M %p")
        speak(f"The time is {strTime}")

    elif "date" in query:
        strDate = datetime.datetime.now().strftime("%B %d, %Y")
        speak(f"Today's date is {strDate}")
    

    elif "day" in query:
        strDay = datetime.datetime.now().strftime("%A")
        speak(f"Today is {strDay}")

    elif "month" in query:
        strMonth = datetime.datetime.now().strftime("%B")
        speak(f"This month is {strMonth}")

    elif "year" in query:
        strYear = datetime.datetime.now().strftime("%Y")
        speak(f"This year is {strYear}")

    elif "week" in query:
        strWeek = datetime.datetime.now().strftime("%U")
        speak(f"This week is {strWeek}")

    elif "tomorrow" in query:
        strTomorrow = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%B %d, %Y")
        speak(f"Tomorrow's date is {strTomorrow}")

    elif "yesterday" in query:
        strYesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%B %d, %Y")
        speak(f"Yesterday's date was {strYesterday}")

    
# To control the system volume, you can use the following code snippet. This code listens for the commands "volume down", "volume up", and "volume mute" and adjusts the system volume accordingly.
    elif "volume down" in query:
        speak("Turning down the volume")
        pyautogui.press("volumedown")

    elif "volume up" in query:
        speak("Turning up the volume")
        pyautogui.press("volumeup")

    elif "volume mute" in query:
        speak("Muting the volume")
        pyautogui.press("volumemute")


    elif "pause" in query or "pause video" in query or "pause song" in query:
        speak("Pausing the video")
        pyautogui.press("k")

    elif "resume" in query or "resume video" in query :
        speak("resuming the video")
        pyautogui.press("k")
    
# To search Wikipedia and read the summary, you can use the following code snippet. This code listens for the command "wikipedia" followed by a search query, retrieves the summary from Wikipedia, and reads it aloud.
    
    elif "wikipedia" in query:


        speak("Searching Wikipedia")

        search_query = query.replace("wikipedia", "").strip()
        
        print(f"Searching Wikipedia for {search_query}...")

        try:
            wikipedia.set_lang("en")

            result = wikipedia.summary(search_query, sentences=2)

            print("\nAccording to Wikipedia:\n")
            print(result)

            speak("According to Wikipedia")
            speak(result)

        except Exception as e:
            print("Error:", e)
            speak("Sorry Sir, I could not find anything on Wikipedia")

    #To search Google for a query, you can use the following code snippet. This code listens for the command "search google for" followed by a search query and opens the search results in the default web browser.

    elif "search google for" in query:
        search_query = query.replace("search google for", "").strip()
        speak(f"Searching Google for {search_query}")
        webbrowser.open(f"https://www.google.com/search?q={search_query}")

    # To select text , save file , copy or paste 
    elif "select all" in query:
        speak("Selecting all text")
        pyautogui.hotkey("ctrl", "a")

    elif "copy" in query:
        speak("Copying selected text")
        pyautogui.hotkey("ctrl", "c")

    elif "paste" in query:
        speak("Pasting from clipboard")
        pyautogui.hotkey("ctrl", "v")

    elif "save " in query:
        speak("Saving the file in 3 seconds")
        time.sleep(3)
        pyautogui.hotkey("ctrl", "s")

    elif "cut" in query:
        speak("Cutting selected text")
        pyautogui.hotkey("ctrl", "x")

# To take a screenshot, you can use the following code snippet. This code listens for the command "screenshot" and saves a screenshot of the current screen to a specified location.

    elif "take screenshot" in query:
        

        speak("Taking screenshot in 3 seconds")
        time.sleep(3)

        now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        filename = f"screenshot_{now}.png"

        path = rf"C:\Users\AnshDeep Singh Batra\OneDrive\Pictures\Screenshots\{filename}"

        screenshot = pyautogui.screenshot()

        screenshot.save(path)

        speak("Screenshot saved successfully")

# Now , The dictation feature
    elif "start dictation" in query:

        speak("Dictation mode will start in 5 seconds")

        time.sleep(5)

        speak("Dictation mode started")

        while True:

            text = takeCommand().lower()

            if text == "":
                continue

            if "stop dictation" in text:
                speak("Dictation mode stopped")
                break

    # Punctuation support
            text = text.replace("comma", ",")
            text = text.replace("full stop", ".")
            text = text.replace("question mark", "?")

            if "new line" in text:
                pyautogui.press("enter")
                continue

            pyautogui.write(text + " ", interval=0.05)

    # Search Youtube for a video and play it
    elif "search youtube for" in query:

        search_query = query.replace("search youtube for", "").strip()

        speak(f"Searching YouTube for {search_query}")

        url = f"https://www.youtube.com/results?search_query={search_query}"

        webbrowser.open(url)

    # To perform basic arithmetic calculations, you can use the following code snippet. This code listens for arithmetic expressions and evaluates them using the eval() function.
    elif any(op in query for op in ["+", "-", "*", "/"]):

        try:

            result = eval(query)

            print("Answer =", result)

            speak(f"The answer is {result}")

        except Exception as e:
            print("Error:", e)
            speak("Sorry Sir, I could not calculate that")

# Weather information with API
    elif "weather" in query:

        try:

            city = "Ludhiana"

            url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"

            response = requests.get(url)

            data = response.json()

            temp = data["main"]["temp"]

            description = data["weather"][0]["description"]

            speak(f"The temperature in {city} is {temp:.1f} degrees Celsius with {description}")

        except Exception as e:

            print(e)

            speak("Sorry Sir, I could not get the weather information")

#Jokes
    elif "tell me a joke" in query or "joke" in query:

        joke = random.choice(english_jokes)

        print(joke)

        speak(joke)

#Battery status

    elif "battery" in query:

        battery = psutil.sensors_battery()

        percentage = battery.percent

        charging = battery.power_plugged

        if charging:
            speak(f"Battery is {percentage} percent and charging")
        else:
            speak(f"Battery is {percentage} percent and not charging")

    #Refresh Jarvish 
    elif "refresh" in query:
        play_startup_sound()
        time.sleep(1)
        speak("Refreshing all modules.")
        speak("Refresh complete.All systems are online.")

        
# System information
    elif "system info" in query or "system information" in query:

        cpu = psutil.cpu_percent(interval=1)

        memory = psutil.virtual_memory().percent

        speak(f"CPU usage is {cpu} percent and memory usage is {memory} percent")

# System shutdown, restart, and log off
    elif "lock computer" in query:
        speak("Locking computer")
        os.system("rundll32.exe user32.dll,LockWorkStation")

    elif "shutdown" in query:
        speak("Shutting down the computer in 10 seconds")
        time.sleep(10)
        os.system("shutdown /s /t 10")

    elif "restart" in query:
        speak("Restarting the computer in 10 seconds")
        time.sleep(10)
        os.system("shutdown /r /t 10")

    elif "cancel shutdown" in query or "abort shutdown" in query:
        speak("Aborting shutdown")
        os.system("shutdown /a")

    elif "cancel restart" in query or "abort restart" in query:
        speak("Aborting restart")
        os.system("shutdown /a")

    elif "sleep" in query:
        speak("Putting the computer to sleep")
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")

    # To take the access back 

    elif "lock jarvis" in query:

        speak("Jarvis has been locked")

        active = False
        
        password = getpass.getpass("Enter the password to access Jarvis: ")

        if password == JARVIS_PASSWORD:
            speak("Access granted")
        else:
            speak("Access denied")
            exit()

#To send whatsapp messages instantly, you can use the following code snippet. This code listens for the command "send whatsapp message" followed by the recipient's number and the message content, and sends the message using the pywhatkit library.
    elif "send whatsapp to" in query:

        name = query.replace("send whatsapp to ", "").strip()

        if name in contacts:

            speak("What is the message?")

            message = takeCommand()

            pywhatkit.sendwhatmsg_instantly(contacts[name],message,wait_time=10,tab_close=False)

            speak("Message sent successfully")

        else:

            speak("Contact not found")

    #To take notes and save them to a text file, you can use the following code snippet. This code listens for the command "take note" followed by the note content, and saves it to a text file.
    elif "write a note" in query:

        speak("Start speaking. Say save note when finished.")

        notes = ""

        while True:

            text = takeCommand().lower()

            if "save note" in text:
                break

            notes += text + "\n"

        with open("Jarvis_Notes.txt", "a") as file:
            file.write(notes)

        speak("Note saved successfully")


    elif "open my notes" in query:

        speak("Opening your notes")
        os.startfile("Jarvis_Notes.txt")

    elif "read my notes" in query:

        with open("Jarvis_Notes.txt", "r") as file:
            notes = file.read()

        speak(notes)

    #To open folders and files on the system, you can use the following code snippet. This code listens for the command "open folder" followed by the folder path, and opens the specified folder using the default file explorer.
    elif "open downloads" in query or "open download" in query:

        speak("Opening Downloads")

        os.startfile(os.path.join(os.path.expanduser("~"), "Downloads"))

    elif "open documents" in query:

        speak("Opening Documents")

        os.startfile(os.path.join(os.path.expanduser("~"), "Documents"))

    elif "open pictures" in query:

        speak("Opening Pictures")

        os.startfile(os.path.join(os.path.expanduser("~"), "Pictures"))

    elif "open screenshots" in query:

        speak("Opening Screenshots")

        os.startfile(os.path.join(os.path.expanduser("~"), "Pictures", "Screenshots"))

    elif "open This PC" in query or "open my computer" in query:

        speak("Opening This PC")

        os.startfile(os.path.join(os.path.expanduser("~"), "This PC"))

    #To send email

    elif "send email" in query:

        speak("Whom should I send the email to")

        name = takeCommand().lower()
        print("You said:", name)

        if name in email_contacts:

            receiver = email_contacts[name]

            speak("What is the message")

            message = takeCommand()

        try:

            sendEmail(receiver, message)

            speak("Email sent successfully")

        except Exception as e:

            print(e)

            speak("Sorry sir, I could not send the email")

        else:
            speak("Contact not found")


    #Gemini API
    else:
        speak("Let me think...")
        answer=ask_gemini(query)
        speak(answer)

    return True

def startup_sequence():
    play_startup_sound()
    time.sleep(1)
    speak("Initializing Jarvis")
    time.sleep(3)
    wishMe()

# To open websites, applications, and play songs on YouTube using voice commands, you can use the following code snippet. This code listens for specific commands and performs the corresponding actions.
if __name__ == "__main__":


    # eel.start(
    #     "index.html",size=(1400,900),block=False)
    # start_jarvis()
    startup_sequence()
    while True:
        query = takeCommand()

        if query == "None":
            continue

        query = query.lower()
        if not process_gui_command(query):
            break
