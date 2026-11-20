# i20 AI Garage - Staging Deployment Guide

**Version:** 1.0
**Target:** Render (Docker Web Service)
**Status:** Ready for deployment

---

## Overview

This guide covers deploying the i20 AI Garage application to a secure staging environment on Render using Docker. The deployment uses simulation mode only—no physical OBD hardware or local LM Studio instance is required.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Render Cloud                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                  Docker Container                    │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │    │
│  │  │   Streamlit  │  │  Simulation  │  │  SQLite    │  │    │
│  │  │   Server     │◄─│   Engine     │  │  Database  │  │    │
│  │  │  (port 8501) │  │  (1Hz)       │  │  (ephemeral)│  │    │
│  │  └──────────────┘  └──────────────┘  └────────────┘  │    │
│  └─────────────────────────────────────────────────────┘    │
│                          │                                    │
│                    HTTPS (Render TLS)                         │
└──────────────────────────┼────────────────────────────────────┘
                           │
                    ┌──────▼──────┐
                    │   Browser   │
                    │  (Tester)   │
                    └─────────────┘
```

---

## Prerequisites

1. **GitHub Repository:** https://github.com/Ishan112-web/Hyundai-i-20-OBD-analyzer-app
2. **Render Account:** Free tier sufficient for staging
3. **Docker** (optional, for local testing): Docker Desktop or Docker Engine

---

## Deployment Steps

### Option A: Deploy via Render Dashboard (Recommended)

#### 1. Connect Repository
1. Log in to [Render Dashboard](https://dashboard.render.com)
2. Click **New +** → **Web Service**
3. Select **Docker** as runtime
4. Connect your GitHub account if not already connected
5. Select repository: `Ishan112-web/Hyundai-i-20-OBD-analyzer-app`
6. Branch: `master`

#### 2. Configure Service
| Setting | Value |
|---------|-------|
| **Name** | `i20-ai-garage-staging` |
| **Region** | Choose closest (e.g., `Oregon (US West)`) |
| **Branch** | `master` |
| **Runtime** | `Docker` |
| **Dockerfile Path** | `./Dockerfile` |
| **Docker Context** | `.` |
| **Plan** | `Starter` (free) or `Standard` |

#### 3. Environment Variables
Add these in **Settings → Environment Variables**:

**Required (Staging Mode):**
| Key | Value | Notes |
|-----|-------|-------|
| `OBD_MODE` | `simulation` | **Critical** - prevents hardware access |
| `SIMULATION_INTERVAL` | `1.0` | Reduces CPU (was 0.5s) |
| `TELEMETRY_REFRESH_INTERVAL` | `2.0` | Reduces UI refresh rate |
| `DATABASE_PATH` | `/app/data/i20_garage_staging.db` | Staging database path |
| `STREAMLIT_SERVER_HEADLESS` | `true` | Required for cloud |
| `STREAMLIT_SERVER_ADDRESS` | `0.0.0.0` | Bind to all interfaces |
| `STREAMLIT_SERVER_ENABLE_CORS` | `false` | Security |
| `STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION` | `true` | Security |
| `PYTHONUNBUFFERED` | `1` | Proper logging |

**Optional (AI - Leave unset to disable gracefully):**
| Key | Value | Notes |
|-----|-------|-------|
| `LM_STUDIO_BASE_URL` | *(leave empty)* | No LM Studio in cloud |
| `LM_STUDIO_MODEL` | `qwen2.5-3b-instruct` | Model name for reference |
| `LM_STUDIO_TEMPERATURE` | `0.7` | |
| `LM_STUDIO_TIMEOUT` | `30` | |

**OBD (Simulation only):**
| Key | Value |
|-----|-------|
| `OBD_PORT` | `N/A` |
| `OBD_BAUDRATE` | `38400` |
| `OBD_PROTOCOL` | `auto` |

#### 4. Deploy
1. Click **Create Web Service**
2. Render will build the Docker image (2-5 minutes)
3. Service starts automatically
4. Note the URL: `https://i20-ai-garage-staging.onrender.com`

---

### Option B: Deploy via `render.yaml` (Infrastructure as Code)

