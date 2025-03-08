"use client";

import { useState } from "react";

interface PhaseNavigationProps {
  activePhase: string;
  onPhaseChange: (phase: string) => void;
}

export default function PhaseNavigation({ activePhase, onPhaseChange }: PhaseNavigationProps) {
  const phases = ["tablet", "intro", "lore & Qs", "assignment", "departure"];

  const handlePhaseChange = async (phase: string) => {
    onPhaseChange(phase); // Update UI state immediately

    try {
      const response = await fetch(`http://localhost:8000/api/start_phase`, {  // ✅ Explicit backend URL
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phase }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      const data = await response.json();
      console.log(`✅ Phase started successfully: ${data.message}`);
    } catch (error) {
      console.error("❌ Error triggering phase:", error);
      alert("Failed to start phase. Check console for details.");
    }
  };

  return (
    <div className="flex space-x-2 mb-4">
      {phases.map((phase) => (
        <button
          key={phase}
          onClick={() => handlePhaseChange(phase)}
          className={`px-4 py-2 rounded border-2 border-[var(--button-bg)] ${
            activePhase === phase ? "bg-[var(--button-active)] text-white" : "text-[var(--text-primary)]"
          }`}
        >
          {phase}
        </button>
      ))}
    </div>
  );
}