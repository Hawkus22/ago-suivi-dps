import { ANTENNES_ORDRE } from './config.js';

export function getVoisins(antenne, rayon = 3) {
  const idx = ANTENNES_ORDRE.indexOf(antenne);
  if (idx < 0) return [];
  const res = [];
  for (let d = 1; d <= rayon; d++) {
    if (idx - d >= 0) res.push(ANTENNES_ORDRE[idx - d]);
    if (idx + d < ANTENNES_ORDRE.length) res.push(ANTENNES_ORDRE[idx + d]);
  }
  return res.slice(0, rayon);
}

export function evaluerDisponibilite(antenne, jour, dpsData) {
  const rows = dpsData.filter(d => d.antenne === antenne && d.jour === jour && !d.est_renfort);
  const tl = rows.reduce((s, d) => s + (d.tl || 0), 0);
  const nb = rows.reduce((s, d) => s + (d.nb || 0), 0);
  if (tl === 0)   return { label: "Libre (Aucun DPS)",             capacite: 99 };
  if (nb >= tl)   return { label: `Libre (Marge de ${nb - tl} IS)`, capacite: nb - tl };
  if (nb > 0)     return { label: `Partielle (Manque ${tl - nb} IS)`, capacite: 0 };
  return           { label: "Indisponible (0 IS)",                  capacite: 0 };
}

function rangDispo(label) {
  if (label.includes('Aucun DPS'))  return 0;
  if (label.includes('Marge'))      return 1;
  if (label.includes('Partielle'))  return 2;
  return 3;
}

export function suggererRenforts(antenneCible, jour, dpsData) {
  return getVoisins(antenneCible).map((ant, i) => {
    const { label, capacite } = evaluerDisponibilite(ant, jour, dpsData);
    return { antenne: ant, distance: i + 1, disponibilite: label, capacite };
  }).sort((a, b) => rangDispo(a.disponibilite) - rangDispo(b.disponibilite));
}

export function toutesDisponibilites(antenneCible, jour, dpsData) {
  const idxC = ANTENNES_ORDRE.indexOf(antenneCible);
  return ANTENNES_ORDRE
    .filter(a => a !== antenneCible)
    .map(ant => {
      const { label, capacite } = evaluerDisponibilite(ant, jour, dpsData);
      const dist = idxC >= 0 ? Math.abs(ANTENNES_ORDRE.indexOf(ant) - idxC) : 99;
      return { antenne: ant, distance: dist, disponibilite: label, capacite };
    })
    .sort((a, b) => {
      const r = rangDispo(a.disponibilite) - rangDispo(b.disponibilite);
      return r !== 0 ? r : a.distance - b.distance;
    });
}
