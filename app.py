# Karpathy-style note:
# The app is a thin orchestration layer: HTTP receives intent, analyzers produce
# typed facts, engines generate deterministic audio, and Socket.IO streams bytes.
# Keep business philosophy visible, but keep computation modular and testable.

from __future__ import annotations

import base64
import functools
import json
import math
import uuid
from http import HTTPStatus
from pathlib import Path
from typing import Any, Callable

import numpy as np
from flask import Flask, jsonify, render_template_string, request, send_file
from flask_socketio import SocketIO, emit
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

try:
    import dashscope
    from dashscope import Generation
except Exception:  # pragma: no cover - lets the app boot without AI dependency.
    dashscope = None
    Generation = None

from acoustic_engine import AcousticEngine, AudioRender
from config import (
    ALLOWED_AUDIO_EXTENSIONS,
    API_KEY,
    BRAINWAVE_TARGETS_HZ,
    DASHSCOPE_BASE_HTTP_API_URL,
    DASHSCOPE_MAX_TOKENS,
    DASHSCOPE_MODEL,
    DASHSCOPE_TEMPERATURE,
    DASHSCOPE_TEST_MODEL,
    MAX_DURATION_SECONDS,
    MAX_UPLOAD_BYTES,
    OUTPUT_DIR,
    PHI,
    RELATIVE_COST_UNITS_PER_1K_TOKENS,
    SAMPLE_RATE,
    SECRET_KEY,
    SOCKETIO_ASYNC_MODE,
    STREAM_CHUNK_SECONDS,
    TOKEN_CHARS_APPROX,
    UPLOAD_DIR,
)
from fractal_visualizer import GoldenSpiralVisualizer
from quantum_analyzer import VoiceAnalyzer


def _resolve_dashscope_api_error() -> type[BaseException]:
    """
    Resolve the requested dashscope.api_error hook across SDK versions.

    Some DashScope SDK releases expose different exception paths. We first look
    for dashscope.api_error, as requested, then fall back to Exception so the
    call is always guarded.
    """
    candidate = getattr(dashscope, "api_error", None) if dashscope is not None else None
    if isinstance(candidate, type) and issubclass(candidate, BaseException):
        return candidate
    return Exception


DASHSCOPE_API_ERROR = _resolve_dashscope_api_error()

app = Flask(__name__)
app.config.update(SECRET_KEY=SECRET_KEY, MAX_CONTENT_LENGTH=MAX_UPLOAD_BYTES)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode=SOCKETIO_ASYNC_MODE)

voice_analyzer = VoiceAnalyzer(sample_rate=SAMPLE_RATE)
acoustic_engine = AcousticEngine(sample_rate=SAMPLE_RATE)
visualizer = GoldenSpiralVisualizer()

JOURNEY_REGISTRY: dict[str, Path] = {}

HOME_TEMPLATE = """
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <title>PhiVox</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 820px; margin: 40px auto; line-height: 1.5; }
    code { background: #f4f4f4; padding: 2px 5px; border-radius: 4px; }
    .card { border: 1px solid #ddd; border-radius: 16px; padding: 20px; margin: 16px 0; }
  </style>
</head>
<body>
  <h1>PhiVox</h1>
  <p>Calibración vocal, síntesis Phi, beats binaurales y visualización fractal en tiempo real.</p>
  <div class="card">
    <h2>Endpoints</h2>
    <p><code>POST /calibrate</code>: multipart con campo <code>audio</code>.</p>
    <p><code>POST /generate_journey</code>: JSON con <code>human_base_freq</code>, <code>duration</code>, <code>desired_state</code>.</p>
    <p><code>GET /download/&lt;journey_id&gt;</code>: descarga WAV generado.</p>
    <p>Socket.IO: emitir <code>start_stream</code> con <code>{"journey_id": "..."}</code>.</p>
  </div>
</body>
</html>
"""


@app.get("/")
def home() -> str:
    return render_template_string(HOME_TEMPLATE)


@app.post("/calibrate")
def calibrate() -> tuple[Any, int]:
    """
    Receive a human voice recording and convert it into a vibrational profile.

    Product philosophy expressed in operational terms: the human contributes a
    unique measurable signal through voice; PhiVox uses that value to generate
    sonic and visual resources around it.
    """
    audio = request.files.get("audio")
    if audio is None:
        return jsonify(error="Missing multipart file field: audio"), HTTPStatus.BAD_REQUEST

    try:
        audio_path = _save_audio_upload(audio)
        profile = voice_analyzer.calibrate_voice(audio_path)
    except Exception as exc:
        return jsonify(error=str(exc)), HTTPStatus.BAD_REQUEST

    return jsonify(
        message="El humano aporta con su voz el valor que la vida usa para generar recursos.",
        profile=profile,
    ), HTTPStatus.OK


