"use client";

import { useEffect, useState } from "react";
import {
  LiveKitRoom,
  RoomAudioRenderer,
  useVoiceAssistant,
  BarVisualizer,
  DisconnectButton,
} from "@livekit/components-react";
import "@livekit/components-styles";

export default function Home() {
  const [connectionDetails, setConnectionDetails] = useState<{
    serverUrl: string;
    roomName: string;
    participantToken: string;
  } | null>(null);

  return (
    <main className="min-h-screen bg-gradient-to-b from-slate-900 via-blue-900 to-slate-900 flex items-center justify-center p-4">
      {!connectionDetails ? (
        <PassphraseEntry onConnect={setConnectionDetails} />
      ) : (
        <LiveKitRoom
          serverUrl={connectionDetails.serverUrl}
          token={connectionDetails.participantToken}
          connect={true}
          audio={true}
          className="w-full max-w-2xl"
        >
          <VoiceAssistantUI />
          <RoomAudioRenderer />
        </LiveKitRoom>
      )}
    </main>
  );
}

function PassphraseEntry({
  onConnect,
}: {
  onConnect: (details: any) => void;
}) {
  const [passphrase, setPassphrase] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const response = await fetch("/api/connection-details", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ passphrase }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || "Failed to connect");
      }

      const details = await response.json();
      onConnect(details);
    } catch (err: any) {
      setError(err.message);
      setLoading(false);
    }
  };

  return (
    <div className="bg-slate-800 rounded-lg shadow-2xl p-8 max-w-md w-full">
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold text-blue-400 mb-2">AstroLB-3</h1>
        <p className="text-slate-300">Starfield Suit AI</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label
            htmlFor="passphrase"
            className="block text-sm font-medium text-slate-300 mb-2"
          >
            Access Passphrase
          </label>
          <input
            type="password"
            id="passphrase"
            value={passphrase}
            onChange={(e) => setPassphrase(e.target.value)}
            className="w-full px-4 py-3 bg-slate-700 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Enter passphrase"
            disabled={loading}
            required
          />
        </div>

        {error && (
          <div className="bg-red-900/50 border border-red-500 text-red-200 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={loading || !passphrase}
          className="w-full py-4 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-colors duration-200"
        >
          {loading ? "Connecting..." : "Connect to AstroLB-3"}
        </button>
      </form>

      <p className="text-xs text-slate-400 mt-6 text-center">
        Systems online • Private connection only
      </p>
    </div>
  );
}

function VoiceAssistantUI() {
  const { state, audioTrack } = useVoiceAssistant();
  const [isPushToTalkActive, setIsPushToTalkActive] = useState(false);

  return (
    <div className="bg-slate-800 rounded-lg shadow-2xl p-8">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold text-blue-400 mb-2">AstroLB-3</h1>
        <p className="text-slate-300 text-sm">
          {state === "connecting" && "Initializing..."}
          {state === "listening" && "🎤 Listening"}
          {state === "thinking" && "🤔 Processing"}
          {state === "speaking" && "🔊 Speaking"}
          {state === "idle" && "⚡ Ready"}
        </p>
      </div>

      {/* Visualizer */}
      {audioTrack && (
        <div className="mb-8">
          <BarVisualizer
            state={state}
            barCount={7}
            trackRef={audioTrack}
            className="h-24"
          />
        </div>
      )}

      {/* Push-to-Talk Button */}
      <div className="flex flex-col items-center gap-6 mb-6">
        <button
          onPointerDown={() => setIsPushToTalkActive(true)}
          onPointerUp={() => setIsPushToTalkActive(false)}
          onPointerLeave={() => setIsPushToTalkActive(false)}
          className={`w-64 h-64 rounded-full font-bold text-2xl transition-all duration-200 shadow-2xl select-none ${
            isPushToTalkActive
              ? "bg-blue-500 text-white scale-95 shadow-blue-500/50"
              : "bg-blue-600 hover:bg-blue-500 text-white shadow-blue-600/30"
          }`}
          style={{
            touchAction: "none",
            WebkitTouchCallout: "none",
            WebkitUserSelect: "none",
          }}
        >
          {isPushToTalkActive ? "🎤 ACTIVE" : "HOLD TO TALK"}
        </button>

        <p className="text-slate-400 text-sm text-center max-w-sm">
          {isPushToTalkActive
            ? "Speak now - Release when done"
            : "Hold the button and speak, then release"}
        </p>
      </div>

      {/* Quick Tips */}
      <div className="bg-slate-700/50 rounded-lg p-4 mb-6">
        <h3 className="text-sm font-semibold text-blue-400 mb-2">
          Example Commands:
        </h3>
        <ul className="text-xs text-slate-300 space-y-1">
          <li>• "How do I build a ship?"</li>
          <li>• "Log that I found a Class B ship"</li>
          <li>• "Set my goal to build an outpost"</li>
          <li>• "What did I do last time?"</li>
          <li>• "Set spoiler level to main-quest"</li>
        </ul>
      </div>

      {/* Disconnect */}
      <div className="flex justify-center">
        <DisconnectButton className="px-6 py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors">
          Disconnect
        </DisconnectButton>
      </div>
    </div>
  );
}
