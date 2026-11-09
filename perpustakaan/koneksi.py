import os
import sys
from pathlib import Path

import mysql.connector
from mysql.connector import Error


def _folder_program():
    """Folder tempat program berada (juga saat sudah menjadi .exe)."""

    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parent


def _baca_env():
    """Baca berkas .env sederhana (KEY=VALUE, baris # diabaikan)."""

    nilai = {}

    for folder in (_folder_program(), Path(__file__).resolve().parent):

        lokasi = folder / ".env"

        if not lokasi.exists():
            continue

        try:
            for baris in lokasi.read_text(encoding="utf-8-sig").splitlines():

                baris = baris.strip()

                if not baris or baris.startswith("#") or "=" not in baris:
                    continue

                kunci, _, isi = baris.partition("=")
                nilai.setdefault(kunci.strip(), isi.strip().strip("\"'"))

        except OSError:
            pass

        break

    return nilai


class Database:

    def __init__(self):

        env = _baca_env()

        def ambil(nama, bawaan):
            return os.environ.get(nama, env.get(nama, bawaan))

        self.config = {
            "host": ambil("DB_HOST", "localhost"),
            "user": ambil("DB_USER", "root"),
            "password": ambil("DB_PASSWORD", ""),
            "database": ambil("DB_NAME", "perpustakaan"),
            "port": int(ambil("DB_PORT", "3306")),
            "autocommit": False
        }

    def hubungkan(self):
        try:
            conn = mysql.connector.connect(**self.config)

            if conn.is_connected():
                return conn

            raise Error("Koneksi database gagal.")

        except Error as e:
            raise ConnectionError(
                f"Tidak dapat terhubung ke database perpustakaan: {e}"
            ) from e