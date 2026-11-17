from flask import Flask, request, jsonify, render_template_string
from threading import Lock
import os

app = Flask(__name__)
scores = {}
lock = Lock()
API_KEY = os.environ.get('GAME_API_KEY')

DASHBOARD = '''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Cloud Arcade | Leaderboard</title>
<style>
:root{color-scheme:dark;font-family:Inter,ui-sans-serif,system-ui,-apple-system,Segoe UI,sans-serif}*{box-sizing:border-box}
body{margin:0;min-height:100vh;background:radial-gradient(ellipse at 50% -10%,#24355e 0%,#101525 46%,#090d18 100%);color:#f3f6ff}
main{max-width:920px;margin:auto;padding:64px 24px}header{display:flex;align-items:center;justify-content:space-between;gap:20px;flex-wrap:wrap}
.eyebrow{color:#8b9ac2;text-transform:uppercase;letter-spacing:.2em;font-size:12px;font-weight:800}
h1{font-size:clamp(38px,6vw,64px);margin:12px 0 6px;letter-spacing:-.05em}h1 span{color:#6ef2cb}
.sub{color:#9daac8;font-size:17px}.status{border:1px solid #2a765e;background:#14352f;padding:12px 18px;border-radius:100px;color:#83f4c8;font-weight:700}
.panel{margin-top:36px;border:1px solid #34415c;border-radius:24px;background:#151d30;overflow:hidden;box-shadow:0 24px 70px #0005}
.panel-top{display:flex;align-items:center;justify-content:space-between;padding:26px 30px;border-bottom:1px solid #303b53}
h2{margin:0;font-size:23px}.small{color:#9ba9c6;font-size:14px}
.entry{display:grid;grid-template-columns:65px 1fr auto;gap:14px;align-items:center;padding:22px 30px;border-bottom:1px solid #2b3449}
.entry:last-child{border:0}.entry:first-child{background:linear-gradient(90deg,#263b47,#18243a)}.rank{font-size:24px;font-weight:900;color:#d7e3fa}
.name{font-size:20px;font-weight:750}.score{font-size:25px;font-weight:900;color:#75f4cb;font-variant-numeric:tabular-nums}
.empty{padding:42px 30px;color:#9ba9c6;text-align:center}.footer{display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap;margin-top:24px;color:#8292b3;font-size:13px}
</style></head><body><main><header><div><div class="eyebrow">Python × AWS EC2</div><h1>☁️ Cloud <span>Arcade</span></h1><div class="sub">Live Snake Game Leaderboard</div></div><div class="status" id="status">● Checking server</div></header>
<section class="panel"><div class="panel-top"><h2>🏆 Top Players</h2><div class="small" id="count">Loading…</div></div><div id="entries"><div class="empty">Loading leaderboard…</div></div></section>
<div class="footer"><span>🐍 Built with Python + Flask • Hosted on AWS</span><span>Auto-refreshes every 5 seconds</span></div>
</main><script>
async function refresh(){try{const [h,l]=await Promise.all([fetch('/health',{cache:'no-store'}),fetch('/leaderboard',{cache:'no-store'})]);if(!h.ok||!l.ok)throw Error('Server unavailable');const health=await h.json(),players=await l.json();document.getElementById('status').textContent='● Server '+health.status;document.getElementById('count').textContent=players.length+' player'+(players.length===1?'':'s');const container=document.getElementById('entries');container.replaceChildren();if(!players.length){const el=document.createElement('div');el.className='empty';el.textContent='No scores yet — play Snake to join the leaderboard!';container.append(el);}players.forEach((p,i)=>{const row=document.createElement('div');row.className='entry';const rank=document.createElement('div');rank.className='rank';rank.textContent=i===0?'🥇':i===1?'🥈':i===2?'🥉':'#'+(i+1);const name=document.createElement('div');name.className='name';name.textContent=p.player;const score=document.createElement('div');score.className='score';score.textContent=Number(p.score).toLocaleString()+' pts';row.append(rank,name,score);container.append(row);});}catch(e){document.getElementById('status').textContent='● Server offline';}}
refresh();setInterval(refresh,5000);
</script></body></html>'''

@app.get('/')
def home():
    return render_template_string(DASHBOARD)

@app.get('/health')
def health():
    with lock:
        count = len(scores)
    return jsonify({'status': 'healthy', 'service': 'Python Cloud Game', 'players': count})

@app.get('/leaderboard')
def leaderboard():
    with lock:
        ranking = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    return jsonify([{'player': name, 'score': score} for name, score in ranking])

@app.post('/score')
def save_score():
    if not API_KEY or request.headers.get('X-API-Key') != API_KEY:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json(silent=True) or {}
    name, score = data.get('player'), data.get('score')
    if not isinstance(name, str) or not 1 <= len(name) <= 30:
        return jsonify({'error': 'Invalid player'}), 400
    if type(score) is not int or not 0 <= score <= 100000:
        return jsonify({'error': 'Invalid score'}), 400
    with lock:
        scores[name] = max(score, scores.get(name, 0))
        best = scores[name]
    return jsonify({'message': 'Score saved!', 'player': name, 'score': best})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
