#(.venv) PS C:\Users\babak\Documents\GitHub\Manipulation-video-sous_titre> python -m pip install json5
#cela installera le module json5 dans l'environnement virtuel actuel sinon cela installera le module json5 globalement sur votre système.

import json5
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import shutil
import time
import multiprocessing
import os


# ============================================================
# CONFIGURATION V1B + QSV HYBRIDE
# ============================================================

MAX_PARALLEL = 4

PARALLEL = True


# ============================================================
# ENCODAGE ET DECODAGE MATÉRIEL INTEL (QSV)
# ============================================================

ENCODER = "h264_qsv"

QSV_PRESET = "veryfast"

QSV_GLOBAL_QUALITY = 20

# ------------------------------------------------------------
# LISTE DES CODECS SUPPORTÉS EN LECTURE MATÉRIELLE (DÉCODAGE)
# ------------------------------------------------------------
# CONFIGURATION ACTUELLE (Intel HD Graphics 520 / Architecture Skylake) :
# Le décodage matériel est limité aux codecs nativement gérés par la puce.
# Le VP9 et l'AV1 provoqueraient des crashs ou des erreurs de lecture.
SUPPORTED_HW_DECODE = ["h264", "hevc"]

# 💡 INSTRUCTIONS POUR UN PC RÉCENT (QUI SUPPORTE TOUT) :
# Si tu utilises ce script sur une machine équipée d'un processeur Intel 
# de 11e génération (ou plus récent), d'une puce Intel Arc, ou d'une carte 
# graphique dédiée moderne (NVIDIA RTX 3000+, AMD RX 6000+), le matériel 
# possède les puces physiques pour décoder l'AV1 et le VP9.
# 
# POUR ACTIVER L'ACCÉLÉRATION TOTALE SUR CES MACHINES :
# 1. Ajoute un '#' devant la ligne SUPPORTED_HW_DECODE ci-dessus pour la désactiver.
# 2. Enlève le '#' devant la ligne ci-dessous pour l'activer.
#
# SUPPORTED_HW_DECODE = ["h264", "hevc", "vp9", "av1", "vp8"]


# ============================================================
# AUDIO
# ============================================================

AUDIO_CODEC = "aac"
AUDIO_BITRATE = "192k"


# ============================================================
# MP4
# ============================================================

FASTSTART = False

OUTPUT_EXTENSION = ".mp4"


# ============================================================
# OUTILS
# ============================================================

def print_separator():
    print("=" * 72)


def format_time(seconds):
    if seconds < 0:
        seconds = 0

    total_ms = int(round(seconds * 1000))

    hours = total_ms // 3_600_000
    total_ms %= 3_600_000

    minutes = total_ms // 60_000
    total_ms %= 60_000

    secs = total_ms // 1000
    ms = total_ms % 1000

    return (
        f"{hours:02d}:"
        f"{minutes:02d}:"
        f"{secs:02d}."
        f"{ms:03d}"
    )


def program_exists(name):
    return shutil.which(name) is not None


def run_capture(command):

    startupinfo = None
    creationflags = 0

    if os.name == "nt":

        startupinfo = subprocess.STARTUPINFO()

        startupinfo.dwFlags |= (
            subprocess.STARTF_USESHOWWINDOW
        )

        creationflags = (
            subprocess.CREATE_NO_WINDOW
        )

    return subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        startupinfo=startupinfo,
        creationflags=creationflags,
    )


# ============================================================
# EXPLORATEUR
# ============================================================

def choose_llc():

    downloads = Path.home() / "Downloads"

    if not downloads.exists():
        downloads = Path.home()

    root = tk.Tk()
    root.withdraw()
    root.attributes(
        "-topmost",
        True
    )

    path = filedialog.askopenfilename(
        title=(
            "Sélectionnez le fichier "
            "LosslessCut (.llc)"
        ),

        initialdir=str(downloads),

        filetypes=[
            (
                "LosslessCut project",
                "*.llc"
            ),
            (
                "Tous les fichiers",
                "*.*"
            ),
        ],
    )

    root.destroy()

    return Path(path) if path else None


