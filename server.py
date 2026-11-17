"""Cloud Arcade: classroom Snake leaderboard and Flask API.

Install: pip install flask gunicorn
Run: GAME_API_KEY='choose-a-demo-key' gunicorn --workers 1 --bind 0.0.0.0:5000 server:app
Scores persist to SQLite in the directory containing this file.
"""
from datetime import datetime, timezone
from pathlib import Path
import hmac
import os
import sqlite3

from flask import Flask, jsonify, render_template_string, request

app = Flask(__name__)
DB_PATH = Path(os.environ.get('GAME_DB_PATH', str(Path(__file__).with_name('leaderboard.db'))))
API_KEY = os.environ.get('GAME_API_KEY', '')


def connect():
    db = sqlite3.connect(DB_PATH, timeout=10)
    db.row_factory = sqlite3.Row
    return db


def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with connect() as db:
        db.execute('''CREATE TABLE IF NOT EXISTS scores (
            player TEXT PRIMARY KEY,
            score INTEGER NOT NULL,
            updated_at TEXT NOT NULL
        )''')


init_db()

DASHBOARD = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="theme-color" content="#0b1020"><title>Cloud Arcade | Live Snake Leaderboard</title>
<style>
:root{font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color-scheme:dark}
*{box-sizing:border-box}body{margin:0;min-height:100vh;background:#0a1020;color:#f1f6ff}
body:before{content:"";position:fixed;inset:0;pointer-events:none;background:radial-gradient(ellipse 70% 45% at 50% 0%,#26426899,transparent),linear-gradient(transparent 95%,#ffffff04 96%),linear-gradient(90deg,transparent 95%,#ffffff04 96%);background-size:auto,38px 38px,38px 38px}
main{position:relative;max-width:1050px;margin:0 auto;padding:52px 22px 38px}
.top{display:flex;justify-content:space-between;align-items:center;gap:20px;flex-wrap:wrap}.kicker{font-size:12px;letter-spacing:.23em;text-transform:uppercase;font-weight:800;color:#8ca9d8}
h1{font-size:clamp(42px,7vw,72px);line-height:1.04;letter-spacing:-.065em;margin:13px 0 12px}h1 span{color:#66edc0}.subtitle{color:#acbbd4;font-size:17px;margin:0}
.status{border:1px solid #326d61;border-radius:999px;background:#14372f;color:#a4ffdd;font-weight:750;padding:12px 16px;white-space:nowrap}.status.offline{background:#45252b;border-color:#a34e56;color:#ffc2c2}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:30px 0}.stat{border:1px solid #2b3d5d;border-radius:18px;background:#141f35bb;padding:19px 22px}.stat .label{font-size:12px;text-transform:uppercase;letter-spacing:.11em;color:#91a5c6;font-weight:800}.stat .value{font-size:clamp(22px,3vw,34px);font-weight:850;margin-top:7px;letter-spacing:-.04em}.stat .value.accent{color:#66edc0}
.panel{border:1px solid #304361;border-radius:24px;overflow:hidden;background:#141e32;box-shadow:0 28px 65px #0006}.panel-head{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:24px 26px;border-bottom:1px solid #2a3b56}h2{margin:0;font-size:23px;letter-spacing:-.035em}.hint{font-size:13px;color:#9fb2d0}
.entry{display:grid;grid-template-columns:58px 1fr auto;align-items:center;gap:12px;padding:20px 26px;border-bottom:1px solid #293850;animation:fade .3s ease}.entry:last-child{border:0}.entry:first-child{background:linear-gradient(90deg,#263f49aa,transparent)}.rank{font-size:25px;font-weight:900}.player{font-size:19px;font-weight:750;overflow-wrap:anywhere}.score{font-size:24px;font-weight:850;color:#6df1c6;font-variant-numeric:tabular-nums}.pts{font-size:12px;color:#a0b3cf;margin-left:5px;font-weight:600}.empty{padding:55px 20px;text-align:center;color:#a7b7d0}
.footer{display:flex;justify-content:space-between;gap:14px;flex-wrap:wrap;margin-top:24px;color:#93a7c6;font-size:13px}.api{color:#9af3d5;text-decoration:none}.api:hover{text-decoration:underline}
@keyframes fade{from{opacity:.55;transform:translateY(4px)}to{opacity:1;transform:translateY(0)}}
@media(max-width:580px){main{padding-top:30px}.stats{grid-template-columns:1fr 1fr}.stat:last-child{grid-column:1/-1}.entry{padding:17px 15px;grid-template-columns:45px 1fr auto}.score{font-size:20px}.player{font-size:16px}.panel-head{padding:20px 15px}}
</style></head><body><main>
<div class="top"><div><div class="kicker">🐍 Python × AWS EC2 × Flask</div><h1>Cloud <span>Arcade.</span></h1><p class="subtitle">Play Snake on a laptop. Watch the scores land in the cloud.</p></div><div class="status" id="status" role="status">● Connecting...</div></div>
<div class="stats"><div class="stat"><div class="label">Players</div><div class="value" id="players">—</div></div><div class="stat"><div class="label">High score</div><div class="value accent" id="high">—</div></div><div class="stat"><div class="label">Current champion</div><div class="value" id="champion">—</div></div></div>
<section class="panel"><div class="panel-head"><h2>🏆 Live Leaderboard</h2><span class="hint">Updates every 5 seconds</span></div><div id="entries"><div class="empty">Loading scores...</div></div></section>
<div class="footer"><span>☁️ Hosted on AWS EC2 · Powered by Python</span><span>Explore the API: <a class="api" href="/health">Health</a> · <a class="api" href="/leaderboard">JSON leaderboard</a></span></div>
</main><script>
const $=id=>document.getElementById(id);
async function refresh(){
 try{
  const [healthRes,boardRes]=await Promise.all([fetch('/health',{cache:'no-store'}),fetch('/leaderboard',{cache:'no-store'})]);
  if(!healthRes.ok||!boardRes.ok)throw new Error('Unavailable');
  const health=await healthRes.json(), board=await boardRes.json();
  $('status').textContent='● Server healthy';$('status').classList.remove('offline');
  $('players').textContent=health.players;$('high').textContent=board.length?Number(board[0].score).toLocaleString():'0';$('champion').textContent=board.length?board[0].player:'—';
  const container=$('entries');container.replaceChildren();
  if(!board.length){const el=document.createElement('div');el.className='empty';el.textContent='No scores yet. Play Snake to join the leaderboard!';container.append(el);}
  board.forEach((p,i)=>{const row=document.createElement('div');row.className='entry';const rank=document.createElement('div');rank.className='rank';rank.textContent=['🥇','🥈','🥉'][i]||'#'+(i+1);const name=document.createElement('div');name.className='player';name.textContent=p.player;const score=document.createElement('div');score.className='score';score.textContent=Number(p.score).toLocaleString();const pts=document.createElement('span');pts.className='pts';pts.textContent='PTS';score.append(pts);row.append(rank,name,score);container.append(row);});
 }catch(e){$('status').textContent='● Server offline';$('status').classList.add('offline');}
}
refresh();setInterval(refresh,5000);
</script></body></html>'''


@app.after_request
def no_cache(response):
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


@app.get('/')
def home():
    return render_template_string(DASHBOARD)


@app.get('/health')
def health():
    with connect() as db:
        count = db.execute('SELECT COUNT(*) FROM scores').fetchone()[0]
    return jsonify({'status': 'healthy', 'service': 'Python Cloud Game', 'players': count})


@app.get('/leaderboard')
def leaderboard():
    with connect() as db:
        rows = db.execute('SELECT player, score FROM scores ORDER BY score DESC, player ASC').fetchall()
    return jsonify([{'player': row['player'], 'score': row['score']} for row in rows])


@app.post('/score')
def save_score():
    provided = request.headers.get('X-API-Key', '')
    if not API_KEY or not hmac.compare_digest(provided, API_KEY):
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({'error': 'Expected JSON object'}), 400
    name, score = data.get('player'), data.get('score')
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 30 or any(ord(c) < 32 for c in name):
        return jsonify({'error': 'Invalid player'}), 400
    if type(score) is not int or not 0 <= score <= 100000:
        return jsonify({'error': 'Invalid score'}), 400
    name = name.strip()
    now = datetime.now(timezone.utc).isoformat()
    with connect() as db:
        db.execute('''INSERT INTO scores (player, score, updated_at) VALUES (?, ?, ?)
            ON CONFLICT(player) DO UPDATE SET
            score = MAX(scores.score, excluded.score), updated_at = excluded.updated_at''', (name, score, now))
        best = db.execute('SELECT score FROM scores WHERE player = ?', (name,)).fetchone()[0]
    return jsonify({'message': 'Score saved!', 'player': name, 'score': best})


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)
