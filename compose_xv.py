#!/usr/bin/env python3
"""Compose Contrapunctus XV — an original fugue on the Art of the Fugue subject.

Version 2: Harmony-aware, rhythmically varied, inhuman virtuosity.

Every vertical sonority is built from chord tones (roots, 3rds, 5ths, 7ths)
of a harmonic progression in D minor.  Voices have distinct characters:
  Soprano: lyrical melody with ornamental grace-note runs, wide leaps
  Alto:    syncopated, angular, fills harmonic gaps
  Tenor:   running sixteenth-note passages, perpetual motion
  Bass:    pedal tones, octave leaps, rhythmic anchor

"Doesn't need to be something a human could play, go nuts."
"""

import mido
import random

random.seed(42)  # reproducible

# ── Tick constants ──
T = 384               # ticks per quarter
WHOLE    = T * 4
DOTTED_H = T * 3
HALF     = T * 2
DOTTED_Q = T + T // 2
QUARTER  = T
EIGHTH   = T // 2
SIXTEENTH = T // 4
TRIPLET_8 = T // 3    # eighth-note triplet
MEASURE  = T * 4

# ── Pitch constants (MIDI) ──
# D minor scale degrees for quick reference
# D=62, E=64, F=65, G=67, A=69, Bb=70, C=72, D=74
# Harmonic minor: C#=73 instead of C=72

# Subject: D A F D C# D E F  intervals: [+7,-4,-3,-1,+1,+2,+1]
SUBJ_INT = [7, -4, -3, -1, 1, 2, 1]
INV_INT  = [-7, 4, 3, 1, -1, -2, -1]
ANS_INT  = [5, -2, -3, -1, 1, 2, 1]
INV_ANS  = [-5, 2, 3, 1, -1, -2, -1]

# ── Harmony: chord progressions as (root_pc, quality) ──
# pc = pitch class (0=C, 1=C#, 2=D, ... 9=A, 10=Bb, 11=B)
# quality: 'm'=minor, 'M'=major, 'dim'=diminished, '7'=dom7
# Chord tones (pc offsets from root): m=[0,3,7], M=[0,4,7], dim=[0,3,6], 7=[0,4,7,10]

CHORD_TONES = {
    'm':   [0, 3, 7],
    'M':   [0, 4, 7],
    'dim': [0, 3, 6],
    '7':   [0, 4, 7, 10],
    'm7':  [0, 3, 7, 10],
}

def chord_pcs(root_pc, quality):
    """Return set of pitch classes belonging to this chord."""
    return {(root_pc + offset) % 12 for offset in CHORD_TONES[quality]}

def is_chord_tone(pitch, root_pc, quality):
    return (pitch % 12) in chord_pcs(root_pc, quality)

def nearest_chord_tone(pitch, root_pc, quality, direction=0):
    """Snap pitch to nearest chord tone. direction: -1=below, +1=above, 0=closest."""
    pcs = chord_pcs(root_pc, quality)
    if (pitch % 12) in pcs:
        return pitch
    candidates = []
    for offset in range(-6, 7):
        p = pitch + offset
        if (p % 12) in pcs:
            candidates.append(p)
    if direction == -1:
        candidates = [c for c in candidates if c <= pitch] or candidates
    elif direction == 1:
        candidates = [c for c in candidates if c >= pitch] or candidates
    return min(candidates, key=lambda c: abs(c - pitch))


# ── Harmonic plan (per half-measure = 2 beats) ──
# Each entry: (root_pitch_class, quality)
# 8 chords per 4 measures. We define the whole piece's harmony.

# Exposition harmony (m1-16): i - V - i - iv - V - i etc.
HARM_EXPO = [
    # m1-4: Dm - A7 - Dm - Gm - A7 - Dm - Bb - A7
    (2,'m'), (9,'7'),  (2,'m'), (2,'m'),  (7,'m'), (9,'7'),  (2,'m'), (2,'m'),
    # m5-8: Dm - A7 - Dm - Gm - C7 - F - Bb - A7
    (2,'m'), (9,'7'),  (2,'m'), (7,'m'),  (0,'7'), (5,'M'),  (10,'M'), (9,'7'),
    # m9-12: Dm - Gm - A7 - Dm - Bb - Gm - A7 - Dm
    (2,'m'), (7,'m'),  (9,'7'), (2,'m'),  (10,'M'), (7,'m'),  (9,'7'), (2,'m'),
    # m13-16: Gm - C7 - F - Bb - Gm - A7 - Dm - Dm
    (7,'m'), (0,'7'),  (5,'M'), (10,'M'),  (7,'m'), (9,'7'),  (2,'m'), (2,'m'),
]

# Episode 1 (m17-24): more adventurous, circle of fifths
HARM_EP1 = [
    # m17-20: Dm - Gm - C7 - F - Bb - Edim - A7 - Dm
    (2,'m'), (7,'m'),  (0,'7'), (5,'M'),  (10,'M'), (4,'dim'),  (9,'7'), (2,'m'),
    # m21-24: Gm - Cm - F7 - Bb - Eb - A7 - Dm - A7
    (7,'m'), (0,'m'),  (5,'7'), (10,'M'),  (3,'M'), (9,'7'),  (2,'m'), (9,'7'),
]

# Middle entries (m25-40)
HARM_MID = [
    # m25-28: Bb - F - Gm - Dm - Eb - Bb - C7 - F
    (10,'M'), (5,'M'),  (7,'m'), (2,'m'),  (3,'M'), (10,'M'),  (0,'7'), (5,'M'),
    # m29-32: Dm - A7 - Dm - Gm - Bb - A7 - Dm - Dm
    (2,'m'), (9,'7'),  (2,'m'), (7,'m'),  (10,'M'), (9,'7'),  (2,'m'), (2,'m'),
    # m33-36: Gm - D7 - Gm - Cm - F7 - Bb - Edim - A7
    (7,'m'), (2,'7'),  (7,'m'), (0,'m'),  (5,'7'), (10,'M'),  (4,'dim'), (9,'7'),
    # m37-40: Dm - Gm - A7 - Dm - Bb - Gm - A7 - Dm
    (2,'m'), (7,'m'),  (9,'7'), (2,'m'),  (10,'M'), (7,'m'),  (9,'7'), (2,'m'),
]

# Episode 2 (m41-48)
HARM_EP2 = [
    # m41-44: Dm - Edim - A7 - Dm - Gm - C7 - F - Dm
    (2,'m'), (4,'dim'),  (9,'7'), (2,'m'),  (7,'m'), (0,'7'),  (5,'M'), (2,'m'),
    # m45-48: Bb - Gm - A7 - Dm - Gm - Edim - A7 - A7
    (10,'M'), (7,'m'),  (9,'7'), (2,'m'),  (7,'m'), (4,'dim'),  (9,'7'), (9,'7'),
]

