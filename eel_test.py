# We have used eel library to make a dedicated window for Jarvis to host its GUI rather then to run it on chrome
# Testing code 
import eel

eel.init("web")

eel.start(
    "index.html",
    size=(1400, 900)
)
