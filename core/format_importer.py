"""
Format importer — imports MusicXML and MIDI files into the Do Muse JSON score format.

Provides:
  - import_from_musicxml(file_path)  — reads .xml/.mxl → JSON dict
  - import_from_midi(file_path)      — reads .mid/.midi → JSON dict
  - import_file(file_path)           — auto-detects format and imports
"""

import os
import logging
from typing import Optional

from music21 import converter, stream, note, chord, meter, key, instrument, \
    tempo, clef, dynamics, expressions, articulations

logger = logging.getLogger(__name__)

# Duration type → string mapping (reverse of _DURATION_TO_FLOAT)
_DURATION_TYPE_TO_STR: dict[str, str] = {
    "whole": "whole",
    "half": "half",
    "quarter": "quarter",
    "eighth": "eighth",
    "16th": "16th",
    "32nd": "32nd",
    "64th": "64th",
}

# music21 dynamics object → string mapping
_DYNAMICS_REVERSE_MAP: dict[str, str] = {
    "pppp": "pppp", "ppp": "ppp", "pp": "pp", "p": "p",
    "mp": "mp", "mf": "mf", "f": "f", "ff": "ff", "fff": "fff", "ffff": "ffff",
    "sfz": "sfz", "sf": "sf", "fz": "fz", "rfz": "rfz", "sffz": "sffz",
    "fp": "fp", "sfp": "sfp",
    "crescendo": "crescendo", "diminuendo": "diminuendo",
    "calando": "calando", "morendo": "morendo",
    "smorzando": "smorzando", "rinforzando": "rinforzando",
}

# articulation type → string mapping
_ARTICULATION_REVERSE_MAP: dict[str, str] = {
    "staccato": "staccato",
    "staccatissimo": "staccatissimo",
    "accent": "accent",
    "tenuto": "tenuto",
    "marcato": "marcato",
    "sforzando": "sforzando",
}


def _duration_to_str(dur) -> str:
    """
    Convert a music21 duration object to a Do Muse duration string (e.g. "quarter", "half.").

    Args:
        dur: music21 duration object.

    Returns:
        str: Duration string, e.g. "quarter", "half.", "16th".
    """
    dur_type = dur.type
    base = _DURATION_TYPE_TO_STR.get(dur_type, "quarter")
    dots = dur.dotes if hasattr(dur, 'dotes') else 0
    if dots > 0:
        return base + "." * dots
    return base


def _extract_dynamics_from_note(n_obj) -> Optional[str]:
    """
    Extract dynamics marking from a music21 note's expressions.

    Args:
        n_obj: music21 Note or Chord object.

    Returns:
        Optional[str]: Dynamics string, or None if no dynamics found.
    """
    for expr in n_obj.expressions:
        expr_str = str(expr)
        if expr_str in _DYNAMICS_REVERSE_MAP:
            return _DYNAMICS_REVERSE_MAP[expr_str]
        # Check for Dynamic objects
        if hasattr(expr, 'value') and expr.value in _DYNAMICS_REVERSE_MAP:
            return _DYNAMICS_REVERSE_MAP[expr.value]
    return None


def _extract_articulation_from_note(n_obj) -> Optional[str]:
    """
    Extract articulation marking from a music21 note's articulations.

    Args:
        n_obj: music21 Note or Chord object.

    Returns:
        Optional[str]: Articulation string, or None if not found.
    """
    for art in n_obj.articulations:
        art_str = str(art).lower()
        for key, val in _ARTICULATION_REVERSE_MAP.items():
            if key in art_str:
                return val
    return None


def _extract_ornament_from_note(n_obj) -> Optional[str]:
    """
    Extract ornament marking from a music21 note's expressions.

    Args:
        n_obj: music21 Note or Chord object.

    Returns:
        Optional[str]: Ornament string, or None if not found.
    """
    from music21 import expressions as expr
    for e in n_obj.expressions:
        if isinstance(e, expr.Trill):
            return "trill"
        if isinstance(e, expr.Mordent):
            return "mordent"
        if isinstance(e, expr.InvertedMordent):
            return "inverted_mordent"
        if isinstance(e, expr.Turn):
            return "turn"
        if isinstance(e, expr.InvertedTurn):
            return "inverted_turn"
    return None


