# -*- coding: utf-8 -*-
"""
Fusion LosslessCut (.llc) -> MP4 H.264 QSV

GUI professionnelle avec :
    - bouton LANCER LA FUSION
    - bouton PAUSE / REPRENDRE
    - bouton STOPPER
    - barre de progression et pourcentage
    - vitesse d'encodage et ETA
    - recherche automatique de la source via mediaFileName
    - une seule session FFmpeg pour tous les segments
    - H.264 Intel Quick Sync Video (h264_qsv)
    - validation FFprobe minimale et optionnelle
    - aucun contrôle PTS/frame-par-frame post-traitement

Dépendance Python :
    python -m pip install json5

FFmpeg / FFprobe :
    - dans le PATH, ou
    - C:\ffmpeg\bin\ffmpeg.exe et ffprobe.exe

IMPORTANT :
    La pause réelle suspend le processus FFmpeg sous Windows avec
    NtSuspendProcess / NtResumeProcess.
"""

from __future__ import annotations

import ctypes
from ctypes import wintypes
import json
import json5
import os
import queue
import shutil
import subprocess
import threading
import time
import tkinter as tk

from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any, Dict, List, Optional, Sequence, Tuple


# ============================================================
# CONFIGURATION — PRIORITÉ À LA VITESSE
# ============================================================

ENCODER = "h264_qsv"
QSV_PRESET = "veryfast"
QSV_GLOBAL_QUALITY = 22
QSV_B_FRAMES = 0

AUDIO_CODEC = "aac"
AUDIO_BITRATE = "192k"

OUTPUT_EXTENSION = ".mp4"

# False = pas d'étape supplémentaire de remux après encodage.
FASTSTART = False

# Validation FFprobe minimale.
FAST_VALIDATION = True

# Test QSV séparé avant chaque fusion.
# False = plus rapide au démarrage.
TEST_QSV_BEFORE_MERGE = False

# Décodage QSV optionnel. CPU par défaut car le pipeline contient
# un filter_complex + concat avec de nombreux inputs.
USE_HW_DECODE_DEFAULT = False
HW_DECODE_FALLBACK_TO_CPU = True
QSV_CHILD_DEVICE_TYPE = "dxva2"

# CFR : la source de ton exemple est déjà CFR 23.976.
FORCE_CFR = True
AVOID_REDUNDANT_FPS_FILTER = True

# Progression FFmpeg.
PROGRESS_INTERVAL = 0.25
GUI_POLL_INTERVAL_MS = 80


# ============================================================
# EXCEPTION
# ============================================================

class FusionCancelled(Exception):
    pass


# ============================================================
# OUTILS GÉNÉRAUX
# ============================================================

def format_time(seconds: float) -> str:
    seconds = max(0.0, float(seconds))
    total_ms = int(round(seconds * 1000.0))
    hours = total_ms // 3_600_000
    total_ms %= 3_600_000
    minutes = total_ms // 60_000
    total_ms %= 60_000
    secs = total_ms // 1000
    ms = total_ms % 1000
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{ms:03d}"


def parse_fraction(value: Any) -> Optional[float]:
    if value is None:
        return None
    raw = str(value).strip()
    if not raw or raw in {"0/0", "N/A", "nan"}:
        return None
    try:
        if "/" in raw:
            num, den = raw.split("/", 1)
            den_f = float(den)
            if den_f == 0:
                return None
            return float(num) / den_f
        return float(raw)
    except (ValueError, TypeError, ZeroDivisionError):
        return None


def normalize_fps_expression(video_stream: Dict[str, Any]) -> str:
    from fractions import Fraction

    raw = str(video_stream.get("r_frame_rate") or "").strip()
    if not raw or raw == "0/0":
        return "30/1"
    try:
        fps = float(Fraction(raw))
    except (ValueError, ZeroDivisionError):
        return "30/1"

    common = {
        23.976: "24000/1001",
        24.0: "24/1",
        25.0: "25/1",
        29.97: "30000/1001",
        30.0: "30/1",
        50.0: "50/1",
        59.94: "60000/1001",
        60.0: "60/1",
    }
    for value, expression in common.items():
        if abs(fps - value) < 0.01:
            return expression
    return raw


def is_source_cfr(video_stream: Dict[str, Any]) -> bool:
    r_fps = parse_fraction(video_stream.get("r_frame_rate"))
    avg_fps = parse_fraction(video_stream.get("avg_frame_rate"))
    if r_fps is None or avg_fps is None:
        return True
    return abs(r_fps - avg_fps) < 0.001


def windows_startupinfo() -> Tuple[Optional[subprocess.STARTUPINFO], int]:
    startupinfo = None
    creationflags = 0
    if os.name == "nt":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        creationflags = subprocess.CREATE_NO_WINDOW
    return startupinfo, creationflags


def program_path(name: str) -> Optional[str]:
    found = shutil.which(name)
    if found:
        return found
    candidates = [
        Path(r"C:\ffmpeg\bin") / f"{name}.exe",
        Path.home() / "ffmpeg" / "bin" / f"{name}.exe",
    ]
    for candidate in candidates:
        try:
            if candidate.is_file():
                return str(candidate)
        except OSError:
            pass
    return None


FFMPEG = program_path("ffmpeg")
FFPROBE = program_path("ffprobe")


def ensure_programs() -> None:
    global FFMPEG, FFPROBE
    FFMPEG = FFMPEG or program_path("ffmpeg")
    FFPROBE = FFPROBE or program_path("ffprobe")

    missing: List[str] = []
    if not FFMPEG:
        missing.append("FFmpeg")
    if not FFPROBE:
        missing.append("FFprobe")
    if missing:
        raise RuntimeError(
            "Programme(s) introuvable(s) : "
            + ", ".join(missing)
            + "\n\nAjoute C:\\ffmpeg\\bin au PATH ou installe FFmpeg."
        )


