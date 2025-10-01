# NL-to-SQL with RAG and Gemini 💬️

Proyek ini adalah sebuah API cerdas yang mampu menerjemahkan pertanyaan dalam bahasa natural (Indonesia) menjadi query SQL yang aman, mengeksekusinya ke database, dan memberikan jawaban analisis dalam format yang mudah dimengerti. Sistem ini dibangun menggunakan arsitektur **Retrieval-Augmented Generation (RAG)** dengan model bahasa dari Google Gemini.

Fitur utamanya meliputi:

- **Klasifikasi Pertanyaan**: Secara otomatis menolak pertanyaan di luar konteks data perusahaan.
- **Generasi SQL Kontekstual**: Mampu memahami percakapan lanjutan (misalnya, kata "tersebut", "itu").
- **Validasi Keamanan**: Memastikan hanya query `SELECT` yang aman yang dieksekusi ke database.
- **Analisis Hasil**: Memberikan ringkasan jawaban dalam bahasa manusia, bukan hanya data mentah.

## 🏛️ Arsitektur

Aplikasi ini menggunakan alur kerja multi-langkah (_multi-step chain_) untuk memproses setiap permintaan:

`Pertanyaan Pengguna` → `1. Router Chain` → `2. NL-to-SQL Chain` → `3. SQL Validator` → `4. SQL Executor` → `5. Analysis Chain` → `Jawaban Final`

## 🛠️ Teknologi yang Digunakan

- **Backend**: **FastAPI**
- **Server**: **Uvicorn**
- **AI / LLM**:
  - **Generator**: **Google Gemini** (via `langchain-google-genai`)
  - **Embedding**: **`BAAI/bge-base-en-v1.5`** (via `langchain-huggingface`)
  - **Orkestrasi**: **LangChain**
- **Database**:
  - **Utama**: **MySQL** (dihubungkan dengan `SQLAlchemy` & `PyMySQL`)
  - **Vector DB**: **ChromaDB**
- **Validasi & Utilitas**: **`sqlparse`**, **`pandas`**, **`python-dotenv`**
- **Rate Limiting**: **`slowapi`**

## 🚀 Cara Instalasi dan Menjalankan Proyek

Berikut adalah langkah-langkah untuk menjalankan proyek ini di lingkungan lokal.

### 1\. Clone Repository

```bash
git clone https://github.com/username-anda/nama-repo.git
cd nama-repo
```

### 2\. Buat dan Aktifkan Virtual Environment

```bash
# Buat venv
python -m venv .venv

# Aktifkan di macOS/Linux
source .venv/bin/activate

# Aktifkan di Windows
.\.venv\Scripts\activate
```

### 3\. Konfigurasi Environment Variables

Salin file `.env.example` menjadi `.env` dan isi dengan kredensial Anda.

```bash
cp .env.example .env
```

Isi dari file `.env` harus terlihat seperti ini:

```ini
# Kredensial Google AI
GOOGLE_API_KEY="AIz...YourSecretKey"

# Kredensial Database MySQL Anda
DB_HOST="127.0.0.1"
DB_USER="root"
DB_PASSWORD="password_anda"
DB_NAME="db_ebudgeting"
DB_PORT="3306"
```

### 4\. Install Semua Dependensi

Pastikan file `requirements.txt` Anda sudah lengkap, lalu jalankan:

```bash
pip install -r requirements.txt
```

### 5\. Siapkan Data untuk RAG (Ingestion)

Pastikan file `data/schema_description.yml` Anda sudah ada dan berisi metadata skema database. Jalankan script _ingest_ untuk membuat database vektor.

```bash
python scripts/ingest_schema.py
```

Proses ini akan membuat folder `chroma_db/` di proyek Anda.

### 6\. Jalankan Server API

```bash
uvicorn src.main:app --reload
```

Server akan berjalan di `http://127.0.0.1:8000`.

## 📡 Dokumentasi API

Setelah server berjalan, Anda bisa mengakses dokumentasi API interaktif untuk melakukan pengujian melalui browser di:
`http://127.0.0.1:8000/docs`

### Contoh Penggunaan Endpoint `/context-nl-to-sql`

#### Permintaan Pertama

```json
{
  "question": "tampilkan 3 unit dengan sisa anggaran terkecil di tahun 2024",
  "conversation_id": "sesi-unik-123"
}
```

#### Permintaan Kedua (Lanjutan)

```json
{
  "question": "dari ketiga unit tersebut, mana yang pagu anggarannya paling besar?",
  "conversation_id": "sesi-unik-123"
}
```
