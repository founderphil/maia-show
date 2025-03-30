"use client";

import { useState, useEffect, useCallback } from "react";
import PhaseNavigation from "@/components/PhaseNavigation";
import LightingControls from "@/components/LightingControls";
import AIPipelineControls from "@/components/AIPipelineControls";
import { WebSocketMessage } from "@/app/types";

export default function ShowrunnerUI() {
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [activePhase, setActivePhase] = useState("tablet");
  const [userData, setUserData] = useState<Record<string, string>>({});
  const [latestSTT, setLatestSTT] = useState<string>("");
  const [llmResponse, setLlmResponse] = useState<string>("");
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [visionImage, setVisionImage] = useState("/static/images/captured.png");
  const [latestVision, setLatestVision] = useState<{ emotion: string; posture: string }>({ emotion: "Unknown", posture: "Unknown" });

  const [lighting, setLighting] = useState({
    maiaLED: 10,
    houseLight1: 20,
    houseLight2: 30,
    chairSpot: 40,
    maiaSpot1: 50,
    maiaSpot2: 60,
    maiaProjector1: 70,
    maiaProjector2: 80,
  });

  useEffect(() => {
    const fetchUserData = async () => {
      try {
        const res = await fetch("/api/proxy?pathname=/users");
        const data = await res.json();
        if (data?.user) {
          setUserData(data.user);
        }
      } catch (err) {
        console.error("Failed to fetch initial user data:", err);
      }
    };

    fetchUserData();
  }, []);

  const connectWebSocket = useCallback(() => {
    const socket = new WebSocket("ws://localhost:8000/ws");

    socket.onopen = () => {
      console.log("✅ WebSocket connected");
      setWs(socket);
    };

    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log("📡 WebSocket Data:", data);

      switch (data.type) {
        case "phase_intro":
        case "phase_tablet":
          setActivePhase(data.phase || "tablet");
          if (data.user_data) setUserData(data.user_data);
          break;

        case "tts_audio_only":
        case "vision_update":
        case "full_inference":
          if (data.audio_url) setAudioUrl(data.audio_url);
          if (data.llm_response) setLlmResponse(data.llm_response);
          if (data.user_question) setLatestSTT(data.user_question);
          if (data.vision_image) setVisionImage(data.vision_image);
          if (data.vision_emotion || data.vision_posture) {
            setLatestVision({
              emotion: data.vision_emotion || "Unknown",
              posture: data.vision_posture || "Unknown",
            });
          }
          break;

        default:
          console.warn("Unhandled WebSocket message type:", data.type);
      }
    };

    socket.onclose = () => {
      console.warn("WebSocket closed. Reconnecting...");
      setTimeout(connectWebSocket, 2000);
    };

    socket.onerror = (err) => {
      console.error("WebSocket error:", err);
    };
  }, []);
  
  useEffect(() => {
    const socket = connectWebSocket();
    return () => socket?.close();
  }, [connectWebSocket]);

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

  const handlePhaseChange = async (phase: string) => {
    setActivePhase(phase); // optional UI highlight
  
    try {
      const response = await fetch("/api/proxy", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          pathname: "/start_phase",
          body: { phase },
        }),
      });
  
      const result = await response.json();
      console.log("✅ Phase started:", result);
    } catch (error) {
      console.error("❌ Failed to start phase:", error);
    }
  };

  return (
    <div className="p-4 min-h-screen bg-[var(--bg-dark)] text-[var(--text-primary)]">
      {/* Top Controls */}
      <div className="flex justify-between mb-4">
        <h1 className="text-2xl font-bold">MAIA Backend Showrunner</h1>
        <div className="flex space-x-2">
          <button onClick={() => sendWebSocketMessage({ type: "show_control", command: "play" })} className="bg-green-600 px-4 py-2 rounded">Play</button>
          <button onClick={() => sendWebSocketMessage({ type: "show_control", command: "pause" })} className="bg-yellow-600 px-4 py-2 rounded">Pause</button>
          <button onClick={() => sendWebSocketMessage({ type: "show_control", command: "reset" })} className="bg-red-600 px-4 py-2 rounded">Reset</button>
        </div>
      </div>

      {/* Phase Navigation */}
      <div className="flex space-x-4 mb-4">
        <PhaseNavigation activePhase={activePhase} onPhaseChange={handlePhaseChange} />
        <AIPipelineControls onAiCommand={(pipeline) => sendWebSocketMessage({ type: "ai_command", pipeline, command: "start" })} />
      </div>

      {/* Main Display */}
      <div className="grid grid-cols-2 gap-4">
        {/* MAIA Activity */}
        <div className="bg-[var(--bg-panel)] p-4 rounded-lg h-[600px] overflow-y-auto">
          <h2 className="text-xl font-bold mb-2">MAIA Activity <span className="ml-2 text-sm text-gray-400">({activePhase})</span></h2>

          {/* Inputs */}
          <div className="border-b pb-4 mb-4 flex justify-between">
            <div className="w-1/2 pr-4">
              <h3 className="text-lg font-bold">HEARING</h3>
              <div className="bg-gray-800 p-2 rounded mt-2 text-sm">{latestSTT || "Waiting for user input..."}</div>
            </div>

            <div className="w-1/2">
              <h3 className="text-lg font-bold">VISION</h3>
              <img
                src={visionImage}
                alt="Vision"
                className="w-full h-40 object-cover mt-2"
                onError={(e) => (e.currentTarget.src = "/static/images/fallback-image.png")}
              />
              <div className="text-sm mt-2">
                <p><strong>Emotion:</strong> {latestVision.emotion}</p>
                <p><strong>Posture:</strong> {latestVision.posture}</p>
              </div>
            </div>
          </div>

          {/* Output */}
          <div>
            <h3 className="text-lg font-bold">MAIA OUTPUT FEED CONSOLE</h3>
            <div className="bg-gray-800 p-2 rounded mt-2 text-sm whitespace-pre-wrap">
              {llmResponse || "Waiting for MAIA response..."}
            </div>
            {audioUrl && (
              <audio controls autoPlay className="w-full mt-4">
                <source src={audioUrl} type="audio/wav" />
              </audio>
            )}
          </div>
        </div>

        {/* Right Column */}
        <div className="flex flex-col space-y-4">
          {/* User Data */}
          <div className="bg-[var(--bg-panel)] p-4 rounded-lg h-[300px] overflow-y-auto">
            <h2 className="text-xl font-bold mb-2">User Data</h2>
            <table className="w-full text-sm">
              <tbody>
                {Object.entries(userData).map(([key, value]) => (
                  <tr key={key}>
                    <td className="pr-4 font-bold">{key}</td>
                    <td className="whitespace-pre-wrap">{value}</td>
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