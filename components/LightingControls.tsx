"use client";

interface LightingControlsProps {
  lighting: { [key: string]: number };
  onLightingUpdate: (light: string, value: number) => void;
}

export default function LightingControls({ lighting, onLightingUpdate }: LightingControlsProps) {
  return (
    <div className="mt-4 bg-gray-800 p-4 rounded-lg">
      <h2 className="text-lg font-semibold mb-2">Lighting Controls</h2>
      {Object.keys(lighting).map((light) => (
        <div key={light} className="flex items-center space-x-2 mb-2">
          <p className="w-32 capitalize">{light.replace(/([A-Z])/g, " $1")}</p>
          <input
            type="range"
            min="0"
            max="100"
            value={lighting[light]}
            onChange={(e) => onLightingUpdate(light, Number(e.target.value))}
            className="w-full appearance-none bg-gray-700 rounded-lg h-2 cursor-pointer accent-[var(--accent)]"
            />
        </div>
      ))}
    </div>
  );
}