@app.post("/generate_journey")
def generate_journey() -> tuple[Any, int]:
    """Generate a Phi-structured sonic journey from a calibrated root frequency."""
    payload = request.get_json(silent=True) or {}
    try:
        human_base_freq = float(payload.get("human_base_freq"))
        duration = min(float(payload.get("duration", 60.0)), MAX_DURATION_SECONDS)
        desired_state = str(payload.get("desired_state", "theta")).lower().strip()
        beat_freq = _resolve_beat_frequency(desired_state)

        sequence = acoustic_engine.generate_golden_sequence(human_base_freq, length=8)
        om_layer = acoustic_engine.synthesize_om(human_base_freq, duration)
        binaural_layer = acoustic_engine.create_binaural_beats(
            base_freq=sequence[0],
            beat_freq=beat_freq,
            duration=duration,
        )
        render = acoustic_engine.mix_layers([om_layer, binaural_layer], weights=[0.72, 0.28])

        journey_id = uuid.uuid4().hex
        output_path = OUTPUT_DIR / f"journey_{journey_id}.wav"
        acoustic_engine.write_wav(render, output_path)
        JOURNEY_REGISTRY[journey_id] = output_path

        description = payload.get("description") or _default_ai_description(
            human_base_freq=human_base_freq,
            beat_freq=beat_freq,
            desired_state=desired_state,
        )
        ai_music_prompt = _generate_ai_music(description)

    except Exception as exc:
        return jsonify(error=str(exc)), HTTPStatus.BAD_REQUEST

    return jsonify(
        journey_id=journey_id,
        wav_path=str(output_path),
        download_url=f"/download/{journey_id}",
        human_base_freq=human_base_freq,
        desired_state=desired_state,
        beat_freq=beat_freq,
        golden_sequence_hz=[round(float(freq), 4) for freq in sequence],
        ai_music_prompt=ai_music_prompt,
        disclaimer="Audio experimental para bienestar y arte; no sustituye diagnóstico ni tratamiento médico.",
    ), HTTPStatus.OK


@app.get("/download/<journey_id>")
def download_journey(journey_id: str):
    path = JOURNEY_REGISTRY.get(journey_id) or OUTPUT_DIR / f"journey_{journey_id}.wav"
    if not path.exists():
        return jsonify(error="Journey not found"), HTTPStatus.NOT_FOUND
    return send_file(path, mimetype="audio/wav", as_attachment=True, download_name=path.name)


@socketio.on("start_stream")
def start_stream(data: dict | None = None) -> None:
    """
    Stream PCM16 audio chunks and synchronized Phi spiral frames.

    The frontend can decode audio_chunk_base64 as little-endian int16 stereo PCM.
    For production, replace this with WebAudio buffering or HLS/WebRTC.
    """
    data = data or {}
    journey_id = str(data.get("journey_id", ""))
    path = JOURNEY_REGISTRY.get(journey_id) or OUTPUT_DIR / f"journey_{journey_id}.wav"
    if not journey_id or not path.exists():
        emit("stream_error", {"error": "Valid journey_id is required"})
        return

    from scipy.io import wavfile

    sr, pcm = wavfile.read(path)
    pcm = _ensure_pcm16_stereo(pcm)
    chunk_size = max(1, int(sr * STREAM_CHUNK_SECONDS))
    total_chunks = int(math.ceil(len(pcm) / chunk_size))

    emit("stream_started", {"journey_id": journey_id, "sample_rate": sr, "total_chunks": total_chunks})
    for index in range(total_chunks):
        start = index * chunk_size
        end = min(start + chunk_size, len(pcm))
        chunk = pcm[start:end]
        phase = (index / max(total_chunks, 1)) * 2.0 * math.pi * PHI
        emit(
            "audio_chunk",
            {
                "journey_id": journey_id,
                "index": index,
                "total_chunks": total_chunks,
                "sample_rate": sr,
                "channels": 2,
                "dtype": "int16_le",
                "audio_chunk_base64": base64.b64encode(chunk.astype("<i2").tobytes()).decode("ascii"),
                "fractal_png_base64": visualizer.generate_frame_base64(phase=phase),
            },
        )
        socketio.sleep(STREAM_CHUNK_SECONDS)
    emit("stream_finished", {"journey_id": journey_id})


def estimate_tokens(text: str) -> int:
    """Fast, local token estimate used before paid calls."""
    return max(1, math.ceil(len(text) / TOKEN_CHARS_APPROX))


