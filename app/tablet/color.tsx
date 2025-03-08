"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

export default function ColorSelection() {
  const [chosenColor, setChosenColor] = useState<string | null>(null);
  const [userName, setUserName] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    const storedName = sessionStorage.getItem("userName");
    if (!storedName) router.push("/tablet");
    setUserName(storedName);
  }, [router]);

  const handleColorSelect = (color: string) => {
    setChosenColor(color);
  };

  const handleActivate = async () => {
    if (!userName || !chosenColor) {
      alert("Complete all selections first!");
      return;
    }

    // Save user profile & trigger OSC activation
    await fetch("/api/save_user", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: userName, color: chosenColor }),
    });

    await fetch("/api/activate", { method: "POST" });

    // Transition to Phase 2 (Intro)
    await fetch("/api/start_intro", { method: "POST" });

    alert("The portal is now open.");
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-black text-white">
      <h1 className="text-2xl font-bold mb-4">What calls to you?</h1>
      <div className="grid grid-cols-3 gap-4">
        {["#999", "#ffb6c1", "#a55", "#5f5", "#3a3", "#a9f", "#f33", "#944", "#ff9"].map((color) => (
          <div
            key={color}
            className={`w-16 h-16 rounded-full cursor-pointer ${chosenColor === color ? "ring-4 ring-white" : ""}`}
            style={{ backgroundColor: color }}
            onClick={() => handleColorSelect(color)}
          />
        ))}
      </div>
      <button onClick={handleActivate} className="mt-4 px-4 py-2 bg-purple-500 rounded">
        Activate
      </button>
    </div>
  );
}