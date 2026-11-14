"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { soundEffects } from "@/lib/audioFeedback";

export type VoiceState = "idle" | "listening" | "thinking" | "speaking" | "sleep";

interface UseVoiceAssistantProps {
  onCommandReceived: (command: string) => void;
  enabled?: boolean;
}

// Phonetic variants of "Hey LARA" / "Hey LAARA" for initial wake-up
const WAKE_PATTERNS = [
  "hey laara", "hay laara", "hi laara", "hello laara", "ok laara", "okay laara", "laara", "laaraa", "hey laaraa", "laarah", "hey laarah", "he laara", "a laara",
  "hey lara", "hay lara", "hi lara", "hello lara", "ok lara", "okay lara", "lara", "laraa", "larah", "hey larah",
  "hey laura", "hay laura", "hi laura", "hello laura", "ok laura", "okay laura", "laura", "laurah",
  "hey lora", "hay lora", "hi lora", "hello lora", "ok lora", "lora",
  "hey lyra", "hay lyra", "hi lyra", "hello lyra", "ok lyra", "lyra",
  "hey layla", "layla", "hey leila", "leila",
  "hey clara", "clara", "hey tara", "tara", "hey sarah", "sarah",
  "hey alara", "alara", "hey leera", "leera", "hey lada", "lada",
  "activate laara", "wake up laara", "activate lara", "wake up lara", "hey jarvis", "jarvis",
];

const SLEEP_PATTERNS = [
  "bye laara", "goodbye laara", "good bye laara", "sleep laara", "go to sleep laara",
  "bye lara", "goodbye lara", "good bye lara", "sleep lara", "go to sleep lara",
  "go to sleep", "standby laara", "standby lara", "bye laura", "goodbye laura", "bye lora",
  "goodbye lora", "bye lyra", "bye jarvis", "goodbye jarvis", "bye", "goodbye",
  "thank you lara", "thank you laara", "thank you", "thanks lara", "thanks laara", "thanks",
  "that's all lara", "that's all laara", "that's all", "thats all", "done lara", "stop listening", "standby"
];

