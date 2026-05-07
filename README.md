# PhiVox

**PhiVox** es una experiencia bioacústica generativa que transforma una voz humana en un viaje sonoro y visual basado en proporción áurea, beats binaurales, geometría simbólica e intención.

> Voz → frecuencia raíz → secuencia Phi → estado sonoro → geometría → viaje audiovisual.

PhiVox está diseñado como un laboratorio creativo entre arte, tecnología, escucha profunda, visualización generativa y biodiversidad simbólica. No es una herramienta médica ni pretende diagnosticar, tratar o curar condiciones de salud.

---

## Estado del proyecto

**Versión actual:** `v0.2.2`

PhiVox ya cuenta con una interfaz web funcional para:

- grabar o cargar una voz;
- calibrar una frecuencia raíz aproximada;
- elegir estado sonoro: `delta`, `theta`, `schumann`, `alpha`, `beta`;
- elegir geometría: espiral Phi, Flor de la Vida, mandala concéntrico, Fermat, Arquímedes o campo toroidal;
- generar un archivo WAV experimental;
- reproducir y descargar el viaje sonoro;
- visualizar una geometría viva mediante Socket.IO.

---

## Visión

PhiVox busca construir un **lenguaje audiovisual de intención**.

La voz humana aporta una señal única. El sistema toma esa señal como semilla y la expande mediante proporción áurea, síntesis sonora, beats binaurales y geometría generativa. La intención puede venir de una persona, de una comunidad, de un territorio o de la biodiversidad que se desea representar.

La pregunta central del proyecto es:

> ¿Cómo puede una voz convertirse en una experiencia sonora y visual que comunique intención, armonía y relación con la vida?

---

## Qué hace PhiVox

PhiVox ejecuta una cadena de transformación:

```text
voz humana
  → análisis de frecuencia base
  → secuencia Phi
  → capa OM / armónicos
  → beat binaural según estado
  → perfil geométrico simbólico
  → archivo WAV
  → visualización viva
```

El resultado es un viaje audiovisual experimental que puede usarse como pieza artística, prototipo de instalación, demo de bioacústica creativa, herramienta educativa o base para experiencias de escucha inmersiva.

---

## Lenguaje geométrico

PhiVox v0.2 introduce un motor de geometría simbólica. Cada estado puede activar una forma distinta:

| Estado | Beat aproximado | Geometría sugerida | Capas | Significado |
|---|---:|---|---:|---|
| `delta` | 2 Hz | Mandala concéntrico | 5 | reposo profundo, centro protegido |
| `theta` | 6 Hz | Espiral Phi | 8 | imaginación, memoria, expansión orgánica |
| `schumann` | 7.83 Hz | Flor de la Vida | 13 | cuerpo, paisaje, biodiversidad |
| `alpha` | 10 Hz | Espiral de Fermat | 21 | claridad suave, distribución vegetal |
| `beta` | 18 Hz | Espiral de Arquímedes | 13 | atención activa, ritmo ordenado |

Geometrías disponibles:

```text
phi_spiral
archimedean_spiral
fermat_spiral
concentric_mandala
flower_of_life
torus_field
```

---

## Arquitectura

```text
phivox/
├── app.py                  # Servidor Flask + API + Socket.IO
├── config.py               # Configuración general y constantes
├── acoustic_engine.py      # Síntesis Phi, OM, binaural y WAV
├── quantum_analyzer.py     # Calibración vocal experimental
├── geometry_engine.py      # Lenguaje geométrico de intención
├── fractal_visualizer.py   # Render visual de geometrías vivas
├── templates/
│   └── index.html          # Interfaz web
├── data/                   # Archivos generados en ejecución
└── README.md
```

---

## Requisitos

Probado en Debian con Python 3.11.

Dependencias del sistema:

```bash
sudo apt update
sudo apt install -y \
  git unzip curl \
  python3 python3-pip python3-venv \
  portaudio19-dev libsndfile1-dev ffmpeg libasound2-dev
```

Dependencias principales de Python:

- Flask
- Flask-SocketIO
- NumPy
- SciPy
- Librosa
- Matplotlib
- DashScope opcional
- pydub / sounddevice según flujo de audio

---

## Instalación desde cero

```bash
git clone https://github.com/oscuridadinfinita/phivox.git
cd phivox

python3 -m venv ~/phivox-env
source ~/phivox-env/bin/activate

pip install --upgrade pip
pip install \
  "numpy==1.26.4" \
  "scipy==1.11.4" \
  "matplotlib==3.8.4" \
  "llvmlite==0.42.0" \
  "numba==0.59.1" \
  "scikit-learn==1.4.2" \
  "librosa==0.10.2.post1" \
  dashscope \
  sounddevice \
  flask \
  flask-socketio \
  pydub
```

Si el repositorio remoto todavía se llama `phyvox`, clonar temporalmente así:

```bash
git clone https://github.com/oscuridadinfinita/phyvox.git phivox
cd phivox
```

---

## Variables de entorno

DashScope es opcional. PhiVox puede generar audio local sin clave de API.

Para activar la capa de IA narrativa:

```bash
export DASHSCOPE_API_KEY="TU_API_KEY"
export DASHSCOPE_MODEL="qwen-turbo"
```

Para pruebas se recomienda `qwen-turbo`. Para exploraciones más elaboradas se puede usar otro modelo compatible configurado en `config.py`.

