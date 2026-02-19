#!/usr/bin/env python3
"""Compose Contrapunctus XV — an original fugue on the Art of the Fugue subject.

Generates a MIDI file in the same format as the existing collection:
  - Type 1, 384 ticks/beat, tempo 500000 (120 BPM), 4/4
  - Tracks: 0=meta, 1=Soprano(ch0), 2=Alto(ch1), 3=Tenor(ch2), 4=Bass(ch3)

Compositional concept: "Stretto by Contrary Motion"
  The subject and its inversion are heard simultaneously from the very first
  entry, with increasingly tight stretto distances culminating in a 4-voice
  stretto where all voices enter within one measure.  Episodes develop the
  head and tail motifs sequentially.  Ends with the subject in augmentation
  in the bass under free counterpoint.

All melodic material is original counterpoint built on the AotF subject
intervals [+7, -4, -3, -1, +1, +2, +1] and their inversion.
"""

import mido

# ── Constants ──
TICKS = 384           # ticks per quarter note
HALF = TICKS * 2      # half note
WHOLE = TICKS * 4     # whole note
QUARTER = TICKS       # quarter note
EIGHTH = TICKS // 2   # eighth note
DOTTED_Q = TICKS + EIGHTH
DOTTED_H = HALF + QUARTER
MEASURE = TICKS * 4   # 4/4 time

# Subject: D A F D C# D E F  (Form A, intervals: +7,-4,-3,-1,+1,+2,+1)
# We work in MIDI pitches.  D4=62, A4=69, etc.
SUBJECT_INTERVALS = [7, -4, -3, -1, 1, 2, 1]   # 7 intervals → 8 notes
INV_INTERVALS     = [-7, 4, 3, 1, -1, -2, -1]   # exact inversion
ANSWER_INTERVALS  = [5, -2, -3, -1, 1, 2, 1]    # tonal answer
INV_ANS_INTERVALS = [-5, 2, 3, 1, -1, -2, -1]   # inverted tonal answer

# Tail intervals (last 4 of subject): -1, +1, +2, +1
TAIL = [-1, 1, 2, 1]
TAIL_INV = [1, -1, -2, -1]

# Head intervals (first 4 of subject): +7, -4, -3, -1
HEAD = [7, -4, -3, -1]


def make_melody(start_pitch, intervals, rhythm):
    """Build a list of (pitch, duration_ticks) from a start pitch, intervals, and rhythm."""
    notes = [(start_pitch, rhythm[0])]
    p = start_pitch
    for i, intv in enumerate(intervals):
        p += intv
        dur = rhythm[i + 1] if i + 1 < len(rhythm) else rhythm[-1]
        notes.append((p, dur))
    return notes


def subject(start_pitch, rhythm=None):
    """The subject in rectus form."""
    if rhythm is None:
        rhythm = [HALF, HALF, HALF, HALF, HALF, QUARTER, QUARTER, HALF]
    return make_melody(start_pitch, SUBJECT_INTERVALS, rhythm)


def subject_inv(start_pitch, rhythm=None):
    """The subject in inversion."""
    if rhythm is None:
        rhythm = [HALF, HALF, HALF, HALF, HALF, QUARTER, QUARTER, HALF]
    return make_melody(start_pitch, INV_INTERVALS, rhythm)


def answer(start_pitch, rhythm=None):
    """The tonal answer."""
    if rhythm is None:
        rhythm = [HALF, HALF, HALF, HALF, HALF, QUARTER, QUARTER, HALF]
    return make_melody(start_pitch, ANSWER_INTERVALS, rhythm)


def answer_inv(start_pitch, rhythm=None):
    """The inverted tonal answer."""
    if rhythm is None:
        rhythm = [HALF, HALF, HALF, HALF, HALF, QUARTER, QUARTER, HALF]
    return make_melody(start_pitch, INV_ANS_INTERVALS, rhythm)


def tail_motif(start_pitch, rhythm=None):
    """Just the tail: 5 notes."""
    if rhythm is None:
        rhythm = [QUARTER, QUARTER, QUARTER, QUARTER, HALF]
    return make_melody(start_pitch, TAIL, rhythm)


