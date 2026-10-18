// CREWBAY's interactive demo. Listings are local examples; no personal data is sent or persisted.
const byId = (id) => document.getElementById(id);
const make = (tag, className, text) => {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
};

const year = byId('year');
if (year) year.textContent = String(new Date().getFullYear());

const listings = [
  { type:'people', name:'Sade Okonkwo', role:'FOH ENGINEER · LIVE SOUND', location:'Lagos, Nigeria', title:'Making every room sound like the record.', initials:'SO', art:'person-sade', tags:['Live audio','Mixing','Touring'], availability:'AVAILABLE', action:'View profile', searchable:'audio sound engineer sound mixing touring lagos nigeria' },
  { type:'gigs', name:'Open call · touring band', role:'MUSIC · PAID GIG', location:'Accra, Ghana', title:'Drummer wanted for a 6-city run.', initials:'♫', art:'gig-tour', tags:['Drummer','Touring','Paid'], availability:'NEW · 2 DAYS AGO', action:'See opportunity', searchable:'drummer musician band touring gig accra ghana paid' },
  { type:'gear', name:'Aputure 300D II kit', role:'RENTAL · LIGHTING', location:'Lagos, Nigeria', title:'Light the scene. Not your budget.', initials:'◉', art:'gear-light', tags:['Lighting','₦35,000 / day','Pickup'], availability:'AVAILABLE', action:'View equipment', searchable:'camera lighting aputure 300d rental rent gear kit lagos nigeria' },
  { type:'people', name:'Maya Adeyemi', role:'PHOTOGRAPHER · DIRECTOR', location:'London, UK · Works globally', title:'Stories with a little more soul.', initials:'MA', art:'person-maya', tags:['Portraits','Campaigns','Available May'], availability:'BOOKING NOW', action:'View profile', searchable:'photographer photography director camera london portrait campaign' },
  { type:'gigs', name:'Freelance video editor', role:'POST-PRODUCTION · CONTRACT', location:'Remote · Global', title:'Shape a 60-second brand film.', initials:'▧', art:'gig-edit', tags:['Video editing','Remote','3 days'], availability:'NEW · 4 DAYS AGO', action:'See opportunity', searchable:'video editor editing post production remote global gig contract' },
  { type:'gear', name:'Shure SM58 · pair', role:'FOR SALE · AUDIO', location:'Nairobi, Kenya', title:'Two road-tested classics, ready to go.', initials:'♫', art:'gear-mic', tags:['Audio','KSh 22,000','Good condition'], availability:'JUST LISTED', action:'View equipment', searchable:'shure microphone mic audio sale sell gear nairobi kenya' },
  { type:'people', name:'Tunde Oladipo', role:'PRODUCTION MANAGER · LIVE', location:'Lagos, Nigeria', title:'From load-in to last note, I’ve got you.', initials:'TO', art:'person-tunde', tags:['Live events','Crew lead','Mentor'], availability:'OPEN TO GIGS', action:'View profile', searchable:'production manager live events crew stage mentor lagos' },
  { type:'help', name:'How do you price a small crew?', role:'CREW TALK · 18 REPLIES', location:'Community · Production', title:'Share your rate card wisdom with a first-timer.', initials:'?', art:'help-card', tags:['Rates','Production','Advice'], availability:'ACTIVE TODAY', action:'Join the discussion', searchable:'help advice rates pricing crew production question community' }
];
const artLabels = { people:'CREATIVE PROFILE', gigs:'OPEN OPPORTUNITY', gear:'GEAR MARKET', help:'COMMUNITY THREAD' };
const artIcons = { people:'↗', gigs:'✳', gear:'▧', help:'?' };
const grid = byId('listing-grid');
const empty = byId('no-results');
let activeCategory = 'all';
let query = '';
let place = '';
let hasInteractedWithListings = false;

function createListing(item) {
  const card = make('article', 'listing-card');
  const art = make('div', `listing-art ${item.art}`);
  art.append(make('span', 'art-symbol', artIcons[item.type] || '✳'));
  const status = make('span', 'listing-status');
  const statusDot = make('i');
  status.append(statusDot, document.createTextNode(item.availability));
  art.append(status, make('span', 'listing-art-label', artLabels[item.type] || 'COMMUNITY'), make('span', 'listing-monogram', item.initials));

  const body = make('div', 'listing-body');
  const kicker = make('div', 'listing-kicker');
  kicker.append(make('span', '', item.role), make('span', '', item.location));
  body.append(kicker, make('h3', '', item.name), make('p', '', item.title));

  const tags = make('div', 'listing-tags');
  item.tags.forEach((tag) => tags.append(make('span', '', tag)));
  body.append(tags);

  const action = make('button', 'listing-action');
  action.type = 'button';
  action.append(document.createTextNode(item.action), make('span', '', '↗'));
  action.addEventListener('click', () => openModal('join'));
  body.append(action);
  card.append(art, body);
  return card;
}

function renderListings() {
  if (!grid) return;
  const normalizedQuery = query.toLocaleLowerCase().trim();
  const normalizedPlace = place.toLocaleLowerCase().trim();
  const filtered = listings.filter((item) => {
    const matchesCategory = activeCategory === 'all' || item.type === activeCategory;
    const searchable = `${item.name} ${item.role} ${item.location} ${item.title} ${item.tags.join(' ')} ${item.searchable}`.toLocaleLowerCase();
    const matchesQuery = !normalizedQuery || searchable.includes(normalizedQuery);
    const normalizedLocation = item.location.toLocaleLowerCase();
    const matchesPlace = !normalizedPlace || normalizedLocation.includes(normalizedPlace) || normalizedLocation.includes('global');
    return matchesCategory && matchesQuery && matchesPlace;
  });

  const fragment = document.createDocumentFragment();
  filtered.forEach((item) => fragment.append(createListing(item)));
  grid.replaceChildren(fragment);
  const status = byId('results-status');
  if (status && hasInteractedWithListings) {
    status.textContent = `${filtered.length} ${filtered.length === 1 ? 'listing' : 'listings'} found`;
  }
  if (empty) empty.hidden = filtered.length !== 0;
  grid.hidden = filtered.length === 0;
}
renderListings();