def choose_video(initial_directory):

    root = tk.Tk()
    root.withdraw()
    root.attributes(
        "-topmost",
        True
    )

    path = filedialog.askopenfilename(
        title="Sélectionnez la vidéo source",

        initialdir=str(initial_directory),

        filetypes=[
            (
                "Vidéos",
                "*.mp4 *.mkv *.mov *.avi "
                "*.webm *.m4v *.ts *.mts *.m2ts "
                "*.flv *.wmv *.vob *.mxf *.ogg"
            ),
            (
                "Tous les fichiers",
                "*.*"
            ),
        ],
    )

    root.destroy()

    return Path(path) if path else None


# ============================================================
# LLC / JSON5
# ============================================================

def load_llc(llc_path):

    try:

        with open(
            llc_path,
            "r",
            encoding="utf-8-sig"
        ) as f:

            data = json5.load(f)

    except Exception as e:

        raise RuntimeError(
            "Impossible de lire le fichier LLC/JSON5.\n\n"
            f"{e}"
        )

    if not isinstance(data, dict):

        raise RuntimeError(
            "Le fichier LLC ne contient pas un objet valide."
        )

    cut_segments = data.get(
        "cutSegments"
    )

    if not isinstance(
        cut_segments,
        list
    ):

        raise RuntimeError(
            "Le fichier LLC ne contient pas de "
            "liste 'cutSegments'."
        )

    result = []

    for original_index, segment in enumerate(
        cut_segments,
        start=1
    ):

        if not isinstance(
            segment,
            dict
        ):

            continue

        if (
            "start" not in segment
            or "end" not in segment
        ):

            continue

        try:

            start = float(
                segment["start"]
            )

            end = float(
                segment["end"]
            )

        except (
            TypeError,
            ValueError
        ):

            continue

        if segment.get(
            "selected",
            True
        ) is False:

            continue

        if start < 0 or end <= start:

            continue

        result.append(
            {
                "number": len(result) + 1,

                "original_index":
                    original_index,

                "start":
                    start,

                "end":
                    end,

                "duration":
                    end - start,

                "name":
                    segment.get(
                        "name",
                        ""
                    ),
            }
        )

    if not result:

        raise RuntimeError(
            "Aucun segment sélectionné et valide."
        )

    return data, result


# ============================================================
# FFPROBE
# ============================================================

def probe_format(video_path):

    command = [

        "ffprobe",

        "-v",
        "error",

        "-show_entries",
        "format=duration",

        "-show_entries",
        (
            "stream="
            "index,"
            "codec_type,"
            "codec_name,"
            "width,"
            "height,"
            "avg_frame_rate"
        ),

        "-of",
        "json",

        str(video_path),
    ]

    result = run_capture(
        command
    )

    if result.returncode != 0:

        raise RuntimeError(
            "ffprobe n'a pas pu analyser la vidéo.\n\n"
            + result.stderr.strip()
        )

    try:

        data = json5.loads(
            result.stdout
        )

        duration = float(
            data["format"]["duration"]
        )

    except Exception as e:

        raise RuntimeError(
            "Réponse ffprobe invalide ou durée absente.\n\n"
            f"{e}"
        )

    return data, duration


def get_video_codec(video_path):

    command = [

        "ffprobe",

        "-v",
        "error",

        "-select_streams",
        "v:0",

        "-show_entries",
        "stream=codec_name",

        "-of",
        "default=noprint_wrappers=1:nokey=1",

        str(video_path),
    ]

    result = run_capture(
        command
    )

    if result.returncode != 0:
        return ""

    return result.stdout.strip().lower()


# ============================================================
# CONSTRUCTION COMMANDE FFMPEG QSV
# ============================================================

