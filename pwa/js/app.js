import { ANTENNES_ORDRE, JOURS_SEMAINE, JOURS_COURT, COLORS, SUPABASE_URL, SUPABASE_ANON_KEY } from './config.js';
import { initSupabase, getSupabase, signIn, signOut, getSession,
         getSemaines, createSemaine, getDPS, updateDPS, insertDPS, deleteDPS } from './db.js';
import { suggererRenforts, toutesDisponibilites } from './renfort.js';
import { genererSynthese } from './synthese.js';

// ─── État global ───────────────────────────────────────────────────────────

const state = {
  semaines: [],
  currentSemaineId: null,
  currentSemaineNum: null,
  currentJour: JOURS_SEMAINE[0],
  dpsData: [],
};

// ─── Bootstrap ─────────────────────────────────────────────────────────────

if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('./sw.js').catch(() => {});
}

initSupabase(SUPABASE_URL, SUPABASE_ANON_KEY);

// ─── Installation PWA ──────────────────────────────────────────────────────

let _installPrompt = null;

// Android Chrome : on capture le prompt natif
window.addEventListener('beforeinstallprompt', e => {
  e.preventDefault();
  _installPrompt = e;
  document.getElementById('install-banner').style.display = 'block';
});

// iOS Safari : pas de prompt natif, on affiche une instruction manuelle
const isIOS = /iphone|ipad|ipod/i.test(navigator.userAgent);
const isInStandaloneMode = window.matchMedia('(display-mode: standalone)').matches
  || window.navigator.standalone;
if (isIOS && !isInStandaloneMode) {
  document.getElementById('ios-hint').style.display = 'block';
}

document.getElementById('btn-install').onclick = async () => {
  if (!_installPrompt) return;
  _installPrompt.prompt();
  const { outcome } = await _installPrompt.userChoice;
  if (outcome === 'accepted') {
    document.getElementById('install-banner').style.display = 'none';
  }
  _installPrompt = null;
};

// Écoute les changements de session (connexion / déconnexion / recovery)
getSupabase().auth.onAuthStateChange((event, session) => {
  if (event === 'PASSWORD_RECOVERY') {
    // Lien "mot de passe oublié" cliqué → demander le nouveau mot de passe
    showSetPassword();
    return;
  }
  if (event === 'SIGNED_IN' && session) {
    // Invitation magic link → demander de définir un mot de passe si pas encore fait
    const isInvite = window.location.hash.includes('type=invite');
    if (isInvite) {
      showSetPassword(session.user.email);
      return;
    }
    showApp(session.user.email);
    return;
  }
  if (session) {
    showApp(session.user.email);
  } else {
    showLogin();
  }
});

// Vérification de session existante au démarrage
(async () => {
  const session = await getSession();
  if (session) {
    showApp(session.user.email);
  } else {
    showLogin();
  }
})();

// ─── Login ─────────────────────────────────────────────────────────────────

function showLogin(errMsg = '') {
  document.getElementById('login-screen').style.display = 'flex';
  document.getElementById('app').style.display = 'none';
  const err = document.getElementById('login-error');
  err.textContent = errMsg;
  err.style.display = errMsg ? 'block' : 'none';
}

document.getElementById('btn-login').onclick = async () => {
  const email = document.getElementById('login-email').value.trim();
  const pwd   = document.getElementById('login-pwd').value;
  if (!email || !pwd) { showLogin('Email et mot de passe requis.'); return; }
  const btn = document.getElementById('btn-login');
  btn.disabled = true;
  btn.textContent = 'Connexion…';
  try {
    await signIn(email, pwd);
    // onAuthStateChange prend le relais
  } catch (err) {
    showLogin(err.message === 'Invalid login credentials'
      ? 'Email ou mot de passe incorrect.'
      : err.message);
    btn.disabled = false;
    btn.textContent = 'Se connecter';
  }
};

// ─── Définir / changer mot de passe ───────────────────────────────────────

function showSetPassword(email = '') {
  document.getElementById('login-screen').style.display = 'none';
  document.getElementById('app').style.display = 'none';
  document.getElementById('set-password-screen').style.display = 'flex';
  if (email) document.getElementById('set-pwd-email').textContent = email;
}

