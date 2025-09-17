# -*- coding: utf-8 -*-
"""
align_srt_jp_to_romanji.py
But: réaligner le SRT japonais sur la segmentation du SRT romanji corrigé,
en évitant de perdre du texte japonais. Scinder uniquement quand l'alignement
mot-par-mot est fiable ; sinon, fallback = texte japonais complet.
"""

import re
import pysrt
from collections import defaultdict
from pykakasi import kakasi
from pathlib import Path

# ========== Réglages ==========
JP_PATH = "C:/Users/babak/Videos/PSO/PSO22.srt"
romanji_PATH = "C:/Users/babak/Videos/PSO/PSO22_rom.srt"
OUT_PATH = "C:/Users/babak/Videos/PSO/PSO22_corrige.srt"

INSERT_SPACES_BETWEEN_KATAKANA_WORDS = False  # si True -> "スリー ツー ワン"
VERBOSE = True

# ========== Romanisation ==========
_kakasi = kakasi()
_kakasi.setMode("H", "a")
_kakasi.setMode("K", "a")
_kakasi.setMode("J", "a")
_kakasi.setMode("r", "Hepburn")
_conv = _kakasi.getConverter()

def romanize(txt: str) -> str:
    if not txt:
        return ""
    return _conv.do(txt)

def norm_romanji(s: str) -> str:
    return re.sub(r"[^a-z]", "", (s or "").lower())

# ========== segmentation JP en "moras" ==========
SMALLS = set(list("ぁぃぅぇぉゃゅょゎァィゥェォャュョヮ"))
CHOON = "ー"
SOKUON = set(list("っッ"))

def segment_jp(text: str):
    text = (text or "").replace("\u200b", "")
    chunks = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch in "\r\n\t ":
            i += 1
            continue
        # prolongateur
        if ch == CHOON and chunks:
            chunks[-1] += ch
            i += 1
            continue
        # petites voyelles
        if ch in SMALLS and chunks:
            chunks[-1] += ch
            i += 1
            continue
        # sokuon -> attacher au suivant si possible
        if ch in SOKUON and i + 1 < len(text):
            nxt = text[i+1]
            if nxt not in "\r\n\t ":
                chunks.append(ch + nxt)
                i += 2
                continue
            else:
                chunks.append(ch)
                i += 1
                continue
        # normal
        chunks.append(ch)
        i += 1
    return chunks

def chunks_with_romanji(jp_chunks):
    out = []
    for c in jp_chunks:
        r = norm_romanji(romanize(c))
        out.append((c, r))
    return out

# ========== utilitaires ==========
def overlaps(a_start, a_end, b_start, b_end):
    return not (a_end <= b_start or a_start >= b_end)

def build_flat_chunks(subs_jp, consumed_map, start_r, end_r):
    """
    Retourne liste plate [(sub_index, jp_chunk, romanji_norm)] en ordre chrono
    mais **sans** ignorer les déjà consommés - consommation appliquée uniquement
    quand alignement réussi (consumed_map est une structure indiquant combien
    de chunks ont déjà été consommés par sous-titre).
    """
    selected = [j for j in subs_jp if overlaps(j.start.ordinal, j.end.ordinal, start_r, end_r)]
    selected.sort(key=lambda s: (s.start.ordinal, s.index))
    flat = []
    for s in selected:
        all_chunks = segment_jp(s.text)
        used_before = consumed_map[s.index]
        remain = all_chunks[used_before:]
        cr = chunks_with_romanji(remain)
        for (jp_c, r_c) in cr:
            flat.append((s.index, jp_c, r_c))
    return flat, selected

def align_chunks_to_target(chunks_romanji, target_norm):
    """
    Tente d'aligner séquentiellement des chunks (jp_chunk, romanji_norm)
    sur target_norm (chaîne normalisée). Stratégie:
     - concaténer les romanji_norm des chunks et vérifier si, mot à mot,
       l'on peut découper target_norm en segments successifs égaux.
     - retourne (list_of_indices_used, success_bool)
    """
    used = []
    acc = ""
    i = 0
    while i < len(chunks_romanji):
        _, r = chunks_romanji[i]
        if not r:
            # chunk qui ne romanise rien : (kanji qui romanjize mal) -> be conservative -> stop
            # treat as mismatch
            return [], False
        # if adding r keeps acc a prefix of target_norm:
        if target_norm.startswith(acc + r):
            used.append(i)
            acc += r
            if acc == target_norm:
                return used, True
            i += 1
            continue
        else:
            # If not started yet, skip this chunk (may be noise)
            if not used:
                i += 1
                continue
            else:
                # we started but next chunk would break the prefix -> cannot match exactly
                return used, (acc == target_norm)
    return used, (acc == target_norm)

