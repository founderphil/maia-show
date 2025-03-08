"use client";

interface LiveDataConsoleProps {
  aiStatus: string;
}

export default function LiveDataConsole({ aiStatus }: LiveDataConsoleProps) {
  return (
    <div className="mb-4 p-4 bg-gray-800 rounded-lg">
      <h2 className="text-lg font-semibold">AI Pipeline Status</h2>
      <p>{aiStatus}</p>
    </div>
  );
}