def _extract_tie(n_obj) -> Optional[str]:
    """
    Extract tie status from a music21 note.

    Args:
        n_obj: music21 Note object.

    Returns:
        Optional[str]: "start", "stop", "continue", or None.
    """
    if not hasattr(n_obj, 'tie') or n_obj.tie is None:
        return None
    tie_type = n_obj.tie.type
    if tie_type == "start":
        return "start"
    elif tie_type == "stop":
        return "stop"
    elif tie_type == "continue":
        return "continue"
    return None


def _extract_lyric(n_obj) -> Optional[str]:
    """
    Extract lyric text from a music21 note.

    Args:
        n_obj: music21 Note object.

    Returns:
        Optional[str]: Lyric text, or None.
    """
    if hasattr(n_obj, 'lyrics') and n_obj.lyrics:
        return str(n_obj.lyrics[0].text)
    return None


def _extract_fermata(n_obj) -> Optional[bool]:
    """
    Check if a music21 note has a fermata marking.

    Args:
        n_obj: music21 Note object.

    Returns:
        Optional[bool]: True if fermata exists, else None.
    """
    from music21 import expressions as expr
    for e in n_obj.expressions:
        if isinstance(e, expr.Fermata):
            return True
    return None


def _extract_arpeggio(n_obj) -> Optional[bool]:
    """
    Check if a music21 note has an arpeggio marking.

    Args:
        n_obj: music21 Note object.

    Returns:
        Optional[bool]: True if arpeggio exists, else None.
    """
    from music21 import expressions as expr
    for e in n_obj.expressions:
        if isinstance(e, expr.ArpeggioMark):
            return True
    return None


def _build_note_from_music21(n_obj) -> dict:
    """
    Convert a music21 note/rest to a Do Muse JSON note dict.

    Args:
        n_obj: music21 Note, Rest, or Chord object.

    Returns:
        dict: Note dict in Do Muse JSON format.
    """
    note_dict: dict = {}

    # Duration
    dur_str = _duration_to_str(n_obj.duration)
    note_dict["duration"] = dur_str

    # Velocity
    if hasattr(n_obj, 'volume') and n_obj.volume.velocity is not None:
        note_dict["velocity"] = int(n_obj.volume.velocity)

    # Check if it is a rest
    if isinstance(n_obj, note.Rest):
        note_dict["pitch"] = -1
        note_dict["velocity"] = 0
        return note_dict

    # Check if it is a chord
    if isinstance(n_obj, chord.Chord):
        pitches = [p.midi for p in n_obj.pitches]
        note_dict["chord"] = pitches
        # Use the first pitch for reference
        note_dict["pitch"] = pitches[0] if pitches else 60
    else:
        # Single note
        note_dict["pitch"] = n_obj.pitch.midi

    # Articulation
    art = _extract_articulation_from_note(n_obj)
    if art:
        note_dict["articulation"] = art

    # Dynamics
    dyn = _extract_dynamics_from_note(n_obj)
    if dyn:
        note_dict["dynamics"] = dyn

    # Tie
    tie = _extract_tie(n_obj)
    if tie:
        note_dict["tie"] = tie

    # Lyric
    lyric = _extract_lyric(n_obj)
    if lyric:
        note_dict["lyric"] = lyric

    # Ornament
    ornament = _extract_ornament_from_note(n_obj)
    if ornament:
        note_dict["ornament"] = ornament

    # Fermata
    fermata = _extract_fermata(n_obj)
    if fermata:
        note_dict["fermata"] = True

    # Arpeggio
    arpeggio = _extract_arpeggio(n_obj)
    if arpeggio:
        note_dict["arpeggio"] = True

    return note_dict


def _get_instrument_name_from_part(part_stream) -> str:
    """
    Extract the instrument name from a music21 Part.

    Args:
        part_stream: music21 Part object.

    Returns:
        str: Instrument name, or "Acoustic Grand Piano" as fallback.
    """
    # Try to get instrument from the part
    for el in part_stream.recurse().getElementsByClass(instrument.Instrument):
        if el.instrumentName:
            return el.instrumentName
    # Try to get from part name
    if hasattr(part_stream, 'partName') and part_stream.partName:
        return part_stream.partName
    return "Acoustic Grand Piano"


