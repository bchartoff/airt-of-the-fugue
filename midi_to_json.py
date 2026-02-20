#!/usr/bin/env python3
"""Convert Art of the Fugue MIDI files to notes JSON.

Usage:
  python3 midi_to_json.py           # converts piece 1 (default)
  python3 midi_to_json.py --piece 2 # converts piece 2
  python3 midi_to_json.py --all     # converts all pieces
"""
import json
import mido
import sys

# Standard 4-voice SATB definitions (track_index, channel, id, name, color)
VOICES_4 = [
    (1, 0, 0, 'Soprano', '#E85D4A'),
    (2, 1, 1, 'Alto',    '#4A90D9'),
    (3, 2, 2, 'Tenor',   '#27AE60'),
    (4, 3, 3, 'Bass',    '#8E44AD'),
]
VOICES_3 = [
    (1, 0, 0, 'Soprano', '#E85D4A'),
    (2, 1, 1, 'Alto',    '#4A90D9'),
    (3, 2, 2, 'Bass',    '#8E44AD'),
]
VOICES_2 = [
    (1, 0, 0, 'Upper',   '#E85D4A'),
    (2, 1, 1, 'Lower',   '#4A90D9'),
]
VOICES_12 = [
    (1,  0,  0,  'Lead',       '#E85D4A'),
    (2,  1,  1,  'Pad',        '#4A90D9'),
    (3,  2,  2,  'Arp',        '#27AE60'),
    (4,  3,  3,  'Sub Bass',   '#8E44AD'),
    (5,  4,  4,  'Pluck',      '#E8A04A'),
    (6,  5,  5,  'Stab',       '#D94A7B'),
    (7,  6,  6,  'Hi-Hat',     '#7F8C8D'),
    (8,  7,  7,  'Kick',       '#2C3E50'),
    (9,  8,  8,  'Clap',       '#C0392B'),
    (10, 9,  9,  'FX Rise',    '#1ABC9C'),
    (11, 10, 10, 'Acid',       '#F39C12'),
    (12, 11, 11, 'Supersaw',   '#9B59B6'),
]

# ── Piece definitions ──
PIECES = {
    1:  {'midi': 'kunst_der_fuge_01_(c)simonetto.mid', 'output': 'notes_01.json',  'title': 'Contrapunctus I',    'number': 'I',    'voices': VOICES_4},
    2:  {'midi': 'kunst_der_fuge_02_mutopia.mid',       'output': 'notes_02.json',  'title': 'Contrapunctus II',   'number': 'II',   'voices': VOICES_4},
    3:  {'midi': 'kunst_der_fuge_iii_mutopia.mid',      'output': 'notes_03.json',  'title': 'Contrapunctus III',  'number': 'III',  'voices': VOICES_4},
    4:  {'midi': 'kunst_der_fuge_iv_mutopia.mid',       'output': 'notes_04.json',  'title': 'Contrapunctus IV',   'number': 'IV',   'voices': VOICES_4},
    5:  {'midi': 'kunst_der_fuge_v_mutopia.mid',        'output': 'notes_05.json',  'title': 'Contrapunctus V',    'number': 'V',    'voices': VOICES_4},
    6:  {'midi': 'kunst_der_fuge_vi_mutopia.mid',       'output': 'notes_06.json',  'title': 'Contrapunctus VI',   'number': 'VI',   'voices': VOICES_4},
    7:  {'midi': 'kunst_der_fuge_vii_mutopia.mid',      'output': 'notes_07.json',  'title': 'Contrapunctus VII',  'number': 'VII',  'voices': VOICES_4},
    8:  {'midi': 'kunst_der_fuge_viii_mutopia.mid',     'output': 'notes_08.json',  'title': 'Contrapunctus VIII', 'number': 'VIII', 'voices': VOICES_3},
    9:  {'midi': 'kunst_der_fuge_ix_mutopia.mid',       'output': 'notes_09.json',  'title': 'Contrapunctus IX',   'number': 'IX',   'voices': VOICES_4},
    10: {'midi': 'kunst_der_fuge_x_mutopia.mid',        'output': 'notes_10.json',  'title': 'Contrapunctus X',    'number': 'X',    'voices': VOICES_4},
    11: {'midi': 'kunst_der_fuge_xi_mutopia.mid',       'output': 'notes_11.json',  'title': 'Contrapunctus XI',   'number': 'XI',   'voices': VOICES_4},
    12: {'midi': 'kunst_der_fuge_xii_mutopia.mid',      'output': 'notes_12.json',  'title': 'Contrapunctus XII',  'number': 'XII',  'voices': VOICES_2},
    13: {'midi': 'kunst_der_fuge_xiv_mutopia.mid',      'output': 'notes_14.json',  'title': 'Contrapunctus XIV',  'number': 'XIV',  'voices': VOICES_2},
    14: {'midi': 'contrapunctus_xv.mid',                'output': 'notes_15.json',  'title': 'Contrapunctus XV',   'number': 'XV*',  'voices': VOICES_12},
}

