#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fusion Video Intelligente - version finale

- Windows file picker
- Analyse ffprobe en parallele
- Tente une concatenation sans reencodage si les flux sont strictement compatibles
- Valide reellement la sortie lossless
- Sinon, reencode proprement avec Intel Quick Sync H.264 (h264_qsv)
- Normalise la video en FPS constant et normalise l'audio
- Affiche une vraie barre de progression dynamique

Le script vise les fichiers que FFmpeg sait decoder.
"""

from __future__ import annotations

import concurrent.futures
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from tkinter import Tk, filedialog

DEFAULT_FOLDER = Path(r"C:\Users\babak\Downloads\Avatar\Clips")
VIDEO_EXTS = (".mp4", ".mkv", ".mov", ".m4v", ".avi", ".ts", ".m2ts", ".mts", ".webm")
BAR_WIDTH = 34


@dataclass
class MediaInfo:
    path: Path
    duration: float
    streams: list[dict]
    video_streams: list[dict]
    audio_streams: list[dict]
    subtitle_streams: list[dict]
    data_streams: list[dict]
    other_streams: list[dict]
    first_video_keyframe: bool | None
    first_video_pts: float | None
    first_audio_pts: float | None
    max_video_gap: float | None
    backwards_video_pts: int


def die(message: str, code: int = 1) -> None:
    print("\nERREUR: " + message, file=sys.stderr)
    raise SystemExit(code)


def find_executable(name: str) -> str | None:
    found = shutil.which(name)
    if found:
        return found
    candidates = [
        Path(r"C:\ffmpeg\bin") / name,
        Path(r"C:\Program Files\ffmpeg\bin") / name,
        Path(r"C:\Program Files\FFmpeg\bin") / name,
        Path(r"C:\ProgramData\chocolatey\bin") / name,
    ]
    for p in candidates:
        if p.exists():
            return str(p)
    return None


def run_capture(exe: str, args: list[str], timeout: int = 120) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [exe, *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


def probe_json(ffprobe: str, path: Path, extra: list[str] | None = None, timeout: int = 180) -> dict:
    args = [
        "-v", "error",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        "-show_data",
        "-show_entries",
        (
            "format=format_name,duration,bit_rate,size,format_long_name:"
            "stream=index,codec_type,codec_name,codec_long_name,profile,level,codec_tag_string,"
            "width,height,pix_fmt,field_order,r_frame_rate,avg_frame_rate,time_base,start_time,duration,"
            "sample_aspect_ratio,display_aspect_ratio,color_range,color_space,color_transfer,color_primaries,"
            "channels,channel_layout,sample_rate,sample_fmt,bit_rate,extradata"
        ),
        "-i", str(path),
    ]
    if extra:
        args[0:0] = extra
    result = run_capture(ffprobe, args, timeout=timeout)
    if result.returncode != 0:
        msg = result.stderr.strip() or "ffprobe a echoue"
        raise RuntimeError(f"{path.name}: {msg}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{path.name}: sortie ffprobe invalide") from exc


def rational_to_float(value: str | None) -> float | None:
    if not value or value in {"0/0", "N/A"}:
        return None
    try:
        if "/" in value:
            a, b = value.split("/", 1)
            if float(b) == 0:
                return None
            return float(a) / float(b)
        return float(value)
    except (ValueError, ZeroDivisionError):
        return None


def fnum(value: float | None, decimals: int = 3) -> str:
    if value is None or not math.isfinite(value):
        return "N/A"
    return f"{value:.{decimals}f}"


def stream_key(stream: dict) -> tuple:
    """Fields that matter for concat demuxer compatibility.

    Deliberately ignores bitrate, title and duration because those can differ
    while the elementary stream parameters remain compatible.
    """
    keys = (
        "codec_type", "codec_name", "profile", "level", "codec_tag_string",
        "width", "height", "pix_fmt", "field_order", "r_frame_rate",
        "avg_frame_rate", "time_base", "sample_aspect_ratio", "display_aspect_ratio",
        "color_range", "color_space", "color_transfer", "color_primaries",
        "channels", "channel_layout", "sample_rate", "sample_fmt", "extradata",
    )
    return tuple(stream.get(k) for k in keys)


def analyze_first_packets(ffprobe: str, path: Path) -> tuple[bool | None, float | None, float | None]:
    video_key = None
    video_pts = None
    audio_pts = None

    for selector, label in (("v:0", "video"), ("a:0", "audio")):
        args = [
            "-v", "error",
            "-select_streams", selector,
            "-read_intervals", "%+0.15",
            "-show_packets",
            "-show_entries", "packet=pts_time,dts_time,flags",
            "-of", "json",
            "-i", str(path),
        ]
        result = run_capture(ffprobe, args, timeout=60)
        if result.returncode != 0:
            continue
        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError:
            continue
        packets = data.get("packets") or []
        if not packets:
            continue
        first = packets[0]
        pts_raw = first.get("pts_time")
        try:
            pts = float(pts_raw) if pts_raw not in (None, "N/A") else None
        except ValueError:
            pts = None
        if label == "video":
            video_key = "K" in (first.get("flags") or "")
            video_pts = pts
        else:
            audio_pts = pts

    return video_key, video_pts, audio_pts


def analyze_video_timestamps(ffprobe: str, path: Path) -> tuple[float | None, int]:
    args = [
        "-v", "error",
        "-select_streams", "v:0",
        "-show_packets",
        "-show_entries", "packet=pts_time",
        "-of", "csv=p=0",
        "-i", str(path),
    ]
    result = run_capture(ffprobe, args, timeout=600)
    if result.returncode != 0:
        return None, 0
    pts_values: list[float] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            pts_values.append(float(line))
        except ValueError:
            pass
    if len(pts_values) < 2:
        return None, 0
    max_gap = 0.0
    backwards = 0
    previous = pts_values[0]
    for current in pts_values[1:]:
        delta = current - previous
        if delta < -0.000001:
            backwards += 1
        elif delta > max_gap:
            max_gap = delta
        previous = current
    return max_gap, backwards


def analyze_one(ffprobe: str, path: Path) -> MediaInfo:
    data = probe_json(ffprobe, path)
    streams = data.get("streams") or []
    fmt = data.get("format") or {}
    duration = float(fmt.get("duration") or 0.0)

    video = [s for s in streams if s.get("codec_type") == "video"]
    audio = [s for s in streams if s.get("codec_type") == "audio"]
    subs = [s for s in streams if s.get("codec_type") == "subtitle"]
    data_streams = [s for s in streams if s.get("codec_type") == "data"]
    other = [s for s in streams if s.get("codec_type") not in {"video", "audio", "subtitle", "data"}]

    first_key, first_vpts, first_apts = analyze_first_packets(ffprobe, path)
    return MediaInfo(
        path=path,
        duration=duration,
        streams=streams,
        video_streams=video,
        audio_streams=audio,
        subtitle_streams=subs,
        data_streams=data_streams,
        other_streams=other,
        first_video_keyframe=first_key,
        first_video_pts=first_vpts,
        first_audio_pts=first_apts,
        max_video_gap=None,
        backwards_video_pts=0,
    )


def print_media(info: MediaInfo, index: int) -> None:
    v = info.video_streams[0] if info.video_streams else {}
    a = info.audio_streams[0] if info.audio_streams else {}
    print(f"\n[{index}] {info.path.name}")
    print(f"    Duree       : {fnum(info.duration, 3)} s")
    print(
        "    Video       : {0} | {1}x{2} | {3} | {4}".format(
            v.get("codec_name", "N/A"), v.get("width", "?"), v.get("height", "?"),
            v.get("pix_fmt", "N/A"), v.get("avg_frame_rate", "N/A")
        )
    )
    print(
        "    Audio       : {0} | {1} Hz | {2} ch | {3}".format(
            a.get("codec_name", "N/A"), a.get("sample_rate", "N/A"),
            a.get("channels", "N/A"), a.get("channel_layout", "N/A")
        )
    )
    print(
        "    Structure   : video={0} | audio={1} | subtitle={2} | data={3} | autres={4}".format(
            len(info.video_streams), len(info.audio_streams), len(info.subtitle_streams),
            len(info.data_streams), len(info.other_streams)
        )
    )
    key = "OUI" if info.first_video_keyframe else ("NON" if info.first_video_keyframe is False else "N/A")
    print(f"    1er packet  : keyframe={key} | PTS={fnum(info.first_video_pts, 3)}")


def strict_copy_compatibility(infos: list[MediaInfo]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if not infos:
        return False, ["aucun fichier"]

    base = infos[0]
    if len(base.video_streams) != 1 or len(base.audio_streams) != 1 or len(base.subtitle_streams) != 0 or len(base.data_streams) != 0 or len(base.other_streams) != 0:
        reasons.append("la structure de reference n'est pas exactement 1 video + 1 audio")

    for i, info in enumerate(infos[1:], start=2):
        if len(info.video_streams) != 1 or len(info.audio_streams) != 1 or len(info.subtitle_streams) != 0 or len(info.data_streams) != 0 or len(info.other_streams) != 0:
            reasons.append(f"video {i}: structure de flux differente")
            continue
        if stream_key(base.video_streams[0]) != stream_key(info.video_streams[0]):
            reasons.append(f"video {i}: parametres video non strictement identiques")
        if stream_key(base.audio_streams[0]) != stream_key(info.audio_streams[0]):
            reasons.append(f"video {i}: parametres audio non strictement identiques")

    for info in infos:
        if info.first_video_keyframe is not True:
            reasons.append(f"{info.path.name}: le premier packet video n'est pas une image-cle")
        if info.first_video_pts is not None and abs(info.first_video_pts) > 0.050:
            reasons.append(f"{info.path.name}: PTS video initial = {info.first_video_pts:.3f} s")

    return len(reasons) == 0, reasons


def concat_escape(path: Path) -> str:
    # concat demuxer uses single-quoted paths. Escape embedded single quotes.
    s = path.resolve().as_posix()
    return s.replace("'", "'\\''")


def make_concat_list(paths: list[Path]) -> Path:
    fd, name = tempfile.mkstemp(prefix="ffconcat_", suffix=".txt")
    os.close(fd)
    p = Path(name)
    p.write_text("\n".join(f"file '{concat_escape(x)}'" for x in paths) + "\n", encoding="utf-8", newline="\n")
    return p


def duration_text(seconds: float) -> str:
    seconds = max(0.0, seconds)
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds - h * 3600 - m * 60
    if h:
        return f"{h:02d}:{m:02d}:{s:05.2f}"
    return f"{m:02d}:{s:05.2f}"


def render_bar(percent: float, width: int = BAR_WIDTH) -> str:
    p = max(0.0, min(100.0, percent))
    filled = int(round(width * p / 100.0))
    return "[" + "#" * filled + "." * (width - filled) + "]"


def run_ffmpeg_progress(ffmpeg: str, args: list[str], total_duration: float, title: str) -> tuple[int, str]:
    cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-progress", "pipe:1", "-nostats", *args]
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        creationflags=creationflags,
    )
    assert process.stdout is not None
    assert process.stderr is not None

    current_time = 0.0
    speed = "N/A"
    started = time.monotonic()
    last_draw = 0.0
    error_text = ""

    # Thread only drains stderr so an unexpected FFmpeg diagnostic cannot block the process.
    def drain_stderr() -> str:
        return process.stderr.read()

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        stderr_future = pool.submit(drain_stderr)
        for raw in process.stdout:
            line = raw.strip()
            if not line or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key == "out_time_ms":
                try:
                    current_time = max(0.0, float(value) / 1_000_000.0)
                except ValueError:
                    pass
            elif key == "speed":
                speed = value
            elif key == "progress" and value == "end":
                current_time = total_duration

            now = time.monotonic()
            if now - last_draw >= 0.10 or key == "progress":
                pct = 100.0 * current_time / total_duration if total_duration > 0 else 0.0
                elapsed = max(0.001, now - started)
                rate = current_time / elapsed if current_time > 0 else 0.0
                eta = (total_duration - current_time) / rate if rate > 0 else float("inf")
                eta_text = duration_text(eta) if math.isfinite(eta) else "--:--"
                line_out = (
                    f"\r{title:<24} {render_bar(pct)} {pct:6.2f}%  "
                    f"{duration_text(current_time)} / {duration_text(total_duration)}  "
                    f"{speed:>8}  ETA {eta_text}"
                )
                sys.stdout.write(line_out)
                sys.stdout.flush()
                last_draw = now

        return_code = process.wait()
        error_text = stderr_future.result()

    sys.stdout.write("\r" + " " * 140 + "\r")
    sys.stdout.flush()
    return return_code, error_text.strip()


def validate_with_ffmpeg(ffmpeg: str, output: Path) -> tuple[bool, str]:
    result = run_capture(ffmpeg, ["-v", "error", "-i", str(output), "-map", "0:v:0", "-map", "0:a:0", "-f", "null", "NUL"], timeout=900)
    return result.returncode == 0, result.stderr.strip()


def validate_output(ffprobe: str, ffmpeg: str, output: Path, expected_duration: float, target_fps: float, check_packets: bool = True) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    try:
        data = probe_json(ffprobe, output, timeout=300)
    except Exception as exc:
        return False, [str(exc)]

    streams = data.get("streams") or []
    videos = [s for s in streams if s.get("codec_type") == "video"]
    audios = [s for s in streams if s.get("codec_type") == "audio"]
    duration = float((data.get("format") or {}).get("duration") or 0.0)

    if len(videos) != 1:
        reasons.append(f"sortie: nombre de videos = {len(videos)}")
    if len(audios) != 1:
        reasons.append(f"sortie: nombre de pistes audio = {len(audios)}")
    if abs(duration - expected_duration) > max(0.35, 0.01 * expected_duration):
        reasons.append(f"duree finale {duration:.3f} s != attendu {expected_duration:.3f} s")

    if videos:
        v = videos[0]
        fps = rational_to_float(v.get("avg_frame_rate"))
        if fps is None or abs(fps - target_fps) > 0.05:
            reasons.append(f"FPS moyen final = {v.get('avg_frame_rate')}, attendu ~{target_fps:.3f}")
        if v.get("width") is None or v.get("height") is None:
            reasons.append("resolution video finale absente")

    if check_packets and videos:
        max_gap, backwards = analyze_video_timestamps(ffprobe, output)
        if backwards > 0:
            reasons.append(f"timestamps video: {backwards} retours arriere")
        if max_gap is not None and max_gap > 0.50:
            reasons.append(f"timestamps video: gros trou de {max_gap:.3f} s")

    ok, err = validate_with_ffmpeg(ffmpeg, output)
    if not ok:
        reasons.append("test de decodage final non reussi")
        if err:
            reasons.append(err[-1200:])

    return len(reasons) == 0, reasons


def choose_target(values: list[float], default: float) -> float:
    vals = [x for x in values if x and math.isfinite(x)]
    if not vals:
        return default
    if max(vals) - min(vals) < 0.01:
        return vals[0]
    # For mixed FPS, preserve the highest source cadence rather than arbitrarily
    # dropping frames from the highest-FPS source.
    return max(vals)


def fps_expr(value: float) -> str:
    # Prefer simple integer/NTSC fractions when possible.
    if abs(value - round(value)) < 1e-6:
        return str(int(round(value)))
    if abs(value - 30000 / 1001) < 1e-4:
        return "30000/1001"
    if abs(value - 24000 / 1001) < 1e-4:
        return "24000/1001"
    if abs(value - 60000 / 1001) < 1e-4:
        return "60000/1001"
    return f"{value:.6f}"


def build_filter_graph(infos: list[MediaInfo], target_w: int, target_h: int, target_fps: float, target_sr: int, target_layout: str) -> str:
    parts: list[str] = []
    audio_labels: list[str] = []
    video_labels: list[str] = []
    fps = fps_expr(target_fps)

    for i, info in enumerate(infos):
        duration = max(0.001, info.duration)
        vlabel = f"v{i}"
        alabel = f"a{i}"
        vf = (
            f"[{i}:v:0]fps=fps={fps},"
            f"scale={target_w}:{target_h}:force_original_aspect_ratio=decrease,"
            f"pad={target_w}:{target_h}:(ow-iw)/2:(oh-ih)/2:color=black,"
            f"format=yuv420p,setsar=1,setpts=PTS-STARTPTS[{vlabel}]"
        )
        parts.append(vf)
        video_labels.append(f"[{vlabel}]")

        if info.audio_streams:
            af = (
                f"[{i}:a:0]aresample={target_sr}:async=1:first_pts=0,"
                f"aformat=sample_fmts=fltp:sample_rates={target_sr}:channel_layouts={target_layout},"
                f"apad,atrim=duration={duration:.6f},asetpts=PTS-STARTPTS[{alabel}]"
            )
        else:
            af = (
                f"anullsrc=r={target_sr}:cl={target_layout},"
                f"atrim=duration={duration:.6f},asetpts=PTS-STARTPTS[{alabel}]"
            )
        parts.append(af)
        audio_labels.append(f"[{alabel}]")

    concat_inputs = "".join(v + a for v, a in zip(video_labels, audio_labels))
    parts.append(f"{concat_inputs}concat=n={len(infos)}:v=1:a=1[outv][outa]")
    return ";".join(parts)


def qsv_available(ffmpeg: str) -> tuple[bool, str]:
    """Verify that h264_qsv is not only listed but actually usable."""
    args = [
        "-hide_banner", "-loglevel", "error",
        "-f", "lavfi",
        "-i", "color=c=black:s=128x128:r=30",
        "-frames:v", "1",
        "-vf", "format=nv12",
        "-c:v", "h264_qsv",
        "-f", "null", "-",
    ]
    result = run_capture(ffmpeg, args, timeout=30)
    if result.returncode == 0:
        return True, "h264_qsv operationnel"
    detail = (result.stderr or result.stdout).strip()
    return False, detail[-2000:] if detail else "FFmpeg a refuse le test h264_qsv."


def main() -> None:
    print("=" * 68)
    print(" FUSION VIDEO INTELLIGENTE - FFmpeg / H264_QSV")
    print("=" * 68)

    ffmpeg = find_executable("ffmpeg.exe") or find_executable("ffmpeg")
    ffprobe = find_executable("ffprobe.exe") or find_executable("ffprobe")
    if not ffmpeg or not ffprobe:
        die("ffmpeg.exe et/ou ffprobe.exe introuvable. Verifie C:\\ffmpeg\\bin ou le PATH.")
    print(f"FFmpeg : {ffmpeg}")
    print(f"FFprobe: {ffprobe}")

    qsv_ok, qsv_detail = qsv_available(ffmpeg)
    if not qsv_ok:
        print("\nDiagnostic QSV:")
        print(qsv_detail)
        die("h264_qsv est present mais le test reel d'encodage QSV a echoue. Ce n'est pas un probleme lie a PowerShell.")
    print("H.264 QSV : test reel d'encodage reussi.")

    root = Tk()
    root.withdraw()
    try:
        root.attributes("-topmost", True)
    except Exception:
        pass

    initial_dir = str(DEFAULT_FOLDER if DEFAULT_FOLDER.exists() else Path.home())
    print("\nOuverture de l'explorateur...")
    paths = filedialog.askopenfilenames(
        title="Selectionne les videos a fusionner",
        initialdir=initial_dir,
        filetypes=[
            ("Videos", "*.mp4 *.mkv *.mov *.m4v *.avi *.ts *.m2ts *.mts *.webm"),
            ("Tous les fichiers", "*.*"),
        ],
    )
    root.destroy()

    if len(paths) < 2:
        die("Selectionne au moins 2 videos.")
    selected = [Path(p) for p in paths]

    print("\nFichiers selectionnes (ordre recu de Windows):")
    for i, path in enumerate(selected, 1):
        print(f"  {i:02d}. {path}")

    print("\nAnalyse ffprobe des fichiers (en parallele)...")
    max_workers = min(len(selected), max(2, min(8, (os.cpu_count() or 4))))
    infos: list[MediaInfo | None] = [None] * len(selected)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        future_map = {pool.submit(analyze_one, ffprobe, path): i for i, path in enumerate(selected)}
        for future in concurrent.futures.as_completed(future_map):
            i = future_map[future]
            try:
                infos[i] = future.result()
            except Exception as exc:
                die(f"analyse impossible pour {selected[i].name}: {exc}")
            print(f"  Analyse {i + 1}/{len(selected)} : OK - {selected[i].name}")

    infos = [x for x in infos if x is not None]
    print("\n========== ANALYSE ==========")
    for i, info in enumerate(infos, 1):
        print_media(info, i)

    total_duration = sum(x.duration for x in infos)
    first_v = infos[0].video_streams[0]
    fps_values = [rational_to_float(x.video_streams[0].avg_frame_rate if False else x.video_streams[0].get("avg_frame_rate")) or 0 for x in infos]
    target_fps = choose_target(fps_values, 30.0)
    widths = [int(x.video_streams[0].get("width") or 0) for x in infos]
    heights = [int(x.video_streams[0].get("height") or 0) for x in infos]
    target_w = max(widths) if widths else 1920
    target_h = max(heights) if heights else 1080
    target_w += target_w % 2
    target_h += target_h % 2

    audio_infos = [x.audio_streams[0] for x in infos if x.audio_streams]
    if audio_infos:
        target_sr = int(audio_infos[0].get("sample_rate") or 44100)
        target_channels = int(audio_infos[0].get("channels") or 2)
        target_layout = audio_infos[0].get("channel_layout") or ("stereo" if target_channels == 2 else "stereo")
    else:
        target_sr = 48000
        target_layout = "stereo"

    compatible, reasons = strict_copy_compatibility(infos)

    output_dir = infos[0].path.parent
    stamp = time.strftime("%Y%m%d_%H%M%S")
    output = output_dir / f"Fusion_Intelligente_{stamp}.mp4"
    temp_copy = output_dir / f".__fusion_copy_{stamp}_{os.getpid()}.mp4"
    concat_list: Path | None = None

    try:
        if compatible:
            print("\n============================================================")
            print(" ETAPE 1: TENTATIVE SANS REENCODAGE (LOSSLESS)")
            print("============================================================")
            print("Les flux sont compatibles. Test des timestamps des sources...")
            for info in infos:
                gap, backwards = analyze_video_timestamps(ffprobe, info.path)
                info.max_video_gap = gap
                info.backwards_video_pts = backwards
                print(
                    f"  {info.path.name}: max gap PTS={fnum(gap, 3)} s | retours arriere={backwards}"
                )
                if backwards > 0 or (gap is not None and gap > 0.50):
                    compatible = False
                    reasons.append(
                        f"{info.path.name}: timestamps anormaux (gap={fnum(gap,3)} s, retours={backwards})"
                    )

        if compatible:
            concat_list = make_concat_list([x.path for x in infos])
            print("Flux et timestamps valides. Tentative concat demuxer + -c copy...")
            args = [
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_list),
                "-map", "0:v:0",
                "-map", "0:a:0",
                "-c", "copy",
                "-copytb", "1",
                "-movflags", "+faststart",
                "-avoid_negative_ts", "disabled",
                str(temp_copy),
            ]
            code, err = run_ffmpeg_progress(ffmpeg, args, total_duration, "Copie lossless")
            if code == 0 and temp_copy.exists() and temp_copy.stat().st_size > 0:
                valid, validation_reasons = validate_output(
                    ffprobe, ffmpeg, temp_copy, total_duration,
                    rational_to_float(first_v.get("avg_frame_rate")) or target_fps,
                    check_packets=True,
                )
                if valid:
                    temp_copy.replace(output)
                    print("\nCOPIE LOSSLESS VALIDEE.")
                    print(f"Sortie: {output}")
                    try:
                        os.startfile(output_dir)  # type: ignore[attr-defined]
                    except Exception:
                        pass
                    return
                print("\nLa copie lossless a ete creee, mais la validation l'a REFUSEE:")
                for r in validation_reasons:
                    print(f"  - {r}")
            else:
                print("\nLa tentative lossless a echoue.")
                if err:
                    print(err[-2000:])
        else:
            print("\n============================================================")
            print(" ETAPE 1: COPIE LOSSLESS NON RETENUE")
            print("============================================================")
            for r in reasons:
                print(f"  - {r}")

        print("\n============================================================")
        print(" ETAPE 2: REENCODAGE ROBUSTE AVEC INTEL QSV")
        print("============================================================")
        print(
            f"Sortie: {target_w}x{target_h} / {fps_expr(target_fps)} FPS CFR / "
            f"H.264 h264_qsv / QSV veryfast / global_quality 18 / AAC {target_sr} Hz"
        )
        print("Une seule pipeline FFmpeg est utilisee: c'est plus efficace que plusieurs encodages concurrents pour un seul fichier final.")

        filter_graph = build_filter_graph(infos, target_w, target_h, target_fps, target_sr, target_layout)
        input_args: list[str] = []
        for path in selected:
            input_args += ["-i", str(path)]

        args = [
            "-y",
            "-filter_threads", "0",
            "-filter_complex_threads", "0",
            "-filter_complex", filter_graph,
            *input_args,
            "-map", "[outv]",
            "-map", "[outa]",
            "-c:v", "h264_qsv",
            "-preset", "veryfast",
            "-global_quality", "18",
            "-look_ahead", "0",
            "-async_depth", "4",
            "-profile:v", "high",
            "-r", fps_expr(target_fps),
            "-fps_mode", "cfr",
            "-c:a", "aac",
            "-b:a", "192k",
            "-ar", str(target_sr),
            "-movflags", "+faststart",
            "-metadata", "comment=Fusion Video Intelligente - H264 QSV",
            str(output),
        ]

        code, err = run_ffmpeg_progress(ffmpeg, args, total_duration, "Reencodage QSV")
        if code != 0 or not output.exists() or output.stat().st_size == 0:
            print("\nLe reencodage QSV a echoue.")
            if err:
                print(err[-4000:])
            raise SystemExit(2)

        # Validation of QSV output: no timestamp deep scan is necessary because the
        # fps filter + cfr output path deliberately creates a regular timeline.
        valid, validation_reasons = validate_output(
            ffprobe, ffmpeg, output, total_duration, target_fps, check_packets=False
        )
        if not valid:
            print("\nATTENTION: le fichier a ete cree mais la validation finale a detecte un probleme:")
            for r in validation_reasons:
                print(f"  - {r}")
            raise SystemExit(3)

        print("\n============================================================")
        print(" FUSION TERMINEE ET VALIDEE")
        print("============================================================")
        print(f"Sortie : {output}")
        print(f"Duree  : {duration_text(total_duration)}")
        print(f"FPS    : {fps_expr(target_fps)} CFR")
        print("Codec  : H.264 h264_qsv")
        try:
            os.startfile(output_dir)  # type: ignore[attr-defined]
        except Exception:
            pass

    finally:
        if concat_list and concat_list.exists():
            try:
                concat_list.unlink()
            except OSError:
                pass
        for tmp in (temp_copy,):
            if tmp.exists() and tmp != output:
                try:
                    tmp.unlink()
                except OSError:
                    pass


if __name__ == "__main__":
    main()
