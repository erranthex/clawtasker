// ── Conversations ──────────────────────────────────────────────────────────
function renderThread(idx){
  const el=document.getElementById('CV_MSGS');el.innerHTML='';
  THREADS[idx].forEach(m=>{
    const div=mk('div','msg'+(m.s==='r'?' r':''));
    const av=mkFaceAv(m.id,'');
    const bubble=mk('div','mb');
    const name=(m.id==='ceo')?(document.getElementById('CEO_NAME').value||'CEO'):(m.id.charAt(0).toUpperCase()+m.id.slice(1));
    bubble.innerHTML=`<div class="ms">${name}</div><div class="mt">${m.t}</div>`;
    div.appendChild(av);div.appendChild(bubble);el.appendChild(div);
  });
  el.scrollTop=el.scrollHeight;
}
function switchT(i,el){document.querySelectorAll('.ti').forEach(t=>t.classList.remove('on'));el.classList.add('on');renderThread(i);}
function sendMsg(){
  const inp=document.getElementById('CV_INP');const text=inp.value.trim();if(!text)return;
  const msgs=document.getElementById('CV_MSGS');
  const div=mk('div','msg r');
  div.appendChild(mkFaceAv('ceo',''));
  const bubble=mk('div','mb');
  bubble.innerHTML=`<div class="ms">${document.getElementById('CEO_NAME').value||'CEO'}</div><div class="mt">${text}</div>`;
  div.appendChild(bubble);msgs.appendChild(div);msgs.scrollTop=msgs.scrollHeight;inp.value='';
}

