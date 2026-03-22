// ── State ─────────────────────────────────────────────────────────────────
let darkMode=true, activePreset='ceo';
let ceoPortrait='ceo', ceoSprite='ceo', ceoPhoto=null;
const agentSprites={};
let calView='week', calDate=new Date(TODAY);
let curDay='Mon';
let boardFilterProj='', boardFilterSpec='';
let editingMissionId=null;

const META={dash:{s:'Command Center',p:'Dashboard'},team:{s:'Operate',p:'Team'},council:{s:'Operate',p:'Council'},cal:{s:'Operate',p:'Calendar'},board:{s:'Work',p:'Board'},pipeline:{s:'Work',p:'Pipeline'},approvals:{s:'Work',p:'Approvals'},miss:{s:'Work',p:'Missions'},conv:{s:'Work',p:'Conversations'},off:{s:'Observe',p:'Office'},acc:{s:'Observe',p:'Access'},req:{s:'Quality',p:'Requirements'},tc:{s:'Quality',p:'Test Cases'},app:{s:'Settings',p:'Appearance'}};

