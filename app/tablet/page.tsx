"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

export default function TabletUI() {
  const [userName, setUserName] = useState("");
  const router = useRouter();
  const [audio, setAudio] = useState<HTMLAudioElement | null>(null);

  useEffect(() => {
    const newAudio = new Audio("/audio/tablet_audio.wav");
    newAudio.loop = true;
    newAudio.volume = 1;
    setAudio(newAudio);

    return () => {
      newAudio.pause();
      newAudio.currentTime = 0;
    };
  }, []);

  const handlePlayAudio = () => {
    if (audio) {
      audio.play().catch((error) => console.log("Autoplay blocked:", error));
    }
  };

  const handleCapture = async () => {
    if (!userName.trim()) {
      alert("Please enter a name.");
      return;
    }

    try {
      const response = await fetch("/api/proxy", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          pathname: "/save_user",
          body: { userName },
        }),
      });

      const result = await response.json();
      console.log("User saved:", result);

      fetch("/api/proxy", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pathname: "/run_tablet_tts" }),
      }).catch((err) => console.error("Background TTS failed:", err));

      sessionStorage.setItem("userName", userName);
      router.push("/tablet/color");
    } catch (error) {
      console.error("Failed to save user:", error);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-black text-white relative">
      {/* <button
        onClick={handlePlayAudio}
        className="absolute top-0 left-0 bg-gray-900 text-gray-800 px-3 py-2 text-xs rounded border-gray"
        style={{ zIndex: 1000, width: "25px", height: "25px", opacity: 0.3 }}
      >
        play
      </button> */}

      <label className="mb-2 text-lg text-purple-300" htmlFor="userNameInput">
       ★ ☀ ✦ ✵ ❖ ✶ ⚝ ❂ ✧ 
      </label>
      <input
        id="userNameInput"
        type="text"
        value={userName}
        onChange={(e) => setUserName(e.target.value)}
        placeholder="What shall I call you? Enscribe your name here…"
        className="p-4 text-xl text-white border-b-2 border-white focus:outline-none bg-transparent w-1/2 text-center"
        autoFocus
      />
      <button
        onClick={handleCapture}
        className={`mt-8 px-6 py-3 rounded-md text-lg transition-opacity duration-200 ${
          userName.trim()
            ? "bg-purple-500 opacity-100"
            : "bg-purple-900 opacity-10 cursor-not-allowed"
        }`}
        disabled={!userName.trim()}
      >
        Continue
      </button>
    </div>
  );
}