def run_capture(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    startupinfo, creationflags = windows_startupinfo()
    return subprocess.run(
        [str(x) for x in command],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        startupinfo=startupinfo,
        creationflags=creationflags,
    )


# ============================================================
# LLC
# ============================================================

def load_llc(llc_path: Path) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    try:
        with llc_path.open("r", encoding="utf-8-sig") as handle:
            data = json5.load(handle)
    except Exception as exc:
        raise RuntimeError(
            "Impossible de lire le fichier LLC/JSON5.\n\n" + str(exc)
        ) from exc

    cut_segments = data.get("cutSegments")
    if not isinstance(cut_segments, list):
        raise RuntimeError("Le fichier LLC ne contient pas de liste 'cutSegments'.")

    result: List[Dict[str, Any]] = []

    for original_index, segment in enumerate(cut_segments, start=1):
        if not isinstance(segment, dict):
            continue
        if "start" not in segment or "end" not in segment:
            continue
        try:
            start = float(segment["start"])
            end = float(segment["end"])
        except (TypeError, ValueError):
            continue
        if segment.get("selected", True) is False:
            continue
        if start < 0.0 or end <= start:
            continue

        result.append(
            {
                "number": len(result) + 1,
                "original_index": original_index,
                "start": start,
                "end": end,
                "duration": end - start,
                "name": str(segment.get("name", "")),
            }
        )

    if not result:
        raise RuntimeError("Aucun segment sélectionné et valide dans le LLC.")

    return data, result


def resolve_source_from_llc(llc_path: Path, data: Dict[str, Any]) -> Optional[Path]:
    media_name = data.get("mediaFileName")
    if not isinstance(media_name, str) or not media_name.strip():
        return None

    raw = media_name.strip().strip('"')
    candidates = [
        Path(raw),
        llc_path.parent / Path(raw),
        llc_path.parent / Path(raw).name,
        llc_path.parent / Path(raw.replace("\\", os.sep)),
    ]

    seen = set()
    for candidate in candidates:
        try:
            key = str(candidate.resolve()).lower()
        except Exception:
            key = str(candidate).lower()
        if key in seen:
            continue
        seen.add(key)
        try:
            if candidate.is_file():
                return candidate.resolve()
        except OSError:
            pass
    return None


# ============================================================
# FFPROBE
# ============================================================

def ffprobe_json(video_path: Path) -> Dict[str, Any]:
    ensure_programs()
    result = run_capture([
        str(FFPROBE),
        "-v", "error",
        "-print_format", "json",
        "-show_streams",
        "-show_format",
        "-i", str(video_path),
    ])
    if result.returncode != 0:
        raise RuntimeError(
            f"FFprobe a échoué pour :\n{video_path}\n\n{result.stderr.strip()}"
        )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("FFprobe a renvoyé un JSON invalide.") from exc


def get_video_info(video_path: Path) -> Dict[str, Any]:
    probe = ffprobe_json(video_path)
    streams = probe.get("streams") or []

    primary_videos = [
        s for s in streams
        if s.get("codec_type") == "video"
        and not (s.get("disposition") or {}).get("attached_pic", 0)
    ]
    audios = [s for s in streams if s.get("codec_type") == "audio"]

    if not primary_videos:
        raise RuntimeError(f"Aucun flux vidéo principal trouvé dans : {video_path}")

    try:
        duration = float((probe.get("format") or {}).get("duration") or 0.0)
    except (TypeError, ValueError):
        duration = 0.0

    video = primary_videos[0]
    return {
        "path": video_path,
        "probe": probe,
        "video": video,
        "video_count": len(primary_videos),
        "audio_count": len(audios),
        "duration": duration,
        "width": int(video.get("width") or 0),
        "height": int(video.get("height") or 0),
        "codec": str(video.get("codec_name") or "unknown"),
        "fps": normalize_fps_expression(video),
        "cfr": is_source_cfr(video),
    }


# ============================================================
# QSV
# ============================================================

def test_qsv_encoder() -> Tuple[bool, str]:
    ensure_programs()
    null_device = "NUL" if os.name == "nt" else "/dev/null"
    result = run_capture([
        str(FFMPEG),
        "-hide_banner",
        "-loglevel", "error",
        "-f", "lavfi",
        "-i", "color=c=black:s=128x72:r=30",
        "-t", "0.5",
        "-an",
        "-c:v", ENCODER,
        "-preset", QSV_PRESET,
        "-global_quality", str(QSV_GLOBAL_QUALITY),
        "-f", "null",
        null_device,
    ])
    return result.returncode == 0, result.stderr.strip() or "OK"


# ============================================================
# FILTRE
# ============================================================

def build_filter_complex(
    segments: Sequence[Dict[str, Any]],
    has_audio: bool,
    add_fps_filter: bool,
    fps_expression: str,
) -> str:
    n = len(segments)
    parts: List[str] = []
    ordered_inputs: List[str] = []

    for i in range(n):
        video_chain = f"[{i}:v:0]setpts=PTS-STARTPTS"
        if add_fps_filter:
            video_chain += f",fps=fps={fps_expression}"
        video_chain += f",format=nv12[v{i}]"
        parts.append(video_chain)

        if has_audio:
            parts.append(f"[{i}:a:0]asetpts=PTS-STARTPTS[a{i}]")
            ordered_inputs.extend([f"[v{i}]", f"[a{i}]"])
        else:
            ordered_inputs.append(f"[v{i}]")

    if has_audio:
        parts.append(
            "".join(ordered_inputs)
            + f"concat=n={n}:v=1:a=1[outv][outa]"
        )
    else:
        parts.append(
            "".join(ordered_inputs)
            + f"concat=n={n}:v=1:a=0[outv]"
        )

    return ";".join(parts)


# ============================================================
# ARGUMENTS FFMPEG
# ============================================================

def build_ffmpeg_arguments(
    source_path: Path,
    segments: Sequence[Dict[str, Any]],
    filter_complex: str,
    has_audio: bool,
    output_path: Path,
    fps_expression: str,
    use_hw_decode: bool,
) -> List[str]:
    args: List[str] = ["-y"]

    if use_hw_decode:
        args.extend([
            "-init_hw_device",
            f"qsv=hw,child_device_type={QSV_CHILD_DEVICE_TYPE}",
        ])

    for segment in segments:
        if use_hw_decode:
            args.extend([
                "-hwaccel", "qsv",
                "-hwaccel_output_format", "nv12",
            ])

        args.extend([
            "-ss", f"{float(segment['start']):.6f}",
            "-accurate_seek",
            "-t", f"{float(segment['duration']):.6f}",
            "-i", str(source_path),
        ])

    args.extend([
        "-filter_complex", filter_complex,
        "-map", "[outv]",
    ])

    if has_audio:
        args.extend([
            "-map", "[outa]",
            "-c:a", AUDIO_CODEC,
            "-b:a", AUDIO_BITRATE,
        ])

    args.extend([
        "-c:v", ENCODER,
        "-preset", QSV_PRESET,
        "-global_quality", str(QSV_GLOBAL_QUALITY),
        "-bf", str(QSV_B_FRAMES),
    ])

    if FORCE_CFR:
        args.extend([
            "-fps_mode", "cfr",
            "-r", fps_expression,
        ])

    if FASTSTART:
        args.extend(["-movflags", "+faststart"])

    # CORRECTIF EXPLORATEUR WINDOWS : Empêche l'exportation des métadonnées et chapitres de la source originale
    args.extend([
        "-map_metadata", "-1",
        "-map_chapters", "-1",
        "-sn",
        "-dn",
        "-write_tmcd", "0",
        str(output_path),
    ])

    return args


# ============================================================
# PAUSE / REPRISE DU PROCESSUS WINDOWS
# ============================================================

class WindowsProcessController:
    """
    Suspend/reprend FFmpeg sous Windows.

    NtSuspendProcess / NtResumeProcess sont utilisés lorsque disponibles.
    Ce sont des fonctions natives de ntdll et non des APIs Win32 documentées.
    """

    PROCESS_SUSPEND_RESUME = 0x0800
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    SYNCHRONIZE = 0x00100000

    def __init__(self) -> None:
        self._suspend = None
        self._resume = None
        self._handle = None
        self._paused = False

        if os.name == "nt":
            try:
                ntdll = ctypes.WinDLL("ntdll.dll")
                self._suspend = ntdll.NtSuspendProcess
                self._suspend.argtypes = [wintypes.HANDLE]
                self._suspend.restype = wintypes.LONG

                self._resume = ntdll.NtResumeProcess
                self._resume.argtypes = [wintypes.HANDLE]
                self._resume.restype = wintypes.LONG
            except Exception:
                self._suspend = None
                self._resume = None

    @property
    def supported(self) -> bool:
        return (
            os.name == "nt"
            and self._suspend is not None
            and self._resume is not None
        )

    def attach(self, process: subprocess.Popen[Any]) -> None:
        self.close()

        if not self.supported:
            raise RuntimeError(
                "La pause réelle est disponible sous Windows uniquement."
            )

        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.argtypes = [
            wintypes.DWORD,
            wintypes.BOOL,
            wintypes.DWORD,
        ]
        kernel32.OpenProcess.restype = wintypes.HANDLE

        access = (
            self.PROCESS_SUSPEND_RESUME
            | self.PROCESS_QUERY_LIMITED_INFORMATION
            | self.SYNCHRONIZE
        )

        handle = kernel32.OpenProcess(
            access,
            False,
            int(process.pid),
        )

        if not handle:
            error = ctypes.get_last_error()
            raise OSError(error, f"OpenProcess a échoué pour PID {process.pid}")

        self._handle = handle
        self._paused = False

    def pause(self) -> None:
        if not self._handle or not self._suspend:
            raise RuntimeError("Processus FFmpeg non disponible pour la pause.")
        if self._paused:
            return

        status = int(self._suspend(self._handle))
        if status != 0:
            raise RuntimeError(
                f"NtSuspendProcess a échoué : 0x{status & 0xFFFFFFFF:08X}"
            )
        self._paused = True

    def resume(self) -> None:
        if not self._handle or not self._resume:
            return
        if not self._paused:
            return

        status = int(self._resume(self._handle))
        if status != 0:
            raise RuntimeError(
                f"NtResumeProcess a échoué : 0x{status & 0xFFFFFFFF:08X}"
            )
        self._paused = False

    def close(self) -> None:
        if self._handle:
            try:
                if self._paused and self._resume:
                    self._resume(self._handle)
            except Exception:
                pass

            try:
                kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
                kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
                kernel32.CloseHandle.restype = wintypes.BOOL
                kernel32.CloseHandle(self._handle)
            except Exception:
                pass

        self._handle = None
        self._paused = False


# ============================================================
# ARRÊT FFmpeg
# ============================================================

def terminate_process(process: Optional[subprocess.Popen[Any]]) -> None:
    if process is None:
        return

    try:
        if process.poll() is None:
            process.terminate()
    except Exception:
        pass

    try:
        process.wait(timeout=1.5)
        return
    except subprocess.TimeoutExpired:
        pass

    if os.name == "nt":
        try:
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=5,
            )
        except Exception:
            pass

    try:
        process.kill()
    except Exception:
        pass

    try:
        process.wait(timeout=2.0)
    except Exception:
        pass


