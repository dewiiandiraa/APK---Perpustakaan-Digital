import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import calendar
from datetime import date, datetime

from koneksi import Database


NAMA_BULAN = [
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]

# status_peminjaman: menunggu / dipinjam / ditolak / selesai
STATUS_DIPINJAM = ("dipinjam", "selesai")

# ---------------------------------------------------------------
# SESUAIKAN bila nama kolom di databasemu berbeda.
# ---------------------------------------------------------------
KOL_PENGAJUAN = "tanggal_pengajuan"   # peminjaman.<kolom> tanggal pengajuan
KOL_PETUGAS = "petugas_id"            # peminjaman.<kolom> petugas yang memproses

SQL_ITEM = f"""
    SELECT
        p.id_peminjaman,
        p.{KOL_PENGAJUAN},
        p.tanggal_pinjam,
        d.tanggal_jatuh_tempo,
        d.tanggal_kembali,
        d.jumlah,
        a.id_anggota,
        a.nama,
        a.no_telepon,
        a.alamat,
        b.id_buku,
        b.judul,
        pt.nama
    FROM peminjaman AS p
    JOIN detail_peminjaman AS d
        ON d.peminjaman_id = p.id_peminjaman
    JOIN anggota AS a
        ON a.id_anggota = p.anggota_id
    JOIN buku AS b
        ON b.id_buku = d.buku_id
    LEFT JOIN petugas AS pt
        ON pt.id_petugas = p.{KOL_PETUGAS}
    WHERE p.status_peminjaman IN ('dipinjam', 'selesai')
      AND p.tanggal_pinjam <= %s
      AND (d.tanggal_kembali IS NULL OR d.tanggal_kembali >= %s)
    ORDER BY p.id_peminjaman, b.judul
"""

SQL_PENGAJUAN = f"""
    SELECT status_peminjaman, COUNT(*)
    FROM peminjaman
    WHERE DATE({KOL_PENGAJUAN}) BETWEEN %s AND %s
    GROUP BY status_peminjaman
"""


def ke_tanggal(nilai):

    if nilai is None or nilai == "":
        return None

    if isinstance(nilai, datetime):
        return nilai.date()

    if isinstance(nilai, date):
        return nilai

    for format_ in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d-%m-%Y"):
        try:
            return datetime.strptime(str(nilai), format_).date()
        except ValueError:
            continue

    return None


def hitung_status(jatuh_tempo, kembali, acuan, hari):
    """
    Status satu buku pada tanggal acuan.
    Mengembalikan (teks status, kode warna, keterangan pengembalian).
    """

    if kembali is not None and kembali <= acuan:

        if jatuh_tempo is not None and kembali > jatuh_tempo:
            telat = (kembali - jatuh_tempo).days
            return (
                "Dikembalikan terlambat",
                "dikembalikan_terlambat",
                f"Terlambat {telat} hari",
            )

        return "Dikembalikan", "dikembalikan", "Tepat waktu"

    if jatuh_tempo is None:
        return "-", "aman", "-"

    sisa = (jatuh_tempo - acuan).days

    if sisa < 0:
        return f"Terlambat {-sisa} hari", "terlambat", "-"

    if sisa == 0:
        return "Jatuh tempo hari ini", "segera", "-"

    if sisa <= hari:
        return f"{sisa} hari lagi", "segera", "-"

    return f"{sisa} hari lagi", "aman", "-"


