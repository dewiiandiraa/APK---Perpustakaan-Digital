import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from koneksi import Database


SQL_BUAT_TABEL = """
    CREATE TABLE IF NOT EXISTS laporan_terkirim (
        id_laporan        INT AUTO_INCREMENT PRIMARY KEY,
        tahun             SMALLINT     NOT NULL,
        bulan             TINYINT      NOT NULL,
        nama_file         VARCHAR(150) NOT NULL,
        isi_file          LONGBLOB     NOT NULL,
        catatan           VARCHAR(255) NULL,
        dikirim_oleh_id   VARCHAR(50)  NULL,
        dikirim_oleh_nama VARCHAR(100) NULL,
        dikirim_pada      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
        dibaca_pada       DATETIME     NULL,
        dibaca_oleh       VARCHAR(100) NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
"""


def folder_unduhan():
    """Folder Downloads milik pengguna (cadangan: Documents, lalu Home)."""

    for kandidat in (
        Path.home() / "Downloads",
        Path.home() / "Documents",
        Path.home(),
    ):
        if kandidat.exists():
            return kandidat

    return Path.home()


def lokasi_unik(folder, nama_file):
    """Bila nama sudah ada, tambahkan (1), (2), ... agar tidak menimpa."""

    lokasi = Path(folder) / nama_file
    n = 1

    while lokasi.exists():
        lokasi = Path(folder) / f"{Path(nama_file).stem} ({n}){Path(nama_file).suffix}"
        n += 1

    return lokasi


class LaporanTerkirim:

    def __init__(self):
        self.db = Database()

    def _buka(self):
        """Koneksi + kursor, dengan memastikan tabel sudah ada."""

        conn = self.db.hubungkan()
        cursor = conn.cursor()

        try:
            cursor.execute(SQL_BUAT_TABEL)
            conn.commit()
        except Exception:
            pass  # tabel mungkin sudah ada / tidak ada hak CREATE

        return conn, cursor

    # ---------- petugas ----------

    def kirim(self, tahun, bulan, nama_file, isi, catatan,
              id_petugas, nama_petugas):

        conn, cursor = self._buka()

        try:
            cursor.execute("""
                INSERT INTO laporan_terkirim
                    (tahun, bulan, nama_file, isi_file, catatan,
                     dikirim_oleh_id, dikirim_oleh_nama)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                tahun, bulan, nama_file, isi, catatan or None,
                None if id_petugas is None else str(id_petugas),
                nama_petugas,
            ))

            conn.commit()

            return cursor.lastrowid

        finally:
            cursor.close()
            conn.close()

    # ---------- operator ----------

    def daftar(self, batas=200):
        """Daftar laporan terbaru (tanpa isi file agar ringan)."""

        conn, cursor = self._buka()

        try:
            cursor.execute("""
                SELECT
                    id_laporan, tahun, bulan, nama_file, catatan,
                    dikirim_oleh_nama, dikirim_pada,
                    dibaca_pada, dibaca_oleh,
                    LENGTH(isi_file)
                FROM laporan_terkirim
                ORDER BY dikirim_pada DESC, id_laporan DESC
                LIMIT %s
            """, (batas,))

            hasil = []

            for (id_, tahun, bulan, nama_file, catatan, pengirim,
                 dikirim, dibaca, pembaca, ukuran) in cursor.fetchall():

                hasil.append({
                    "id": int(id_),
                    "tahun": int(tahun),
                    "bulan": int(bulan),
                    "nama_file": str(nama_file),
                    "catatan": catatan or "",
                    "pengirim": pengirim or "-",
                    "dikirim_pada": dikirim,
                    "dibaca_pada": dibaca,
                    "dibaca_oleh": pembaca or "",
                    "ukuran": int(ukuran or 0),
                })

            return hasil

        finally:
            cursor.close()
            conn.close()

    def ambil_file(self, id_laporan):
        """Mengembalikan (nama_file, isi bytes)."""

        conn, cursor = self._buka()

        try:
            cursor.execute(
                "SELECT nama_file, isi_file FROM laporan_terkirim "
                "WHERE id_laporan = %s",
                (id_laporan,)
            )

            baris = cursor.fetchone()

            if baris is None:
                raise ValueError("Laporan tidak ditemukan.")

            return str(baris[0]), bytes(baris[1])

        finally:
            cursor.close()
            conn.close()

    def tandai_dibaca(self, id_laporan, nama_pembaca):

        conn, cursor = self._buka()

        try:
            cursor.execute("""
                UPDATE laporan_terkirim
                SET dibaca_pada = NOW(), dibaca_oleh = %s
                WHERE id_laporan = %s AND dibaca_pada IS NULL
            """, (nama_pembaca, id_laporan))

            conn.commit()

        finally:
            cursor.close()
            conn.close()

    def jumlah_baru(self):

        conn, cursor = self._buka()

        try:
            cursor.execute(
                "SELECT COUNT(*) FROM laporan_terkirim "
                "WHERE dibaca_pada IS NULL"
            )

            return int(cursor.fetchone()[0])

        finally:
            cursor.close()
            conn.close()