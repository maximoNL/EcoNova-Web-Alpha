"""Game A - Eco-Runner: Trash Collect & Sort (10 levels, SDG 13).

Collect waste, carry it to the Recycling Factory, then sort it into bins that shuffle
after every item. Supports keyboard, mouse and touch, plus fullscreen.

A self-contained HTML5 Canvas game (no external assets). ``get_trash_platformer_html``
returns the page to embed with ``streamlit.components.v1.html(..., height=620)``.
"""
from __future__ import annotations

import json

LEVELS = 10

WASTE_ITEMS = [
    {"id": "newspaper", "name": "Newspaper", "bin": "paper", "level": 1,
     "reason": "Paper fibres can be recycled into new paper."},
    {"id": "plastic_bottle", "name": "Plastic Bottle", "bin": "plastic", "level": 1,
     "reason": "Plastic bottles are collected with plastics so they can be recycled."},
    {"id": "glass_jar", "name": "Glass Jar", "bin": "glass", "level": 1,
     "reason": "Glass can be recycled again and again."},
    {"id": "banana_peel", "name": "Banana Peel", "bin": "organic", "level": 1,
     "reason": "Food scraps are organic. Rotting in a landfill they release methane, a greenhouse gas."},
    {"id": "cardboard_box", "name": "Cardboard Box", "bin": "paper", "level": 1,
     "reason": "Cardboard is made of paper fibres and goes with paper."},
    {"id": "plastic_cup", "name": "Plastic Cup", "bin": "plastic", "level": 1,
     "reason": "A plastic cup is plastic, so it goes in the plastic bin."},
    {"id": "glass_bottle", "name": "Glass Bottle", "bin": "glass", "level": 1,
     "reason": "Glass bottles go with glass, never with plastic."},
    {"id": "apple_core", "name": "Apple Core", "bin": "organic", "level": 1,
     "reason": "An apple core is organic waste that can rot and return to the soil as compost."},
    {"id": "aluminum_can", "name": "Aluminum Can", "bin": "metal", "level": 4,
     "reason": "Aluminum can be recycled again and again, which saves a lot of energy compared with making new metal."},
    {"id": "tin_can", "name": "Tin Can", "bin": "metal", "level": 4,
     "reason": "Steel food cans are metal and can be melted down and recycled."},
    {"id": "aa_battery", "name": "AA Battery", "bin": "battery", "level": 7,
     "reason": "Batteries contain chemicals and metals. Never put them in the normal trash; use a battery collection point."},
    {"id": "rechargeable_battery", "name": "Rechargeable Battery", "bin": "battery", "level": 7,
     "reason": "Used batteries are hazardous waste. Take them to a battery collection point so the metals can be recovered."},
]

# A bin is available from its ``level`` on (more bins on harder levels).
BINS = [
    {"id": "paper", "label": "Paper/Cardboard", "color": "#3b82c4", "level": 1},
    {"id": "plastic", "label": "Plastic", "color": "#e0a526", "level": 1},
    {"id": "glass", "label": "Glass", "color": "#2f9e6f", "level": 1},
    {"id": "organic", "label": "Organic", "color": "#8a5a36", "level": 1},
    {"id": "metal", "label": "Metal & Aluminum", "color": "#6b7a8c", "level": 4},
    {"id": "battery", "label": "Batteries", "color": "#c0392b", "level": 7},
]

SECRET_MESSAGE = (
    "Every item you sorted is a small climate action. Food scraps that rot in a landfill release methane, "
    "a greenhouse gas that warms the planet, so sorting waste properly helps protect the climate (SDG 13). "
    "And when you share what you learned with a friend, you are also supporting quality education (SDG 4)."
)

