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

# ── Secondary subject: Contrapunctus IX descending-scale subject ──
# Octave leap up, then stepwise descent over an octave, into the standard tail.
# D→D(8va)→C#→B→A→G→F→E→D  (9 notes, 8 intervals)
# This is a DIFFERENT subject from the main AotF theme and gets its own motif label.
SUBJECT2_C9         = [12, -1, -2, -2, -2, -2, -1, -2]   # subject on D (C IX Alto m1)
SUBJECT2_C9_ANSWER  = [12, -1, -1, -2, -2, -2, -1, -2]   # answer on A (tonal adj.)

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
    (SUBJECT2_C9,               9, 'subject2',    'C IX descending-scale subject (D)'),
    (SUBJECT2_C9_ANSWER,        9, 'subject2',    'C IX descending-scale answer (A)'),
]

# Tail = last 5 notes of Form A subject: D C# D E F → [-1,+1,+2,+1]
TAIL_INTERVALS = [-1, 1, 2, 1]
TAIL_INV       = [1, -1, -2, -1]   # inversion of tail

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

        # ── Pass 5: Fuzzy similarity scoring for ALL notes ──
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

    all_notes = []
    for notes in notes_by_voice.values():
        all_notes.extend(notes)
    all_notes.sort(key=lambda n: n['start'])

    total_duration = max(n['start'] + n['duration'] for n in all_notes)
    total_measures = max(n['measure'] for n in all_notes)

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
    }

    with open(output_path, 'w') as f:
        json.dump(output, f, separators=(',', ':'))

    from collections import Counter
    motif_counts = Counter(n['motif'] for n in all_notes if n['motif'])
    print(f"[{piece['title']}] Wrote {len(all_notes)} notes to {output_path}")
    print(f'  Duration: {total_duration:.1f}s, Measures: {total_measures}')
    for m, c in sorted(motif_counts.items()):
        print(f'  {m}: {c} notes')
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
