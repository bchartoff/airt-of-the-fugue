#!/usr/bin/env python3
"""Compose Contrapunctus XV — progressive layered electronic fugue.

Bach's Art of the Fugue subject, gradually layered across 12 voices.
Not EDM — no drops. Think Nils Frahm meets Bach: slow build, melodic
variations accumulate, voices enter one at a time, then thin back out.

Voices:
  Lead:     main melody, subject statements
  Pad:      sustained chords, slow evolving
  Arp:      arpeggiated chord tones, sixteenths/thirty-seconds
  Sub Bass: root pedals, low sine wave
  Pluck:    staccato rapid-fire subject fragments (the star)
  Stab:     sparse off-beat chord accents
  Hi-Hat:   minimal rhythmic texture
  Kick:     gentle pulse, enters late
  Clap:     sparse accents
  FX Rise:  textural sweeps
  Acid:     subject in all four forms, staccato cycling
  Supersaw: thick sustained subject for climax

Structure (80 bars at ~110 BPM):
  m1-8:    A — Solo: Pad + Lead alone
  m9-16:   B — Echo: Lead repeats, Pluck enters with staccato subject
  m17-28:  C — Conversation: Acid joins, call & response with Pluck
  m29-44:  D — Accumulation: all melodic voices, rapid pluck fragments
  m45-60:  E — Density: stretto, maximum melodic layering
  m61-72:  F — Thinning: voices drop out, fading
  m73-80:  G — Coda: Pad + Lead, dissolves
"""

import mido

# ── Tick constants (110 BPM → tempo=545454) ──
T = 384
WHOLE    = T * 4
DOTTED_H = T * 3
HALF     = T * 2
DOTTED_Q = T + T // 2
QUARTER  = T
EIGHTH   = T // 2
SIXTEENTH = T // 4
THIRTYSECOND = T // 8
MEASURE  = T * 4
TEMPO    = 545454  # ~110 BPM

# Subject intervals
SUBJ = [7, -4, -3, -1, 1, 2, 1]
INV  = [-7, 4, 3, 1, -1, -2, -1]
ANS  = [5, -2, -3, -1, 1, 2, 1]
INV_ANS = [-5, 2, 3, 1, -1, -2, -1]

# Chord tones
CHORDS = {
    'm':   [0, 3, 7],
    'M':   [0, 4, 7],
    '7':   [0, 4, 7, 10],
    'dim': [0, 3, 6],
}

# ── Harmonic plan (per half-bar, 2 beats each) ──
# Slower harmonic rhythm — chords change every 2-4 bars mostly.
# Dm-centered with gentle modal borrowing.

def _h(bars, chords):
    """Expand a chord list to half-bar granularity for N bars."""
    out = []
    per_bar = len(chords)
    if per_bar == 1:
        return chords * (bars * 2)
    # Distribute chords evenly across bars
    total_halves = bars * 2
    per_chord = total_halves // per_bar
    for c in chords:
        out.extend([c] * per_chord)
    # Pad if needed
    while len(out) < total_halves:
        out.append(chords[-1])
    return out[:total_halves]

# Section A: m1-8 — pure Dm
H_A = _h(8, [(2,'m')])

# Section B: m9-16 — Dm with gentle motion to Gm and A7
H_B = _h(4, [(2,'m')]) + _h(2, [(7,'m')]) + _h(2, [(9,'7')])

# Section C: m17-28 — more harmonic variety
H_C = (
    _h(4, [(2,'m'), (10,'M')]) +     # m17-20
    _h(4, [(5,'M'), (9,'7')]) +       # m21-24
    _h(4, [(2,'m'), (7,'m')])         # m25-28
)

# Section D: m29-44 — richer progression
H_D = (
    _h(4, [(2,'m'), (10,'M')]) +     # m29-32
    _h(4, [(0,'7'), (9,'7')]) +       # m33-36
    _h(4, [(2,'m'), (5,'M')]) +       # m37-40
    _h(4, [(7,'m'), (9,'7')])         # m41-44
)

# Section E: m45-60 — harmonic tension
H_E = (
    _h(4, [(2,'m'), (10,'M')]) +     # m45-48
    _h(4, [(0,'7'), (9,'7')]) +       # m49-52
    _h(4, [(5,'M'), (7,'m')]) +       # m53-56
    _h(4, [(9,'7'), (2,'m')])         # m57-60
)

# Section F: m61-72 — returning home
H_F = (
    _h(4, [(2,'m'), (7,'m')]) +       # m61-64
    _h(4, [(10,'M'), (9,'7')]) +      # m65-68
    _h(4, [(2,'m')])                  # m69-72
)