# ── Subject interval patterns ──
#
# Bach's subject exists in two notated forms across this MIDI collection:
#
# FORM A — Unornamented (8 notes, Contrapunctus I, II, IX):
#   Subject: D  A  F  D  C# D  E  F   → [+7,−4,−3,−1,+1,+2,+1]
#   Answer:  A  D  C  A  G# A  B  C   → [+5,−2,−3,−1,+1,+2,+1]
#
# FORM B — Ornamented (9 notes, most other contrapunctuses):
#   The skip D→A is filled in with G, making D→A→G→F→E→D→C#→D→E→F
#   Subject: D  A  G  F  E  D  C# D  E  F  → [+7,−2,−2,−1,−2,−1,+1,+2,+1] (wait — 9 intervals for 10 notes)
#   Actual 9-note form observed (Bass Contrapunctus VI):
#   D  A  G  F  E  D  C# D  E  → [+7,−2,−2,−1,−2,−1,+1,+2] ... check below
#
# From MIDI inspection (Contrapunctus VI Bass, starts D3):
#   Intervals: [7, -2, -2, -1, -2, -1, 1, 2, 1, 2, -2, ...]
#   First 8 intervals = [7, -2, -2, -1, -2, -1, 1, 2]  → 9 notes D A G F E D C# D E
#   That's 9 notes, so we match 9-note patterns:
#
# 9-note FORM B patterns:
#   Subject (starts on D): [+7,−2,−2,−1,−2,−1,+1,+2]
#   Answer  (starts on A): [+5,−2,−1,−2,−1,−2,+1,+2]  (tonal adjustment in key of D minor)
#   (Answer observed: A D C B♭ A G# A B C → [+5,−2,−2,−1,−1,+1,+2] ... need to verify)
#
# Inversion forms (Contrapunctus III, IV, XIV):
#   Inv. answer on D (9-note): [−5,+3,+4,+1,−1,−2,−1]   ← already verified (8 notes, Form A inv)
#   Inv. subject on A (9-note): [−7,+3,+4,+1,−1,−2,−2]   ← already verified (8 notes, Form A inv)
#
# NOTE: Form B subject has 9 notes → 8 intervals. We match windows of 9 consecutive notes.

# Form A (8 notes → 7 intervals)
SUBJECT_INTERVALS_A = [7, -4, -3, -1, 1, 2, 1]    # unornamented subject (D→A→F→D→C#→D→E→F)
ANSWER_INTERVALS_A  = [5, -2, -3, -1, 1, 2, 1]    # unornamented answer  (A→D→C→A→G#→A→B→C)

# Form B (9 notes → 8 intervals) — ornamented, observed in MIDI
SUBJECT_INTERVALS_B = [7, -2, -2, -1, -2, -1, 1, 2]   # ornamented subject (D→A→G→F→E→D→C#→D→E)
ANSWER_INTERVALS_B  = [5, -2, -1, -2, -1, -2, 1, 2]   # ornamented answer  (A→E→D→C→B→A→G#→A→B)

# Inversion of Form A (Contrapunctus III/IV — tonal inversion, not real):
# Tonal inv. answer on D: [-5,+3,+4,+1,-1,-2,-1]
# Tonal inv. subject on A: [-7,+3,+4,+1,-1,-2,-2]
SUBJECT_INV_A_SUBJ  = [-5, 3, 4, 1, -1, -2, -1]   # tonal inv. answer starting on D
SUBJECT_INV_A_ANS   = [-7, 3, 4, 1, -1, -2, -2]   # tonal inv. subject starting on A
# Real inversion of Form A (fallback):
SUBJECT_INV_A_REAL_SUBJ = [-7, 4, 3, 1, -1, -2, -1]
SUBJECT_INV_A_REAL_ANS  = [-5, 2, 3, 1, -1, -2, -1]

# Inversion of Form B (9-note):
# Real inversion (exact negation of Form B intervals):
SUBJECT_INV_B_SUBJ       = [-7, 2, 2, 1, 2, 1, -1, -2]   # real inv. subj (confirmed C VI Tenor m26)
SUBJECT_INV_B_ANS        = [-5, 2, 1, 2, 1, 2, -1, -2]   # real inv. answer
# Tonal inversion (adjusted to stay in D minor, observed in C V):
SUBJECT_TONAL_INV_B_SUBJ = [-7, 2, 1, 2, 2, 1, -1, -2]   # tonal inv. subj (C V Alto m1, C V Sop m69)
SUBJECT_TONAL_INV_B_ANS  = [-5, 2, 1, 2, 2, 1, -1, -2]   # tonal inv. answer (C V Sop m17)

# Mirror fugue (Contrapunctus XII) — subject appears strictly inverted:
# Upper voice opens: [-7,-1,1,2,-2,2,1,...] — this is the inversion presented as the primary voice
# We treat these the same as subject_inv entries.

# ── Contrapunctus IX: main subject with scalar elaboration ──
# The descending scale D→D(8va)→C#→B→A→G→F→E→D fills in the subject's
# opening leap with stepwise passing tones, then converges on the standard
# tail (D→C#→D→E→F).  The structural endpoints map to main-subject positions:
#   pos 0: D, pos 1: D(8va) (octave variant of the fifth), scale fills to
#   pos 3: D, then 4: C#, 5: D, 6: E, 7: F — identical to main subject tail.
# These are tagged as 'subject' (not a separate theme) with the warm palette.
SUBJECT_C9_SCALE         = [12, -1, -2, -2, -2, -2, -1, -2]   # subject on D (C IX Alto m1)
SUBJECT_C9_SCALE_ANSWER  = [12, -1, -1, -2, -2, -2, -1, -2]   # answer on A (tonal adj.)

# ALL patterns with their note-count (8 or 9), motif label
# Format: (intervals_list, notes_in_window, motif_label, description)
SUBJECT_PATTERNS = [
    (SUBJECT_INTERVALS_A,       8, 'subject',     'unornamented rectus (Form A)'),
    (ANSWER_INTERVALS_A,        8, 'subject',     'unornamented answer (Form A)'),
    (SUBJECT_INTERVALS_B,       9, 'subject',     'ornamented rectus (Form B)'),
    (ANSWER_INTERVALS_B,        9, 'subject',     'ornamented answer (Form B)'),
    (SUBJECT_INV_A_SUBJ,        8, 'subject_inv', 'tonal inv. Form A (D-entry)'),
    (SUBJECT_INV_A_ANS,         8, 'subject_inv', 'tonal inv. Form A (A-entry)'),
    (SUBJECT_INV_A_REAL_SUBJ,   8, 'subject_inv', 'real inv. Form A (rectus)'),
    (SUBJECT_INV_A_REAL_ANS,    8, 'subject_inv', 'real inv. Form A (answer)'),
    (SUBJECT_INV_B_SUBJ,             9, 'subject_inv', 'real inv. Form B (rectus)'),
    (SUBJECT_INV_B_ANS,              9, 'subject_inv', 'real inv. Form B (answer)'),
    (SUBJECT_TONAL_INV_B_SUBJ,       9, 'subject_inv', 'tonal inv. Form B (rectus)'),
    (SUBJECT_TONAL_INV_B_ANS,        9, 'subject_inv', 'tonal inv. Form B (answer)'),
    (SUBJECT_C9_SCALE,          9, 'subject',     'C IX scalar elaboration of subject (D)'),
    (SUBJECT_C9_SCALE_ANSWER,   9, 'subject',     'C IX scalar elaboration of answer (A)'),
]