def cost_guard(func: Callable[..., str]) -> Callable[..., str]:
    """Warn estimated model cost before each DashScope call and log usage after."""

    @functools.wraps(func)
    def wrapper(description: str, model: str = DASHSCOPE_MODEL, *args: Any, **kwargs: Any) -> str:
        input_tokens = estimate_tokens(description)
        max_output = int(kwargs.get("max_tokens", DASHSCOPE_MAX_TOKENS))
        unit_rate = RELATIVE_COST_UNITS_PER_1K_TOKENS.get(model, 1.0)
        estimated_units = ((input_tokens + max_output) / 1_000.0) * unit_rate
        print(
            "[PhiVox cost guard] "
            f"model={model} estimated_tokens≈{input_tokens + max_output} "
            f"relative_cost_units≈{estimated_units:.4f}. "
            f"For tests, {DASHSCOPE_TEST_MODEL} is documented here as ~10x cheaper than qwen-plus."
        )
        result = func(description, model=model, *args, **kwargs)
        print("[PhiVox cost guard] DashScope call completed.")
        return result

    return wrapper


@cost_guard
def _generate_ai_music(
    description: str,
    model: str = DASHSCOPE_MODEL,
    max_tokens: int = DASHSCOPE_MAX_TOKENS,
) -> str:
    """Use Qwen to turn a vibrational fingerprint into a soundscape brief."""
    if dashscope is None or Generation is None:
        return "DashScope SDK is not installed. Install with: pip install dashscope"
    if not API_KEY:
        return "DASHSCOPE_API_KEY is not configured; AI soundscape generation skipped."

    dashscope.api_key = API_KEY
    if DASHSCOPE_BASE_HTTP_API_URL:
        dashscope.base_http_api_url = DASHSCOPE_BASE_HTTP_API_URL

    messages = [
        {
            "role": "system",
            "content": (
                "Eres un diseñador sonoro. Devuelve un paisaje sonoro breve, técnico y evocador. "
                "No hagas promesas médicas; describe textura, frecuencia, capas y movimiento."
            ),
        },
        {"role": "user", "content": description},
    ]

    try:
        response = Generation.call(
            model=model,
            messages=messages,
            result_format="message",
            max_tokens=max_tokens,
            temperature=DASHSCOPE_TEMPERATURE,
        )
        if response.status_code == HTTPStatus.OK:
            usage = getattr(response, "usage", None)
            if usage:
                print(f"[PhiVox token usage] {json.dumps(usage, ensure_ascii=False, default=str)}")
            return response.output.choices[0].message.content
        return f"DashScope error {response.status_code}: {getattr(response, 'code', '')} {getattr(response, 'message', '')}"
    except DASHSCOPE_API_ERROR as exc:
        return f"DashScope API error captured via dashscope.api_error-compatible handler: {exc}"
    except Exception as exc:
        return f"Unexpected DashScope error: {exc}"


def _save_audio_upload(audio: FileStorage) -> Path:
    filename = secure_filename(audio.filename or "voice.wav")
    suffix = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if suffix not in ALLOWED_AUDIO_EXTENSIONS:
        raise ValueError(f"Unsupported audio extension: {suffix or 'none'}")
    path = UPLOAD_DIR / f"{uuid.uuid4().hex}_{filename}"
    audio.save(path)
    return path


def _resolve_beat_frequency(desired_state: str) -> float:
    if desired_state in BRAINWAVE_TARGETS_HZ:
        return float(BRAINWAVE_TARGETS_HZ[desired_state])
    try:
        value = float(desired_state)
        if value <= 0:
            raise ValueError
        return value
    except ValueError as exc:
        options = ", ".join(sorted(BRAINWAVE_TARGETS_HZ))
        raise ValueError(f"desired_state must be one of [{options}] or a positive beat frequency") from exc


def _default_ai_description(human_base_freq: float, beat_freq: float, desired_state: str) -> str:
    return (
        f"Un drone profundo que resuena en {human_base_freq:.2f} Hz, "
        f"con beat binaural de {beat_freq:.2f} Hz para un estado artístico {desired_state}, "
        "textura de viento solar, armónicos de cuarzo y respiración Phi en capas lentas."
    )


def _ensure_pcm16_stereo(pcm: np.ndarray) -> np.ndarray:
    data = np.asarray(pcm)
    if data.ndim == 1:
        data = np.column_stack((data, data))
    if data.dtype != np.int16:
        if np.issubdtype(data.dtype, np.floating):
            data = np.clip(data, -1.0, 1.0) * np.iinfo(np.int16).max
        data = data.astype(np.int16)
    return data


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
