import sys
from pathlib import Path

FOLDER_INI = Path(__file__).resolve().parent
ROOT_DIR = FOLDER_INI.parent

for _jalur in (FOLDER_INI, ROOT_DIR):
    if str(_jalur) not in sys.path:
        sys.path.insert(0, str(_jalur))

import tkinter as tk

import tema as t

from anggota.umum_anggota import (
    BIRU, BIRU_TUA, ABU, ABU_MUDA, PUTIH, LATAR,
    UKURAN_DETAIL, AreaGulir,
)


class HalamanDetail:

    def __init__(self, app, induk, b):

        self.app = app

        t.Header(
            induk, "DETAIL BUKU", "Informasi lengkap buku"
        ).pack(fill="x")

        wadah = tk.Frame(induk, bg=LATAR)
        wadah.pack(fill="both", expand=True, padx=22, pady=(18, 12))

        area = AreaGulir(wadah)
        area.luar.pack(fill="both", expand=True)
        app.area_gulir = area

        panel, isi = t.buat_panel(area.isi)
        panel.pack(fill="x", padx=6, pady=(0, 12))

        isi.grid_columnconfigure(1, weight=1)

        # Sampul besar
        gambar = app.sampul(b["id"], b["judul"], UKURAN_DETAIL)

        tk.Label(
            isi, image=gambar, bg=PUTIH, bd=0
        ).grid(row=0, column=0, sticky="n", padx=(0, 28), pady=4)

        # Informasi
        kanan = tk.Frame(isi, bg=PUTIH)
        kanan.grid(row=0, column=1, sticky="nsew")

        tk.Label(
            kanan, text=b["judul"], font=("Segoe UI", 20, "bold"),
            bg=PUTIH, fg=BIRU_TUA, wraplength=520, justify="left", anchor="w"
        ).pack(anchor="w")

        tk.Label(
            kanan, text=f"oleh {b['penulis'] or '-'}",
            font=("Segoe UI", 11), bg=PUTIH, fg=ABU
        ).pack(anchor="w", pady=(4, 10))

        ada = b["stok_tersedia"] > 0

        tk.Label(
            kanan,
            text=(
                f"  Tersedia · {b['stok_tersedia']} eksemplar  "
                if ada else "  Sedang tidak tersedia  "
            ),
            font=("Segoe UI", 9, "bold"),
            bg="#DCFCE7" if ada else "#FEE2E2",
            fg="#166534" if ada else "#991B1B",
            pady=4
        ).pack(anchor="w", pady=(0, 14))

        baris_info = [
            ("ID Buku", b["id"]),
            ("Penulis", b["penulis"]),
            ("Penerbit", b["penerbit"]),
            ("Tahun Terbit", b["tahun"]),
            ("Kategori", b["kategori"]),
            ("Stok Total", str(b["stok_total"])),
            ("Stok Tersedia", str(b["stok_tersedia"])),
        ]

        for label, nilai in baris_info:

            tk.Frame(kanan, bg=ABU_MUDA, height=1).pack(fill="x")

            baris = tk.Frame(kanan, bg=PUTIH)
            baris.pack(fill="x", pady=7)

            tk.Label(
                baris, text=label, width=16, anchor="w",
                font=("Segoe UI", 9, "bold"), bg=PUTIH, fg=ABU
            ).pack(side="left")

            tk.Label(
                baris, text=nilai if nilai else "-", anchor="w",
                font=("Segoe UI", 11), bg=PUTIH, fg=BIRU_TUA
            ).pack(side="left")

        tk.Frame(kanan, bg=ABU_MUDA, height=1).pack(fill="x")

        # Tombol
        tombol = tk.Frame(kanan, bg=PUTIH)
        tombol.pack(anchor="w", pady=(18, 4))

        t.Tombol(
            tombol, "←  Kembali ke Katalog", BIRU_TUA,
            lambda: app.pilih_menu("Katalog Buku")
        ).pack(side="left")

        t.Tombol(
            tombol, "Lihat Jadwal Pengembalian", BIRU,
            lambda: app.pilih_menu("Jadwal Pengembalian")
        ).pack(side="left", padx=10)