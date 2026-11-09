import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import os
from io import BytesIO

from PIL import Image, ImageOps

# Dukungan AVIF: Pillow >= 11.3 sudah bawaan; versi lama: pillow-avif-plugin
try:
    import pillow_avif  # noqa: F401
except ImportError:
    pass

from koneksi import Database


EKSTENSI = (".jpg", ".jpeg", ".png", ".webp", ".avif")
UKURAN_MAKS = (600, 800)          # sisi terpanjang foto yang disimpan
KUALITAS_JPEG = 90
BATAS_FILE_MB = 20


def _folder_sampul():
    """assets/sampul di folder proyek (folder yang berisi 'assets')."""

    folder = Path(__file__).resolve().parent

    for kandidat in (folder, folder.parent):
        if (kandidat / "assets").exists():
            return kandidat / "assets" / "sampul"

    return folder.parent / "assets" / "sampul"


FOLDER_SAMPUL = _folder_sampul()

SQL_BUAT_TABEL = """
    CREATE TABLE IF NOT EXISTS sampul_buku (
        id_buku    VARCHAR(10) NOT NULL PRIMARY KEY,
        isi_file   LONGBLOB    NOT NULL,
        diperbarui TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP
                               ON UPDATE CURRENT_TIMESTAMP
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""


class SampulBuku:

    def __init__(self):
        self.db = Database()

    # ==================== OLAH GAMBAR ====================

    @staticmethod
    def proses(lokasi):
        """
        Membaca gambar pilihan pengguna dan mengubahnya menjadi JPEG
        (maks 600x800) agar ukuran kecil dan seragam. Mengembalikan bytes.
        """

        lokasi = Path(lokasi)

        if not lokasi.exists():
            raise ValueError("File gambar tidak ditemukan.")

        if lokasi.stat().st_size > BATAS_FILE_MB * 1024 * 1024:
            raise ValueError(f"Ukuran file maksimal {BATAS_FILE_MB} MB.")

        try:
            gambar = Image.open(lokasi)
            gambar = ImageOps.exif_transpose(gambar)

        except Exception:
            raise ValueError(
                "File tidak dapat dibaca sebagai gambar.\n"
                "Format yang didukung: JPG, PNG, WEBP, AVIF.\n"
                "(Untuk AVIF, perbarui Pillow: pip install --upgrade pillow)"
            )

        # Latar putih bila gambar punya bagian transparan
        if gambar.mode in ("RGBA", "LA", "P"):
            gambar = gambar.convert("RGBA")
            latar = Image.new("RGB", gambar.size, (255, 255, 255))
            latar.paste(gambar, mask=gambar.split()[-1])
            gambar = latar
        else:
            gambar = gambar.convert("RGB")

        gambar.thumbnail(UKURAN_MAKS, Image.LANCZOS)

        buffer = BytesIO()
        gambar.save(buffer, "JPEG", quality=KUALITAS_JPEG, optimize=True)

        return buffer.getvalue()

    # ==================== DATABASE ====================

    def _buka(self):

        conn = self.db.hubungkan()
        cursor = conn.cursor()

        try:
            cursor.execute(SQL_BUAT_TABEL)
            conn.commit()
        except Exception:
            pass  # tabel sudah ada / tidak ada hak CREATE

        return conn, cursor

    # ==================== FILE ====================

    @staticmethod
    def _file_ada(id_buku):

        for ekstensi in EKSTENSI:
            lokasi = FOLDER_SAMPUL / f"{id_buku}{ekstensi}"

            if lokasi.exists():
                return lokasi

        return None

    @staticmethod
    def _hapus_file(id_buku):

        for ekstensi in EKSTENSI:
            lokasi = FOLDER_SAMPUL / f"{id_buku}{ekstensi}"

            try:
                if lokasi.exists():
                    lokasi.unlink()
            except OSError:
                pass

    # ==================== OPERASI ====================

    def simpan(self, id_buku, isi_jpeg):
        """
        Menyimpan foto ke folder DAN database.
        Mengembalikan None bila semuanya berhasil, atau teks peringatan
        bila hanya salah satunya yang berhasil.
        Melempar OSError bila file tidak dapat ditulis ke folder.
        """

        # 1) folder (foto lama dengan ekstensi lain dibuang agar tidak menutupi)
        FOLDER_SAMPUL.mkdir(parents=True, exist_ok=True)
        self._hapus_file(id_buku)
        (FOLDER_SAMPUL / f"{id_buku}.jpg").write_bytes(isi_jpeg)

        # 2) database
        try:
            conn, cursor = self._buka()

            try:
                cursor.execute("""
                    INSERT INTO sampul_buku (id_buku, isi_file)
                    VALUES (%s, %s)
                    ON DUPLICATE KEY UPDATE isi_file = VALUES(isi_file)
                """, (id_buku, isi_jpeg))

                conn.commit()

            finally:
                cursor.close()
                conn.close()

        except Exception as e:
            return (
                "Foto tersimpan di folder assets/sampul, tetapi gagal "
                f"disalin ke database:\n{e}"
            )

        return None

    def hapus(self, id_buku):
        """Menghapus foto dari folder dan database. Mengembalikan peringatan/None."""

        self._hapus_file(id_buku)

        try:
            conn, cursor = self._buka()

            try:
                cursor.execute(
                    "DELETE FROM sampul_buku WHERE id_buku = %s", (id_buku,)
                )
                conn.commit()

            finally:
                cursor.close()
                conn.close()

        except Exception as e:
            return f"Foto di folder terhapus, tetapi salinan di database gagal dihapus:\n{e}"

        return None

    def ada(self, id_buku):
        return self._file_ada(id_buku) is not None

    def ambil(self, id_buku):
        """
        Isi foto (bytes) atau None bila belum ada.
        Dicari di folder dulu; bila tidak ada, diambil dari database
        lalu dikembalikan ke folder.
        """

        lokasi = self._file_ada(id_buku)

        if lokasi is not None:
            try:
                return lokasi.read_bytes()
            except OSError:
                pass

        try:
            conn, cursor = self._buka()

            try:
                cursor.execute(
                    "SELECT isi_file FROM sampul_buku WHERE id_buku = %s",
                    (id_buku,)
                )
                baris = cursor.fetchone()

            finally:
                cursor.close()
                conn.close()

        except Exception as e:
            print(f"[Sampul] Gagal membaca database: {e}")
            return None

        if baris is None:
            return None

        isi = bytes(baris[0])

        try:
            FOLDER_SAMPUL.mkdir(parents=True, exist_ok=True)
            (FOLDER_SAMPUL / f"{id_buku}.jpg").write_bytes(isi)
        except OSError:
            pass

        return isi

    def sinkronkan_dari_db(self):
        """
        Menyalin ke folder semua foto yang ada di database tetapi belum ada
        di komputer ini. Mengembalikan jumlah foto yang disalin.
        """

        try:
            conn, cursor = self._buka()

            try:
                cursor.execute("SELECT id_buku FROM sampul_buku")
                di_db = [str(b[0]) for b in cursor.fetchall()]

                kurang = [i for i in di_db if self._file_ada(i) is None]

                if not kurang:
                    return 0

                FOLDER_SAMPUL.mkdir(parents=True, exist_ok=True)

                jumlah = 0

                for id_buku in kurang:
                    cursor.execute(
                        "SELECT isi_file FROM sampul_buku WHERE id_buku = %s",
                        (id_buku,)
                    )
                    baris = cursor.fetchone()

                    if baris is None:
                        continue

                    (FOLDER_SAMPUL / f"{id_buku}.jpg").write_bytes(bytes(baris[0]))
                    jumlah += 1

                return jumlah

            finally:
                cursor.close()
                conn.close()

        except Exception as e:
            print(f"[Sampul] Sinkronisasi gagal: {e}")
            return 0