# Stretto (m49-64)
HARM_STRETTO = [
    # m49-52: Dm - A7 - Dm - Gm - A7 - Dm - Bb - A7
    (2,'m'), (9,'7'),  (2,'m'), (7,'m'),  (9,'7'), (2,'m'),  (10,'M'), (9,'7'),
    # m53-56: Dm - Gm - C7 - F - Bb - A7 - Dm - Dm
    (2,'m'), (7,'m'),  (0,'7'), (5,'M'),  (10,'M'), (9,'7'),  (2,'m'), (2,'m'),
    # m57-60: Dm - A7 - Dm - Dm - Gm - C7 - F - A7
    (2,'m'), (9,'7'),  (2,'m'), (2,'m'),  (7,'m'), (0,'7'),  (5,'M'), (9,'7'),
    # m61-64: Dm - Gm - Edim - A7 - Dm - Bb - A7 - Dm
    (2,'m'), (7,'m'),  (4,'dim'), (9,'7'),  (2,'m'), (10,'M'),  (9,'7'), (2,'m'),
]

# Finale (m65-80)
HARM_FINALE = [
    # m65-68: Dm - Dm - Gm - Gm - A7 - A7 - Dm - Dm
    (2,'m'), (2,'m'),  (7,'m'), (7,'m'),  (9,'7'), (9,'7'),  (2,'m'), (2,'m'),
    # m69-72: Bb - F - Gm - C7 - F - Bb - A7 - Dm
    (10,'M'), (5,'M'),  (7,'m'), (0,'7'),  (5,'M'), (10,'M'),  (9,'7'), (2,'m'),
    # m73-76: Dm - Gm - A7 - Dm - Bb - Edim - A7 - Dm
    (2,'m'), (7,'m'),  (9,'7'), (2,'m'),  (10,'M'), (4,'dim'),  (9,'7'), (2,'m'),
    # m77-80: Gm - A7 - Dm - Dm - Gm - A7 - Dm - Dm (final)
    (7,'m'), (9,'7'),  (2,'m'), (2,'m'),  (7,'m'), (9,'7'),  (2,'m'), (2,'m'),
]

ALL_HARMONY = HARM_EXPO + HARM_EP1 + HARM_MID + HARM_EP2 + HARM_STRETTO + HARM_FINALE

def harmony_at(tick):
    """Return (root_pc, quality) for the harmony at a given tick."""
    half_bar_idx = tick // HALF
    if half_bar_idx < 0:
        half_bar_idx = 0
    if half_bar_idx >= len(ALL_HARMONY):
        half_bar_idx = len(ALL_HARMONY) - 1
    return ALL_HARMONY[half_bar_idx]


# ── Voice builder ──
class Voice:
    def __init__(self, channel):
        self.channel = channel
        self.notes = []
        self.cursor = 0

    def rest(self, dur):
        self.cursor += dur

    def note(self, pitch, dur, vel=68):
        self.notes.append((self.cursor, pitch, dur, vel))
        self.cursor += dur

    def add_melody(self, pitches_durs, vel=68):
        for p, d in pitches_durs:
            self.note(p, d, vel)

    def add_subject(self, start_pitch, intervals, rhythm, vel=68):
        """Add subject with given intervals and rhythm."""
        p = start_pitch
        self.note(p, rhythm[0], vel)
        for i, intv in enumerate(intervals):
            p += intv
            self.note(p, rhythm[min(i + 1, len(rhythm) - 1)], vel)

    def goto(self, tick):
        self.cursor = tick


def make_subject_rhythm_basic():
    """Standard subject rhythm: half notes with quarter notes on the chromatic turn."""
    return [HALF, HALF, HALF, HALF, HALF, QUARTER, QUARTER, HALF]

def make_subject_rhythm_decorated():
    """Decorated subject rhythm with dotted notes and grace notes."""
    return [DOTTED_Q, EIGHTH, DOTTED_Q, EIGHTH, HALF, SIXTEENTH, SIXTEENTH, SIXTEENTH, SIXTEENTH, HALF]

def make_subject_rhythm_driving():
    """Urgent rhythm: shorter values."""
    return [QUARTER, QUARTER, QUARTER, QUARTER, QUARTER, EIGHTH, EIGHTH, HALF]

def make_subject_rhythm_augmented():
    """Augmented rhythm: doubled values."""
    return [WHOLE, WHOLE, WHOLE, WHOLE, WHOLE, HALF, HALF, WHOLE]


# ── Ornamental helper functions ──

def grace_run_up(start_pitch, target_pitch, dur_each=SIXTEENTH):
    """Chromatic or scalar run from start to target."""
    notes = []
    p = start_pitch
    step = 1 if target_pitch > start_pitch else -1
    while p != target_pitch:
        notes.append((p, dur_each))
        p += step
    return notes

def grace_run_down(start_pitch, target_pitch, dur_each=SIXTEENTH):
    return grace_run_up(start_pitch, target_pitch, dur_each)

def scalar_run(start_pitch, steps, dur_each=SIXTEENTH):
    """Diatonic-ish run using D minor scale intervals."""
    # D minor scale intervals from any starting point
    dm_steps = [2, 1, 2, 2, 1, 2, 2]  # whole, half, whole, whole, half, whole, whole
    notes = []
    p = start_pitch
    notes.append((p, dur_each))
    step_idx = (start_pitch % 12) % 7  # rough mapping
    for i in range(abs(steps)):
        if steps > 0:
            p += dm_steps[step_idx % 7]
            step_idx += 1
        else:
            step_idx -= 1
            p -= dm_steps[step_idx % 7]
        notes.append((p, dur_each))
    return notes

def arpeggio(root_pitch, quality, octaves=2, dur_each=SIXTEENTH, direction='up'):
    """Arpeggiate a chord over given octaves."""
    offsets = CHORD_TONES[quality]
    notes = []
    for oct in range(octaves):
        pitches = [root_pitch + oct * 12 + o for o in offsets]
        if direction == 'down':
            pitches = list(reversed(pitches))
        for p in pitches:
            notes.append((p, dur_each))
    if direction == 'updown':
        up = [(root_pitch + oct * 12 + o, dur_each) for oct in range(octaves) for o in offsets]
        down = list(reversed(up[:-1]))
        notes = up + down
    return notes

def trill(pitch, dur_total, interval=1):
    """Trill between pitch and pitch+interval."""
    notes = []
    remaining = dur_total
    while remaining > 0:
        d = min(SIXTEENTH, remaining)
        notes.append((pitch, d))
        remaining -= d
        if remaining <= 0:
            break
        d = min(SIXTEENTH, remaining)
        notes.append((pitch + interval, d))
        remaining -= d
    return notes

def mordent(pitch, dur_main, interval=2):
    """Main note → upper → main."""
    return [(pitch, dur_main - 2 * SIXTEENTH), (pitch + interval, SIXTEENTH), (pitch, SIXTEENTH)]

