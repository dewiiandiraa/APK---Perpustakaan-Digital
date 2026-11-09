import sys
from pathlib import Path

FOLDER_INI = Path(__file__).resolve().parent
ROOT_DIR = FOLDER_INI.parent

for _jalur in (FOLDER_INI, ROOT_DIR):
    if str(_jalur) not in sys.path:
        sys.path.insert(0, str(_jalur))

import tkinter as tk
from tkinter import ttk, messagebox

from PIL import ImageTk

import tema as t
from koneksi import Database

from anggota.umum_anggota import (
    BIRU, BIRU_TUA, ABU, ABU_MUDA, PUTIH, LATAR, HIJAU, MERAH_HEX,
    HARI_SEGERA, UKURAN_KARTU,
    AreaGulir, buat_banner, potong,
)
from peminjaman.riwayat_peminjaman import JadwalPengembalian

# Foto sampul yang tersimpan di database (disalin ke folder bila belum ada)
try:
    from buku.sampul_buku import SampulBuku
except ImportError:
    try:
        from sampul_buku import SampulBuku
    except ImportError:
        SampulBuku = None


LEBAR_KARTU = 196   # lebar satu kotak buku (termasuk jarak)
BATCH_KARTU = 40    # jumlah buku yang ditampilkan per tahap


# ==================================================
# MODEL: KATALOG BUKU
# ==================================================