1. Ensure `render.yaml` is committed to repository root
2. In Render Dashboard: **New +** → **Blueprint**
3. Connect repository
4. Render reads `render.yaml` and creates service
5. Add environment variables in dashboard (Blueprint doesn't support all env vars)

---

### Option C: Local Docker Test (Before Cloud Deploy)

```bash
# Build image
docker build -t i20-ai-garage:staging .

# Run container
docker run -d \
  --name i20-staging \
  -p 8501:8501 \
  -e OBD_MODE=simulation \
  -e SIMULATION_INTERVAL=1.0 \
  -e TELEMETRY_REFRESH_INTERVAL=2.0 \
  -e DATABASE_PATH=/app/data/i20_garage_staging.db \
  -e STREAMLIT_SERVER_HEADLESS=true \
  -e STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
  -v i20-staging-data:/app/data \
  i20-ai-garage:staging

# Test locally
open http://localhost:8501

# Check logs
docker logs -f i20-staging

# Cleanup
docker stop i20-staging && docker rm i20-staging
docker volume rm i20-staging-data
```

---

## Authentication & Access Control

### Render Built-in Protection (Recommended)

Render provides **Basic Authentication** for staging services:

1. Go to **Settings → Basic Authentication**
2. Enable **Password Protection**
3. Set username: `staging`
4. Set password: *(generate strong password)*
5. Save

**Access URL:** `https://staging:password@i20-ai-garage-staging.onrender.com`

### Alternative: Application-Level Auth

If implementing in-app authentication (future enhancement):
- Add `STREAMLIT_AUTH_TYPE=basic` and credentials to env vars
- Requires code changes to `app.py` for auth middleware

---

## Database Behavior

### Ephemeral Storage (Default - Free Tier)
- SQLite file at `/app/data/i20_garage_staging.db`
- **Data LOST on redeploy/restart**
- Acceptable for staging: demo data regenerates automatically
- Schema auto-created on first run via migrations

### Persistent Storage (Paid Plan)
1. Add Render Disk: **Settings → Disks → Add Disk**
2. Name: `i20-data`, Mount Path: `/app/data`, Size: 1 GB
3. Update `DATABASE_PATH` unchanged
4. Data survives redeploys

### Migration Behavior
- Fresh container: `DatabaseService._init_database()` creates schema
- `ensure_database_migrated()` records baseline version
- Subsequent migrations run automatically via `MigrationRunner`
- No manual migration step needed

---

## AI Assistant Limitations

### Cloud Staging Reality
| Feature | Local | Staging |
|---------|-------|---------|
| LM Studio Connection | ✅ `localhost:1234` | ❌ Unavailable |
| Model Inference | ✅ Local GPU/CPU | ❌ No model loaded |
| Chat Responses | ✅ Real AI | ⚠️ Error message |
| Structured Diagnosis | ✅ JSON output | ⚠️ Error message |

### Staging Behavior
- AI Assistant page loads normally
- Connection test shows "❌ AI connection failed - check LM Studio is running"
- User sees clear message: "LM Studio not available in staging. AI responses are disabled."
- All other pages fully functional
- **No simulated/fake AI responses presented as real**

### Testing AI UI Without Model
1. Open AI Assistant page
2. Verify error message displays correctly
3. Test input field accepts text
4. Test "Test AI Connection" button in Settings
5. Verify no crashes or blank screens

---

## OBD Simulation Limitations

### What Works in Staging
- All 5 simulation scenarios (idle, city, highway, acceleration, overheating)
- Real-time telemetry charts (Plotly)
- DTC scanning (demo codes: P0300, P0171, P0420, P0128)
- Freeze frame data (simulated)
- Vehicle info (simulated VIN)
- Connection wizard (shows simulation status)

### What Does NOT Work (By Design)
- Real ELM327 adapter connection
- Serial port access (no `/dev/ttyUSB0` or `COM3`)
- ECU write commands (Mode 04 clear DTC, actuator tests)
- Live PID polling from hardware
- VIN reading from actual ECU

### Simulation Tuning for Cloud
```env
SIMULATION_INTERVAL=1.0        # 1 Hz (was 0.5s = 2 Hz)
TELEMETRY_REFRESH_INTERVAL=2.0 # UI updates every 2s
```
Reduces CPU ~60% with minimal UX impact.

---

## Verification Checklist

After deployment, verify each area:

### Core Application
- [ ] Home page loads without errors
- [ ] No 5xx errors in Render logs
- [ ] Health check passes (`/_stcore/health`)

### Navigation & Pages
- [ ] Dashboard renders with telemetry cards
- [ ] Diagnostics page loads, shows demo DTCs
- [ ] Performance page shows charts
- [ ] Maintenance page shows intervals
- [ ] Reports page lists report types
- [ ] Vehicle Profile shows specs
- [ ] AI Assistant opens, shows unavailable message
- [ ] OBD Connection page shows simulation mode
- [ ] Settings page loads all sections
- [ ] Sidebar navigation works
- [ ] Mobile drawer works (resize browser)

### Functionality
- [ ] Simulation start/stop buttons work
- [ ] Scenario selector changes telemetry
- [ ] Charts render (Plotly interactive)
- [ ] Forms validate (maintenance entry, settings)
- [ ] Report generation (HTML/PDF) works
- [ ] Database initializes (check logs for "Database initialized")
- [ ] Migrations apply (check logs for "Baseline adoption")

### Security
- [ ] Basic auth prompts for credentials
- [ ] No `.env` or secrets in container
- [ ] No stack traces in UI errors
- [ ] HTTPS enforced by Render

### Browser Console
- [ ] No critical JS errors (red)
- [ ] No CORS errors
- [ ] WebSocket connects for Streamlit

---

## Known Issues & Workarounds

| Issue | Impact | Workaround |
|-------|--------|------------|
| Ephemeral DB loses data on restart | Staging only | Use Render Disk (paid) |
| AI Assistant shows error | Expected | Document as known limitation |
| First load slow (cold start) | ~30s on free tier | Upgrade to Standard plan |
| Plotly charts may need WebGL | Some browsers | Works in Chrome/Firefox/Edge |
| WebSocket disconnects on idle | Free tier spins down | User interaction wakes it |

---

## Redeployment Procedure

### Automatic (Push to Master)
1. Push changes to `master` branch
2. Render auto-deploys (if `autoDeploy: true`)
3. Monitor build logs in Render Dashboard

### Manual Trigger
1. Render Dashboard → Service → **Manual Deploy**
2. Select **Clear build cache** if dependency issues
3. Deploy latest commit

### Environment Variable Changes
1. Update in **Settings → Environment Variables**
2. Click **Save Changes**
3. Render restarts service automatically

---

## Shutdown Procedure

### Temporary (Free Tier)
- Service spins down after 15 min inactivity
- Cold start ~30s on next access
- No action needed

### Permanent
1. Render Dashboard → Service → **Settings → Delete Service**
2. Confirm deletion
3. **Note:** Ephemeral data lost immediately

### With Persistent Disk
1. Download database backup first (if needed)
2. Delete service
3. Delete disk separately (Settings → Disks)

---

## Troubleshooting

### Build Fails
```bash
# Check build logs in Render Dashboard
# Common issues:
# - Python version mismatch (Dockerfile: 3.11)
# - Missing system deps (freetype, jpeg, openblas)
# - requirements.txt syntax error
```

### Container Crashes on Start
```bash
# Check Runtime Logs
# Common issues:
# - Port binding (must use 0.0.0.0:8501)
# - Database path permissions
# - Missing env var (OBD_MODE=simulation)
```

### Health Check Fails
- Verify `/_stcore/health` returns 200
- Check `STREAMLIT_SERVER_HEADLESS=true`
- Increase `healthCheckPath` timeout in render.yaml

### Database Errors
```bash
# Check logs for:
# - "Database initialized successfully"
# - "Baseline adoption" messages
# - Migration runner output
```

---

## Local Development vs Staging Parity

| Aspect | Local | Staging | Notes |
|--------|-------|---------|-------|
| OBD Mode | simulation/real | simulation only | Enforced by env |
| AI Model | LM Studio local | Unavailable | Graceful degradation |
| Database | `data/i20_garage.db` | `/app/data/i20_garage_staging.db` | Separate files |
| Auth | None | Basic Auth (Render) | Different layer |
| HTTPS | No | Yes (Render TLS) | Automatic |
| Persistence | Full | Ephemeral (default) | Add Disk for parity |
| Simulation Speed | 0.5s interval | 1.0s interval | CPU optimization |

---

## Next Steps for Production

When promoting to production:
1. Add Render Disk for database persistence
2. Provision external PostgreSQL (replace SQLite)
3. Deploy LM Studio on GPU instance or use cloud LLM API
4. Implement application-level authentication
5. Add monitoring (Sentry, LogRocket)
6. Configure custom domain
7. Set up CI/CD with staging → production promotion
8. Load test with concurrent users

---

## Support

- **Render Docs:** https://render.com/docs
- **Streamlit Deploy:** https://docs.streamlit.io/deploy
- **Issues:** https://github.com/Ishan112-web/Hyundai-i-20-OBD-analyzer-app/issues