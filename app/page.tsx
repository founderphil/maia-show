"use client";

import { useState, useEffect, useCallback } from "react";
import PhaseNavigation from "@/components/PhaseNavigation";
import LightingControls from "@/components/LightingControls";
import AIPipelineControls from "@/components/AIPipelineControls";
import LiveDataConsole from "@/components/LiveDataConsole";
import { WebSocketMessage } from "@/app/types";

export default function ShowrunnerUI() {
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [aiStatus, setAiStatus] = useState<string>("idle");
  const [activePhase, setActivePhase] = useState("tablet");
  //TODO: Replace with actual user data
  const [userData, setUserData] = useState({ 
    name: "Querent",
    color: "Purple",
    signet: "Star",
    responses: [],
  });
  
  const [ttsAudio, setTtsAudio] = useState<string | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);

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
    if (!ws) return;
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === "tts_audio") {
        console.log("Received AI response:", data);
        setTtsAudio(data.audio_url);
      }
    };
  }, [ws]);
  
  const handlePlayTTS = () => {
    if (ttsAudio) {
      const audio = new Audio(ttsAudio);
      audio.play();
    }
  };

  useEffect(() => {
    const connectWebSocket = () => {
      const socket = new WebSocket("ws://localhost:8000/ws");

      socket.onopen = () => {
        console.log("Connected to WebSocket");
        setWs(socket);
      };

      socket.onmessage = (event) => {
        const data: { 
          type: string; 
          pipeline?: string; 
          status?: string; 
          light?: string; 
          value?: number; 
          userData?: any; 
          audio_url?: string;
        } = JSON.parse(event.data);
      
        console.log("Received WebSocket message:", data);
      
        if (data.type === "ai_status" && data.pipeline && data.status) {
          setAiStatus(`${data.pipeline} is ${data.status}`);
        } else if (data.type === "lighting_status" && typeof data.light === "string" && typeof data.value === "number") {
          setLighting((prev) => ({
            ...prev,
            [String(data.light)]: data.value, // ✅ Ensure light key is a string
          }));
        } else if (data.type === "user_data" && data.userData) {
          setUserData(data.userData);
        } else if (data.type === "tts_audio" && typeof data.audio_url === "string") {
          console.log("New TTS Audio:", data.audio_url);
          setAudioUrl(data.audio_url);
        }
      };

      socket.onclose = () => {
        console.log("WebSocket disconnected, attempting to reconnect...");
        setTimeout(connectWebSocket, 2000);
      };

      socket.onerror = (error) => {
        console.error("WebSocket Error:", error);
      };

      return socket;
    };

    const wsInstance = connectWebSocket();
    return () => wsInstance.close();
  }, []);

  const sendWebSocketMessage = useCallback((data: WebSocketMessage) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(data));
    }
  }, [ws]);

  const changePhase = (phase: string) => {
    setActivePhase(phase);
    sendWebSocketMessage({ type: "phase_change", phase });
  };

  const updateLighting = (light: string, value: number) => {
    setLighting((prev) => ({ ...prev, [light]: value }));
    sendWebSocketMessage({ type: "lighting_update", light, value });
  };

  const sendAiCommand = (pipeline: string, command: string) => {
    sendWebSocketMessage({ type: "ai_command", pipeline, command });
  };

  const handleShowControl = (command: string) => {
    if (command === "pause") {
      sendWebSocketMessage({ type: "lighting_update", light: "houseLight1", value: 100 });
      sendWebSocketMessage({ type: "lighting_update", light: "houseLight2", value: 100 });
    }
    sendWebSocketMessage({ type: "show_control", command });
  };


  return (
    <div className="p-4 min-h-screen bg-[var(--bg-dark)] text-[var(--text-primary)]">
      <div className="flex justify-between mb-4">
        <h1 className="text-2xl font-bold mb-2 text-left">MAIA Backend Showrunner</h1>
        <div className="flex space-x-2">
          <button onClick={() => handleShowControl("play")} className="bg-green-600 hover:bg-green-700 px-4 py-2 rounded">
            Play
          </button>
          <button onClick={() => handleShowControl("pause")} className="bg-yellow-600 hover:bg-yellow-700 px-4 py-2 rounded">
            Pause
          </button>
          <button onClick={() => handleShowControl("reset")} className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded">
            Reset
          </button>
        </div>
      </div>

      <div className="flex justify-between mb-4">
        <PhaseNavigation activePhase={activePhase} onPhaseChange={changePhase} />
      </div>

      <div className="flex space-x-2 mb-4">
        <AIPipelineControls onAiCommand={sendAiCommand} />
      </div>

      <div className="grid grid-cols-2 gap-4">
        {/* AI Status and Audio Player */}
        <div className="bg-[var(--bg-panel)] p-4 rounded-lg">
          <h2 className="text-xl font-bold mb-2">AI Pipeline Status</h2>
          <LiveDataConsole aiStatus={aiStatus} />
          
          {/* Audio Player */}
          {audioUrl && (
            <div className="mt-4">
              <h3 className="text-lg font-bold">TTS Output</h3>
              <audio controls autoPlay className="w-full mt-2">
                <source src={audioUrl} type="audio/wav" />
                Your browser does not support the audio element.
              </audio>
            </div>
          )}
        </div>

        <div className="bg-[var(--bg-panel)] p-4 rounded-lg">
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

        <div>
          <h2 className="text-lg font-bold mt-4 mb-2">Lighting Controls</h2>
          <LightingControls lighting={lighting} onLightingUpdate={updateLighting} />
        </div>
      </div>
    </div>
  );
}