# ========== pipeline principal ==========
def align_files(jp_path, romanji_path, out_path):
    subs_jp = pysrt.open(jp_path, encoding="utf-8")
    subs_romanji = pysrt.open(romanji_path, encoding="utf-8")

    consumed_map = defaultdict(int)   # sub_index -> nb de chunks déjà consommés
    result = []
    stats = {"blocks": 0, "aligned_exact": 0, "aligned_by_words": 0, "fallback_kept": 0}

    for rsub in subs_romanji:
        stats["blocks"] += 1
        start_r = rsub.start.ordinal
        end_r = rsub.end.ordinal
        raw_target = rsub.text or ""
        # break romanji into words (by whitespace/newline) and normalize each
        r_words = [norm_romanji(w) for w in re.split(r"[\s\n]+", raw_target.strip()) if w.strip()]
        target_block_norm = "".join(r_words)

        # build flat chunks from JP overlapping this romanji block
        flat, selected_subs = build_flat_chunks(subs_jp, consumed_map, start_r, end_r)
        # If no flat chunks found (no overlapping JP), fallback empty
        if not flat:
            result.append((rsub.index, rsub.start, rsub.end, ""))
            stats["fallback_kept"] += 1
            continue

        # If romanji target is empty -> nothing to align -> fallback: keep nothing
        if not target_block_norm:
            result.append((rsub.index, rsub.start, rsub.end, ""))
            stats["fallback_kept"] += 1
            continue

        # Try best-effort: align word by word
        used_abs_indices_global = []
        jp_word_pieces = []
        cursor = 0
        chunks_romanji_pair = [(flat[i][1], flat[i][2]) for i in range(len(flat))]  # (jp_piece, romanji_norm)
        # align per romanji word
        for w in r_words:
            # create sublist from cursor
            sub_part = [(flat[i][1], flat[i][2]) for i in range(cursor, len(flat))]
            used_rel, ok = align_chunks_to_target([(jp, r) for (jp, r) in sub_part], w)
            if not used_rel:
                # can't align this word reliably: abort word-by-word strategy
                used_abs_indices_global = []
                jp_word_pieces = []
                break
            # convert relative indices to absolute in flat
            used_abs = [cursor + u for u in used_rel]
            # collect jp pieces
            jp_pieces = [flat[k][1] for k in used_abs]
            jp_word = "".join(jp_pieces)
            jp_word_pieces.append(jp_word)
            used_abs_indices_global.extend(used_abs)
            cursor = used_abs[-1] + 1

        # If word-by-word failed, try block-level exact match (whole target_block_norm)
        if not used_abs_indices_global:
            used_rel_block, ok_block = align_chunks_to_target([(flat[i][1], flat[i][2]) for i in range(len(flat))], target_block_norm)
            if used_rel_block:
                used_abs_indices_global = used_rel_block
                jp_word_pieces = ["".join(flat[k][1] for k in used_abs_indices_global)]
                ok = ok_block
            else:
                ok = False

        # If alignment ok (we matched entire target), commit consumption and produce jp_text
        if used_abs_indices_global and ok:
            # mark consumption per original sub index
            # prepare flat_chunks mapping to original subs
            per_sub_count = defaultdict(int)
            for idx_in_flat in used_abs_indices_global:
                sub_idx = flat[idx_in_flat][0]
                per_sub_count[sub_idx] += 1
            # apply consumption
            for sub_idx, cnt in per_sub_count.items():
                consumed_map[sub_idx] += cnt
            # build final jp text: either words with spaces or concatenated
            if INSERT_SPACES_BETWEEN_KATAKANA_WORDS and len(jp_word_pieces) > 1:
                jp_text_final = " ".join(jp_word_pieces)
            else:
                jp_text_final = "".join(jp_word_pieces)
            result.append((rsub.index, rsub.start, rsub.end, jp_text_final))
            stats["aligned_by_words"] += 1
        else:
            # FALLBACK CONSERVATEUR : on ne consomme rien, on renvoie TOUT le texte JP fusionné dans la plage
            merged = "".join([s.text for s in selected_subs])
            # Nettoyage minime : garder retours de lignes originaux entre subs
            merged_with_newlines = "\n".join([s.text for s in selected_subs])
            result.append((rsub.index, rsub.start, rsub.end, merged_with_newlines))
            stats["fallback_kept"] += 1

    # write out SRT
    with open(out_path, "w", encoding="utf-8") as f:
        for idx, st, et, txt in result:
            f.write(f"{idx}\n")
            f.write(f"{st} --> {et}\n")
            f.write((txt or "") + "\n\n")

    # report
    if VERBOSE:
        total = stats["blocks"]
        print("=== Rapport d'alignement ===")
        print(f"Blocs traités: {total}")
        print(f"Alignés mot-par-mot: {stats['aligned_by_words']}")
        print(f"Fallbacks (texte JP complet gardé): {stats['fallback_kept']}")
        print("============================")

    return out_path

if __name__ == "__main__":
    align_files(JP_PATH, romanji_PATH, OUT_PATH)