# Tail = last 5 notes of Form A subject: D C# D E F → [-1,+1,+2,+1]
TAIL_INTERVALS = [-1, 1, 2, 1]
TAIL_INV       = [1, -1, -2, -1]   # inversion of tail

# ── BACH motif (Bb-A-C-B♮) ──
# Intervals: [-1, +3, -1] (semitone down, minor 3rd up, semitone down)
# 4 notes, appears across many contrapunctuses (10 total occurrences).
# Exact pitch class: Bb=10, A=9, C=0, B=11 (pitch % 12).
# We tag all transpositions; exact Bb-A-C-B gets a special flag.
BACH_INTERVALS = [-1, 3, -1]
BACH_PITCH_CLASSES = [10, 9, 0, 11]  # Bb, A, C, B♮

# ── Contrapunctus X "Enigmatic Subject" ──
# Two 3-note cells, each: chromatic approach → target → perfect 4th leap.
# Cell type A: [+1, -5] (semitone up, P4 down)
# Cell type B: [-1, +5] (semitone down, P4 up)
# Full subject (Form 1): cell A + gap + cell B → [+1, -5, +8, -1, +5]
# Full subject (Form 2): cell B + gap + cell A → [-1, +5, -8, +1, -5] (retrograde)
# The gap is typically ±8 (minor 6th) but may range ±6 to ±9.
ENIGMATIC_CELL_A = [1, -5]    # semitone up, P4 down
ENIGMATIC_CELL_B = [-1, 5]    # semitone down, P4 up
# Also accept tritone (±6) and P5 (±7) leaps as variant cells
ENIGMATIC_CELL_A_VARIANTS = [[1, -5], [1, -6], [1, -7]]
ENIGMATIC_CELL_B_VARIANTS = [[-1, 5], [-1, 6], [-1, 7]]

# Tail B = last 5 notes of Form B subject: D C# D E (F) — same tail as Form A
# (the ornamented form converges to the same tail)

# Head = first 5 notes of Form A subject: D A F D C# → [+7,-4,-3,-1]
HEAD_INTERVALS     = [7, -4, -3, -1]
HEAD_ANS_INTERVALS = [5, -2, -3, -1]

# Head B = first 5 notes of Form B subject: D A G F E → [+7,-2,-2,-1]
HEAD_B_INTERVALS     = [7, -2, -2, -1]
HEAD_B_ANS_INTERVALS = [5, -2, -1, -2]

# Head inversion forms
HEAD_INV_INTERVALS             = [-7, 4, 3, 1]
HEAD_ANS_INV_INTERVALS         = [-5, 2, 3, 1]
HEAD_TONAL_INV_SUBJ            = [-5, 3, 4, 1]
HEAD_TONAL_INV_ANS             = [-7, 3, 4, 1]
HEAD_B_INV_INTERVALS           = [-7, 2, 2, 1]
HEAD_B_ANS_INV_INTERVALS       = [-5, 2, 1, 2]
HEAD_B_TONAL_INV_SUBJ          = [-7, 2, 1, 2]   # tonal inv Form B subject (C III/IV soprano/tenor entries)


def flexible_match(voice_notes, start_idx, pattern, max_skips=4, min_dur=0.4):
    """Match a subject interval pattern allowing grace-note skips.

    Walks forward from start_idx, matching each expected interval in *pattern*.
    If the next note doesn't produce the expected interval **and** it is short
    (duration < *min_dur*), skip it (treat as grace note) and try the note after.
    Multiple consecutive grace notes may be skipped (up to *max_skips* total).

    Returns ``(matched_indices, skipped_indices)`` on success, or ``None``.
    *matched_indices* contains the indices of the structural (subject-position)
    notes; *skipped_indices* contains the grace notes that were skipped.
    """
    n_intervals = len(pattern)
    count = len(voice_notes)
    matched = [start_idx]
    skipped = []
    j = start_idx

    for p in range(n_intervals):
        j += 1
        if j >= count:
            return None

        actual = voice_notes[j]['pitch'] - voice_notes[matched[-1]]['pitch']

        if actual == pattern[p]:
            matched.append(j)
        else:
            # Try skipping one or more consecutive short notes (grace notes)
            found = False
            while (voice_notes[j]['duration'] < min_dur
                   and len(skipped) < max_skips):
                skipped.append(j)
                j += 1
                if j >= count:
                    return None
                actual = voice_notes[j]['pitch'] - voice_notes[matched[-1]]['pitch']
                if actual == pattern[p]:
                    matched.append(j)
                    found = True
                    break
            if not found:
                return None

    return matched, skipped