document.getElementById('btn-set-pwd').onclick = async () => {
  const pwd1 = document.getElementById('set-pwd-1').value;
  const pwd2 = document.getElementById('set-pwd-2').value;
  const err  = document.getElementById('set-pwd-error');

  if (pwd1.length < 8) {
    err.textContent = 'Le mot de passe doit faire au moins 8 caractères.';
    err.style.display = 'block'; return;
  }
  if (pwd1 !== pwd2) {
    err.textContent = 'Les mots de passe ne correspondent pas.';
    err.style.display = 'block'; return;
  }

  const btn = document.getElementById('btn-set-pwd');
  btn.disabled = true; btn.textContent = 'Enregistrement…';

  try {
    const { error } = await getSupabase().auth.updateUser({ password: pwd1 });
    if (error) throw error;
    // Nettoyer le hash de l'URL (type=invite / type=recovery)
    history.replaceState(null, '', window.location.pathname);
    const { data: { session } } = await getSupabase().auth.getSession();
    document.getElementById('set-password-screen').style.display = 'none';
    showApp(session.user.email);
  } catch (e) {
    err.textContent = e.message;
    err.style.display = 'block';
    btn.disabled = false; btn.textContent = 'Enregistrer';
  }
};

// ─── App démarrée ──────────────────────────────────────────────────────────

async function showApp(userEmail) {
  document.getElementById('login-screen').style.display = 'none';
  document.getElementById('app').style.display = 'flex';
  document.getElementById('user-email').textContent = userEmail;
  renderDayTabs();
  bindHeaderActions();
  await loadSemaines();
}

// ─── Semaines ──────────────────────────────────────────────────────────────

async function loadSemaines() {
  state.semaines = await getSemaines();
  renderWeekSelector();
  if (state.semaines.length) {
    const s = state.semaines[0];
    await selectSemaine(s.id, s.numero);
  } else {
    document.getElementById('main-content').innerHTML =
      '<p class="empty-msg">Aucune semaine. Appuyez sur + pour en créer une.</p>';
  }
}

function renderWeekSelector() {
  const sel = document.getElementById('semaine-select');
  sel.innerHTML = state.semaines.length
    ? state.semaines.map(s =>
        `<option value="${s.id}" data-num="${s.numero}">Semaine ${s.numero}</option>`
      ).join('')
    : '<option value="">—</option>';
  if (state.currentSemaineId) sel.value = state.currentSemaineId;
}

async function selectSemaine(id, numero) {
  state.currentSemaineId = id;
  state.currentSemaineNum = numero;
  document.getElementById('semaine-select').value = id;
  await loadDPS();
}

// ─── DPS ───────────────────────────────────────────────────────────────────

async function loadDPS() {
  if (!state.currentSemaineId) return;
  setLoading(true);
  try {
    state.dpsData = await getDPS(state.currentSemaineId);
  } catch (err) {
    alert('Erreur chargement : ' + err.message);
  } finally {
    setLoading(false);
  }
  renderView();
}

// ─── En-têtes ──────────────────────────────────────────────────────────────

function renderDayTabs() {
  const ct = document.getElementById('day-tabs');
  ct.innerHTML = JOURS_SEMAINE.map((j, i) =>
    `<button class="day-tab${j === state.currentJour ? ' active' : ''}" data-jour="${j}">${JOURS_COURT[i]}</button>`
  ).join('');
  ct.querySelectorAll('.day-tab').forEach(btn => {
    btn.onclick = () => {
      state.currentJour = btn.dataset.jour;
      ct.querySelectorAll('.day-tab').forEach(b => b.classList.toggle('active', b === btn));
      renderView();
    };
  });
}

function bindHeaderActions() {
  document.getElementById('semaine-select').onchange = e => {
    const opt = e.target.selectedOptions[0];
    if (!opt || !opt.value) return;
    selectSemaine(+opt.value, +opt.dataset.num);
  };
  document.getElementById('btn-new-week').onclick = openNewWeekModal;
  document.getElementById('btn-refresh').onclick  = loadDPS;
  document.getElementById('btn-synthese').onclick = openSyntheseModal;
  document.getElementById('btn-logout').onclick = async () => {
    if (!confirm('Se déconnecter ?')) return;
    await signOut();
  };
}

// ─── Vue principale ────────────────────────────────────────────────────────

