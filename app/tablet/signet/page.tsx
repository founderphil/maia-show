"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

export default function SignetSelection() {
  const [chosenSignet, setChosenSignet] = useState<string | null>(null);
  const [userName, setUserName] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    const storedName = sessionStorage.getItem("userName");
    if (!storedName) {
      router.push("/tablet");
      return;
    }
    setUserName(storedName);
  }, [router]);

  const handleSignetSelect = (signet: string) => {
    setChosenSignet(signet);
  };

  const handleActivate = async () => {
    if (!userName || !chosenSignet) {
      alert("Complete all selections first!");
      return;
    }

    //Save user signet 
    const response = await fetch("/api/proxy", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        pathname: "/save_user", 
        body: { userName, chosenSignet },
      }),
    });

    const result = await response.json();
    console.log("User saved:", result);

    // move on to intro
    await fetch("/api/proxy", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pathname: "/start_intro" }),
    });

    alert("The portal is now open.");
  };


  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-black text-white">
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
    </div>
  );
}