def detect_stretto_and_combinations(notes_by_voice):
    """Post-processing pass: detect stretto entries and subject combinations.

    Stretto = when a new subject entry in one voice begins before the previous
    entry in another voice has finished. We identify overlapping subject/subject_inv
    entries across voices.

    Subject combination = when 2+ different motif types sound simultaneously.
    This is critical for the triple fugues (C VIII, XI) where multiple subjects
    are combined.

    Adds to each note:
      stretto: True if this note is part of an overlapping subject entry
      stretto_voices: number of voices in stretto at this point (0 if not stretto)
      combination: list of distinct motif types sounding simultaneously across voices
    """
    # Collect all subject/subject_inv entry spans: (voice_id, start_time, end_time, motif_type)
    entries = []
    for voice_id, vnotes in notes_by_voice.items():
        i = 0
        while i < len(vnotes):
            n = vnotes[i]
            if n['motif'] in ('subject', 'subject_inv') and n['motif_pos'] == 0:
                # Found start of an entry — find its end
                entry_motif = n['motif']
                start_time = n['start']
                end_time = n['start'] + n['duration']
                j = i + 1
                while j < len(vnotes) and vnotes[j]['motif'] == entry_motif and vnotes[j]['motif_pos'] > 0:
                    end_time = max(end_time, vnotes[j]['start'] + vnotes[j]['duration'])
                    j += 1
                entries.append((voice_id, start_time, end_time, entry_motif))
                i = j
            else:
                i += 1

    # Detect stretto: find overlapping entries in DIFFERENT voices
    stretto_spans = []  # list of (start, end, voice_count, overlapping_entry_indices)
    for idx_a, (va, sa, ea, ma) in enumerate(entries):
        overlapping = [idx_a]
        for idx_b, (vb, sb, eb, mb) in enumerate(entries):
            if idx_b == idx_a:
                continue
            if va == vb:
                continue  # same voice doesn't count
            # Check temporal overlap
            if sb < ea and sa < eb:
                overlapping.append(idx_b)
        if len(overlapping) > 1:
            # This entry overlaps with at least one other
            all_starts = [entries[i][1] for i in overlapping]
            all_ends = [entries[i][2] for i in overlapping]
            span_start = max(all_starts)  # overlap begins when last entry starts
            span_end = min(all_ends)      # overlap ends when first entry finishes
            if span_start < span_end:
                voices_in_stretto = len(set(entries[i][0] for i in overlapping))
                stretto_spans.append((span_start, span_end, voices_in_stretto))

    # Mark notes that fall within stretto spans
    for voice_id, vnotes in notes_by_voice.items():
        for n in vnotes:
            n['stretto'] = False
            n['stretto_voices'] = 0
            n['combination'] = []

            if n['motif'] in ('subject', 'subject_inv'):
                note_mid = n['start'] + n['duration'] / 2
                for (ss, se, sv) in stretto_spans:
                    if ss <= note_mid <= se:
                        n['stretto'] = True
                        n['stretto_voices'] = max(n['stretto_voices'], sv)
                        break

    # Detect subject combinations: at each moment, what distinct motif types are sounding?
    # Build time slices from all note boundaries
    all_notes_flat = []
    for voice_id, vnotes in notes_by_voice.items():
        for n in vnotes:
            if n['motif'] in ('subject', 'subject_inv', 'bach', 'bach_transposed', 'enigmatic'):
                all_notes_flat.append(n)

    # For each note, find what other motif types are active at its midpoint
    for voice_id, vnotes in notes_by_voice.items():
        for n in vnotes:
            if not n['motif']:
                continue
            t_mid = n['start'] + n['duration'] / 2
            active_motifs = set()
            for other in all_notes_flat:
                if other['start'] <= t_mid <= other['start'] + other['duration']:
                    active_motifs.add(other['motif'])
            # Normalize: group subject variants
            combo = set()
            for m in active_motifs:
                if m in ('subject', 'subject_inv'):
                    combo.add('subject_family')
                elif m in ('bach', 'bach_transposed'):
                    combo.add('bach_family')
                else:
                    combo.add(m)
            n['combination'] = sorted(combo) if len(combo) > 1 else []


def detect_augmentation_diminution(notes_by_voice):
    """Detect subject entries played at augmented (2×) or diminished (½×) rhythm.

    Augmentation: the subject's interval pattern is preserved but each note is
    roughly 2× the normal duration. Diminution: each note is roughly ½×.

    We compare the rhythm (durations) of each detected subject entry against the
    typical rhythm of the first subject entry found. If the ratio is consistently
    ~2.0 that's augmentation; ~0.5 is diminution.

    Adds to each note:
      aug_dim: 'augmentation', 'diminution', or '' (normal)
      rhythm_ratio: float, average duration ratio vs reference entry
    """
    # First, collect all subject entries with their note durations
    # Reference: the first complete subject entry we find
    ref_durations = None
    all_entries = []  # list of (voice_id, start_idx, end_idx, durations[])

    for voice_id, vnotes in notes_by_voice.items():
        i = 0
        while i < len(vnotes):
            n = vnotes[i]
            if n['motif'] in ('subject', 'subject_inv') and n['motif_pos'] == 0:
                entry_motif = n['motif']
                entry_notes = [n]
                j = i + 1
                while (j < len(vnotes) and vnotes[j]['motif'] == entry_motif
                       and vnotes[j]['motif_pos'] > 0):
                    entry_notes.append(vnotes[j])
                    j += 1
                durs = [en['duration'] for en in entry_notes]
                all_entries.append((voice_id, i, j, durs, entry_notes))
                if ref_durations is None and len(durs) >= 7:
                    ref_durations = durs
                i = j
            else:
                i += 1

    if ref_durations is None or len(all_entries) < 2:
        # Not enough data — initialize fields and return
        for vnotes in notes_by_voice.values():
            for n in vnotes:
                n['aug_dim'] = ''
                n['rhythm_ratio'] = 1.0
        return

    ref_avg = sum(ref_durations) / len(ref_durations)

    for voice_id, si, ei, durs, entry_notes in all_entries:
        if len(durs) < 3:
            for en in entry_notes:
                en['aug_dim'] = ''
                en['rhythm_ratio'] = 1.0
            continue

        entry_avg = sum(durs) / len(durs)
        if ref_avg > 0:
            ratio = entry_avg / ref_avg
        else:
            ratio = 1.0

        label = ''
        if ratio >= 1.7:
            label = 'augmentation'
        elif ratio <= 0.6:
            label = 'diminution'

        for en in entry_notes:
            en['aug_dim'] = label
            en['rhythm_ratio'] = round(ratio, 2)

    # Initialize any notes not part of an entry
    for vnotes in notes_by_voice.values():
        for n in vnotes:
            if 'aug_dim' not in n:
                n['aug_dim'] = ''
                n['rhythm_ratio'] = 1.0


