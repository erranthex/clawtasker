// ── Util ───────────────────────────────────────────────────────────────────
function mk(tag,cls){const e=document.createElement(tag);if(cls)e.className=cls;return e;}
function txt(tag,cls,content){const e=mk(tag,cls);e.textContent=content;return e;}
function relTime(iso){
  if(!iso)return'never';
  const diff=Math.floor((Date.now()-new Date(iso))/1000);
  if(diff<60)return diff+'s ago';
  if(diff<3600)return Math.floor(diff/60)+'m ago';
  return Math.floor(diff/3600)+'h ago';
}

function mkPortrait(id,cls){
  const img=mk('img','card-portrait'+(cls?' '+cls:''));
  img.src=(id==='ceo'?(ceoPhoto||PT[ceoPortrait]||PT['ceo']):PT[id]||PT['ceo']);
  img.alt=id;img.style.imageRendering='pixelated';
  return img;
}
function mkFaceAv(id,sizeCls){
  const div=mk('div','face-av'+(sizeCls?' '+sizeCls:''));
  div.setAttribute('data-id',id);
  const img=mk('img','');
  // Use pre-cropped head image (rows 32-83, no neck gap)
  const headSrc=(id==='ceo'&&ceoPhoto)?ceoPhoto:(HEADS[id]||PT[id]||PT['ceo']);
  img.src=headSrc; img.alt=id;
  div.appendChild(img);
  return div;
}

function mkSprite(id,pose,cls){
  const d=mk('div','sprite'+(pose?' '+pose:'')+(cls?' '+cls:''));
  const spId=agentSprites[id]||id;
  const src=(id==='ceo'&&ceoPhoto)?null:SPR[spId]||SPR[id]||SPR['ceo'];
  if(id==='ceo'&&ceoPhoto){d.style.backgroundImage='url('+ceoPhoto+')';d.style.backgroundSize='cover';d.style.backgroundPosition='center top';}
  else d.style.backgroundImage='url('+src+')';
  return d;
}