export function useVoiceAssistant({
  onCommandReceived,
  enabled = true,
}: UseVoiceAssistantProps) {
  const [isWakeWordActive, setIsWakeWordActive] = useState<boolean>(true);
  const [voiceState, setVoiceState] = useState<VoiceState>("idle");
  const [transcript, setTranscript] = useState<string>("");
  const [interimTranscript, setInterimTranscript] = useState<string>("");
  const [isSpeechSupported, setIsSpeechSupported] = useState<boolean>(false);
  const [micPermission, setMicPermission] = useState<"prompt" | "granted" | "denied">("prompt");
  const [micError, setMicError] = useState<string | null>(null);

  const recognitionRef = useRef<any>(null);
  const isRecognizingRef = useRef<boolean>(false);
  const isProcessingCommandRef = useRef<boolean>(false);
  const restartBackoffMsRef = useRef<number>(600);
  const isListeningCommandRef = useRef<boolean>(false);
  const silenceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const followUpTimerRef = useRef<NodeJS.Timeout | null>(null);
  const restartTimerRef = useRef<NodeJS.Timeout | null>(null);
  const echoBufferTimerRef = useRef<NodeJS.Timeout | null>(null);
  const isSleepingRef = useRef<boolean>(false);
  const isSpeakingRef = useRef<boolean>(false);
  const isAudioPlayingRef = useRef<boolean>(false);
  const isDestroyedRef = useRef<boolean>(false);
  const audioElementRef = useRef<HTMLAudioElement | null>(null);
  const voicesListRef = useRef<SpeechSynthesisVoice[]>([]);
  const onCommandReceivedRef = useRef(onCommandReceived);

  // Keep callback reference updated
  useEffect(() => {
    onCommandReceivedRef.current = onCommandReceived;
  }, [onCommandReceived]);

  // Initialize SpeechSynthesis voices
  useEffect(() => {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) return;

    const loadVoices = () => {
      const voices = window.speechSynthesis.getVoices();
      voicesListRef.current = voices;
    };

    loadVoices();
    window.speechSynthesis.onvoiceschanged = loadVoices;
  }, []);

  const getSweetFemaleVoice = useCallback((): SpeechSynthesisVoice | null => {
    const voices = voicesListRef.current.length > 0
      ? voicesListRef.current
      : (typeof window !== "undefined" ? window.speechSynthesis.getVoices() : []);

    if (!voices || voices.length === 0) return null;

    const preferredFemaleNames = [
      "Microsoft Jenny Online (Natural)",
      "Microsoft Aria Online (Natural)",
      "Google UK English Female",
      "Google US English",
      "Samantha",
      "Victoria",
      "Karen",
      "Moira",
      "Microsoft Zira",
      "Microsoft Hazel",
    ];

    for (const name of preferredFemaleNames) {
      const found = voices.find((v) => v.name.toLowerCase().includes(name.toLowerCase()));
      if (found) return found;
    }

    const femaleVoice = voices.find(
      (v) => (v.lang.startsWith("en") || v.lang.startsWith("en-")) &&
             (v.name.toLowerCase().includes("female") || v.name.toLowerCase().includes("woman") || v.name.toLowerCase().includes("zira") || v.name.toLowerCase().includes("samantha"))
    );
    if (femaleVoice) return femaleVoice;

    const defaultEn = voices.find((v) => v.lang.startsWith("en"));
    return defaultEn || voices[0] || null;
  }, []);

  const safeStartRecognition = useCallback(() => {
    if (isDestroyedRef.current || isSpeakingRef.current || isAudioPlayingRef.current) return;
    const rec = recognitionRef.current;
    if (!rec || isRecognizingRef.current) return;

    try {
      rec.start();
    } catch (e: any) {
      if (e?.name === "InvalidStateError") {
        isRecognizingRef.current = true;
      }
    }
  }, []);

  const safeStopRecognition = useCallback(() => {
    const rec = recognitionRef.current;
    if (!rec) return;
    try {
      rec.stop();
    } catch {}
    isRecognizingRef.current = false;
  }, []);

  /**
   * Clean text and extract wake word if present.
   */
  const extractWakeWord = useCallback((text: string): { matched: string | null; remainder: string } => {
    const lower = text.toLowerCase().trim();

    for (const pattern of WAKE_PATTERNS) {
      const idx = lower.indexOf(pattern);
      if (idx !== -1) {
        const remainder = lower.substring(idx + pattern.length).replace(/^[,.:;\s]+/, "").trim();
        return { matched: pattern, remainder };
      }
    }

    const regex = /(?:^|\b)(?:hey|hay|hi|hello|he|a|ok|okay)?\s*(?:l+a+a+r+a+|l+a+r+a+|l+a+u+r+a+|l+o+r+a+|l+y+r+a+|l+a+a+r+a+h*|l+a+h+o+r+e+|l+e+e+r+a+|l+a+d+a+)(?:\b|$)/i;
    const match = regex.exec(lower);
    if (match) {
      const matchedStr = match[0].trim();
      const matchIdx = lower.indexOf(matchedStr);
      const remainder = lower.substring(matchIdx + matchedStr.length).replace(/^[,.:;\s]+/, "").trim();
      return { matched: matchedStr, remainder };
    }

    return { matched: null, remainder: lower };
  }, []);

  /**
   * Clean command text from leading wake words if repeated.
   */
  const sanitizeCommand = useCallback((text: string): string => {
    let cleaned = text.trim();
    for (const pattern of WAKE_PATTERNS) {
      const regex = new RegExp(`^${pattern}[,.:;\\s]*`, "i");
      cleaned = cleaned.replace(regex, "");
    }
    const phoneticRegex = /^(?:hey|hay|hi|hello|he|a|ok|okay)?\s*(?:l+a+a+r+a+|l+a+r+a+|l+a+u+r+a+|l+o+r+a+|l+y+r+a+|l+a+a+r+a+h*|l+a+h+o+r+e+|l+e+e+r+a+|l+a+d+a+)[,.:;\s]*/i;
    cleaned = cleaned.replace(phoneticRegex, "");
    return cleaned.trim();
  }, []);

  /**
   * Speaks text aloud with sweet female tuning - with strict echo prevention.
   */
  const speakText = useCallback(
    (rawText: string) => {
      if (typeof window === "undefined" || !("speechSynthesis" in window)) return;

      const cleanText = rawText
        .replace(/```[\s\S]*?```/g, "Code output is on your screen.")
        .replace(/`([^`]+)`/g, "$1")
        .replace(/\*\*([^*]+)\*\*/g, "$1")
        .replace(/\*([^*]+)\*/g, "$1")
        .replace(/\[([^\]]+)\]\([^\)]+\)/g, "$1")
        .replace(/#+\s/g, "")
        .replace(/[-*•>|]\s/g, "")
        .trim();

      if (!cleanText) return;

      try {
        if (audioElementRef.current) {
          audioElementRef.current.pause();
          audioElementRef.current.src = "";
        }
        window.speechSynthesis.cancel();

        safeStopRecognition();
        isSpeakingRef.current = true;
        isAudioPlayingRef.current = true;
        setVoiceState("speaking");

        const utterance = new SpeechSynthesisUtterance(cleanText);
        const bestVoice = getSweetFemaleVoice();
        if (bestVoice) {
          utterance.voice = bestVoice;
        }

        utterance.pitch = 1.08;
        utterance.rate = 1.02;
        utterance.volume = 1.0;

        utterance.onend = () => {
          isAudioPlayingRef.current = false;
          isProcessingCommandRef.current = false;

          if (isSleepingRef.current) {
            isSpeakingRef.current = false;
            setVoiceState("sleep");
            return;
          }

          if (echoBufferTimerRef.current) clearTimeout(echoBufferTimerRef.current);
          echoBufferTimerRef.current = setTimeout(() => {
            isSpeakingRef.current = false;
            isListeningCommandRef.current = true;
            setVoiceState("listening");

            if (!isDestroyedRef.current && !isAudioPlayingRef.current) {
              safeStartRecognition();
            }
          }, 700);

          if (followUpTimerRef.current) clearTimeout(followUpTimerRef.current);
          followUpTimerRef.current = setTimeout(() => {
            if (!isSpeakingRef.current && isListeningCommandRef.current) {
              isListeningCommandRef.current = false;
              setVoiceState("idle");
            }
          }, 15000);
        };

        utterance.onerror = () => {
          isAudioPlayingRef.current = false;
          isSpeakingRef.current = false;
          isProcessingCommandRef.current = false;
          if (!isSleepingRef.current) {
            isListeningCommandRef.current = true;
            setVoiceState("listening");
            setTimeout(() => {
              if (!isDestroyedRef.current) safeStartRecognition();
            }, 500);
          }
        };

        window.speechSynthesis.speak(utterance);
      } catch (err) {
        console.warn("TTS playback notice:", err);
        isAudioPlayingRef.current = false;
        isSpeakingRef.current = false;
        isProcessingCommandRef.current = false;
      }
    },
    [getSweetFemaleVoice, safeStartRecognition, safeStopRecognition]
  );

  /**
   * Plays Studio Neural Voice Audio with absolute echo isolation.
   */
  const playNeuralAudio = useCallback(
    async (audioSrc: string | null | undefined, fallbackText?: string) => {
      if (typeof window === "undefined") return;

      if (!audioSrc && fallbackText) {
        speakText(fallbackText);
        return;
      }

      if (!audioSrc) {
        isProcessingCommandRef.current = false;
        return;
      }

      try {
        if ("speechSynthesis" in window) {
          window.speechSynthesis.cancel();
        }

        if (audioElementRef.current) {
          audioElementRef.current.pause();
          audioElementRef.current.src = "";
        }

        safeStopRecognition();
        isSpeakingRef.current = true;
        isAudioPlayingRef.current = true;
        setVoiceState("speaking");

        const audio = new Audio(audioSrc);
        audioElementRef.current = audio;

        audio.onended = () => {
          isAudioPlayingRef.current = false;
          isProcessingCommandRef.current = false;

          if (isSleepingRef.current) {
            isSpeakingRef.current = false;
            setVoiceState("sleep");
            return;
          }

          if (echoBufferTimerRef.current) clearTimeout(echoBufferTimerRef.current);
          echoBufferTimerRef.current = setTimeout(() => {
            isSpeakingRef.current = false;
            isListeningCommandRef.current = true;
            setVoiceState("listening");

            if (!isDestroyedRef.current && !isAudioPlayingRef.current) {
              safeStartRecognition();
            }
          }, 700);

          if (followUpTimerRef.current) clearTimeout(followUpTimerRef.current);
          followUpTimerRef.current = setTimeout(() => {
            if (!isSpeakingRef.current && isListeningCommandRef.current) {
              isListeningCommandRef.current = false;
              setVoiceState("idle");
            }
          }, 15000);
        };

        audio.onerror = (e) => {
          console.warn("Neural audio playback notice, falling back:", e);
          isAudioPlayingRef.current = false;
          if (fallbackText) {
            speakText(fallbackText);
          } else {
            isSpeakingRef.current = false;
            isProcessingCommandRef.current = false;
            safeStartRecognition();
          }
        };

        await audio.play();
      } catch (err) {
        console.warn("Neural audio play notice:", err);
        isAudioPlayingRef.current = false;
        if (fallbackText) {
          speakText(fallbackText);
        } else {
          isSpeakingRef.current = false;
          isProcessingCommandRef.current = false;
        }
      }
    },
    [safeStartRecognition, safeStopRecognition, speakText]
  );

  const lastCommandRef = useRef<string>("");
  const lastCommandTimeRef = useRef<number>(0);

  /**
   * Dispatches command safely with lock to avoid duplicate parallel executions.
   */
  const dispatchCommand = useCallback(
    (commandText: string) => {
      const clean = commandText.trim();
      const now = Date.now();

      // Deduplication lock: Reject identical command within 3.5s to prevent toggle loops
      if (
        clean.toLowerCase() === lastCommandRef.current.toLowerCase() &&
        now - lastCommandTimeRef.current < 3500
      ) {
        return;
      }

      if (!clean || clean.length < 2 || isProcessingCommandRef.current || isSpeakingRef.current) {
        return;
      }

      lastCommandRef.current = clean;
      lastCommandTimeRef.current = now;
      isProcessingCommandRef.current = true;

      if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);

      setTranscript(clean);
      setVoiceState("thinking");
      setInterimTranscript("");

      onCommandReceivedRef.current(clean);
    },
    []
  );

  /**
   * Request microphone permission explicitly via getUserMedia.
   */
  const requestMicAccess = useCallback(async () => {
    if (typeof window === "undefined" || !navigator?.mediaDevices?.getUserMedia) {
      return false;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      stream.getTracks().forEach((track) => track.stop());
      setMicPermission("granted");
      setMicError(null);

      if (recognitionRef.current && isWakeWordActive) {
        safeStartRecognition();
      }
      return true;
    } catch (err: any) {
      console.warn("Microphone access notice:", err);
      setMicPermission("denied");
      setMicError(err.message || "Microphone access denied by browser.");
      return false;
    }
  }, [isWakeWordActive, safeStartRecognition]);

  /**
   * Initializes Speech Recognition instance once on mount.
   */
  useEffect(() => {
    if (typeof window === "undefined") return;

    isDestroyedRef.current = false;

    const SpeechRecognition =
      (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

    if (!SpeechRecognition) {
      console.warn("Web Speech API not supported in this browser environment.");
      setIsSpeechSupported(false);
      return;
    }

    setIsSpeechSupported(true);
    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-US";
    recognition.maxAlternatives = 3;

    recognition.onstart = () => {
      isRecognizingRef.current = true;
      restartBackoffMsRef.current = 600;
      setMicPermission("granted");
      setMicError(null);
    };

    recognition.onresult = (event: any) => {
      // Discard all speech input while LARA is speaking or processing a prior command
      if (isSpeakingRef.current || isAudioPlayingRef.current || isProcessingCommandRef.current) {
        return;
      }

      let finalStr = "";
      let interimStr = "";
      let hasFinal = false;

      for (let i = event.resultIndex; i < event.results.length; ++i) {
        const item = event.results[i];
        if (item.isFinal) {
          finalStr += item[0].transcript;
          hasFinal = true;
        } else {
          interimStr += item[0].transcript;
        }
      }

      const activeText = (finalStr || interimStr).trim().toLowerCase();
      if (!activeText) return;

      setInterimTranscript(interimStr || finalStr);

      // 1. SLEEP & DISMISS DETECTION ("Bye LARA", "Thank you", "That's all", "Done")
      if (SLEEP_PATTERNS.some((p) => activeText.includes(p))) {
        if (followUpTimerRef.current) clearTimeout(followUpTimerRef.current);
        if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
        soundEffects.playSleepChime();
        isSleepingRef.current = true;
        isListeningCommandRef.current = false;
        setVoiceState("sleep");
        setInterimTranscript("");

        if (activeText.includes("thank") || activeText.includes("thanks") || activeText.includes("that's all") || activeText.includes("done")) {
          speakText("You are very welcome Bunty. Standing by. Say 'Hey LARA' anytime.");
        } else {
          speakText("Goodbye Bunty. Entering standby mode. Say 'Hey LARA' to wake me.");
        }
        return;
      }

      // 2. WAKE-WORD DETECTION & SINGLE-COMMAND DISPATCH
      const isAwake = isListeningCommandRef.current && !isSleepingRef.current;

      if (!isAwake) {
        // Cold Standby: ONLY activate if wake-word is present
        const { matched, remainder } = extractWakeWord(activeText);
        if (!matched) {
          return;
        }

        isSleepingRef.current = false;
        isListeningCommandRef.current = true;
        setVoiceState("listening");
        soundEffects.playWakeChime();

        const cleanCmd = sanitizeCommand(remainder);
        if (cleanCmd.length >= 2) {
          if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);

          // If speech is finalized or after 900ms silence, dispatch command
          if (hasFinal) {
            dispatchCommand(cleanCmd);
          } else {
            silenceTimerRef.current = setTimeout(() => {
              dispatchCommand(cleanCmd);
            }, 900);
          }
        } else {
          if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
          silenceTimerRef.current = setTimeout(() => {
            if (isListeningCommandRef.current && !isSpeakingRef.current && !isAudioPlayingRef.current && !isProcessingCommandRef.current) {
              speakText("Hello Bunty! LARA is online and standing by.");
            }
          }, 800);
        }
      } else {
        // Active Session: Listen for follow-up command
        if (followUpTimerRef.current) clearTimeout(followUpTimerRef.current);

        const cleanCmd = sanitizeCommand(activeText);
        if (cleanCmd.length >= 2) {
          if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);

          if (hasFinal) {
            dispatchCommand(cleanCmd);
          } else {
            silenceTimerRef.current = setTimeout(() => {
              dispatchCommand(cleanCmd);
            }, 900);
          }
        }
      }
    };

    recognition.onerror = (event: any) => {
      if (event.error === "not-allowed" || event.error === "service-not-allowed") {
        setMicPermission("denied");
        setMicError("Microphone access blocked. Click microphone icon in address bar to allow.");
        isRecognizingRef.current = false;
      } else if (event.error === "no-speech") {
        restartBackoffMsRef.current = 500;
      } else if (event.error === "aborted") {
        isRecognizingRef.current = false;
      } else {
        console.debug("Speech recognition non-fatal notice:", event.error);
        restartBackoffMsRef.current = Math.min(restartBackoffMsRef.current * 1.5, 3000);
      }
    };

    recognition.onend = () => {
      isRecognizingRef.current = false;
      if (isWakeWordActive && !isDestroyedRef.current && !isSpeakingRef.current && !isAudioPlayingRef.current) {
        if (restartTimerRef.current) clearTimeout(restartTimerRef.current);
        restartTimerRef.current = setTimeout(() => {
          if (!isDestroyedRef.current && isWakeWordActive && !isSpeakingRef.current && !isAudioPlayingRef.current) {
            safeStartRecognition();
          }
        }, restartBackoffMsRef.current);
      }
    };

    recognitionRef.current = recognition;

    if (isWakeWordActive && enabled) {
      safeStartRecognition();
    }

    return () => {
      isDestroyedRef.current = true;
      if (echoBufferTimerRef.current) clearTimeout(echoBufferTimerRef.current);
      if (restartTimerRef.current) clearTimeout(restartTimerRef.current);
      if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
      if (followUpTimerRef.current) clearTimeout(followUpTimerRef.current);
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch {}
      }
    };
  }, [isWakeWordActive, enabled, extractWakeWord, sanitizeCommand, speakText, safeStartRecognition, dispatchCommand]);

  const toggleWakeWord = useCallback(() => {
    setIsWakeWordActive((prev) => {
      const next = !prev;
      if (next) {
        isSleepingRef.current = false;
        setVoiceState("idle");
        safeStartRecognition();
      } else {
        isListeningCommandRef.current = false;
        setVoiceState("idle");
        safeStopRecognition();
      }
      return next;
    });
  }, [safeStartRecognition, safeStopRecognition]);

  const startManualListening = useCallback(() => {
    soundEffects.playWakeChime();
    isSleepingRef.current = false;
    isListeningCommandRef.current = true;
    setVoiceState("listening");
    safeStartRecognition();
  }, [safeStartRecognition]);

  const stopManualListening = useCallback(() => {
    isListeningCommandRef.current = false;
    setVoiceState("idle");
    setInterimTranscript("");
    safeStopRecognition();
  }, [safeStopRecognition]);

  return {
    isWakeWordActive,
    voiceState,
    transcript,
    interimTranscript,
    isSpeechSupported,
    micPermission,
    micError,
    toggleWakeWord,
    speakText,
    playNeuralAudio,
    requestMicAccess,
    startManualListening,
    stopManualListening,
  };
}
