"use client";

import { useMemo, useState } from "react";
import { Track } from "livekit-client";
import { TokenSource } from "livekit-client";
import {
  RoomAudioRenderer,
  SessionProvider,
  StartAudio,
  useSession,
  useSessionContext,
  useVoiceAssistant,
  BarVisualizer,
  useLocalParticipant,
} from "@livekit/components-react";
import "@livekit/components-styles";

export default function Home() {
  const [isAuthorized, setIsAuthorized] = useState(false);

  if (!isAuthorized) {
    return (
      <main className="min-h-screen bg-gradient-to-b from-slate-900 via-blue-900 to-slate-900 flex items-center justify-center p-4">
        <WelcomeView onAuthorized={() => setIsAuthorized(true)} />
      </main>
    );
  }

  return <AuthorizedApp />;
}

function AuthorizedApp() {
  const tokenSource = useMemo(
    () => TokenSource.endpoint("/api/connection-details"),
    []
  );

  const session = useSession(tokenSource, {
    agentName: "astrolb3-starfield",
  });

  return (
    <SessionProvider session={session}>
      <main className="min-h-screen bg-gradient-to-b from-slate-900 via-blue-900 to-slate-900 flex items-center justify-center p-4">
        <SessionView />
        <StartAudio label="Start Audio" />
        <RoomAudioRenderer />
      </main>
    </SessionProvider>
  );
}

function WelcomeView({ onAuthorized }: { onAuthorized: () => void }) {
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

      // Passphrase verified, authorize
      onAuthorized();
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

function SessionView() {
  const { state: agentState, audioTrack: agentAudioTrack } = useVoiceAssistant();
  const { localParticipant } = useLocalParticipant();
  const { end } = useSessionContext();
  const [isMuted, setIsMuted] = useState(false);

  const toggleMute = () => {
    if (localParticipant) {
      localParticipant.setMicrophoneEnabled(isMuted);
      setIsMuted(!isMuted);
    }
  };

  return (
    <div className="bg-slate-800 rounded-lg shadow-2xl p-8 w-full max-w-2xl">
      {/* Header */}
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold text-blue-400 mb-2">AstroLB-3</h1>
        <p className="text-slate-300 text-sm">
          {agentState === "connecting" && "Initializing..."}
          {agentState === "listening" && "🎤 Listening"}
          {agentState === "thinking" && "🤔 Processing"}
          {agentState === "speaking" && "🔊 Speaking"}
          {agentState === "idle" && "⚡ Ready"}
        </p>
      </div>

      {/* Visualizer */}
      <div className="mb-8 flex items-center justify-center">
        <div className="bg-slate-900/50 rounded-lg p-8 w-full">
          <BarVisualizer
            barCount={5}
            state={agentState}
            options={{ minHeight: 5 }}
            trackRef={agentAudioTrack}
            className="flex h-24 items-center justify-center gap-2"
          >
            <span className="bg-slate-600 min-h-2.5 w-2.5 rounded-full origin-center transition-colors duration-250 ease-linear data-[lk-highlighted=true]:bg-blue-400 data-[lk-muted=true]:bg-slate-600" />
          </BarVisualizer>
        </div>
      </div>

      {/* Mute/Unmute Button */}
      <div className="flex flex-col items-center gap-6 mb-6">
        <button
          onClick={toggleMute}
          className={`w-64 h-64 rounded-full font-bold text-2xl transition-all duration-200 shadow-2xl select-none ${
            isMuted
              ? "bg-red-600 hover:bg-red-500 text-white shadow-red-600/30"
              : "bg-blue-600 hover:bg-blue-500 text-white shadow-blue-600/30"
          }`}
        >
          {isMuted ? "🔇 MUTED" : "🎤 LISTENING"}
        </button>

        <p className="text-slate-400 text-sm text-center max-w-sm">
          {isMuted
            ? "Click to unmute and talk to AstroLB-3"
            : "Microphone active - Speak naturally"}
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
        <button
          onClick={() => end()}
          className="px-6 py-3 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-colors"
        >
          Disconnect
        </button>
      </div>

      {/* Version Footer */}
      <div className="mt-6 text-center">
        <p className="text-xs text-slate-500">
          v1.4.0 - Delayed Session Creation
        </p>
      </div>
    </div>
  );
}