def _get_part_metadata(part_stream) -> tuple:
    """
    Extract time signature, key signature, and tempo from a part.

    Args:
        part_stream: music21 Part object.

    Returns:
        tuple: (time_sig_str, key_sig_str, tempo_bpm).
    """
    time_sig = "4/4"
    key_sig = None
    tempo_bpm = 120

    for el in part_stream.flat.getElementsByClass(meter.TimeSignature):
        time_sig = el.ratioString
        break

    for el in part_stream.flat.getElementsByClass(key.Key):
        key_sig = el.sharps  # numeric representation
        # Convert to string name
        try:
            key_sig = str(el)
        except Exception:
            key_sig = None
        break

    for el in part_stream.flat.getElementsByClass(tempo.MetronomeMark):
        if el.number:
            tempo_bpm = int(el.number)
            break

    return time_sig, key_sig, tempo_bpm


def _get_notes_in_order(part_stream) -> list:
    """
    Get all notes/rests from a part in sequential order (by offset).

    Args:
        part_stream: music21 Part object.

    Returns:
        list: Sorted list of (offset, music21-object) tuples.
    """
    note_objs = []
    for el in part_stream.flat.notesAndRests:
        note_objs.append((el.offset, el))
    # Sort by offset
    note_objs.sort(key=lambda x: (x[0], x[1].duration.quarterLength))
    return note_objs


def import_from_musicxml(file_path: str) -> dict:
    """
    Import a MusicXML file (.xml or .mxl) and convert to Do Muse JSON format.

    Args:
        file_path: Path to the MusicXML file.

    Returns:
        dict: Score JSON dict in Do Muse format.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file cannot be parsed as MusicXML.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"MusicXML file not found: {file_path}")

    try:
        score = converter.parse(file_path)
    except Exception as e:
        raise ValueError(f"Failed to parse MusicXML file: {e}") from e

    return _convert_score_to_json(score)


def import_from_midi(file_path: str) -> dict:
    """
    Import a MIDI file (.mid or .midi) and convert to Do Muse JSON format.

    Args:
        file_path: Path to the MIDI file.

    Returns:
        dict: Score JSON dict in Do Muse format.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file cannot be parsed as MIDI.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"MIDI file not found: {file_path}")

    try:
        score = converter.parse(file_path)
    except Exception as e:
        raise ValueError(f"Failed to parse MIDI file: {e}") from e

    return _convert_score_to_json(score)


def _convert_score_to_json(score: stream.Score) -> dict:
    """
    Convert a music21 Score object to a Do Muse JSON dict.

    Args:
        score: music21 Score object.

    Returns:
        dict: Score JSON dict in Do Muse format.
    """
    json_data: dict = {
        "title": "Untitled",
        "composer": "Unknown",
        "metadata": {
            "tempo_bpm": 120,
            "time_signature": "4/4",
        },
        "tracks": [],
    }

    # Extract title and composer from metadata
    if score.metadata:
        if score.metadata.title:
            json_data["title"] = score.metadata.title
        if score.metadata.composer:
            json_data["composer"] = score.metadata.composer

    # Process each part
    for part_stream in score.parts:
        instrument_name = _get_instrument_name_from_part(part_stream)
        time_sig, key_sig, tempo_bpm = _get_part_metadata(part_stream)

        # Use first part's metadata for the score-level metadata
        if json_data["metadata"]["tempo_bpm"] == 120 and tempo_bpm != 120:
            json_data["metadata"]["tempo_bpm"] = tempo_bpm
        if json_data["metadata"]["time_signature"] == "4/4":
            json_data["metadata"]["time_signature"] = time_sig
        if key_sig and "key_signature" not in json_data["metadata"]:
            json_data["metadata"]["key_signature"] = key_sig

        # Build notes array
        notes = []
        note_objs = _get_notes_in_order(part_stream)

        for offset, n_obj in note_objs:
            note_dict = _build_note_from_music21(n_obj)
            notes.append(note_dict)

        track = {
            "instrument": instrument_name,
            "notes": notes,
        }
        json_data["tracks"].append(track)

    return json_data


def import_file(file_path: str) -> dict:
    """
    Auto-detect file format and import to Do Muse JSON format.

    Supported formats:
      - .xml, .mxl  → MusicXML
      - .mid, .midi  → MIDI

    Args:
        file_path: Path to the input file.

    Returns:
        dict: Score JSON dict in Do Muse format.

    Raises:
        ValueError: If the file format is not supported.
        FileNotFoundError: If the file does not exist.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()

    if ext in (".xml", ".mxl"):
        return import_from_musicxml(file_path)
    elif ext in (".mid", ".midi"):
        return import_from_midi(file_path)
    else:
        raise ValueError(
            f"Unsupported file format: '{ext}'. "
            f"Supported formats: .xml, .mxl, .mid, .midi"
        )