import sys
from pathlib import Path

FOLDER_INI = Path(__file__).resolve().parent
ROOT_DIR = FOLDER_INI.parent

for _jalur in (FOLDER_INI, ROOT_DIR):
    if str(_jalur) not in sys.path:
        sys.path.insert(0, str(_jalur))

import tkinter as tk
from datetime import date

import tema as t
from koneksi import Database

from anggota.umum_anggota import (
    BIRU, BIRU_TUA, ABU, ABU_MUDA, PUTIH, LATAR, HIJAU, MERAH_HEX,
    HARI_SEGERA, UKURAN_MINI,
    AreaGulir, ke_tanggal, format_tanggal,
)


# ==================================================
# MODEL: JADWAL PENGEMBALIAN
# ==================================================
SQL_JADWAL = """
    SELECT
        p.id_peminjaman,
        b.id_buku,
        b.judul,
        p.tanggal_pinjam,
        d.tanggal_jatuh_tempo,
        d.tanggal_kembali,
        d.jumlah
    FROM peminjaman AS p
    JOIN detail_peminjaman AS d
        ON p.id_peminjaman = d.peminjaman_id
    JOIN buku AS b
        ON d.buku_id = b.id_buku
    WHERE p.anggota_id = %s
      AND d.tanggal_jatuh_tempo IS NOT NULL
    ORDER BY
        CASE WHEN d.tanggal_kembali IS NULL THEN 0 ELSE 1 END,
        d.tanggal_jatuh_tempo
"""


class JadwalPengembalian:

    def __init__(self):
        self.db = Database()

    @staticmethod
    def hitung_status(jatuh_tempo, kembali, hari_ini=None):
        """Mengembalikan (teks, kode). Kode: dikembalikan/terlambat/segera/aman."""

        hari_ini = hari_ini or date.today()

        if kembali:
            return "Sudah dikembalikan", "dikembalikan"

        if jatuh_tempo is None:
            return "-", "aman"

        sisa = (jatuh_tempo - hari_ini).days

        if sisa < 0:
            return f"Terlambat {-sisa} hari", "terlambat"

        if sisa == 0:
            return "Jatuh tempo hari ini", "segera"

        if sisa <= HARI_SEGERA:
            return f"{sisa} hari lagi", "segera"

        return f"{sisa} hari lagi", "aman"

    def ambil(self, id_anggota):

        conn = self.db.hubungkan()
        cursor = conn.cursor()

        try:
            cursor.execute(SQL_JADWAL, (id_anggota,))

            hasil = []

            for (id_pjm, id_buku, judul, pinjam,
                 jatuh_tempo, kembali, jumlah) in cursor.fetchall():

                jatuh_tempo = ke_tanggal(jatuh_tempo)
                kembali = ke_tanggal(kembali)

                teks, kode = self.hitung_status(jatuh_tempo, kembali)

                hasil.append({
                    "id_peminjaman": str(id_pjm),
                    "id_buku": str(id_buku),
                    "judul": str(judul),
                    "tanggal_pinjam": ke_tanggal(pinjam),
                    "jatuh_tempo": jatuh_tempo,
                    "kembali": kembali,
                    "jumlah": jumlah,
                    "status_teks": teks,
                    "status_kode": kode,
                })

            return hasil

        finally:
            cursor.close()
            conn.close()

    @staticmethod
    def ringkasan(data):

        aktif = [x for x in data if x["status_kode"] != "dikembalikan"]

        terdekat = None
        for x in aktif:
            if x["jatuh_tempo"] and (
                terdekat is None or x["jatuh_tempo"] < terdekat
            ):
                terdekat = x["jatuh_tempo"]

        return {
            "dipinjam": len(aktif),
            "terdekat": terdekat,
            "terlambat": sum(1 for x in aktif if x["status_kode"] == "terlambat"),
            "segera": sum(1 for x in aktif if x["status_kode"] == "segera"),
        }


# ==================================================
# HALAMAN
# ==================================================

