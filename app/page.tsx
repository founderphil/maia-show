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
  const [userData, setUserData] = useState<Record<string, string>>({});
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [latestSTT, setLatestSTT] = useState<string>("");
  const [ttsAudio, setTtsAudio] = useState<string | null>(null);
  const [latestVision, setLatestVision] = useState<{ emotion: string; posture: string }>({ emotion: "", posture: "" });
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

  const handlePhaseChange = async (phase: string) => {
    setActivePhase(phase); // ✅ Update active phase in state

    try {
      const response = await fetch(`http://localhost:8000/api/start_phase`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phase }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      const data = await response.json();
      console.log(`Phase started successfully: ${data.message}`);
    } catch (error) {
      console.error("Error triggering phase:", error);
      alert("Failed to start phase. Check console for details.");
    }
  };

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
        console.log("✅ Connected to WebSocket");
        setWs(socket);
      };
  
      socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log("📡 WebSocket Data Received:", data);
    
        if (!data) {
            console.error("🚨 WebSocket Error: Received null or empty message!");
            return;
        }
    
        if (data.type === "tts_audio" || data.type === "phase_intro") {
            setAudioUrl(data.audio_url || ""); 
            setUserData((prevData) => ({
                ...prevData,
                latest_maia_output: data.llm_response || "Waiting for MAIA response...",
            }));
        }
    
        if (data.type === "stt_update" || data.type === "vision_update") {
            setLatestSTT(data.stt_input || "No speech detected."); 
        }
    
        if (data.type === "vision_update") {
            setLatestVision({
                emotion: data.vision_emotion || "Unknown",
                posture: data.vision_posture || "Unknown",
            });
        }
    
        if (data.type === "user_data") {
            setUserData(data.user_data || {}); 
        }
    };
  
      socket.onclose = () => {
        console.warn("⚠️ WebSocket disconnected, attempting to reconnect...");
        setTimeout(connectWebSocket, 2000);
      };
  
      socket.onerror = (error) => {
        console.error("🚨 WebSocket Error:", error);
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
      {/* Top Header with Controls */}
      <div className="flex justify-between mb-4">
        <h1 className="text-2xl font-bold mb-2 text-left">MAIA Backend Showrunner</h1>
        <div className="flex space-x-2">
          <button onClick={() => sendWebSocketMessage({ type: "show_control", command: "play" })} className="bg-green-600 hover:bg-green-700 px-4 py-2 rounded">Play</button>
          <button onClick={() => sendWebSocketMessage({ type: "show_control", command: "pause" })} className="bg-yellow-600 hover:bg-yellow-700 px-4 py-2 rounded">Pause</button>
          <button onClick={() => sendWebSocketMessage({ type: "show_control", command: "reset" })} className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded">Reset</button>
        </div>
      </div>

      {/* Phase Navigation & AI Pipeline Controls */}
      <div className="flex space-x-4 mb-4 col-span-2">
      <PhaseNavigation activePhase={activePhase} onPhaseChange={handlePhaseChange} />
        <AIPipelineControls onAiCommand={(pipeline) => sendWebSocketMessage({ type: "ai_command", pipeline, command: "start" })} />
      </div>

      {/* Two-Column Layout */}
      <div className="grid grid-cols-2 gap-4">
        {/* Left Column: MAIA Activity */}
        <div className="bg-[var(--bg-panel)] p-4 rounded-lg h-[600px] overflow-y-auto">
          <h2 className="text-xl font-bold mb-2">MAIA Activity</h2>

          {/* Input Layer */}
          <div className="border-b pb-4 mb-4">
            <div className="flex justify-between">
              {/* Hearing */}
              <div className="w-1/2 pr-4">
                <h3 className="text-lg font-bold">HEARING</h3>
                <div className="bg-gray-800 p-2 rounded mt-2 text-sm">{latestSTT}</div>
              </div>

              {/* Vision */}
              <div className="w-1/2">
                <h3 className="text-lg font-bold">VISION</h3>
                <img 
                  src="/static/images/captured.png" 
                  alt="No Image" 
                  className="w-full h-40 object-cover mt-2" 
                  onError={(e) => e.currentTarget.src = "/static/images/fallback-image.png"} 
                />
                <div className="text-sm mt-2">
                  <p><strong>Emotion:</strong> {latestVision.emotion || "Unknown"}</p>
                  <p><strong>Posture:</strong> {latestVision.posture || "Unknown"}</p>
                </div>
              </div>
            </div>
          </div>

          {/* MAIA Output Feed Console */}
          <div>
            <h3 className="text-lg font-bold">MAIA OUTPUT FEED CONSOLE</h3>
            <div className="bg-gray-800 p-2 rounded mt-2 text-sm">{userData["latest_maia_output"] || "Waiting for MAIA response..."}</div>
            {audioUrl && (
              <audio controls autoPlay className="w-full mt-4">
                <source src={audioUrl} type="audio/wav" />
                Your browser does not support the audio element.
              </audio>
            )}
          </div>
        </div>

        {/* Right Column: User Data & Lighting Controls */}
        <div className="flex flex-col space-y-4">
          {/* User Data Box */}
          <div className="bg-[var(--bg-panel)] p-4 rounded-lg h-[300px] overflow-y-auto">
            <h2 className="text-xl font-bold mb-2">User Data</h2>
            <table className="w-full text-sm">
              <tbody>
                {Object.entries(userData).map(([key, value]) => (
                  <tr key={key}>
                    <td className="pr-4 font-bold">{key}</td>
                    <td>{value}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Lighting Controls */}
          <div className="bg-[var(--bg-panel)] p-4 rounded-lg">
            <h2 className="text-xl font-bold mb-2">Lighting Controls</h2>
            <LightingControls lighting={lighting} onLightingUpdate={updateLighting} />
          </div>
        </div>
      </div>
    </div>
  );
}