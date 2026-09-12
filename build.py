import json, html, sys, re, os
LOCAL = '--local' in sys.argv
tracks = json.load(open('tracks.json'))
def safe(t): return re.sub(r'[^A-Za-z0-9 ._()&,-]', '_', f"{t['n']:02d} - {t['title']}")

# Song slug: used for the section anchor, the TOC link and the lyrics.json key.
# Defined once so those three can't drift apart.
def slug(s): return s.lower().replace(" ", "-").replace(",", "")

# Lyrics live per song, not per version, so all takes of a song share one entry.
# Missing file or missing song is fine — the view shows an empty state.
lyrics = {}
if os.path.exists('lyrics.json'):
    lyrics = (json.load(open('lyrics.json')) or {}).get('songs', {})
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
    sl = slug(s)
    has = ' has' if lyrics.get(sl) else ''
    rows.append(f'<section class="song" id="{html.escape(sl)}"><h2>{html.escape(s)}<span class="count">{len(vs)} version{"s" if len(vs)>1 else ""}</span><button class="lyrbtn{has}" data-song="{html.escape(sl)}" title="Lyrics for {html.escape(s)}">Lyrics</button></h2><ol class="versions">')
    for t in vs:
        sub = t['title'][len(s):].strip() if t['title'].startswith(s) else t['title']
        sub = sub.strip('() ').replace(') (', ' · ') or 'Original take'
        rows.append(f'<li class="tr" data-n="{t["n"]}"><button class="play" aria-label="Play {html.escape(t["title"])}"><svg viewBox="0 0 24 24"><path class="p" d="M8 5v14l11-7z"/><path class="q" d="M6 5h4v14H6zm8 0h4v14h-4z"/></svg></button><img class="art" src="{t["art"]}" alt="" loading="lazy"><div class="meta"><div class="t">{html.escape(sub)}</div></div><span class="dur">{fmt(t["dur"])}</span><a class="dl" href="{t["wav"]}" download title="Download WAV">WAV</a></li>')
    rows.append('</ol></section>')

# Kept out of the page f-string below so the braces don't all need doubling.
LYRICS_CSS = """
.lyrbtn{font-family:'JetBrains Mono',monospace;font-size:11px;font-weight:400;letter-spacing:0;color:var(--fg3);background:none;border:1px solid var(--line);padding:3px 7px;border-radius:4px;cursor:pointer}
.lyrbtn:hover{color:var(--acc);border-color:var(--fg3)}
.lyrbtn.has{color:var(--acc2);border-color:var(--line)}
.lyrbtn.has:hover{color:var(--acc)}
h2 .lyrbtn{align-self:center}
#bar .in{grid-template-columns:auto 1fr auto auto}
#lyr{position:fixed;inset:0;z-index:50;background:var(--bg);display:none;flex-direction:column}
#lyr.show{display:flex}
#lyr :focus-visible{outline:2px solid var(--acc);outline-offset:2px}
#lyrhead{display:flex;align-items:center;gap:12px;padding:14px 16px;border-bottom:1px solid var(--line)}
#lyrhead .id{flex:1;min-width:0}
#lyrt{display:block;font-size:17px;font-weight:700;letter-spacing:-.01em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#lyrs{font-family:'JetBrains Mono',monospace;font-size:12px;color:var(--fg2);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#lyrhead .ctl{display:flex;gap:6px;flex:0 0 auto}
#lyrhead .ctl button{width:36px;height:36px;border-radius:50%;border:1px solid var(--line);background:var(--bg3);color:var(--fg);cursor:pointer;font-family:'JetBrains Mono',monospace}
#lyrhead .ctl button:hover{border-color:var(--fg3)}
#lyrbox{flex:1;overflow-y:auto;overscroll-behavior:contain}
#lyrin{max-width:34ch;margin:0 auto;padding:40vh 16px}
#lyrin p{margin:0;padding:7px 0;font-size:clamp(22px,4.4vw,34px);line-height:1.3;letter-spacing:-.01em;color:var(--fg3);transition:color .3s}
#lyrin p.on{color:var(--fg)}
#lyrin p.sec{font-family:'JetBrains Mono',monospace;font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--acc2);padding:20px 0 6px}
#lyrin p.sec.on{color:var(--acc)}
#lyrin p.gap{padding:0;height:.7em}
#lyrin .empty{font-family:'JetBrains Mono',monospace;font-size:14px;line-height:1.7;color:var(--fg2)}
#lyrin .empty code{color:var(--acc)}
#lyrfoot{display:flex;gap:14px;align-items:center;flex-wrap:wrap;padding:10px 16px;border-top:1px solid var(--line);font-family:'JetBrains Mono',monospace;font-size:12px;color:var(--fg3)}
#lyr.imm #lyrhead,#lyr.imm #lyrfoot{opacity:0;pointer-events:none;transition:opacity .3s}
#lyr.imm:hover #lyrhead,#lyr.imm:hover #lyrfoot,#lyr.imm:focus-within #lyrhead,#lyr.imm:focus-within #lyrfoot{opacity:1;pointer-events:auto}
body.lock{overflow:hidden}
@media (max-width:560px){#lyrin{padding:32vh 16px}#lyrfoot .hint{display:none}}
@media (prefers-reduced-motion:reduce){#lyrin p{transition:none}#lyrbox{scroll-behavior:auto}}
"""

