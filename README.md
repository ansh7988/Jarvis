# Jarvis
#This is code for Jarvis
import pyttsx3
import os
import speech_recognition as sr # type: ignore
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
api_key = "b12a6ef2b4862eef2da6cb71bb9ecdd9"
JARVIS_PASSWORD = "crazy coder"

# To make the assistant speak, you can use the following code snippet. This code initializes the text-to-speech engine and defines a function to convert text to speech.
def speak(audio):
    print(f"Jarvis: {audio}")

    engine = pyttsx3.init()

    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[0].id)

    engine.say(audio)
    engine.runAndWait()

# To wish the user based on the time of day, you can use the following code snippet. This code checks the current hour and greets the user accordingly.

def wishMe():
    hour = datetime.datetime.now().hour

    if 0 <= hour < 12:
        speak("Good Morning!")

    elif 12 <= hour < 18:
        speak("Good Afternoon!")

    else:
        speak("Good Evening!")

    speak("Hello Sir....  , I am Jarvis. Please tell me how may I help you")


english_jokes = [
    "Why don't programmers like nature? It has too many bugs.",

    "Why did the computer go to the doctor? Because it caught a virus.",

    "I told my computer I needed a break. It said, no problem, I'll go to sleep.",

    "Why was the math book sad? Because it had too many problems.",

    "Why don't skeletons fight each other? They don't have the guts.",

    "My boss told me to have a good day, so I went home.",

    "Why did the student eat his homework? Because the teacher said it was a piece of cake.",

    "I only know 25 letters of the alphabet. I don't know why.",

    "Why did the scarecrow win an award? Because he was outstanding in his field.",

    "Parallel lines have so much in common. It's a shame they'll never meet."
]



contacts = {"myself": "+91 9023143111", "brother": "+91 8054143121", "mom": "+91 8054143121", "dad": "+91 8288827818"}

# To take a password input from the user and grant access to Jarvis, you can use the following code snippet. This code prompts the user for a password and checks if it matches the predefined password before allowing access to the assistant.
password = input("Enter the password to access Jarvis: ")
if password != JARVIS_PASSWORD:
    speak("Incorrect password. Access denied.")
    exit()
speak("Access granted. Welcome to Jarvis!")
# To take voice commands from the user, you can use the following code snippet. This code listens for audio input and converts it to text using Google's speech recognition API.

def takeCommand():

    r = sr.Recognizer()

    with sr.Microphone() as source:
        print("Listening...")
        r.pause_threshold = 2
        audio = r.listen(source)

    try:
        print("Recognizing...")
        query = r.recognize_google(audio, language='en-in')
        print(f"User said: {query}\n")
        return query

    except Exception as e:
        print("Say that again please...")
        return "None"
    
    

# To open websites, applications, and play songs on YouTube using voice commands, you can use the following code snippet. This code listens for specific commands and performs the corresponding actions.
if __name__ == "__main__":
    speak("Initializing Jarvis")
    wishMe()

    active = False

    while True:

        query = takeCommand()

        if query == "None":
            continue

        query = query.lower()

        # Exit anytime
        if "goodbye " in query or"good bye jarvis" in query or "goodbye jarvis" in query or "good bye" in query:
            speak("Goodbye Sir...Take care")
            break

        # Wake word
        if not active:
            if "hi jarvis" in query or "hello jarvis" in query or "hey jarvis" in query or "wake up jarvis" in query or "wake up" in query or "hi" in query or "hello" in query or "HEY" in query:
                active = True
                speak("Yes Sir , I am ready to assist you")
            continue

        # Sleep mode
        if "go to sleep" in query:
            active = False
            speak("Sleeping Sir")
            continue

        # Commands
        if "open youtube" in query:
            speak("Opening YouTube")
            webbrowser.open("https://www.youtube.com")

        elif "open google" in query:
            speak("Opening Google")
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
            webbrowser.open("https://www.linkedin.com/")

        elif "open github" in query:
            speak("Opening GitHub")
            webbrowser.open("https://www.github.com/")

        elif "open ums" in query or"open lPU UMS" in query or "UMS" in query or "ums" in query:
            speak("Opening UMS")
            webbrowser.open("https://ums.lpu.in/lpuums/")

        elif "play" in query:
            song = query.replace("play", "")
            speak(f"Playing {song}")
            pywhatkit.playonyt(song)


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
            
            password = input("Enter Jarvis Password: ")

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