# ============================================================
# FFmpeg PROGRESS
# ============================================================

def invoke_ffmpeg_progress(
    arguments: Sequence[str],
    total_seconds: float,
    progress_queue: "queue.Queue[Tuple[str, Any]]",
    cancel_event: threading.Event,
    process_holder: Dict[str, Optional[subprocess.Popen[Any]]],
    controller: WindowsProcessController,
) -> Tuple[int, str]:
    ensure_programs()

    startupinfo, creationflags = windows_startupinfo()

    command = [
        str(FFMPEG),
        "-hide_banner",
        "-loglevel", "error",
        "-nostdin",
        "-progress", "pipe:1",
        "-stats_period", str(PROGRESS_INTERVAL),
        *[str(x) for x in arguments],
    ]

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        startupinfo=startupinfo,
        creationflags=creationflags,
    )

    process_holder["process"] = process

    try:
        controller.attach(process)
        progress_queue.put(("process_ready", controller.supported))
    except Exception as exc:
        progress_queue.put(("log", f"Pause FFmpeg indisponible : {exc}"))
        progress_queue.put(("process_ready", False))

    stderr_lines: List[str] = []

    def read_stderr() -> None:
        if process.stderr is None:
            return
        for line in process.stderr:
            stderr_lines.append(line)

    stderr_thread = threading.Thread(target=read_stderr, daemon=True)
    stderr_thread.start()

    last_report = -1.0
    started = time.perf_counter()
    cancelled = False

    try:
        assert process.stdout is not None

        for raw_line in process.stdout:
            if cancel_event.is_set():
                cancelled = True
                try:
                    controller.resume()
                except Exception:
                    pass
                terminate_process(process)
                break

            line = raw_line.strip()
            if not line.startswith("out_time_us="):
                continue

            try:
                current_seconds = float(line.split("=", 1)[1]) / 1_000_000.0
            except (ValueError, TypeError):
                continue

            current_seconds = max(0.0, current_seconds)

            if total_seconds > 0:
                percent = min(100.0, current_seconds / total_seconds * 100.0)
            else:
                percent = 0.0

            elapsed_wall = max(0.001, time.perf_counter() - started)
            speed_x = current_seconds / elapsed_wall
            eta = (
                max(0.0, (total_seconds - current_seconds) / speed_x)
                if speed_x > 0
                else 0.0
            )

            if current_seconds - last_report >= 0.05 or percent >= 100.0:
                last_report = current_seconds
                progress_queue.put((
                    "progress",
                    {
                        "seconds": current_seconds,
                        "percent": percent,
                        "speed": speed_x,
                        "eta": eta,
                    },
                ))

    finally:
        if cancelled and process.poll() is None:
            try:
                controller.resume()
            except Exception:
                pass
            terminate_process(process)

        try:
            process.wait()
        except Exception:
            pass

        stderr_thread.join(timeout=2.0)
        controller.close()
        process_holder["process"] = None

    if cancelled:
        raise FusionCancelled()

    return process.returncode, "".join(stderr_lines).strip()


# ============================================================
# VALIDATION RAPIDE
# ============================================================

def validate_output_fast(
    output_path: Path,
    expected_duration: float,
    segment_count: int,
    expect_audio: bool,
) -> Tuple[bool, str]:
    if not output_path.is_file():
        return False, "Fichier de sortie absent."

    try:
        size = output_path.stat().st_size
    except OSError as exc:
        return False, f"Impossible de lire la taille : {exc}"

    if size < 2048:
        return False, "Fichier vide ou anormalement petit."

    try:
        info = get_video_info(output_path)
    except Exception as exc:
        return False, f"FFprobe erreur : {exc}"

    if info["video_count"] != 1:
        return False, f"Nombre de flux vidéo incorrect : {info['video_count']}"

    if expect_audio and info["audio_count"] < 1:
        return False, "Piste audio manquante."

    # Validation uniquement des métadonnées / durée.
    # Aucun décodage frame par frame.
    tolerance = max(1.5, 0.05 * segment_count)
    duration_error = abs(info["duration"] - expected_duration)

    if duration_error > tolerance:
        return (
            False,
            f"Écart de durée trop important : {duration_error:.3f}s "
            f"(tolérance {tolerance:.3f}s).",
        )

    return (
        True,
        f"OK — durée {info['duration']:.3f}s | "
        f"{info['width']}x{info['height']} | "
        f"vidéo={info['codec']} | "
        f"audio={'oui' if info['audio_count'] else 'non'}",
    )


