import requests
import pyttsx3
import pyaudio
import json
import random
import os
from vosk import Model, KaldiRecognizer

MODEL_PATH = "vosk-model-small-en-us-0.15"
API_URL = "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/rub.json"
SAMPLE_RATE = 16000

engine = pyttsx3.init()
engine.setProperty('rate', 150)
engine.setProperty('volume', 0.9)

if not os.path.exists(MODEL_PATH):
    print(f"Model not found at '{MODEL_PATH}'.")
    exit(1)
model = Model(MODEL_PATH)


def speak(text):
    # Text-to-speech
    print(f"Assistant: {text}")
    try:
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        print(f"TTS Error: {e}")


def fetch_currency_data():
    # Currency rates from API
    try:
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        speak(f"Network error: {e}")
        return None


def invert_rate(rate):
    # To RUB converter
    return round(1 / rate, 2) if rate and rate != 0 else None



def cmd_dollar(data):
    # USD converter
    try:
        rub_rates = data.get('rub', {})
        rate = rub_rates.get('usd')
        if rate:
            rub_per_usd = invert_rate(rate)
            speak(f"The exchange rate for dollar is {rub_per_usd} rubles")
        else:
            speak("Could not get dollar exchange rate")
    except Exception as e:
        speak("Error processing dollar command")


def cmd_euro(data):
    # EURO converter
    try:
        rub_rates = data.get('rub', {})
        rate = rub_rates.get('eur')
        if rate:
            rub_per_eur = invert_rate(rate)
            speak(f"The exchange rate for euro is {rub_per_eur} rubles")
        else:
            speak("Could not get euro exchange rate")
    except Exception as e:
        speak("Error processing euro command")


def cmd_save(data):
    # Rates to file
    try:
        rub_rates = data.get('rub', {})
        filename = 'currency_rates.txt'
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("Currency Rates (1 RUB = X currency | 1 currency ≈ Y RUB)\n\n")
            for curr, rate in sorted(rub_rates.items()):
                inv = invert_rate(rate)
                f.write(f"{curr.upper():6s} | 1 RUB = {rate:.6f} | 1 {curr.upper():s} ≈ {inv} RUB\n")
        speak(f"Rates saved to file {filename}")
    except Exception as e:
        speak(f"Error saving file: {e}")


def cmd_count(data):
    # Number of currencies
    try:
        rub_rates = data.get('rub', {})
        count = len(rub_rates)
        speak(f"There are {count} currencies available")
    except Exception as e:
        speak("Error processing count command")


def cmd_random(data):
    # Random currency rate
    try:
        rub_rates = data.get('rub', {})
        if rub_rates:
            currency = random.choice(list(rub_rates.keys()))
            rate = rub_rates[currency]
            inv = invert_rate(rate)
            if inv:
                speak(f"Random currency: {currency.upper()}. One {currency.upper()} is approximately {inv} rubles")
            else:
                speak(f"Rate for {currency.upper()} is not available")
        else:
            speak("Could not get currency list")
    except Exception as e:
        speak("Error processing random command")



def process_command(text, data):
    # Recognizing and executing a command
    text_lower = text.lower().strip()

    if 'dollar' in text_lower or 'usd' in text_lower:
        cmd_dollar(data)
    elif 'euro' in text_lower or 'eur' in text_lower:
        cmd_euro(data)
    elif 'save' in text_lower:
        cmd_save(data)
    elif 'count' in text_lower:
        cmd_count(data)
    elif 'random' in text_lower:
        cmd_random(data)
    elif 'exit' in text_lower or 'quit' in text_lower or 'stop' in text_lower:
        speak("Goodbye!")
        return False
    else:
        speak("Command not recognized. Please try again.")
    return True



def main():
    # Starting voice assistant
    speak("The model is loaded. Say a command.")

    p = pyaudio.PyAudio()

    try:
        stream = p.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=SAMPLE_RATE,
                        input=True,
                        frames_per_buffer=4096)
        stream.start_stream()

        recognizer = KaldiRecognizer(model, SAMPLE_RATE)

        while True:
            audio_data = stream.read(4096, exception_on_overflow=False)

            if recognizer.AcceptWaveform(audio_data):
                result = json.loads(recognizer.Result())
                text = result.get('text', '').strip()

                if text:
                    print(f"You said: {text}")

                    currency_data = fetch_currency_data()
                    if currency_data:
                        if not process_command(text, currency_data):
                            break
                    else:
                        speak("Could not load rates.")

    except KeyboardInterrupt:
        speak("Work completed. Goodbye!")
    except Exception as e:
        speak(f"An error occurred: {e}")
        print(f"DEBUG: {e}")
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()


if __name__ == "__main__":
    main()
