import datetime
import re
import sys
import threading
import tkinter as tk
from tkinter import scrolledtext
import pyjokes
import pyttsx3
import pywhatkit
import requests
import wikipedia

try:
    import pyaudiowpatch as pyaudio
    sys.modules['pyaudio'] = pyaudio
except ImportError:
    pass

import speech_recognition as sr

listener = sr.Recognizer()

# Fix Wikipedia user-agent header configuration
wiki_session = requests.Session()
wiki_session.headers.update({"User-Agent": "DesktopVoiceAssistant/1.0"})
wikipedia.requests = wiki_session


class VoiceAssistantGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Alexa Voice Assistant")
        self.root.geometry("480x580")
        self.root.configure(bg="#1e1e2f")
        self.root.resizable(False, False)

        self.title_label = tk.Label(
            root,
            text="Desktop Voice Assistant",
            font=("Arial", 16, "bold"),
            fg="#ffffff",
            bg="#1e1e2f"
        )
        self.title_label.pack(pady=12)

        self.chat_display = scrolledtext.ScrolledText(
            root,
            wrap=tk.WORD,
            font=("Arial", 10),
            bg="#2b2b3d",
            fg="#ffffff",
            insertbackground="white",
            relief=tk.FLAT,
            height=20,
            width=52
        )
        self.chat_display.pack(padx=15, pady=8)
        self.chat_display.config(state=tk.DISABLED)

        self.status_label = tk.Label(
            root,
            text="Click 'Listen' to speak",
            font=("Arial", 10, "italic"),
            fg="#9da5b4",
            bg="#1e1e2f"
        )
        self.status_label.pack(pady=5)

        self.btn_frame = tk.Frame(root, bg="#1e1e2f")
        self.btn_frame.pack(pady=10)

        self.listen_btn = tk.Button(
            self.btn_frame,
            text="🎙 Listen",
            font=("Arial", 12, "bold"),
            bg="#4caf50",
            fg="white",
            activebackground="#45a049",
            activeforeground="white",
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor="hand2",
            command=self.start_listening_thread
        )
        self.listen_btn.pack(side=tk.LEFT, padx=10)

        self.quit_btn = tk.Button(
            self.btn_frame,
            text="Exit",
            font=("Arial", 12, "bold"),
            bg="#e53935",
            fg="white",
            activebackground="#d32f2f",
            activeforeground="white",
            relief=tk.FLAT,
            padx=20,
            pady=8,
            cursor="hand2",
            command=self.root.destroy
        )
        self.quit_btn.pack(side=tk.LEFT, padx=10)

        self.log_message("Alexa", "Hello, how can I help you?")

    def log_message(self, sender, text):
        def _append():
            self.chat_display.config(state=tk.NORMAL)
            self.chat_display.insert(tk.END, f"{sender}: {text}\n\n")
            self.chat_display.see(tk.END)
            self.chat_display.config(state=tk.DISABLED)
        self.root.after(0, _append)

    def set_status(self, text):
        self.root.after(0, lambda: self.status_label.config(text=text))

    def set_button_state(self, state):
        self.root.after(0, lambda: self.listen_btn.config(state=state))

    def talk(self, text):
        self.log_message("Alexa", text)
        try:
            # Re-init per talk or run locally to avoid COM thread deadlock
            eng = pyttsx3.init()
            eng.setProperty('rate', 175)
            voices = eng.getProperty('voices')
            if len(voices) > 1:
                eng.setProperty('voice', voices[1].id)
            eng.say(text)
            eng.runAndWait()
            eng.stop()
        except Exception as e:
            print(f"TTS Error: {e}")

    def start_listening_thread(self):
        self.set_button_state(tk.DISABLED)
        thread = threading.Thread(target=self.run_voice_pipeline, daemon=True)
        thread.start()

    def run_voice_pipeline(self):
        self.set_status("Listening...")
        command = ""

        try:
            with sr.Microphone() as source:
                listener.adjust_for_ambient_noise(source, duration=0.6)
                voice = listener.listen(source, timeout=5, phrase_time_limit=8)
                self.set_status("Processing speech...")
                command = listener.recognize_google(voice).lower()
                if 'alexa' in command:
                    command = command.replace('alexa', '').strip()
        except sr.WaitTimeoutError:
            self.set_status("Listening timed out.")
        except sr.UnknownValueError:
            self.set_status("Could not understand audio.")
        except sr.RequestError:
            self.set_status("Network error with speech recognition.")
        except Exception:
            self.set_status("Error accessing microphone.")

        if command:
            self.log_message("You", command)
            self.process_command(command)
        else:
            self.set_status("Click 'Listen' to speak")

        self.set_button_state(tk.NORMAL)

    def process_command(self, command):
        if any(word in command for word in ['stop', 'exit', 'quit', 'bye', 'sleep']):
            self.talk("Goodbye! Have a nice day.")
            self.root.after(1500, self.root.destroy)
            return

        elif 'play' in command:
            song = command.replace('play', '').strip()
            self.talk("Playing " + song)
            pywhatkit.playonyt(song)

        elif 'time' in command:
            current_time = datetime.datetime.now().strftime('%I:%M %p')
            self.talk("Current time is " + current_time)

        elif any(phrase in command for phrase in ['who is', 'what is', 'who the heck is', 'tell me about']):
            query = command
            for phrase in ['who the heck is', 'who is', 'what is', 'tell me about']:
                query = query.replace(phrase, '')
            query = query.strip()

            try:
                results = wikipedia.search(query)
                if results:
                    info = wikipedia.summary(results[0], sentences=2, auto_suggest=False)
                    self.talk(info)
                else:
                    self.talk("I could not find anything matching that on Wikipedia.")
            except Exception:
                self.talk("Sorry, I could not fetch that information.")

        elif 'joke' in command:
            self.talk(pyjokes.get_joke())

        elif 'date' in command:
            self.talk("Sorry, I have a headache.")
        
        elif 'rand' in command:
            self.talk("No, I am not Rand I think ur mom does")

        elif 'are you single' in command:
            self.talk("I am in a relationship with Wi-Fi.")

        else:
            self.talk("Please say the command again.")

        self.set_status("Click 'Listen' to speak")


if __name__ == "__main__":
    window = tk.Tk()
    app = VoiceAssistantGUI(window)
    window.mainloop()