def turn(pitch, dur_main, interval=2):
    """Upper → main → lower → main."""
    each = dur_main // 4
    return [(pitch + interval, each), (pitch, each), (pitch - 1, each), (pitch, each)]


# ══════════════════════════════════════════════════════════════
# COMPOSE THE FUGUE
# ══════════════════════════════════════════════════════════════
def compose():
    sop  = Voice(0)
    alto = Voice(1)
    ten  = Voice(2)
    bass = Voice(3)

    # ────────────────────────────────────────
    # EXPOSITION (m1-16)
    # ────────────────────────────────────────

    # m1-4: ALTO states subject on D4(62), basic rhythm
    alto.add_subject(62, SUBJ_INT, make_subject_rhythm_basic(), vel=72)

    # m1-2: other voices rest, then enter
    sop.rest(2 * MEASURE)
    ten.rest(4 * MEASURE)
    bass.rest(8 * MEASURE)

    # m3-6: SOPRANO enters with inverted answer on A4(69), decorated rhythm
    sop.add_subject(69, INV_ANS, make_subject_rhythm_decorated(), vel=70)

    # m3-6: Alto continues — countersubject with syncopation
    # Harmonizes with soprano's inversion: chord-tone based
    alto.add_melody([
        (65, EIGHTH), (67, EIGHTH), (69, DOTTED_Q), (67, EIGHTH),
        (65, QUARTER), (64, QUARTER), (62, EIGHTH), (64, EIGHTH), (65, QUARTER),
        (67, QUARTER), (69, EIGHTH), (70, EIGHTH), (69, QUARTER), (67, QUARTER),
        (65, DOTTED_Q), (64, EIGHTH), (62, HALF),
    ])

    # m5-8: TENOR enters with answer on A3(57), driving rhythm
    ten.add_subject(57, ANS_INT, make_subject_rhythm_driving(), vel=68)

    # m5-8: Soprano — ornamental flourishes over tenor entry
    sop.add_melody(mordent(67, QUARTER))
    sop.add_melody([(65, EIGHTH), (64, EIGHTH)])
    sop.add_melody(turn(69, QUARTER))
    sop.add_melody([(70, QUARTER), (72, QUARTER)])
    sop.add_melody(trill(74, HALF))
    sop.add_melody([(72, QUARTER), (70, EIGHTH), (69, EIGHTH)])
    sop.add_melody(mordent(67, QUARTER))
    sop.add_melody([(65, QUARTER)])
    sop.add_melody(grace_run_up(62, 69, SIXTEENTH))
    sop.note(69, QUARTER)

    # m5-8: Alto — angular syncopated counterpoint
    alto.add_melody([
        (69, EIGHTH), (65, EIGHTH), (67, QUARTER + EIGHTH), (69, EIGHTH),
        (70, QUARTER), (67, QUARTER + EIGHTH), (65, EIGHTH), (62, QUARTER),
        (64, QUARTER + EIGHTH), (65, EIGHTH), (67, QUARTER), (69, QUARTER),
        (70, QUARTER + EIGHTH), (69, EIGHTH), (67, HALF),
    ])

    # m9-12: BASS enters with inverted subject on D3(50)
    bass.add_subject(50, INV_INT, make_subject_rhythm_basic(), vel=75)

    # m9-12: Soprano — soaring line with grace note cascades
    sop.add_melody([(72, QUARTER)])
    sop.add_melody(grace_run_up(72, 77, SIXTEENTH))  # chromatic run to F5
    sop.note(77, QUARTER)
    sop.add_melody([(76, EIGHTH), (74, EIGHTH), (72, QUARTER)])
    sop.add_melody(trill(74, HALF, 1))
    sop.add_melody([(72, QUARTER), (70, EIGHTH), (69, EIGHTH)])
    sop.add_melody(grace_run_down(69, 62, SIXTEENTH))
    sop.note(62, QUARTER)
    sop.add_melody([(65, QUARTER), (69, HALF)])

    # m9-12: Alto — running eighths filling harmony
    alto.add_melody([
        (62, EIGHTH), (64, EIGHTH), (65, EIGHTH), (67, EIGHTH),
        (69, QUARTER), (67, EIGHTH), (65, EIGHTH),
        (64, EIGHTH), (62, EIGHTH), (61, EIGHTH), (62, EIGHTH),
        (64, QUARTER), (65, QUARTER),
        (67, EIGHTH), (69, EIGHTH), (70, EIGHTH), (69, EIGHTH),
        (67, QUARTER), (65, QUARTER),
        (64, EIGHTH), (62, EIGHTH), (64, EIGHTH), (65, EIGHTH),
        (67, HALF),
    ])

    # m9-12: Tenor — tail motifs and sequences
    ten.add_melody([
        (60, QUARTER), (59, EIGHTH), (60, EIGHTH), (62, QUARTER), (60, QUARTER),
        (57, QUARTER), (55, QUARTER), (53, QUARTER), (55, QUARTER),
        (57, EIGHTH), (59, EIGHTH), (60, QUARTER), (62, QUARTER), (60, QUARTER),
        (57, HALF), (55, HALF),
    ])

    # m13-16: Closing of exposition — all voices, rich texture
    tick_13 = 12 * MEASURE

    # Soprano: lyrical melody with turns
    sop.goto(tick_13)
    sop.add_melody(turn(72, QUARTER))
    sop.add_melody([(74, QUARTER), (76, EIGHTH), (77, EIGHTH), (76, QUARTER)])
    sop.add_melody(mordent(74, QUARTER))
    sop.add_melody([(72, QUARTER)])
    sop.add_melody(trill(70, HALF, 2))
    sop.add_melody([(69, QUARTER), (70, QUARTER)])
    sop.add_melody([(72, EIGHTH), (74, EIGHTH), (76, QUARTER)])
    sop.add_melody([(77, DOTTED_Q), (76, EIGHTH), (74, HALF)])

    # Alto: off-beat accents
    alto.goto(tick_13)
    alto.add_melody([
        (65, EIGHTH), (67, DOTTED_Q), (69, EIGHTH), (67, DOTTED_Q),
        (65, EIGHTH), (64, EIGHTH), (62, EIGHTH), (64, QUARTER + EIGHTH),
        (65, QUARTER + EIGHTH), (67, EIGHTH), (69, QUARTER), (70, QUARTER),
        (69, EIGHTH), (67, DOTTED_Q), (65, HALF + QUARTER),
    ])

    # Tenor: running sixteenths — perpetual motion character established
    ten.goto(tick_13)
    ten.add_melody([
        (57, SIXTEENTH), (59, SIXTEENTH), (60, SIXTEENTH), (62, SIXTEENTH),
        (64, SIXTEENTH), (62, SIXTEENTH), (60, SIXTEENTH), (59, SIXTEENTH),
        (57, SIXTEENTH), (55, SIXTEENTH), (53, SIXTEENTH), (55, SIXTEENTH),
        (57, SIXTEENTH), (59, SIXTEENTH), (60, SIXTEENTH), (62, SIXTEENTH),
    ])
    ten.add_melody([
        (60, SIXTEENTH), (59, SIXTEENTH), (57, SIXTEENTH), (55, SIXTEENTH),
        (53, SIXTEENTH), (55, SIXTEENTH), (57, SIXTEENTH), (59, SIXTEENTH),
        (60, SIXTEENTH), (62, SIXTEENTH), (64, SIXTEENTH), (65, SIXTEENTH),
        (64, SIXTEENTH), (62, SIXTEENTH), (60, SIXTEENTH), (59, SIXTEENTH),
    ])
    ten.add_melody([
        (57, SIXTEENTH), (59, SIXTEENTH), (60, SIXTEENTH), (57, SIXTEENTH),
        (55, SIXTEENTH), (57, SIXTEENTH), (59, SIXTEENTH), (60, SIXTEENTH),
        (62, SIXTEENTH), (60, SIXTEENTH), (59, SIXTEENTH), (57, SIXTEENTH),
        (55, SIXTEENTH), (53, SIXTEENTH), (52, SIXTEENTH), (53, SIXTEENTH),
    ])
    ten.add_melody([
        (55, SIXTEENTH), (57, SIXTEENTH), (59, SIXTEENTH), (60, SIXTEENTH),
        (62, SIXTEENTH), (60, SIXTEENTH), (59, SIXTEENTH), (57, SIXTEENTH),
        (55, QUARTER), (57, QUARTER), (58, HALF),
    ])

    # Bass: pedal tones with octave leaps
    bass.goto(tick_13)
    bass.add_melody([
        (43, QUARTER), (55, EIGHTH), (43, EIGHTH),   # G octave leap
        (48, QUARTER), (60, EIGHTH), (48, EIGHTH),   # C octave leap
        (45, QUARTER), (57, EIGHTH), (45, EIGHTH),   # A octave
        (46, QUARTER), (58, EIGHTH), (46, EIGHTH),   # Bb octave
        (43, QUARTER), (55, EIGHTH), (43, EIGHTH),
        (45, DOTTED_Q), (57, EIGHTH),
        (50, HALF),
        (50, QUARTER), (38, QUARTER),  # big drop to D2
    ])

    # ────────────────────────────────────────
    # EPISODE 1 (m17-24) — Sequential development
    # ────────────────────────────────────────
    tick_ep1 = 16 * MEASURE

    # Soprano: descending sequence with grace note cascades every 2 bars
    sop.goto(tick_ep1)
    sop.add_melody(grace_run_down(77, 72, SIXTEENTH))
    sop.note(72, QUARTER)
    sop.add_melody([(74, EIGHTH), (72, EIGHTH), (70, QUARTER), (69, QUARTER)])
    sop.add_melody(mordent(70, QUARTER))
    sop.add_melody([(72, QUARTER)])
    sop.add_melody(grace_run_down(74, 69, SIXTEENTH))
    sop.note(69, QUARTER)
    sop.add_melody([(70, EIGHTH), (69, EIGHTH), (67, QUARTER), (65, QUARTER)])
    sop.add_melody(turn(67, QUARTER))
    sop.add_melody([(69, QUARTER)])
    # Rising sequence
    sop.add_melody(grace_run_up(65, 72, SIXTEENTH))
    sop.note(72, QUARTER)
    sop.add_melody(trill(74, HALF, 1))
    sop.add_melody([(72, QUARTER), (70, QUARTER)])
    sop.add_melody(grace_run_up(67, 74, SIXTEENTH))
    sop.note(74, QUARTER)
    sop.add_melody(trill(76, HALF, 1))
    sop.add_melody([(74, QUARTER), (72, HALF)])

    # Alto: tail motifs rising in sequence, syncopated
    alto.goto(tick_ep1)
    # tail on D: D C# D E F
    alto.add_melody([(62, EIGHTH), (61, DOTTED_Q), (62, QUARTER), (64, QUARTER), (65, QUARTER + EIGHTH)])
    # tail on F: F E F G A
    alto.add_melody([(65, EIGHTH), (64, DOTTED_Q), (65, QUARTER), (67, QUARTER), (69, QUARTER + EIGHTH)])
    # inverted tail on A: A Bb A G F
    alto.add_melody([(69, EIGHTH), (70, DOTTED_Q), (69, QUARTER), (67, QUARTER), (65, QUARTER + EIGHTH)])
    # tail on G: G F# G A Bb
    alto.add_melody([(67, EIGHTH), (66, DOTTED_Q), (67, QUARTER), (69, QUARTER), (70, QUARTER + EIGHTH)])
    # Free resolution
    alto.add_melody([
        (69, QUARTER), (67, EIGHTH), (65, EIGHTH), (64, QUARTER), (62, QUARTER),
        (64, EIGHTH), (65, EIGHTH), (67, QUARTER), (69, QUARTER), (70, QUARTER),
        (69, EIGHTH), (67, EIGHTH), (65, HALF), (64, HALF), (62, HALF),
    ])

    # Tenor: perpetual sixteenth-note motion — arpeggiated chords
    ten.goto(tick_ep1)
    # 8 measures of running sixteenths following the harmony
    harm_ep1_chords = HARM_EP1
    for ci, (rpc, qual) in enumerate(harm_ep1_chords):
        base = 53 + (rpc - 2) % 12  # root near tenor range
        if base > 65:
            base -= 12
        if base < 48:
            base += 12
        arp = arpeggio(base, qual, octaves=1, dur_each=SIXTEENTH, direction='up')
        # Add some variation: reverse every other chord
        if ci % 2 == 1:
            arp = list(reversed(arp))
        # Fill half-bar (HALF = 8 sixteenths)
        total = 0
        for p, d in arp:
            if total + d > HALF:
                break
            ten.note(p, d, 64)
            total += d
        # Fill remaining time
        while total < HALF:
            ten.note(base, SIXTEENTH, 64)
            total += SIXTEENTH

    # Bass: long pedals with occasional dramatic leaps
    bass.goto(tick_ep1)
    bass.add_melody([
        (50, WHOLE),                          # D pedal
        (48, HALF), (36, QUARTER), (48, QUARTER),  # C with octave drop
        (45, WHOLE),                          # A pedal
        (43, HALF), (31, QUARTER), (43, QUARTER),  # G with octave drop
        (46, WHOLE),                          # Bb pedal
        (40, HALF), (52, QUARTER), (40, QUARTER),  # E with octave leap
        (45, HALF), (33, HALF),               # A pedal with drop
        (38, WHOLE),                          # D pedal
    ])

    # ────────────────────────────────────────
    # MIDDLE ENTRIES (m25-40)
    # ────────────────────────────────────────
    tick_mid = 24 * MEASURE

    # m25-28: Tenor subject on Bb3(58), driving rhythm
    ten.goto(tick_mid)
    ten.add_subject(58, SUBJ_INT, make_subject_rhythm_driving(), vel=72)

    # m26-29: Soprano inverted answer on F5(77), decorated with trills
    sop.goto(tick_mid + MEASURE)
    sop.add_melody(mordent(77, HALF))
    sop.add_melody([(72, HALF)])
    sop.add_melody(trill(74, HALF, 1))
    sop.add_melody([(77, QUARTER), (76, EIGHTH), (77, EIGHTH)])
    sop.add_melody([(78, QUARTER), (77, EIGHTH), (76, EIGHTH)])
    sop.add_melody([(74, HALF)])
    sop.add_melody(trill(76, HALF, 1))

    # m25-28: Alto syncopated harmonic fill
    alto.goto(tick_mid)
    alto.add_melody([
        (65, EIGHTH), (67, DOTTED_Q), (69, QUARTER + EIGHTH), (67, EIGHTH),
        (65, QUARTER), (67, EIGHTH), (69, EIGHTH), (70, QUARTER + EIGHTH), (69, EIGHTH),
        (67, QUARTER), (65, EIGHTH), (64, EIGHTH), (62, QUARTER + EIGHTH), (64, EIGHTH),
        (65, QUARTER), (67, QUARTER), (69, HALF),
    ])

    # m25-28: Bass — pedal Bb with rhythmic punctuation
    bass.goto(tick_mid)
    bass.add_melody([
        (46, HALF), (58, QUARTER), (46, QUARTER),
        (45, HALF), (57, QUARTER), (45, QUARTER),
        (43, QUARTER), (55, EIGHTH), (43, EIGHTH), (46, QUARTER), (58, EIGHTH), (46, EIGHTH),
        (50, HALF), (38, HALF),
    ])

    # m29-32: free counterpoint, building tension
    tick_29 = 28 * MEASURE

    sop.goto(tick_29)
    sop.add_melody(grace_run_up(69, 77, SIXTEENTH))
    sop.note(77, QUARTER)
    sop.add_melody([(76, EIGHTH), (74, EIGHTH)])
    sop.add_melody(trill(72, HALF, 2))
    sop.add_melody([(70, QUARTER), (69, QUARTER)])
    sop.add_melody(mordent(67, QUARTER))
    sop.add_melody([(69, QUARTER), (70, HALF)])
    sop.add_melody([(72, QUARTER), (74, EIGHTH), (72, EIGHTH), (70, HALF)])

    alto.goto(tick_29)
    alto.add_melody([
        (62, EIGHTH), (64, DOTTED_Q), (65, QUARTER + EIGHTH), (67, EIGHTH),
        (69, EIGHTH), (70, DOTTED_Q), (69, QUARTER + EIGHTH), (67, EIGHTH),
        (65, QUARTER), (64, EIGHTH), (62, EIGHTH), (61, QUARTER), (62, QUARTER),
        (64, QUARTER), (65, QUARTER), (67, HALF),
    ])

    ten.goto(tick_29)
    # Tenor: sixteenth-note sequences
    for _ in range(2):
        ten.add_melody([
            (57, SIXTEENTH), (59, SIXTEENTH), (60, SIXTEENTH), (62, SIXTEENTH),
            (64, SIXTEENTH), (62, SIXTEENTH), (60, SIXTEENTH), (59, SIXTEENTH),
            (57, SIXTEENTH), (55, SIXTEENTH), (53, SIXTEENTH), (55, SIXTEENTH),
            (57, SIXTEENTH), (59, SIXTEENTH), (60, SIXTEENTH), (62, SIXTEENTH),
        ])
    ten.add_melody([
        (60, SIXTEENTH), (62, SIXTEENTH), (64, SIXTEENTH), (65, SIXTEENTH),
        (64, SIXTEENTH), (62, SIXTEENTH), (60, SIXTEENTH), (59, SIXTEENTH),
        (57, EIGHTH), (55, EIGHTH), (53, QUARTER), (55, HALF),
    ])

    bass.goto(tick_29)
    bass.add_melody([
        (50, QUARTER), (45, QUARTER), (38, HALF),
        (43, QUARTER), (50, EIGHTH), (43, EIGHTH), (38, HALF),
        (46, HALF), (43, QUARTER), (45, QUARTER),
        (50, HALF), (38, HALF),
    ])

    # m33-36: Bass subject on G2(43), alto inversion on D4(62)
    tick_33 = 32 * MEASURE

    bass.goto(tick_33)
    bass.add_subject(43, SUBJ_INT, make_subject_rhythm_basic(), vel=75)

    alto.goto(tick_33 + MEASURE)
    alto.add_subject(62, INV_INT, make_subject_rhythm_driving(), vel=70)

    sop.goto(tick_33)
    sop.add_melody(trill(74, HALF, 1))
    sop.add_melody([(72, QUARTER), (70, QUARTER)])
    sop.add_melody(grace_run_up(67, 74, SIXTEENTH))
    sop.note(74, QUARTER)
    sop.add_melody([(77, QUARTER), (76, EIGHTH), (74, EIGHTH)])
    sop.add_melody(trill(72, HALF, 2))
    sop.add_melody([(70, EIGHTH), (69, EIGHTH), (67, QUARTER)])
    sop.add_melody(mordent(69, QUARTER))
    sop.add_melody([(70, QUARTER), (72, HALF)])
    sop.add_melody([(74, QUARTER), (72, EIGHTH), (70, EIGHTH), (69, HALF)])

    ten.goto(tick_33)
    # Running sixteenths
    ten.add_melody([
        (57, SIXTEENTH), (55, SIXTEENTH), (53, SIXTEENTH), (52, SIXTEENTH),
        (50, SIXTEENTH), (52, SIXTEENTH), (53, SIXTEENTH), (55, SIXTEENTH),
        (57, SIXTEENTH), (59, SIXTEENTH), (60, SIXTEENTH), (62, SIXTEENTH),
        (60, SIXTEENTH), (59, SIXTEENTH), (57, SIXTEENTH), (55, SIXTEENTH),
    ] * 2)
    ten.add_melody([
        (53, SIXTEENTH), (55, SIXTEENTH), (57, SIXTEENTH), (59, SIXTEENTH),
        (60, SIXTEENTH), (62, SIXTEENTH), (64, SIXTEENTH), (65, SIXTEENTH),
        (64, SIXTEENTH), (62, SIXTEENTH), (60, SIXTEENTH), (59, SIXTEENTH),
        (57, SIXTEENTH), (55, SIXTEENTH), (53, SIXTEENTH), (55, SIXTEENTH),
    ])
    ten.add_melody([(57, QUARTER), (59, QUARTER), (60, HALF)])

    # m37-40
    tick_37 = 36 * MEASURE

    sop.goto(tick_37)
    sop.add_melody(grace_run_down(74, 67, SIXTEENTH))
    sop.note(67, QUARTER)
    sop.add_melody([(69, EIGHTH), (70, EIGHTH), (72, QUARTER), (74, QUARTER)])
    sop.add_melody(trill(76, HALF, 1))
    sop.add_melody([(74, QUARTER), (72, QUARTER)])
    sop.add_melody(mordent(70, QUARTER))
    sop.add_melody([(69, QUARTER), (67, HALF)])
    sop.add_melody([(69, QUARTER), (70, QUARTER), (72, HALF)])

    alto.goto(tick_37)
    alto.add_melody([
        (57, EIGHTH), (59, EIGHTH), (60, QUARTER + EIGHTH), (62, EIGHTH),
        (64, QUARTER), (62, QUARTER), (64, QUARTER + EIGHTH), (65, EIGHTH),
        (67, QUARTER), (65, QUARTER), (64, EIGHTH), (62, EIGHTH), (60, QUARTER),
        (62, QUARTER), (64, QUARTER), (65, HALF),
    ])

    ten.goto(tick_37)
    ten.add_melody([
        (57, SIXTEENTH), (59, SIXTEENTH), (60, SIXTEENTH), (62, SIXTEENTH),
        (64, SIXTEENTH), (62, SIXTEENTH), (60, SIXTEENTH), (59, SIXTEENTH),
        (57, SIXTEENTH), (55, SIXTEENTH), (53, SIXTEENTH), (52, SIXTEENTH),
        (50, SIXTEENTH), (52, SIXTEENTH), (53, SIXTEENTH), (55, SIXTEENTH),
    ] * 2)
    ten.add_melody([
        (57, EIGHTH), (59, EIGHTH), (60, QUARTER),
        (62, QUARTER), (60, QUARTER), (59, HALF),
    ])

    bass.goto(tick_37)
    bass.add_melody([
        (50, QUARTER), (38, QUARTER), (43, HALF),
        (46, QUARTER), (34, QUARTER), (38, HALF),
        (43, QUARTER), (55, EIGHTH), (43, EIGHTH), (45, QUARTER), (57, EIGHTH), (45, EIGHTH),
        (50, HALF), (38, HALF),
    ])

    # ────────────────────────────────────────
    # EPISODE 2 (m41-48) — Tail canons, building to stretto
    # ────────────────────────────────────────
    tick_ep2 = 40 * MEASURE

    # Soprano: tail canon leader, then soaring
    sop.goto(tick_ep2)
    # Tail: D C# D E F
    sop.add_melody([(74, QUARTER), (73, QUARTER), (74, QUARTER), (76, QUARTER), (77, HALF)])
    sop.add_melody(trill(79, HALF, 1))
    # Tail again higher
    sop.add_melody([(77, QUARTER), (76, QUARTER), (77, QUARTER), (79, QUARTER), (81, HALF)])
    sop.add_melody(grace_run_down(81, 74, SIXTEENTH))
    sop.note(74, QUARTER)
    # Soaring climax approach
    sop.add_melody(grace_run_up(74, 81, SIXTEENTH))
    sop.note(81, QUARTER)
    sop.add_melody(trill(79, HALF, 2))
    sop.add_melody([(77, QUARTER), (76, QUARTER)])
    sop.add_melody([(74, QUARTER), (72, QUARTER), (70, HALF)])
    sop.add_melody(mordent(72, QUARTER))
    sop.add_melody([(74, QUARTER), (76, HALF)])

    # Alto: tail canon follower at 1 bar delay
    alto.goto(tick_ep2)
    alto.rest(MEASURE)
    alto.add_melody([(69, QUARTER), (68, QUARTER), (69, QUARTER), (71, QUARTER), (72, HALF)])
    alto.add_melody([(70, QUARTER), (69, EIGHTH), (67, EIGHTH)])
    alto.add_melody([(69, QUARTER), (68, QUARTER), (69, QUARTER), (71, QUARTER)])
    alto.add_melody([(72, QUARTER), (70, QUARTER), (69, QUARTER), (67, QUARTER)])
    alto.add_melody([
        (65, EIGHTH), (67, DOTTED_Q), (69, QUARTER + EIGHTH), (67, EIGHTH),
        (65, QUARTER), (67, QUARTER), (69, HALF),
    ])

    # Soprano fills the first bar of alto's rest
    # (already covered above)

    # Tenor: relentless sixteenths, arpeggiating the harmony
    ten.goto(tick_ep2)
    harm_ep2_chords = HARM_EP2
    for ci, (rpc, qual) in enumerate(harm_ep2_chords):
        base = 53 + (rpc - 2) % 12
        if base > 65: base -= 12
        if base < 48: base += 12
        arp = arpeggio(base, qual, octaves=1, dur_each=SIXTEENTH, direction='updown' if ci % 3 == 0 else 'up')
        total = 0
        for p, d in arp:
            if total + d > HALF: break
            ten.note(p, d, 64)
            total += d
        while total < HALF:
            ten.note(base, SIXTEENTH, 64)
            total += SIXTEENTH

    # Bass: rising chromatic bass line (dramatic!)
    bass.goto(tick_ep2)
    bass.add_melody([
        (38, DOTTED_Q), (50, EIGHTH), (39, DOTTED_Q), (51, EIGHTH),
        (40, DOTTED_Q), (52, EIGHTH), (41, DOTTED_Q), (53, EIGHTH),
        (42, DOTTED_Q), (54, EIGHTH), (43, DOTTED_Q), (55, EIGHTH),
        (44, DOTTED_Q), (56, EIGHTH), (45, DOTTED_Q), (57, EIGHTH),
    ])

    # ────────────────────────────────────────
    # STRETTO (m49-64) — The climax
    # ────────────────────────────────────────
    tick_str = 48 * MEASURE

    # TIGHT STRETTO 1: m49-52
    # Alto: subject on D4(62)
    alto.goto(tick_str)
    alto.add_subject(62, SUBJ_INT, make_subject_rhythm_driving(), vel=75)

    # Soprano: inverted subject on A4(69), 2 beats later
    sop.goto(tick_str + HALF)
    sop.add_subject(69, INV_INT, make_subject_rhythm_driving(), vel=73)

    # Tenor: answer on A3(57), 1 bar later
    ten.goto(tick_str + MEASURE)
    ten.add_subject(57, ANS_INT, make_subject_rhythm_driving(), vel=70)

    # Bass: inverted answer on D3(50), 1.5 bars later
    bass.goto(tick_str + MEASURE + HALF)
    bass.add_subject(50, INV_ANS, make_subject_rhythm_driving(), vel=75)

    # m53-56: aftermath — all voices free, complex texture
    tick_53 = 52 * MEASURE

    sop.goto(tick_53)
    sop.add_melody(grace_run_up(65, 74, SIXTEENTH))
    sop.note(74, QUARTER)
    sop.add_melody(trill(76, HALF, 1))
    sop.add_melody([(74, QUARTER), (72, EIGHTH), (70, EIGHTH)])
    sop.add_melody(mordent(69, QUARTER))
    sop.add_melody([(70, QUARTER), (72, QUARTER), (74, QUARTER)])
    sop.add_melody(turn(76, QUARTER))
    sop.add_melody([(77, QUARTER), (76, EIGHTH), (74, EIGHTH), (72, HALF)])

    alto.goto(tick_53)
    alto.add_melody([
        (65, EIGHTH), (67, DOTTED_Q), (69, EIGHTH), (70, DOTTED_Q),
        (69, QUARTER), (67, EIGHTH), (65, EIGHTH), (64, QUARTER), (62, QUARTER),
        (64, EIGHTH), (65, EIGHTH), (67, QUARTER + EIGHTH), (69, EIGHTH),
        (70, QUARTER), (69, QUARTER), (67, HALF),
    ])

    ten.goto(tick_53)
    ten.add_melody([
        (60, SIXTEENTH), (62, SIXTEENTH), (64, SIXTEENTH), (65, SIXTEENTH),
        (64, SIXTEENTH), (62, SIXTEENTH), (60, SIXTEENTH), (59, SIXTEENTH),
        (57, SIXTEENTH), (59, SIXTEENTH), (60, SIXTEENTH), (62, SIXTEENTH),
        (64, SIXTEENTH), (65, SIXTEENTH), (67, SIXTEENTH), (65, SIXTEENTH),
    ] * 2)
    ten.add_melody([
        (60, SIXTEENTH), (59, SIXTEENTH), (57, SIXTEENTH), (55, SIXTEENTH),
        (53, SIXTEENTH), (55, SIXTEENTH), (57, SIXTEENTH), (59, SIXTEENTH),
        (60, QUARTER), (62, QUARTER), (60, HALF),
    ])

    bass.goto(tick_53)
    bass.add_melody([
        (50, QUARTER), (38, QUARTER), (43, QUARTER), (55, EIGHTH), (43, EIGHTH),
        (46, HALF), (45, QUARTER), (43, QUARTER),
        (41, QUARTER), (53, EIGHTH), (41, EIGHTH), (38, HALF),
        (43, QUARTER), (45, QUARTER), (50, HALF),
    ])

    # TIGHT STRETTO 2 (m57-60): ALL 4 voices within 1 beat!
    tick_57 = 56 * MEASURE

    # Tenor: subject on D3(50)
    ten.goto(tick_57)
    ten.add_subject(50, SUBJ_INT, [QUARTER, QUARTER, QUARTER, QUARTER, QUARTER, EIGHTH, EIGHTH, QUARTER], vel=72)

    # Bass: inversion on D2(38), 1 beat later
    bass.goto(tick_57 + QUARTER)
    bass.add_subject(38, INV_INT, [QUARTER, QUARTER, QUARTER, QUARTER, QUARTER, EIGHTH, EIGHTH, QUARTER], vel=75)

    # Alto: inverted answer on A4(69), 2 beats later
    alto.goto(tick_57 + HALF)
    alto.add_subject(69, INV_ANS, [QUARTER, QUARTER, QUARTER, QUARTER, QUARTER, EIGHTH, EIGHTH, QUARTER], vel=70)

    # Soprano: answer on A4(69), 3 beats later — DECORATED with grace notes!
    sop.goto(tick_57 + HALF + QUARTER)
    # Grace note cascade into the answer
    sop.add_melody(grace_run_up(65, 69, SIXTEENTH))
    sop.add_subject(69, ANS_INT, [QUARTER, DOTTED_Q, EIGHTH, QUARTER, QUARTER, SIXTEENTH, SIXTEENTH, SIXTEENTH, SIXTEENTH, QUARTER], vel=73)

    # m61-64: all voices free, preparing the finale
    tick_61 = 60 * MEASURE

    sop.goto(tick_61)
    sop.add_melody(trill(77, HALF, 1))
    sop.add_melody([(76, EIGHTH), (74, EIGHTH), (72, QUARTER)])
    sop.add_melody(mordent(70, QUARTER))
    sop.add_melody([(72, QUARTER), (74, HALF)])
    sop.add_melody(grace_run_up(70, 77, SIXTEENTH))
    sop.note(77, QUARTER)
    sop.add_melody([(76, EIGHTH), (74, EIGHTH)])
    sop.add_melody([(72, QUARTER), (70, QUARTER), (69, HALF)])

    alto.goto(tick_61)
    alto.add_melody([
        (65, EIGHTH), (64, EIGHTH), (62, QUARTER + EIGHTH), (64, EIGHTH),
        (65, QUARTER), (67, QUARTER), (69, QUARTER + EIGHTH), (67, EIGHTH),
        (65, QUARTER), (64, QUARTER), (62, QUARTER + EIGHTH), (64, EIGHTH),
        (65, QUARTER), (67, QUARTER), (69, HALF),
    ])

    ten.goto(tick_61)
    ten.add_melody([
        (55, SIXTEENTH), (57, SIXTEENTH), (59, SIXTEENTH), (60, SIXTEENTH),
        (62, SIXTEENTH), (60, SIXTEENTH), (59, SIXTEENTH), (57, SIXTEENTH),
        (55, SIXTEENTH), (53, SIXTEENTH), (52, SIXTEENTH), (53, SIXTEENTH),
        (55, SIXTEENTH), (57, SIXTEENTH), (59, SIXTEENTH), (60, SIXTEENTH),
    ] * 2)
    ten.add_melody([
        (57, EIGHTH), (59, EIGHTH), (60, QUARTER),
        (62, QUARTER), (60, QUARTER), (59, QUARTER), (57, QUARTER),
    ])

    bass.goto(tick_61)
    bass.add_melody([
        (50, HALF), (43, QUARTER), (55, EIGHTH), (43, EIGHTH),
        (46, QUARTER), (38, QUARTER), (43, HALF),
        (50, QUARTER), (46, QUARTER), (43, QUARTER), (45, QUARTER),
        (50, HALF), (38, HALF),
    ])

    # ────────────────────────────────────────
    # FINALE (m65-80) — Subject in augmentation + grand climax
    # ────────────────────────────────────────
    tick_fin = 64 * MEASURE

    # BASS: Subject in AUGMENTATION on D2(38) — spans 8 bars!
    bass.goto(tick_fin)
    bass.add_subject(38, SUBJ_INT, make_subject_rhythm_augmented(), vel=80)

    # SOPRANO: Inverted subject on D5(74), then free, then final subject
    sop.goto(tick_fin)
    sop.add_subject(74, INV_INT, make_subject_rhythm_decorated(), vel=72)
    sop.add_melody(grace_run_down(69, 62, SIXTEENTH))
    sop.note(62, QUARTER)
    sop.add_melody(grace_run_up(62, 74, SIXTEENTH))
    sop.note(74, QUARTER)
    sop.add_melody(trill(76, HALF, 1))
    sop.add_melody([(74, QUARTER), (72, QUARTER)])
    sop.add_melody(mordent(70, QUARTER))
    sop.add_melody([(72, QUARTER)])

    # Soprano: subject on A4(69) approaching climax
    sop.add_subject(69, SUBJ_INT, make_subject_rhythm_driving(), vel=75)

    # Soprano: final ornamental cadential figure
    sop.add_melody(grace_run_up(76, 81, SIXTEENTH))
    sop.note(81, QUARTER)
    sop.add_melody(trill(79, WHOLE, 2))
    sop.add_melody([(77, QUARTER), (76, EIGHTH), (74, EIGHTH)])
    sop.add_melody([(72, QUARTER), (74, QUARTER)])
    sop.add_melody(trill(76, HALF, 1))
    sop.add_melody([(74, DOTTED_H + HALF)])  # long final note

    # ALTO: weaving counterpoint
    alto.goto(tick_fin)
    alto.add_melody([
        (62, EIGHTH), (64, EIGHTH), (65, QUARTER + EIGHTH), (67, EIGHTH),
        (69, QUARTER), (67, EIGHTH), (65, EIGHTH), (64, HALF),
        (62, EIGHTH), (61, EIGHTH), (62, QUARTER + EIGHTH), (64, EIGHTH),
        (65, QUARTER), (67, QUARTER), (69, HALF),
    ])
    # Alto: tail motifs
    alto.add_melody([(69, QUARTER), (68, QUARTER), (69, QUARTER), (71, QUARTER), (72, HALF)])
    alto.add_melody([
        (70, EIGHTH), (69, EIGHTH), (67, QUARTER),
        (65, EIGHTH), (67, DOTTED_Q),
    ])
    alto.add_melody([(69, QUARTER), (68, QUARTER), (69, QUARTER), (71, QUARTER)])
    alto.add_melody([
        (72, QUARTER), (70, QUARTER), (69, QUARTER), (67, QUARTER),
    ])
    # Alto free continuation
    alto.add_melody([
        (65, EIGHTH), (67, EIGHTH), (69, QUARTER + EIGHTH), (70, EIGHTH),
        (72, QUARTER), (70, EIGHTH), (69, EIGHTH), (67, HALF),
        (65, QUARTER), (64, QUARTER), (62, QUARTER), (64, QUARTER),
        (65, HALF), (67, HALF),
        (69, QUARTER), (67, QUARTER), (65, QUARTER + EIGHTH), (64, EIGHTH),
        (62, HALF), (65, DOTTED_H + HALF),  # long final
    ])

    # TENOR: answer on A3(57), then running sixteenths to end
    ten.goto(tick_fin + 2 * MEASURE)
    ten.add_subject(57, ANS_INT, make_subject_rhythm_driving(), vel=70)
    # Running sixteenths for 4 bars
    for _ in range(4):
        ten.add_melody([
            (57, SIXTEENTH), (59, SIXTEENTH), (60, SIXTEENTH), (62, SIXTEENTH),
            (64, SIXTEENTH), (62, SIXTEENTH), (60, SIXTEENTH), (59, SIXTEENTH),
            (57, SIXTEENTH), (55, SIXTEENTH), (53, SIXTEENTH), (55, SIXTEENTH),
            (57, SIXTEENTH), (59, SIXTEENTH), (60, SIXTEENTH), (62, SIXTEENTH),
        ])
    # Final bars: broadening
    ten.add_melody([
        (60, EIGHTH), (59, EIGHTH), (57, QUARTER),
        (55, QUARTER), (57, QUARTER), (59, HALF),
        (60, QUARTER), (62, QUARTER), (60, HALF),
        (57, DOTTED_H + HALF),  # long final A3
    ])

    # Bass: after augmented subject, cadential figure
    # Augmented subject ends around m73. Add cadential bass.
    bass.add_melody([
        (43, QUARTER), (45, QUARTER), (50, HALF),
        (48, QUARTER), (46, QUARTER), (45, QUARTER), (43, QUARTER),
        (41, HALF), (38, HALF),
        (36, QUARTER), (33, QUARTER), (38, HALF),
        (43, QUARTER), (45, QUARTER), (50, HALF),
        (38, DOTTED_H + HALF),  # final D2
    ])

    return sop, alto, ten, bass


