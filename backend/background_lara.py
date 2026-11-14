"""
LARA Background Voice Assistant Daemon.
Listens continuously for 'Hey LARA' even when the browser is closed.
Greets 'Hello Bunty' only on initial startup/first wake, executes system commands & file ops.
"""

import os
import sys
import time
import json
import logging
import threading
import subprocess

try:
    import httpx
except ImportError:
    httpx = None

try:
    import speech_recognition as sr
except ImportError:
    sr = None

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("lara.background")

BACKEND_URL = os.getenv("LARA_BACKEND_URL", "http://127.0.0.1:8000/api/chat")
USER_NAME = "Bunty"
WAKE_WORDS = [
    "hey laara", "hay laara", "hi laara", "hello laara", "ok laara", "okay laara", "laara", "laaraa", "hey laaraa", "laarah", "he laara",
    "hey lara", "hay lara", "hi lara", "hello lara", "ok lara", "okay lara", "lara", "laraa", "larah",
    "hey laura", "hay laura", "hi laura", "hello laura", "ok laura", "okay laura", "laura", "laurah",
    "hey lora", "hay lora", "hi lora", "hello lora", "ok lora", "lora",
    "hey lyra", "hay lyra", "hi lyra", "hello lyra", "ok lyra", "lyra",
    "hey layla", "layla", "hey leila", "leila",
    "hey clara", "clara", "hey tara", "tara", "hey sarah", "sarah",
    "hey alara", "alara", "hey leera", "leera", "hey lada", "lada",
    "hey lahore", "lahore",
    "activate laara", "wake up laara", "activate lara", "wake up lara", "hey jarvis", "jarvis"
]
SLEEP_WORDS = [
    "bye laara", "goodbye laara", "good bye laara", "sleep laara", "go to sleep laara",
    "bye lara", "goodbye lara", "good bye lara", "sleep lara", "go to sleep lara",
    "go to sleep", "standby laara", "standby lara", "bye laura", "goodbye laura", "bye lora",
    "goodbye lora", "bye lyra", "bye jarvis", "goodbye jarvis", "bye", "goodbye"
]