def build_ffmpeg_command(
    video_path,
    temp_path,
    segment,
    codec
):

    start = segment["start"]

    duration = segment["duration"]

    command = [

        "ffmpeg",

        "-hide_banner",

        "-loglevel",
        "error",

        # ----------------------------------------------------
        # RECHERCHE EXACTE
        # ----------------------------------------------------

        "-ss",
        f"{start:.9f}",

        "-accurate_seek",
    ]

    # ----------------------------------------------------
    # CONDITION : LECTURE MATÉRIELLE SI COMPATIBLE
    # ----------------------------------------------------
    
    if codec in SUPPORTED_HW_DECODE:
        
        command.extend([
            "-hwaccel",
            "qsv",
        ])

    command.extend([

        # ----------------------------------------------------
        # SOURCE
        # ----------------------------------------------------

        "-i",
        str(video_path),

        # ----------------------------------------------------
        # DURÉE
        # ----------------------------------------------------

        "-t",
        f"{duration:.9f}",

        # ----------------------------------------------------
        # VIDÉO ET AUDIO
        # ----------------------------------------------------

        "-map",
        "0:v:0",

        "-map",
        "0:a?",

        "-sn",
        "-dn",

        # ----------------------------------------------------
        # ENCODAGE QSV
        # ----------------------------------------------------

        "-c:v",
        ENCODER,

        "-preset",
        QSV_PRESET,

        "-global_quality",
        str(QSV_GLOBAL_QUALITY),

        "-fps_mode",
        "passthrough",

        # ----------------------------------------------------
        # AUDIO
        # ----------------------------------------------------

        "-c:a",
        AUDIO_CODEC,

        "-b:a",
        AUDIO_BITRATE,

        "-map_metadata",
        "0",

    ])

    if FASTSTART:

        command.extend([

            "-movflags",
            "+faststart",

        ])

    command.extend([

        # ----------------------------------------------------
        # SORTIE
        # ----------------------------------------------------

        "-y",

        str(temp_path),

    ])

    return command


# ============================================================
# VALIDATION
# ============================================================

def verify_output(
    output_path,
    expected_duration
):

    if not output_path.exists():

        return (
            False,
            "fichier inexistant"
        )

    if output_path.stat().st_size < 2048:

        return (
            False,
            "fichier anormalement petit"
        )

    command = [

        "ffprobe",

        "-v",
        "error",

        "-show_entries",
        "format=duration",

        "-show_entries",
        "stream=codec_type,codec_name",

        "-of",
        "json",

        str(output_path),
    ]

    result = run_capture(
        command
    )

    if result.returncode != 0:

        return (
            False,
            "fichier illisible par ffprobe"
        )

    try:

        data = json5.loads(
            result.stdout
        )

        actual_duration = float(
            data["format"]["duration"]
        )

    except Exception:

        return (
            False,
            "durée de sortie illisible"
        )

    difference = abs(
        actual_duration
        - expected_duration
    )

    if difference > 0.20:

        return (
            False,
            (
                f"durée inattendue : "
                f"{actual_duration:.6f}s "
                f"(attendu "
                f"{expected_duration:.6f}s, "
                f"écart "
                f"{difference:.6f}s)"
            ),
        )

    streams = data.get(
        "streams",
        []
    )

    has_video = any(
        stream.get(
            "codec_type"
        ) == "video"
        for stream in streams
    )

    if not has_video:

        return (
            False,
            "aucun flux vidéo"
        )

    return (
        True,
        actual_duration
    )


# ============================================================
# EXTRACTION D'UN SEGMENT
# ============================================================

def extract_segment(
    video_path,
    output_path,
    segment,
    codec
):

    number = segment["number"]

    temp_path = output_path.with_name(
        output_path.stem
        + ".part.mp4"
    )

    try:

        if temp_path.exists():

            temp_path.unlink()

        command = build_ffmpeg_command(
            video_path,
            temp_path,
            segment,
            codec
        )

        started = time.perf_counter()

        result = run_capture(
            command
        )

        elapsed = (
            time.perf_counter()
            - started
        )

        if result.returncode != 0:

            error = result.stderr.strip()

            if not error:

                error = (
                    "FFmpeg a retourné "
                    "une erreur inconnue."
                )

            return {

                "success": False,

                "number": number,

                "segment": segment,

                "output": output_path,

                "elapsed": elapsed,

                "error": error,

            }

        if not temp_path.exists():

            return {

                "success": False,

                "number": number,

                "segment": segment,

                "output": output_path,

                "elapsed": elapsed,

                "error": (
                    "FFmpeg terminé mais "
                    "aucun fichier n'a été créé."
                ),

            }

        valid, info = verify_output(
            temp_path,
            segment["duration"]
        )

        if not valid:

            try:
                temp_path.unlink()
            except OSError:
                pass

            return {

                "success": False,

                "number": number,

                "segment": segment,

                "output": output_path,

                "elapsed": elapsed,

                "error": (
                    f"Vérification échouée : "
                    f"{info}"
                ),

            }

        if output_path.exists():

            output_path.unlink()

        temp_path.replace(
            output_path
        )

        return {

            "success": True,

            "number": number,

            "segment": segment,

            "output": output_path,

            "elapsed": elapsed,

            "actual_duration": info,

        }

    except Exception as exc:

        try:

            if temp_path.exists():
                temp_path.unlink()

        except OSError:
            pass

        return {

            "success": False,

            "number": number,

            "segment": segment,

            "output": output_path,

            "elapsed": 0.0,

            "error": (
                f"Exception Python : {exc}"
            ),

        }