def compute_chromatic_density(all_notes, total_measures):
    """Compute per-measure chromatic density.

    Chromatic density = fraction of intervals in each measure that are
    semitones (±1). Higher density indicates more chromatic writing,
    which Bach uses to build tension.

    Returns a list of dicts: [{measure, density, chromatic_count, interval_count}]
    Also tags each note with its measure's chromatic_density.
    """
    from collections import defaultdict

    # Group notes by voice and measure
    voice_measure_notes = defaultdict(lambda: defaultdict(list))
    for n in all_notes:
        voice_measure_notes[n['voice']][n['measure']].append(n)

    # Sort each voice-measure group by start time
    for v in voice_measure_notes:
        for m in voice_measure_notes[v]:
            voice_measure_notes[v][m].sort(key=lambda n: n['start'])

    # Count chromatic intervals per measure
    measure_data = {}
    for m in range(1, total_measures + 1):
        chromatic = 0
        total_intervals = 0
        for v in voice_measure_notes:
            notes = voice_measure_notes[v].get(m, [])
            for i in range(len(notes) - 1):
                interval = abs(notes[i + 1]['pitch'] - notes[i]['pitch'])
                if interval > 0:  # skip repeated notes
                    total_intervals += 1
                    if interval == 1:
                        chromatic += 1

        density = chromatic / total_intervals if total_intervals > 0 else 0.0
        measure_data[m] = {
            'measure': m,
            'density': round(density, 3),
            'chromatic_count': chromatic,
            'interval_count': total_intervals,
        }

    # Tag each note with its measure's density
    for n in all_notes:
        md = measure_data.get(n['measure'])
        n['chromatic_density'] = md['density'] if md else 0.0

    return list(measure_data.values())