const categoryButtons = [...document.querySelectorAll('.category')];
function selectCategory(category) {
  const allowed = new Set(['all', 'people', 'gigs', 'gear', 'help']);
  activeCategory = allowed.has(category) ? category : 'all';
  hasInteractedWithListings = true;
  categoryButtons.forEach((button) => {
    const selected = button.dataset.category === activeCategory;
    button.classList.toggle('active', selected);
    button.setAttribute('aria-pressed', String(selected));
  });
  renderListings();
}
categoryButtons.forEach((button) => button.addEventListener('click', () => selectCategory(button.dataset.category)));

document.querySelectorAll('[data-set-filter]').forEach((link) => link.addEventListener('click', () => {
  const value = link.dataset.setFilter;
  selectCategory(value === 'gigs' || value === 'gear' || value === 'help' ? value : 'people');
}));

const searchForm = byId('search-form');
if (searchForm) searchForm.addEventListener('submit', (event) => {
  event.preventDefault();
  query = byId('search').value.trim();
  place = byId('location').value.trim();
  selectCategory('all');
  document.querySelector('.discover')?.scrollIntoView({
    behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth'
  });
});
document.querySelectorAll('.search-shortcuts button').forEach((button) => button.addEventListener('click', () => {
  byId('search').value = '';
  byId('location').value = '';
  query = '';
  place = '';
  selectCategory(button.dataset.setFilter);
  document.querySelector('.discover')?.scrollIntoView({
    behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth'
  });
}));
byId('reset-search')?.addEventListener('click', () => {
  query = '';
  place = '';
  byId('search').value = '';
  byId('location').value = '';
  selectCategory('all');
});

const dialog = byId('signup-modal');
const signupForm = byId('signup-form');
function openModal(mode) {
  if (!dialog || !signupForm || dialog.open) return;
  const isSignIn = mode === 'signin';
  const title = byId('modal-title');
  title.replaceChildren(document.createTextNode(isSignIn ? 'Good to' : 'Find your'), document.createElement('br'));
  const emphasis = make('em', '', isSignIn ? 'see you.' : 'people.');
  title.append(emphasis);
  document.querySelector('.modal-description').textContent = isSignIn
    ? 'Member sign-in will be available when the network launches.'
    : 'One network for creators, crew, and everyone behind the scenes.';
  const roleField = signupForm.querySelector('[name="role"]');
  const nameField = signupForm.querySelector('[name="name"]');
  roleField.closest('label').hidden = isSignIn;
  roleField.required = !isSignIn;
  nameField.closest('label').hidden = isSignIn;
  nameField.required = !isSignIn;
  const submit = signupForm.querySelector('button[type="submit"]');
  submit.replaceChildren(document.createTextNode(isSignIn ? 'Continue with email ' : 'Request an invite '), make('span', '', '↗'));
  signupForm.dataset.mode = isSignIn ? 'signin' : 'join';
  signupForm.hidden = false;
  byId('success-message').hidden = true;
  dialog.showModal();
}
document.querySelectorAll('[data-open]').forEach((button) => button.addEventListener('click', () => openModal(button.dataset.open)));
if (signupForm) signupForm.addEventListener('submit', (event) => {
  event.preventDefault();
  if (!signupForm.reportValidity()) return;
  const success = byId('success-message');
  if (signupForm.dataset.mode === 'signin') {
    success.querySelector('h3').textContent = 'Sign-in is coming soon.';
    success.querySelector('p').textContent = 'Member accounts are not connected in this prototype yet.';
  } else {
    success.querySelector('h3').textContent = 'Thanks for trying the demo.';
    success.querySelector('p').textContent = 'This prototype does not save or send your details. Real invitations will be available when the platform backend is ready.';
  }
  success.hidden = false;
  signupForm.hidden = true;
});
byId('done-button')?.addEventListener('click', () => dialog?.close());
if (dialog && signupForm) dialog.addEventListener('close', () => {
  signupForm.reset();
  signupForm.hidden = false;
  signupForm.dataset.mode = 'join';
  signupForm.querySelector('[name="name"]').closest('label').hidden = false;
  signupForm.querySelector('[name="name"]').required = true;
  signupForm.querySelector('[name="role"]').closest('label').hidden = false;
  signupForm.querySelector('[name="role"]').required = true;
  byId('success-message').hidden = true;
});

const menuButton = document.querySelector('.mobile-menu');
const nav = document.querySelector('.main-nav');
if (menuButton && nav) {
  menuButton.addEventListener('click', () => {
    const open = menuButton.getAttribute('aria-expanded') !== 'true';
    menuButton.setAttribute('aria-expanded', String(open));
    menuButton.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    nav.classList.toggle('nav-open', open);
  });
  nav.querySelectorAll('a').forEach((link) => link.addEventListener('click', () => {
    nav.classList.remove('nav-open');
    menuButton.setAttribute('aria-expanded', 'false');
    menuButton.setAttribute('aria-label', 'Open menu');
  }));
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      nav.classList.remove('nav-open');
      menuButton.setAttribute('aria-expanded', 'false');
      menuButton.setAttribute('aria-label', 'Open menu');
    }
  });
}
