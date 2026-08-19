"""
JSON validator — validates the completeness and legality of score JSON data

Provides the validate() function to check the AI Muse score JSON structure,
including required fields, type checks, range checks, and duration validity,
and auto-fills missing default values.
"""

# Base duration set
_BASE_DURATIONS = {"whole", "half", "quarter", "eighth", "16th", "32nd", "64th"}

# Valid tuplet types (actual note count)
_VALID_TUPLETS = {3, 5, 6, 7, 9}

# Valid articulation types
_VALID_ARTICULATIONS = {
    "staccato", "staccatissimo", "accent", "tenuto", "marcato", "sforzando"
}

# Valid dynamics markings
_VALID_DYNAMICS = {
    "pppp", "ppp", "pp", "p", "mp", "mf", "f", "ff", "fff", "ffff",
    "sfz", "sf", "fz", "rfz", "sffz",
    "fp", "sfp",
    "crescendo", "diminuendo",
    "calando", "morendo", "smorzando", "rinforzando",
}

# Valid ornament types
_VALID_ORNAMENTS = {
    "trill", "mordent", "inverted_mordent", "turn", "inverted_turn"
}

# Default values
_DEFAULT_TITLE = "Untitled"
_DEFAULT_COMPOSER = "Unknown"
_DEFAULT_VELOCITY = 80


def _is_valid_duration(duration_str: str) -> bool:
    """
    Check whether a duration string is valid.

    Valid durations are base types (whole/half/quarter/eighth/16th/32nd/64th)
    with an optional "." suffix for dotted notes.

    Args:
        duration_str: The duration string to validate.

    Returns:
        bool: True if the duration is valid, False otherwise.
    """
    if not isinstance(duration_str, str):
        return False
    base = duration_str.rstrip(".")
    dot_count = len(duration_str) - len(base)
    if dot_count > 1:
        return False
    return base in _BASE_DURATIONS