def tag_motifs(notes_by_voice):
    """Tag each note with motif info.

    Sets fields on each note:
      subject_pos: 0–7 for full subject/answer, else -1
      motif: string label — 'subject', 'tail', 'tail_inv', 'head', or ''
      motif_pos: position within the matched motif (0-indexed), or -1
      best_pos: 0–7, which subject position this note most resembles
      similarity: 0.0–1.0, how confident the match is
    """
    # ── All intervals in the subject (both forms) for reference ──
    # Subject positions 0–7 have these intervals:
    #   Before pos:  [-, +7, -4, -3, -1, +1, +2, +1]  (- means first note)
    #   After pos:   [+7, -4, -3, -1, +1, +2, +1, -]  (- means last note)
    # Answer form:
    #   Before pos:  [-, +5, -2, -3, -1, +1, +2, +1]
    #   After pos:   [+5, -2, -3, -1, +1, +2, +1, -]

    # For each subject position, define the characteristic intervals
    # (interval_before, interval_after) for both subject and answer forms
    # None means no interval (edge of subject)
    SUBJ_INT = [7, -4, -3, -1, 1, 2, 1]  # intervals between consecutive positions
    ANS_INT  = [5, -2, -3, -1, 1, 2, 1]

    for voice_notes in notes_by_voice.values():
        count = len(voice_notes)

        # Initialize all notes
        for n in voice_notes:
            n['subject_pos'] = -1
            n['motif'] = ''
            n['motif_pos'] = -1
            n['best_pos'] = 0
            n['similarity'] = 0.0

        # Pass 1: full subject/answer — transposition-invariant, variable window size.
        # Matches any N-note run (N=8 for Form A, N=9 for Form B) whose interval pattern
        # equals any subject-family pattern, regardless of starting pitch.
        for i in range(count):
            for pattern, n_notes, motif_label, _ in SUBJECT_PATTERNS:
                if i + n_notes > count:
                    continue
                seg = [voice_notes[i + j]['pitch'] for j in range(n_notes)]
                seg_int = [seg[j + 1] - seg[j] for j in range(n_notes - 1)]
                if seg_int == pattern:
                    # Don't overwrite a run that's already fully tagged by a previous match
                    if all(voice_notes[i + j]['motif'] == '' for j in range(n_notes)):
                        for pos in range(n_notes):
                            voice_notes[i + pos]['subject_pos'] = pos
                            voice_notes[i + pos]['motif'] = motif_label
                            voice_notes[i + pos]['motif_pos'] = pos
                        break  # don't double-tag same starting note

        # Pass 1b: grace-note-tolerant full subject/answer matching.
        # Re-scans using flexible_match() which can skip short-duration notes
        # (ornamental grace notes) to find the structural subject underneath.
        # Only fires when at least one grace note is skipped (exact matches
        # were already found in Pass 1).
        for i in range(count):
            if voice_notes[i]['motif'] != '':
                continue  # already tagged
            for pattern, n_notes, motif_label, _ in SUBJECT_PATTERNS:
                result = flexible_match(voice_notes, i, pattern)
                if result is None:
                    continue
                matched, skipped = result
                if len(skipped) == 0:
                    continue  # exact match — handled by Pass 1
                all_indices = matched + skipped
                if not all(voice_notes[idx]['motif'] == '' for idx in all_indices):
                    continue  # overlaps with an existing tag
                # Tag the structural (subject-position) notes
                for pos, idx in enumerate(matched):
                    voice_notes[idx]['subject_pos'] = pos
                    voice_notes[idx]['motif'] = motif_label
                    voice_notes[idx]['motif_pos'] = pos
                # Tag grace notes with the same motif; assign motif_pos
                # from the preceding structural note so they color correctly.
                for idx in skipped:
                    # Find the structural note just before this grace note
                    preceding_pos = 0
                    for pos, m_idx in enumerate(matched):
                        if m_idx < idx:
                            preceding_pos = pos
                        else:
                            break
                    voice_notes[idx]['motif'] = motif_label
                    voice_notes[idx]['motif_pos'] = preceding_pos
                break  # don't double-tag same starting note

        # Pass 2: tail fragment (5 notes, only tag notes not already tagged)
        for i in range(count - 4):
            seg = [voice_notes[i + j]['pitch'] for j in range(5)]
            seg_int = [seg[j + 1] - seg[j] for j in range(4)]
            if seg_int == TAIL_INTERVALS:
                if all(voice_notes[i + j]['motif'] == '' for j in range(5)):
                    for pos in range(5):
                        voice_notes[i + pos]['motif'] = 'tail'
                        voice_notes[i + pos]['motif_pos'] = pos + 3

        # Pass 3: inverted tail (5 notes)
        for i in range(count - 4):
            seg = [voice_notes[i + j]['pitch'] for j in range(5)]
            seg_int = [seg[j + 1] - seg[j] for j in range(4)]
            if seg_int == TAIL_INV:
                if all(voice_notes[i + j]['motif'] == '' for j in range(5)):
                    for pos in range(5):
                        voice_notes[i + pos]['motif'] = 'tail_inv'
                        voice_notes[i + pos]['motif_pos'] = pos

        # Pass 4: head fragment (5 notes) outside of full subject
        # Catches Form A and Form B head patterns, plus all inversion forms.
        # The overlap check only requires the first 4 notes to be untagged —
        # the 5th note may already belong to a tail/tail_inv from another pass.
        HEAD_RECTUS = (HEAD_INTERVALS, HEAD_ANS_INTERVALS, HEAD_B_INTERVALS, HEAD_B_ANS_INTERVALS)
        HEAD_INV    = (HEAD_INV_INTERVALS, HEAD_ANS_INV_INTERVALS,
                       HEAD_TONAL_INV_SUBJ, HEAD_TONAL_INV_ANS,
                       HEAD_B_INV_INTERVALS, HEAD_B_ANS_INV_INTERVALS,
                       HEAD_B_TONAL_INV_SUBJ)
        for i in range(count - 4):
            seg = [voice_notes[i + j]['pitch'] for j in range(5)]
            seg_int = [seg[j + 1] - seg[j] for j in range(4)]
            if seg_int in HEAD_RECTUS:
                if all(voice_notes[i + j]['motif'] == '' for j in range(4)):
                    for pos in range(5):
                        if voice_notes[i + pos]['motif'] == '':
                            voice_notes[i + pos]['motif'] = 'head'
                            voice_notes[i + pos]['motif_pos'] = pos
            elif seg_int in HEAD_INV:
                if all(voice_notes[i + j]['motif'] == '' for j in range(4)):
                    for pos in range(5):
                        if voice_notes[i + pos]['motif'] == '':
                            voice_notes[i + pos]['motif'] = 'head_inv'
                            voice_notes[i + pos]['motif_pos'] = pos

        # ── Pass 5: BACH motif (4 notes, intervals [-1, +3, -1]) ──
        # Tags as 'bach' (exact Bb-A-C-B pitch class) or 'bach_transposed'.
        # Only tags notes not already claimed by a higher-priority motif.
        for i in range(count - 3):
            seg = [voice_notes[i + j]['pitch'] for j in range(4)]
            seg_int = [seg[j + 1] - seg[j] for j in range(3)]
            if seg_int == BACH_INTERVALS:
                if all(voice_notes[i + j]['motif'] == '' for j in range(4)):
                    pcs = [seg[j] % 12 for j in range(4)]
                    is_exact = (pcs == BACH_PITCH_CLASSES)
                    label = 'bach' if is_exact else 'bach_transposed'
                    for pos in range(4):
                        voice_notes[i + pos]['motif'] = label
                        voice_notes[i + pos]['motif_pos'] = pos

        # ── Pass 5b: Contrapunctus X enigmatic subject ──
        # Detect paired cells: [+1,-5,gap,-1,+5] or [-1,+5,gap,+1,-5]
        # where gap is ±6 to ±9 (minor 6th to major 6th range).
        # Also detect single cells [+1,-5] or [-1,+5] standalone.
        #
        # Paired cells (6 notes = 5 intervals):
        for i in range(count - 5):
            seg = [voice_notes[i + j]['pitch'] for j in range(6)]
            seg_int = [seg[j + 1] - seg[j] for j in range(5)]
            # Check Form 1: cell A + gap + cell B
            if (seg_int[0:2] in ENIGMATIC_CELL_A_VARIANTS
                    and 6 <= abs(seg_int[2]) <= 9
                    and seg_int[3:5] in ENIGMATIC_CELL_B_VARIANTS):
                if all(voice_notes[i + j]['motif'] == '' for j in range(6)):
                    for pos in range(6):
                        voice_notes[i + pos]['motif'] = 'enigmatic'
                        voice_notes[i + pos]['motif_pos'] = pos
                    continue
            # Check Form 2: cell B + gap + cell A
            if (seg_int[0:2] in ENIGMATIC_CELL_B_VARIANTS
                    and 6 <= abs(seg_int[2]) <= 9
                    and seg_int[3:5] in ENIGMATIC_CELL_A_VARIANTS):
                if all(voice_notes[i + j]['motif'] == '' for j in range(6)):
                    for pos in range(6):
                        voice_notes[i + pos]['motif'] = 'enigmatic'
                        voice_notes[i + pos]['motif_pos'] = pos
                    continue

        # Single enigmatic cells (3 notes, only if not part of a paired match):
        for i in range(count - 2):
            seg = [voice_notes[i + j]['pitch'] for j in range(3)]
            seg_int = [seg[j + 1] - seg[j] for j in range(2)]
            if seg_int in ENIGMATIC_CELL_A_VARIANTS or seg_int in ENIGMATIC_CELL_B_VARIANTS:
                if all(voice_notes[i + j]['motif'] == '' for j in range(3)):
                    for pos in range(3):
                        voice_notes[i + pos]['motif'] = 'enigmatic_cell'
                        voice_notes[i + pos]['motif_pos'] = pos

        # ── Pass 6: Fuzzy similarity scoring for ALL notes ──
        # For each note, compute how well its local interval context
        # matches each of the 8 subject positions.
        #
        # We look at a window of intervals around each note (up to 3 before,
        # 3 after) and compare against what the subject has at each position.
        # This gives every note a "best_pos" and "similarity" score.

        # Build interval list for this voice
        intervals = []
        for j in range(count - 1):
            intervals.append(voice_notes[j + 1]['pitch'] - voice_notes[j]['pitch'])
        # intervals[j] = interval from note j to note j+1

        # For each subject position p (0–7), we know the intervals around it:
        #   subject form: SUBJ_INT[p-1] before, SUBJ_INT[p] after
        #   answer form:  ANS_INT[p-1] before, ANS_INT[p] after
        # We compare using a window of up to 3 intervals before and after.

        def interval_similarity(actual, expected_subj, expected_ans):
            """Score how well an actual interval matches expected subject/answer interval.
            Returns 0.0–1.0. Exact match = 1.0, close = partial credit."""
            if actual is None or (expected_subj is None and expected_ans is None):
                return 0.0
            best = 0.0
            for exp in [expected_subj, expected_ans]:
                if exp is None:
                    continue
                diff = abs(actual - exp)
                if diff == 0:
                    score = 1.0
                elif diff == 1:
                    score = 0.5  # off by a semitone
                elif diff == 2:
                    score = 0.25  # off by a whole tone
                elif diff <= 4:
                    score = 0.1
                else:
                    score = 0.0
                best = max(best, score)
            return best

        for i in range(count):
            # If this note already has an exact motif, set similarity=1.0 and use motif_pos
            if voice_notes[i]['motif'] != '':
                mp = voice_notes[i]['motif_pos']
                voice_notes[i]['best_pos'] = mp if 0 <= mp < 8 else 0
                voice_notes[i]['similarity'] = 1.0
                continue

            # Get intervals around this note
            # intervals[i-1] = interval before this note (from note i-1 to note i)
            # intervals[i]   = interval after this note (from note i to note i+1)
            int_before = []  # up to 3 intervals before
            int_after = []   # up to 3 intervals after
            for k in range(1, 4):
                if i - k >= 0:
                    int_before.append(intervals[i - k])
                else:
                    int_before.append(None)
            for k in range(3):
                if i + k < len(intervals):
                    int_after.append(intervals[i + k])
                else:
                    int_after.append(None)

            best_score = 0.0
            best_p = 0

            for p in range(8):
                score = 0.0
                weight_total = 0.0

                # Compare intervals BEFORE this note (looking backwards)
                # At subject position p, the intervals before are:
                #   1 before: SUBJ_INT[p-1], 2 before: SUBJ_INT[p-2], etc.
                for k in range(3):
                    idx = p - 1 - k  # index into subject intervals array
                    w = [1.0, 0.5, 0.25][k]  # closer intervals matter more
                    weight_total += w
                    if idx >= 0:
                        s_exp = SUBJ_INT[idx]
                        a_exp = ANS_INT[idx]
                        score += w * interval_similarity(int_before[k], s_exp, a_exp)

                # Compare intervals AFTER this note
                # At subject position p, the intervals after are:
                #   1 after: SUBJ_INT[p], 2 after: SUBJ_INT[p+1], etc.
                for k in range(3):
                    idx = p + k  # index into subject intervals array
                    w = [1.0, 0.5, 0.25][k]
                    weight_total += w
                    if idx < 7:
                        s_exp = SUBJ_INT[idx]
                        a_exp = ANS_INT[idx]
                        score += w * interval_similarity(int_after[k], s_exp, a_exp)

                # Normalize
                if weight_total > 0:
                    score /= weight_total

                if score > best_score:
                    best_score = score
                    best_p = p

            voice_notes[i]['best_pos'] = best_p
            voice_notes[i]['similarity'] = round(best_score, 3)


