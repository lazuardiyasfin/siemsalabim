# siemsalabim - Simple SIEM

Sistem Security Information and Event Management (SIEM) sederhana yang mengumpulkan log dari server target, memproses dan menganalisis secara real-time, lalu menampilkan alert di dashboard web.

> https://siemsalabim.duckdns.org/

## Tim

| NRP        | Nama                           | Role  |
| ---------- | ------------------------------ | ----- |
| 5025241001 | Kenzie Maheswara               |       |
| 5025241020 | Raynald Ramadhani Fachriansyah |       |
| 5025241139 | Mohammed Lazuardi Yasfin       |       |   
| 5025241152 | Bintang Ilham Pabeta           |       |


## Deskripsi Project

Pada tugas final project NCC ini, kami diminta untuk membangun sistem SIEM mini dengan fitur:

1. Mengumpulkan log dari sistem (server target)
2. Melakukan parsing log untuk mengekstrak informasi terstruktur
3. Menampilkan monitoring pada dashboard secara real-time
4. Komunikasi real-time via WebSocket
5. Containerized dengan Docker
6. CI/CD via Jenkins
7. Lolos SonarQube quality gate
8. Dapat diakses publik melalui domain

Fitur bonus yang diimplementasikan: rule engine dengan konfigurasi YAML, severity levels, GeoIP enrichment, real-time EPS monitoring, dan persistent storage alert + event via SQLite.

## Tech Stack

