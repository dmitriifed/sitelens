# Demo watch - Fedora setup

Goal: the app never greets a reviewer with the sleep screen during the
17-28 Aug screening window, and you have a latency log you own.

Three layers, independent:
1. UptimeRobot (tonight, 5 minutes) - external HTTP monitor, 5-min
   interval, free tier. Always-on regardless of your laptop's state.
   This is the primary keep-alive because a laptop sleeps too.
2. Fedora systemd timer (below) - your owned instrument: liveness
   classification + latency log. Also your first proper Linux job.
3. Demo video (Saturday, Q11) - reviewer-proof regardless of app state.

Honest caveat: whether a plain HTTP GET counts as "activity" for
Streamlit Community Cloud's sleep detection needs one empirical day -
community reports vary. Verification step below. If GET does not hold it
awake, escalate to a headless-browser ping (playwright) or accept
UptimeRobot + morning manual wake.

The pinger covers liveness only. It does not exercise Pinecone or
Gemini. One manual end-to-end run each morning during screening: map
loads, one semantic query, one Gemini translation.

---

## 1. Script - ~/bin/sitelens_watch.sh

```bash
#!/usr/bin/env bash
# Keep-alive ping + health classification for the deployed demo.
set -u
URL="https://sitelens.streamlit.app"        # adjust if needed
LOG="$HOME/sitelens_watch/watch.log"
mkdir -p "$(dirname "$LOG")"

ts=$(date -Is)
start=$(date +%s%3N)
body=$(curl -fsSL --max-time 30 "$URL" 2>/dev/null)
rc=$?
end=$(date +%s%3N)
ms=$((end - start))

if [ $rc -ne 0 ]; then
    state="DOWN(rc=$rc)"
elif printf '%s' "$body" | grep -qiE 'gone to sleep|wake it up|zzz'; then
    state="SLEEPING"
elif printf '%s' "$body" | grep -qi 'streamlit'; then
    state="AWAKE"
else
    state="UNKNOWN"
fi

echo "$ts,$state,${ms}ms" >> "$LOG"
[ "$state" = "AWAKE" ]
```

Note: the SLEEPING marker strings are a first guess. When you first
catch a real sleep page (or after submission, pause the timer for a day
and look), adjust the grep to the exact text Streamlit serves.

## 2. Units - ~/.config/systemd/user/

sitelens-watch.service
```ini
[Unit]
Description=SiteLens demo keep-alive and health check

[Service]
Type=oneshot
ExecStart=%h/bin/sitelens_watch.sh
```

sitelens-watch.timer
```ini
[Unit]
Description=Run SiteLens watch every 30 minutes

[Timer]
OnBootSec=2min
OnUnitActiveSec=30min
Persistent=true

[Install]
WantedBy=timers.target
```

## 3. Install

```bash
mkdir -p ~/bin ~/.config/systemd/user
# create the three files above, then:
chmod +x ~/bin/sitelens_watch.sh
systemctl --user daemon-reload
systemctl --user enable --now sitelens-watch.timer
loginctl enable-linger "$USER"   # timer survives logout (not suspend)
```

## 4. Verify

```bash
~/bin/sitelens_watch.sh; echo "exit=$?"   # run once by hand
systemctl --user list-timers | grep sitelens
tail -5 ~/sitelens_watch/watch.log
```

Empirical test (before freeze): leave the app untouched by humans for
24h with the timer running. If the log stays AWAKE throughout, GET holds
it. If SLEEPING appears, the GET is not registering as activity -
UptimeRobot may behave the same, so escalate: `pip install playwright`
+ a 5-line headless page-load on the same timer, or accept the morning
manual wake during screening (open the app before ~09:00 JST = 03:00
IDT is not realistic manually, which is why the automated layer
matters).

Laptop reality: suspend pauses user timers. For the screening window the
external monitor is the layer that never sleeps; the Fedora timer is the
instrument and the log.
