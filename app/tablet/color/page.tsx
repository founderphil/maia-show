"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";

export default function ColorSelection() {
  const [chosenColor, setChosenColor] = useState<string>("#ffffff");
  const [userName, setUserName] = useState<string | null>(null);
  const router = useRouter();
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const isDraggingRef = useRef<boolean>(false);

  useEffect(() => {
    const storedName = sessionStorage.getItem("userName");
    if (!storedName) router.push("/tablet");
    setUserName(storedName);
    drawColorSpectrum();

    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = "auto";
    };
  }, [router]);

  const drawColorSpectrum = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const gradient = ctx.createLinearGradient(0, 0, canvas.width, 0);
    gradient.addColorStop(0, "red");
    gradient.addColorStop(0.17, "yellow");
    gradient.addColorStop(0.34, "green");
    gradient.addColorStop(0.51, "cyan");
    gradient.addColorStop(0.68, "blue");
    gradient.addColorStop(0.85, "magenta");
    gradient.addColorStop(1, "red");

    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    const whiteToBlack = ctx.createLinearGradient(0, 0, 0, canvas.height);
    whiteToBlack.addColorStop(0, "rgba(255,255,255,1)");
    whiteToBlack.addColorStop(0.5, "rgba(255,255,255,0)");
    whiteToBlack.addColorStop(0.5, "rgba(0,0,0,0)");
    whiteToBlack.addColorStop(1, "rgba(0,0,0,1)");

    ctx.fillStyle = whiteToBlack;
    ctx.fillRect(0, 0, canvas.width, canvas.height);
  };

  const getColorFromCanvas = (event: React.TouchEvent<HTMLCanvasElement> | React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const rect = canvas.getBoundingClientRect();
    const x = "touches" in event ? event.touches[0].clientX - rect.left : event.clientX - rect.left;
    const y = "touches" in event ? event.touches[0].clientY - rect.top : event.clientY - rect.top;

    if (x < 0 || x > canvas.width || y < 0 || y > canvas.height) return;

    const pixel = ctx.getImageData(x, y, 1, 1).data;
    const color = `rgb(${pixel[0]}, ${pixel[1]}, ${pixel[2]})`;

    setChosenColor(color);
  };

  const startSelecting = () => { isDraggingRef.current = true; };
  const stopSelecting = () => { isDraggingRef.current = false; };
  const handleMove = (event: React.TouchEvent<HTMLCanvasElement> | React.MouseEvent<HTMLCanvasElement>) => {
    if (isDraggingRef.current) {
      getColorFromCanvas(event);
    }
  };

  const handleChoose = async () => {
    if (!userName || !chosenColor) {
      alert("Complete all selections first!");
      return;
    }
  
    try {
      fetch("/api/proxy", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          pathname: "/save_user",
          body: { userName, chosenColor },
        }),
      });
  
      // Background TTS placeholder (non-blocking, currently disabled)
      // fetch("/api/proxy", {
      //   method: "POST",
      //   headers: { "Content-Type": "application/json" },
      //   body: JSON.stringify({ pathname: "/run_color_tts" }),
      // }).catch((err) => console.error("Background color TTS failed:", err));

      router.push("/tablet/signet");
    } catch (error) {
      console.error("Failed to save user:", error);
    }
  };

  return (
    <div
      className="flex flex-col items-center justify-center min-h-screen transition-all duration-200"
      style={{ backgroundColor: chosenColor }}
    >
      <h1 className="text-2xl font-bold mb-4 text-light-gray-100">
      {userName ? `${userName}, what calls to you?` : "What calls to you?"}
      </h1>

      <canvas
        ref={canvasRef}
        width={600} 
        height={400}
        className="cursor-crosshair border border-white"
        onMouseDown={startSelecting}
        onMouseUp={stopSelecting}
        onMouseMove={handleMove}
        onTouchStart={startSelecting}
        onTouchEnd={stopSelecting}
        onTouchMove={handleMove}
      />

      <p className="mt-4 text-white"><span>{chosenColor}</span></p>

      <button onClick={handleChoose} className="mt-4 px-12 py-6 border-2 border border-white text-white rounded-lg bg-transparent hover:bg-white hover:text-black shadow-md"
        style={{ borderColor: "white", borderWidth: "2px" }}>
        Choose
      </button>
    </div>
  );
}