def tail_inv_motif(start_pitch, rhythm=None):
    if rhythm is None:
        rhythm = [QUARTER, QUARTER, QUARTER, QUARTER, HALF]
    return make_melody(start_pitch, TAIL_INV, rhythm)


def head_motif(start_pitch, rhythm=None):
    """Just the head: 5 notes."""
    if rhythm is None:
        rhythm = [HALF, HALF, HALF, HALF, HALF]
    return make_melody(start_pitch, HEAD, rhythm)


def free_line(pitches_and_durs):
    """Arbitrary melody as list of (pitch, dur) tuples."""
    return list(pitches_and_durs)


# ── Voice class for building note lists ──
class Voice:
    def __init__(self, channel):
        self.channel = channel
        self.notes = []  # (tick_start, pitch, duration_ticks, velocity)
        self.cursor = 0  # current tick position

    def rest(self, dur):
        self.cursor += dur

    def add(self, melody, velocity=68):
        """Add a melody (list of (pitch, dur)) at the current cursor."""
        for pitch, dur in melody:
            self.notes.append((self.cursor, pitch, dur, velocity))
            self.cursor += dur

    def add_at(self, tick, melody, velocity=68):
        """Add a melody starting at a specific tick."""
        self.cursor = tick
        self.add(melody, velocity)

    def hold(self, pitch, dur, velocity=68):
        """Add a single sustained note."""
        self.notes.append((self.cursor, pitch, dur, velocity))
        self.cursor += dur


