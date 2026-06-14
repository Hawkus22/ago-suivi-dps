import { ANTENNES_ORDRE, JOURS_SEMAINE } from './config.js';

function fmtDate(d) {
  if (!d) return '';
  const [y, m, j] = d.split('-');
  return `${j}/${m}/${y}`;
}

export function genererSynthese(semaineNum, semaine, dpsData) {
  // Renfort totaux par DPS parent
  const renfortParParent = {};
  for (const d of dpsData) {
    if (d.est_renfort && d.parent_dps_id)
      renfortParParent[d.parent_dps_id] = (renfortParParent[d.parent_dps_id] || 0) + d.nb;
  }

  // Renforts indexés par parent pour la synthèse visuelle
  const renffortsDe = {};
  const byKey = {};
  for (const d of dpsData) {
    const key = `${d.antenne}|${d.jour}`;
    if (!byKey[key]) byKey[key] = { principaux: [], renforts: [] };
    if (d.est_renfort) {
      byKey[key].renforts.push(d);
      if (d.parent_dps_id) {
        if (!renffortsDe[d.parent_dps_id]) renffortsDe[d.parent_dps_id] = [];
        renffortsDe[d.parent_dps_id].push(d);
      }
    } else {
      byKey[key].principaux.push(d);
    }
  }

  const principaux = dpsData.filter(d => !d.est_renfort);
  const renforts   = dpsData.filter(d => d.est_renfort);
  const totalTl    = principaux.reduce((s, d) => s + d.tl, 0);
  const totalEng   = principaux.reduce((s, d) => s + d.nb + (renfortParParent[d.id] || 0), 0);
  const totalMan   = principaux.reduce((s, d) => s + Math.max(0, d.tl - d.nb - (renfortParParent[d.id] || 0)), 0);
  const nbIncomp   = principaux.filter(d => d.nb + (renfortParParent[d.id] || 0) < d.tl).length;

  const periode = semaine
    ? `Du ${fmtDate(semaine.date_debut)} au ${fmtDate(semaine.date_fin)}`
    : '';

  const html = [];
  const wa   = [];

  html.push(`
<style>
body{font-family:Arial,sans-serif;font-size:13px;margin:10px}
h2{color:#1E3C72;border-bottom:2px solid #1E3C72;padding-bottom:4px}
h3{color:#2196F3;margin:14px 0 4px}
h4{margin:8px 0 2px;color:#333}
table{border-collapse:collapse;width:100%;margin:4px 0}
td,th{border:1px solid #ddd;padding:4px 8px;font-size:12px}
th{background:#1E3C72;color:#fff}
.ok{background:#C6EFCE}.ko{background:#FFC000}
.rok{background:#9DC3E6}.rko{background:#FFE699}
.bilan{background:#f0f4ff;border:1px solid #1E3C72;padding:10px;border-radius:6px;margin-top:12px}
</style>
<h2>📊 Synthèse — Semaine ${semaineNum}</h2>
<p><i>${periode}</i></p>`);

  wa.push(`📊 *SYNTHÈSE — SEMAINE ${semaineNum}*`, `_${periode}_`, '');

  for (const ant of ANTENNES_ORDRE) {
    const joursAnt = JOURS_SEMAINE.filter(j => {
      const g = byKey[`${ant}|${j}`];
      return g && (g.principaux.length || g.renforts.length);
    });
    if (!joursAnt.length) continue;

    html.push(`<h3>${ant}</h3>`);
    wa.push(`*${ant}*`);

    for (const jour of JOURS_SEMAINE) {
      const grp = byKey[`${ant}|${jour}`];
      if (!grp?.principaux.length && !grp?.renforts.length) continue;

      html.push(`<h4>📅 ${jour}</h4><table><tr><th>DPS</th><th>Engagés</th><th>Σ</th><th>Manque</th><th></th></tr>`);
      wa.push(`  📅 ${jour}`);

      for (const d of grp.principaux) {
        const eff  = d.nb + (renfortParParent[d.id] || 0);
        const man  = Math.max(0, d.tl - eff);
        const css  = eff >= d.tl ? 'ok' : 'ko';
        const ic   = eff >= d.tl ? '✅' : '⚠️';
        html.push(`<tr class="${css}"><td>${d.nom_dps}</td><td>${eff}</td><td>${d.tl}</td><td>${man}</td><td>${ic}</td></tr>`);
        wa.push(`  ${ic} ${d.nom_dps}`);
        wa.push(`     Engagés : ${eff}/${d.tl}` + (man ? ` · Manque : ${man}` : ' · Complet'));

        for (const rf of (renffortsDe[d.id] || [])) {
          const ric  = rf.nb >= rf.tl ? '✅' : '⏳';
          const rcss = rf.nb >= rf.tl ? 'rok' : 'rko';
          html.push(`<tr class="${rcss}"><td>&nbsp;&nbsp;↳ [R] ${rf.antenne}</td><td>${rf.nb}</td><td>${rf.tl}</td><td>${Math.max(0, rf.tl - rf.nb)}</td><td>${ric}</td></tr>`);
          wa.push(`     ↳ [R] ${rf.antenne} : ${rf.nb}/${rf.tl} IS ${ric}`);
        }
      }

      // Renforts envoyés par cette antenne (sans parent dans ce groupe)
      for (const r of grp.renforts) {
        if (grp.principaux.some(p => p.id === r.parent_dps_id)) continue; // déjà affiché via renffortsDe
        const ric  = r.nb >= r.tl ? '✅' : '⏳';
        const rcss = r.nb >= r.tl ? 'rok' : 'rko';
        html.push(`<tr class="${rcss}"><td>${r.nom_dps}</td><td>${r.nb}</td><td>${r.tl}</td><td>${Math.max(0, r.tl - r.nb)}</td><td>${ric}</td></tr>`);
      }

      html.push('</table>');
      wa.push('');
    }
    wa.push('');
  }

  html.push(`
<div class="bilan"><b>📈 Bilan global</b><br>
DPS principaux : <b>${principaux.length}</b> &nbsp;|&nbsp;
Incomplets : <b>${nbIncomp}</b> &nbsp;|&nbsp;
Renforts créés : <b>${renforts.length}</b><br>
IS requis : <b>${totalTl}</b> &nbsp;|&nbsp;
Engagés : <b>${totalEng}</b> &nbsp;|&nbsp;
Manquants : <b style="color:${totalMan ? 'red' : 'green'}">${totalMan}</b>
</div>`);

  wa.push(
    '─────────────────────',
    `📈 *BILAN SEMAINE ${semaineNum}*`,
    `DPS principaux : ${principaux.length} | Incomplets : ${nbIncomp}`,
    `Renforts créés : ${renforts.length}`,
    `IS requis : ${totalTl} | Engagés : ${totalEng} | Manquants : ${totalMan}`,
  );

  return { html: html.join('\n'), wa: wa.join('\n') };
}