def build_tempo_map(tracks):
    """Return sorted list of (abs_tick, tempo_us_per_beat) from all tracks."""
    events = [(0, 500000)]  # MIDI default
    for track in tracks:
        abs_tick = 0
        for msg in track:
            abs_tick += msg.time
            if msg.type == 'set_tempo':
                events.append((abs_tick, msg.tempo))
    return sorted(events)


def ticks_to_seconds(tick, tempo_map, tpb):
    """Convert absolute tick count to seconds, respecting tempo changes."""
    seconds = 0.0
    prev_tick, prev_tempo = tempo_map[0]
    for i in range(1, len(tempo_map)):
        seg_tick, seg_tempo = tempo_map[i]
        if tick <= seg_tick:
            break
        seconds += (seg_tick - prev_tick) * prev_tempo / (tpb * 1_000_000)
        prev_tick, prev_tempo = seg_tick, seg_tempo
    seconds += (tick - prev_tick) * prev_tempo / (tpb * 1_000_000)
    return seconds


def tick_to_measure_beat(tick, tpb, beats_per_measure=4):
    """Return 1-indexed (measure, beat) for a given absolute tick."""
    beat_float = tick / tpb  # 0-indexed beat count
    measure = int(beat_float / beats_per_measure) + 1
    beat = (beat_float % beats_per_measure) + 1.0
    return measure, round(beat, 4)