# ── Compose the fugue ──
def compose():
    soprano = Voice(0)
    alto    = Voice(1)
    tenor   = Voice(2)
    bass    = Voice(3)

    # ================================================================
    # EXPOSITION (m1-16, ticks 0 to 16*MEASURE)
    # ================================================================
    # m1-4: Alto states the subject on D4(62)
    alto.add(subject(62))

    # m1-4: Soprano rests 2 measures, then enters m3 with inverted answer on A4(69)
    soprano.rest(2 * MEASURE)
    soprano.add(answer_inv(69))

    # Alto continues with free counterpoint against soprano's inversion
    # A flowing line that complements the inverted answer
    alto.add(free_line([
        (65, QUARTER), (67, QUARTER), (69, HALF),
        (67, QUARTER), (65, QUARTER), (64, QUARTER), (62, QUARTER),
        (64, HALF), (65, HALF),
        (67, QUARTER), (69, QUARTER), (70, HALF),
    ]))

    # m5-8: Tenor enters with subject on A3(57) — answer level
    tenor.rest(4 * MEASURE)
    tenor.add(answer(57))

    # Soprano free counterpoint m5-8
    soprano.add(free_line([
        (67, QUARTER), (65, QUARTER), (64, HALF),
        (62, QUARTER), (64, QUARTER), (65, QUARTER), (67, QUARTER),
        (69, HALF), (67, HALF),
        (65, QUARTER), (64, QUARTER), (62, HALF),
    ]))

    # Alto free counterpoint m5-8
    alto.add(free_line([
        (69, HALF), (67, QUARTER), (65, QUARTER),
        (64, HALF), (62, HALF),
        (60, QUARTER), (62, QUARTER), (64, QUARTER), (65, QUARTER),
        (67, HALF), (65, HALF),
    ]))

    # m9-12: Bass enters with inverted subject on D3(50)
    bass.rest(8 * MEASURE)
    bass.add(subject_inv(50))

    # Soprano m9-12: tail motif then free
    soprano.add(tail_motif(68))
    soprano.add(free_line([
        (70, QUARTER), (72, QUARTER), (74, HALF),
        (72, HALF), (70, HALF),
        (69, QUARTER), (67, QUARTER), (65, HALF),
    ]))

    # Alto m9-12: free counterpoint
    alto.add(free_line([
        (62, QUARTER), (64, QUARTER), (65, HALF),
        (67, HALF), (69, QUARTER), (67, QUARTER),
        (65, HALF), (64, HALF),
        (62, QUARTER), (61, QUARTER), (62, HALF),
    ]))

    # Tenor m9-12: free counterpoint after subject ends
    tenor.add(free_line([
        (60, QUARTER), (62, QUARTER), (64, HALF),
        (65, HALF), (64, QUARTER), (62, QUARTER),
        (60, HALF), (57, HALF),
        (55, QUARTER), (57, QUARTER), (59, HALF),
    ]))

    # m13-16: Close of exposition — all voices free, settling
    # Soprano
    soprano.add(free_line([
        (64, QUARTER), (65, QUARTER), (67, HALF),
        (69, HALF), (70, QUARTER), (69, QUARTER),
        (67, HALF), (65, HALF),
        (67, QUARTER), (69, QUARTER), (70, HALF),
    ]))

    # Alto
    alto.add(free_line([
        (64, HALF), (65, HALF),
        (67, QUARTER), (65, QUARTER), (64, QUARTER), (62, QUARTER),
        (61, HALF), (62, HALF),
        (64, QUARTER), (62, QUARTER), (61, QUARTER), (62, QUARTER),
    ]))

    # Tenor
    tenor.add(free_line([
        (57, HALF), (55, HALF),
        (53, QUARTER), (55, QUARTER), (57, HALF),
        (59, HALF), (57, HALF),
        (55, QUARTER), (57, QUARTER), (58, HALF),
    ]))

    # Bass — free after inversion ends
    bass.add(free_line([
        (48, QUARTER), (50, QUARTER), (52, HALF),
        (53, HALF), (50, HALF),
        (48, HALF), (46, HALF),
        (45, QUARTER), (46, QUARTER), (48, HALF),
    ]))

    # ================================================================
    # EPISODE 1 (m17-24) — Sequential development of head & tail
    # ================================================================
    tick_ep1 = 16 * MEASURE

    # Soprano: descending sequence using head motif fragments
    soprano.add_at(tick_ep1, free_line([
        (72, QUARTER), (74, QUARTER), (72, QUARTER), (70, QUARTER),
        (69, HALF), (67, HALF),
        (65, QUARTER), (67, QUARTER), (69, HALF),
        (70, HALF), (72, HALF),
    ]))
    # Continue
    soprano.add(free_line([
        (74, QUARTER), (72, QUARTER), (70, QUARTER), (69, QUARTER),
        (67, HALF), (65, HALF),
        (64, QUARTER), (65, QUARTER), (67, HALF),
        (69, HALF), (70, HALF),
    ]))

    # Alto: tail motif rising sequence
    alto.add_at(tick_ep1, tail_motif(61))
    alto.add(tail_motif(64))
    alto.add(free_line([
        (69, QUARTER), (67, QUARTER), (65, HALF),
        (64, HALF), (62, HALF),
        (64, QUARTER), (65, QUARTER), (67, HALF),
        (69, HALF), (67, HALF),
    ]))

    # Tenor: inverted tail sequence
    tenor.add_at(tick_ep1, tail_inv_motif(62))
    tenor.add(tail_inv_motif(59))
    tenor.add(free_line([
        (55, QUARTER), (57, QUARTER), (59, HALF),
        (60, HALF), (62, HALF),
        (60, QUARTER), (59, QUARTER), (57, HALF),
        (55, HALF), (57, HALF),
    ]))

    # Bass: long notes, harmonic support
    bass.add_at(tick_ep1, free_line([
        (50, WHOLE), (48, WHOLE),
        (46, WHOLE), (45, WHOLE),
        (43, WHOLE), (41, WHOLE),
        (38, WHOLE), (41, WHOLE),
    ]))

    # ================================================================
    # MIDDLE ENTRIES (m25-40) — Subject+Inv in new keys, stretto at 1 bar
    # ================================================================
    tick_mid = 24 * MEASURE

    # m25-28: Tenor subject on Bb3(58) — relative major area
    tenor.add_at(tick_mid, subject(58))

    # m26-29: Soprano inverted answer on F5(77) — enters 1 bar after tenor
    soprano.add_at(tick_mid + MEASURE, answer_inv(77))

    # Alto: free counterpoint m25-28
    alto.add_at(tick_mid, free_line([
        (65, HALF), (67, HALF),
        (69, QUARTER), (70, QUARTER), (72, HALF),
        (70, HALF), (69, QUARTER), (67, QUARTER),
        (65, HALF), (64, HALF),
    ]))

    # Bass: free counterpoint m25-28
    bass.add_at(tick_mid, free_line([
        (46, HALF), (48, HALF),
        (50, HALF), (53, HALF),
        (50, QUARTER), (48, QUARTER), (46, HALF),
        (45, HALF), (46, HALF),
    ]))

    # m29-32: continuation — free counterpoint in all voices
    tick_29 = 28 * MEASURE

    soprano.add_at(tick_29, free_line([
        (74, QUARTER), (72, QUARTER), (70, HALF),
        (69, HALF), (67, HALF),
        (65, QUARTER), (64, QUARTER), (62, HALF),
        (64, HALF), (65, HALF),
    ]))

    alto.add_at(tick_29, free_line([
        (62, QUARTER), (64, QUARTER), (65, HALF),
        (67, HALF), (69, QUARTER), (70, QUARTER),
        (72, HALF), (70, HALF),
        (69, QUARTER), (67, QUARTER), (65, HALF),
    ]))

    tenor.add_at(tick_29, free_line([
        (58, QUARTER), (57, QUARTER), (55, HALF),
        (53, HALF), (55, HALF),
        (57, QUARTER), (58, QUARTER), (60, HALF),
        (62, HALF), (60, HALF),
    ]))

    bass.add_at(tick_29, free_line([
        (48, HALF), (46, HALF),
        (45, HALF), (43, HALF),
        (41, HALF), (43, HALF),
        (45, QUARTER), (46, QUARTER), (48, HALF),
    ]))

    # m33-36: Bass subject on G2(43) — G minor area
    tick_33 = 32 * MEASURE
    bass.add_at(tick_33, subject(43))

    # m34-37: Alto inversion enters 1 bar later on D4(62)
    alto.add_at(tick_33 + MEASURE, subject_inv(62))

    # Soprano m33-36: free
    soprano.add_at(tick_33, free_line([
        (67, HALF), (69, HALF),
        (70, QUARTER), (72, QUARTER), (74, HALF),
        (72, HALF), (70, HALF),
        (69, QUARTER), (67, QUARTER), (65, HALF),
    ]))

    # Tenor m33-36: free
    tenor.add_at(tick_33, free_line([
        (57, HALF), (55, HALF),
        (53, QUARTER), (55, QUARTER), (57, HALF),
        (59, HALF), (60, HALF),
        (62, QUARTER), (60, QUARTER), (59, HALF),
    ]))

    # m37-40: continuation
    tick_37 = 36 * MEASURE

    soprano.add_at(tick_37, free_line([
        (64, QUARTER), (65, QUARTER), (67, HALF),
        (69, HALF), (70, HALF),
        (72, QUARTER), (70, QUARTER), (69, HALF),
        (67, HALF), (65, HALF),
    ]))

    alto.add_at(tick_37, free_line([
        (57, QUARTER), (58, QUARTER), (60, HALF),
        (62, HALF), (64, HALF),
        (65, QUARTER), (64, QUARTER), (62, HALF),
        (60, HALF), (62, HALF),
    ]))

    tenor.add_at(tick_37, free_line([
        (57, HALF), (55, HALF),
        (53, QUARTER), (52, QUARTER), (50, HALF),
        (48, HALF), (50, HALF),
        (52, QUARTER), (53, QUARTER), (55, HALF),
    ]))

    bass.add_at(tick_37, free_line([
        (46, QUARTER), (48, QUARTER), (50, HALF),
        (48, HALF), (46, HALF),
        (45, HALF), (43, HALF),
        (41, QUARTER), (43, QUARTER), (45, HALF),
    ]))

    # ================================================================
    # EPISODE 2 (m41-48) — Tail in sequence, building tension
    # ================================================================
    tick_ep2 = 40 * MEASURE

    # Rising sequence: tail in soprano, inverted tail echoed in tenor
    soprano.add_at(tick_ep2, tail_motif(69))
    soprano.add(tail_motif(72))
    soprano.add(free_line([
        (77, QUARTER), (76, QUARTER), (74, HALF),
        (72, HALF), (74, HALF),
        (76, QUARTER), (77, QUARTER), (79, HALF),
        (77, HALF), (76, HALF),
    ]))

    alto.add_at(tick_ep2, free_line([
        (62, HALF), (64, HALF),
        (65, HALF), (67, HALF),
    ]))
    alto.add(tail_inv_motif(69))
    alto.add(tail_inv_motif(67))
    alto.add(free_line([
        (62, HALF), (64, HALF),
        (65, QUARTER), (67, QUARTER), (69, HALF),
        (70, HALF), (69, HALF),
    ]))

    tenor.add_at(tick_ep2, tail_inv_motif(57))
    tenor.add(tail_inv_motif(55))
    tenor.add(free_line([
        (50, QUARTER), (52, QUARTER), (53, HALF),
        (55, HALF), (57, HALF),
        (58, QUARTER), (57, QUARTER), (55, HALF),
        (53, HALF), (55, HALF),
    ]))

    bass.add_at(tick_ep2, free_line([
        (45, WHOLE), (43, WHOLE),
        (41, WHOLE), (38, WHOLE),
        (36, WHOLE), (38, WHOLE),
        (41, WHOLE), (43, WHOLE),
    ]))

    # ================================================================
    # STRETTO (m49-64) — Tight stretto, all 4 voices within 1 measure
    # ================================================================
    tick_str = 48 * MEASURE

    # m49: Alto subject on D4(62)
    alto.add_at(tick_str, subject(62))

    # m49 beat 3: Soprano inverted subject on A4(69) — enters 2 beats later
    soprano.add_at(tick_str + HALF, subject_inv(69))

    # m50: Tenor answer on A3(57) — enters 1 bar after alto
    tenor.add_at(tick_str + MEASURE, answer(57))

    # m50 beat 3: Bass inverted answer on D3(50) — enters 2 beats after tenor
    bass.add_at(tick_str + MEASURE + HALF, answer_inv(50))

    # Free counterpoint after each voice finishes its subject statement
    # m53-56: Alto free (subject ended)
    tick_53 = 52 * MEASURE
    alto.add_at(tick_53, free_line([
        (65, QUARTER), (67, QUARTER), (69, HALF),
        (70, HALF), (69, QUARTER), (67, QUARTER),
        (65, HALF), (64, HALF),
        (62, QUARTER), (64, QUARTER), (65, HALF),
    ]))

    # Soprano free m53-56
    soprano.add_at(tick_53 + HALF, free_line([
        (64, QUARTER), (65, QUARTER),
        (67, HALF), (69, HALF),
        (70, QUARTER), (72, QUARTER), (74, HALF),
        (72, HALF), (70, HALF),
    ]))

    # m55-56: Tenor free
    tick_55 = 54 * MEASURE
    tenor.add_at(tick_55, free_line([
        (60, QUARTER), (62, QUARTER), (64, HALF),
        (65, HALF), (62, HALF),
        (60, QUARTER), (59, QUARTER), (57, HALF),
    ]))

    # Bass free m55-56
    bass.add_at(tick_55 + HALF, free_line([
        (46, QUARTER), (48, QUARTER),
        (50, HALF), (48, HALF),
        (46, QUARTER), (45, QUARTER), (43, HALF),
    ]))

    # m57-60: Second stretto round, even tighter — all enter within 2 beats
    tick_57 = 56 * MEASURE

    # Tenor subject on D3(50)
    tenor.add_at(tick_57, subject(50))

    # Bass inversion on D2(38) — 1 beat later
    bass.add_at(tick_57 + QUARTER, subject_inv(38))

    # Alto inverted answer on A4(69) — 2 beats later
    alto.add_at(tick_57 + HALF, answer_inv(69))

    # Soprano answer on A4(69) — 3 beats later
    soprano.add_at(tick_57 + HALF + QUARTER, answer(69))

    # Free counterpoint m61-64 to bridge to final section
    tick_61 = 60 * MEASURE

    soprano.add_at(tick_61, free_line([
        (74, HALF), (72, HALF),
        (70, QUARTER), (69, QUARTER), (67, HALF),
        (69, HALF), (70, HALF),
        (72, QUARTER), (74, QUARTER), (76, HALF),
    ]))

    alto.add_at(tick_61, free_line([
        (65, QUARTER), (64, QUARTER), (62, HALF),
        (61, HALF), (62, HALF),
        (64, QUARTER), (65, QUARTER), (67, HALF),
        (69, HALF), (67, HALF),
    ]))

    tenor.add_at(tick_61, free_line([
        (55, QUARTER), (57, QUARTER), (58, HALF),
        (60, HALF), (58, HALF),
        (57, QUARTER), (55, QUARTER), (53, HALF),
        (55, HALF), (57, HALF),
    ]))

    bass.add_at(tick_61, free_line([
        (43, HALF), (45, HALF),
        (46, HALF), (48, HALF),
        (50, QUARTER), (48, QUARTER), (46, HALF),
        (45, HALF), (43, HALF),
    ]))

    # ================================================================
    # FINAL SECTION (m65-80) — Subject in augmentation + climax
    # ================================================================
    tick_fin = 64 * MEASURE

    # Bass: subject in AUGMENTATION on D2(38) — each note doubled in length
    aug_rhythm = [WHOLE, WHOLE, WHOLE, WHOLE, WHOLE, HALF, HALF, WHOLE]
    bass.add_at(tick_fin, subject(38, rhythm=aug_rhythm))

    # Soprano: inverted subject at normal speed on D5(74), then again
    soprano.add_at(tick_fin, subject_inv(74))
    soprano.add(free_line([
        (72, QUARTER), (74, QUARTER), (76, HALF),
        (77, HALF), (76, QUARTER), (74, QUARTER),
        (72, HALF), (70, HALF),
        (69, QUARTER), (70, QUARTER), (72, HALF),
    ]))
    # Soprano: subject statement approaching the end (m73)
    soprano.add(subject(69))

    # Alto: free counterpoint, weaving between soprano and tenor
    alto.add_at(tick_fin, free_line([
        (62, HALF), (64, HALF),
        (65, HALF), (67, HALF),
        (69, QUARTER), (67, QUARTER), (65, HALF),
        (64, HALF), (62, HALF),
    ]))
    alto.add(free_line([
        (61, QUARTER), (62, QUARTER), (64, HALF),
        (65, HALF), (67, HALF),
        (69, HALF), (70, HALF),
        (72, QUARTER), (70, QUARTER), (69, HALF),
    ]))
    alto.add(free_line([
        (67, HALF), (65, HALF),
        (64, QUARTER), (62, QUARTER), (61, HALF),
        (62, HALF), (64, HALF),
        (65, QUARTER), (67, QUARTER), (69, HALF),
    ]))
    # Alto tail to end
    alto.add(tail_motif(68))
    alto.add(free_line([
        (70, QUARTER), (69, QUARTER), (67, HALF),
    ]))

    # Tenor: subject on A3(57), starting m67
    tenor.add_at(tick_fin, free_line([
        (57, HALF), (55, HALF),
        (53, QUARTER), (55, QUARTER), (57, HALF),
    ]))
    tenor.add_at(tick_fin + 2 * MEASURE, answer(57))
    tenor.add(free_line([
        (60, QUARTER), (62, QUARTER), (64, HALF),
        (62, HALF), (60, HALF),
        (59, QUARTER), (60, QUARTER), (62, HALF),
        (64, HALF), (62, HALF),
    ]))
    tenor.add(free_line([
        (60, QUARTER), (59, QUARTER), (57, HALF),
        (55, HALF), (53, HALF),
        (52, QUARTER), (53, QUARTER), (55, HALF),
        (57, HALF), (58, HALF),
    ]))

    # m77-80: Final cadential approach
    tick_77 = 76 * MEASURE

    # Soprano: decorated descent to final D5
    soprano.add_at(tick_77, free_line([
        (72, QUARTER), (74, QUARTER), (76, HALF),
        (77, HALF), (76, QUARTER), (74, QUARTER),
        (72, HALF), (70, HALF),
        (69, HALF), (74, DOTTED_H + QUARTER),  # final D5, long
    ]))

    # Alto: inner voice resolution
    alto.add_at(tick_77, free_line([
        (65, HALF), (67, HALF),
        (69, QUARTER), (67, QUARTER), (65, HALF),
        (64, HALF), (65, HALF),
        (66, HALF), (65, DOTTED_H + QUARTER),  # A4 (tierce de Picardie? no, stay minor)
    ]))

    # Tenor: resolution
    tenor.add_at(tick_77, free_line([
        (57, HALF), (55, HALF),
        (53, QUARTER), (55, QUARTER), (57, HALF),
        (58, HALF), (57, HALF),
        (55, HALF), (57, DOTTED_H + QUARTER),  # A3
    ]))

    # Bass: cadential bass D2
    bass.add_at(tick_77, free_line([
        (43, HALF), (41, HALF),
        (38, HALF), (36, HALF),
        (34, HALF), (33, HALF),
        (36, HALF), (38, DOTTED_H + QUARTER),  # D2 final
    ]))

    return soprano, alto, tenor, bass


