// ── Nav ────────────────────────────────────────────────────────────────────
function goV(id,btn){
  document.querySelectorAll('.vw').forEach(v=>v.classList.remove('on'));
  document.getElementById('V_'+id).classList.add('on');
  document.querySelectorAll('.nv').forEach(b=>b.classList.remove('on'));
  btn.classList.add('on');
  const m=META[id]||META.dash;
  document.getElementById('TB_S').textContent=m.s;
  document.getElementById('TB_P').textContent=m.p;
  // Lazy-init canvas office when office tab opens
  if(id==='off'&&typeof offInited!=='undefined'&&!offInited)
    setTimeout(initCanvasOffice,50);
  // Load version info when updates tab opens
  if(id==='updates'&&typeof buildUpdates==='function')
    buildUpdates();
}