function renderView() {
  const jour = state.currentJour;

  const renfortParParent = {};
  for (const d of state.dpsData) {
    if (d.est_renfort && d.parent_dps_id)
      renfortParParent[d.parent_dps_id] = (renfortParParent[d.parent_dps_id] || 0) + d.nb;
  }

  const cards = ANTENNES_ORDRE.map(ant => {
    const rows      = state.dpsData.filter(d => d.antenne === ant && d.jour === jour);
    const principaux = rows.filter(d => !d.est_renfort);
    const renforts   = rows.filter(d => d.est_renfort);

    const dpRows = [
      ...principaux.map(d => renderPrincipalRow(d, renfortParParent, ant, jour)),
      ...renforts.map(r => renderRenfortRow(r)),
    ].join('');

    const hasData = rows.length > 0;
    return `
<div class="antenne-card">
  <div class="antenne-header">
    <span>${ant}</span>
    <button class="btn-add-dps" data-ant="${enc(ant)}" data-jour="${enc(jour)}">+ DPS</button>
  </div>
  <div class="antenne-body${hasData ? '' : ' collapsed'}">
    ${dpRows || '<p class="empty-ant">Aucun DPS</p>'}
  </div>
</div>`;
  }).join('');

  document.getElementById('main-content').innerHTML = cards;
  bindViewEvents();
}

function renderPrincipalRow(d, renfortParParent, ant, jour) {
  const eff     = d.nb + (renfortParParent[d.id] || 0);
  const man     = Math.max(0, d.tl - eff);
  const complet = eff >= d.tl;
  const bg      = complet ? COLORS.GREEN : COLORS.ORANGE;
  const rCount  = state.dpsData.filter(r => r.est_renfort && r.parent_dps_id === d.id).length;
  const rInfo   = rCount > 0
    ? `<span class="renfort-badge">↗ ${rCount} R · ${renfortParParent[d.id] || 0} IS</span>`
    : '';
  const renfortBtn = !complet
    ? `<button class="btn-renfort"
         data-id="${d.id}" data-nom="${enc(d.nom_dps)}"
         data-ant="${enc(ant)}" data-jour="${enc(jour)}"
         data-nb="${eff}" data-tl="${d.tl}">💡 Renfort</button>`
    : '';

  return `
<div class="dps-row" style="background:${bg}">
  <div class="dps-line">
    <span class="dps-nom" title="${d.nom_dps}">${d.nom_dps}</span>
    <span class="dps-stat">${eff}/${d.tl}${man ? ` <em>-${man}</em>` : ' ✓'}</span>
    <span class="dps-act">
      <button class="btn-edit" data-id="${d.id}">✏️</button>
      <button class="btn-del"  data-id="${d.id}">🗑️</button>
    </span>
  </div>
  ${rInfo}${renfortBtn}
</div>`;
}

function renderRenfortRow(r) {
  const complet = r.nb >= r.tl;
  const bg = complet ? COLORS.RENFORT_OK : COLORS.RENFORT_KO;
  return `
<div class="dps-row dps-renfort" style="background:${bg}">
  <div class="dps-line">
    <span class="dps-nom" title="${r.nom_dps}">${r.nom_dps}</span>
    <span class="dps-stat">${r.nb}/${r.tl}${r.nb < r.tl ? ` <em>-${r.tl - r.nb}</em>` : ' ✓'}</span>
    <span class="dps-act">
      <button class="btn-edit" data-id="${r.id}">✏️</button>
      <button class="btn-del"  data-id="${r.id}">🗑️</button>
    </span>
  </div>
</div>`;
}

function bindViewEvents() {
  document.querySelectorAll('.btn-edit').forEach(b =>
    b.onclick = e => { e.stopPropagation(); openEditModal(+b.dataset.id); }
  );
  document.querySelectorAll('.btn-del').forEach(b =>
    b.onclick = async e => {
      e.stopPropagation();
      if (!confirm('Supprimer ce DPS et ses renforts associés ?')) return;
      try { await deleteDPS(+b.dataset.id); await loadDPS(); }
      catch (err) { alert(err.message); }
    }
  );
  document.querySelectorAll('.btn-add-dps').forEach(b =>
    b.onclick = () => openAddDpsModal(dec(b.dataset.ant), dec(b.dataset.jour))
  );
  document.querySelectorAll('.btn-renfort').forEach(b =>
    b.onclick = () => openRenfortModal(
      +b.dataset.id, dec(b.dataset.nom),
      dec(b.dataset.ant), dec(b.dataset.jour),
      +b.dataset.nb, +b.dataset.tl
    )
  );
  // Toggle corps de carte pour antennes vides
  document.querySelectorAll('.antenne-header').forEach(h => {
    const body = h.nextElementSibling;
    h.onclick = e => {
      if (e.target.classList.contains('btn-add-dps')) return;
      body.classList.toggle('collapsed');
    };
  });
}

// ─── Modals helpers ────────────────────────────────────────────────────────

