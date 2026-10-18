const $ = (selector, root=document) => root.querySelector(selector);
const node = (tag, className, text) => {
  const el = document.createElement(tag);
  if (className) el.className = className;
  if (text !== undefined) el.textContent = text;
  return el;
};
const state = { user:null, csrf:null, view:'discover', gigs:[], selectedGig:null, pending:'', query:{q:'',city:'',discipline:''} };
const authDialog = $('#auth-dialog');
const postDialog = $('#post-dialog');
const detailDialog = $('#detail-dialog');
const applyDialog = $('#apply-dialog');
const reportDialog = $('#report-dialog');
$('#year').textContent = new Date().getFullYear();

function detailMessage(payload, fallback) {
  if (typeof payload?.detail === 'string') return payload.detail;
  if (Array.isArray(payload?.detail)) return payload.detail.map(item => item.msg).filter(Boolean).join(' ');
  return fallback;
}
async function api(path, options={}) {
  const headers = new Headers(options.headers || {});
  if (options.body && !headers.has('Content-Type')) headers.set('Content-Type','application/json');
  if (state.csrf && !['GET','HEAD'].includes((options.method||'GET').toUpperCase())) headers.set('X-CSRF-Token',state.csrf);
  const response = await fetch(path,{...options,headers,credentials:'same-origin'});
  if (response.status === 204) return null;
  const data = await response.json().catch(()=>({}));
  if (!response.ok) throw new Error(detailMessage(data,`Request failed (${response.status}).`));
  return data;
}
function authMode(mode) {
  const login = mode === 'login';
  $('#auth-heading').replaceChildren(document.createTextNode(login?'Welcome ':'Join the '));
  $('#auth-heading').append(node('em','',login?'back.':'crew.'));
  $('#auth-intro').textContent = login?'Sign in to manage your gigs and applications.':'Create an account to post a gig or apply to an opportunity.';
  $('.auth-name').hidden = login; $('.auth-name input').required = !login;
  $('.auth-role').hidden = login; $('.auth-role select').required = !login;
  $('.auth-city').hidden = login; $('.auth-city input').required = !login;
  $('.auth-invite').hidden = login;
  const password = $('[name="password"]', $('#auth-form'));
  password.autocomplete = login?'current-password':'new-password';
  password.minLength = login?1:12;
  $('#auth-form button[type="submit"]').textContent = login?'Log in':'Create account';
  $('#switch-copy').textContent = login?'New to the pilot?':'Already a member?';
  $('#switch-auth').textContent = login?'Create an account':'Log in';
  $('#auth-form').dataset.mode = login?'login':'register';
  $('#auth-error').textContent = '';
}
function openAuth(mode='register', pending='') {
  state.pending = pending;
  authMode(mode);
  if (!authDialog.open) authDialog.showModal();
}
function updateAuthUI() {
  const signedIn = Boolean(state.user);
  $('#signed-user').textContent = signedIn ? `Hi, ${state.user.name}` : '';
  $('#login-button').hidden = signedIn;
  $('#join-button').hidden = signedIn;
  $('#logout-button').hidden = !signedIn;
  $('#reports-tab').hidden = !signedIn || !state.user.is_moderator;
}
function escapeDate(value) {
  const date = new Date(value);
  return Number.isNaN(date.valueOf())?'Recently posted':new Intl.DateTimeFormat(undefined,{dateStyle:'medium'}).format(date);
}
function renderGig(gig, mode) {
  const card = node('article','gig-card');
  const top = node('div');
  top.append(node('h3','',gig.title));
  const metadata = node('div','gig-meta');
  [gig.discipline,gig.location,gig.engagement,gig.poster_name].filter(Boolean).forEach(value=>metadata.append(node('span','',value)));
  top.append(metadata);
  const pay = node('div','gig-pay',gig.pay_info||'Pay details on request');
  card.append(top,pay);
  if (mode==='reports') {
    metadata.replaceChildren(...[gig.reason,gig.location,`Reported by ${gig.reporter_name}`,`Status: ${gig.status}`].map(value=>node('span','',value)));
    top.replaceChildren(node('h3','',`Report: ${gig.gig_title}`),metadata);
    card.append(node('p','gig-desc',gig.details||'No extra details provided.'));
    const footer=node('div','gig-footer');footer.append(node('small','',`Reported ${escapeDate(gig.created_at)}`));
    if(gig.status==='pending'){
      const actions=node('div','report-actions');
      [['reviewed','Mark reviewed',false],['reviewed','Review & close gig',true],['dismissed','Dismiss',false]].forEach(([status,label,closeGig])=>{const button=node('button','',label);button.type='button';button.addEventListener('click',()=>moderateReport(gig.id,status,closeGig));actions.append(button);});
      footer.append(actions);
    }
    card.append(footer);
  } else if (mode==='my-applications') {
    card.append(node('p','gig-desc',`Your application: ${gig.status}. ${gig.message}`));
    card.append(node('p','gig-desc',`Gig status: ${gig.gig_status}`));
  } else {
    const desc = node('p','gig-desc',gig.description);
    const footer = node('div','gig-footer');
    footer.append(node('small','',`${gig.application_count||0} applications · Posted ${escapeDate(gig.created_at)}`));
    const detail = node('button','',mode==='my-gigs'?'Manage gig':'View details');
    detail.type='button'; detail.addEventListener('click',()=>showGig(gig));
    footer.append(detail);
    card.append(desc,footer);
  }
  return card;
}
function renderItems(items, mode) {
  const list=$('#gig-list'), empty=$('#empty-state');
  list.replaceChildren(...items.map(item=>renderGig(item,mode)));
  list.hidden=items.length===0; empty.hidden=items.length!==0;
  $('#board-status').textContent=`${items.length} ${items.length===1?'result':'results'} · ${mode==='discover'?'open gigs':mode==='my-gigs'?'your gig posts':mode==='reports'?'moderation reports':'your applications'}`;
  $('#empty-state h3').textContent=mode==='reports'?'No pending reports.':'No gigs found yet.';
  $('#empty-state p').textContent=mode==='reports'?'The moderation queue is clear.':'Try a different search, or be the first to post an opportunity.';
  $('#empty-post').hidden=mode==='reports';
}
async function loadBoard() {
  const list=$('#gig-list'); list.setAttribute('aria-busy','true');
  $('#board-status').textContent='Loading gigs…';
  try {
    let result;
    if(state.view==='discover') {
      const params=new URLSearchParams(Object.fromEntries(Object.entries(state.query).filter(([,v])=>v)));
      result=await api(`/api/gigs?${params}`);
    } else if(state.view==='my-gigs') result=await api('/api/my/gigs');
    else if(state.view==='reports') result=await api('/api/moderation/reports');
    else result=await api('/api/my/applications');
    state.gigs=result.items||[];
    renderItems(state.gigs,state.view);
  } catch(error) {
    if(error.message.includes('sign in')) openAuth('login');
    $('#board-status').textContent=error.message;
    $('#empty-state').hidden=true; list.hidden=true;
  } finally {list.removeAttribute('aria-busy');}
}
async function refreshSession() {
  try { const data=await api('/api/auth/session'); state.user=data.user; state.csrf=data.csrf_token; }
  catch { state.user=null; state.csrf=null; }
  updateAuthUI();
  await loadBoard();
}
function showGig(gig) {
  state.selectedGig=gig;
  $('#detail-heading').textContent=gig.title;
  $('#detail-kicker').textContent=`${gig.discipline.toUpperCase()} · ${gig.status.toUpperCase()}`;
  const meta=$('#detail-meta');
  meta.replaceChildren(...[gig.location,gig.engagement,gig.pay_info||'Pay details on request',gig.poster_name?`Posted by ${gig.poster_name}`:''].filter(Boolean).map(item=>node('span','',item)));
  $('#detail-description').textContent=gig.description;
  const isOwner=state.user&&gig.owner_id===state.user.id;
  const isOpen=gig.status==='open';
  $('#apply-button').hidden=!isOpen||isOwner;
  $('#apply-button').textContent=state.user?'Apply to this gig':'Log in to apply';
  $('#report-button').hidden=!isOpen||isOwner;
  $('#view-applications-button').hidden=!isOwner;
  $('#view-applications-button').textContent=`View applications (${gig.application_count||0})`;
  $('#close-gig-button').hidden=!isOwner||!isOpen;
  $('#applications-list').hidden=true;
  detailDialog.showModal();
}
function setView(view) {
  if(view==='reports'&&(!state.user||!state.user.is_moderator)){openAuth('login');return;}
  state.view=view;
  document.querySelectorAll('.tab').forEach(tab=>{
    const active=tab.dataset.view===view;
    tab.classList.toggle('active',active);tab.setAttribute('aria-pressed',String(active));
  });
  $('#gig-search').hidden=view!=='discover';
  loadBoard();
}
$('#gig-search').addEventListener('submit',event=>{
  event.preventDefault();
  const form=new FormData(event.currentTarget);
  state.query={q:String(form.get('q')||'').trim(),city:String(form.get('city')||'').trim(),discipline:String(form.get('discipline')||'').trim()};
  loadBoard();
});
document.querySelectorAll('.tab').forEach(tab=>tab.addEventListener('click',()=>{
  if(!state.user&&tab.dataset.view!=='discover'){openAuth('login');return;}
  setView(tab.dataset.view);
}));
$('#join-button').addEventListener('click',()=>openAuth('register'));
$('#login-button').addEventListener('click',()=>openAuth('login'));
$('#switch-auth').addEventListener('click',()=>authMode($('#auth-form').dataset.mode==='login'?'register':'login'));
$('#auth-form').addEventListener('submit',async event=>{
  event.preventDefault(); const form=event.currentTarget; const values=Object.fromEntries(new FormData(form));
  const mode=form.dataset.mode; const error=$('#auth-error'); error.textContent='';
  const submit=$('button[type="submit"]',form);submit.disabled=true;
  try {
    const payload=mode==='register'?values:{email:values.email,password:values.password};
    const data=await api(`/api/auth/${mode}`,{method:'POST',body:JSON.stringify(payload)});
    state.user=data.user;state.csrf=data.csrf_token;updateAuthUI();authDialog.close();
    const pending=state.pending;state.pending='';
    if(pending==='post')postDialog.showModal();
    else if(pending==='apply'&&state.selectedGig){$('#apply-gig-title').textContent=state.selectedGig.title;applyDialog.showModal();}
    else if(pending==='report'&&state.selectedGig)reportDialog.showModal();
    else if(location.search.includes('signin=1'))history.replaceState({},'', '/app');
    await loadBoard();
  } catch(err){error.textContent=err.message;} finally{submit.disabled=false;}
});
$('#logout-button').addEventListener('click',async()=>{
  try{await api('/api/auth/logout',{method:'POST'});}catch(err){$('#board-status').textContent=err.message;}
  state.user=null;state.csrf=null;updateAuthUI();setView('discover');
});
function requestPost(){if(!state.user){openAuth('register','post');return;}postDialog.showModal();}
$('#post-gig-button').addEventListener('click',requestPost);
$('#empty-post').addEventListener('click',requestPost);
$('#post-form').addEventListener('submit',async event=>{
  event.preventDefault();const form=event.currentTarget;const error=$('#post-error');error.textContent='';
  const payload=Object.fromEntries(new FormData(form));const submit=$('button[type="submit"]',form);submit.disabled=true;
  try{const gig=await api('/api/gigs',{method:'POST',body:JSON.stringify(payload)});form.reset();postDialog.close();state.query={q:'',city:'',discipline:''};$('#gig-search').reset();setView('my-gigs');showGig(gig);$('#board-status').textContent='Gig posted. It is now visible on the open board.';}
  catch(err){error.textContent=err.message;}finally{submit.disabled=false;}
});
$('#apply-button').addEventListener('click',()=>{
  if(!state.user){detailDialog.close();openAuth('login','apply');return;}
  $('#apply-gig-title').textContent=state.selectedGig.title;detailDialog.close();$('#apply-error').textContent='';applyDialog.showModal();
});
$('#apply-form').addEventListener('submit',async event=>{
  event.preventDefault();const error=$('#apply-error');error.textContent='';const submit=$('button[type="submit"]',event.currentTarget);submit.disabled=true;
  try{const message=new FormData(event.currentTarget).get('message');await api(`/api/gigs/${encodeURIComponent(state.selectedGig.id)}/applications`,{method:'POST',body:JSON.stringify({message})});event.currentTarget.reset();applyDialog.close();$('#board-status').textContent='Application sent to the gig poster.';setView('my-applications');}
  catch(err){error.textContent=err.message;}finally{submit.disabled=false;}
});
$('#close-gig-button').addEventListener('click',async()=>{
  if(!state.selectedGig||!confirm('Close this gig? It will no longer accept applications.'))return;
  try{await api(`/api/gigs/${encodeURIComponent(state.selectedGig.id)}/close`,{method:'PATCH'});detailDialog.close();$('#board-status').textContent='Gig closed.';setView('my-gigs');}
  catch(err){$('#board-status').textContent=err.message;}
});
$('#view-applications-button').addEventListener('click',async()=>{
  const region=$('#applications-list');region.hidden=false;region.replaceChildren(node('p','','Loading applications…'));
  try{const data=await api(`/api/gigs/${encodeURIComponent(state.selectedGig.id)}/applications`);region.replaceChildren();
    if(!data.items.length){region.append(node('p','','No applications yet.'));return;}
    data.items.forEach(application=>{const item=node('article','application-item');item.append(node('b','',`${application.applicant_name} · ${application.applicant_discipline}`),node('small','',application.applicant_city),node('p','',application.message));if(application.applicant_email){const email=node('a','application-email','Email applicant');const [localPart,domainPart]=application.applicant_email.split('@');email.href=`mailto:${encodeURIComponent(localPart)}@${domainPart}`;item.append(email);}else item.append(node('small','',"Applicant chose not to share an email."));region.append(item);});
  }catch(err){region.replaceChildren(node('p','',err.message));}
});
$('#report-button').addEventListener('click',()=>{
  if(!state.user){detailDialog.close();openAuth('login','report');return;}
  $('#report-error').textContent='';detailDialog.close();reportDialog.showModal();
});
async function moderateReport(reportId,status,closeGig=false){
  try{await api(`/api/moderation/reports/${encodeURIComponent(reportId)}`,{method:'PATCH',body:JSON.stringify({status,note:'',close_gig:closeGig})});$('#board-status').textContent=closeGig?'Report reviewed and gig closed.':`Report ${status}.`;loadBoard();}
  catch(err){$('#board-status').textContent=err.message;}
}
$('#report-form').addEventListener('submit',async event=>{
  event.preventDefault();const error=$('#report-error');error.textContent='';const form=event.currentTarget;const values=Object.fromEntries(new FormData(form));
  try{const result=await api(`/api/gigs/${encodeURIComponent(state.selectedGig.id)}/reports`,{method:'POST',body:JSON.stringify(values)});form.reset();reportDialog.close();$('#board-status').textContent=result.message;}
  catch(err){error.textContent=err.message;}
});
const params=new URLSearchParams(location.search);
authMode(params.has('signin')?'login':'register');
refreshSession().then(()=>{
  if(params.has('signin')&&!state.user)authDialog.showModal();
  if(params.has('post')){if(state.user)postDialog.showModal();else openAuth('register','post');}
});