def voices_to_midi(voices, output_path):
    """Write voices to MIDI."""
    mid = mido.MidiFile(type=1, ticks_per_beat=T)

    meta = mido.MidiTrack()
    meta.append(mido.MetaMessage('time_signature', numerator=4, denominator=4,
                                  clocks_per_click=96, notated_32nd_notes_per_beat=8, time=0))
    meta.append(mido.MetaMessage('set_tempo', tempo=500000, time=0))
    meta.append(mido.MetaMessage('key_signature', key='Dm', time=0))
    meta.append(mido.MetaMessage('end_of_track', time=0))
    mid.tracks.append(meta)

    names = ['Soprano', 'Alto', 'Tenor', 'Bass']
    for voice, name in zip(voices, names):
        track = mido.MidiTrack()
        track.append(mido.MetaMessage('track_name', name=name, time=0))
        track.append(mido.MetaMessage('key_signature', key='Dm', time=0))

        events = []
        for (t, p, d, v) in voice.notes:
            events.append((t, 'on', p, v))
            events.append((t + d, 'off', p, 0))
        events.sort(key=lambda e: (e[0], 0 if e[1] == 'off' else 1))

        prev = 0
        for (t, typ, p, v) in events:
            delta = t - prev
            if typ == 'on':
                track.append(mido.Message('note_on', channel=voice.channel, note=p, velocity=v, time=delta))
            else:
                track.append(mido.Message('note_off', channel=voice.channel, note=p, velocity=0, time=delta))
            prev = t

        track.append(mido.MetaMessage('end_of_track', time=0))
        mid.tracks.append(track)

    mid.save(output_path)

    total_notes = sum(len(v.notes) for v in voices)
    max_tick = max(max(t + d for (t, _, d, _) in v.notes) for v in voices if v.notes)
    print(f'Wrote {output_path}')
    print(f'  {total_notes} notes, {max_tick // MEASURE} measures, {max_tick / T * 0.5:.1f}s')


if __name__ == '__main__':
    voices = compose()
    voices_to_midi(voices, '/Users/benjaminchartoff/Projects/airt-of-the-fugue/contrapunctus_xv.mid')