def validate(json_data: dict) -> tuple:
    """
    Validate the completeness and legality of a score JSON dictionary, and auto-fill
    missing default values.

    Validation rules:
      - metadata must exist with tempo_bpm (int) and time_signature (string "x/y")
      - tracks must exist and be a non-empty array
      - each track must have instrument (string) and notes (non-empty array)
      - each note must have pitch (int or None, -1 for rest) and duration (string)
      - pitch must be in 21-108 range if provided as an integer
      - duration must be a valid duration string
      - velocity is optional (default 80), must be 0-127 if provided
      - articulation, dynamics, tie, slur, lyric, etc. are optional with constraints
      - chord, time_signature_change, key_signature_change, arpeggio, tremolo,
        glissando, navigation, hairpin, tempo_gradual, subito, expression are optional
      - Fills in missing defaults: title, composer, velocity

    Args:
        json_data: The score JSON dictionary to validate.

    Returns:
        tuple: (is_valid, errors), where is_valid is a bool and errors is a list of
               error message strings (empty if valid).
    """
    errors = []

    # ---------- Type check ----------
    if not isinstance(json_data, dict):
        errors.append("JSON data must be an object (not an array or scalar)")
        return (False, errors)

    # ---------- Fill defaults ----------
    if "title" not in json_data or json_data.get("title") is None:
        json_data["title"] = _DEFAULT_TITLE
    if "composer" not in json_data or json_data.get("composer") is None:
        json_data["composer"] = _DEFAULT_COMPOSER

    # ---------- metadata validation ----------
    metadata = json_data.get("metadata")
    if metadata is None or not isinstance(metadata, dict):
        errors.append("metadata must exist and be an object")
    else:
        tempo = metadata.get("tempo_bpm")
        if tempo is None or not isinstance(tempo, int):
            errors.append("metadata.tempo_bpm must exist and be an integer")

        time_sig = metadata.get("time_signature")
        if time_sig is None or not isinstance(time_sig, str):
            errors.append("metadata.time_signature must exist and be a string")
        else:
            parts = time_sig.split("/")
            if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
                errors.append("metadata.time_signature format must be x/y (e.g. 4/4)")

    # ---------- tracks validation ----------
    tracks = json_data.get("tracks")
    if tracks is None or not isinstance(tracks, list):
        errors.append("tracks must exist and be an array")
    elif len(tracks) == 0:
        errors.append("tracks cannot be an empty array")
    else:
        for t_idx, track in enumerate(tracks):
            track_num = t_idx + 1

            if not isinstance(track, dict):
                errors.append(f"Track {track_num} must be an object")
                continue

            instrument = track.get("instrument")
            if instrument is None or not isinstance(instrument, str):
                errors.append(f"Track {track_num} instrument must exist and be a string")

            notes = track.get("notes")
            if notes is None or not isinstance(notes, list):
                errors.append(f"Track {track_num} notes must exist and be an array")
            elif len(notes) == 0:
                errors.append(f"Track {track_num} notes cannot be an empty array")
            else:
                for n_idx, note in enumerate(notes):
                    note_num = n_idx + 1

                    if not isinstance(note, dict):
                        errors.append(f"Track {track_num}, note {note_num} must be an object")
                        continue

                    # pitch validation (optional if chord is present)
                    pitch = note.get("pitch")
                    has_chord = note.get("chord") is not None
                    if pitch is None and not has_chord:
                        errors.append(f"Track {track_num}, note {note_num} pitch must exist (or provide chord)")
                    elif pitch is not None and not isinstance(pitch, int):
                        errors.append(f"Track {track_num}, note {note_num} pitch must be an integer or null (-1 for rest)")
                    elif pitch is not None and pitch != -1 and (pitch < 21 or pitch > 108):
                        errors.append(
                            f"Track {track_num}, note {note_num} pitch value {pitch} out of range 21-108"
                        )

                    # duration validation
                    duration = note.get("duration")
                    if duration is None or not isinstance(duration, str):
                        errors.append(f"Track {track_num}, note {note_num} duration must exist and be a string")
                    elif not _is_valid_duration(duration):
                        errors.append(
                            f"Track {track_num}, note {note_num} duration '{duration}' is not a valid duration"
                        )

                    # velocity fill and validation
                    velocity = note.get("velocity")
                    if velocity is None:
                        note["velocity"] = _DEFAULT_VELOCITY
                    elif not isinstance(velocity, int) or velocity < 0 or velocity > 127:
                        errors.append(
                            f"Track {track_num}, note {note_num} velocity must be in 0-127 range"
                        )

                    # tuplet validation (optional)
                    tuplet = note.get("tuplet")
                    if tuplet is not None:
                        if not isinstance(tuplet, int):
                            errors.append(
                                f"Track {track_num}, note {note_num} tuplet must be an integer"
                            )
                        elif tuplet < 2:
                            errors.append(
                                f"Track {track_num}, note {note_num} tuplet value {tuplet} is invalid, "
                                f"tuplet actual note count must be >= 2"
                            )
                        elif tuplet not in _VALID_TUPLETS:
                            errors.append(
                                f"Track {track_num}, note {note_num} tuplet value {tuplet} is invalid, "
                                f"only {sorted(_VALID_TUPLETS)} supported (e.g. 3=triplet, 5=quintuplet)"
                            )

                    # articulation validation (optional)
                    articulation = note.get("articulation")
                    if articulation is not None:
                        if not isinstance(articulation, str):
                            errors.append(
                                f"Track {track_num}, note {note_num} articulation must be a string"
                            )
                        elif articulation not in _VALID_ARTICULATIONS:
                            errors.append(
                                f"Track {track_num}, note {note_num} articulation value '{articulation}' is invalid, "
                                f"only {sorted(_VALID_ARTICULATIONS)} supported"
                            )

                    # dynamics validation (optional)
                    dynamics = note.get("dynamics")
                    if dynamics is not None:
                        if not isinstance(dynamics, str):
                            errors.append(
                                f"Track {track_num}, note {note_num} dynamics must be a string"
                            )
                        elif dynamics not in _VALID_DYNAMICS:
                            errors.append(
                                f"Track {track_num}, note {note_num} dynamics value '{dynamics}' is invalid, "
                                f"only {sorted(_VALID_DYNAMICS)} supported"
                            )

                    # tie validation (optional)
                    tie = note.get("tie")
                    if tie is not None:
                        if not isinstance(tie, str):
                            errors.append(
                                f"Track {track_num}, note {note_num} tie must be a string"
                            )
                        elif tie not in ("start", "stop", "continue"):
                            errors.append(
                                f"Track {track_num}, note {note_num} tie value '{tie}' is invalid, "
                                f"only 'start', 'stop', or 'continue' supported"
                            )

                    # slur validation (optional)
                    slur = note.get("slur")
                    if slur is not None:
                        if not isinstance(slur, str):
                            errors.append(
                                f"Track {track_num}, note {note_num} slur must be a string"
                            )
                        elif slur not in ("start", "stop", "continue"):
                            errors.append(
                                f"Track {track_num}, note {note_num} slur value '{slur}' is invalid, "
                                f"only 'start', 'stop', or 'continue' supported"
                            )

                    # lyric validation (optional)
                    lyric = note.get("lyric")
                    if lyric is not None:
                        if not isinstance(lyric, str):
                            errors.append(
                                f"Track {track_num}, note {note_num} lyric must be a string"
                            )
                        elif len(lyric) > 100:
                            errors.append(
                                f"Track {track_num}, note {note_num} lyric length exceeds 100 characters"
                            )

                    # grace_note validation (optional)
                    grace_note = note.get("grace_note")
                    if grace_note is not None:
                        if not isinstance(grace_note, dict):
                            errors.append(
                                f"Track {track_num}, note {note_num} grace_note must be an object"
                            )
                        else:
                            gn_pitch = grace_note.get("pitch")
                            if gn_pitch is None or not isinstance(gn_pitch, int):
                                errors.append(
                                    f"Track {track_num}, note {note_num} grace_note.pitch must exist and be an integer"
                                )
                            elif gn_pitch != -1 and (gn_pitch < 21 or gn_pitch > 108):
                                errors.append(
                                    f"Track {track_num}, note {note_num} grace_note.pitch value {gn_pitch} out of range 21-108"
                                )
                            gn_duration = grace_note.get("duration")
                            if gn_duration is not None:
                                if not isinstance(gn_duration, str) or not _is_valid_duration(gn_duration):
                                    errors.append(
                                        f"Track {track_num}, note {note_num} grace_note.duration '{gn_duration}' is not a valid duration"
                                    )

                    # ornament validation (optional)
                    ornament = note.get("ornament")
                    if ornament is not None:
                        if not isinstance(ornament, str):
                            errors.append(
                                f"Track {track_num}, note {note_num} ornament must be a string"
                            )
                        elif ornament not in _VALID_ORNAMENTS:
                            errors.append(
                                f"Track {track_num}, note {note_num} ornament value '{ornament}' is invalid, "
                                f"only {sorted(_VALID_ORNAMENTS)} supported"
                            )

                    # tempo_change validation (optional)
                    tempo_change = note.get("tempo_change")
                    if tempo_change is not None:
                        if not isinstance(tempo_change, int):
                            errors.append(
                                f"Track {track_num}, note {note_num} tempo_change must be an integer (BPM)"
                            )
                        elif tempo_change < 20 or tempo_change > 300:
                            errors.append(
                                f"Track {track_num}, note {note_num} tempo_change value {tempo_change} out of range 20-300"
                            )

                    # text validation (optional)
                    text = note.get("text")
                    if text is not None:
                        if not isinstance(text, str):
                            errors.append(
                                f"Track {track_num}, note {note_num} text must be a string"
                            )
                        elif len(text) > 200:
                            errors.append(
                                f"Track {track_num}, note {note_num} text length exceeds 200 characters"
                            )

                    # fermata validation (optional)
                    fermata = note.get("fermata")
                    if fermata is not None:
                        if not isinstance(fermata, bool):
                            errors.append(
                                f"Track {track_num}, note {note_num} fermata must be a boolean (true/false)"
                            )

                    # pedal validation (optional)
                    pedal = note.get("pedal")
                    if pedal is not None:
                        if not isinstance(pedal, str):
                            errors.append(
                                f"Track {track_num}, note {note_num} pedal must be a string"
                            )
                        elif pedal not in ("start", "stop", "continue"):
                            errors.append(
                                f"Track {track_num}, note {note_num} pedal value '{pedal}' is invalid, "
                                f"only 'start', 'stop', or 'continue' supported"
                            )

                    # ---------- Expressive field validation ----------

                    # hairpin validation (optional)
                    hairpin = note.get("hairpin")
                    if hairpin is not None:
                        if not isinstance(hairpin, str):
                            errors.append(
                                f"Track {track_num}, note {note_num} hairpin must be a string"
                            )
                        elif hairpin not in ("crescendo", "diminuendo", "stop"):
                            errors.append(
                                f"Track {track_num}, note {note_num} hairpin value '{hairpin}' is invalid, "
                                f"only 'crescendo', 'diminuendo', or 'stop' supported"
                            )

                    # tempo_gradual validation (optional)
                    tempo_gradual = note.get("tempo_gradual")
                    if tempo_gradual is not None:
                        if not isinstance(tempo_gradual, dict):
                            errors.append(
                                f"Track {track_num}, note {note_num} tempo_gradual must be an object"
                            )
                        else:
                            tg_target = tempo_gradual.get("target_bpm")
                            if tg_target is None or not isinstance(tg_target, int):
                                errors.append(
                                    f"Track {track_num}, note {note_num} tempo_gradual.target_bpm must exist and be an integer"
                                )
                            elif tg_target < 20 or tg_target > 300:
                                errors.append(
                                    f"Track {track_num}, note {note_num} tempo_gradual.target_bpm value {tg_target} out of range 20-300"
                                )
                            tg_duration = tempo_gradual.get("duration_beats")
                            if tg_duration is not None:
                                if not isinstance(tg_duration, (int, float)):
                                    errors.append(
                                        f"Track {track_num}, note {note_num} tempo_gradual.duration_beats must be a number"
                                    )
                                elif tg_duration <= 0 or tg_duration > 100:
                                    errors.append(
                                        f"Track {track_num}, note {note_num} tempo_gradual.duration_beats value {tg_duration} out of range 0.1-100"
                                    )

                    # subito validation (optional)
                    subito = note.get("subito")
                    if subito is not None:
                        if not isinstance(subito, str):
                            errors.append(
                                f"Track {track_num}, note {note_num} subito must be a string"
                            )
                        elif subito not in _VALID_DYNAMICS:
                            errors.append(
                                f"Track {track_num}, note {note_num} subito value '{subito}' is invalid, "
                                f"only valid dynamics markings supported: {sorted(_VALID_DYNAMICS)}"
                            )

                    # expression validation (optional)
                    expression = note.get("expression")
                    if expression is not None:
                        if not isinstance(expression, str):
                            errors.append(
                                f"Track {track_num}, note {note_num} expression must be a string"
                            )
                        elif len(expression) > 200:
                            errors.append(
                                f"Track {track_num}, note {note_num} expression length exceeds 200 characters"
                            )

                    # ---------- JSON Schema-like field validation ----------

                    # chord validation (optional)
                    chord = note.get("chord")
                    if chord is not None:
                        if not isinstance(chord, list):
                            errors.append(
                                f"Track {track_num}, note {note_num} chord must be an array of integers"
                            )
                        elif len(chord) == 0:
                            errors.append(
                                f"Track {track_num}, note {note_num} chord cannot be empty"
                            )
                        else:
                            for i, p in enumerate(chord):
                                if not isinstance(p, int):
                                    errors.append(
                                        f"Track {track_num}, note {note_num} chord pitch {i+1} must be an integer"
                                    )
                                elif p != -1 and (p < 21 or p > 108):
                                    errors.append(
                                        f"Track {track_num}, note {note_num} chord pitch {p} out of range 21-108"
                                    )

                    # time_signature_change validation (optional)
                    time_sig_change = note.get("time_signature_change")
                    if time_sig_change is not None:
                        if not isinstance(time_sig_change, str):
                            errors.append(
                                f"Track {track_num}, note {note_num} time_signature_change must be a string"
                            )
                        else:
                            parts = time_sig_change.split("/")
                            if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
                                errors.append(
                                    f"Track {track_num}, note {note_num} time_signature_change format must be x/y (e.g. 3/4)"
                                )

                    # key_signature_change validation (optional)
                    key_sig_change = note.get("key_signature_change")
                    if key_sig_change is not None:
                        if not isinstance(key_sig_change, str):
                            errors.append(
                                f"Track {track_num}, note {note_num} key_signature_change must be a string"
                            )

                    # arpeggio validation (optional)
                    arpeggio = note.get("arpeggio")
                    if arpeggio is not None:
                        if not isinstance(arpeggio, bool):
                            errors.append(
                                f"Track {track_num}, note {note_num} arpeggio must be a boolean"
                            )

                    # tremolo validation (optional)
                    tremolo = note.get("tremolo")
                    if tremolo is not None:
                        if not isinstance(tremolo, dict):
                            errors.append(
                                f"Track {track_num}, note {note_num} tremolo must be an object"
                            )
                        else:
                            trem_dur = tremolo.get("duration")
                            if trem_dur is not None:
                                if not isinstance(trem_dur, str) or not _is_valid_duration(trem_dur):
                                    errors.append(
                                        f"Track {track_num}, note {note_num} tremolo.duration '{trem_dur}' is not a valid duration"
                                    )

                    # glissando validation (optional)
                    glissando = note.get("glissando")
                    if glissando is not None:
                        if not isinstance(glissando, bool):
                            errors.append(
                                f"Track {track_num}, note {note_num} glissando must be a boolean"
                            )

                    # navigation validation (optional)
                    navigation = note.get("navigation")
                    if navigation is not None:
                        if not isinstance(navigation, str):
                            errors.append(
                                f"Track {track_num}, note {note_num} navigation must be a string"
                            )
                        elif navigation not in ("D.C.", "D.S.", "Coda", "Fine"):
                            errors.append(
                                f"Track {track_num}, note {note_num} navigation value '{navigation}' is invalid, "
                                f"only 'D.C.', 'D.S.', 'Coda', 'Fine' supported"
                            )

            # Track-level field validation
            repeat_begin = track.get("repeat_begin")
            if repeat_begin is not None:
                if not isinstance(repeat_begin, bool):
                    errors.append(f"Track {track_num} repeat_begin must be a boolean")

            repeat_end = track.get("repeat_end")
            if repeat_end is not None:
                if not isinstance(repeat_end, bool):
                    errors.append(f"Track {track_num} repeat_end must be a boolean")

            volta = track.get("volta")
            if volta is not None:
                if not isinstance(volta, int):
                    errors.append(f"Track {track_num} volta must be an integer")
                elif volta < 1 or volta > 4:
                    errors.append(f"Track {track_num} volta value {volta} out of range 1-4")

    return (len(errors) == 0, errors)