class HalamanJadwal:

    WARNA_STATUS = {
        # kode: (warna garis, latar chip, teks chip)
        "terlambat": (MERAH_HEX, "#FEE2E2", "#B91C1C"),
        "segera": ("#F59E0B", "#FEF3C7", "#B45309"),
        "aman": (BIRU, "#DBEAFE", "#1D4ED8"),
        "dikembalikan": (HIJAU, "#DCFCE7", "#166534"),
    }

    def __init__(self, app, induk):

        self.app = app

        t.Header(
            induk, "JADWAL PENGEMBALIAN",
            "Pantau tanggal jatuh tempo buku yang Anda pinjam"
        ).pack(fill="x")

        wadah = tk.Frame(induk, bg=LATAR)
        wadah.pack(fill="both", expand=True, padx=22, pady=(18, 12))

        # Data
        try:
            data = JadwalPengembalian().ambil(app.id_anggota)
            galat = None
        except Exception as e:
            data = []
            galat = e

        ringkas = JadwalPengembalian.ringkasan(data)

        # Kartu ringkasan
        statistik = tk.Frame(wadah, bg=LATAR)
        statistik.pack(fill="x", pady=(0, 10))

        t.buat_kartu(
            statistik, "SEDANG DIPINJAM", str(ringkas["dipinjam"]), BIRU
        )
        t.buat_kartu(
            statistik, "JATUH TEMPO TERDEKAT",
            format_tanggal(ringkas["terdekat"]), "#D97706"
        )
        t.buat_kartu(
            statistik, "TERLAMBAT", str(ringkas["terlambat"]), MERAH_HEX
        )

        area = AreaGulir(wadah)
        area.luar.pack(fill="both", expand=True)
        app.area_gulir = area

        isi = area.isi

        if galat is not None:

            tk.Label(
                isi,
                text=(
                    "Jadwal pengembalian belum dapat dimuat.\n\n"
                    f"Detail: {galat}\n\n"
                    "Periksa nama kolom pada SQL_JADWAL di riwayat_peminjaman.py."
                ),
                font=("Segoe UI", 10), bg=LATAR, fg=MERAH_HEX,
                justify="left"
            ).pack(anchor="w", padx=8, pady=20)

            return

        aktif = [x for x in data if x["status_kode"] != "dikembalikan"]
        riwayat = [x for x in data if x["status_kode"] == "dikembalikan"]

        self.bagian_jadwal(
            isi, f"Sedang Dipinjam  ({len(aktif)})", aktif,
            "Anda tidak sedang meminjam buku."
        )

        if riwayat:
            self.bagian_jadwal(
                isi, f"Sudah Dikembalikan  ({len(riwayat)})", riwayat, ""
            )

    def bagian_jadwal(self, parent, judul, daftar, pesan_kosong):

        tk.Label(
            parent, text=judul, font=("Segoe UI", 12, "bold"),
            bg=LATAR, fg=BIRU_TUA
        ).pack(anchor="w", padx=8, pady=(10, 6))

        if not daftar:

            tk.Label(
                parent, text=pesan_kosong, font=("Segoe UI", 10),
                bg=LATAR, fg=ABU
            ).pack(anchor="w", padx=8, pady=(0, 10))

            return

        for item in daftar:
            self.buat_kartu_jadwal(parent, item)

    def buat_kartu_jadwal(self, parent, item):

        garis, bg_chip, fg_chip = self.WARNA_STATUS[item["status_kode"]]

        kartu = tk.Frame(
            parent, bg=PUTIH,
            highlightbackground=ABU_MUDA, highlightthickness=1
        )
        kartu.pack(fill="x", padx=6, pady=5)

        tk.Frame(kartu, bg=garis, width=6).pack(side="left", fill="y")

        gambar = self.app.sampul(item["id_buku"], item["judul"], UKURAN_MINI)

        tk.Label(
            kartu, image=gambar, bg=PUTIH, bd=0
        ).pack(side="left", padx=(14, 14), pady=12)

        # Info buku
        info = tk.Frame(kartu, bg=PUTIH)
        info.pack(side="left", fill="x", expand=True, pady=12)

        tk.Label(
            info, text=item["judul"], font=("Segoe UI", 11, "bold"),
            bg=PUTIH, fg=BIRU_TUA, anchor="w"
        ).pack(anchor="w")

        tk.Label(
            info,
            text=(
                f"Dipinjam: {format_tanggal(item['tanggal_pinjam'])}   ·   "
                f"Jumlah: {item['jumlah']}   ·   "
                f"ID Peminjaman: {item['id_peminjaman']}"
            ),
            font=("Segoe UI", 9), bg=PUTIH, fg=ABU, anchor="w"
        ).pack(anchor="w", pady=(4, 0))

        # Jatuh tempo + status
        kanan = tk.Frame(kartu, bg=PUTIH)
        kanan.pack(side="right", padx=20, pady=12)

        if item["kembali"]:
            judul_tanggal = "Dikembalikan"
            tanggal = item["kembali"]
        else:
            judul_tanggal = "Jatuh tempo"
            tanggal = item["jatuh_tempo"]

        tk.Label(
            kanan, text=judul_tanggal, font=("Segoe UI", 8),
            bg=PUTIH, fg=ABU, anchor="e"
        ).pack(anchor="e")

        tk.Label(
            kanan, text=format_tanggal(tanggal),
            font=("Segoe UI", 13, "bold"), bg=PUTIH, fg=BIRU_TUA, anchor="e"
        ).pack(anchor="e")

        tk.Label(
            kanan, text=f"  {item['status_teks']}  ",
            font=("Segoe UI", 8, "bold"), bg=bg_chip, fg=fg_chip, pady=3
        ).pack(anchor="e", pady=(6, 0))