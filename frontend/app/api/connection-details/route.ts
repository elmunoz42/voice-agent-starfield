import { AccessToken, RoomServiceClient } from "livekit-server-sdk";
import { NextRequest, NextResponse } from "next/server";

const API_KEY = process.env.LIVEKIT_API_KEY;
const API_SECRET = process.env.LIVEKIT_API_SECRET;
const LIVEKIT_URL = process.env.LIVEKIT_URL;
const PASSPHRASE = process.env.ACCESS_PASSPHRASE || "starfield";
const AGENT_NAME = "astrolb3-starfield";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { passphrase } = body;

    // Verify passphrase
    if (passphrase !== PASSPHRASE) {
      return NextResponse.json(
        { error: "Invalid passphrase" },
        { status: 403 }
      );
    }

    // Validate environment variables
    if (!API_KEY || !API_SECRET || !LIVEKIT_URL) {
      return NextResponse.json(
        { error: "Server configuration error" },
        { status: 500 }
      );
    }

    // Generate room name and participant identity
    const roomName = `astrolb3-${Date.now()}`;
    const participantName = "Carlos";

    // Create access token
    const at = new AccessToken(API_KEY, API_SECRET, {
      identity: participantName,
      ttl: "5h", // Token valid for 5 hours
    });

    at.addGrant({
      room: roomName,
      roomJoin: true,
      canPublish: true,
      canSubscribe: true,
    });

    const token = await at.toJwt();

    // Create room and dispatch agent
    const roomService = new RoomServiceClient(LIVEKIT_URL, API_KEY, API_SECRET);

    try {
      // Create the room first
      await roomService.createRoom({
        name: roomName,
        emptyTimeout: 300, // Room will close after 5 minutes if empty
        maxParticipants: 2, // Just the user and the agent
      });

      // Dispatch the agent to the room
      await roomService.createDispatch(roomName, {
        agentName: AGENT_NAME,
        metadata: JSON.stringify({ userId: participantName }),
      });
    } catch (err) {
      console.error("Error creating room or dispatching agent:", err);
      // Continue anyway - room might already exist
    }

    return NextResponse.json({
      serverUrl: LIVEKIT_URL,
      roomName,
      participantToken: token,
      participantName,
    });
  } catch (error) {
    console.error("Error generating token:", error);
    return NextResponse.json(
      { error: "Failed to generate connection details" },
      { status: 500 }
    );
  }
}
