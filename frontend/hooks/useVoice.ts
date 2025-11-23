"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { toast } from "@/lib/utils/toast";

/**
 * Voice Input/Output Hook
 * Web Speech API integration for hands-free operation
 * Supports both speech recognition (input) and synthesis (output)
 */

interface UseVoiceReturn {
  // Speech Recognition (Input)
  isListening: boolean;
  transcript: string;
  startListening: () => void;
  stopListening: () => void;
  resetTranscript: () => void;

  // Speech Synthesis (Output)
  isSpeaking: boolean;
  speak: (text: string, options?: SpeechOptions) => void;
  stopSpeaking: () => void;

  // Browser support
  isSupported: boolean;
}

interface SpeechOptions {
  rate?: number; // 0.1 to 10
  pitch?: number; // 0 to 2
  volume?: number; // 0 to 1
  lang?: string;
  voice?: SpeechSynthesisVoice;
}

export function useVoice(): UseVoiceReturn {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isSupported, setIsSupported] = useState(false);

  const recognitionRef = useRef<SpeechRecognition | null>(null);

  // Check browser support
  useEffect(() => {
    const SpeechRecognition =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition;

    const speechSynthesisSupported = "speechSynthesis" in window;

    setIsSupported(!!SpeechRecognition && speechSynthesisSupported);

    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = "en-US";

      recognition.onresult = (event: SpeechRecognitionEvent) => {
        let finalTranscript = "";
        let interimTranscript = "";

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcriptPiece = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcriptPiece + " ";
          } else {
            interimTranscript += transcriptPiece;
          }
        }

        setTranscript(
          (prev) => prev + finalTranscript + interimTranscript
        );
      };

      recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
        console.error("Speech recognition error:", event.error);
        setIsListening(false);

        if (event.error === "not-allowed") {
          toast.error("Microphone access denied");
        } else if (event.error === "no-speech") {
          toast.warning("No speech detected");
        } else {
          toast.error(`Speech recognition error: ${event.error}`);
        }
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = recognition;
    }
  }, []);

  const startListening = useCallback(() => {
    if (!isSupported) {
      toast.error("Speech recognition not supported in this browser");
      return;
    }

    if (recognitionRef.current && !isListening) {
      try {
        recognitionRef.current.start();
        setIsListening(true);
        toast.success("Listening...");
      } catch (error) {
        console.error("Failed to start recognition:", error);
        toast.error("Failed to start listening");
      }
    }
  }, [isSupported, isListening]);

  const stopListening = useCallback(() => {
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    }
  }, [isListening]);

  const resetTranscript = useCallback(() => {
    setTranscript("");
  }, []);

  const speak = useCallback(
    (text: string, options: SpeechOptions = {}) => {
      if (!isSupported) {
        toast.error("Speech synthesis not supported in this browser");
        return;
      }

      // Cancel any ongoing speech
      window.speechSynthesis.cancel();

      const utterance = new SpeechSynthesisUtterance(text);

      utterance.rate = options.rate ?? 1;
      utterance.pitch = options.pitch ?? 1;
      utterance.volume = options.volume ?? 1;
      utterance.lang = options.lang ?? "en-US";

      if (options.voice) {
        utterance.voice = options.voice;
      }

      utterance.onstart = () => {
        setIsSpeaking(true);
      };

      utterance.onend = () => {
        setIsSpeaking(false);
      };

      utterance.onerror = (event) => {
        console.error("Speech synthesis error:", event);
        setIsSpeaking(false);
        toast.error("Failed to speak text");
      };

      window.speechSynthesis.speak(utterance);
    },
    [isSupported]
  );

  const stopSpeaking = useCallback(() => {
    window.speechSynthesis.cancel();
    setIsSpeaking(false);
  }, []);

  return {
    isListening,
    transcript,
    startListening,
    stopListening,
    resetTranscript,
    isSpeaking,
    speak,
    stopSpeaking,
    isSupported,
  };
}

// Helper function to get available voices
export function getAvailableVoices(): Promise<SpeechSynthesisVoice[]> {
  return new Promise((resolve) => {
    let voices = window.speechSynthesis.getVoices();

    if (voices.length > 0) {
      resolve(voices);
    } else {
      window.speechSynthesis.onvoiceschanged = () => {
        voices = window.speechSynthesis.getVoices();
        resolve(voices);
      };
    }
  });
}
