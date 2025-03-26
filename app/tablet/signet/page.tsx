"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

export default function SignetSelection() {
  const [chosenSignet, setChosenSignet] = useState<string | null>(null);
  const [userName, setUserName] = useState<string | null>(null);
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [activated, setActivated] = useState(false);
  const router = useRouter();

  useEffect(() => {
    // Retrieve user name from session storage
    const storedName = sessionStorage.getItem("userName");
    if (!storedName) {
      router.push("/tablet");
      return;
    }
    setUserName(storedName);

    // Initialize WebSocket connection
    const socket = new WebSocket("ws://localhost:8000/ws");

    socket.onopen = () => {
      console.log("✅ Connected to WebSocket");
      setWs(socket);
    };

    socket.onerror = (error) => {
      console.error("⚠️ WebSocket Error:", error);
    };

    return () => {
      socket.close();
    };
  }, [router]);

  const handleSignetSelect = (signet: string) => {
    setChosenSignet(signet);
  };

  const handleActivate = async () => {
    if (!userName || !chosenSignet) {
      alert("Complete all selections first!");
      return;
    }

    // Save user signet
    const response = await fetch("/api/proxy", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        pathname: "/save_user",
        body: { userName, chosenSignet },
      }),
    });

    // 📡 WebSocket Message to Start Phase 2
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: "start_intro" }));
    }

    // Backup API call to ensure Phase 2 starts
    await fetch("/api/proxy", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        pathname: "/start_phase",
        body: { phase: "intro" },
      }),
    });

    setActivated(true);
  };

  return (
    <div
      className={`flex flex-col items-center justify-center min-h-screen bg-black text-white transition-opacity duration-5000 ease-in-out ${
        activated ? "opacity-0" : "opacity-100"
      }`}
    >
      {!activated ? (
        <>
          <h1 className="text-2xl font-bold mb-4">
            {userName ? `${userName}, what calls to you?` : "What calls to you?"}
          </h1>
          <div className="grid grid-cols-3 gap-4">
            {["★", "☀", "✦", "✵", "❖", "✶", "⚝", "❂", "✧"].map((signet) => (
              <div
                key={signet}
                className={`w-16 h-16 flex items-center justify-center border-2 border-white cursor-pointer text-3xl ${
                  chosenSignet === signet ? "bg-white text-black ring-4 ring-white" : ""
                }`}
                onClick={() => handleSignetSelect(signet)}
              >
                {signet}
              </div>
            ))}
          </div>
          <button onClick={handleActivate} className="mt-4 px-4 py-2 bg-purple-500 rounded">
            Activate
          </button>
        </>
      ) : (
        <div className="fixed inset-0 flex items-center justify-center bg-black text-white text-4xl font-bold animate-fadeOut zoom-out">
          The portal is now open.
        </div>
      )}
    </div>
  );
}