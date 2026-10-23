import { AccessToken } from "livekit-server-sdk";
import { NextRequest, NextResponse } from "next/server";

const API_KEY = process.env.LIVEKIT_API_KEY;
const API_SECRET = process.env.LIVEKIT_API_SECRET;
const LIVEKIT_URL = process.env.LIVEKIT_URL;
const PASSPHRASE = process.env.ACCESS_PASSPHRASE || "starfield";

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