Nunca subas claves reales al repositorio. Usa `.env` local o variables de entorno.

---

## Ejecutar PhiVox

```bash
cd ~/phivox
source ~/phivox-env/bin/activate
export DASHSCOPE_MODEL="qwen-turbo"
python app.py
```

Abrir en el navegador:

```text
http://127.0.0.1:5000
```

Desde otro dispositivo en la misma red local:

```text
http://TU_IP_LOCAL:5000
```

Ejemplo observado en desarrollo:

```text
http://192.168.100.165:5000
```

---

## Uso desde la interfaz web

1. Abrir `http://127.0.0.1:5000`.
2. Grabar voz o subir un archivo de audio.
3. Calibrar la frecuencia raíz.
4. Elegir estado sonoro.
5. Elegir geometría o dejar que PhiVox la resuelva.
6. Escribir intención, por ejemplo: `calma`, `expansión`, `biodiversidad`, `regeneración`.
7. Generar viaje.
8. Reproducir, descargar o iniciar visualización viva.

---

## API HTTP

### `POST /calibrate`

Recibe un archivo de audio por multipart form con el campo `audio`.

```bash
curl -X POST http://127.0.0.1:5000/calibrate \
  -F "audio=@test_audio/voz_prueba.wav"
```

Respuesta esperada: perfil experimental con frecuencia base, duración, confianza aproximada y otros datos de análisis.

---

### `POST /generate_journey`

Genera un viaje sonoro WAV.

```bash
curl -X POST http://127.0.0.1:5000/generate_journey \
  -H "Content-Type: application/json" \
  -d '{
    "human_base_freq": 194.4,
    "duration": 30,
    "desired_state": "schumann",
    "intention": "biodiversidad",
    "source": "voice",
    "geometry": "flower_of_life"
  }'
```

Respuesta ejemplo:

```json
{
  "journey_id": "...",
  "download_url": "/download/...",
  "human_base_freq": 194.4,
  "desired_state": "schumann",
  "beat_freq": 7.83,
  "geometry_profile": {
    "geometry": "flower_of_life",
    "layers": 13,
    "source": "voice",
    "intention": "biodiversidad",
    "desired_state": "schumann",
    "meaning": "campo terrestre: interconexión entre cuerpo, paisaje y biodiversidad"
  }
}
```

---

### `GET /download/<journey_id>`

Descarga el WAV generado.

```bash
curl -L -o viaje_phivox.wav \
  http://127.0.0.1:5000/download/TU_JOURNEY_ID
```

---

## Socket.IO

Evento principal:

```text
start_stream
```

Payload:

```json
{
  "journey_id": "TU_JOURNEY_ID"
}
```

El servidor emite cuadros visuales y fragmentos sincronizados para la visualización viva.

---

## Seguridad y uso responsable

PhiVox es una herramienta experimental de arte, bienestar creativo y exploración sonora.

No debe usarse como sustituto de:

- diagnóstico médico;
- tratamiento psicológico o psiquiátrico;
- terapia clínica;
- consejo profesional de salud.

Los beats binaurales y las experiencias de audio inmersivo pueden no ser adecuados para todas las personas. Usar volumen moderado y detener la experiencia si causa incomodidad.

---

## Buenas prácticas de Git

No subir archivos generados:

```text
data/
*.wav
*.mp3
*.flac
*.ogg
*.webm
*.aac
.env
```

Antes de hacer commit:

```bash
python -m py_compile \
  config.py \
  acoustic_engine.py \
  quantum_analyzer.py \
  geometry_engine.py \
  fractal_visualizer.py \
  app.py

git status
```

Crear una versión estable:

```bash
git tag -a v0.2.2 -m "PhiVox v0.2.2: experiencia web completa con voz, geometría, audio y visualización"
git push origin v0.2.2
```

---

## Roadmap

### v0.3 — Identidad de experiencia

- favicon y logo;
- presets de intención: calma, expansión, biodiversidad, regeneración, memoria;
- mejor narrativa visual para cada geometría;
- pantalla final de resultado compartible;
- limpieza visual del panel técnico.

### v0.4 — Biodiversidad sonora

- importar sonidos de agua, viento, aves, insectos o paisaje local;
- mapear biodiversidad a geometrías específicas;
- crear perfiles por territorio o comunidad.

### v0.5 — Instalación inmersiva

- proyección visual;
- audio espacial;
- sensores externos;
- integración con ESP32 u otros dispositivos físicos.

---

## Filosofía técnica

PhiVox intenta mantener dos principios:

1. **La experiencia debe sentirse poética.**
2. **La implementación debe ser inspeccionable.**

Por eso la lógica está separada en motores pequeños: análisis vocal, síntesis acústica, geometría, visualización y servidor web.

La magia no debe ocultar las reglas. La belleza debe poder explicarse, modificarse y compartirse.

---

## Licencia

Licencia por definir.

Antes de usar PhiVox con fines comerciales, comunitarios o institucionales, definir una licencia explícita para código, audios generados, visuales y marca.

---

## Autoría

Proyecto desarrollado como exploración de bioacústica generativa, geometría simbólica, voz humana y relación con la biodiversidad.

**Nombre del proyecto:** PhiVox  
**Concepto central:** transformar voz e intención en experiencia audiovisual generativa.