# Section G: m73-80 — Dm pedal
H_G = _h(8, [(2,'m')])

ALL_H = H_A + H_B + H_C + H_D + H_E + H_F + H_G

def harm(tick):
    idx = tick // HALF
    idx = max(0, min(idx, len(ALL_H) - 1))
    return ALL_H[idx]

def chord_pitches(root_pc, qual, base_oct_pitch):
    """Get chord tones near a base pitch."""
    offsets = CHORDS[qual]
    base = base_oct_pitch
    while (base % 12) != root_pc:
        base += 1
    return [base + o for o in offsets]


class V:
    """Voice builder."""
    def __init__(self, ch):
        self.ch = ch
        self.notes = []
        self.c = 0  # cursor

    def n(self, pitch, dur, vel=80):
        self.notes.append((self.c, pitch, dur, vel))
        self.c += dur

    def r(self, dur):
        self.c += dur

    def go(self, tick):
        self.c = tick

    def mel(self, pairs, vel=80):
        for p, d in pairs:
            self.n(p, d, vel)

    def subj(self, start, intervals, rhythm, vel=80):
        p = start
        self.n(p, rhythm[0], vel)
        for i, iv in enumerate(intervals):
            p += iv
            self.n(p, rhythm[min(i+1, len(rhythm)-1)], vel)


