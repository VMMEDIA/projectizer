<div align="center">

# Projectizer

### L'alternativa open-source e leggera a Plaud

Trasforma qualsiasi registrazione di una riunione in riassunti strutturati e azionabili — pronti per PRD, Notion o la wiki del team.

Niente hardware. Niente abbonamenti. Solo le tue registrazioni e una API key.

[![License: MIT](https://img.shields.io/badge/License-MIT-6c5ce7.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-a29bfe.svg)](https://python.org)
[![OpenAI Whisper](https://img.shields.io/badge/OpenAI-Whisper-00b894.svg)](https://platform.openai.com/docs/guides/speech-to-text)

<br>

**$0,36/ora** vs $79/anno — fai tu i calcoli.

<sub><a href="README.md">🇬🇧 English</a> · 🇮🇹 Italiano</sub>

</div>

---

## Perché Projectizer?

Plaud e dispositivi simili ti vincolano a hardware proprietario, abbonamenti cloud ed ecosistemi chiusi.

Projectizer adotta un approccio diverso:

| | Plaud | Projectizer |
|---|---|---|
| **Costo** | $79/anno + $159 di hardware | ~$0,36/ora, paghi quanto usi |
| **Hardware richiesto** | Dispositivo proprietario | Nessuno — usa qualsiasi telefono, laptop o registratore |
| **Privacy dei dati** | Il loro cloud, le loro regole | Tutto in locale, la tua API key, i tuoi dati |
| **Formato output** | Bloccato nella loro app | Plain text + Markdown — incolla dove vuoi |
| **Personalizzazione** | Nessuna | Open source — modifica prompt, modelli, tutto |
| **Accesso offline** | Richiede la loro app | Web UI locale, funziona su qualsiasi browser |
| **Qualità del riassunto** | Modello AI fisso | Scegli qualsiasi modello OpenAI (GPT-4o, 4o-mini, o1...) |
| **Etichette parlanti** | Limitate | Diarization integrata (pyannote.audio) |

<br>

> **Registra con quello che hai già.** Trascina i file in Projectizer. Ottieni il riassunto. Fatto.

---

## Cosa ottieni

**Trascrizione** — Powered by Whisper, supporta 50+ lingue con auto-detection. Carica un file o dieci — Projectizer concatena, comprime e suddivide tutto automaticamente.

**Diarization (opzionale)** — Identifica chi ha detto cosa con `pyannote.audio`. Ottieni trascrizioni etichettate `Persona 1: ...`, `Persona 2: ...` invece di un blocco unico. *Richiede un token HuggingFace gratuito — vedi [step 4 sotto](#4-setup-della-diarization-opzionale).*

**Riassunti strutturati** — Non un muro di testo. Ogni riassunto è organizzato in punti chiave, decisioni prese, action item con responsabili e prossimi passi. Pensato per i product team.

**Costi trasparenti** — Vedi esattamente quanto spenderai *prima* di trascrivere. Niente sorprese in bolletta.

**Progresso in tempo reale** — Guarda la trascrizione mentre avviene. Compressione, chunking, trascrizione, riassunto — ogni passo ti viene streamato in diretta.

---

## Avvio rapido

```bash
git clone https://github.com/VMMEDIA/projectizer.git
cd projectizer
bash run.sh
```

Lo script sincronizza i file sorgente dentro `Projectizer.app/Contents/Resources/`, crea un virtual environment **dentro il bundle**, installa le dipendenze e avvia il server su **http://localhost:8899**.

Incolla la tua OpenAI API key nel pannello **Settings** e sei pronto.

> **Il primo avvio richiede 3–5 minuti** — PyTorch e pyannote.audio sono dipendenze pesanti (~1 GB su disco). Gli avvii successivi partono in pochi secondi.

### Due modi per avviarlo

| Modalità | Come | Risultato |
|----------|------|-----------|
| **Browser** (sviluppo) | `bash run.sh` | Apre `localhost:8899` nel browser di default. Sincronizza in automatico le modifiche al codice dentro il bundle .app. |
| **Finestra nativa** (macOS) | `open Projectizer.app` | Vera app desktop con icona e finestra propria. Il bundle è **self-contained** — puoi metterlo in `/Applications/`, `~/Desktop/`, ovunque. Vedi [Avviare come app nativa](#avviare-come-app-nativa). |

Le due modalità condividono lo stesso backend; usa quella che preferisci.

---

## Installazione

### 1. Prerequisiti di sistema

Ti servono tre cose installate sulla tua macchina prima di clonare il repo:

#### Python 3.10 o superiore

Verifica la versione:

```bash
python3 --version
```

| Piattaforma | Installazione |
|-------------|---------------|
| **macOS** | `brew install python@3.11` |
| **Ubuntu / Debian** | `sudo apt install python3.11 python3.11-venv` |
| **Fedora / RHEL** | `sudo dnf install python3.11` |
| **Windows** | [installer python.org](https://www.python.org/downloads/) — spunta "Add to PATH" |

> Projectizer è testato su 3.10, 3.11 e 3.12. Evita la 3.13 per ora: i wheel di pyannote.audio sono in ritardo sulle release Python più recenti.

#### FFmpeg

Usato per compressione audio, concatenazione e analisi metadata.

| Piattaforma | Installazione |
|-------------|---------------|
| **macOS** | `brew install ffmpeg` |
| **Ubuntu / Debian** | `sudo apt install ffmpeg` |
| **Fedora / RHEL** | `sudo dnf install ffmpeg` |
| **Windows** | `winget install Gyan.FFmpeg` oppure `choco install ffmpeg` |

Verifica con `ffmpeg -version` e `ffprobe -version` — entrambi devono essere nel `PATH`.

#### Una OpenAI API key

Generala su [platform.openai.com/api-keys](https://platform.openai.com/api-keys). La incollerai nel pannello Settings di Projectizer dopo il primo avvio — non serve nessuna variabile d'ambiente.

---

### 2. Installa Projectizer

#### Opzione A — Automatica (consigliata)

```bash
git clone https://github.com/VMMEDIA/projectizer.git
cd projectizer
bash run.sh
```

`run.sh` gestisce creazione del venv, `pip install` e avvio del server.

> Se modifichi `requirements.txt` in seguito, cancella `.venv/` e rilancia `bash run.sh` — lo script installa le dipendenze solo al primo avvio.

#### Opzione B — Manuale

Se vuoi capire ogni passaggio o usare un ambiente Python esistente, il venv viene creato **dentro il bundle .app** così la `.app` rimane portabile. Anche i sorgenti vanno copiati lì:

```bash
git clone https://github.com/VMMEDIA/projectizer.git
cd projectizer

APP_RES=Projectizer.app/Contents/Resources
cp app.py launcher.py requirements.txt config.example.json "$APP_RES/"
cp -R static "$APP_RES/static"

python3 -m venv "$APP_RES/.venv"
"$APP_RES/.venv/bin/python" -m pip install --upgrade pip
"$APP_RES/.venv/bin/python" -m pip install -r "$APP_RES/requirements.txt"

# Modalità browser
( cd "$APP_RES" && "$APP_RES/.venv/bin/python" app.py )

# Modalità finestra nativa
( cd /tmp && "$APP_RES/.venv/bin/python" "$APP_RES/launcher.py" )
```

Una volta fatto, `Projectizer.app` funziona anche da Finder. `bash run.sh` fa tutto questo per te.

---

### 3. Note su PyTorch

`requirements.txt` installa `torch>=2.2.0` da PyPI, che fornisce la build giusta per la maggior parte delle macchine:

- **macOS (Apple Silicon)** — CPU + accelerazione MPS out of the box.
- **macOS (Intel)** — solo CPU.
- **Linux / Windows (CPU)** — build CPU.

Se hai una **GPU NVIDIA su Linux/Windows** e vuoi usare CUDA per la diarization, installa torch dall'index ufficiale *prima* di lanciare `pip install -r requirements.txt`:

```bash
# Esempio: CUDA 12.1
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt
```

Scegli l'URL corretto da [pytorch.org/get-started/locally](https://pytorch.org/get-started/locally/).

> La diarization senza GPU funziona bene per riunioni brevi (sotto i ~30 minuti). Per registrazioni più lunghe su CPU, aspettati 0,5–1× il realtime.

---

### 4. Setup della diarization (opzionale)

#### Cos'è la diarization e ti serve davvero?

La diarization è il processo di capire **chi parla quando** in un file audio. Senza, Projectizer ti dà una trascrizione unica:

```
Okay quindi la deadline è venerdì. Secondo me dovremmo spostarla la prossima settimana.
Perché? Perché il design non è pronto. Va bene, facciamo martedì.
```

Con la diarization attiva, ottieni etichette per ogni parlante:

```
Persona 1: Okay quindi la deadline è venerdì.
Persona 2: Secondo me dovremmo spostarla la prossima settimana.
Persona 1: Perché?
Persona 2: Perché il design non è pronto.
Persona 1: Va bene, facciamo martedì.
```

È opzionale. **Salta questa sezione del tutto se** le tue riunioni sono perlopiù monologhi, ti basta un riassunto ad alto livello, o non vuoi creare un account HuggingFace. Trascrizione, action item e riassunto funzionano tutti senza.

#### Perché HuggingFace?

La diarization gira **in locale** sulla tua macchina usando [`pyannote.audio`](https://github.com/pyannote/pyannote-audio) — una libreria gratuita e open-source. La libreria sta su PyPI (`pip` la installa come parte di `requirements.txt`), ma i *pesi del modello addestrato* di cui ha bisogno sono ospitati su HuggingFace con licenza "gated":

- Il modello è gratis, ma gli autori richiedono che tu accetti i loro termini d'uso prima di scaricarlo.
- L'accettazione avviene sul sito HuggingFace (un click).
- Un access token personale dimostra al server di download che hai accettato.

È tutto qui il motivo dello step HuggingFace. **Nessun dato esce dalla tua macchina** — la diarization è 100% locale. Il token serve solo per il download iniziale del modello (~500 MB, cachati per sempre).

#### Step di setup

1. **Crea un account HuggingFace** su [huggingface.co/join](https://huggingface.co/join). Gratis, 30 secondi.
2. **Accetta i termini** di entrambi i modelli gated — apri ciascun link mentre sei loggato e clicca "Agree and access repository":
   - [`pyannote/speaker-diarization-3.1`](https://huggingface.co/pyannote/speaker-diarization-3.1)
   - [`pyannote/segmentation-3.0`](https://huggingface.co/pyannote/segmentation-3.0)
3. **Genera un access token** su [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) — il tipo `Read` è sufficiente. Copia la stringa `hf_...`.
4. **Incollalo nel pannello Settings di Projectizer** sotto "HuggingFace token" (oppure imposta `hf_token` in `config.json`).

La prima volta che la diarization gira, pyannote scarica ~500 MB di pesi del modello — cachati per tutti gli avvii successivi.

---

## Configurazione

La configurazione vive in `Projectizer.app/Contents/Resources/config.json` — **dentro il bundle .app**, così viaggia con la `.app` quando la sposti. Il file viene creato automaticamente la prima volta che salvi le impostazioni dalla UI. Puoi anche partire dal template:

```bash
cp config.example.json Projectizer.app/Contents/Resources/config.json
```

```json
{
  "openai_api_key": "sk-...",
  "summary_model": "gpt-4o-mini",
  "hf_token": "hf_..."
}
```

| Parametro | Default | Descrizione |
|-----------|---------|-------------|
| `openai_api_key` | — | La tua OpenAI API key (obbligatoria) |
| `summary_model` | `gpt-4o-mini` | Modello per il riassunto — usa `gpt-4o` per qualità maggiore |
| `hf_token` | — | Token HuggingFace (obbligatorio solo per la diarization) |
| `PORT` (env var) | `8899` | Porta del server — `PORT=9000 bash run.sh` |

---

## Avviare come app nativa

Vuoi che Projectizer sembri una vera applicazione desktop — con la sua icona, la sua finestra, niente tab del browser? Usa uno dei launcher per piattaforma qui sotto. Avviano il server in background e aprono la UI in una finestra nativa via [pywebview](https://pywebview.flowrl.com/).

> Il flusso `bash run.sh` continua a funzionare e sincronizza in automatico le tue modifiche al codice dentro il bundle, così la `.app` riflette sempre l'ultimo stato.

### macOS — .app self-contained

`Projectizer.app` è **self-contained**: dopo il primo `bash run.sh`, tutti i file sorgente, il virtual environment e le dipendenze vivono dentro `Projectizer.app/Contents/Resources/`. Puoi spostare la `.app` ovunque — `/Applications/`, `~/Desktop/`, un disco esterno — e continua a funzionare.

**Setup iniziale**:

```bash
git clone https://github.com/VMMEDIA/projectizer.git
cd projectizer
bash run.sh
```

Lo script crea il venv dentro il bundle (`Projectizer.app/Contents/Resources/.venv/`, ~1 GB) e avvia il server in modalità browser. Una volta partito puoi:

- Fermare con `Ctrl+C` e fare **doppio click su `Projectizer.app`** per la finestra nativa
- Oppure continuare a usare il browser su `localhost:8899`

**Sposta la `.app` dove vuoi**:

```bash
# Copia o sposta — funzionano entrambi
cp -R Projectizer.app /Applications/
# oppure
mv Projectizer.app ~/Desktop/Projectizer.app
```

Doppio click dalla nuova posizione. Niente da riconfigurare.

> **Nota architetturale**: i sorgenti vivono nel project root per essere modificati. `bash run.sh` li sincronizza dentro `Projectizer.app/Contents/Resources/` ad ogni avvio, così le modifiche si propagano. La `.app` legge dai file dentro il bundle a runtime — è per questo che funziona dopo essere stata spostata.

> **Sandbox macOS / TCC**: quando la `.app` si trova in `~/Documents/`, `~/Desktop/`, `~/Downloads/` o iCloud Drive, macOS le permette comunque di leggere il proprio bundle. I file del progetto fuori dal bundle non sono accessibili da una `.app` lanciata da Finder in quelle cartelle — ma siccome tutto ciò che serve a runtime è *dentro* il bundle, non è un problema.

> **Icona personalizzata**: metti un file `icon.icns` in `Projectizer.app/Contents/Resources/` per sostituire quella di default. macOS potrebbe richiedere `killall Dock` per aggiornare la cache.

### Windows

```cmd
git clone https://github.com/VMMEDIA/projectizer.git
cd projectizer
Projectizer.bat
```

Il primo avvio installa il venv, gli avvii successivi vanno dritti alla finestra nativa. Click destro su `Projectizer.bat` → **Crea collegamento**, poi trascina il collegamento sul Desktop o aggiungilo al menu Start.

Il launcher usa `pythonw.exe`, quindi non resta nessuna finestra di console aperta. Se qualcosa non va e vuoi vedere i log, modifica `Projectizer.bat` e sostituisci `pythonw.exe` con `python.exe`.

### Linux

pywebview su Linux richiede pacchetti GTK + WebKit2GTK a livello di sistema. Su Debian/Ubuntu:

```bash
sudo apt install python3-gi gir1.2-webkit2-4.1 libwebkit2gtk-4.1-0
```

Poi crea il venv (una volta sola) e installa la voce di menu:

```bash
bash run.sh                                  # ctrl-C appena parte, serve solo a creare .venv
source .venv/bin/activate
pip install 'pywebview[gtk]'                 # binding del backend GTK
deactivate

bash scripts/install-launcher-linux.sh
```

Lo script di install scrive `~/.local/share/applications/projectizer.desktop` con il path assoluto del tuo clone. Projectizer dovrebbe ora comparire nel menu applicazioni.

---

## Troubleshooting

**`ffmpeg: command not found`**
FFmpeg non è nel `PATH`. Su macOS verifica che `brew --prefix`/bin sia nel PATH; su Windows riavvia il terminale dopo l'installazione o aggiungi manualmente la cartella `bin/` di FFmpeg al PATH.

**`ERROR: Could not find a version that satisfies the requirement torch`**
Probabilmente sei su Python 3.13 o un'architettura non supportata. Installa Python 3.11 e ricrea `.venv`.

**`Impossibile caricare il modello di diarization` / pyannote restituisce `None`**
O il token HuggingFace è sbagliato, o non hai accettato i termini di *entrambi* i modelli `pyannote/speaker-diarization-3.1` e `pyannote/segmentation-3.0`. Ricontrolla lo step 4 del setup diarization.

**La diarization è lenta / la ventola gira a manetta**
Atteso su CPU. Disattiva la diarization dalla UI per trascrizioni veloci, oppure installa un torch con CUDA su Linux/Windows.

**`OSError: [Errno 48] Address already in use`**
La porta 8899 è occupata. Avvia con una porta diversa: `PORT=9000 bash run.sh`.

**`run.sh` non rileva i nuovi requirements**
`run.sh` rileva le modifiche tramite hash SHA-1 di `requirements.txt` (memorizzato in `.venv/.installed`). Se il refresh fallisce, forza la reinstallazione cancellando il venv dentro il bundle: `rm -rf Projectizer.app/Contents/Resources/.venv && bash run.sh`.

**Apple Silicon: warning su MPS fallback**
Innocui. Alcune operazioni di pyannote non sono implementate su Metal — vengono eseguite automaticamente in fallback su CPU (la variabile `PYTORCH_ENABLE_MPS_FALLBACK=1` è impostata in `app.py`).

**`Projectizer.app` non apre una finestra**
Lancia prima `bash run.sh` — fa il bootstrap del bundle (sincronizza i sorgenti, crea il venv dentro `Contents/Resources/`). Dopo, il doppio click funziona. Se la `.app` parte e si chiude in silenzio, controlla `/tmp/projectizer-launcher.log` per la diagnosi.

**Le modifiche ad `app.py` o `static/index.html` non si vedono dentro `Projectizer.app`**
La `.app` legge da `Contents/Resources/`. Lancia `bash run.sh` per ri-sincronizzare le modifiche dentro il bundle, poi riapri la `.app`. (`run.sh` lo fa ad ogni avvio.)

---

## Come funziona

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Upload     │────▶│  Compress    │────▶│  Transcribe  │────▶│  Summarize   │
│  file audio  │     │  Opus 32kbps │     │  Whisper API │     │  GPT-4o-mini │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                                                                       │
       ┌───────────────────────────────────────────────────────────────┘
       ▼
  Output strutturato:
  • Punti chiave discussi
  • Decisioni prese
  • Action item (con responsabili)
  • Prossimi passi
```

**Upload multi-file** ordinati automaticamente per metadata di creazione — perfetto per registrazioni interrotte o setup multi-device.

**Compressione smart** converte qualsiasi formato audio in Opus 32kbps mono prima di mandarlo all'API, riducendo la dimensione dell'80–90% senza perdita di qualità sul parlato.

**Chunking** suddivide i file che superano il limite di 25 MB di Whisper, trascrive ogni segmento e ricompone i risultati senza soluzione di continuità.

**Diarization (opzionale)** gira in locale via pyannote.audio, poi allinea i turni di parola con i segmenti Whisper per produrre una trascrizione etichettata.

---

## Costi

| Cosa | Costo |
|------|-------|
| Trascrizione (Whisper) | $0,006 / minuto |
| Riassunto (GPT-4o-mini) | ~$0,0003 / riunione |
| Diarization (locale) | $0 — gira sulla tua CPU/GPU |
| **Riunione di 1 ora, totale** | **~$0,36** |

Per dare un riferimento: 200 ore di riunioni l'anno costano circa **$72** — meno di un anno di abbonamento Plaud, senza acquisto hardware.

---

## Tech Stack

Volutamente minimale. Niente build step, niente bundler, niente overhead di framework.

- **Backend**: FastAPI + Uvicorn
- **Frontend**: HTML/CSS/JS vanilla — file singolo, zero dipendenze
- **Audio**: FFmpeg per compressione e chunking
- **AI**: OpenAI Whisper (trascrizione) + GPT (riassunto) + pyannote.audio (diarization)

---

## Contribuire

Le PR sono benvenute. Il codebase è volutamente piccolo (~500 righe di Python, ~600 di frontend) — facile da capire, facile da estendere.

```
projectizer/                          (project root — modifica i sorgenti qui)
├── app.py                            # Backend — tutta la logica API
├── launcher.py                       # Entry point per finestra nativa (pywebview)
├── static/
│   └── index.html                    # Frontend — single-page app
├── run.sh                            # Launcher browser + sync del bundle
├── Projectizer.bat                   # Launcher Windows → finestra nativa
├── scripts/
│   ├── projectizer-launcher.sh       # invocato dal .desktop Linux
│   └── install-launcher-linux.sh     # crea la voce .desktop
├── requirements.txt                  # Dipendenze Python
├── config.example.json               # Template di configurazione
└── Projectizer.app/                  # Bundle macOS self-contained
    └── Contents/
        ├── Info.plist
        ├── MacOS/projectizer         # Script bash di lancio
        └── Resources/                # ← qui vivono i file a runtime
            ├── app.py                # Sincronizzato dal project root
            ├── launcher.py           #   "
            ├── static/               #   "
            ├── requirements.txt      #   "
            ├── config.json           # API key salvate dall'utente
            └── .venv/                # Venv Python (~1 GB, creato al primo run)
```

**Source of truth**: modifica i file nel project root. `bash run.sh` mantiene `Projectizer.app/Contents/Resources/` sincronizzato — `app.py`, `launcher.py`, `static/`, `requirements.txt`, `config.example.json` vengono copiati nel bundle ad ogni avvio. Il `.venv` e `config.json` (dati utente) vivono solo dentro il bundle.

---

<div align="center">

**Smetti di pagare abbonamenti per la trascrizione delle riunioni.**

**Inizia a possedere il tuo workflow.**

<br>

Licenza MIT

</div>