class KatalogBuku:

    def __init__(self):
        self.db = Database()

    def semua(self):
        """Seluruh buku untuk katalog (SESUAIKAN nama kolom bila berbeda)."""

        conn = self.db.hubungkan()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT
                    id_buku,
                    judul,
                    penulis,
                    penerbit,
                    tahun_terbit,
                    kategori,
                    stok_total,
                    stok_tersedia
                FROM buku
                ORDER BY judul
            """)

            def teks(nilai):
                return "" if nilai is None else str(nilai)

            hasil = []

            for baris in cursor.fetchall():
                hasil.append({
                    "id": teks(baris[0]),
                    "judul": teks(baris[1]),
                    "penulis": teks(baris[2]),
                    "penerbit": teks(baris[3]),
                    "tahun": teks(baris[4]),
                    "kategori": teks(baris[5]).strip(),
                    "stok_total": int(baris[6] or 0),
                    "stok_tersedia": int(baris[7] or 0),
                })

            return hasil

        finally:
            cursor.close()
            conn.close()


# ==================================================
# HALAMAN
# ==================================================

class HalamanKatalog:

    def __init__(self, app, induk):

        self.app = app

        self.semua = []
        self.hasil = []
        self.kartu = []
        self.tampil = BATCH_KARTU
        self.kolom = 0
        self.tombol_lanjut = None
        self.area = None
        self.img_banner = None

        self.bangun(induk)

    # ==================== KERANGKA HALAMAN ====================

    def bangun(self, induk):

        app = self.app

        wadah = tk.Frame(induk, bg=LATAR)
        wadah.pack(fill="both", expand=True, padx=28, pady=(24, 12))

        # Banner sambutan
        banner = tk.Canvas(
            wadah, height=120, bg=LATAR, highlightthickness=0, bd=0
        )
        banner.pack(fill="x")

        lebar_terakhir = [0]

        def gambar_banner(event=None):

            if app.sedang_animasi:
                return

            try:
                w = banner.winfo_width()
            except tk.TclError:
                return

            if w < 100 or w == lebar_terakhir[0]:
                return

            lebar_terakhir[0] = w

            banner.delete("all")

            self.img_banner = ImageTk.PhotoImage(buat_banner(w, 120))

            banner.create_image(0, 0, image=self.img_banner, anchor="nw")

            banner.create_text(
                34, 46, anchor="w",
                text=f"Halo, {app.nama}!",
                font=("Segoe UI", 20, "bold"),
                fill=PUTIH
            )

            banner.create_text(
                34, 82, anchor="w",
                text="Temukan dan pelajari koleksi buku perpustakaan.",
                font=("Segoe UI", 10),
                fill="#DBEAFE"
            )

        jadwal = [None]

        def saat_ubah(event=None):

            if jadwal[0] is not None:
                banner.after_cancel(jadwal[0])

            jadwal[0] = banner.after(40, gambar_banner)

        banner.bind("<Configure>", saat_ubah)
        app.redraw_banner = gambar_banner

        # Tempat peringatan jadwal (muncul bila perlu)
        self.peringatan = tk.Frame(wadah, bg=LATAR)
        self.peringatan.pack(fill="x")

        # Toolbar pencarian
        bar = tk.Frame(
            wadah, bg=PUTIH,
            highlightbackground=ABU_MUDA, highlightthickness=1
        )
        bar.pack(fill="x", pady=(14, 12))

        isi = tk.Frame(bar, bg=PUTIH, padx=16, pady=12)
        isi.pack(fill="x")

        self.var_cari = tk.StringVar(value=app.filter_simpan[0])
        self.var_kat = tk.StringVar(value=app.filter_simpan[1])

        tk.Label(
            isi, text="Cari:", bg=PUTIH, fg=ABU, font=("Segoe UI", 9, "bold")
        ).pack(side="left")

        entry = t.buat_entry(isi, self.var_cari, width=34)
        entry.pack(side="left", padx=(8, 20), ipady=6)

        tk.Label(
            isi, text="Kategori:", bg=PUTIH, fg=ABU,
            font=("Segoe UI", 9, "bold")
        ).pack(side="left")

        self.combo_kat = ttk.Combobox(
            isi, textvariable=self.var_kat, state="readonly",
            width=20, font=("Segoe UI", 10),
            values=["Semua kategori"]
        )
        self.combo_kat.pack(side="left", padx=(8, 0), ipady=3)

        t.Tombol(
            isi, "Muat Ulang", BIRU, self.muat_katalog
        ).pack(side="right")

        self.label_jumlah = tk.Label(
            isi, text="", bg=PUTIH, fg=ABU, font=("Segoe UI", 9)
        )
        self.label_jumlah.pack(side="right", padx=16)

        self._tunda_cari = None

        def jadwalkan_saring(event=None):

            if self._tunda_cari is not None:
                entry.after_cancel(self._tunda_cari)

            self._tunda_cari = entry.after(250, self.saring)

        entry.bind("<KeyRelease>", jadwalkan_saring)
        self.combo_kat.bind("<<ComboboxSelected>>", lambda e: self.saring())

        # Area katalog yang bisa digulir
        self.area = AreaGulir(wadah)
        self.area.luar.pack(fill="both", expand=True)
        self.area.pada_lebar = lambda w: self.tata_katalog(w)

        app.area_gulir = self.area

        self.muat_katalog()

    # ==================== DATA & FILTER ====================

    def muat_katalog(self):

        # Salin foto sampul dari database yang belum ada di komputer ini.
        if SampulBuku is not None:
            try:
                SampulBuku().sinkronkan_dari_db()
            except Exception as e:
                print(f"[Katalog] Sinkronisasi sampul gagal: {e}")

        # Kosongkan cache gambar agar sampul yang baru ditambahkan ikut terbaca.
        self.app.cache_gambar.clear()

        try:
            self.semua = KatalogBuku().semua()

        except Exception as e:

            self.semua = []

            messagebox.showerror(
                "Kesalahan",
                f"Gagal memuat katalog buku:\n{e}",
                parent=self.app.root
            )

        kategori = sorted({b["kategori"] for b in self.semua if b["kategori"]})
        nilai = ["Semua kategori"] + kategori

        self.combo_kat["values"] = nilai

        if self.var_kat.get() not in nilai:
            self.var_kat.set("Semua kategori")

        self.saring()
        self.cek_peringatan()

    def saring(self):

        kata = self.var_cari.get().strip().lower()
        kategori = self.var_kat.get()

        self.app.filter_simpan = (self.var_cari.get(), kategori)

        def cocok(b):

            if kategori != "Semua kategori" and b["kategori"] != kategori:
                return False

            if not kata:
                return True

            gabungan = " ".join(
                [b["id"], b["judul"], b["penulis"], b["penerbit"], b["kategori"]]
            ).lower()

            return kata in gabungan

        self.hasil = [b for b in self.semua if cocok(b)]
        self.tampil = BATCH_KARTU

        self.label_jumlah.config(text=f"{len(self.hasil)} buku")

        self.bangun_katalog()

    # ==================== KISI KARTU BUKU ====================

    def bangun_katalog(self, reset=True):

        area = self.area

        for widget in area.isi.winfo_children():
            widget.destroy()

        self.kartu = []
        self.tombol_lanjut = None
        self.kolom = 0

        if not self.hasil:

            tk.Label(
                area.isi,
                text="Buku tidak ditemukan.\nCoba kata kunci atau kategori lain.",
                font=("Segoe UI", 11), bg=LATAR, fg=ABU, justify="center"
            ).grid(row=0, column=0, pady=60)

            area.isi.grid_columnconfigure(0, weight=1)

            return

        for b in self.hasil[:self.tampil]:
            self.kartu.append(self.buat_kartu_buku(area.isi, b))

        if len(self.hasil) > self.tampil:
            self.tombol_lanjut = t.Tombol(
                area.isi, "Tampilkan lebih banyak", BIRU, self.lebih_banyak
            )

        self.tata_katalog(paksa=True)

        if reset:
            area.ke_atas()

    def lebih_banyak(self):

        self.tampil += BATCH_KARTU
        self.bangun_katalog(reset=False)

    def tata_katalog(self, lebar=None, paksa=False):

        if self.area is None or not self.kartu:
            return

        area = self.area

        if lebar is None:
            lebar = area.lebar()

        kolom = max(1, lebar // LEBAR_KARTU)

        if kolom == self.kolom and not paksa:
            return

        for c in range(max(kolom, self.kolom) + 1):
            area.isi.grid_columnconfigure(c, weight=0, uniform="")

        for c in range(kolom):
            area.isi.grid_columnconfigure(c, weight=1, uniform="kartu")

        for i, kartu in enumerate(self.kartu):
            kartu.grid(
                row=i // kolom, column=i % kolom,
                padx=6, pady=8, sticky="n"
            )

        if self.tombol_lanjut is not None:
            baris = (len(self.kartu) + kolom - 1) // kolom
            self.tombol_lanjut.grid(
                row=baris, column=0, columnspan=kolom, pady=18
            )

        self.kolom = kolom

    def buat_kartu_buku(self, parent, b):

        ada = b["stok_tersedia"] > 0

        kartu = tk.Frame(
            parent, bg=PUTIH,
            highlightbackground=ABU_MUDA, highlightthickness=1,
            cursor="hand2"
        )

        gambar = self.app.sampul(b["id"], b["judul"], UKURAN_KARTU)

        cover = tk.Label(
            kartu, image=gambar, bg=PUTIH, bd=0, cursor="hand2"
        )
        cover.pack(padx=12, pady=(12, 8))

        judul = tk.Label(
            kartu, text=potong(b["judul"], 56),
            font=("Segoe UI", 10, "bold"), bg=PUTIH, fg=BIRU_TUA,
            wraplength=170, justify="left", anchor="nw", height=2,
            cursor="hand2"
        )
        judul.pack(fill="x", padx=12)

        penulis = tk.Label(
            kartu, text=potong(b["penulis"] or "-", 30),
            font=("Segoe UI", 9), bg=PUTIH, fg=ABU, anchor="w",
            cursor="hand2"
        )
        penulis.pack(fill="x", padx=12, pady=(2, 0))

        badge = tk.Label(
            kartu, text="●  Tersedia" if ada else "●  Habis",
            font=("Segoe UI", 8, "bold"), bg=PUTIH,
            fg=HIJAU if ada else MERAH_HEX, anchor="w", cursor="hand2"
        )
        badge.pack(fill="x", padx=12, pady=(8, 12))

        for widget in (kartu, cover, judul, penulis, badge):

            widget.bind(
                "<Button-1>", lambda e, data=b: self.app.buka_detail(data)
            )

            widget.bind(
                "<Enter>",
                lambda e, k=kartu: k.config(highlightbackground=BIRU)
            )
            widget.bind(
                "<Leave>",
                lambda e, k=kartu: k.config(highlightbackground=ABU_MUDA)
            )

        return kartu

    # ==================== PERINGATAN JADWAL ====================

    def cek_peringatan(self):

        for widget in self.peringatan.winfo_children():
            widget.destroy()

        try:
            data = JadwalPengembalian().ambil(self.app.id_anggota)
        except Exception:
            return  # peringatan bersifat tambahan; abaikan bila gagal

        r = JadwalPengembalian.ringkasan(data)

        bagian = []

        if r["terlambat"]:
            bagian.append(f"{r['terlambat']} buku terlambat dikembalikan")

        if r["segera"]:
            bagian.append(
                f"{r['segera']} buku jatuh tempo dalam {HARI_SEGERA} hari"
            )

        if not bagian:
            return

        genting = r["terlambat"] > 0

        bg = "#FEE2E2" if genting else "#FEF3C7"
        fg = "#991B1B" if genting else "#92400E"

        strip = tk.Frame(self.peringatan, bg=bg, padx=16, pady=10)
        strip.pack(fill="x", pady=(14, 0))

        tk.Label(
            strip, text="Perhatian:  " + "  dan  ".join(bagian) + ".",
            font=("Segoe UI", 9, "bold"), bg=bg, fg=fg
        ).pack(side="left")

        lihat = tk.Label(
            strip, text="Lihat jadwal  →", font=("Segoe UI", 9, "bold"),
            bg=bg, fg=fg, cursor="hand2"
        )
        lihat.pack(side="right")
        lihat.bind(
            "<Button-1>",
            lambda e: self.app.pilih_menu("Jadwal Pengembalian")
        )