def voices_to_midi(soprano, alto, tenor, bass, output_path):
    """Write the four voices to a MIDI file in the project's format."""
    mid = mido.MidiFile(type=1, ticks_per_beat=TICKS)

    # Track 0: meta
    meta_track = mido.MidiTrack()
    meta_track.append(mido.MetaMessage('time_signature', numerator=4, denominator=4,
                                        clocks_per_click=96, notated_32nd_notes_per_beat=8, time=0))
    meta_track.append(mido.MetaMessage('set_tempo', tempo=500000, time=0))
    meta_track.append(mido.MetaMessage('key_signature', key='Dm', time=0))
    meta_track.append(mido.MetaMessage('end_of_track', time=0))
    mid.tracks.append(meta_track)

    voices = [soprano, alto, tenor, bass]
    names = ['Soprano', 'Alto', 'Tenor', 'Bass']

    for voice, name in zip(voices, names):
        track = mido.MidiTrack()
        track.append(mido.MetaMessage('track_name', name=name, time=0))
        track.append(mido.MetaMessage('key_signature', key='Dm', time=0))

        # Build events sorted by time
        events = []
        for (tick_start, pitch, dur, vel) in voice.notes:
            events.append((tick_start, 'on', pitch, vel))
            events.append((tick_start + dur, 'off', pitch, 0))

        events.sort(key=lambda e: (e[0], 0 if e[1] == 'off' else 1))

        prev_tick = 0
        for (tick, typ, pitch, vel) in events:
            delta = tick - prev_tick
            if typ == 'on':
                track.append(mido.Message('note_on', channel=voice.channel,
                                           note=pitch, velocity=vel, time=delta))
            else:
                track.append(mido.Message('note_off', channel=voice.channel,
                                           note=pitch, velocity=0, time=delta))
            prev_tick = tick

        track.append(mido.MetaMessage('end_of_track', time=0))
        mid.tracks.append(track)

    mid.save(output_path)
    print(f'Wrote {output_path}')
    total_ticks = max(max(t + d for (t, _, d, _) in v.notes) for v in voices if v.notes)
    total_sec = total_ticks / TICKS * 0.5  # at 120 BPM, 1 beat = 0.5s
    total_measures = total_ticks // MEASURE
    total_notes = sum(len(v.notes) for v in voices)
    print(f'  {total_notes} notes, {total_measures} measures, {total_sec:.1f}s')


if __name__ == '__main__':
    s, a, t, b = compose()
    voices_to_midi(s, a, t, b, '/Users/benjaminchartoff/Projects/airt-of-the-fugue/contrapunctus_xv.mid')
