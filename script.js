// Fast, static prototype: discovery data is local and no third-party scripts are loaded.
const year = document.querySelector('#year');
if (year) year.textContent = new Date().getFullYear();

const listings = [
  { type:'people', name:'Sade Okonkwo', role:'FOH ENGINEER · LIVE SOUND', location:'Lagos, Nigeria', title:'Making every room sound like the record.', initials:'SO', art:'person-sade', tags:['Live audio','Mixing','Touring'], availability:'AVAILABLE', action:'View profile', searchable:'audio sound engineer sound mixing touring lagos nigeria' },
  { type:'gigs', name:'Open call · touring band', role:'MUSIC · PAID GIG', location:'Accra, Ghana', title:'Drummer wanted for a 6-city run.', initials:'♫', art:'gig-tour', tags:['Drummer','Touring','Paid'], availability:'NEW · 2 DAYS AGO', action:'See opportunity', searchable:'drummer musician band touring gig accra ghana paid' },
  { type:'gear', name:'Aputure 300D II kit', role:'RENTAL · LIGHTING', location:'Lagos, Nigeria', title:'Light the scene. Not your budget.', initials:'◉', art:'gear-light', tags:['Lighting','₦35,000 / day','Pickup'], availability:'AVAILABLE', action:'View equipment', searchable:'camera lighting apurture 300d rental rent gear kit lagos nigeria' },
  { type:'people', name:'Maya Adeyemi', role:'PHOTOGRAPHER · DIRECTOR', location:'London, UK · Works globally', title:'Stories with a little more soul.', initials:'MA', art:'person-maya', tags:['Portraits','Campaigns','Available May'], availability:'BOOKING NOW', action:'View profile', searchable:'photographer photography director camera london portrait campaign' },
  { type:'gigs', name:'Freelance video editor', role:'POST-PRODUCTION · CONTRACT', location:'Remote · Global', title:'Shape a 60-second brand film.', initials:'▧', art:'gig-edit', tags:['Video editing','Remote','3 days'], availability:'NEW · 4 DAYS AGO', action:'See opportunity', searchable:'video editor editing post production remote global gig contract' },
  { type:'gear', name:'Shure SM58 · pair', role:'FOR SALE · AUDIO', location:'Nairobi, Kenya', title:'Two road-tested classics, ready to go.', initials:'♫', art:'gear-mic', tags:['Audio','KSh 22,000','Good condition'], availability:'JUST LISTED', action:'View equipment', searchable:'shure microphone mic audio sale sell gear nairobi kenya' },
  { type:'people', name:'Tunde Oladipo', role:'PRODUCTION MANAGER · LIVE', location:'Lagos, Nigeria', title:'From load-in to last note, I’ve got you.', initials:'TO', art:'person-tunde', tags:['Live events','Crew lead','Mentor'], availability:'OPEN TO GIGS', action:'View profile', searchable:'production manager live events crew stage mentor lagos' },
  { type:'help', name:'How do you price a small crew?', role:'CREW TALK · 18 REPLIES', location:'Community · Production', title:'Share your rate card wisdom with a first-timer.', initials:'?', art:'help-card', tags:['Rates','Production','Advice'], availability:'ACTIVE TODAY', action:'Join the discussion', searchable:'help advice rates pricing crew production question community' }
];
const grid = document.querySelector('#listing-grid');
const empty = document.querySelector('#no-results');
let activeCategory = 'all';
let query = '';
let place = '';
const icons = {people:'↗',gigs:'✳',gear:'▧',help:'?'};
function renderListings(){
  const filtered = listings.filter(item => {
    const categoryMatch = activeCategory === 'all' || activeCategory === item.type || (activeCategory === 'gear' && item.type === 'gear');
    const text = `${item.name} ${item.role} ${item.location} ${item.title} ${item.tags.join(' ')} ${item.searchable}`.toLowerCase();
    const queryMatch = !query || text.includes(query.toLowerCase());
    const placeMatch = !place || item.location.toLowerCase().includes(place.toLowerCase()) || item.location.toLowerCase().includes('global');
    return categoryMatch && queryMatch && placeMatch;
  });
  grid.innerHTML = filtered.map(item => `<article class="listing-card"><div class="listing-art ${item.art}"><span class="art-symbol">${icons[item.type]}</span><span class="listing-status"><i></i>${item.availability}</span><span class="listing-art-label">${item.type === 'people' ? 'CREATIVE PROFILE' : item.type === 'gigs' ? 'OPEN OPPORTUNITY' : item.type === 'gear' ? 'GEAR MARKET' : 'COMMUNITY THREAD'}</span><span class="listing-monogram">${item.initials}</span></div><div class="listing-body"><div class="listing-kicker"><span>${item.role}</span><span>${item.location}</span></div><h3>${item.name}</h3><p>${item.title}</p><div class="listing-tags">${item.tags.map(tag=>`<span>${tag}</span>`).join('')}</div><button class="listing-action" data-open="join">${item.action}<span>↗</span></button></div></article>`).join('');
  empty.hidden = filtered.length !== 0;
  grid.hidden = filtered.length === 0;
  grid.querySelectorAll('[data-open="join"]').forEach(button => button.addEventListener('click', () => openModal('join')));
}
renderListings();