| Kategori           | Teknologi                                         |
| ------------------ | ------------------------------------------------- |
| Bahasa             | Python 3.12+                                      |
| Package Manager    | [uv](https://docs.astral.sh/uv/) (workspace mode) |
| Engine Framework   | FastAPI + Uvicorn                                 |
| Exporter           | Python + watchdog + websockets                    |
| Dashboard Frontend | Vite + Vanilla JS + Chart.js + Leaflet            |
| Dashboard Backend  | Python + FastAPI                                  |
| Database           | SQLite (engine) + In-memory state (dashboard)     |
| Container          | Docker + Docker Compose                           |
| CI/CD              | Jenkins (self-hosted) + SonarQube Community       |
| Linting & Format   | Ruff                                              |
| Testing            | pytest + pytest-cov + Vitest                      |
| Registry           | GitHub Container Registry (GHCR)                  |
| Reverse Proxy      | Nginx + Let's Encrypt SSL                         |
| Domain             | siemsalabim.duckdns.org                           |
| Private Network    | Tailscale                                         |

## Architecture

Sistem ini mengadopsi arsitektur microservices yang terbagi menjadi tiga komponen utama:

```
┌─────────────────────────────────────────────────────────────────┐
│                     CLIENT (Browser)                            │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP/HTTPS
                             ▼
        ┌───────────────────────────────────────────────┐
        │  DASHBOARD (React/Vite + FastAPI)             │
        │  - Visualisasi logs dan alerts                │
        │  - Authentication (JWT)                       │
        │  - WebSocket untuk real-time updates          │
        └────────────────────┬──────────────────────────┘
                             │ WebSocket
                             ▼
    ┌────────────────────────────────────────────────────────┐
    │  ENGINE (FastAPI Core)                                 │
    │  - Log ingestion (HTTP + WebSocket)                    │
    │  - Parsing & Decoding (Regex)                          │
    │  - Rule Matching & Evaluation                          │
    │  - Broadcasting alerts                                 │
    └──────────────────────┬─────────────────────────────────┘
          ▲                │
          │ WebSocket      │ WebSocket broadcast
          │                │
    ┌─────┴────────────────┴───────────┐
    │  EXPORTER (Watchdog Agent)       │
    │  - File monitoring (Linux/MacOS) │
    │  - Real-time log tailing         │
    │  - Queue management              │
    │  - Auto-reconnect (exponential)  │
    └──────────────────────────────────┘
          │
          ▼
    [Log Sources: /var/log/*, custom paths]
```


### Alur Data End-to-End

```
Target VPS: Log file berubah (/var/log/auth.log, /var/log/nginx/access.log)
  → watchdog detect perubahan file
    → reader baca baris baru dari offset terakhir
      → bungkus sebagai RawLog JSON
        → kirim ke engine via WebSocket (wss://.../engine/ws/ingest)
          → engine predecoder detect format (syslog / nginx)
            → decoder extract field terstruktur (user, IP, action, status, dll)
              → rule engine evaluasi: match rules? frequency threshold?
                → Ya → generate Alert dengan severity level
                  → broadcast Alert + Event ke semua dashboard client
                    → dashboard render chart, tabel, dan map secara real-time
```


## Project Structure

```
siemsalabim/
├─ apps/
│  ├─ dashboard/           # UI + Backend
│  │  ├─ backend/          # FastAPI auth & state
│  │  │  └─ src/
│  │  │     ├─ main.py
│  │  │     ├─ engine_client.py  # Engine integration
│  │  │     └─ security.py       # JWT & auth
│  │  └─ frontend/         # React/Vite SPA
│  │     └─ src/
│  │        ├─ features/   # Feature modules
│  │        ├─ components/ # UI components
│  │        └─ lib/        # Utilities
│  │
│  ├─ engine/              # Core processing engine
│  │  ├─ src/
│  │  │  ├─ main.py
│  │  │  ├─ ingest.py      # WebSocket ingest handler
│  │  │  ├─ parser/        # Log parsing
│  │  │  ├─ rules/         # Rule matching
│  │  │  └─ broadcaster.py # Alert broadcasting
│  │  ├─ decoders/         # YAML decoder configs
│  │  └─ rules/            # YAML rule configs
│  │
│  └─ exporter/            # Log collection agent
│     └─ src/
│        ├─ main.py
│        ├─ watcher.py     # File monitoring
│        ├─ ws_client.py   # WebSocket client
│        └─ pipeline.py    # Main pipeline
│
└─ devops/
   ├─ docker/              # Docker configs
   │  ├─ jenkins-agent/    # Custom Jenkins agent
   │  └─ nginx/            # Reverse proxy
   └─ ansible/             # Deployment automation
```


## CI/CD Tools

- Jenkins: Orkestrator otomatisasi untuk membangun pipeline (Build, Test, Push, Deploy).
    - Jenkins-Agent: Custom agent berbasis Docker sebagai build executor dalam pipeline.
- SonarQube: Static Application Security Testing (SAST) untuk memastikan kualitas kode dan penerapan Quality Gate.
- Docker: Platform containerization untuk standarisasi environment pengembangan hingga production.
- Ansible: Configuration management untuk deployment otomatis (Idempoten).


## Exporter (`apps/exporter/`) 

**Main Features**

- [Mengumpulkan Log dari Sistem](#mengumpulkan-log-dari-sistem)
- [Menerapkan Komunikasi Real-time menggunakan WebSocket](#menerapkan-komunikasi-realtime-menggunakan-websocket)

Exporter menggunakan library watchdog untuk monitoring real-time perubahan file log. Ketika ada modifikasi pada file yang di-watch:

### Modul

| File           | Fungsi                                                                           |
| -------------- | -------------------------------------------------------------------------------- |
| `config.py`    | Konfigurasi dari environment variable via Pydantic Settings                      |
| `models.py`    | Model `RawLog` sesuai kontrak ingestion WebSocket                                |
| `state.py`     | Offset tracking per file + inode rotation detection                              |
| `reader.py`    | Baca baris baru dari offset sampai EOF, handle partial lines dan truncation      |
| `watcher.py`   | File monitoring via watchdog library dengan debounce 0.5 detik                   |
| `ws_client.py` | WebSocket client dengan reconnect (exponential backoff 1-60s), bounded queue 10k |
| `pipeline.py`  | Orchestrator async: watcher → reader → ws_client                                 |
| `main.py`      | Entrypoint: boot config, logging, jalankan pipeline                              |

### Mengumpulkan Log dari Sistem

> Tech: Watchdog library + WebSocket client

Exporter menggunakan library watchdog untuk monitoring real-time perubahan file log. Ketika ada modifikasi pada file yang di-watch:

- FileSystemEventHandler mendeteksi FileModifiedEvent pada path yang dikonfigurasi
- Debounce mechanism (0.5s) mencegah multiple events untuk single write
- Log lines di-enqueue ke async queue untuk di-send ke Engine
- Automatic reconnection dengan exponential backoff jika koneksi terputus

```python
# apps/exporter/src/watcher.py
class LogWatcher:
    - Memantau multiple directories
    - Debounce untuk menghindari duplikasi events
    - Graceful start/stop
```

Use Case: Setup Exporter pada server target yang memiliki logs, misal:

- `/var/log/auth.log` (authentication logs)
- `/var/log/nginx/access.log` (web server logs)
- `/custom/path/application.log` (custom application logs)


#### Fitur Utama

**Offset Persistence** — Exporter menyimpan posisi baca terakhir untuk setiap file ke `state.json`. Saat restart, exporter melanjutkan dari posisi terakhir tanpa membaca ulang atau kehilangan log.

**Inode Rotation Detection** — Saat `logrotate` me-rename file dan membuat file baru, inode berubah. Exporter mendeteksi perubahan inode dan mereset offset ke 0 untuk membaca file baru.

**Reconnect dengan Exponential Backoff** — Jika koneksi ke engine terputus, exporter reconnect otomatis dengan delay 1s, 2s, 4s, 8s, ..., max 60s. Saat engine kembali online, exporter langsung connect tanpa intervensi manual.

**Bounded Queue** — Send queue berkapasitas 10.000 message. Jika engine down dan queue penuh, message terbaru di-drop untuk mencegah out-of-memory.

#### Environment Variables

| Variable               | Contoh                                           | Keterangan                           |
| ---------------------- | ------------------------------------------------ | ------------------------------------ |
| `SIEM_INGEST_URL`      | `wss://siemsalabim.duckdns.org/engine/ws/ingest` | WebSocket URL engine                 |
| `SIEM_INGEST_TOKEN`    | `<secret>`                                       | Bearer token untuk autentikasi       |
| `SIEM_EXPORTER_ID`     | `node-target-prod-01`                            | ID unik exporter                     |
| `SIEM_WATCH_PATHS`     | `/var/log/auth.log,/var/log/nginx/access.log`    | File yang dipantau (comma-separated) |
| `SIEM_STATE_FILE_PATH` | `/var/lib/exporter/state.json`                   | Path untuk simpan offset             |
| `SIEM_LOG_LEVEL`       | `INFO`                                           | Level logging                        |

### Menerapkan Komunikasi Realtime menggunakan WebSocket

> Tech: websockets library (Python) + native WebSocket API (JavaScript)

Bidirectional Communication:
```
Exporter ──ws://engine:8000/ws/ingest──► Engine
   │                                        │
   │◄──── Acknowledgment (optional) ────────┘
   
   
Engine ──ws://localhost:8001/ws/dashboard──► Dashboard
  │                                            │
  └──── Broadcast alerts & logs ───────────────┘
```

#### Kontrak WebSocket (Exporter → Engine)

Setiap baris log dikirim sebagai satu JSON message:

```json
{
  "exporter_id": "node-target-prod-01",
  "host": "siem-target",
  "path": "/var/log/auth.log",
  "line": "2026-05-20T04:03:49.940072+00:00 siem-target sshd[22184]: Invalid user fakeuser from 182.8.65.13 port 40908",
  "received_at": "2026-05-20T04:03:50.123456Z"
}
```


## Engine (`apps/engine`)  

**Main Features**

- [Membuat Parser Log untuk Mengekstrak Informasi Penting](#membuat-parser-log-untuk-mengekstrak-informasi-penting)

**Extra Features**

- [Membuat Custom Rule Engine Berbasis Konfigurasi JSON/YAML](#membuat-custom-rule-engine-berbasis-konfigurasi-jsonyaml)
- [Menambahkan Severity Level pada Alert](#menambahkan-severity-level-pada-alert)
- [Menyimpan Event ke dalam Database](#menyimpan-event-ke-dalam-database)
- [Menambahkan Notifikasi ketika Rule Tertentu Terpenuhi](#menambahkan-fitur-input-path-log-melalui-dashboard)


Engine adalah pusat pemrosesan SIEM. Menerima raw log dari exporter, mem-parse menjadi data terstruktur, mengevaluasi terhadap rules, dan broadcast alert ke dashboard.

#### Modul Engine

| File             | Fungsi                                                                                 |
| ---------------- | -------------------------------------------------------------------------------------- |
| `config.py`      | Konfigurasi engine dari environment variable via Pydantic Settings                     |
| `models.py`      | Model `RawLog`, `Event`, `PreDecodedLog`, `LogFormat`                                  |
| `database.py`    | Inisialisasi SQLite (WAL mode), tabel `events` & `alerts`, `store_events_and_alerts()` |
| `ingest.py`      | WebSocket handler: auth token, parse, evaluate rules, simpan ke DB, broadcast          |
| `broadcaster.py` | Manage koneksi dashboard WebSocket dan broadcast JSON ke semua client                  |
| `main.py`        | Entrypoint FastAPI: lifespan `init_db()`, semua endpoint REST + WebSocket              |

### Membuat Parser Log untuk Mengekstrak Informasi Penting

> Tech: YAML-based decoder config + Python regex

Engine memiliki dua layer parsing:

1. Layer 1: Predecoder
    - Deteksi format log berdasarkan pattern
    - Extract metadata dasar (timestamp, level)
    - Tentukan decoder mana yang akan digunakan

    | Format          | Contoh                                                                                      | Sumber                                 |
    | --------------- | ------------------------------------------------------------------------------------------- | -------------------------------------- |
    | Syslog RFC 5424 | `2026-05-20T04:03:49.940072+00:00 siem-target sshd[22184]: message`                         | `/var/log/auth.log`, `/var/log/syslog` |
    | Nginx Combined  | `185.177.72.16 - - [19/May/2026:21:46:44 +0000] "GET / HTTP/1.1" 200 409 "-" "Mozilla/5.0"` | `/var/log/nginx/access.log`            |


2. Layer 2: Decoder (YAML Config)
    
    Decoder menjalankan regex pattern pada YAML mengekstrak field spesifik seperti:

    - Username, IP address, action, port, protocol
    - Timestamp dan severity level
    - Custom fields sesuai log format

    Contoh decoder SSHD (`apps/engine/decoders/sshd.yaml`):

    ```yaml
    decoders:
    - id: sshd_invalid_user
        program: sshd
        pattern: "Invalid user (?P<user>\\S+) from (?P<src_ip>\\S+) port (?P<src_port>\\d+)"
        fields:
        action: invalid_user
        int_fields: [src_port]
    ```

    Actions yang dideteksi oleh SSHD decoder:

    | Action              | Contoh Log                                                             |
    | ------------------- | ---------------------------------------------------------------------- |
    | `invalid_user`      | `Invalid user fakeuser from 182.8.65.13 port 40908`                    |
    | `accepted`          | `Accepted publickey for root from 182.8.65.13 port 40919 ssh2`         |
    | `failed`            | `Failed password for root from 1.2.3.4 port 22 ssh2`                   |
    | `connection_closed` | `Connection closed by invalid user admin 116.110.14.96 port 44718`     |
    | `disconnected`      | `Disconnected from invalid user user3 94.26.106.201 port 26574`        |
    | `connection_reset`  | `Connection reset by authenticating user root 45.148.10.141 port 8882` |
    | `session_opened`    | `pam_unix(sshd:session): session opened for user root(uid=0)`          |

    Fields yang diekstrak oleh Nginx decoder:

    | Field        | Contoh                          |
    | ------------ | ------------------------------- |
    | `client_ip`  | `185.177.72.16`                 |
    | `method`     | `GET`, `POST`, `HEAD`           |
    | `path`       | `/.git/config`                  |
    | `status`     | `200`, `404`, `400`             |
    | `user_agent` | `curl/8.7.1`, `Shodan-Pull/1.0` |

    Decoder bersifat **hot-reloadable** — tambah file YAML baru ke `decoders/` lalu hit endpoint `POST /decoders/reload`. Tidak perlu restart engine.

### Membuat Custom Rule Engine Berbasis Konfigurasi JSON/YAML 

Rule engine mengevaluasi setiap Event terhadap definisi rule yang didefinisikan di YAML. Mendukung dua tipe rule:

**1. Single-event rules** — Semua kondisi harus match pada satu event. Alert langsung di-generate.

    ```yaml
    - id: ssh_invalid_user
    name: SSH Invalid User Attempt
    severity: medium
    program: sshd
    description: "SSH login attempt with invalid user '{user}' from {src_ip}"
    conditions:
        - field: decoded.action
        value: invalid_user
    ```

**2. Frequency rules** — Kondisi harus match DAN jumlah event dalam time window harus mencapai threshold. Cocok untuk deteksi brute force.

    ```yaml
    - id: ssh_brute_force
    name: SSH Brute Force Detected
    severity: critical
    program: sshd
    description: "Multiple failed SSH attempts from {src_ip}"
    conditions:
        - field: decoded.action
        value: [invalid_user, failed]
    frequency:
        count: 5
        window_seconds: 120
        group_by: decoded.src_ip
    ```

### Menambahkan Severity Level pada Alert

**Severity Levels:**

| Level      | Contoh Rule                              | Aksi                                 |
| ---------- | ---------------------------------------- | ------------------------------------ |
| `low`      | SSH successful login, Shodan scanner     | Informational, log saja              |
| `medium`   | SSH invalid user, failed password        | Perlu dipantau                       |
| `high`     | Path traversal attempt                   | Serangan aktif, perlu ditindak       |
| `critical` | SSH brute force (5 failed dalam 2 menit) | Immediate response, notifikasi admin |

Rule engine juga **hot-reloadable** via `POST /rules/reload`.

### Menyimpan Event ke dalam Database

Engine menyimpan setiap event dan alert yang di-generate ke database SQLite lokal (`data/siem.db`). Database diinisialisasi otomatis saat startup via FastAPI lifespan.

**Tabel:**

| Tabel    | Kolom                                                                                                       | Keterangan                         |
| -------- | ----------------------------------------------------------------------------------------------------------- | ---------------------------------- |
| `events` | `id`, `timestamp`, `program`, `payload` (JSON)                                                              | Semua parsed event yang masuk      |
| `alerts` | `id`, `timestamp`, `rule_id`, `rule_name`, `severity`, `description`, `event_count`, `source_events` (JSON) | Alert yang di-generate rule engine |

**Optimasi:**

- WAL mode (`PRAGMA journal_mode=WAL`) untuk read concurrent tanpa blocking
- Index pada `alerts.severity` dan `alerts.timestamp DESC` untuk query dashboard yang cepat

Setiap kali `ingest_handler` berhasil mem-parse sebuah event, `store_events_and_alerts()` dipanggil secara async dan error-nya tidak memblok alur utama (log error saja).

#### API Endpoints

| Method | Path               | Fungsi                                                           |
| ------ | ------------------ | ---------------------------------------------------------------- |
| `GET`  | `/health`          | Liveness probe                                                   |
| `GET`  | `/stats`           | Jumlah dashboard yang connected                                  |
| `POST` | `/rules/reload`    | Hot-reload YAML rules tanpa restart                              |
| `POST` | `/decoders/reload` | Hot-reload YAML decoders tanpa restart                           |
| `GET`  | `/api/alerts`      | Query historical alerts dari SQLite (param: `limit`, `severity`) |
| `WS`   | `/ws/ingest`       | Terima log dari exporter (auth: Bearer token)                    |
| `WS`   | `/ws/dashboard`    | Broadcast events + alerts ke dashboard backend                   |

### Menambahkan Notifikasi ketika Rule Tertentu Terpenuhi

> wait that's kinda my thing, but wait


## 3. Dashboard (`apps/dashboard/`)
Dashboard adalah web UI untuk monitoring SIEM secara real-time.

**Main Features**

- [Menampilkan Hasil Monitoring dalam Bentuk Dashboard](#menampilkan-hasil-monitoring-dalam-bentuk-dashboard)
- [Memastikan SIEM dapat Diakses Secara Publik (via Domain)](#memastikan-siem-dapat-diakses-secara-publik-via-domain)


**Extra Features**

- [Menambahkan Fitur Input Path Log melalui Dashboard](#menambahkan-fitur-input-path-log-melalui-dashboard)


#### Stack

| Komponen   | Teknologi                                             |
| ---------- | ----------------------------------------------------- |
| Frontend   | Vite + Vanilla JS + Chart.js + Leaflet + Lucide Icons |
| Backend    | Python + FastAPI                                      |
| Komunikasi | WebSocket (`/ws/events`)                              |

#### Fitur

- **Real-time event stream** — Events dan alerts masuk secara real-time via WebSocket, ditampilkan di tabel dan chart
- **Dashboard overview** — Statistics card, event timeline chart, log type distribution chart
- **GeoIP map** — Visualisasi lokasi sumber serangan pada peta menggunakan Leaflet
- **Log management** — Tabel log aktif dari exporter yang terkoneksi
- **Rule management** — Lihat dan kelola rule definitions
- **Authentication** — Login flow dengan JWT (HttpOnly cookie) untuk akses dashboard

#### API Endpoints Dashboard Backend

| Method | Path           | Fungsi                                                                          |
| ------ | -------------- | ------------------------------------------------------------------------------- |
| `POST` | `/login`       | Autentikasi admin, set JWT sebagai HttpOnly cookie                              |
| `GET`  | `/health`      | Liveness probe                                                                  |
| `GET`  | `/stats`       | Jumlah frontend connected + status koneksi ke engine                            |
| `GET`  | `/api/auth/me` | Validasi sesi JWT yang aktif                                                    |
| `GET`  | `/api/alerts`  | Proxy historical alerts dari engine (auth required, param: `limit`, `severity`) |
| `WS`   | `/ws/events`   | Stream real-time events + alerts ke frontend (auth via cookie)                  |

Endpoint `/api/alerts` di dashboard backend adalah **secure proxy** ke engine: ia memverifikasi JWT terlebih dulu, lalu meneruskan request ke `GET /api/alerts` di engine menggunakan `httpx`.

#### Konsumsi WebSocket

Frontend subscribe ke **dashboard backend** (bukan langsung ke engine) dan menerima beberapa tipe message:

```javascript
// Frontend → Dashboard Backend (ws/events)
const wsUrl = API_BASE_URL.replace(/^http/, "ws") + "/ws/events";
const ws = new WebSocket(wsUrl);

ws.onmessage = (event) => {
  const envelope = JSON.parse(event.data);
  const isAlert = envelope.rule_id || envelope.type?.toUpperCase() === "ALERT";

  if (isAlert) {
    // Alert dari rule engine — update chart, tabel, dan map
    handleAlertMetrics(envelope.rule_id ? envelope : envelope.data);
  } else {
    // Pesan sistem dari dashboard backend
    // type: "EPS_UPDATE" → update EPS counter
    // type: "EXPORTER_STATUS" → update jumlah exporter aktif
    handleSystemMetrics(envelope);
  }
};
```

Dashboard backend menjadi perantara: ia subscribe ke engine via `ws://siem-engine:8000/ws/dashboard`, lalu meneruskan events ke semua frontend yang terkoneksi di `/ws/events`.

### Menampilkan Hasil Monitoring dalam Bentuk Dashboard

> Tech: React/Vite frontend + FastAPI backend + WebSocket

Visualisasi Data:

- Real-time log stream dengan filtering
- Event timeline (kapan log terjadi)
- Chart distribusi log types
- Map visualization untuk IP-based events
- Statistics panel (total logs, alerts, severity breakdown)

Fitur Interaksi:

- View recent logs dengan pagination
- Filter by log type, severity, timestamp
- Search functionality
- Export logs to CSV

Authentication:

- Login page dengan username/password
- JWT token untuk session management
- Password hashing dengan bcrypt
- Automatic logout on token expiry


## CI/CD

**Main Features**

- [Menggunakan Containerization dengan Docker](#menggunakan-containerization-dengan-docker)
- [Menerapkan CI/CD menggunakan Jenkins selama Proses Development](#menerapkan-cicd-menggunakan-jenkins-selama-proses-development)
- [Memastikan Project Lolos Standar Kualitas (Quality Gate) SonarQube](#memastikan-project-lolos-standar-kualitas-quality-gate-sonarqube)
- [Memastikan SIEM dapat Diakses Secara Publik (via Domain)](#memastikan-siem-dapat-diakses-secara-publik-via-domain)

### Menerapkan CI/CD menggunakan Jenkins selama Proses Development

> Tech: Jenkins pipeline + custom Docker agent (`Jenkinsfile`)

| Stage                  | Deskripsi                                                     |
| ---------------------- | ------------------------------------------------------------- |
| **Sync**               | `uv sync --frozen --all-packages --all-extras`                |
| **Lint & Format**      | `ruff check` + `ruff format --check`                          |
| **Test Exporter**      | `pytest` dengan coverage XML (change-gated)                   |
| **Test Engine**        | `pytest` dengan coverage XML (change-gated)                   |
| **Test Dashboard**     | `pytest` + `vitest` dengan coverage (change-gated)            |
| **SonarQube Analysis** | Analisis per-app (exporter, engine, dashboard)                |
| **Quality Gate**       | Block pipeline jika gagal (timeout 5 menit)                   |
| **Docker Build**       | `docker compose build` pada PR dan main                       |
| **Docker Push**        | Push ke GHCR dengan tag `v1.0.<BUILD>` + `latest` (main only) |
| **Deploy**             | Ansible playbook ke SIEM VPS (main only)                      |

### Memastikan Project Lolos Standar Kualitas (Quality Gate) SonarQube

> Tech: SonarQube server + Scanner

Coverage Requirements:

- Python: Pytest coverage dengan XML reports
- JavaScript: Vitest coverage dengan LCOV format

Analysis Scope:

```
Exporter Analysis:
  ├─ Sources: apps/exporter/src
  ├─ Tests: apps/exporter/tests
  └─ Coverage: coverage-exporter.xml

Engine Analysis:
  ├─ Sources: apps/engine/src
  ├─ Tests: apps/engine/tests
  └─ Coverage: coverage-engine.xml

Dashboard Analysis:
  ├─ Backend: apps/dashboard/backend
  ├─ Frontend: apps/dashboard/frontend
  ├─ Coverage: coverage-dashboard.xml + lcov.info
  └─ Exclusions: assets, test files, config
```

Quality Metrics:

- Code duplication
- Code coverage percentage
- Code smells & bugs
- Security vulnerabilities
- Maintainability rating

Quality Gate Policy:

- Block pipeline jika gate tidak lolos
- Metrics: coverage >= threshold, 0 blockers, etc.


### Menggunakan Containerization dengan Docker

> Tech: Docker + Docker Compose

Setiap komponen di-containerize dalam image terpisah:

```
ghcr.io/ilhmpbta/siem-engine:latest
  ├─ Base: Python 3.12
  ├─ FastAPI server
  ├─ Decoders & rules mounted
  └─ Port: 8000

ghcr.io/ilhmpbta/siem-dashboard:latest
  ├─ Base: Node.js
  ├─ Vite SPA frontend
  ├─ FastAPI backend
  └─ Port: 8001

ghcr.io/ilhmpbta/siem-exporter:latest
  ├─ Base: Python 3.12
  ├─ Watchdog library
  ├─ WebSocket client
  └─ Volume mounts: /logs
```
- Internal docker network siem_network untuk inter-service communication
- Service discovery via container names
- Environment variables untuk configuration


### Memastikan SIEM dapat Diakses Secara Publik (via Domain)

Infrastructure:

- DuckDNS untuk dynamic DNS pointing (siemsalabim.duckdns.org)
- Nginx reverse proxy dengan SSL/TLS
- Let's Encrypt untuk certificate auto-renewal
- ACME challenge untuk certificate renewal automation


Access Points:

- Dashboard: `https://siemsalabim.duckdns.org`
- Engine API: `https://siemsalabim.duckdns.org/engine`
- Engine WebSocket: `wss://siemsalabim.duckdns.org/engine/ws/...`

Security Features:

- HTTPS only - HTTP to HTTPS redirect (port 80 → 443)
- Let's Encrypt SSL certificates dengan auto-renewal
- WebSocket upgrade headers untuk real-time communication
- Long timeout (86400s) untuk persistent WebSocket connections
- X-Forwarded headers untuk preserving client IP dan protocol
- ACME challenge endpoint untuk certificate renewal tanpa downtime


## Quick Commands

### Setup

```bash
uv sync --all-packages --all-extras # Install dependencies
uv run pytest                       # Run tests
uv run ruff format .                # Format code
uv run ruff check .                 # Lint
```

### Local Deploy

Clone this repository

```bash
git clone https://github.com/lazuardiyasfin/siemsalabim
```

```bash
# Engine lokal
cd apps/engine
SIEM_INGEST_TOKEN=devtoken123 uv run uvicorn src.main:app --port 8000 --reload

# Exporter lokal
cd apps/exporter
SIEM_INGEST_URL=ws://localhost:8000/ws/ingest \
SIEM_INGEST_TOKEN=devtoken123 \
SIEM_EXPORTER_ID=local-dev \
SIEM_WATCH_PATHS=/tmp/fake-logs/test.log \
SIEM_STATE_FILE_PATH=/tmp/exporter-state.json \
uv run python -m src.main

# Run tests
uv run pytest apps/engine/tests/ -v
uv run pytest apps/exporter/tests/ -v

# Lint
uv run ruff check apps/engine/ apps/exporter/
uv run ruff format --check apps/engine/ apps/exporter/
```

### Quick Deploy w/ Docker Container

Prequisites:

- Docker & Docker Compose installed
- Git clone repository

```bash
# Create docker network
docker network create siem_network

# Engine
docker pull ghcr.io/ilhmpbta/siem-engine:latest

docker run -d \
  --name siem-engine \
  --restart unless-stopped \
  --network siem_network \
  -p 8000:8000 \
  -e SIEM_INGEST_TOKEN="your_ingest_token" \
  ghcr.io/ilhmpbta/siem-engine:latest


# Dashbaord
docker pull ghcr.io/ilhmpbta/siem-dashboard:latest

docker run -d \
  --name siem-dashboard \
  --restart unless-stopped \
  --network siem_network \
  -p 8001:8001 \
  -e DASHBOARD_PASSWORD_HASH="your_bcrypt_hash" \
  -e DASHBOARD_JWT_SECRET_KEY="your_jwt_secret" \
  -e DASHBOARD_ENGINE_URL="ws://siem-engine:8000/ws/dashboard" \
  ghcr.io/ilhmpbta/siem-dashboard:latest


# Exporter
docker pull ghcr.io/ilhmpbta/siem-exporter:latest

docker run -d \
  --name siem-exporter \
  -e SIEM_INGEST_URL="ws://siem-engine:8000/ws/ingest" \
  -e SIEM_INGEST_TOKEN="your_ingest_token" \
  -e SIEM_EXPORTER_ID="production-server-1" \
  -e SIEM_WATCH_PATHS="/logs/auth.log,/logs/app.log" \
  -v /var/log:/logs:ro \
  --network siem_network \
  ghcr.io/ilhmpbta/siem-exporter:latest
``` 


## Referensi

| Sumber                   | Link                                                                      |
| ------------------------ | ------------------------------------------------------------------------- |
| Wazuh Documentation      | https://documentation.wazuh.com/current/                                  |
| Wazuh Architecture       | https://documentation.wazuh.com/current/getting-started/architecture.html |
| FastAPI Documentation    | https://fastapi.tiangolo.com/                                             |
| Pydantic Settings        | https://docs.pydantic.dev/dev/concepts/pydantic_settings/                 |
| watchdog Documentation   | https://python-watchdog.readthedocs.io/en/stable/                         |
| websockets Documentation | https://websockets.readthedocs.io/en/stable/                              |
| Python asyncio           | https://docs.python.org/3/library/asyncio.html                            |
| Chart.js                 | https://www.chartjs.org/                                                  |
| Leaflet.js               | https://leafletjs.com/                                                    |
| Docker Documentation     | https://docs.docker.com/                                                  |
| Jenkins Pipeline         | https://www.jenkins.io/doc/book/pipeline/                                 |
| SonarQube                | https://docs.sonarsource.com/sonarqube-community-build/                   |
| Ruff Linter              | https://docs.astral.sh/ruff/                                              |
| uv Package Manager       | https://docs.astral.sh/uv/                                                |
| MITRE ATT&CK Framework   | https://attack.mitre.org/                                                 |
| AI Assistance — Claude   | https://claude.ai/                                                        |
| AI Assistance — Gemini   | https://gemini.google.com/                                                |
