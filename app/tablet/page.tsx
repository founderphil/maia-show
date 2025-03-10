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

      sessionStorage.setItem("userName", userName);
      router.push("/tablet/color");
    } catch (error) {
      console.error("Failed to save user:", error);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-black text-white relative">
      {/* Audio Play Button (Absolute Upper-Left Corner) */}
      <button
        onClick={handlePlayAudio}
        className="absolute top-0 left-0 bg-gray-900 text-gray-800 px-3 py-2 text-xs rounded border-gray"
        style={{ zIndex: 1000, width: "25px", height: "25px", opacity: 0.3 }}
      >
        play
      </button>

      <h1 className="text-2xl font-bold mb-4">What do I call you?</h1>
      <input
        type="text"
        value={userName}
        onChange={(e) => setUserName(e.target.value)}
        placeholder="Who is this..."
        className="p-2 rounded mb-4 w-64 text-white border-b border-white border-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
      />
      <button onClick={handleCapture} className="mt-4 px-4 py-2 bg-purple-500 rounded">
        Capture
      </button>
    </div>
  );
}