# ============================================================
# RAPPORT
# ============================================================

def write_report(
    report_path,
    llc_path,
    video_path,
    source_duration,
    elapsed,
    successful,
    failed,
    codec
):

    with open(
        report_path,
        "w",
        encoding="utf-8"
    ) as file:

        file.write(
            "LLC SEGMENTER V1B + QSV HYBRIDE\n"
        )

        file.write(
            "MOTEUR INTEL MATERIEL RAPIDE\n"
        )

        file.write(
            "=" * 72
            + "\n\n"
        )

        file.write(
            f"LLC : {llc_path}\n"
        )

        file.write(
            f"VIDEO : {video_path}\n"
        )
        
        file.write(
            f"CODEC SOURCE : {codec}\n"
        )
        
        mode_lecture = "MATERIEL (QSV)" if codec in SUPPORTED_HW_DECODE else "LOGICIEL (CPU)"
        file.write(
            f"MODE DE LECTURE : {mode_lecture}\n"
        )

        file.write(
            f"DUREE SOURCE : "
            f"{source_duration:.9f}s\n"
        )

        file.write(
            f"ENCODEUR : "
            f"{ENCODER}\n"
        )

        file.write(
            f"PRESET : "
            f"{QSV_PRESET}\n"
        )

        file.write(
            f"GLOBAL QUALITY : "
            f"{QSV_GLOBAL_QUALITY}\n"
        )

        file.write(
            f"PARALLELE : "
            f"{PARALLEL}\n"
        )

        file.write(
            f"MAX_PARALLEL : "
            f"{MAX_PARALLEL}\n"
        )

        file.write(
            f"TEMPS TOTAL : "
            f"{elapsed:.3f}s\n\n"
        )

        file.write(
            "SEGMENTS REUSSIS\n"
        )

        file.write(
            "-" * 72
            + "\n"
        )

        for result in sorted(
            successful,
            key=lambda x: x["number"]
        ):

            segment = result[
                "segment"
            ]

            file.write(
                f"\nSegment "
                f"{segment['number']:03d}\n"
            )

            file.write(
                f"  START LLC : "
                f"{segment['start']:.9f}\n"
            )

            file.write(
                f"  END LLC   : "
                f"{segment['end']:.9f}\n"
            )

            file.write(
                f"  DURATION LLC : "
                f"{segment['duration']:.9f}s\n"
            )

            file.write(
                f"  OUTPUT : "
                f"{result['output']}\n"
            )

            file.write(
                f"  DUREE OUTPUT : "
                f"{result['actual_duration']:.9f}s\n"
            )

            file.write(
                f"  TEMPS FFMPEG : "
                f"{result['elapsed']:.3f}s\n"
            )

        file.write(
            "\n\nSEGMENTS EN ECHEC\n"
        )

        file.write(
            "-" * 72
            + "\n"
        )

        for result in sorted(
            failed,
            key=lambda x: x["number"]
        ):

            segment = result[
                "segment"
            ]

            file.write(
                f"\nSegment "
                f"{segment['number']:03d}\n"
            )

            file.write(
                f"  START : "
                f"{segment['start']:.9f}\n"
            )

            file.write(
                f"  END : "
                f"{segment['end']:.9f}\n"
            )

            file.write(
                f"  ERREUR : "
                f"{result['error']}\n"
            )


# ============================================================
# MAIN
# ============================================================

