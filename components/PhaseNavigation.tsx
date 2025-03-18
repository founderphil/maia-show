"use client";

import { useState } from "react";

interface PhaseNavigationProps {
  activePhase: string;
  onPhaseChange: (phase: string) => void;
}

export default function PhaseNavigation({ activePhase, onPhaseChange }: PhaseNavigationProps) {
  const phases = ["tablet", "intro", "lore & Qs", "assignment", "departure"];

  return (
    <div className="flex space-x-2 mb-4">
      {phases.map((phase) => (
        <button
          key={phase}
          onClick={() => onPhaseChange(phase)}
          className={`px-4 py-2 rounded border-2 border-[var(--button-bg)] transition duration-300
            ${activePhase === phase ? "bg-purple-600 text-white" : "bg-transparent text-[var(--text-primary)]"}
          `}
        >
          {phase.toUpperCase()}
        </button>
      ))}
    </div>
  );
}