def compose():
    # 12 voices: channels 0-11
    lead     = V(0)
    pad      = V(1)
    arp      = V(2)
    sub      = V(3)
    pluck    = V(4)
    stab     = V(5)
    hihat    = V(6)
    kick     = V(7)
    clap     = V(8)
    fx       = V(9)
    acid     = V(10)
    ssaw     = V(11)

    # Rhythm templates
    R_BASIC  = [HALF, HALF, HALF, HALF, HALF, QUARTER, QUARTER, HALF]
    R_DRIVE  = [QUARTER, QUARTER, QUARTER, QUARTER, QUARTER, EIGHTH, EIGHTH, HALF]
    R_SHORT  = [EIGHTH, EIGHTH, EIGHTH, EIGHTH, EIGHTH, SIXTEENTH, SIXTEENTH, QUARTER]
    R_AUG    = [WHOLE, WHOLE, WHOLE, WHOLE, WHOLE, HALF, HALF, WHOLE]
    R_DOTTED = [DOTTED_Q, EIGHTH, DOTTED_Q, EIGHTH, HALF, EIGHTH, EIGHTH, DOTTED_Q]
    R_PLUCK  = [SIXTEENTH] * 8

    # Helper: add a chord pad for N bars starting at tick
    def pad_chord(tick, bars, vel=45):
        rpc, qual = harm(tick)
        for p in chord_pitches(rpc, qual, 55):
            pad.notes.append((tick, p, bars * MEASURE, vel))
        for p in chord_pitches(rpc, qual, 67):
            pad.notes.append((tick, p, bars * MEASURE, int(vel * 0.7)))

    # Helper: arp pattern for one bar
    def arp_bar(tick, dur=SIXTEENTH, vel=55):
        rpc, qual = harm(tick)
        base = 62
        while (base % 12) != rpc:
            base += 1
        if base > 72:
            base -= 12
        pts = chord_pitches(rpc, qual, base)
        pts_ext = pts + [p + 12 for p in pts] + [p + 24 for p in pts[:2]]
        notes_per_bar = MEASURE // dur
        arp.go(tick)
        for i in range(notes_per_bar):
            arp.n(pts_ext[i % len(pts_ext)], dur, vel)

    # Helper: sub bass root for one bar
    def sub_bar(tick, dur=HALF, vel=80):
        rpc, _ = harm(tick)
        bass_p = 26 + rpc
        if bass_p < 28:
            bass_p += 12
        notes_per_bar = MEASURE // dur
        sub.go(tick)
        for _ in range(notes_per_bar):
            sub.n(bass_p, dur, vel)

    # Helper: simple kick pattern for one bar
    def kick_bar(tick, vel=75, pattern='half'):
        kick.go(tick)
        if pattern == 'half':
            kick.n(36, EIGHTH, vel)
            kick.r(HALF - EIGHTH)
            kick.n(36, EIGHTH, int(vel * 0.7))
            kick.r(HALF - EIGHTH)
        elif pattern == 'quarter':
            for _ in range(4):
                kick.n(36, EIGHTH, vel)
                kick.r(QUARTER - EIGHTH)

    # Helper: hihat for one bar
    def hihat_bar(tick, vel=50, density='quarter'):
        if density == 'quarter':
            for beat in range(4):
                hihat.go(tick + beat * QUARTER)
                hihat.n(80, QUARTER, vel)
        elif density == 'eighth':
            for e in range(8):
                hihat.go(tick + e * EIGHTH)
                v = vel if e % 2 == 0 else int(vel * 1.2)
                hihat.n(80, EIGHTH, v)

    # Helper: clap on beat 3
    def clap_bar(tick, vel=65):
        clap.go(tick + 2 * QUARTER)
        clap.n(74, EIGHTH, vel)

    # Helper: off-beat stab for one bar
    def stab_bar(tick, vel=60):
        rpc, qual = harm(tick)
        pts = chord_pitches(rpc, qual, 62)
        for beat_off in [EIGHTH, QUARTER + EIGHTH, 2*QUARTER + EIGHTH, 3*QUARTER + EIGHTH]:
            for p in pts:
                stab.notes.append((tick + beat_off, p, EIGHTH, vel))

    # ════════════════════════════════════════════════
    # A: SOLO (m1-8) — Pad holds Dm, Lead plays subject
    # ════════════════════════════════════════════════

    # Pad: sustained Dm chord across 8 bars
    pad_chord(0, 8, vel=40)

    # Lead: subject, unhurried
    lead.go(MEASURE)  # start at m2 for breathing room
    lead.subj(62, SUBJ, R_BASIC, vel=75)
    # Rest, then answer
    lead.r(MEASURE)
    lead.subj(69, ANS, R_BASIC, vel=70)

    # FX: gentle texture — a slow ascending sweep m5-8
    fx.go(4 * MEASURE)
    for i in range(16):
        p = 55 + i
        fx.n(p, QUARTER, 25 + i)

    # ════════════════════════════════════════════════
    # B: ECHO (m9-16) — Lead repeats, Pluck enters
    # ════════════════════════════════════════════════
    t9 = 8 * MEASURE

    # Pad: evolving chords
    pad_chord(t9, 4, vel=45)
    pad_chord(t9 + 4 * MEASURE, 4, vel=50)

    # Lead: subject in driving rhythm
    lead.go(t9)
    lead.subj(62, SUBJ, R_DRIVE, vel=80)
    lead.subj(69, ANS, R_DRIVE, vel=75)

    # Pluck: enters! Staccato subject echo — the star of the show
    pluck.go(t9 + 2 * MEASURE)  # enters at m11
    pluck.subj(74, SUBJ, R_PLUCK, vel=60)
    pluck.r(MEASURE)
    pluck.subj(69, ANS, R_PLUCK, vel=55)
    pluck.r(MEASURE)
    # Descending repetitions
    pluck.subj(71, SUBJ, R_PLUCK, vel=62)
    pluck.r(HALF)
    pluck.subj(66, INV, R_PLUCK, vel=58)

    # Sub bass: enters with gentle root pedal
    for bar in range(8, 16):
        sub_bar(bar * MEASURE, dur=WHOLE, vel=65)

    # ════════════════════════════════════════════════
    # C: CONVERSATION (m17-28) — Acid joins, call & response
    # ════════════════════════════════════════════════
    t17 = 16 * MEASURE

    # Pad: continuous
    for group_start in range(16, 28, 4):
        pad_chord(group_start * MEASURE, 4, vel=48)

    # Lead: subject variations, different registers
    lead.go(t17)
    lead.subj(74, SUBJ, R_DRIVE, vel=80)
    lead.r(MEASURE)
    lead.subj(62, INV, R_DRIVE, vel=75)
    lead.r(MEASURE)
    lead.subj(69, ANS, R_DOTTED, vel=78)

    # Acid: enters! Subject cycling in short staccato
    acid.go(t17)
    acid.subj(50, SUBJ, R_SHORT, vel=70)
    acid.subj(57, INV, R_SHORT, vel=65)
    acid.r(HALF)
    acid.subj(45, ANS, R_SHORT, vel=72)
    acid.subj(50, INV_ANS, R_SHORT, vel=68)
    # Continue with varied pitches
    acid.r(MEASURE)
    acid.subj(52, SUBJ, R_DOTTED, vel=70)
    acid.subj(47, INV, R_SHORT, vel=65)

    # Pluck: call and response with acid
    pluck.go(t17 + 2 * MEASURE)  # m19
    pluck.subj(74, SUBJ, R_PLUCK, vel=65)
    pluck.r(MEASURE)  # acid plays
    pluck.subj(69, INV, R_PLUCK, vel=60)
    pluck.r(MEASURE)
    pluck.subj(71, ANS, R_PLUCK, vel=63)
    pluck.r(HALF)
    pluck.subj(76, SUBJ, R_PLUCK, vel=67)
    # Rapid descending cascade
    for i in range(3):
        pluck.subj(74 - i * 3, SUBJ, R_PLUCK, vel=60 + i * 3)

    # Arp: gentle sixteenths, enters at m21
    for bar in range(20, 28):
        arp_bar(bar * MEASURE, dur=SIXTEENTH, vel=45 + (bar - 20) * 2)

    # Kick: enters softly at m21
    for bar in range(20, 28):
        kick_bar(bar * MEASURE, vel=55 + (bar - 20), pattern='half')

    # Sub bass: continuous
    for bar in range(16, 28):
        sub_bar(bar * MEASURE, dur=HALF, vel=70)

    # FX: subtle texture m25-28
    fx.go(24 * MEASURE)
    for i in range(24):
        fx.n(58 + (i * 20) // 24, QUARTER, 20 + i)

    # ════════════════════════════════════════════════
    # D: ACCUMULATION (m29-44) — All melodic voices
    # ════════════════════════════════════════════════
    t29 = 28 * MEASURE

    # Pad: richer voicings
    for group_start in range(28, 44, 4):
        tick = group_start * MEASURE
        rpc, qual = harm(tick)
        for octave_base in [48, 55, 67]:
            for p in chord_pitches(rpc, qual, octave_base):
                pad.notes.append((tick, p, 4 * MEASURE, 42))

    # Lead: subject in multiple registers
    lead.go(t29)
    lead.subj(74, SUBJ, R_DRIVE, vel=82)
    lead.subj(69, INV, R_DRIVE, vel=78)
    lead.r(MEASURE)
    lead.subj(81, SUBJ, R_SHORT, vel=80)
    lead.subj(74, ANS, R_DRIVE, vel=76)
    # Higher register
    lead.r(2 * MEASURE)
    lead.subj(86, SUBJ, R_DRIVE, vel=75)
    lead.subj(81, INV, R_DOTTED, vel=72)

    # Pluck: THIS IS THE STAR — rapid descending fragments, lots of them
    pluck.go(t29)
    # Cascade 1: descending by 3 semitones
    for i in range(6):
        pluck.subj(76 - i * 3, SUBJ, R_PLUCK, vel=65 + i * 2)
    # Cascade 2: ascending by 4, inversions
    pluck.r(MEASURE)
    for i in range(4):
        pluck.subj(62 + i * 4, INV, R_PLUCK, vel=68 + i * 2)
    # Cascade 3: mixed forms
    pluck.r(HALF)
    for i in range(5):
        form = [SUBJ, ANS, INV, INV_ANS, SUBJ][i]
        pluck.subj(74 - i * 2, form, R_PLUCK, vel=70)

    # Acid: cycling through all forms with varied pitches
    acid.go(t29)
    acid.subj(50, SUBJ, R_SHORT, vel=75)
    acid.subj(57, INV, R_SHORT, vel=72)
    acid.subj(45, ANS, R_SHORT, vel=74)
    acid.subj(52, INV_ANS, R_SHORT, vel=70)
    # Second round at different pitches
    acid.subj(55, SUBJ, R_DOTTED, vel=73)
    acid.subj(48, INV, R_SHORT, vel=70)
    acid.subj(50, ANS, R_DOTTED, vel=72)
    acid.subj(57, SUBJ, R_SHORT, vel=75)

    # Supersaw: enters with augmented subject underneath
    ssaw.go(t29 + 4 * MEASURE)  # m33
    ssaw.subj(62, SUBJ, R_AUG, vel=55)

    # Stab: sparse off-beat color
    for bar in range(32, 44):
        if bar % 2 == 0:  # every other bar
            stab_bar(bar * MEASURE, vel=50 + (bar - 32))

    # Arp: sixteenths throughout, gradually louder
    for bar in range(28, 44):
        arp_bar(bar * MEASURE, dur=SIXTEENTH, vel=50 + (bar - 28))

    # Drums: kick + hihat enter, build slowly
    for bar in range(28, 44):
        intensity = (bar - 28) / 16  # 0 to 1
        kick_bar(bar * MEASURE, vel=int(60 + 20 * intensity), pattern='half')
        if bar >= 32:
            hihat_bar(bar * MEASURE, vel=int(35 + 20 * intensity), density='quarter')
        if bar >= 36:
            clap_bar(bar * MEASURE, vel=int(45 + 15 * intensity))

    # Sub: continuous, following harmony
    for bar in range(28, 44):
        sub_bar(bar * MEASURE, dur=HALF, vel=75)

    # ════════════════════════════════════════════════
    # E: DENSITY (m45-60) — Stretto, maximum melodic layering
    # ════════════════════════════════════════════════
    t45 = 44 * MEASURE

    # Pad: thick sustained chords
    for group_start in range(44, 60, 4):
        tick = group_start * MEASURE
        rpc, qual = harm(tick)
        for octave_base in [43, 55, 67, 79]:
            for p in chord_pitches(rpc, qual, octave_base):
                pad.notes.append((tick, p, 4 * MEASURE, 38))

    # Lead: stretto — subject, then overlapping entries
    lead.go(t45)
    lead.subj(74, SUBJ, R_DRIVE, vel=85)
    # Second entry overlaps 1 bar into first
    lead.go(t45 + 3 * MEASURE)
    lead.subj(81, INV, R_DRIVE, vel=80)
    # Third entry
    lead.go(t45 + 6 * MEASURE)
    lead.subj(69, ANS, R_SHORT, vel=82)
    lead.subj(74, SUBJ, R_SHORT, vel=80)
    # More stretto
    lead.r(MEASURE)
    lead.subj(81, SUBJ, R_DRIVE, vel=78)
    lead.subj(76, INV_ANS, R_SHORT, vel=75)

    # Pluck: MAXIMUM — rapid cascading everywhere
    pluck.go(t45)
    # Long cascade descending
    for i in range(8):
        pluck.subj(79 - i * 3, SUBJ, R_PLUCK, vel=72)
    # Ascending cascade with inversions
    for i in range(6):
        pluck.subj(57 + i * 4, INV, R_PLUCK, vel=68)
    # Interleaved subject/answer
    for i in range(6):
        form = SUBJ if i % 2 == 0 else ANS
        pluck.subj(74 - i * 2, form, R_PLUCK, vel=70 + i)

    # Acid: relentless cycling, building velocity
    acid.go(t45)
    for rep in range(10):
        form = [SUBJ, INV, ANS, INV_ANS][rep % 4]
        start_p = 50 + (rep % 3) * 3
        acid.subj(start_p, form, R_SHORT, vel=72 + rep * 2)

    # Supersaw: subject in drive rhythm, powerful
    ssaw.go(t45)
    ssaw.subj(74, SUBJ, R_DRIVE, vel=70)
    ssaw.subj(69, INV, R_DRIVE, vel=68)
    ssaw.subj(74, ANS, R_DRIVE, vel=72)
    ssaw.subj(81, SUBJ, R_SHORT, vel=70)

    # Stab: denser — every bar now
    for bar in range(44, 60):
        stab_bar(bar * MEASURE, vel=55)

    # Arp: thirty-second notes for maximum shimmer
    for bar in range(44, 60):
        arp_bar(bar * MEASURE, dur=THIRTYSECOND, vel=50)

    # Full drums (controlled, not overwhelming)
    for bar in range(44, 60):
        kick_bar(bar * MEASURE, vel=75, pattern='quarter')
        hihat_bar(bar * MEASURE, vel=50, density='eighth')
        clap_bar(bar * MEASURE, vel=60)

    # Sub: following harmony, quarter-note pulse
    for bar in range(44, 60):
        sub_bar(bar * MEASURE, dur=QUARTER, vel=80)

    # FX: textural sweep at peak
    fx.go(t45 + 8 * MEASURE)  # m53
    for i in range(32):
        p = 50 + (i * 30) // 32
        fx.n(p, SIXTEENTH, 25 + i * 2)

    # ════════════════════════════════════════════════
    # F: THINNING (m61-72) — Voices drop out gradually
    # ════════════════════════════════════════════════
    t61 = 60 * MEASURE

    # Pad: gentle, thinning
    pad_chord(t61, 4, vel=40)
    pad_chord(t61 + 4 * MEASURE, 4, vel=32)
    pad_chord(t61 + 8 * MEASURE, 4, vel=25)

    # Lead: one final augmented subject, then fading statements
    lead.go(t61)
    lead.subj(74, SUBJ, R_AUG, vel=70)
    # Small echo at end
    lead.go(t61 + 8 * MEASURE)
    lead.subj(62, SUBJ, R_BASIC, vel=50)

    # Pluck: continues but fading — fewer repetitions, lower velocity
    pluck.go(t61)
    for i in range(4):
        pluck.subj(74 - i * 3, SUBJ, R_PLUCK, vel=60 - i * 8)
    # One last cascade, very quiet
    pluck.r(2 * MEASURE)
    for i in range(3):
        pluck.subj(69 - i * 4, INV, R_PLUCK, vel=40 - i * 5)

    # Acid: fading subject statements
    acid.go(t61)
    acid.subj(50, SUBJ, R_SHORT, vel=60)
    acid.subj(57, INV, R_DOTTED, vel=50)
    acid.r(2 * MEASURE)
    acid.subj(50, SUBJ, R_BASIC, vel=40)

    # Arp: slowing down — back to sixteenths, fading
    for bar in range(60, 68):
        fade = 1.0 - (bar - 60) / 8
        arp_bar(bar * MEASURE, dur=SIXTEENTH, vel=int(45 * fade))

    # Supersaw: drops out after one last statement
    ssaw.go(t61)
    ssaw.subj(62, SUBJ, R_BASIC, vel=50)

    # Drums: thinning
    for bar in range(60, 68):
        fade = 1.0 - (bar - 60) / 8
        kick_bar(bar * MEASURE, vel=int(60 * fade), pattern='half')
        if bar < 64:
            hihat_bar(bar * MEASURE, vel=int(35 * fade), density='quarter')
        if bar < 62:
            clap_bar(bar * MEASURE, vel=int(40 * fade))

    # Sub: fading
    for bar in range(60, 68):
        fade = 1.0 - (bar - 60) / 8
        sub_bar(bar * MEASURE, dur=WHOLE, vel=int(65 * fade))

    # ════════════════════════════════════════════════
    # G: CODA (m73-80) — Pad + Lead, dissolving
    # ════════════════════════════════════════════════
    t73 = 72 * MEASURE

    # Pad: final Dm, slowly fading
    for p in chord_pitches(2, 'm', 55):
        pad.notes.append((t73, p, 8 * MEASURE, 30))
    for p in chord_pitches(2, 'm', 67):
        pad.notes.append((t73, p, 8 * MEASURE, 20))

    # Lead: subject one last time, very slow and quiet
    lead.go(t73 + MEASURE)
    lead.subj(62, SUBJ, R_AUG, vel=45)

    # Sub: final D pedal
    sub.go(t73)
    sub.n(38, 4 * MEASURE, 45)
    sub.n(26, 4 * MEASURE, 30)  # sub octave, dying away

    # Acid: ghost of the subject
    acid.go(t73 + 2 * MEASURE)
    acid.subj(50, SUBJ, R_BASIC, vel=30)

    return [lead, pad, arp, sub, pluck, stab, hihat, kick, clap, fx, acid, ssaw]


def voices_to_midi(voices, path):
    mid = mido.MidiFile(type=1, ticks_per_beat=T)

    meta = mido.MidiTrack()
    meta.append(mido.MetaMessage('time_signature', numerator=4, denominator=4,
                                  clocks_per_click=96, notated_32nd_notes_per_beat=8, time=0))
    meta.append(mido.MetaMessage('set_tempo', tempo=TEMPO, time=0))
    meta.append(mido.MetaMessage('key_signature', key='Dm', time=0))
    meta.append(mido.MetaMessage('end_of_track', time=0))
    mid.tracks.append(meta)

    names = ['Lead', 'Pad', 'Arp', 'Sub Bass', 'Pluck', 'Stab',
             'Hi-Hat', 'Kick', 'Clap', 'FX Rise', 'Acid', 'Supersaw']

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
                track.append(mido.Message('note_on', channel=voice.ch, note=p, velocity=v, time=delta))
            else:
                track.append(mido.Message('note_off', channel=voice.ch, note=p, velocity=0, time=delta))
            prev = t

        track.append(mido.MetaMessage('end_of_track', time=0))
        mid.tracks.append(track)

    mid.save(path)
    total = sum(len(v.notes) for v in voices)
    max_t = max(max(t+d for t,_,d,_ in v.notes) for v in voices if v.notes)
    print(f'Wrote {path}')
    print(f'  {total} notes, {max_t // MEASURE} measures, {max_t / T * (TEMPO / 1e6):.1f}s')


if __name__ == '__main__':
    voices = compose()
    voices_to_midi(voices, '/Users/benjaminchartoff/Projects/airt-of-the-fugue/contrapunctus_xv.mid')
