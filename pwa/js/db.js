let _sb = null;

export function initSupabase(url, key) {
  _sb = window.supabase.createClient(url, key);
}

// ─── Semaines ──────────────────────────────────────────────────────────────

export async function getSemaines() {
  const { data, error } = await _sb.from('semaines').select('*').order('numero', { ascending: false });
  if (error) throw error;
  return data ?? [];
}

export async function createSemaine(numero, dateDebut, dateFin) {
  const { data, error } = await _sb
    .from('semaines')
    .insert({ numero, date_debut: dateDebut, date_fin: dateFin })
    .select()
    .single();
  if (error) throw error;
  return data;
}

// ─── DPS ───────────────────────────────────────────────────────────────────

export async function getDPS(semaineId) {
  const { data, error } = await _sb
    .from('dps')
    .select('*')
    .eq('semaine_id', semaineId)
    .order('antenne')
    .order('jour')
    .order('est_renfort');
  if (error) throw error;
  return data ?? [];
}

export async function updateDPS(id, fields) {
  const { error } = await _sb.from('dps').update(fields).eq('id', id);
  if (error) throw error;
}

export async function insertDPS(row) {
  const { data, error } = await _sb.from('dps').insert(row).select().single();
  if (error) throw error;
  return data;
}

export async function deleteDPS(id) {
  await _sb.from('dps').delete().eq('parent_dps_id', id);
  const { error } = await _sb.from('dps').delete().eq('id', id);
  if (error) throw error;
}

// ─── Renforts backup ───────────────────────────────────────────────────────

export async function getRenfortsBackup(semaineNum) {
  const { data, error } = await _sb
    .from('renforts_backup')
    .select('*')
    .eq('semaine_num', semaineNum);
  if (error) throw error;
  return data ?? [];
}

export async function deleteRenfortsBackup(semaineNum) {
  const { error } = await _sb.from('renforts_backup').delete().eq('semaine_num', semaineNum);
  if (error) throw error;
}