def main():

    print_separator()

    print(
        "       LLC SEGMENTER V1B + QSV HYBRIDE"
    )

    print(
        "       MOTEUR INTEL MATERIEL RAPIDE"
    )

    print_separator()

    print()

    if not program_exists(
        "ffmpeg"
    ):

        messagebox.showerror(
            "FFmpeg introuvable",
            (
                "FFmpeg n'est pas accessible "
                "dans le PATH."
            )
        )

        return

    if not program_exists(
        "ffprobe"
    ):

        messagebox.showerror(
            "FFprobe introuvable",
            (
                "FFprobe n'est pas accessible "
                "dans le PATH."
            )
        )

        return

    print(
        "✓ FFmpeg trouvé"
    )

    print(
        "✓ FFprobe trouvé"
    )

    print()

    print(
        "Sélection du fichier LLC..."
    )

    llc_path = choose_llc()

    if not llc_path:

        print(
            "Opération annulée."
        )

        return

    print(
        f"✓ LLC : {llc_path}"
    )

    print()

    try:

        llc_data, segments = load_llc(
            llc_path
        )

    except Exception as exc:

        messagebox.showerror(
            "Erreur LLC",
            str(exc)
        )

        return

    media_name = (
        llc_data.get(
            "mediaFileName",
            ""
        )
    )

    print(
        f"Vidéo indiquée dans LLC : "
        f"{media_name}"
    )

    print(
        f"Segments sélectionnés : "
        f"{len(segments)}"
    )

    print()

    print(
        "Sélection de la vidéo source..."
    )

    video_path = choose_video(
        llc_path.parent
    )

    if not video_path:

        print(
            "Opération annulée."
        )

        return

    print(
        f"✓ Vidéo : "
        f"{video_path}"
    )

    if media_name:

        expected_name = Path(
            media_name
        ).name

        actual_name = (
            video_path.name
        )

        if (
            expected_name.lower()
            != actual_name.lower()
        ):

            root = tk.Tk()

            root.withdraw()

            root.attributes(
                "-topmost",
                True
            )

            answer = (
                messagebox.askyesno(
                    "Vidéo différente",
                    (
                        "Le fichier vidéo sélectionné "
                        "ne correspond pas au nom du LLC.\n\n"
                        f"LLC : {expected_name}\n"
                        f"Vidéo : {actual_name}\n\n"
                        "Continuer quand même ?"
                    )
                )
            )

            root.destroy()

            if not answer:

                print(
                    "Opération annulée."
                )

                return

    print()

    print(
        "Analyse de la vidéo source..."
    )

    try:

        _, source_duration = (
            probe_format(
                video_path
            )
        )

    except Exception as exc:

        messagebox.showerror(
            "Erreur vidéo",
            str(exc)
        )

        return

    codec = get_video_codec(
        video_path
    )

    print(
        f"✓ Codec : "
        f"{codec or 'inconnu'}"
    )

    print(
        f"✓ Durée : "
        f"{format_time(source_duration)}"
    )

    print()

    print(
        "Segments LLC :"
    )

    print()

    valid_segments = []

    for segment in segments:

        start = segment[
            "start"
        ]

        end = segment[
            "end"
        ]

        if start >= source_duration:

            print(
                f"✗ Segment "
                f"{segment['number']:02d} : "
                "START hors vidéo."
            )

            continue

        if end > source_duration:

            print(
                f"⚠ Segment "
                f"{segment['number']:02d} : "
                "END dépasse la vidéo ; "
                "limitation."
            )

            segment["end"] = (
                source_duration
            )

            segment["duration"] = (
                source_duration
                - segment["start"]
            )

        valid_segments.append(
            segment
        )

        print(
            f"{segment['number']:02d}  "
            f"{format_time(start)} → "
            f"{format_time(end)}  "
            f"({segment['duration']:.6f}s)"
        )

    if not valid_segments:

        messagebox.showerror(
            "Aucun segment",
            "Aucun segment valide."
        )

        return

    output_dir = (
        video_path.parent
        / f"{video_path.stem}_segments"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    print()

    print(
        f"Dossier de sortie : "
        f"{output_dir}"
    )

    jobs = []

    for segment in valid_segments:

        output_path = (
            output_dir
            / (
                f"{video_path.stem}"
                "_segment_"
                f"{segment['number']:03d}"
                f"{OUTPUT_EXTENSION}"
            )
        )

        jobs.append(
            (
                video_path,
                output_path,
                segment,
                codec,
            )
        )

    workers = min(
        MAX_PARALLEL
        if PARALLEL
        else 1,
        len(jobs),
    )

    print()

    print_separator()

    if PARALLEL:

        print(
            f"Traitement parallèle : "
            f"{workers} FFmpeg simultanés"
        )

    else:

        print(
            "Traitement séquentiel"
        )

    print(
        f"Moteur sortie : "
        f"{ENCODER}"
    )

    if codec in SUPPORTED_HW_DECODE:
        print(
            f"Moteur lecture : MATERIEL (QSV activé)"
        )
    else:
        print(
            f"Moteur lecture : LOGICIEL (Codec {codec} non supporté en natif)"
        )

    print(
        f"Preset : "
        f"{QSV_PRESET}"
    )

    print(
        f"Qualité Globale : "
        f"{QSV_GLOBAL_QUALITY}"
    )

    print_separator()

    print()

    overall_start = time.perf_counter()

    successful = []

    failed = []

    if PARALLEL and workers > 1:

        with ThreadPoolExecutor(
            max_workers=workers
        ) as executor:

            futures = {

                executor.submit(
                    extract_segment,
                    video,
                    output,
                    segment,
                    codec,
                ): segment

                for (
                    video,
                    output,
                    segment,
                    codec,
                ) in jobs
            }

            for future in as_completed(
                futures
            ):

                result = future.result()

                segment = result[
                    "segment"
                ]

                if result["success"]:

                    successful.append(
                        result
                    )

                    print()

                    print(
                        f"✓ Segment "
                        f"{segment['number']:02d} → "
                        f"{result['output'].name}"
                    )

                    print(
                        f"  durée : "
                        f"{result['actual_duration']:.6f}s "
                        f"/ demandé "
                        f"{segment['duration']:.6f}s"
                    )

                    print(
                        f"  temps FFmpeg : "
                        f"{result['elapsed']:.2f}s"
                    )

                else:

                    failed.append(
                        result
                    )

                    print()

                    print(
                        f"✗ Segment "
                        f"{segment['number']:02d} ÉCHEC"
                    )

                    print(
                        f"  {result['error']}"
                    )

                print()

    else:

        for (
            video,
            output,
            segment,
            codec,
        ) in jobs:

            result = extract_segment(
                video,
                output,
                segment,
                codec,
            )

            if result["success"]:

                successful.append(
                    result
                )

                print(
                    f"✓ Segment "
                    f"{segment['number']:02d} → "
                    f"{result['output'].name}"
                )

                print(
                    f"  durée : "
                    f"{result['actual_duration']:.6f}s"
                )

                print(
                    f"  temps : "
                    f"{result['elapsed']:.2f}s"
                )

            else:

                failed.append(
                    result
                )

                print(
                    f"✗ Segment "
                    f"{segment['number']:02d} ÉCHEC"
                )

                print(
                    f"  {result['error']}"
                )

            print()

    elapsed = (
        time.perf_counter()
        - overall_start
    )

    report_path = (
        output_dir
        / "rapport.txt"
    )

    write_report(
        report_path,
        llc_path,
        video_path,
        source_duration,
        elapsed,
        successful,
        failed,
        codec,
    )

    print_separator()

    print(
        "TERMINÉ"
    )

    print_separator()

    print(
        f"Demandés : "
        f"{len(valid_segments)}"
    )

    print(
        f"Réussis : "
        f"{len(successful)}"
    )

    print(
        f"Échecs : "
        f"{len(failed)}"
    )

    print(
        f"Temps total : "
        f"{elapsed:.2f}s"
    )

    print()

    print(
        f"Résultats : "
        f"{output_dir}"
    )

    print(
        f"Rapport : "
        f"{report_path}"
    )

    print()

    try:

        os.startfile(
            str(output_dir)
        )

    except Exception:

        pass

    root = tk.Tk()

    root.withdraw()

    root.attributes(
        "-topmost",
        True
    )

    if failed:

        messagebox.showwarning(
            "Extraction terminée avec erreurs",
            (
                f"{len(successful)} segment(s) réussi(s).\n"
                f"{len(failed)} segment(s) en échec.\n\n"
                f"Résultats :\n{output_dir}\n\n"
                f"Rapport :\n{report_path}"
            ),
        )

    else:

        messagebox.showinfo(
            "Extraction terminée",
            (
                f"{len(successful)} segment(s) créé(s).\n\n"
                "Moteur : h264_qsv (Matériel)\n"
                "Découpage : accurate_seek\n\n"
                f"Résultats :\n{output_dir}"
            ),
        )

    root.destroy()


if __name__ == "__main__":

    multiprocessing.freeze_support()

    try:

        main()

    except KeyboardInterrupt:

        print()

        print(
            "Opération interrompue par l'utilisateur."
        )

    except Exception as exc:

        print()

        print_separator()

        print(
            "ERREUR FATALE"
        )

        print_separator()

        print(
            exc
        )

        try:

            messagebox.showerror(
                "Erreur",
                str(exc)
            )

        except Exception:

            pass