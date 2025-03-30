"use client";

import React from "react";

interface PhaseNavigationProps {
  activePhase: string;
  onPhaseChange: (phase: string) => void;
}

const phases = [
  { label: "Tablet", value: "tablet" },
  { label: "Intro", value: "intro" },
  { label: "Lore", value: "lore" },
  { label: "Assignment", value: "assignment" },
  { label: "Departure", value: "departure" },
];

export default function PhaseNavigation({ activePhase, onPhaseChange }: PhaseNavigationProps) {
  return (
    <div className="flex space-x-2">
      {phases.map((phase) => (
        <button
          key={phase.value}
          onClick={() => onPhaseChange(phase.value)}
          className={`px-4 py-2 rounded border transition-all duration-150 ${
            activePhase === phase.value
              ? "bg-white text-black border-white"
              : "bg-transparent text-white border-white hover:bg-white hover:text-black"
          }`}
        >
          {phase.label}
        </button>
      ))}
    </div>
  );
}