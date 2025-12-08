import google.generativeai as genai
import requests
from PIL import Image
import io
import speech_recognition as sr
import asyncio
import edge_tts
import pygame
import os

# --- CONFIGURATION ---
API_KEY = "YOUR API KEY"
ESP32_IP = "192.168.1.XXX"
URL = f"http://192.168.1.XXX/capture"

# Voice Selection: "en-US-GuyNeural" (Male) or "en-US-AriaNeural" (Female)
VOICE = "en-US-GuyNeural" 

# --- SETUP GEMINI ---
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash') 

# --- SETUP AUDIO ---
recognizer = sr.Recognizer()
pygame.mixer.init()

async def generate_audio(text):
    """Generates human-like audio from text using Edge TTS"""
    communicate = edge_tts.Communicate(text, VOICE)
    await communicate.save("response.mp3")

def play_audio():
    """Plays the generated audio file"""
    try:
        pygame.mixer.music.load("response.mp3")
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        # Unload to release the file so we can delete/overwrite it next time
        pygame.mixer.music.unload() 
    except Exception as e:
        print(f"Audio Error: {e}")

def speak(text):
    """Orchestrates the speech generation and playback"""
    print(f"🗣️ JARVIS: {text}")
    try:
        # Run the async TTS generation
        asyncio.run(generate_audio(text))
        # Play the result
        play_audio()
        # Cleanup
        if os.path.exists("response.mp3"):
            os.remove("response.mp3")
    except Exception as e:
        print(f"Speaking Error: {e}")

def listen():
    """Listens for your voice command"""
    with sr.Microphone() as source:
        print("\n🎤 Listening... (Ask me something!)")
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source, timeout=5)
            query = recognizer.recognize_google(audio)
            print(f"You said: '{query}'")
            return query
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return None
        except Exception as e:
            print(f"Mic Error: {e}")
            return None

def get_image_from_esp32():
    try:
        print(f"📸 Snapping photo...")
        response = requests.get(URL, timeout=5)
        if response.status_code == 200:
            return Image.open(io.BytesIO(response.content))
        else:
            return None
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None

def main():
    speak("Visual systems online. I am ready.")
    
    chat = model.start_chat(history=[])
    
    # Updated System Prompt for more "Personality"
    system_instruction = (
        "You are Jarvis, a highly intelligent and helpful AI assistant. "
        "You can see via a camera. "
        "Your responses should be natural, conversational, and slightly witty. "
        "Do not be robotic. Act like a helpful friend. "
        "Keep responses short (under 2 sentences) for spoken conversation."
    )

    while True:
        user_query = listen()
        
        if user_query:
            if "exit" in user_query.lower() or "stop" in user_query.lower():
                speak("Shutting down. Goodbye.")
                break

            img = get_image_from_esp32()
            
            if img:
                try:
                    # We add "Answer concisely" to the prompt to keep speech fast
                    response = chat.send_message([system_instruction, img, user_query])
                    speak(response.text)
                except Exception as e:
                    speak("I'm having trouble connecting to the network.")
                    print(e)
            else:
                speak("I can't see anything. Check the camera connection.")

if __name__ == "__main__":

    main()