def parse_track(track, voice_id, tempo_map, tpb):
    """Parse a MIDI track and return a list of note event dicts."""
    abs_tick = 0
    active = {}  # pitch -> (start_tick, velocity)
    notes = []

    for msg in track:
        abs_tick += msg.time
        if msg.type == 'note_on' and msg.velocity > 0:
            active[msg.note] = (abs_tick, msg.velocity)
        elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
            if msg.note in active:
                start_tick, vel = active.pop(msg.note)
                start_sec = ticks_to_seconds(start_tick, tempo_map, tpb)
                end_sec = ticks_to_seconds(abs_tick, tempo_map, tpb)
                measure, beat = tick_to_measure_beat(start_tick, tpb)
                notes.append({
                    'voice': voice_id,
                    'pitch': msg.note,
                    'start': round(start_sec, 4),
                    'duration': round(end_sec - start_sec, 4),
                    'velocity': vel,
                    'measure': measure,
                    'beat': beat,
                })

    return notes


def convert_piece(piece_num):
    piece = PIECES[piece_num]
    midi_path = piece['midi']
    output_path = piece['output']

    mid = mido.MidiFile(midi_path)
    tpb = mid.ticks_per_beat

    tempo_map = build_tempo_map(mid.tracks)
    tempo_us = tempo_map[0][1]
    tempo_bpm = round(60_000_000 / tempo_us, 2)

    notes_by_voice = {}
    voice_meta = []

    for track_idx, channel, voice_id, name, color in piece['voices']:
        track = mid.tracks[track_idx]
        notes = parse_track(track, voice_id, tempo_map, tpb)
        notes_by_voice[voice_id] = notes

        pitches = [n['pitch'] for n in notes]
        voice_meta.append({
            'id': voice_id,
            'name': name,
            'midi_channel': channel,
            'midi_track': track_idx,
            'color': color,
            'pitch_min': min(pitches) if pitches else 0,
            'pitch_max': max(pitches) if pitches else 0,
            'note_count': len(notes),
        })

    tag_motifs(notes_by_voice)
    detect_stretto_and_combinations(notes_by_voice)
    detect_augmentation_diminution(notes_by_voice)

    all_notes = []
    for notes in notes_by_voice.values():
        all_notes.extend(notes)
    all_notes.sort(key=lambda n: n['start'])

    total_duration = max(n['start'] + n['duration'] for n in all_notes)
    total_measures = max(n['measure'] for n in all_notes)

    chromatic_data = compute_chromatic_density(all_notes, total_measures)

    output = {
        'metadata': {
            'title': f"The Art of the Fugue, {piece['title']}",
            'number': piece['number'],
            'composer': 'J.S. Bach',
            'source_midi': midi_path,
            'tempo_bpm': tempo_bpm,
            'tempo_us_per_beat': tempo_us,
            'ticks_per_beat': tpb,
            'time_signature': '4/4',
            'key_signature': 'D minor',
            'total_duration_seconds': round(total_duration, 4),
            'total_measures': total_measures,
            'beats_per_measure': 4,
        },
        'voices': voice_meta,
        'notes': all_notes,
        'chromatic_density': chromatic_data,
    }

    with open(output_path, 'w') as f:
        json.dump(output, f, separators=(',', ':'))

    from collections import Counter
    motif_counts = Counter(n['motif'] for n in all_notes if n['motif'])
    stretto_count = sum(1 for n in all_notes if n.get('stretto'))
    combo_count = sum(1 for n in all_notes if n.get('combination'))
    max_stretto = max((n.get('stretto_voices', 0) for n in all_notes), default=0)
    aug_count = sum(1 for n in all_notes if n.get('aug_dim') == 'augmentation')
    dim_count = sum(1 for n in all_notes if n.get('aug_dim') == 'diminution')
    avg_chromatic = sum(d['density'] for d in chromatic_data) / len(chromatic_data) if chromatic_data else 0
    max_chromatic = max((d['density'] for d in chromatic_data), default=0)
    print(f"[{piece['title']}] Wrote {len(all_notes)} notes to {output_path}")
    print(f'  Duration: {total_duration:.1f}s, Measures: {total_measures}')
    for m, c in sorted(motif_counts.items()):
        print(f'  {m}: {c} notes')
    if stretto_count:
        print(f'  STRETTO: {stretto_count} notes in stretto (max {max_stretto} voices)')
    if combo_count:
        print(f'  COMBINATIONS: {combo_count} notes in multi-motif combinations')
    if aug_count:
        print(f'  AUGMENTATION: {aug_count} notes in augmented entries')
    if dim_count:
        print(f'  DIMINUTION: {dim_count} notes in diminished entries')
    print(f'  CHROMATIC: avg={avg_chromatic:.1%}, max={max_chromatic:.1%}')
    for v in voice_meta:
        print(f"  {v['name']}: {v['note_count']} notes, pitch {v['pitch_min']}–{v['pitch_max']}")


def write_manifest():
    manifest = [
        {'number': p['number'], 'title': p['title'], 'file': p['output']}
        for p in PIECES.values()
    ]
    with open('pieces.json', 'w') as f:
        json.dump(manifest, f, separators=(',', ':'))
    print(f'Wrote pieces.json ({len(manifest)} pieces)')


def main():
    args = sys.argv[1:]
    if '--all' in args:
        for num in PIECES:
            convert_piece(num)
        write_manifest()
    elif '--piece' in args:
        idx = args.index('--piece')
        num = int(args[idx + 1])
        convert_piece(num)
        write_manifest()
    else:
        # Default: convert piece 1 for backwards compatibility
        convert_piece(1)
        write_manifest()


if __name__ == '__main__':
    main()