_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Eco-Runner</title>
<style>
html,body{margin:0;padding:0;height:100%;background:#0f2a1d;color:#D8F3DC;font-family:'Segoe UI',Arial,sans-serif;overflow:hidden}
#wrap{display:flex;flex-direction:column;align-items:center;background:#0f2a1d;min-height:100%}
#bar{display:flex;gap:10px;align-items:center;justify-content:center;flex-wrap:wrap;font-size:13px;padding:6px 10px;text-align:center;line-height:1.3}
#fs{background:#2D6A4F;color:#fff;border:0;border-radius:999px;padding:5px 14px;font:inherit;font-weight:700;cursor:pointer}
#fs:hover{background:#40916c}
canvas{display:block;width:100%;height:auto;max-width:min(1000px,calc((100vh - 52px) * 1.7778));background:#cfeedd;border-radius:10px;outline:none;touch-action:none;-webkit-user-select:none;user-select:none}
:fullscreen #wrap,:-webkit-full-screen #wrap{justify-content:center;height:100vh}
</style></head><body><div id="wrap">
<div id="bar"><span><b>Eco-Runner</b> &middot; Move: A/D or arrows &middot; Jump: W, Up or Space &middot; Sort: drag an item to a bin, tap a bin or press its number</span><button id="fs" type="button">Fullscreen</button></div>
<canvas id="game" width="960" height="540" tabindex="0"></canvas></div>
<script>
(function(){
"use strict";
const CFG = __CONFIG__;
const W=960,H=540,GROUND=480,SPEED=260,GRAV=1800,JUMP=640;
const cv=document.getElementById('game'),ctx=cv.getContext('2d');
const ITEMS=CFG.items,BINS=CFG.bins,TOTAL=CFG.levels;
const keys={};let state='menu',level=1,score=0,scoreAtStart=0,time=0,tAnim=0,worldW=1600;
let P,platforms,items,obstacles,collected,queue=[],floaters=[],feedback=null,shake={i:-1,t:0},bonus=0,confetti=[];
let drag=null,itemPos={x:480,y:175},camX=0,activeBins=[],slotBin=[],allDone=false,note=null,fade=0,touchMode=false;
const holds={},touch={left:false,right:false,jump:false};
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
const levelTime=n=>Math.round(90-(n-1)*10/3);
function mulberry32(a){return function(){a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296;};}
function rr(x,y,w,h,r){ctx.beginPath();ctx.moveTo(x+r,y);ctx.arcTo(x+w,y,x+w,y+h,r);ctx.arcTo(x+w,y+h,x,y+h,r);ctx.arcTo(x,y+h,x,y,r);ctx.arcTo(x,y,x+w,y,r);ctx.closePath();}
function wrap(text,maxW,font){ctx.font=font;const out=[];let line='';for(const w of text.split(' ')){const t=line?line+' '+w:w;if(ctx.measureText(t).width>maxW&&line){out.push(line);line=w;}else line=t;}if(line)out.push(line);return out;}
function centerText(text,y,font,color,maxW){const ls=wrap(text,maxW||820,font);ctx.font=font;ctx.fillStyle=color;ctx.textAlign='center';const px=parseInt(/(\d+)px/.exec(font)[1],10);ls.forEach((l,i)=>ctx.fillText(l,W/2,y+i*px*1.35));ctx.textAlign='left';return ls.length;}

/* ---------- fullscreen (hidden where the browser does not support it) ---------- */
const fsBtn=document.getElementById('fs'),fsRoot=document.getElementById('wrap'),docEl=document.documentElement;
const fsOn=()=>document.fullscreenElement||document.webkitFullscreenElement;
fsBtn.addEventListener('click',()=>{
  if(fsOn()){(document.exitFullscreen||document.webkitExitFullscreen).call(document);}
  else{const f=fsRoot.requestFullscreen||fsRoot.webkitRequestFullscreen;if(f)f.call(fsRoot);}
});
function fsUpdate(){fsBtn.textContent=fsOn()?'Exit fullscreen':'Fullscreen';}
if(document.addEventListener){document.addEventListener('fullscreenchange',fsUpdate);document.addEventListener('webkitfullscreenchange',fsUpdate);}
if(!(docEl&&(docEl.requestFullscreen||docEl.webkitRequestFullscreen)))fsBtn.style.display='none';

/* ---------- level generation (seeded, so every level is the same each time) ---------- */
function buildLevel(n){
  const rng=mulberry32(n*7919+13);
  worldW=1500+n*110;platforms=[];obstacles=[];items=[];collected=[];allDone=false;note=null;
  activeBins=BINS.filter(b=>b.level<=n);
  if(n<3){platforms.push({x:0,y:GROUND,w:worldW,h:60,ground:true});}
  else{
    const pitMax=Math.min(120,40+n*8);let x=0;
    while(true){
      let len=x===0?420:300+rng()*250;
      if(x+len>worldW-520){platforms.push({x:x,y:GROUND,w:worldW-x,h:60,ground:true});break;}  /* last stretch always reaches the factory */
      platforms.push({x:x,y:GROUND,w:len,h:60,ground:true});x+=len+50+rng()*(pitMax-50);
    }
  }
  const maxGap=40+n*7,riseMax=50+n*4,minY=330-n*17,limit=worldW-270;
  let px=220,py=GROUND-80;
  while(px<worldW-250){
    const w=Math.max(90,170-n*6+rng()*60);
    platforms.push({x:px,y:py,w:w,h:16,ground:false});
    px+=w+30+rng()*(maxGap-30);
    py=clamp(py+(rng()*2-1)*riseMax,minY,GROUND-70);
  }
  const spots=[];
  platforms.forEach(p=>{
    if(!p.ground){if(p.x+p.w/2<limit)spots.push({x:p.x+p.w/2,y:p.y-24});}
    else for(let sx=p.x+60;sx<p.x+p.w-40;sx+=200)if(sx>260&&sx<limit)spots.push({x:sx,y:GROUND-24});
  });
  const count=7+n,pool=ITEMS.filter(i=>i.level<=n);
  for(let sx=300;spots.length<count;sx+=140)spots.push({x:sx,y:GROUND-24});
  spots.sort((a,b)=>a.x-b.x);
  for(let i=0;i<count;i++){
    const s=spots[Math.min(spots.length-1,Math.floor((i+rng()*0.6)*spots.length/count))];
    items.push({x:s.x,y:s.y,def:pool[i%pool.length],got:false});
  }
  const kinds=n<4?[0]:(n<7?[0,1]:[0,1,2]),nObs=Math.floor((n+1)/2),homes=platforms.filter(p=>p.x>350&&p.w>=(p.ground?250:140));
  for(let i=0;i<nObs&&homes.length;i++){
    const p=homes.splice(Math.floor(rng()*homes.length),1)[0],mx=Math.min(p.x+p.w-42,limit-40);
    if(mx<=p.x+8)continue;
    obstacles.push({x:p.x+20,y:p.y-28,w:34,h:28,min:p.x+8,max:mx,dir:1,speed:50+n*10,kind:kinds[i%kinds.length]});
  }
  P={x:60,y:GROUND-40,w:28,h:40,vx:0,vy:0,face:1,onGround:false,coyote:0,buffer:0,inv:0,safe:{x:60,y:GROUND-40}};
  time=levelTime(n);floaters=[];feedback=null;
}
const factory=()=>({x:worldW-210,y:GROUND-150,w:170,h:150,doorX:worldW-150,doorW:52});
function startLevel(n){level=n;scoreAtStart=score;buildLevel(n);state='intro';}
function say(text,x,y,color){floaters.push({text:text,x:x,y:y,t:1.2,color:color||'#fff'});}

/* ---------- input: keyboard ---------- */
const JUMPS=['KeyW','ArrowUp','Space'];
window.addEventListener('keydown',e=>{
  if(['Space','ArrowUp','ArrowDown','ArrowLeft','ArrowRight'].includes(e.code))e.preventDefault();
  if(!keys[e.code]&&JUMPS.includes(e.code)&&P)P.buffer=0.12;
  keys[e.code]=true;
  if(e.code==='Enter'||e.code==='Space')advance();
  if(state==='sort'){const m=/^(Digit|Numpad)(\d)$/.exec(e.code);if(m){const i=parseInt(m[2],10)-1;if(i>=0&&i<activeBins.length)place(i);}}
});
window.addEventListener('keyup',e=>{keys[e.code]=false;});
window.addEventListener('blur',()=>{for(const k in keys)keys[k]=false;});
function advance(){
  if(state==='menu'){score=0;startLevel(1);}
  else if(state==='intro'){state='play';}
  else if(state==='levelDone'){if(level>=TOTAL){state='victory';for(let i=0;i<120;i++)confetti.push({x:Math.random()*W,y:-Math.random()*H,v:60+Math.random()*120,c:['#2D6A4F','#D8F3DC','#e0a526','#3b82c4'][i%4]});}else startLevel(level+1);}
  else if(state==='timeup'){score=scoreAtStart;startLevel(level);}
  else if(state==='victory'){score=0;startLevel(1);}
}

/* ---------- input: mouse, touch and pen (pointer events) ---------- */
function mouse(e){const r=cv.getBoundingClientRect();return{x:(e.clientX-r.left)*W/r.width,y:(e.clientY-r.top)*H/r.height};}
const BTN={left:{x:80,y:490,r:44},right:{x:182,y:490,r:44},jump:{x:880,y:486,r:52}};
function zoneAt(m){for(const k in BTN){const b=BTN[k];if(Math.hypot(m.x-b.x,m.y-b.y)<=b.r+14)return k;}return null;}
function applyHolds(){touch.left=touch.right=touch.jump=false;for(const id in holds)touch[holds[id]]=true;}
function binSlot(m){const n=activeBins.length;for(let i=0;i<n;i++){const b=binRect(i,n);if(m.x>=b.x&&m.x<=b.x+b.w&&m.y>=b.y-40&&m.y<=b.y+b.h)return i;}return -1;}
function binRect(i,n){const gap=14,bw=(W-60-(n-1)*gap)/n;return{x:30+i*(bw+gap),y:380,w:bw,h:130};}
cv.addEventListener('pointerdown',e=>{
  cv.focus();const m=mouse(e);if(e.pointerType&&e.pointerType!=='mouse')touchMode=true;
  if(state==='play'){
    const z=zoneAt(m);
    if(z&&touchMode){holds[e.pointerId]=z;applyHolds();if(z==='jump'&&P)P.buffer=0.12;try{cv.setPointerCapture(e.pointerId);}catch(_){}}
    return;
  }
  if(state==='sort'&&queue.length){
    if(Math.hypot(m.x-itemPos.x,m.y-itemPos.y)<85){drag={dx:itemPos.x-m.x,dy:itemPos.y-m.y,moved:false};try{cv.setPointerCapture(e.pointerId);}catch(_){}return;}
    const b=binSlot(m);if(b>=0)place(b);return;
  }
  if(state!=='entering'&&state!=='sort')advance();
});
cv.addEventListener('pointermove',e=>{
  const m=mouse(e);
  if(holds[e.pointerId]!==undefined){const z=zoneAt(m);if(z)holds[e.pointerId]=z;else delete holds[e.pointerId];applyHolds();return;}
  if(!drag)return;itemPos.x=m.x+drag.dx;itemPos.y=m.y+drag.dy;drag.moved=true;
});
function release(e){
  if(holds[e.pointerId]!==undefined){delete holds[e.pointerId];applyHolds();return;}
  if(!drag)return;const m=mouse(e),moved=drag.moved;drag=null;
  const b=binSlot({x:itemPos.x,y:itemPos.y+60});itemPos={x:480,y:175};
  if(moved&&b>=0)place(b);
}
cv.addEventListener('pointerup',release);cv.addEventListener('pointercancel',release);

/* ---------- the sorting hall: bins are shuffled again after every item ---------- */
function shuffleSlots(){
  const n=activeBins.length,prev=slotBin.join(',');let tries=0;
  do{slotBin=activeBins.map((_,i)=>i);for(let i=n-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[slotBin[i],slotBin[j]]=[slotBin[j],slotBin[i]];}tries++;}
  while(n>1&&slotBin.join(',')===prev&&tries<20);
}
function enterSort(){state='sort';queue=collected.slice();itemPos={x:480,y:175};feedback=null;slotBin=[];shuffleSlots();}
function place(slot){
  if(state!=='sort'||!queue.length||slot<0||slot>=slotBin.length)return;
  const it=queue[0],chosen=slotBin[slot],right=activeBins.findIndex(b=>b.id===it.def.bin);
  if(chosen===right){
    queue.shift();score+=20;
    feedback={ok:true,t:3,text:'Correct! '+it.def.name+' goes in '+activeBins[right].label+'. '+it.def.reason+' The bins just shuffled!'};
    if(!queue.length){bonus=Math.round(Math.max(0,time))*2;score+=bonus;state='levelDone';}else shuffleSlots();
  }else{
    shake={i:slot,t:0.5};
    feedback={ok:false,t:5,text:'Not quite! '+it.def.name+' does not go in '+activeBins[chosen].label+'. It goes in '+activeBins[right].label+'. '+it.def.reason+' Try again!'};
  }
}

/* ---------- update ---------- */
function update(dt){
  tAnim+=dt;
  floaters.forEach(f=>{f.t-=dt;f.y-=30*dt;});floaters=floaters.filter(f=>f.t>0);
  if(feedback){feedback.t-=dt;if(feedback.t<0)feedback.t=0;}
  if(note){note.t-=dt;if(note.t<=0)note=null;}
  if(shake.t>0)shake.t-=dt;
  if(state==='victory')confetti.forEach(c=>{c.y+=c.v*dt;if(c.y>H)c.y=-10;});
  if(state==='entering'){fade-=dt;if(fade<=0)enterSort();return;}
  if(state!=='play')return;
  const l=keys.KeyA||keys.ArrowLeft||touch.left,r=keys.KeyD||keys.ArrowRight||touch.right,ax=(r?1:0)-(l?1:0);
  P.vx=ax*SPEED;if(ax)P.face=ax;
  P.coyote-=dt;P.buffer-=dt;P.inv-=dt;
  const jh=keys.KeyW||keys.ArrowUp||keys.Space||touch.jump;
  if(P.buffer>0&&P.coyote>0){P.vy=-JUMP;P.buffer=0;P.coyote=0;P.onGround=false;}
  if(!jh&&P.vy<-260)P.vy=-260;
  P.vy=Math.min(P.vy+GRAV*dt,1100);
  const prevBottom=P.y+P.h;
  P.x=clamp(P.x+P.vx*dt,0,worldW-P.w);P.y+=P.vy*dt;P.onGround=false;
  if(P.vy>=0){
    for(const p of platforms){
      if(P.x+P.w>p.x+2&&P.x<p.x+p.w-2&&prevBottom<=p.y+2&&P.y+P.h>=p.y){
        P.y=p.y-P.h;P.vy=0;P.onGround=true;
        if(p.w>80&&P.x>p.x+20&&P.x+P.w<p.x+p.w-20)P.safe={x:P.x,y:P.y};
        break;
      }
    }
  }
  if(P.onGround)P.coyote=0.1;
  if(P.y>H+80){time-=3;say('-3s (pit!)',P.x,GROUND-90,'#fecaca');P.x=P.safe.x;P.y=P.safe.y;P.vy=0;}
  obstacles.forEach(o=>{
    o.x+=o.dir*o.speed*dt;if(o.x<o.min){o.x=o.min;o.dir=1;}if(o.x>o.max){o.x=o.max;o.dir=-1;}
    if(P.inv<=0&&P.x<o.x+o.w&&P.x+P.w>o.x&&P.y<o.y+o.h&&P.y+P.h>o.y){time-=4;P.inv=1.5;P.vy=-300;say('-4s (ouch!)',P.x,P.y-10,'#fecaca');}
  });
  items.forEach(it=>{
    if(!it.got&&Math.hypot(it.x-(P.x+P.w/2),it.y-(P.y+P.h/2))<30){it.got=true;collected.push(it);score+=10;say('+10 '+it.def.name,it.x,it.y-20,'#fff7a8');}
  });
  if(!allDone&&collected.length===items.length){allDone=true;note={t:5,text:'All items collected! Run to the Recycling Factory on the right!'};}
  time-=dt;
  if(time<=0){time=0;state='timeup';return;}
  const f=factory();
  if(allDone&&P.onGround&&P.x+P.w>f.doorX&&P.x<f.doorX+f.doorW){state='entering';fade=0.8;}
  camX=clamp(P.x+P.w/2-W*0.4,0,worldW-W);
}

/* ---------- drawing: items ---------- */
function drawItem(id,x,y,s){
  ctx.save();ctx.translate(x,y);ctx.scale(s,s);ctx.lineWidth=1.5;ctx.strokeStyle='rgba(0,0,0,.35)';
  const f=(c)=>{ctx.fillStyle=c;};
  if(id==='newspaper'){ctx.rotate(-0.15);f('#f1f1ea');rr(-16,-14,32,28,2);ctx.fill();ctx.stroke();f('#333');ctx.fillRect(-12,-10,24,5);f('#777');for(let i=0;i<3;i++)ctx.fillRect(-12,-2+i*5,i===2?12:24,2);}
  else if(id==='plastic_bottle'){f('rgba(120,190,235,.9)');rr(-8,-8,16,26,4);ctx.fill();ctx.stroke();ctx.fillRect(-4,-15,8,8);f('#2563eb');ctx.fillRect(-5,-20,10,5);f('rgba(255,255,255,.8)');ctx.fillRect(-8,2,16,6);}
  else if(id==='glass_jar'){f('rgba(190,235,215,.75)');rr(-12,-8,24,24,5);ctx.fill();ctx.stroke();f('#d4a017');ctx.fillRect(-13,-14,26,6);f('rgba(255,255,255,.7)');ctx.fillRect(-8,-3,3,14);}
  else if(id==='banana_peel'){ctx.rotate(0.2);f('#f6d533');ctx.beginPath();ctx.moveTo(-16,6);ctx.quadraticCurveTo(0,-22,16,4);ctx.quadraticCurveTo(0,-6,-16,6);ctx.fill();ctx.stroke();f('#6b4a1a');ctx.fillRect(13,0,5,5);ctx.beginPath();ctx.moveTo(-4,4);ctx.quadraticCurveTo(0,16,10,14);ctx.quadraticCurveTo(2,10,-4,4);f('#f1c40f');ctx.fill();}
  else if(id==='cardboard_box'){f('#c8914f');ctx.fillRect(-16,-12,32,26);ctx.strokeRect(-16,-12,32,26);f('#e3b779');ctx.fillRect(-4,-12,8,26);f('#a9763a');ctx.fillRect(-16,-12,32,4);}
  else if(id==='plastic_cup'){f('#ef6f6c');ctx.beginPath();ctx.moveTo(-11,-14);ctx.lineTo(11,-14);ctx.lineTo(8,16);ctx.lineTo(-8,16);ctx.closePath();ctx.fill();ctx.stroke();f('#fff');ctx.fillRect(-12,-16,24,4);}
  else if(id==='glass_bottle'){f('#2f9e6f');rr(-8,-2,16,22,4);ctx.fill();ctx.stroke();ctx.fillRect(-3,-16,6,16);f('#1f6b4a');ctx.fillRect(-4,-20,8,5);f('rgba(255,255,255,.55)');ctx.fillRect(-5,2,2,12);}
  else if(id==='apple_core'){f('#d64545');ctx.beginPath();ctx.ellipse(0,-9,10,6,0,0,Math.PI*2);ctx.fill();ctx.beginPath();ctx.ellipse(0,10,10,6,0,0,Math.PI*2);ctx.fill();f('#f7f1d8');ctx.fillRect(-5,-9,10,20);ctx.strokeRect(-5,-9,10,20);f('#5a3a1a');ctx.fillRect(-1,-4,2,3);ctx.fillRect(-1,3,2,3);ctx.fillRect(-1,-18,2,8);}
  else if(id==='aluminum_can'){f('#cfd6dd');rr(-9,-14,18,28,3);ctx.fill();ctx.stroke();f('#e11d48');ctx.fillRect(-9,-3,18,9);f('rgba(255,255,255,.7)');ctx.fillRect(-6,-12,2,24);f('#9aa5b1');ctx.beginPath();ctx.ellipse(0,-14,9,3,0,0,7);ctx.fill();ctx.stroke();f('#6b7a8c');ctx.fillRect(-2,-16,4,2);}
  else if(id==='tin_can'){f('#b8bec6');rr(-10,-12,20,26,2);ctx.fill();ctx.stroke();ctx.strokeStyle='rgba(0,0,0,.25)';ctx.beginPath();ctx.moveTo(-10,-8);ctx.lineTo(10,-8);ctx.moveTo(-10,10);ctx.lineTo(10,10);ctx.stroke();f('#d9482b');ctx.fillRect(-10,-5,20,12);f('#fff3d6');ctx.beginPath();ctx.arc(0,1,3.5,0,7);ctx.fill();}
  else if(id==='aa_battery'){f('#2b2d31');rr(-8,-10,16,26,3);ctx.fill();ctx.stroke();f('#d4a017');ctx.fillRect(-4,-15,8,5);f('#c9822b');ctx.fillRect(-8,-10,16,9);f('#fff');ctx.fillRect(-1,3,2,8);ctx.fillRect(-4,6,8,2);}
  else if(id==='rechargeable_battery'){f('#2563eb');rr(-8,-10,16,26,3);ctx.fill();ctx.stroke();f('#d4a017');ctx.fillRect(-4,-15,8,5);f('#74c69d');ctx.fillRect(-8,-2,16,5);f('#fff');ctx.beginPath();ctx.moveTo(2,5);ctx.lineTo(-3,10);ctx.lineTo(0,10);ctx.lineTo(-2,15);ctx.lineTo(4,9);ctx.lineTo(1,9);ctx.closePath();ctx.fill();}
  ctx.restore();
}

/* ---------- drawing: the creatures (smog puff, oil slick, plastic-bag ghost) ---------- */
function drawMonster(o,t){
  const x=o.x-camX+o.w/2,y=o.y+o.h/2;ctx.save();ctx.translate(x,y);
  const eye=(ex,ey,r)=>{ctx.fillStyle='#fff';ctx.beginPath();ctx.arc(ex,ey,r,0,7);ctx.fill();ctx.fillStyle='#16202b';ctx.beginPath();ctx.arc(ex+o.dir*r*0.35,ey+1,r*0.5,0,7);ctx.fill();ctx.fillStyle='#fff';ctx.beginPath();ctx.arc(ex+o.dir*r*0.35+1,ey-0.5,r*0.18,0,7);ctx.fill();};
  if(o.kind===0){ /* Smoglet: a puffy smog cloud with a tiny chimney */
    ctx.fillStyle='rgba(150,220,90,.35)';ctx.beginPath();ctx.ellipse(0,14,22,5,0,0,7);ctx.fill();
    const g=ctx.createRadialGradient(-4,-6,2,0,0,22);g.addColorStop(0,'#9aa0b8');g.addColorStop(1,'#565b73');ctx.fillStyle=g;
    ctx.beginPath();ctx.arc(-11,3+Math.sin(t*4)*1.2,11,0,7);ctx.arc(11,3+Math.cos(t*4)*1.2,11,0,7);ctx.arc(0,-3,14,0,7);ctx.arc(0,8,12,0,7);ctx.fill();
    ctx.fillStyle='#8c4a3a';ctx.fillRect(-3,-22,7,10);ctx.fillStyle='#b8664f';ctx.fillRect(-4,-23,9,3);
    for(let i=0;i<3;i++){const k=(t*1.2+i/3)%1;ctx.globalAlpha=1-k;ctx.fillStyle='#c9ced9';ctx.beginPath();ctx.arc(1+Math.sin(k*6+i)*4,-24-k*22,3+k*5,0,7);ctx.fill();}ctx.globalAlpha=1;
    eye(-5,-1,4.6);eye(6,-1,4.6);
    ctx.strokeStyle='#2a2e3f';ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(-10,-7);ctx.lineTo(-2,-5);ctx.moveTo(11,-7);ctx.lineTo(3,-5);ctx.stroke();
    ctx.beginPath();ctx.moveTo(-5,9);for(let i=0;i<5;i++)ctx.lineTo(-5+i*2.6+1.3,i%2?9:12);ctx.stroke();
  }else if(o.kind===1){ /* Oil slick: a glossy rainbow blob that squashes and stretches */
    const sq=1+Math.sin(t*5)*0.08;ctx.scale(1/sq,sq);ctx.translate(0,(1-sq)*10);
    ctx.fillStyle='#14161d';ctx.beginPath();ctx.moveTo(-19,13);ctx.quadraticCurveTo(-22,-8,-4,-12);ctx.quadraticCurveTo(14,-16,20,2);ctx.quadraticCurveTo(24,13,14,14);ctx.lineTo(10,19+Math.sin(t*3)*2);ctx.lineTo(6,14);ctx.lineTo(-6,14);ctx.lineTo(-10,20+Math.cos(t*3)*2);ctx.lineTo(-13,14);ctx.closePath();ctx.fill();
    for(let i=0;i<5;i++){ctx.strokeStyle='hsla('+((i*70+t*60)%360)+',85%,62%,.55)';ctx.lineWidth=2.2;ctx.beginPath();ctx.arc(-2+i*2,-2,6+i*3,Math.PI*1.1,Math.PI*1.8);ctx.stroke();}
    ctx.fillStyle='rgba(255,255,255,.75)';ctx.beginPath();ctx.ellipse(-8,-6,5,2.4,-0.5,0,7);ctx.fill();
    ctx.strokeStyle='rgba(180,220,255,.7)';ctx.lineWidth=1.2;const b=(t*0.8)%1;ctx.beginPath();ctx.arc(14,-10-b*12,3+b*2,0,7);ctx.stroke();
    eye(-6,0,4.4);eye(6,0,4.4);
  }else{ /* Bag ghost: a floating plastic bag */
    const fy=Math.sin(t*3)*4;ctx.translate(0,fy-2);
    ctx.strokeStyle='rgba(120,170,210,.9)';ctx.lineWidth=2.4;ctx.beginPath();ctx.arc(-7,-14,6,Math.PI,0);ctx.stroke();ctx.beginPath();ctx.arc(7,-14,6,Math.PI,0);ctx.stroke();
    ctx.fillStyle='rgba(235,246,255,.88)';ctx.strokeStyle='rgba(120,170,210,.9)';ctx.lineWidth=1.6;
    ctx.beginPath();ctx.moveTo(-14,-14);ctx.lineTo(14,-14);ctx.lineTo(18,8);for(let i=0;i<6;i++)ctx.lineTo(18-i*6-3,14+(i%2?4:-1)+Math.sin(t*6+i)*1.5);ctx.lineTo(-18,8);ctx.closePath();ctx.fill();ctx.stroke();
    ctx.strokeStyle='rgba(120,170,210,.55)';ctx.beginPath();ctx.moveTo(-8,-10);ctx.quadraticCurveTo(-12,0,-9,8);ctx.stroke();
    eye(-5,-3,4);eye(5,-3,4);ctx.strokeStyle='#355d82';ctx.lineWidth=1.6;ctx.beginPath();ctx.arc(0,6,3,0.15*Math.PI,0.85*Math.PI);ctx.stroke();
  }
  ctx.restore();
}

/* ---------- drawing: world, factory, HUD ---------- */
function drawBg(){
  const g=ctx.createLinearGradient(0,0,0,H);g.addColorStop(0,'#bfe6f5');g.addColorStop(1,'#e8f7ea');ctx.fillStyle=g;ctx.fillRect(0,0,W,H);
  ctx.fillStyle='#fff6bf';ctx.beginPath();ctx.arc(820,80,38,0,7);ctx.fill();
  ctx.fillStyle='rgba(255,255,255,.85)';for(let i=0;i<7;i++){const cx=((i*260-camX*0.3)%1700+1700)%1700-150;ctx.beginPath();ctx.arc(cx,90+(i%3)*40,26,0,7);ctx.arc(cx+30,84+(i%3)*40,32,0,7);ctx.arc(cx+62,92+(i%3)*40,24,0,7);ctx.fill();}
  ctx.fillStyle='#a8d5ba';ctx.beginPath();ctx.moveTo(0,H);for(let x=0;x<=W;x+=40){ctx.lineTo(x,330+Math.sin((x+camX*0.2)/90)*30);}ctx.lineTo(W,H);ctx.fill();
  ctx.fillStyle='#7fbf9a';ctx.beginPath();ctx.moveTo(0,H);for(let x=0;x<=W;x+=40){ctx.lineTo(x,400+Math.sin((x+camX*0.5)/60+2)*22);}ctx.lineTo(W,H);ctx.fill();
}
function recycleSign(cx,cy,r,col){
  ctx.save();ctx.translate(cx,cy);ctx.rotate(tAnim*0.6);ctx.fillStyle=col;
  for(let i=0;i<3;i++){ctx.save();ctx.rotate(i*Math.PI*2/3);ctx.beginPath();ctx.moveTo(-r*0.45,-r);ctx.lineTo(r*0.3,-r);ctx.lineTo(r*0.3,-r*1.25);ctx.lineTo(r*0.85,-r*0.8);ctx.lineTo(r*0.3,-r*0.4);ctx.lineTo(r*0.3,-r*0.62);ctx.lineTo(-r*0.45,-r*0.62);ctx.closePath();ctx.fill();ctx.restore();}
  ctx.restore();
}
function drawFactory(){
  const f=factory(),x=f.x-camX,y=f.y;if(x>W+40||x+f.w<-40)return;
  for(let i=0;i<2;i++){const cx=x+30+i*34;ctx.fillStyle='#6b7a8c';ctx.fillRect(cx-9,y-34,18,40);ctx.fillStyle='#4b5868';ctx.fillRect(cx-11,y-38,22,7);
    for(let k=0;k<4;k++){const q=(tAnim*0.5+k/4+i*0.3)%1;ctx.globalAlpha=0.8*(1-q);ctx.fillStyle='#fff';ctx.beginPath();ctx.arc(cx+Math.sin(q*5+i)*7,y-44-q*50,6+q*10,0,7);ctx.fill();}ctx.globalAlpha=1;}
  ctx.fillStyle='#3d5a4c';ctx.fillRect(x,y+4,f.w,f.h-4);ctx.fillStyle='#52796f';ctx.fillRect(x+6,y+10,f.w-12,f.h-14);
  ctx.fillStyle='#2f4a3d';ctx.beginPath();ctx.moveTo(x-8,y+6);ctx.lineTo(x+f.w/2,y-18);ctx.lineTo(x+f.w+8,y+6);ctx.closePath();ctx.fill();
  ctx.fillStyle='#D8F3DC';rr(x+18,y+16,f.w-36,26,6);ctx.fill();recycleSign(x+34,y+29,8,'#2D6A4F');ctx.fillStyle='#1B4332';ctx.font='bold 14px Segoe UI,Arial';ctx.textAlign='left';ctx.fillText('RECYCLING',x+50,y+34);
  ctx.fillStyle='#cfe8d5';for(let i=0;i<2;i++){rr(x+14+i*118,y+56,34,26,3);ctx.fill();}
  const dx=f.doorX-camX,open=allDone;ctx.fillStyle=open?'#74c69d':'#6b7280';rr(dx,GROUND-72,f.doorW,72,4);ctx.fill();
  ctx.fillStyle=open?'rgba(255,255,200,.55)':'rgba(0,0,0,.25)';ctx.fillRect(dx+f.doorW/2-1,GROUND-72,2,72);
  ctx.font='bold 12px Segoe UI,Arial';ctx.textAlign='center';ctx.fillStyle=open?'#1B4332':'#e5e7eb';ctx.fillText(open?'ENTER':'LOCKED',dx+f.doorW/2,GROUND-80);ctx.textAlign='left';
  if(open){ctx.fillStyle='#fff7a8';ctx.beginPath();const b=Math.sin(tAnim*6)*4;ctx.moveTo(dx+f.doorW/2,GROUND-104+b);ctx.lineTo(dx+f.doorW/2-9,GROUND-118+b);ctx.lineTo(dx+f.doorW/2+9,GROUND-118+b);ctx.closePath();ctx.fill();}
}
function drawWorld(){
  ctx.fillStyle='#16352a';ctx.fillRect(0,GROUND+10,W,H);
  platforms.forEach(p=>{
    const x=p.x-camX;if(x>W||x+p.w<0)return;
    if(p.ground){ctx.fillStyle='#7a5230';ctx.fillRect(x,p.y,p.w,p.h);ctx.fillStyle='#5f3f23';for(let dx=10;dx<p.w;dx+=34)ctx.fillRect(x+dx,p.y+22+(dx%3)*9,8,5);ctx.fillStyle='#3f9b61';ctx.fillRect(x,p.y,p.w,10);}
    else{ctx.fillStyle='#8a5c34';rr(x,p.y,p.w,p.h,5);ctx.fill();ctx.fillStyle='#3f9b61';rr(x,p.y-3,p.w,9,4);ctx.fill();}
  });
  drawFactory();
  items.forEach((it,i)=>{if(it.got)return;const bob=Math.sin(tAnim*3+i)*3;ctx.fillStyle='rgba(255,255,255,.55)';ctx.beginPath();ctx.arc(it.x-camX,it.y+bob,24,0,7);ctx.fill();drawItem(it.def.id,it.x-camX,it.y+bob,1);});
  obstacles.forEach(o=>drawMonster(o,tAnim));
  const px=P.x-camX;
  if(P.inv<=0||Math.floor(tAnim*12)%2===0){
    const step=P.onGround&&P.vx?Math.sin(tAnim*16)*6:0;
    ctx.fillStyle='#24456b';ctx.fillRect(px+5,P.y+28,7,12+step*0.3);ctx.fillRect(px+16,P.y+28,7,12-step*0.3);
    ctx.fillStyle='#2D6A4F';rr(px+2,P.y+12,24,19,5);ctx.fill();
    ctx.fillStyle='#f0c9a0';ctx.beginPath();ctx.arc(px+14,P.y+8,9,0,7);ctx.fill();
    ctx.fillStyle='#1B4332';ctx.beginPath();ctx.arc(px+14,P.y+5,9,Math.PI,0);ctx.fill();ctx.fillStyle='#74c69d';ctx.beginPath();ctx.ellipse(px+14+P.face*8,P.y-2,6,3,P.face*0.6,0,7);ctx.fill();
    ctx.fillStyle='#222';ctx.fillRect(px+14+P.face*4-1,P.y+7,3,3);
  }
  floaters.forEach(f=>{ctx.globalAlpha=Math.min(1,f.t);ctx.font='bold 15px Segoe UI,Arial';ctx.fillStyle=f.color;ctx.strokeStyle='rgba(0,0,0,.5)';ctx.lineWidth=3;ctx.strokeText(f.text,f.x-camX,f.y);ctx.fillText(f.text,f.x-camX,f.y);ctx.globalAlpha=1;});
}
function hud(){
  ctx.fillStyle='rgba(15,42,29,.78)';rr(10,10,940,40,10);ctx.fill();ctx.font='bold 17px Segoe UI,Arial';ctx.fillStyle='#D8F3DC';
  ctx.fillText('Level '+level+' / '+TOTAL,26,36);ctx.fillText('Items '+collected.length+' / '+items.length,200,36);
  ctx.fillStyle=time<=10?'#fca5a5':'#D8F3DC';ctx.fillText('Time '+Math.ceil(time)+'s',390,36);ctx.fillStyle='#D8F3DC';ctx.fillText('Score '+score,560,36);
  if(allDone){ctx.fillStyle='#fff7a8';ctx.fillText('Go to the factory \u2192',730,36);}
  if(note){ctx.fillStyle='rgba(15,42,29,.85)';rr(150,58,660,34,10);ctx.fill();centerText(note.text,81,'bold 16px Segoe UI,Arial','#fff7a8',620);}
  if(allDone){const f=factory(),fx=f.doorX-camX;if(fx>W){const b=Math.sin(tAnim*6)*5;ctx.fillStyle='#fff7a8';ctx.beginPath();ctx.moveTo(W-14+b,GROUND-60);ctx.lineTo(W-40+b,GROUND-80);ctx.lineTo(W-40+b,GROUND-40);ctx.closePath();ctx.fill();}}
  if(touchMode&&state==='play'){
    ctx.globalAlpha=0.5;ctx.fillStyle='#0f2a1d';for(const k in BTN){const b=BTN[k];ctx.beginPath();ctx.arc(b.x,b.y,b.r,0,7);ctx.fill();}
    ctx.globalAlpha=0.9;ctx.fillStyle='#D8F3DC';ctx.font='bold 34px Segoe UI,Arial';ctx.textAlign='center';ctx.fillText('\u25C0',BTN.left.x,BTN.left.y+12);ctx.fillText('\u25B6',BTN.right.x,BTN.right.y+12);ctx.font='bold 20px Segoe UI,Arial';ctx.fillText('JUMP',BTN.jump.x,BTN.jump.y+7);ctx.textAlign='left';ctx.globalAlpha=1;
  }
}
function panel(title,lines,hint){
  ctx.fillStyle='rgba(15,42,29,.9)';rr(120,90,720,360,18);ctx.fill();
  ctx.font='bold 34px Segoe UI,Arial';ctx.fillStyle='#D8F3DC';ctx.textAlign='center';ctx.fillText(title,W/2,148);ctx.textAlign='left';
  let y=198;lines.forEach(t=>{y+=centerText(t,y,'19px Segoe UI,Arial','#F8FAF9',640)*26+6;});
  ctx.font='bold 17px Segoe UI,Arial';ctx.fillStyle='#74c69d';ctx.textAlign='center';ctx.fillText(hint,W/2,428);ctx.textAlign='left';
}

/* ---------- drawing: the recycling factory sorting hall ---------- */
function gear(cx,cy,r,rot,col){ctx.save();ctx.translate(cx,cy);ctx.rotate(rot);ctx.fillStyle=col;for(let i=0;i<10;i++){ctx.rotate(Math.PI/5);ctx.fillRect(-r*0.18,-r*1.18,r*0.36,r*0.4);}ctx.beginPath();ctx.arc(0,0,r,0,7);ctx.fill();ctx.fillStyle='#2f3b45';ctx.beginPath();ctx.arc(0,0,r*0.4,0,7);ctx.fill();ctx.restore();}
function drawBin(slot,n){
  const b=binRect(slot,n),bin=activeBins[slotBin[slot]],dx=shake.t>0&&shake.i===slot?Math.sin(shake.t*60)*6:0,x=b.x+dx;
  ctx.fillStyle='rgba(255,255,255,.18)';ctx.beginPath();ctx.moveTo(x+10,b.y-30);ctx.lineTo(x+b.w-10,b.y-30);ctx.lineTo(x+b.w-26,b.y);ctx.lineTo(x+26,b.y);ctx.closePath();ctx.fill();
  ctx.fillStyle=bin.color;rr(x,b.y+8,b.w,b.h-8,12);ctx.fill();ctx.fillStyle='rgba(0,0,0,.25)';rr(x-4,b.y-4,b.w+8,20,8);ctx.fill();
  ctx.fillStyle='rgba(255,255,255,.16)';for(let k=1;k<4;k++)ctx.fillRect(x+k*b.w/4,b.y+26,3,b.h-40);
  ctx.fillStyle='#fff';ctx.beginPath();ctx.arc(x+b.w/2,b.y+34,19,0,7);ctx.fill();ctx.fillStyle='#16202b';ctx.font='bold 24px Segoe UI,Arial';ctx.textAlign='center';ctx.fillText(String(slot+1),x+b.w/2,b.y+43);
  let fs=20;ctx.font='bold '+fs+'px Segoe UI,Arial';while(ctx.measureText(bin.label).width>b.w-14&&fs>11){fs--;ctx.font='bold '+fs+'px Segoe UI,Arial';}
  ctx.fillStyle='#fff';ctx.fillText(bin.label,x+b.w/2,b.y+100);ctx.textAlign='left';
}
function drawSort(){
  const g=ctx.createLinearGradient(0,0,0,H);g.addColorStop(0,'#26343f');g.addColorStop(1,'#34495b');ctx.fillStyle=g;ctx.fillRect(0,0,W,H);
  ctx.fillStyle='rgba(255,255,255,.05)';for(let i=0;i<8;i++)ctx.fillRect(i*128,0,4,H);
  gear(70,172,30,tAnim*0.8,'#5b6b7b');gear(122,198,18,-tAnim*1.2,'#6e8092');gear(890,115,38,-tAnim*0.7,'#5b6b7b');gear(835,150,22,tAnim*1.2,'#6e8092');
  ctx.fillStyle='#6b7a8c';ctx.fillRect(0,52,W,8);
  const bx=(tAnim*60)%40;ctx.fillStyle='#1f262d';ctx.fillRect(0,222,W,34);ctx.fillStyle='#3b4753';for(let x=-40+bx;x<W;x+=40)ctx.fillRect(x,226,20,26);ctx.fillStyle='#8b98a5';ctx.fillRect(0,220,W,4);ctx.fillRect(0,256,W,4);
  ctx.fillStyle='#D8F3DC';rr(300,12,360,38,10);ctx.fill();recycleSign(326,31,8,'#2D6A4F');ctx.fillStyle='#1B4332';ctx.font='bold 20px Segoe UI,Arial';ctx.textAlign='left';ctx.fillText('RECYCLING FACTORY',348,38);
  ctx.textAlign='center';ctx.fillStyle='#D8F3DC';ctx.font='15px Segoe UI,Arial';ctx.fillText('Level '+level+': '+queue.length+' item'+(queue.length===1?'':'s')+' left. Drag it to a bin, tap a bin or press its number. The bins shuffle after every item!',W/2,82);ctx.textAlign='left';
  if(queue.length){ctx.fillStyle='rgba(255,255,255,.12)';ctx.beginPath();ctx.arc(itemPos.x,itemPos.y,66,0,7);ctx.fill();drawItem(queue[0].def.id,itemPos.x,itemPos.y,2.3);
    ctx.textAlign='center';ctx.font='bold 22px Segoe UI,Arial';ctx.fillStyle='#fff';ctx.fillText(queue[0].def.name,W/2,292);ctx.textAlign='left';}
  queue.slice(1,9).forEach((q,i)=>drawItem(q.def.id,50+i*36,114,0.75));
  if(feedback&&feedback.t>0)centerText(feedback.text,314,'bold 15px Segoe UI,Arial',feedback.ok?'#b7f5c8':'#ffd0a8',880);
  const n=activeBins.length;for(let i=0;i<n;i++)drawBin(i,n);
}
function draw(){
  ctx.clearRect(0,0,W,H);
  if(state==='sort'){drawSort();return;}
  if(state==='levelDone'){drawSort();panel('Level '+level+' complete!',['All items sorted correctly. Time bonus: +'+bonus+'. Score: '+score+'.',level<TOTAL?(level===3?'Next up: Level 4 with a new Metal & Aluminum bin, higher platforms and new creatures.':(level===6?'Next up: Level 7 with a new Batteries bin and even more creatures.':'Next up: Level '+(level+1)+' with higher platforms, wider gaps and faster creatures.')):'You finished the final level!'],'Press Enter or tap to continue');return;}
  if(state==='victory'){
    const g=ctx.createLinearGradient(0,0,0,H);g.addColorStop(0,'#1B4332');g.addColorStop(1,'#2D6A4F');ctx.fillStyle=g;ctx.fillRect(0,0,W,H);
    confetti.forEach(c=>{ctx.fillStyle=c.c;ctx.fillRect(c.x,c.y,8,8);});
    ctx.textAlign='center';ctx.fillStyle='#D8F3DC';ctx.font='bold 38px Segoe UI,Arial';ctx.fillText('You cleared all 10 levels!',W/2,80);ctx.font='20px Segoe UI,Arial';ctx.fillText('Final score: '+score,W/2,116);ctx.textAlign='left';
    ctx.fillStyle='rgba(248,250,249,.96)';rr(110,150,740,250,18);ctx.fill();ctx.textAlign='center';ctx.fillStyle='#1B4332';ctx.font='bold 22px Segoe UI,Arial';ctx.fillText('Secret SDG 13 Climate Action Message',W/2,190);ctx.textAlign='left';
    centerText(CFG.secret,226,'19px Segoe UI,Arial','#1E293B',660);
    ctx.textAlign='center';ctx.fillStyle='#D8F3DC';ctx.font='bold 17px Segoe UI,Arial';ctx.fillText('Press Enter or tap to play again',W/2,450);ctx.textAlign='left';return;}
  if(!P){drawBg();panel('Eco-Runner',['Collect the waste scattered around each level, then carry it to the Recycling Factory and sort it into the right bins.','10 levels: higher platforms, wider gaps, new creatures, new bins and less time.'],'Press Enter or tap to start');return;}
  drawBg();drawWorld();hud();
  if(state==='intro'){
    const lines=['Collect all '+items.length+' waste items in '+levelTime(level)+' seconds, then enter the Recycling Factory at the end of the level.','Avoid the creatures (-4s) and the pits (-3s).'];
    const nb=BINS.filter(b=>b.level===level&&level>1);if(nb.length)lines.push('New bin unlocked: '+nb.map(b=>b.label).join(', ')+'. Bins shuffle after every item, so read the labels!');
    panel('Level '+level+' of '+TOTAL,lines,'Press Enter or tap to go');
  }
  if(state==='entering'){ctx.fillStyle='rgba(15,42,29,'+(1-Math.max(0,fade)/0.8)+')';ctx.fillRect(0,0,W,H);}
  if(state==='timeup')panel("Time's up!",['You collected '+collected.length+' of '+items.length+' items. Try the level again, you can do it!'],'Press Enter or tap to retry');
}
let last=performance.now();
function frame(now){const dt=Math.min(0.033,(now-last)/1000);last=now;update(dt);draw();requestAnimationFrame(frame);}
requestAnimationFrame(frame);
window.__eco={get state(){return state;},get level(){return level;},keys:keys,advance:advance,place:place,get P(){return P;},get items(){return items;},get queue(){return queue;},startLevel:startLevel,update:update,draw:draw,get platforms(){return platforms;},get obstacles(){return obstacles;},get time(){return time;},set time(v){time=v;},get slotBin(){return slotBin;},get bins(){return activeBins;},factory:factory,get allDone(){return allDone;},get worldW(){return worldW;}};
})();
</script></body></html>
"""


def get_trash_platformer_html() -> str:
    """Return the complete Eco-Runner HTML page."""
    config = {"items": WASTE_ITEMS, "bins": BINS, "levels": LEVELS, "secret": SECRET_MESSAGE}
    return _TEMPLATE.replace("__CONFIG__", json.dumps(config))