const categoryButtons = [...document.querySelectorAll('.category')];
function selectCategory(category){
  activeCategory = category;
  categoryButtons.forEach(button => {
    const selected = button.dataset.category === category;
    button.classList.toggle('active', selected);
    button.setAttribute('aria-pressed', String(selected));
  });
  renderListings();
}
categoryButtons.forEach(button => button.addEventListener('click', () => selectCategory(button.dataset.category)));

document.querySelectorAll('[data-set-filter]').forEach(link => link.addEventListener('click', () => {
  const value = link.dataset.setFilter;
  selectCategory(value === 'gigs' ? 'gigs' : value === 'gear' ? 'gear' : 'people');
}));
const searchForm = document.querySelector('#search-form');
searchForm.addEventListener('submit', event => {
  event.preventDefault();
  query = document.querySelector('#search').value.trim();
  place = document.querySelector('#location').value.trim();
  selectCategory('all');
  document.querySelector('.discover').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});
});
document.querySelectorAll('.search-shortcuts button').forEach(button => button.addEventListener('click', () => {
  document.querySelector('#search').value = '';
  document.querySelector('#location').value = '';
  query = ''; place = '';
  selectCategory(button.dataset.setFilter);
  document.querySelector('.discover').scrollIntoView({behavior:'smooth'});
}));
document.querySelector('#reset-search').addEventListener('click', () => {
  query = ''; place = '';
  document.querySelector('#search').value = '';
  document.querySelector('#location').value = '';
  selectCategory('all');
});

const dialog = document.querySelector('#signup-modal');
const signupForm = document.querySelector('#signup-form');
function openModal(mode){
  const title = document.querySelector('#modal-title');
  const description = document.querySelector('.modal-description');
  const roleField = signupForm.querySelector('[name="role"]');
  const nameField = signupForm.querySelector('[name="name"]');
  const submit = signupForm.querySelector('button[type="submit"]');
  title.innerHTML = mode === 'signin' ? 'Good to<br><em>see you.</em>' : 'Find your<br><em>people.</em>';
  description.textContent = mode === 'signin' ? 'Member sign-in will be available when the network launches.' : 'One network for creators, crew, and everyone behind the scenes.';
  roleField.closest('label').hidden = mode === 'signin';
  roleField.required = mode !== 'signin';
  nameField.closest('label').hidden = mode === 'signin';
  nameField.required = mode !== 'signin';
  submit.innerHTML = mode === 'signin' ? 'Continue with email <span>↗</span>' : 'Request an invite <span>↗</span>';
  signupForm.dataset.mode = mode;
  signupForm.hidden = false;
  document.querySelector('#success-message').hidden = true;
  dialog.showModal();
}
document.querySelectorAll('[data-open]').forEach(button => button.addEventListener('click', () => openModal(button.dataset.open)));
signupForm.addEventListener('submit', event => {
  event.preventDefault();
  if (!signupForm.reportValidity()) return;
  const success = document.querySelector('#success-message');
  if (signupForm.dataset.mode === 'signin') {
    success.querySelector('h3').textContent = 'Sign-in is coming soon.';
    success.querySelector('p').textContent = 'Member accounts are not connected in this prototype yet.';
  } else {
    success.querySelector('h3').textContent = 'You’re on the list.';
    success.querySelector('p').textContent = 'This is a working prototype. The full community signup will be connected when the platform backend is ready.';
  }
  success.hidden = false;
  signupForm.hidden = true;
});
document.querySelector('#done-button').addEventListener('click', () => dialog.close());
document.querySelector('.mobile-menu').addEventListener('click', event => {
  const button = event.currentTarget;
  const open = button.getAttribute('aria-expanded') !== 'true';
  button.setAttribute('aria-expanded', String(open));
  button.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
  document.querySelector('.main-nav').classList.toggle('nav-open', open);
});
document.querySelectorAll('.main-nav a').forEach(link => link.addEventListener('click', () => {
  document.querySelector('.main-nav').classList.remove('nav-open');
  document.querySelector('.mobile-menu').setAttribute('aria-expanded', 'false');
}));
