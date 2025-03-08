// this might change to just indicators, or something sophisticated and manual
"use client";

import { useState } from "react";

interface AIPipelineControlsProps {
  onAiCommand: (pipeline: string, command: string) => void;
}

export default function AIPipelineControls({ onAiCommand }: AIPipelineControlsProps) {
  const pipelines = ["CV2STT_LLM_TTS", "TTS_only", "CV2_TTS", "Assignment", "Guardian"];
  const [selectedPipeline, setSelectedPipeline] = useState<string | null>(null);

  const handlePipelineClick = (pipeline: string) => {
    setSelectedPipeline(pipeline);
    onAiCommand(pipeline, "start");
  };

  return (
    <div className="mt-4 bg-[var(--bg-panel)] p-4 rounded-lg">
      <h2 className="text-lg font-semibold mb-2">AI Pipeline Controls</h2>
      {pipelines.map((pipeline) => (
        <button
          key={pipeline}
          onClick={() => handlePipelineClick(pipeline)}
          className={`px-4 py-2 rounded border-2 border-[var(--button-bg)] ${
            selectedPipeline === pipeline ? "bg-[var(--button-active)] text-white" : "text-[var(--text-primary)]"
          }`}
        >
          {pipeline}
        </button>
      ))}
    </div>
  );
}