function openModal(html) {
  const ov = document.getElementById('modal-overlay');
  document.getElementById('modal-content').innerHTML = html;
  ov.classList.remove('hidden');
  ov.onclick = e => { if (e.target === ov) closeModal(); };
  document.getElementById('modal-content').querySelector('.btn-close')?.addEventListener('click', closeModal);
}

function closeModal() {
  document.getElementById('modal-overlay').classList.add('hidden');
}

// ─── Modal : éditer DPS ────────────────────────────────────────────────────

function openEditModal(id) {
  const d = state.dpsData.find(x => x.id === id);
  if (!d) return;
  const label = d.est_renfort ? d.nom_dps : d.nom_dps;
  openModal(`
<div class="modal-box">
  <h3>Modifier</h3>
  <p class="modal-sub">${label}</p>
  <div class="fg"><label>Engagés</label><input type="number" id="e-nb" min="0" value="${d.nb}"></div>
  <div class="fg"><label>Requis total (Σ)</label><input type="number" id="e-tl" min="0" value="${d.tl}"></div>
  <div class="modal-btns">
    <button class="btn-close btn-sec">Annuler</button>
    <button class="btn-prim" id="btn-save-edit">Enregistrer</button>
  </div>
</div>`);

  document.getElementById('btn-save-edit').onclick = async () => {
    const nb = +document.getElementById('e-nb').value;
    const tl = +document.getElementById('e-tl').value;
    try { await updateDPS(id, { nb, tl }); closeModal(); await loadDPS(); }
    catch (err) { alert(err.message); }
  };
}

// ─── Modal : ajouter DPS ───────────────────────────────────────────────────

function openAddDpsModal(ant, jour) {
  openModal(`
<div class="modal-box">
  <h3>Ajouter un DPS</h3>
  <p class="modal-sub">${ant} · ${jour}</p>
  <div class="fg"><label>Nom du DPS</label><input type="text" id="a-nom" placeholder="ex : Match Football 14h–18h"></div>
  <div class="fg"><label>Engagés</label><input type="number" id="a-nb" min="0" value="0"></div>
  <div class="fg"><label>Requis total (Σ)</label><input type="number" id="a-tl" min="1" value="1"></div>
  <div class="modal-btns">
    <button class="btn-close btn-sec">Annuler</button>
    <button class="btn-prim" id="btn-save-add">Ajouter</button>
  </div>
</div>`);

  document.getElementById('btn-save-add').onclick = async () => {
    const nom = document.getElementById('a-nom').value.trim();
    const nb  = +document.getElementById('a-nb').value;
    const tl  = +document.getElementById('a-tl').value;
    if (!nom) { alert('Le nom est requis.'); return; }
    try {
      await insertDPS({
        semaine_id: state.currentSemaineId,
        antenne: ant, jour,
        nom_dps: nom, nb, tl,
        est_renfort: 0, parent_dps_id: null, est_manuel: 1,
      });
      closeModal();
      await loadDPS();
    } catch (err) { alert(err.message); }
  };
}

// ─── Modal : renforts ──────────────────────────────────────────────────────

function openRenfortModal(dpsId, nomDps, ant, jour, nb, tl) {
  const besoin   = tl - nb;
  const sugg     = suggererRenforts(ant, jour, state.dpsData);
  const toutes   = toutesDisponibilites(ant, jour, state.dpsData);
  let   showAll  = false;

  const ov = document.getElementById('modal-overlay');
  ov.classList.remove('hidden');
  ov.onclick = e => { if (e.target === ov) closeModal(); };

  function render() {
    const list = showAll ? toutes : sugg;
    document.getElementById('modal-content').innerHTML = renfortHTML(list, nomDps, ant, jour, besoin, showAll);

    document.querySelector('.btn-close').onclick = closeModal;

    document.getElementById('tog-toutes').onchange = e => {
      const prev = [...document.querySelectorAll('input[name="ra"]:checked')].map(i => i.value);
      showAll = e.target.checked;
      render();
      prev.forEach(v => {
        const inp = [...document.querySelectorAll('input[name="ra"]')].find(i => i.value === v);
        if (inp) inp.checked = true;
      });
    };

    document.getElementById('btn-valider').onclick = async () => {
      const sel = [...document.querySelectorAll('input[name="ra"]:checked')].map(i => i.value);
      if (!sel.length) { alert('Sélectionnez au moins une antenne.'); return; }
      const base = Math.floor(besoin / sel.length);
      const rest = besoin % sel.length;
      try {
        for (let i = 0; i < sel.length; i++) {
          await insertDPS({
            semaine_id: state.currentSemaineId,
            antenne: sel[i], jour,
            nom_dps: `[R] ${nomDps}`,
            nb: 0, tl: base + (i < rest ? 1 : 0),
            est_renfort: 1, parent_dps_id: dpsId, est_manuel: 1,
          });
        }
        closeModal();
        await loadDPS();
      } catch (err) { alert(err.message); }
    };
  }

  render();
}

