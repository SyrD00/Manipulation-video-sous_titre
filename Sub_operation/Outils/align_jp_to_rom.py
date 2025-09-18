# -*- coding: utf-8 -*-
"""
align_subtitles.py
But: réaligner des sous-titres japonais sur une segmentation
de sous-titres en romanji, pour les formats SRT et ASS.
"""

import re
from collections import defaultdict
from pykakasi import kakasi
from pathlib import Path
import pysubs2

# ========== Réglages ==========
# Assurez-vous que ces chemins d'accès sont corrects
JP_PATH = "C:/Users/babak/Videos/PSO/PSO22.srt"
ROMANJI_PATH = "C:/Users/babak/Videos/PSO/PSO22_rom_sans_song.ass"
OUT_PATH = "C:/Users/babak/Videos/PSO/PSO22_corrige.ass"

INSERT_SPACES_BETWEEN_KATAKANA_WORDS = False
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
SMALLS = set(list("ぁぃぅぇぉゃゅょゎァィゥェォャゅョヮ"))
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
        if ch == CHOON and chunks:
            chunks[-1] += ch
            i += 1
            continue
        if ch in SMALLS and chunks:
            chunks[-1] += ch
            i += 1
            continue
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
    selected_with_indices = [(i, s) for i, s in enumerate(subs_jp) if overlaps(s.start, s.end, start_r, end_r)]
    selected_with_indices.sort(key=lambda item: item[1].start)
    
    selected_subs = [s for i, s in selected_with_indices]
    
    flat = []
    for sub_idx, s in selected_with_indices:
        all_chunks = segment_jp(s.text)
        
        used_before = consumed_map.get(sub_idx, 0)
        remain = all_chunks[used_before:]
        cr = chunks_with_romanji(remain)
        for (jp_c, r_c) in cr:
            flat.append((sub_idx, jp_c, r_c))
            
    return flat, selected_subs

def align_chunks_to_target(chunks_romanji, target_norm):
    used = []
    acc = ""
    i = 0
    while i < len(chunks_romanji):
        _, r = chunks_romanji[i]
        if not r:
            return [], False
        if target_norm.startswith(acc + r):
            used.append(i)
            acc += r
            if acc == target_norm:
                return used, True
            i += 1
            continue
        else:
            if not used:
                i += 1
                continue
            else:
                return used, (acc == target_norm)
    return used, (acc == target_norm)

# ========== pipeline principal ==========
def align_files(jp_path, romanji_path, out_path):
    subs_jp = pysubs2.load(jp_path, encoding="utf-8")
    subs_romanji = pysubs2.load(romanji_path, encoding="utf-8")

    consumed_map = defaultdict(int)
    result = []
    stats = {"blocks": 0, "aligned_exact": 0, "aligned_by_words": 0, "fallback_kept": 0}

    for rsub in subs_romanji:
        stats["blocks"] += 1
        start_r = rsub.start
        end_r = rsub.end
        raw_target = rsub.text or ""
        r_words = [norm_romanji(w) for w in re.split(r"[\s\n]+", raw_target.strip()) if w.strip()]
        target_block_norm = "".join(r_words)

        flat, selected_subs = build_flat_chunks(subs_jp, consumed_map, start_r, end_r)
        
        jp_text_final = ""
        is_aligned = False
        
        # New variable to hold the indices that were successfully used
        final_used_indices = []

        if flat and target_block_norm:
            jp_word_pieces = []
            cursor = 0
            
            used_abs_indices_global = []
            
            for w in r_words:
                # Correct way to pass the list of tuples to align_chunks_to_target
                sub_part = flat[cursor:]
                used_rel, ok = align_chunks_to_target([(item[1], item[2]) for item in sub_part], w)

                if not used_rel:
                    used_abs_indices_global = []
                    jp_word_pieces = []
                    break
                
                used_abs = [cursor + u for u in used_rel]
                jp_pieces = [flat[k][1] for k in used_abs]
                jp_word = "".join(jp_pieces)
                jp_word_pieces.append(jp_word)
                used_abs_indices_global.extend(used_abs)
                cursor = used_abs[-1] + 1
            
            if used_abs_indices_global and all(jp_word_pieces):
                is_aligned = True
                final_used_indices = used_abs_indices_global
                if INSERT_SPACES_BETWEEN_KATAKANA_WORDS and len(jp_word_pieces) > 1:
                    jp_text_final = " ".join(jp_word_pieces)
                else:
                    jp_text_final = "".join(jp_word_pieces)
            
        if not is_aligned and flat:
            used_rel_block, ok_block = align_chunks_to_target([(flat[i][1], flat[i][2]) for i in range(len(flat))], target_block_norm)
            if used_rel_block and ok_block:
                is_aligned = True
                final_used_indices = used_rel_block # Use relative indices from block alignment
                jp_pieces = [flat[k][1] for k in used_rel_block]
                jp_text_final = "".join(jp_pieces)
            else:
                final_used_indices = []

        if is_aligned and final_used_indices:
            per_sub_count = defaultdict(int)
            for idx_in_flat in final_used_indices:
                sub_idx = flat[idx_in_flat][0]
                per_sub_count[sub_idx] += 1
            for sub_idx, cnt in per_sub_count.items():
                consumed_map[sub_idx] += cnt
            stats["aligned_by_words"] += 1
        else:
            merged_text = "\\N".join([s.text for s in selected_subs])
            jp_text_final = merged_text
            stats["fallback_kept"] += 1

        # Construction sécurisée des arguments pour SSAEvent
        event_args = {
            "start": rsub.start,
            "end": rsub.end,
            "text": jp_text_final,
        }
        
        # Utiliser hasattr() pour vérifier si les attributs existent
        if hasattr(rsub, "style"):
            event_args["style"] = rsub.style
        if hasattr(rsub, "alignment"):
            event_args["alignment"] = rsub.alignment
        if hasattr(rsub, "marginl"):
            event_args["marginl"] = rsub.marginl
        if hasattr(rsub, "marginr"):
            event_args["marginr"] = rsub.marginr
        if hasattr(rsub, "marginv"):
            event_args["marginv"] = rsub.marginv
            
        new_sub = pysubs2.SSAEvent(**event_args)
        result.append(new_sub)

    out_subs = pysubs2.SSAFile()
    
    # Copier les styles et informations de l'ASS si applicable
    if subs_romanji.format.lower() == "ass":
        out_subs.styles = subs_romanji.styles
        out_subs.info = subs_romanji.info

    for sub in result:
        out_subs.append(sub)

    out_subs.save(out_path, encoding="utf-8")

    if VERBOSE:
        total = stats["blocks"]
        print("=== Rapport d'alignement ===")
        print(f"Blocs traités: {total}")
        print(f"Alignés mot-par-mot: {stats['aligned_by_words']}")
        print(f"Fallbacks (texte JP complet gardé): {stats['fallback_kept']}")
        print("============================")

    return out_path

if __name__ == "__main__":
    align_files(JP_PATH, ROMANJI_PATH, OUT_PATH)