class LaporanPeminjaman:

    def __init__(self):
        self.db = Database()

    def kumpulkan(self, tahun, bulan, hari_jatuh_tempo=3,
                  dibuat_oleh="", role="", catatan=""):

        awal = date(tahun, bulan, 1)
        akhir = date(tahun, bulan, calendar.monthrange(tahun, bulan)[1])

        # Periode berjalan: acuan = hari ini. Periode lampau: hari terakhir bulan.
        acuan = min(date.today(), akhir)

        conn = self.db.hubungkan()
        cursor = conn.cursor()

        try:
            cursor.execute(SQL_PENGAJUAN, (awal, akhir))
            hitung = {
                str(s).strip().lower(): int(n)
                for s, n in cursor.fetchall()
            }

            cursor.execute(SQL_ITEM, (akhir, awal))
            sumber = cursor.fetchall()

        finally:
            cursor.close()
            conn.close()

        pengajuan = {
            "menunggu": hitung.get("menunggu", 0),
            # disetujui = sedang dipinjam + sudah selesai
            "disetujui": (
                hitung.get("dipinjam", 0)
                + hitung.get("selesai", 0)
                + hitung.get("disetujui", 0)
            ),
            "ditolak": hitung.get("ditolak", 0),
        }

        semua = [
            self._baris(r, acuan, hari_jatuh_tempo) for r in sumber
        ]

        def selesai(b):
            return b["kembali"] is not None and b["kembali"] <= acuan

        def belum(b):
            return (not selesai(b)) and b["tgl_pinjam"] is not None \
                and b["tgl_pinjam"] <= acuan

        def urut_tempo(b):
            return (b["jatuh_tempo"] or date.max, b["id_peminjaman"])

        belum_kembali = sorted(
            [b for b in semua if belum(b)], key=urut_tempo
        )

        terlambat = [
            b for b in belum_kembali
            if b["jatuh_tempo"] is not None and b["jatuh_tempo"] < acuan
        ]

        jatuh_tempo = [
            b for b in belum_kembali
            if b["jatuh_tempo"] is not None
            and 0 <= (b["jatuh_tempo"] - acuan).days <= hari_jatuh_tempo
        ]

        peminjaman = sorted(
            [
                b for b in semua
                if b["tgl_pinjam"] is not None
                and awal <= b["tgl_pinjam"] <= akhir
            ],
            key=lambda b: (b["tgl_pinjam"], b["id_peminjaman"])
        )

        dikembalikan = sorted(
            [
                b for b in semua
                if selesai(b) and awal <= b["kembali"] <= akhir
            ],
            key=lambda b: (b["kembali"], b["id_peminjaman"])
        )

        return {
            "tahun": tahun,
            "bulan": bulan,
            "nama_bulan": f"{NAMA_BULAN[bulan - 1]} {tahun}",
            "acuan": acuan,
            "dibuat_pada": datetime.now(),
            "dibuat_oleh": dibuat_oleh,
            "role": role,
            "catatan": catatan,
            "hari_jatuh_tempo": hari_jatuh_tempo,
            "pengajuan": pengajuan,
            "lembar": {
                "belum_kembali": belum_kembali,
                "terlambat": terlambat,
                "jatuh_tempo": jatuh_tempo,
                "peminjaman": peminjaman,
                "dikembalikan": dikembalikan,
            },
        }

    @staticmethod
    def _baris(r, acuan, hari):

        (id_pjm, pengajuan, pinjam, jatuh_tempo, kembali, jumlah,
         id_anggota, nama, telepon, alamat, id_buku, judul, petugas) = r

        pinjam = ke_tanggal(pinjam)
        jatuh_tempo = ke_tanggal(jatuh_tempo)
        kembali = ke_tanggal(kembali)

        status, kode, ket = hitung_status(jatuh_tempo, kembali, acuan, hari)

        sisa = None
        hari_terlambat = None

        if jatuh_tempo is not None and not (
            kembali is not None and kembali <= acuan
        ):
            sisa = (jatuh_tempo - acuan).days
            hari_terlambat = max(0, -sisa)

        return {
            "id_peminjaman": str(id_pjm),
            "id_anggota": str(id_anggota),
            "nama": str(nama or ""),
            "telepon": "" if telepon is None else str(telepon),
            "alamat": "" if alamat is None else str(alamat),
            "id_buku": str(id_buku),
            "judul": str(judul or ""),
            "jumlah": int(jumlah or 0),
            "tgl_pengajuan": ke_tanggal(pengajuan),
            "tgl_pinjam": pinjam,
            "jatuh_tempo": jatuh_tempo,
            "kembali": kembali,
            "status": status,
            "kode": kode,
            "petugas": "" if petugas is None else str(petugas),
            "sisa": sisa,
            "hari_terlambat": hari_terlambat,
            "keterangan_kembali": ket,
        }