function renfortHTML(list, nomDps, ant, jour, besoin, showAll) {
  const items = list.map(s => {
    const cls = s.disponibilite.includes('Aucun') || s.disponibilite.includes('Marge')
      ? 'libre' : s.disponibilite.includes('Partielle') ? 'partielle' : 'indispo';
    return `
<label class="ri ri-${cls}">
  <input type="checkbox" name="ra" value="${s.antenne}">
  <span class="ri-name">${s.antenne}</span>
  <span class="ri-dispo">${s.disponibilite}</span>
</label>`;
  }).join('');

  return `
<div class="modal-box">
  <h3>💡 Proposer des renforts</h3>
  <p class="modal-sub">${nomDps} · ${ant} · ${jour}</p>
  <p class="r-besoin">Besoin : <b>${besoin} IS</b></p>
  <div class="r-list">${items}</div>
  <label class="tog-lbl">
    <input type="checkbox" id="tog-toutes" ${showAll ? 'checked' : ''}>
    Afficher toutes les antennes
  </label>
  <div class="modal-btns">
    <button class="btn-close btn-sec">Annuler</button>
    <button class="btn-prim" id="btn-valider">Valider les [R]</button>
  </div>
</div>`;
}

// ─── Modal : nouvelle semaine ───────────────────────────────────────────────

function openNewWeekModal() {
  const today  = new Date();
  const monday = new Date(today);
  monday.setDate(today.getDate() - ((today.getDay() + 6) % 7));
  const sunday = new Date(monday);
  sunday.setDate(monday.getDate() + 6);
  const fmt = d => d.toISOString().slice(0, 10);

  // Numéro ISO de semaine
  const jan4   = new Date(today.getFullYear(), 0, 4);
  const weekN  = Math.ceil(((today - jan4) / 86400000 + jan4.getDay() + 1) / 7);

  openModal(`
<div class="modal-box">
  <h3>Nouvelle semaine</h3>
  <div class="fg"><label>Numéro de semaine</label><input type="number" id="w-num" min="1" max="53" value="${weekN}"></div>
  <div class="fg"><label>Date début</label><input type="date" id="w-deb" value="${fmt(monday)}"></div>
  <div class="fg"><label>Date fin</label><input type="date" id="w-fin" value="${fmt(sunday)}"></div>
  <div class="modal-btns">
    <button class="btn-close btn-sec">Annuler</button>
    <button class="btn-prim" id="btn-save-week">Créer</button>
  </div>
</div>`);

  document.getElementById('btn-save-week').onclick = async () => {
    const num = +document.getElementById('w-num').value;
    const deb = document.getElementById('w-deb').value;
    const fin = document.getElementById('w-fin').value;
    if (!num || !deb || !fin) { alert('Tous les champs sont requis.'); return; }
    try {
      const sem = await createSemaine(num, deb, fin);
      state.semaines = await getSemaines();
      renderWeekSelector();
      await selectSemaine(sem.id, sem.numero);
      closeModal();
    } catch (err) { alert(err.message); }
  };
}

// ─── Modal : synthèse ──────────────────────────────────────────────────────

async function openSyntheseModal() {
  if (!state.currentSemaineId) return;
  const sem = state.semaines.find(s => s.id === state.currentSemaineId);
  const { html, wa } = genererSynthese(state.currentSemaineNum, sem, state.dpsData);

  openModal(`
<div class="modal-box modal-lg">
  <h3>📊 Synthèse — Semaine ${state.currentSemaineNum}</h3>
  <div class="synt-body">${html}</div>
  <div class="modal-btns">
    <button class="btn-close btn-sec">Fermer</button>
    <button class="btn-wa" id="btn-wa">📱 Copier WhatsApp</button>
  </div>
</div>`);

  document.getElementById('btn-wa').onclick = async () => {
    try {
      await navigator.clipboard.writeText(wa);
      document.getElementById('btn-wa').textContent = '✅ Copié !';
    } catch {
      prompt('Copiez ce texte :', wa);
    }
  };
}

// ─── Utilitaires ───────────────────────────────────────────────────────────

function setLoading(on) {
  document.getElementById('loading').style.display = on ? 'flex' : 'none';
}

const enc = v => encodeURIComponent(v);
const dec = v => decodeURIComponent(v);