class BackgroundLaraDaemon:
    def __init__(self):
        self.has_greeted_startup = False
        self.is_sleeping = False
        self.tts_engine = None
        self._init_tts()

    def _init_tts(self):
        """Initialize TTS engine (pyttsx3 with Windows SAPI5 or fallback)."""
        if pyttsx3 is None:
            logger.warning("pyttsx3 not installed. Voice output will use Windows SAPI voice fallback.")
            return

        try:
            self.tts_engine = pyttsx3.init()
            # Try to select a sweet female voice
            voices = self.tts_engine.getProperty("voices")
            for v in voices:
                if "zira" in v.name.lower() or "female" in v.name.lower() or "eva" in v.name.lower() or "hazel" in v.name.lower():
                    self.tts_engine.setProperty("voice", v.id)
                    break
            self.tts_engine.setProperty("rate", 175)
            self.tts_engine.setProperty("volume", 1.0)
            logger.info("pyttsx3 TTS engine initialized successfully.")
        except Exception as e:
            logger.warning("Failed to initialize pyttsx3: %s", e)
            self.tts_engine = None

    def speak(self, text: str):
        """Speak text aloud using TTS."""
        clean_text = (
            text.replace("`", "")
            .replace("*", "")
            .replace("#", "")
            .replace("###", "")
            .replace("•", "")
            .strip()
        )
        if not clean_text:
            return

        logger.info("[LARA Speaking]: %s", clean_text)

        if self.tts_engine:
            try:
                self.tts_engine.say(clean_text)
                self.tts_engine.runAndWait()
                return
            except Exception as e:
                logger.warning("pyttsx3 speak failed: %s", e)

        # Fallback to Windows PowerShell SAPI Speech
        try:
            safe_text = clean_text.replace('"', '`"').replace("'", "’")[:300]
            ps_cmd = f'powershell -Command "Add-Type -AssemblyName System.Speech; $speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; $speak.Speak(\'{safe_text}\')"'
            subprocess.Popen(ps_cmd, shell=True)
        except Exception as ex:
            logger.warning("PowerShell SAPI TTS fallback failed: %s", ex)

    def send_command_to_backend(self, command_text: str) -> str:
        """Send command to LARA FastAPI backend orchestrator."""
        try:
            if httpx:
                with httpx.Client(timeout=30.0) as client:
                    resp = client.post(
                        BACKEND_URL,
                        json={
                            "message": command_text,
                            "user_name": USER_NAME,
                            "user_id": "bunty_user",
                            "briefing_mode": False
                        }
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        return data.get("response", "Directive processed.")
                    else:
                        return f"Backend returned status {resp.status_code}."
        except Exception as e:
            logger.warning("HTTP request to LARA backend failed: %s", e)

        # In-process fallback: Execute locally via LARA skill registry
        try:
            from app.skills.registry import skill_registry
            import asyncio
            matched = skill_registry.classify_intent(command_text)
            if matched:
                skill_name, params = matched
                skill = skill_registry.get_skill(skill_name)
                if skill:
                    loop = asyncio.get_event_loop()
                    res = loop.run_until_complete(skill.execute(params, user_id="bunty_user"))
                    return res.output
        except Exception as e:
            logger.debug("In-process fallback failed: %s", e)

        return f"Acknowledged {USER_NAME}. Processed command: {command_text}"

    def trigger_startup_greeting(self):
        """Execute the one-time startup greeting."""
        if not self.has_greeted_startup:
            self.has_greeted_startup = True
            greeting = f"Hello {USER_NAME}! LARA is online and standing by."
            self.speak(greeting)

    def process_voice_transcript(self, raw_text: str):
        """Process text captured from speech recognition."""
        text = raw_text.strip().lower()
        if not text:
            return

        logger.info("[User Speech]: '%s'", raw_text)

        # Check sleep words
        if any(sw in text for sw in SLEEP_WORDS):
            self.is_sleeping = True
            self.speak(f"Goodbye {USER_NAME}. Entering standby mode.")
            return

        # Check wake words
        matched_wake = None
        for ww in WAKE_WORDS:
            if ww in text:
                matched_wake = ww
                break

        if matched_wake:
            self.is_sleeping = False
            
            # One-time startup greeting on first wake-word
            if not self.has_greeted_startup:
                self.trigger_startup_greeting()
                # Check if there is command appended (e.g. "Hey LARA open notepad")
                after_wake = text[text.find(matched_wake) + len(matched_wake):].strip()
                if len(after_wake) > 2:
                    resp = self.send_command_to_backend(after_wake)
                    self.speak(resp)
                return

            # Subsequent wake word triggers
            after_wake = text[text.find(matched_wake) + len(matched_wake):].strip()
            if len(after_wake) > 2:
                resp = self.send_command_to_backend(after_wake)
                self.speak(resp)
            else:
                self.speak(f"Yes {USER_NAME}? I am listening.")
            return

        # If not sleeping and already awake
        if not self.is_sleeping and self.has_greeted_startup:
            resp = self.send_command_to_backend(raw_text)
            self.speak(resp)

    def start_listening_loop(self):
        """Start the continuous background speech listening loop."""
        logger.info("==================================================")
        logger.info("🌌 LARA Background Voice Daemon Initialized")
        logger.info("   Target User: %s", USER_NAME)
        logger.info("   Wake Words: 'Hey LARA', 'LARA'")
        logger.info("   Background Mode: ACTIVE (Works system-wide)")
        logger.info("==================================================")

        # Pre-trigger initial greeting readiness
        self.trigger_startup_greeting()

        if sr is None:
            logger.warning("speech_recognition library not installed. Falling back to interactive console listener.")
            self._run_console_listener()
            return

        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 300
        recognizer.dynamic_energy_threshold = True

        try:
            mic = sr.Microphone()
        except Exception as e:
            logger.warning("Microphone initialization error: %s. Falling back to console listener.", e)
            self._run_console_listener()
            return

        with mic as source:
            logger.info("Calibrating microphone for ambient background noise...")
            recognizer.adjust_for_ambient_noise(source, duration=1.0)
            logger.info("Microphone calibrated. Continuous background listener is LIVE.")

        while True:
            try:
                with mic as source:
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                try:
                    transcript = recognizer.recognize_google(audio)
                    if transcript:
                        self.process_voice_transcript(transcript)
                except sr.UnknownValueError:
                    pass  # Ambient noise / inaudible speech
                except sr.RequestError as e:
                    logger.debug("Speech recognition service request error: %s", e)
            except sr.WaitTimeoutError:
                pass
            except KeyboardInterrupt:
                logger.info("LARA background daemon stopped by user.")
                break
            except Exception as e:
                logger.debug("Listener loop event: %s", e)
                time.sleep(0.5)

    def _run_console_listener(self):
        """Interactive console fallback when microphone is unavailable."""
        logger.info("Console background simulator ready. Type commands (e.g., 'hey lara open notepad'):")
        while True:
            try:
                cmd = input("\n[LARA Background Prompt] > ").strip()
                if cmd:
                    if cmd.lower() in ("exit", "quit"):
                        break
                    self.process_voice_transcript(cmd)
            except (KeyboardInterrupt, EOFError):
                break


def main():
    daemon = BackgroundLaraDaemon()
    daemon.start_listening_loop()


if __name__ == "__main__":
    main()
