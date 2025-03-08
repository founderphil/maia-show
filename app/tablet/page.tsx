"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function TabletUI() {
  const [name, setName] = useState("");
  const router = useRouter();

  const handleCapture = async () => {
    if (!name.trim()) {
      alert("Please enter a name.");
      return;
    }

    // Save name & send to backend
    await fetch("/api/save_user", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    });

    sessionStorage.setItem("userName", name);
    router.push("/tablet/color");
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-black text-white">
      <h1 className="text-2xl font-bold mb-4">What do I call you?</h1>
      <input
        type="text"
        id="nameInput"
        value={name}
        onChange={(e) => setName(e.target.value)}
        placeholder="Who is this..."
        className="text-black p-2 rounded"
      />
      <button onClick={handleCapture} className="mt-4 px-4 py-2 bg-purple-500 rounded">Capture</button>
    </div>
  );
}