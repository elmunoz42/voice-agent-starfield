import {
  AccessToken,
  RoomAgentDispatch,
  RoomConfiguration,
} from "livekit-server-sdk";
import { NextRequest, NextResponse } from "next/server";

const API_KEY = process.env.LIVEKIT_API_KEY;
const API_SECRET = process.env.LIVEKIT_API_SECRET;
const LIVEKIT_URL = process.env.LIVEKIT_URL;
const PASSPHRASE = process.env.ACCESS_PASSPHRASE || "starfield";

// Must match AGENT_NAME in agent/voice_agent.py. Agents registered with an
// explicit name are only dispatched when requested, which we do via the token.
const AGENT_NAME = "astrolb3-starfield";

const PASSPHRASE_HEADER = "x-access-passphrase";

async function generateConnectionDetails() {
  if (!API_KEY || !API_SECRET || !LIVEKIT_URL) {
    return NextResponse.json(
      { error: "Server configuration error" },
      { status: 500 }
    );
  }

  // New room per session: agents won't rejoin a room that already existed
  const roomName = `astrolb3-${Date.now()}`;
  const participantName = "Carlos";
  const participantIdentity = `carlos-${crypto.randomUUID().slice(0, 8)}`;

  const at = new AccessToken(API_KEY, API_SECRET, {
    identity: participantIdentity,
    name: participantName,
    ttl: "5h",
  });

  at.addGrant({
    room: roomName,
    roomJoin: true,
    canPublish: true,
    canPublishData: true,
    canSubscribe: true,
  });

  // Dispatch the agent when the room is created on join
  at.roomConfig = new RoomConfiguration({
    agents: [new RoomAgentDispatch({ agentName: AGENT_NAME })],
  });

  const participantToken = await at.toJwt();

  return NextResponse.json({
    serverUrl: LIVEKIT_URL,
    roomName,
    participantToken,
    participantName,
  });
}

// POST handler - called by the passphrase form ({ passphrase }) and by
// TokenSource.endpoint() (passphrase sent in the x-access-passphrase header)
export async function POST(request: NextRequest) {
  try {
    const body = await request.json().catch(() => ({}));

    // Passphrase verification from the login form
    if (typeof body?.passphrase === "string") {
      if (body.passphrase !== PASSPHRASE) {
        return NextResponse.json(
          { error: "Invalid passphrase" },
          { status: 403 }
        );
      }
      return NextResponse.json({ success: true });
    }

    // Token request - always requires the passphrase
    if (request.headers.get(PASSPHRASE_HEADER) !== PASSPHRASE) {
      return NextResponse.json(
        { error: "Invalid passphrase" },
        { status: 403 }
      );
    }

    return await generateConnectionDetails();
  } catch (error) {
    console.error("Error generating token:", error);
    return NextResponse.json(
      { error: "Failed to generate connection details" },
      { status: 500 }
    );
  }
}
