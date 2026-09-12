import json, html, sys, re
LOCAL = '--local' in sys.argv
tracks = json.load(open('tracks.json'))
def safe(t): return re.sub(r'[^A-Za-z0-9 ._()&,-]', '_', f"{t['n']:02d} - {t['title']}")
if LOCAL:
    for t in tracks:
        t['m4a'] = 'audio/' + safe(t) + '.mp3'
        t['wav'] = 'audio/' + safe(t) + '.wav'
        t['art'] = 'audio/' + safe(t) + '.jpg'
songs = []
for t in tracks:
    if t['song'] not in songs: songs.append(t['song'])

def fmt(s): return f"{s//60}:{s%60:02d}"
total = sum(t['dur'] for t in tracks)

rows = []
for s in songs:
    vs = [t for t in tracks if t['song'] == s]
    rows.append(f'<section class="song" id="{html.escape(s.lower().replace(" ","-").replace(",",""))}"><h2>{html.escape(s)}<span class="count">{len(vs)} version{"s" if len(vs)>1 else ""}</span></h2><ol class="versions">')
    for t in vs:
        sub = t['title'][len(s):].strip() if t['title'].startswith(s) else t['title']
        sub = sub.strip('() ').replace(') (', ' · ') or 'Original take'
        rows.append(f'<li class="tr" data-n="{t["n"]}"><button class="play" aria-label="Play {html.escape(t["title"])}"><svg viewBox="0 0 24 24"><path class="p" d="M8 5v14l11-7z"/><path class="q" d="M6 5h4v14H6zm8 0h4v14h-4z"/></svg></button><img class="art" src="{t["art"]}" alt="" loading="lazy"><div class="meta"><div class="t">{html.escape(sub)}</div></div><span class="dur">{fmt(t["dur"])}</span><a class="dl" href="{t["wav"]}" download title="Download WAV">WAV</a></li>')
    rows.append('</ol></section>')

page = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>No Control — Killer Box Cutters, rebuilt</title>
<meta name="description" content="{len(tracks)} tracks: the Killer Box Cutters catalog rebuilt as 1st-wave reggae, dub, rocksteady and ska-punk under the name No Control.">
<meta property="og:title" content="No Control — Killer Box Cutters, rebuilt">
<meta property="og:description" content="{len(songs)} songs, {len(tracks)} versions. Reggae, dub and ska-punk remakes of the Killer Box Cutters catalog.">
<meta property="og:image" content="{tracks[0]['art']}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
:root{{--bg:#0b0c0f;--bg2:#13151a;--bg3:#1b1e25;--fg:#e8e6df;--fg2:#9a9890;--fg3:#5f5e58;--acc:#f2c14e;--acc2:#3fb27f;--line:#262932}}
*{{box-sizing:border-box}}
html{{scroll-behavior:smooth}}
body{{margin:0;background:var(--bg);color:var(--fg);font-family:'Space Grotesk',system-ui,sans-serif;padding:0 16px 120px;line-height:1.45}}
a{{color:inherit}}
.wrap{{max-width:900px;margin:0 auto}}
header{{padding:56px 0 28px;border-bottom:1px solid var(--line)}}
.kicker{{font-family:'JetBrains Mono',monospace;font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--acc2)}}
h1{{font-size:clamp(40px,8vw,84px);line-height:.95;margin:10px 0 14px;letter-spacing:-.03em;font-weight:700}}
.lede{{font-size:18px;color:var(--fg2);max-width:640px;margin:0 0 20px}}
.stats{{font-family:'JetBrains Mono',monospace;font-size:13px;color:var(--fg3);display:flex;gap:18px;flex-wrap:wrap}}
.stats b{{color:var(--fg)}}
.btnrow{{display:flex;gap:10px;flex-wrap:wrap;margin-top:22px}}
.btn{{font-family:'JetBrains Mono',monospace;font-size:13px;padding:10px 16px;border:1px solid var(--line);border-radius:6px;background:var(--bg2);color:var(--fg);cursor:pointer;text-decoration:none}}
.btn.pri{{background:var(--acc);color:#111;border-color:var(--acc);font-weight:600}}
nav.toc{{display:flex;flex-wrap:wrap;gap:6px 14px;padding:18px 0;border-bottom:1px solid var(--line);font-family:'JetBrains Mono',monospace;font-size:12px}}
nav.toc a{{color:var(--fg2);text-decoration:none}} nav.toc a:hover{{color:var(--acc)}}
.song{{padding:28px 0 8px}}
h2{{font-size:26px;margin:0 0 10px;display:flex;align-items:baseline;gap:12px;letter-spacing:-.01em}}
.count{{font-family:'JetBrains Mono',monospace;font-size:12px;color:var(--fg3);font-weight:400}}
ol.versions{{list-style:none;margin:0;padding:0}}
.tr{{display:grid;grid-template-columns:36px 44px 1fr auto auto;align-items:center;gap:12px;padding:8px 10px;border-radius:8px;border:1px solid transparent}}
.tr:hover{{background:var(--bg2)}}
.tr.on{{background:var(--bg3);border-color:var(--line)}}
.play{{width:36px;height:36px;border-radius:50%;border:1px solid var(--line);background:var(--bg2);color:var(--fg);cursor:pointer;display:grid;place-items:center;padding:0}}
.play svg{{width:18px;height:18px;fill:currentColor}} .play .q{{display:none}}
.tr.on .play{{background:var(--acc);color:#111;border-color:var(--acc)}}
.tr.on.playing .play .p{{display:none}} .tr.on.playing .play .q{{display:block}}
.art{{width:44px;height:44px;border-radius:6px;object-fit:cover;background:var(--bg3)}}
.meta{{min-width:0}} .t{{font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.tr.on .t{{color:var(--acc)}}
.dur{{font-family:'JetBrains Mono',monospace;font-size:12px;color:var(--fg3)}}
.dl{{font-family:'JetBrains Mono',monospace;font-size:11px;color:var(--fg3);text-decoration:none;border:1px solid var(--line);padding:3px 7px;border-radius:4px}}
.dl:hover{{color:var(--fg);border-color:var(--fg3)}}
footer{{margin-top:48px;padding-top:20px;border-top:1px solid var(--line);color:var(--fg3);font-size:13px;font-family:'JetBrains Mono',monospace}}
#bar{{position:fixed;left:0;right:0;bottom:0;background:rgba(19,21,26,.96);backdrop-filter:blur(8px);border-top:1px solid var(--line);padding:10px 16px;transform:translateY(110%);transition:transform .25s}}
#bar.show{{transform:none}}
#bar .in{{max-width:900px;margin:0 auto;display:grid;grid-template-columns:auto 1fr auto;gap:14px;align-items:center}}
#bar .now{{min-width:0;font-size:14px}} #bar .now b{{display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}} #bar .now span{{color:var(--fg2);font-size:12px;font-family:'JetBrains Mono',monospace}}
#seek{{width:100%;margin:6px 0 0;accent-color:var(--acc)}}
#bar .ctl{{display:flex;gap:6px}}
#bar .ctl button{{width:36px;height:36px;border-radius:50%;border:1px solid var(--line);background:var(--bg3);color:var(--fg);cursor:pointer;font-family:'JetBrains Mono',monospace}}
@media (max-width:560px){{.tr{{grid-template-columns:36px 1fr auto}}.art,.dl{{display:none}}}}
</style>
</head>
<body>
<div class="wrap">
<header>
<div class="kicker">Killer Box Cutters · rebuilt</div>
<h1>No Control</h1>
<p class="lede">The Killer Box Cutters songbook, rebuilt from the ground up as 1st-wave reggae, rocksteady, dub and ska-punk. Same songs, new riddims. A virtual version of the band, under a new name.</p>
<div class="stats"><span><b>{len(songs)}</b> songs</span><span><b>{len(tracks)}</b> versions</span><span><b>{total//3600}h {total%3600//60}m</b> total</span></div>
<div class="btnrow"><button class="btn pri" id="playall">▶ Play all</button><button class="btn" id="shuffle">Shuffle</button><a class="btn" href="https://www.flowmusic.app/playlist/f82a3c26-469a-463a-af96-dba40f117fa1" target="_blank" rel="noopener">Flow playlist ↗</a></div>
</header>
<nav class="toc">{"".join(f'<a href="#{html.escape(s.lower().replace(" ","-").replace(",",""))}">{html.escape(s)}</a>' for s in songs)}</nav>
{"".join(rows)}
<footer>No Control is AntimatterAnomaly's virtual reworking of Killer Box Cutters. Every track here is a remake of a KBC original.</footer>
</div>
<div id="bar"><div class="in"><div class="ctl"><button id="prev" title="Previous">‹</button><button id="pp" title="Play/Pause">▶</button><button id="next" title="Next">›</button></div><div class="now"><b id="nowt">—</b><span id="nows"></span><input id="seek" type="range" min="0" max="1000" value="0"></div><div class="dur" id="nowd">0:00</div></div></div>
<audio id="a" preload="none"></audio>
<script>
const T={json.dumps([{ 'n':t['n'],'title':t['title'],'song':t['song'],'m4a':t['m4a'] } for t in tracks])};
const a=document.getElementById('a'),bar=document.getElementById('bar'),rows=[...document.querySelectorAll('.tr')];
let cur=-1,order=T.map((_,i)=>i);
const f=s=>isFinite(s)?`${{Math.floor(s/60)}}:${{String(Math.floor(s%60)).padStart(2,'0')}}`:'0:00';
function load(i,go=true){{cur=i;const t=T[i];a.src=t.m4a;document.getElementById('nowt').textContent=t.title;document.getElementById('nows').textContent=t.song;rows.forEach(r=>r.classList.toggle('on',+r.dataset.n===t.n));bar.classList.add('show');if(go)a.play();}}
function step(d){{if(cur<0)return load(order[0]);const p=order.indexOf(cur);load(order[(p+d+order.length)%order.length]);}}
rows.forEach((r,i)=>r.querySelector('.play').onclick=()=>{{const idx=T.findIndex(t=>t.n===+r.dataset.n);if(idx===cur){{a.paused?a.play():a.pause();}}else load(idx);}});
document.getElementById('playall').onclick=()=>{{order=T.map((_,i)=>i);load(order[0]);}};
document.getElementById('shuffle').onclick=()=>{{order=T.map((_,i)=>i).sort(()=>Math.random()-.5);load(order[0]);}};
document.getElementById('pp').onclick=()=>{{if(cur<0)return load(0);a.paused?a.play():a.pause();}};
document.getElementById('prev').onclick=()=>step(-1);document.getElementById('next').onclick=()=>step(1);
a.onended=()=>step(1);
a.onplay=a.onpause=()=>{{const p=!a.paused;document.getElementById('pp').textContent=p?'❚❚':'▶';rows.forEach(r=>r.classList.toggle('playing',r.classList.contains('on')&&p));}};
a.ontimeupdate=()=>{{if(a.duration){{seek.value=a.currentTime/a.duration*1000;document.getElementById('nowd').textContent=f(a.currentTime)+' / '+f(a.duration);}}}};
seek.oninput=()=>{{if(a.duration)a.currentTime=seek.value/1000*a.duration;}};
if('mediaSession' in navigator){{navigator.mediaSession.setActionHandler('nexttrack',()=>step(1));navigator.mediaSession.setActionHandler('previoustrack',()=>step(-1));}}
</script>
</body>
</html>'''
open('index.html','w').write(page)
print(len(page))
