# M3 Deployment Guide: Phone Deployment

This guide covers deploying AstroLB-3 to LiveKit Cloud (agent) and Vercel (frontend) for phone access.

## Prerequisites

- LiveKit Cloud account: https://cloud.livekit.io
- Vercel account: https://vercel.com
- OpenAI API key: https://platform.openai.com

## Part 1: Deploy Agent to LiveKit Cloud

### 1. Install LiveKit CLI

**Windows:**
```bash
winget install LiveKit.LiveKitCLI
```

**macOS:**
```bash
brew install livekit
```

**Linux:**
```bash
curl -sSL https://get.livekit.io/cli | bash
```

### 2. Authenticate with LiveKit Cloud

```bash
lk cloud auth
```

This will open your browser to authenticate. Follow the prompts.

### 3. Deploy the Agent

Navigate to the agent directory:
```bash
cd agent
```

Create a deployable agent:
```bash
lk agent create
```

Follow the prompts:
- Agent name: `astrolb3-agent` (or your preferred name)
- Entry point: `voice_agent.py`

The CLI will deploy your agent and provide:
- **Agent URL** (wss://...)
- **API Key**
- **API Secret**

**Save these credentials** - you'll need them for the frontend.

### 4. Set Agent Environment Variables

In the LiveKit Cloud dashboard, add these environment variables for your agent:
- `OPENAI_API_KEY`: Your OpenAI API key

## Part 2: Deploy Frontend to Vercel

### 1. Install Vercel CLI (optional)

```bash
npm i -g vercel
```

### 2. Configure Environment Variables

Create `frontend/.env.local` based on `.env.local.example`:

```bash
cd frontend
cp .env.local.example .env.local
```

Edit `.env.local` with the credentials from LiveKit Cloud (Step 1.3):

```env
# LiveKit Cloud Configuration
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=your-api-key
LIVEKIT_API_SECRET=your-api-secret

# Access Control
ACCESS_PASSPHRASE=starfield
```

### 3. Deploy to Vercel

**Option A: Using Vercel CLI**
```bash
vercel
```

Follow the prompts. For production deployment:
```bash
vercel --prod
```

**Option B: Using Vercel Dashboard**
1. Go to https://vercel.com/new
2. Import your git repository
3. Set the root directory to `frontend`
4. Add environment variables in the Vercel dashboard:
   - `LIVEKIT_URL`
   - `LIVEKIT_API_KEY`
   - `LIVEKIT_API_SECRET`
   - `ACCESS_PASSPHRASE`
5. Deploy

### 4. Add PWA Icons (Optional but Recommended)

For a polished home screen experience, replace the placeholder icons:
- `frontend/public/icon-192.png` (192x192 PNG)
- `frontend/public/icon-512.png` (512x512 PNG)

Use a Starfield-themed icon (suit AI, helmet, etc.)

## Part 3: Access from Phone

### 1. Open the Vercel URL

Navigate to your deployed Vercel URL (e.g., `https://astrolb3.vercel.app`) on your phone.

### 2. Install as PWA (Progressive Web App)

**iOS Safari:**
1. Tap the Share button
2. Scroll down and tap "Add to Home Screen"
3. Name it "AstroLB-3"
4. Tap "Add"

**Android Chrome:**
1. Tap the menu (three dots)
2. Tap "Add to Home Screen"
3. Name it "AstroLB-3"
4. Tap "Add"

### 3. Connect with Earbuds

1. Connect your Bluetooth earbuds/headphones
2. Open the AstroLB-3 app from your home screen
3. Enter the passphrase (default: `starfield`)
4. Grant microphone permissions when prompted
5. Hold the "HOLD TO TALK" button and speak
6. Release when done speaking

## Troubleshooting

### Agent Issues

**Check agent logs:**
```bash
lk agent logs
```

**Redeploy agent:**
```bash
lk agent deploy
```

### Frontend Issues

**Test locally first:**
```bash
cd frontend
npm run dev
```

**Check Vercel deployment logs:**
- Go to your Vercel dashboard
- Select your project
- Click "Deployments"
- Click on the latest deployment
- View "Build Logs" and "Function Logs"

### Connection Issues

1. Verify environment variables match between LiveKit Cloud and Vercel
2. Check that `LIVEKIT_URL` starts with `wss://` (not `ws://`)
3. Ensure passphrase matches in both `.env.local` and your input
4. Check browser console for errors (F12 Developer Tools)

### Audio Issues

1. Grant microphone permissions in browser
2. Check that earbuds/headphones are connected
3. Test with a simple voice recording app first
4. Try refreshing the page or reinstalling the PWA

## Security Notes

- The `ACCESS_PASSPHRASE` protects against unauthorized access
- Change the default passphrase in production
- Keep your LiveKit API credentials secret
- Never commit `.env.local` or `.env` files to git

## Next Steps

After successful deployment:
- Test all voice commands (see example commands in the UI)
- Try logging progress, setting goals, asking Starfield questions
- Adjust spoiler level as you progress through the game
- Run M4 playtest scenarios (see `build-prompt.md`)
