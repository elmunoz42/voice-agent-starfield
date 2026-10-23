import { AccessToken } from "livekit-server-sdk";
import { NextRequest, NextResponse } from "next/server";

const API_KEY = process.env.LIVEKIT_API_KEY;
const API_SECRET = process.env.LIVEKIT_API_SECRET;
const LIVEKIT_URL = process.env.LIVEKIT_URL;
const PASSPHRASE = process.env.ACCESS_PASSPHRASE || "starfield";

async function generateConnectionDetails() {
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

  // Manually dispatch agent to room
  try {
    const dispatchUrl = `${LIVEKIT_URL}/twirp/livekit.AgentDispatchService/CreateDispatch`;
    const dispatchAuth = Buffer.from(`${API_KEY}:${API_SECRET}`).toString('base64');

    console.log('Dispatching agent astrolb3-starfield to room:', roomName);

    const dispatchResponse = await fetch(dispatchUrl, {
      method: 'POST',
      headers: {
        'Authorization': `Basic ${dispatchAuth}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        room: roomName,
        agent_name: 'astrolb3-starfield',
      }),
    });

    if (!dispatchResponse.ok) {
      const errorText = await dispatchResponse.text();
      console.error('Failed to dispatch agent:', errorText);
    } else {
      console.log('Agent dispatched successfully');
    }
  } catch (err) {
    console.error('Error dispatching agent:', err);
  }

  return NextResponse.json({
    serverUrl: LIVEKIT_URL,
    roomName,
    participantToken: token,
    participantName,
  });
}

// GET/POST handler - called by LiveKit and passphrase form
export async function GET(request: NextRequest) {
  try {
    return await generateConnectionDetails();
  } catch (error) {
    console.error("Error generating token:", error);
    return NextResponse.json(
      { error: "Failed to generate connection details" },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    // Check if this is a passphrase validation request or token request
    const body = await request.json();
    const { passphrase } = body;

    // If passphrase is provided, validate it
    if (passphrase !== undefined) {
      if (passphrase !== PASSPHRASE) {
        return NextResponse.json(
          { error: "Invalid passphrase" },
          { status: 403 }
        );
      }
      // Passphrase valid, return success (no token needed yet)
      return NextResponse.json({ success: true });
    }

    // Otherwise generate token
    return await generateConnectionDetails();
  } catch (error) {
    console.error("Error generating token:", error);
    return NextResponse.json(
      { error: "Failed to generate connection details" },
      { status: 500 }
    );
  }
}