# ============================================================
# NOM SORTIE
# ============================================================

def make_output_path(source_path: Path) -> Path:
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    candidate = source_path.with_name(
        f"{source_path.stem}_Fusion_LLC_{timestamp}{OUTPUT_EXTENSION}"
    )

    if not candidate.exists():
        return candidate

    index = 2
    while True:
        candidate = source_path.with_name(
            f"{source_path.stem}_Fusion_LLC_{timestamp}_{index}{OUTPUT_EXTENSION}"
        )
        if not candidate.exists():
            return candidate
        index += 1


# ============================================================
# GUI
# ============================================================

class FusionApp(tk.Tk):

    BG = "#0B1120"
    PANEL = "#111827"
    PANEL_2 = "#182235"
    FIELD = "#0F172A"
    TEXT = "#F8FAFC"
    MUTED = "#94A3B8"
    BORDER = "#263449"
    BLUE = "#3B82F6"
    BLUE_HOVER = "#2563EB"
    AMBER = "#F59E0B"
    AMBER_HOVER = "#D97706"
    RED = "#EF4444"
    RED_HOVER = "#DC2626"
    GREEN = "#22C55E"

    def __init__(self) -> None:
        super().__init__()

        self.title("Fusion LosslessCut — H.264 QSV")
        self.geometry("980x720")
        self.minsize(760, 560)
        self.configure(bg=self.BG)

        # Projet
        self.llc_path: Optional[Path] = None
        self.source_path: Optional[Path] = None
        self.segments: List[Dict[str, Any]] = []
        self.source_info: Optional[Dict[str, Any]] = None
        self.expected_duration = 0.0

        # Exécution
        self.worker: Optional[threading.Thread] = None
        self.cancel_event = threading.Event()
        self.progress_queue: "queue.Queue[Tuple[str, Any]]" = queue.Queue()
        self.process_holder: Dict[str, Optional[subprocess.Popen[Any]]] = {
            "process": None
        }
        self.controller = WindowsProcessController()

        self.running = False
        self.paused = False
        self.process_ready = False
        self.stopping = False
        self.last_output: Optional[Path] = None

        self.run_use_hw_decode = USE_HW_DECODE_DEFAULT
        self.run_validation = FAST_VALIDATION

        self._configure_style()
        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.bind("<space>", self._space_shortcut)
        self.bind("<Escape>", self._escape_shortcut)
        self.after(GUI_POLL_INTERVAL_MS, self.poll_queue)

    # --------------------------------------------------------
    # STYLE
    # --------------------------------------------------------

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(
            "Q.Horizontal.TProgressbar",
            troughcolor="#0A1020",
            background=self.BLUE,
            lightcolor=self.BLUE,
            darkcolor=self.BLUE,
            bordercolor="#0A1020",
            thickness=18,
        )

    # --------------------------------------------------------
    # UI PRINCIPALE
    # --------------------------------------------------------

    def _build_ui(self) -> None:
        # ----------------------------------------------------
        # STRUCTURE GÉNÉRALE
        # ----------------------------------------------------
        outer = tk.Frame(self, bg=self.BG)
        outer.pack(fill="both", expand=True)

        footer = tk.Frame(outer, bg=self.BG)
        footer.pack(side="bottom", fill="x", padx=18, pady=(8, 14))

        # ----------------------------------------------------
        # PROGRESSION FIXE
        # ----------------------------------------------------
        progress_panel = self._panel(footer)
        progress_panel.pack(fill="x", pady=(0, 8))
        self._panel_title(progress_panel, "PROGRESSION")

        top = tk.Frame(progress_panel, bg=self.PANEL)
        top.pack(fill="x", padx=12, pady=(0, 5))

        self.percent_var = tk.StringVar(value="0.0 %")
        tk.Label(
            top,
            textvariable=self.percent_var,
            bg=self.PANEL,
            fg=self.TEXT,
            font=("Segoe UI", 23, "bold"),
        ).pack(side="left")

        stats = tk.Frame(top, bg=self.PANEL)
        stats.pack(side="right", pady=(4, 0))

        self.time_var = tk.StringVar(value="00:00:00.000 / 00:00:00.000")
        self.speed_var = tk.StringVar(value="Vitesse : —")
        self.eta_var = tk.StringVar(value="ETA : —")
        for var in (self.time_var, self.speed_var, self.eta_var):
            tk.Label(
                stats,
                textvariable=var,
                bg=self.PANEL,
                fg=self.MUTED,
                font=("Segoe UI", 8),
            ).pack(anchor="e")

        self.progress = ttk.Progressbar(
            progress_panel,
            style="Q.Horizontal.TProgressbar",
            orient="horizontal",
            mode="determinate",
            maximum=100.0,
        )
        self.progress.pack(fill="x", padx=12, pady=(0, 7))

        self.status_var = tk.StringVar(
            value="Prêt à démarrer. Sélectionne un LLC puis clique sur Lancer."
        )
        self.status_label = tk.Label(
            progress_panel,
            textvariable=self.status_var,
            bg=self.PANEL,
            fg=self.TEXT,
            font=("Segoe UI", 9, "bold"),
        )
        self.status_label.pack(anchor="w", padx=12, pady=(0, 9))

        # ----------------------------------------------------
        # COMMANDES FIXES
        # ----------------------------------------------------
        controls = tk.Frame(footer, bg=self.BG)
        controls.pack(fill="x")
        controls.grid_columnconfigure(0, weight=1, uniform="actions")
        controls.grid_columnconfigure(1, weight=1, uniform="actions")
        controls.grid_columnconfigure(2, weight=1, uniform="actions")

        self.start_button = self._action_button(
            controls,
            "▶  LANCER LA FUSION",
            self.start_fusion,
            self.BLUE,
            self.BLUE_HOVER,
        )
        self.start_button.grid(row=0, column=0, sticky="ew", padx=(0, 4), ipady=6)

        self.pause_button = self._action_button(
            controls,
            "⏸  PAUSE",
            self.toggle_pause,
            self.AMBER,
            self.AMBER_HOVER,
        )
        self.pause_button.grid(row=0, column=1, sticky="ew", padx=4, ipady=6)
        self.pause_button.config(state="disabled")

        self.stop_button = self._action_button(
            controls,
            "■  STOPPER",
            self.stop_fusion,
            self.RED,
            self.RED_HOVER,
        )
        self.stop_button.grid(row=0, column=2, sticky="ew", padx=(4, 0), ipady=6)
        self.stop_button.config(state="disabled")

        self.control_hint = tk.Label(
            controls,
            text="Espace = Pause/Reprendre   •   Échap = Stopper",
            bg=self.BG,
            fg=self.MUTED,
            font=("Segoe UI", 8),
        )
        self.control_hint.grid(row=1, column=0, columnspan=3, pady=(4, 0))

        # ----------------------------------------------------
        # ZONE SCROLLABLE
        # ----------------------------------------------------
        scroll_area = tk.Frame(outer, bg=self.BG)
        scroll_area.pack(side="top", fill="both", expand=True, padx=18, pady=(14, 0))

        canvas = tk.Canvas(
            scroll_area,
            bg=self.BG,
            highlightthickness=0,
            bd=0,
        )
        scrollbar = tk.Scrollbar(
            scroll_area,
            orient="vertical",
            command=canvas.yview,
            bg=self.PANEL_2,
            troughcolor=self.BG,
            activebackground=self.BLUE,
            relief="flat",
            width=13,
        )
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y", padx=(5, 0))

        canvas.configure(yscrollcommand=scrollbar.set)

        content = tk.Frame(canvas, bg=self.BG)
        window_id = canvas.create_window((0, 0), window=content, anchor="nw")

        def update_scroll_region(_event: Optional[tk.Event] = None) -> None:
            canvas.configure(scrollregion=canvas.bbox("all"))

        def resize_content(event: tk.Event) -> None:
            canvas.itemconfigure(window_id, width=event.width)

        content.bind("<Configure>", update_scroll_region)
        canvas.bind("<Configure>", resize_content)

        self.scroll_canvas = canvas

        def mousewheel(event: tk.Event) -> None:
            delta = getattr(event, "delta", 0)
            if delta:
                canvas.yview_scroll(int(-delta / 120), "units")

        canvas.bind_all("<MouseWheel>", mousewheel, add="+")

        # ----------------------------------------------------
        # CONTENU DÉFILABLE
        # ----------------------------------------------------
        header = tk.Frame(content, bg=self.BG)
        header.pack(fill="x", pady=(0, 12))

        title_row = tk.Frame(header, bg=self.BG)
        title_row.pack(fill="x")

        tk.Label(
            title_row,
            text="🎬  FUSION LOSSLESSCUT",
            bg=self.BG,
            fg=self.TEXT,
            font=("Segoe UI", 21, "bold"),
        ).pack(side="left")

        self.status_pill = tk.Label(
            title_row,
            text="  PRÊT  ",
            bg="#1E293B",
            fg=self.MUTED,
            font=("Segoe UI", 9, "bold"),
            padx=8,
            pady=4,
        )
        self.status_pill.pack(side="right", pady=2)

        tk.Label(
            header,
            text="Fusion rapide de segments • Intel Quick Sync Video • une seule session FFmpeg",
            bg=self.BG,
            fg=self.MUTED,
            font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(3, 0))

        # FICHIERS
        files_panel = self._panel(content)
        files_panel.pack(fill="x", pady=(0, 10))
        self._panel_title(files_panel, "FICHIERS")

        self.llc_var = tk.StringVar()
        self.source_var = tk.StringVar()
        self._file_row(files_panel, "Projet LLC", self.llc_var, self.choose_llc)
        self._file_row(files_panel, "Vidéo source", self.source_var, self.choose_source)

        # INFOS
        info_panel = self._panel(content)
        info_panel.pack(fill="x", pady=(0, 10))
        self._panel_title(info_panel, "ANALYSE")

        grid = tk.Frame(info_panel, bg=self.PANEL)
        grid.pack(fill="x", padx=12, pady=(0, 12))

        self.info_vars: Dict[str, tk.StringVar] = {}
        labels = [
            ("Segments", "—"),
            ("Durée finale", "—"),
            ("Résolution", "—"),
            ("Codec source", "—"),
            ("FPS", "—"),
            ("Audio", "—"),
        ]

        for i, (label, initial) in enumerate(labels):
            row, col = divmod(i, 3)
            cell = tk.Frame(grid, bg=self.PANEL_2)
            cell.grid(row=row, column=col, sticky="ew", padx=4, pady=4, ipadx=8, ipady=7)
            grid.columnconfigure(col, weight=1)

            tk.Label(
                cell,
                text=label.upper(),
                bg=self.PANEL_2,
                fg=self.MUTED,
                font=("Segoe UI", 8, "bold"),
            ).pack(anchor="w")

            var = tk.StringVar(value=initial)
            self.info_vars[label] = var
            tk.Label(
                cell,
                textvariable=var,
                bg=self.PANEL_2,
                fg=self.TEXT,
                font=("Segoe UI", 10, "bold"),
            ).pack(anchor="w", pady=(2, 0))

        # OPTIONS
        options_panel = self._panel(content)
        options_panel.pack(fill="x", pady=(0, 10))
        self._panel_title(options_panel, "OPTIONS DE VITESSE")

        inside = tk.Frame(options_panel, bg=self.PANEL)
        inside.pack(fill="x", padx=12, pady=(0, 11))

        self.hw_decode_var = tk.BooleanVar(value=USE_HW_DECODE_DEFAULT)
        self.validation_var = tk.BooleanVar(value=FAST_VALIDATION)

        self.hw_check = self._checkbutton(
            inside,
            "Décodage QSV (test / repli CPU)",
            self.hw_decode_var,
        )
        self.hw_check.pack(anchor="w", pady=(0, 4))

        self.validation_check = self._checkbutton(
            inside,
            "Validation FFprobe rapide",
            self.validation_var,
        )
        self.validation_check.pack(anchor="w")

        tk.Label(
            inside,
            text=f"Encodeur : {ENCODER} • {QSV_PRESET} • Q{QSV_GLOBAL_QUALITY}",
            bg=self.PANEL,
            fg=self.MUTED,
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(6, 0))

        # JOURNAL
        log_panel = self._panel(content)
        log_panel.pack(fill="both", expand=True, pady=(0, 10))
        self._panel_title(log_panel, "JOURNAL")

        log_inner = tk.Frame(log_panel, bg=self.PANEL)
        log_inner.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.log_text = tk.Text(
            log_inner,
            bg="#080D18",
            fg="#CBD5E1",
            insertbackground=self.TEXT,
            relief="flat",
            wrap="word",
            font=("Consolas", 9),
            padx=10,
            pady=8,
            height=8,
            state="disabled",
        )
        self.log_text.pack(side="left", fill="both", expand=True)

        log_scroll = tk.Scrollbar(
            log_inner,
            orient="vertical",
            command=self.log_text.yview,
            bg=self.PANEL,
            troughcolor="#080D18",
            relief="flat",
        )
        log_scroll.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=log_scroll.set)

        self.after(50, update_scroll_region)

    # --------------------------------------------------------
    # PETITS WIDGETS
    # --------------------------------------------------------

    def _panel(self, parent: tk.Widget) -> tk.Frame:
        return tk.Frame(
            parent,
            bg=self.PANEL,
            highlightbackground=self.BORDER,
            highlightthickness=1,
            bd=0,
        )

    def _panel_title(self, parent: tk.Frame, text: str) -> None:
        tk.Label(
            parent,
            text=text,
            bg=self.PANEL,
            fg=self.MUTED,
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor="w", padx=12, pady=(10, 7))

    def _file_row(
        self,
        parent: tk.Frame,
        label: str,
        variable: tk.StringVar,
        command: Any,
    ) -> None:
        row = tk.Frame(parent, bg=self.PANEL)
        row.pack(fill="x", padx=12, pady=4)

        tk.Label(
            row,
            text=label,
            bg=self.PANEL,
            fg=self.TEXT,
            width=13,
            anchor="w",
            font=("Segoe UI", 9, "bold"),
        ).pack(side="left")

        entry = tk.Entry(
            row,
            textvariable=variable,
            state="readonly",
            readonlybackground=self.FIELD,
            bg=self.FIELD,
            fg=self.TEXT,
            relief="flat",
            font=("Segoe UI", 9),
        )
        entry.pack(side="left", fill="x", expand=True, padx=(7, 7), ipady=7)

        tk.Button(
            row,
            text="PARCOURIR",
            command=command,
            bg="#25344A",
            fg=self.TEXT,
            activebackground="#334866",
            activeforeground=self.TEXT,
            relief="flat",
            bd=0,
            padx=14,
            pady=7,
            cursor="hand2",
            font=("Segoe UI", 9, "bold"),
        ).pack(side="right")

    def _checkbutton(
        self,
        parent: tk.Frame,
        text: str,
        variable: tk.BooleanVar,
    ) -> tk.Checkbutton:
        return tk.Checkbutton(
            parent,
            text=text,
            variable=variable,
            bg=self.PANEL,
            fg=self.TEXT,
            activebackground=self.PANEL,
            activeforeground=self.TEXT,
            selectcolor=self.FIELD,
            font=("Segoe UI", 9),
            bd=0,
            highlightthickness=0,
        )

    def _action_button(
        self,
        parent: tk.Frame,
        text: str,
        command: Any,
        bg: str,
        active_bg: str,
    ) -> tk.Button:
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg="white",
            activebackground=active_bg,
            activeforeground="white",
            disabledforeground="#94A3B8",
            relief="flat",
            bd=0,
            cursor="hand2",
            font=("Segoe UI", 10, "bold"),
            pady=9,
        )

    # --------------------------------------------------------
    # JOURNAL
    # --------------------------------------------------------

    def log(self, message: str) -> None:
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    # --------------------------------------------------------
    # ÉTAT INTERFACE
    # --------------------------------------------------------

    def set_status_pill(self, text: str, bg: str, fg: str = "white") -> None:
        self.status_pill.config(text=f"  {text}  ", bg=bg, fg=fg)

    def set_running_state(self, running: bool) -> None:
        if running:
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
            self.hw_check.config(state="disabled")
            self.validation_check.config(state="disabled")
        else:
            self.start_button.config(state="normal")
            self.pause_button.config(state="disabled")
            self.stop_button.config(state="disabled")
            self.hw_check.config(state="normal")
            self.validation_check.config(state="normal")

    # --------------------------------------------------------
    # CHOISIR LLC
    # --------------------------------------------------------

    def choose_llc(self) -> None:
        initial = Path.home() / "Downloads"
        if not initial.exists():
            initial = Path.home()

        path = filedialog.askopenfilename(
            title="Sélectionnez le fichier LosslessCut (.llc)",
            initialdir=str(initial),
            filetypes=[
                ("Projet LosslessCut", "*.llc"),
                ("Tous les fichiers", "*.*"),
            ],
        )
        if not path:
            return

        try:
            llc = Path(path)
            data, segments = load_llc(llc)
            source = resolve_source_from_llc(llc, data)

            self.llc_path = llc
            self.segments = segments
            self.expected_duration = sum(float(s["duration"]) for s in segments)
            self.llc_var.set(str(llc))

            self.log(f"LLC chargé : {llc.name}")
            self.log(f"Segments valides : {len(segments)}")
            self.log(f"Durée finale attendue : {format_time(self.expected_duration)}")

            if source:
                self.source_path = source
                self.source_var.set(str(source))
                self.load_source_info()
            else:
                self.source_path = None
                self.source_var.set("")
                self.clear_info()
                self.status_var.set("Source non trouvée automatiquement — choisis-la manuellement.")

        except Exception as exc:
            messagebox.showerror("Erreur LLC", str(exc))

    # --------------------------------------------------------
    # CHOISIR SOURCE
    # --------------------------------------------------------

    def choose_source(self) -> None:
        initial = self.llc_path.parent if self.llc_path else Path.home() / "Downloads"
        if not initial.exists():
            initial = Path.home()

        path = filedialog.askopenfilename(
            title="Sélectionnez la vidéo source",
            initialdir=str(initial),
            filetypes=[
                (
                    "Vidéos",
                    "*.mp4 *.mkv *.mov *.avi *.webm *.m4v *.ts *.mts *.m2ts *.flv *.wmv *.vob *.mxf *.ogg",
                ),
                ("Tous les fichiers", "*.*"),
            ],
        )
        if not path:
            return

        self.source_path = Path(path)
        self.source_var.set(str(self.source_path))
        self.load_source_info()

    # --------------------------------------------------------
    # ANALYSE SOURCE
    # --------------------------------------------------------

    def clear_info(self) -> None:
        for var in self.info_vars.values():
            var.set("—")

    def load_source_info(self, show_error: bool = True) -> None:
        if not self.source_path:
            return

        try:
            self.source_info = get_video_info(self.source_path)
            info = self.source_info

            self.info_vars["Segments"].set(str(len(self.segments)))
            self.info_vars["Durée finale"].set(format_time(self.expected_duration))
            self.info_vars["Résolution"].set(f"{info['width']} × {info['height']}")
            self.info_vars["Codec source"].set(info["codec"])
            self.info_vars["FPS"].set(f"{info['fps']} ({'CFR' if info['cfr'] else 'VFR'})")
            self.info_vars["Audio"].set("Oui" if info["audio_count"] else "Non")

            self.status_var.set("Prêt à démarrer. Clique sur « Lancer la fusion »." if self.segments else "Source chargée.")
            self.set_status_pill("PRÊT", "#1E293B", self.MUTED)

            self.log(
                f"Source : {self.source_path.name} | "
                f"{info['width']}x{info['height']} | {info['codec']} | {info['fps']}"
            )

        except Exception as exc:
            self.source_info = None
            self.clear_info()
            if show_error:
                messagebox.showerror("Erreur source", str(exc))

    # --------------------------------------------------------
    # LANCER
    # --------------------------------------------------------

    def start_fusion(self) -> None:
        if self.running:
            return

        if not self.llc_path or not self.llc_path.is_file():
            messagebox.showwarning("Projet LLC", "Sélectionne d'abord un fichier .llc.")
            return

        if not self.segments:
            messagebox.showwarning("Segments", "Aucun segment valide trouvé dans le LLC.")
            return

        if not self.source_path or not self.source_path.is_file():
            messagebox.showwarning("Vidéo source", "Sélectionne la vidéo source.")
            return

        if not self.source_info:
            self.load_source_info()
            if not self.source_info:
                return

        self.cancel_event.clear()
        self.stopping = False
        self.paused = False
        self.process_ready = False
        self.running = True
        self.run_use_hw_decode = bool(self.hw_decode_var.get())
        self.run_validation = bool(self.validation_var.get())

        self.progress["value"] = 0.0
        self.percent_var.set("0.0 %")
        self.time_var.set(f"00:00:00.000 / {format_time(self.expected_duration)}")
        self.speed_var.set("Vitesse : —")
        self.eta_var.set("ETA : —")
        self.status_var.set("Préparation de FFmpeg…")
        self.status_label.config(fg=self.TEXT)
        self.set_status_pill("PRÉPARATION", "#334155")

        self.set_running_state(True)
        self.pause_button.config(state="disabled", text="⏸  PAUSE")
        self.log("")
        self.log("==================== FUSION ====================")

        self.worker = threading.Thread(target=self.fusion_worker, daemon=True)
        self.worker.start()

    # --------------------------------------------------------
    # PAUSE / REPRENDRE
    # --------------------------------------------------------

    def toggle_pause(self) -> None:
        if not self.running or not self.process_ready:
            return

        process = self.process_holder.get("process")
        if process is None or process.poll() is not None:
            self.process_ready = False
            self.pause_button.config(state="disabled")
            return

        if self.paused:
            try:
                self.controller.resume()
                self.paused = False
                self.pause_button.config(text="⏸  PAUSE")
                self.status_var.set("Fusion reprise…")
                self.status_label.config(fg=self.TEXT)
                self.set_status_pill("EN COURS", self.BLUE)
                self.log("▶ Fusion reprise.")
            except Exception as exc:
                messagebox.showerror("Reprendre", str(exc))
            return

        try:
            self.controller.pause()
            self.paused = True
            self.pause_button.config(text="▶  REPRENDRE")
            self.status_var.set("Fusion en pause — FFmpeg est suspendu.")
            self.status_label.config(fg=self.AMBER)
            self.set_status_pill("EN PAUSE", self.AMBER)
            self.log("⏸ Fusion mise en pause.")
        except Exception as exc:
            messagebox.showerror("Pause", str(exc))

    # --------------------------------------------------------
    # STOPPER
    # --------------------------------------------------------

    def stop_fusion(self) -> None:
        if not self.running:
            return

        confirm = messagebox.askyesno(
            "Stopper la fusion",
            "Arrêter FFmpeg et supprimer le fichier temporaire ?",
        )
        if not confirm:
            return

        self.stopping = True
        self.cancel_event.set()
        self.process_ready = False
        self.pause_button.config(state="disabled")
        self.stop_button.config(state="disabled")
        self.status_var.set("Arrêt de FFmpeg…")
        self.status_label.config(fg=self.RED)
        self.set_status_pill("ARRÊT", self.RED)

        try:
            self.controller.resume()
        except Exception:
            pass

        terminate_process(self.process_holder.get("process"))

    # --------------------------------------------------------
    # WORKER
    # --------------------------------------------------------

    def fusion_worker(self) -> None:
        started = time.perf_counter()
        output_path: Optional[Path] = None
        temp_output: Optional[Path] = None

        try:
            ensure_programs()

            source = self.source_path
            info = self.source_info
            if source is None or info is None:
                raise RuntimeError("Source vidéo indisponible.")

            use_hw_decode = self.run_use_hw_decode
            do_validation = self.run_validation

            self.progress_queue.put(("log", f"FFmpeg : {FFMPEG}"))
            self.progress_queue.put(("log", f"FFprobe : {FFPROBE}"))
            self.progress_queue.put((
                "log",
                f"Encodeur : {ENCODER} | preset={QSV_PRESET} | Q{QSV_GLOBAL_QUALITY}"
            ))
            self.progress_queue.put(("log", "Encodage vidéo : Intel QSV (h264_qsv)"))
            self.progress_queue.put((
                "log",
                "Décodage : " + (
                    "QSV demandé + repli CPU"
                    if use_hw_decode
                    else "CPU logiciel"
                )
            ))

            if TEST_QSV_BEFORE_MERGE:
                self.progress_queue.put(("status", "Test rapide de l'encodeur QSV…"))
                qsv_ok, qsv_msg = test_qsv_encoder()
                if not qsv_ok:
                    raise RuntimeError("Encodeur QSV indisponible :\n" + qsv_msg)

            add_fps_filter = not (AVOID_REDUNDANT_FPS_FILTER and info["cfr"])
            filter_complex = build_filter_complex(
                self.segments,
                has_audio=info["audio_count"] > 0,
                add_fps_filter=add_fps_filter,
                fps_expression=info["fps"],
            )

            output_path = make_output_path(source)
            temp_output = output_path.with_name(
                output_path.stem + ".part" + output_path.suffix
            )

            try:
                if temp_output.exists():
                    temp_output.unlink()
            except OSError:
                pass

            ffmpeg_args = build_ffmpeg_arguments(
                source_path=source,
                segments=self.segments,
                filter_complex=filter_complex,
                has_audio=info["audio_count"] > 0,
                output_path=temp_output,
                fps_expression=info["fps"],
                use_hw_decode=use_hw_decode,
            )

            self.progress_queue.put((
                "log",
                f"Segments : {len(self.segments)} | Durée : {format_time(self.expected_duration)}"
            ))
            self.progress_queue.put((
                "log",
                "Filtre FPS : " + ("actif" if add_fps_filter else "inutile (source CFR)")
            ))
            self.progress_queue.put(("log", "Validation frame-by-frame / PTS : désactivée"))
            self.progress_queue.put(("status", "Fusion FFmpeg en cours…"))

            return_code, stderr = invoke_ffmpeg_progress(
                ffmpeg_args,
                self.expected_duration,
                self.progress_queue,
                self.cancel_event,
                self.process_holder,
                self.controller,
            )

            if (
                return_code != 0
                and use_hw_decode
                and HW_DECODE_FALLBACK_TO_CPU
                and not self.cancel_event.is_set()
            ):
                self.progress_queue.put((
                    "log",
                    "Pipeline QSV decode échoué — nouvelle tentative avec décodage CPU."
                ))

                if temp_output.exists():
                    try:
                        temp_output.unlink()
                    except OSError:
                        pass

                cpu_args = build_ffmpeg_arguments(
                    source_path=source,
                    segments=self.segments,
                    filter_complex=filter_complex,
                    has_audio=info["audio_count"] > 0,
                    output_path=temp_output,
                    fps_expression=info["fps"],
                    use_hw_decode=False,
                )

                self.progress_queue.put(("status", "Fusion FFmpeg — décodage CPU…"))
                return_code, stderr = invoke_ffmpeg_progress(
                    cpu_args,
                    self.expected_duration,
                    self.progress_queue,
                    self.cancel_event,
                    self.process_holder,
                    self.controller,
                )

            if return_code != 0:
                if self.cancel_event.is_set():
                    raise FusionCancelled()
                raise RuntimeError(
                    "FFmpeg a échoué.\n\n" + (stderr.strip() or "Aucun message d'erreur fourni.")
                )

            if not temp_output.is_file():
                raise RuntimeError("FFmpeg a terminé sans créer le fichier temporaire.")

            if do_validation:
                self.progress_queue.put(("status", "Validation FFprobe rapide…"))
                valid, msg = validate_output_fast(
                    temp_output,
                    expected_duration=self.expected_duration,
                    segment_count=len(self.segments),
                    expect_audio=info["audio_count"] > 0,
                )
                if not valid:
                    raise RuntimeError("Validation échouée : " + msg)
                self.progress_queue.put(("log", "Validation : " + msg))
            else:
                self.progress_queue.put(("log", "Validation finale désactivée."))

            if output_path.exists():
                output_path.unlink()
            temp_output.replace(output_path)
            temp_output = None

            elapsed = time.perf_counter() - started
            self.progress_queue.put((
                "progress",
                {
                    "seconds": self.expected_duration,
                    "percent": 100.0,
                    "speed": self.expected_duration / max(0.001, elapsed),
                    "eta": 0.0,
                },
            ))
            self.progress_queue.put((
                "success",
                {
                    "output": str(output_path),
                    "elapsed": elapsed,
                },
            ))

        except FusionCancelled:
            if temp_output:
                try:
                    if temp_output.exists():
                        temp_output.unlink()
                except OSError:
                    pass
            self.progress_queue.put(("cancelled", None))

        except Exception as exc:
            if temp_output:
                try:
                    if temp_output.exists():
                        temp_output.unlink()
                except OSError:
                    pass
            self.progress_queue.put(("error", str(exc)))

        finally:
            if temp_output:
                try:
                    if temp_output.exists():
                        temp_output.unlink()
                except OSError:
                    pass

    # --------------------------------------------------------
    # ÉVÉNEMENTS GUI
    # --------------------------------------------------------

    def poll_queue(self) -> None:
        try:
            while True:
                kind, payload = self.progress_queue.get_nowait()
                self.handle_event(kind, payload)
        except queue.Empty:
            pass
        self.after(GUI_POLL_INTERVAL_MS, self.poll_queue)

    def handle_event(self, kind: str, payload: Any) -> None:
        if kind == "log":
            self.log(str(payload))
            return

        if kind == "status":
            self.status_var.set(str(payload))
            return

        if kind == "process_ready":
            self.process_ready = bool(payload)
            if self.running and not self.paused:
                if self.process_ready:
                    self.pause_button.config(state="normal")
                    self.set_status_pill("EN COURS", self.BLUE)
                else:
                    self.pause_button.config(state="disabled")
            return

        if kind == "progress":
            seconds = float(payload.get("seconds", 0.0))
            percent = float(payload.get("percent", 0.0))
            speed = float(payload.get("speed", 0.0))
            eta = float(payload.get("eta", 0.0))

            self.progress["value"] = max(0.0, min(100.0, percent))
            self.percent_var.set(f"{percent:.1f} %")
            self.time_var.set(
                f"{format_time(seconds)} / {format_time(self.expected_duration)}"
            )
            self.speed_var.set(f"Vitesse : {speed:.2f}×")
            self.eta_var.set(f"ETA : {format_time(eta)}" if speed > 0 else "ETA : —")
            return

        if kind == "success":
            self.running = False
            self.paused = False
            self.process_ready = False
            self.last_output = Path(payload["output"])
            elapsed = float(payload["elapsed"])

            self.set_running_state(False)
            self.progress["value"] = 100.0
            self.percent_var.set("100.0 %")
            self.time_var.set(
                f"{format_time(self.expected_duration)} / {format_time(self.expected_duration)}"
            )
            self.speed_var.set(
                f"Vitesse moyenne : {self.expected_duration / max(0.001, elapsed):.2f}×"
            )
            self.eta_var.set("ETA : 00:00:00.000")
            self.status_var.set("Fusion terminée avec succès.")
            self.status_label.config(fg=self.GREEN)
            self.set_status_pill("TERMINÉ", self.GREEN)

            self.log("==================== TERMINÉ ====================")
            self.log(f"Sortie : {payload['output']}")
            self.log(f"Temps : {elapsed:.2f}s")

            if messagebox.askyesno(
                "Fusion terminée",
                f"Fusion terminée avec succès.\n\nTemps : {elapsed:.2f}s\n\nOuvrir le dossier de sortie ?",
            ):
                try:
                    if os.name == "nt":
                        os.startfile(str(self.last_output.parent))  # type: ignore[attr-defined]
                except Exception:
                    pass
            return

        if kind == "cancelled":
            self.running = False
            self.paused = False
            self.process_ready = False
            self.set_running_state(False)
            self.progress["value"] = 0.0
            self.percent_var.set("0.0 %")
            self.status_var.set("Fusion stoppée. Le fichier temporaire a été supprimé.")
            self.status_label.config(fg=self.RED)
            self.set_status_pill("ARRÊTÉ", self.RED)
            self.log("Fusion stoppée — fichier temporaire supprimé.")
            return

        if kind == "error":
            self.running = False
            self.paused = False
            self.process_ready = False
            self.set_running_state(False)
            self.status_var.set("Erreur pendant la fusion.")
            self.status_label.config(fg=self.RED)
            self.set_status_pill("ERREUR", self.RED)
            self.log("==================== ERREUR ====================")
            self.log(str(payload))
            messagebox.showerror("Erreur de fusion", str(payload))
            return

    # --------------------------------------------------------
    # RACCOURCIS
    # --------------------------------------------------------

    def _space_shortcut(self, _event: tk.Event) -> None:
        if self.running and self.process_ready:
            self.toggle_pause()

    def _escape_shortcut(self, _event: tk.Event) -> None:
        if self.running:
            self.stop_fusion()

    # --------------------------------------------------------
    # FERMETURE
    # --------------------------------------------------------

    def on_close(self) -> None:
        if self.running:
            confirm = messagebox.askyesno(
                "Fermer",
                "Une fusion est en cours. L'arrêter et fermer l'application ?",
            )
            if not confirm:
                return

            self.cancel_event.set()
            try:
                self.controller.resume()
            except Exception:
                pass
            terminate_process(self.process_holder.get("process"))

        self.destroy()


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    try:
        ensure_programs()
    except Exception as exc:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("FFmpeg introuvable", str(exc))
        root.destroy()
        return

    app = FusionApp()
    app.mainloop()


if __name__ == "__main__":
    main()