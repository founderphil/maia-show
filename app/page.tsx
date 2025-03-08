"use client";

import { useState, useEffect } from "react";
import PhaseNavigation from "@/components/PhaseNavigation";
import LightingControls from "@/components/LightingControls";
import AIPipelineControls from "@/components/AIPipelineControls";
import LiveDataConsole from "@/components/LiveDataConsole";

export default function ShowrunnerUI() {
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [aiStatus, setAiStatus] = useState<string>("idle");
  const [activePhase, setActivePhase] = useState("intro");
  const [userData, setUserData] = useState({
    name: "Querent",
    color: "Purple",
    signet: "Star",
    responses: [],
  });
  const [lighting, setLighting] = useState({
    maiaLED: 50,
    houseLight1: 80,
    houseLight2: 100,
    chairSpot: 80,
    maiaSpot1: 80,
    maiaSpot2: 80,
    maiaProjector1: 0,
    maiaProjector2: 80,
  });

  useEffect(() => {
    const socket = new WebSocket("ws://localhost:8000/ws");

    socket.onopen = () => {
      console.log("Connected to FastAPI WebSocket");
      setWs(socket);
    };

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log("Received message:", data);

      if (data.type === "ai_status") {
        setAiStatus(`${data.pipeline} is ${data.status}`);
      } else if (data.type === "lighting_status") {
        setLighting((prev) => ({ ...prev, [data.light]: data.value }));
      } else if (data.type === "user_data") {
        setUserData(data.userData);
      }
    };

    socket.onclose = () => {
      console.log("WebSocket disconnected");
      setWs(null);
    };

    return () => socket.close();
  }, []);

  const changePhase = (phase: string) => {
    setActivePhase(phase);
    if (ws) {
      ws.send(JSON.stringify({ type: "phase_change", phase }));
    }
  };

  const updateLighting = (light: string, value: number) => {
    setLighting((prev) => ({ ...prev, [light]: value }));
    if (ws) {
      ws.send(JSON.stringify({ type: "lighting_update", light, value }));
    }
  };

  const sendAiCommand = (pipeline: string, command: string) => {
    if (ws) {
      ws.send(JSON.stringify({ type: "ai_command", pipeline, command }));
    }
  };

  return (
    <div className="p-4 min-h-screen bg-[var(--bg-dark)] text-[var(--text-primary)]">
      
      {/* Title Row */}
      <div className="flex justify-between mb-4">
      <h1 className="text-2xl font-bold mb-2 text-left">MAIA Backend Showrunner</h1>
      <div className="flex space-x-2">
          <button className="bg-[var(--button-bg)] hover:bg-[var(--button-active)] px-4 py-2">Play</button>
          <button className="bg-[var(--button-bg)] hover:bg-[var(--button-active)] px-4 py-2">Pause</button>
          <button className="bg-[var(--button-bg)] hover:bg-[var(--button-active)] px-4 py-2">Reset</button>
        </div>
      </div>

      {/* Scene Navigation */}
      <div className="flex justify-between mb-4">
        <PhaseNavigation activePhase={activePhase} onPhaseChange={changePhase} />
       
      </div>

      {/* AI Pipelines Row */}
      <div className="flex space-x-2 mb-4">
      <AIPipelineControls onAiCommand={sendAiCommand} />
      </div>

      {/* Two-Column Layout */}
      <div className="grid grid-cols-2 gap-4">
        
        {/* Left Column: AI Console */}
        <div>
          <LiveDataConsole aiStatus={aiStatus} />
        </div>

        {/* Right Column: User Data & Lighting Controls */}
        <div className="bg-[var(--bg-panel)] p-4 rounded-lg">
          {/* User Data Section */}
          <h2 className="text-xl font-bold mb-2">User Data</h2>
          <p>Name: {userData.name}</p>
          <p>Color: {userData.color}</p>
          <p>Signet: {userData.signet}</p>
          <h3 className="mt-4 text-lg font-bold">Responses</h3>
          <ul className="text-sm">
            {userData.responses.map((res, index) => (
              <li key={index}>- {res}</li>
            ))}
          </ul>
        </div>
                  {/* Lighting Controls */}

          <h2 className="text-lg font-bold mt-4 mb-2">Lighting Controls</h2>
          <LightingControls lighting={lighting} onLightingUpdate={updateLighting} />

      </div>
    </div>
  );
}