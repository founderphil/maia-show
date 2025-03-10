"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function TabletUI() {
  const [userName, setUserName] = useState("");
  const router = useRouter();

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
    <div className="flex flex-col items-center justify-center min-h-screen bg-black text-white">
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