LYRICS_JS = """
(function(){
const ov=document.getElementById('lyr'),box=document.getElementById('lyrbox'),inner=document.getElementById('lyrin'),
      ttl=document.getElementById('lyrt'),sub=document.getElementById('lyrs'),pos=document.getElementById('lyrpos');
let si=-1,els=[],nav=[],li=0,lastFocus=null;
const rm=()=>matchMedia('(prefers-reduced-motion: reduce)').matches;
const isSec=t=>/^\\s*\\[.*\\]\\s*$/.test(t);

function render(lines){
  inner.innerHTML='';els=[];nav=[];
  if(!lines.length){
    const d=document.createElement('div');d.className='empty';
    d.innerHTML='No lyrics for this song yet.<br><br>Add them to <code>lyrics.json</code> under <code>songs \\u2192 "'+SONGS[si].slug+'"</code>, then run <code>make build</code>.';
    inner.appendChild(d);pos.textContent='';return;
  }
  lines.forEach((t,i)=>{
    const p=document.createElement('p');
    if(!String(t).trim()){p.className='gap';p.setAttribute('aria-hidden','true');}
    else{if(isSec(t))p.className='sec';p.textContent=t;nav.push(i);}
    inner.appendChild(p);els[i]=p;
  });
  setLine(nav.length?nav[0]:0,false);
}
function centre(n){
  if(!n)return;
  const b=box.getBoundingClientRect(),r=n.getBoundingClientRect();
  box.scrollTo({top:box.scrollTop+(r.top+r.height/2)-(b.top+b.height/2),behavior:rm()?'auto':'smooth'});
}
function setLine(i,scroll){
  els.forEach((n,j)=>{if(n)n.classList.toggle('on',j===i);});
  li=i;
  if(scroll!==false)centre(els[i]);
  const k=nav.indexOf(i);
  pos.textContent=k>=0?'Line '+(k+1)+' / '+nav.length:'';
}
function stepLine(d){
  if(!nav.length)return;
  let k=nav.indexOf(li);
  if(k<0){k=0;for(let x=0;x<nav.length;x++){if(nav[x]>=li){k=x;break;}}}
  else k=Math.min(nav.length-1,Math.max(0,k+d));
  setLine(nav[k]);
}
function openSong(i,subtitle,trigger){
  if(i<0||i>=SONGS.length)return;
  si=i;if(trigger!==null)lastFocus=trigger||document.activeElement;
  const s=SONGS[i];
  ttl.textContent=s.name;
  sub.textContent=subtitle||(s.count+' version'+(s.count>1?'s':''));
  ov.classList.add('show');document.body.classList.add('lock');
  render(LYR[s.slug]||[]);
  box.scrollTop=0;if(nav.length)centre(els[nav[0]]);
  ov.focus();
}
function stepSong(d){if(si<0)return;openSong((si+d+SONGS.length)%SONGS.length,null,null);}
function close(){
  exitFs();ov.classList.remove('show','imm');
  document.body.classList.remove('lock');si=-1;
  if(lastFocus&&lastFocus.focus)lastFocus.focus();
}
const fsEl=()=>document.fullscreenElement||document.webkitFullscreenElement||null;
function exitFs(){if(!fsEl())return;const f=document.exitFullscreen||document.webkitExitFullscreen;if(f){try{f.call(document);}catch(e){}}}
function toggleFs(){
  if(fsEl()){exitFs();return;}
  const f=ov.requestFullscreen||ov.webkitRequestFullscreen;
  if(!f){ov.classList.add('imm');return;}
  let r;try{r=f.call(ov);}catch(e){ov.classList.add('imm');return;}
  if(r&&r.catch)r.catch(()=>ov.classList.add('imm'));
}
document.addEventListener('fullscreenchange',()=>{if(!fsEl())ov.classList.remove('imm');setTimeout(()=>centre(els[li]),60);});
document.getElementById('lyrclose').onclick=close;
document.getElementById('lyrfs').onclick=toggleFs;
document.getElementById('lyrprev').onclick=()=>stepSong(-1);
document.getElementById('lyrnext').onclick=()=>stepSong(1);
document.querySelectorAll('.lyrbtn[data-song]').forEach(b=>{
  b.onclick=()=>openSong(SONGS.findIndex(s=>s.slug===b.dataset.song),null,b);
});
const nowBtn=document.getElementById('lyrnow');
nowBtn.onclick=()=>{if(cur<0)return;const t=T[cur];openSong(SONGS.findIndex(s=>s.slug===t.slug),t.title,nowBtn);};
document.addEventListener('keydown',e=>{
  if(!ov.classList.contains('show'))return;
  if(e.metaKey||e.ctrlKey||e.altKey)return;
  switch(e.key){
    case 'Escape':e.preventDefault();
      if(fsEl()||ov.classList.contains('imm')){exitFs();ov.classList.remove('imm');}else close();break;
    case 'ArrowUp':case 'k':case 'K':e.preventDefault();stepLine(-1);break;
    case 'ArrowDown':case 'j':case 'J':e.preventDefault();stepLine(1);break;
    case 'ArrowLeft':e.preventDefault();stepSong(-1);break;
    case 'ArrowRight':e.preventDefault();stepSong(1);break;
    case 'Home':e.preventDefault();if(nav.length)setLine(nav[0]);break;
    case 'End':e.preventDefault();if(nav.length)setLine(nav[nav.length-1]);break;
    case 'f':case 'F':e.preventDefault();toggleFs();break;
    case ' ':e.preventDefault();if(cur<0){load(0);}else{a.paused?a.play():a.pause();}break;
    case 'Tab':{
      const fo=[...ov.querySelectorAll('button')].filter(n=>n.offsetParent!==null);
      if(!fo.length)break;
      const first=fo[0],last=fo[fo.length-1];
      if(e.shiftKey&&(document.activeElement===first||document.activeElement===ov)){e.preventDefault();last.focus();}
      else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}
      break;
    }
  }
});
})();
"""

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
{LYRICS_CSS}
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
<nav class="toc">{"".join(f'<a href="#{html.escape(slug(s))}">{html.escape(s)}</a>' for s in songs)}</nav>
{"".join(rows)}
<footer>No Control is AntimatterAnomaly's virtual reworking of Killer Box Cutters. Every track here is a remake of a KBC original.</footer>
</div>
<div id="bar"><div class="in"><div class="ctl"><button id="prev" title="Previous">‹</button><button id="pp" title="Play/Pause">▶</button><button id="next" title="Next">›</button></div><div class="now"><b id="nowt">—</b><span id="nows"></span><input id="seek" type="range" min="0" max="1000" value="0"></div><div class="dur" id="nowd">0:00</div><button class="lyrbtn" id="lyrnow" title="Lyrics for the current track">Lyrics</button></div></div>
<div id="lyr" role="dialog" aria-modal="true" aria-labelledby="lyrt" tabindex="-1">
<div id="lyrhead"><div class="id"><b id="lyrt"></b><span id="lyrs"></span></div><div class="ctl"><button id="lyrprev" title="Previous song (Left arrow)" aria-label="Previous song">&lsaquo;</button><button id="lyrnext" title="Next song (Right arrow)" aria-label="Next song">&rsaquo;</button><button id="lyrfs" title="Fullscreen (F)" aria-label="Toggle fullscreen">&#9974;</button><button id="lyrclose" title="Close (Escape)" aria-label="Close lyrics">&#10005;</button></div></div>
<div id="lyrbox" tabindex="0"><div id="lyrin"></div></div>
<div id="lyrfoot"><span id="lyrpos"></span><span class="hint">&uarr;&darr; lines &middot; &larr;&rarr; songs &middot; F fullscreen &middot; Space play/pause &middot; Esc close</span></div>
</div>
<audio id="a" preload="none"></audio>
<script>
const T={json.dumps([{ 'n':t['n'],'title':t['title'],'song':t['song'],'slug':slug(t['song']),'m4a':t['m4a'] } for t in tracks])};
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
const LYR={json.dumps(lyrics)},SONGS={json.dumps([{'slug': slug(s), 'name': s, 'count': sum(1 for t in tracks if t['song'] == s)} for s in songs])};
{LYRICS_JS}
</script>
</body>
</html>'''
open('index.html','w').write(page)
print(len(page))
