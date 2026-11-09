import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import os
import tkinter as tk
from datetime import date, datetime
from tkinter import filedialog, messagebox, ttk

import tema as t

from laporan.laporan_kirim import LaporanTerkirim
from laporan.laporan_peminjaman import LaporanPeminjaman, NAMA_BULAN


# ==================== PALET WARNA (SAMA DENGAN DASHBOARD) ====================

BIRU_TUA = "#17365D"
BIRU = "#2563EB"
PUTIH = "#FFFFFF"
LATAR = "#F1F5F9"
ABU = "#64748B"
ABU_GELAP = "#334155"
ABU_MUDA = "#E2E8F0"
HIJAU = "#16A34A"
MERAH = "#DC2626"
ORANYE = "#D97706"
KUNING = "#F59E0B"

FONT = t.FONT

# kode status -> (latar baris, teks)
WARNA_BARIS = {
    "terlambat": ("#FEE2E2", "#991B1B"),
    "segera": ("#FEF3C7", "#92400E"),
    "aman": ("#FFFFFF", "#1E293B"),
    "dikembalikan": ("#DCFCE7", "#166534"),
    "dikembalikan_terlambat": ("#FFEDD5", "#9A3412"),
}


# ==================== PENGATURAN ====================

HARI_JATUH_TEMPO = 3     # "jatuh tempo" = dalam 3 hari ke depan
BATAS_BARIS = 300        # jumlah baris maksimum yang ditampilkan di tabel

# kunci lembar -> (judul kartu, warna aksen)
# Judul kartu sengaja singkat agar tidak terpotong; keterangan lengkapnya
# tampil sebagai judul tabel (lihat JUDUL_TABEL) saat kartu dipilih.
KARTU = [
    ("belum_kembali", "Belum Kembali", KUNING),
    ("terlambat", "Terlambat", MERAH),
    ("jatuh_tempo", "Jatuh Tempo", ORANYE),
    ("peminjaman", "Dipinjam", BIRU),
    ("dikembalikan", "Dikembalikan", HIJAU),
]

JUDUL_TABEL = {
    "belum_kembali": "Anggota yang Belum Mengembalikan Buku",
    "terlambat": "Peminjaman yang Terlambat Dikembalikan",
    "jatuh_tempo": f"Buku yang Jatuh Tempo dalam {HARI_JATUH_TEMPO} Hari ke Depan",
    "peminjaman": "Seluruh Peminjaman pada Bulan Ini",
    "dikembalikan": "Buku yang Dikembalikan pada Bulan Ini",
}

# (kunci data, judul kolom, lebar, rata)
_KOLOM_BELUM = [
    ("nama", "Nama Anggota", 190, "w"),
    ("telepon", "No. Telepon", 120, "w"),
    ("judul", "Judul Buku", 250, "w"),
    ("jumlah", "Jml", 55, "center"),
    ("jatuh_tempo", "Jatuh Tempo", 110, "center"),
    ("status", "Status", 150, "center"),
]

KOLOM_TABEL = {
    "belum_kembali": _KOLOM_BELUM,
    "terlambat": _KOLOM_BELUM,
    "jatuh_tempo": _KOLOM_BELUM,
    "peminjaman": [
        ("id_peminjaman", "ID Peminjaman", 125, "w"),
        ("nama", "Nama Anggota", 180, "w"),
        ("judul", "Judul Buku", 240, "w"),
        ("jumlah", "Jml", 55, "center"),
        ("tgl_pinjam", "Tgl Pinjam", 105, "center"),
        ("jatuh_tempo", "Jatuh Tempo", 110, "center"),
        ("status", "Status", 140, "center"),
    ],
    "dikembalikan": [
        ("id_peminjaman", "ID Peminjaman", 125, "w"),
        ("nama", "Nama Anggota", 180, "w"),
        ("judul", "Judul Buku", 240, "w"),
        ("jumlah", "Jml", 55, "center"),
        ("tgl_pinjam", "Tgl Pinjam", 105, "center"),
        ("kembali", "Tgl Kembali", 110, "center"),
        ("keterangan_kembali", "Keterangan", 130, "center"),
    ],
}

KUNCI_TANGGAL = {"tgl_pengajuan", "tgl_pinjam", "jatuh_tempo", "kembali"}


def format_tanggal(tanggal):
    return tanggal.strftime("%d-%m-%Y") if tanggal else "-"


def nilai_sel(baris, kunci):

    nilai = baris.get(kunci)

    if kunci in KUNCI_TANGGAL:
        return format_tanggal(nilai)

    if nilai is None or nilai == "":
        return "-"

    return str(nilai)


KOLOM_FLEKSIBEL = ("nama", "judul")


def pas_kolom(tree, kolom):
    """
    Membuat tabel pas selebar areanya (kolom paling kanan tidak terpotong).
    Hanya kolom teks panjang (nama, judul) yang melebar/menyempit; kolom
    lain (tanggal, jumlah, status) tetap pada lebarnya agar judulnya utuh.
    """

    lebar = tree.winfo_width() - 4

    if lebar < 100:
        return

    fleksibel = [k for k in kolom if k[0] in KOLOM_FLEKSIBEL]

    if not fleksibel:
        return

    tetap = sum(k[2] for k in kolom if k[0] not in KOLOM_FLEKSIBEL)
    nominal = sum(k[2] for k in fleksibel)
    sisa = max(lebar - tetap, 120 * len(fleksibel))

    for kode, _judul, w, _rata in kolom:

        if kode in KOLOM_FLEKSIBEL:
            tree.column(kode, width=max(120, int(sisa * w / nominal)))
        else:
            tree.column(kode, width=w)


def ringkas_lembar(daftar):
    """(jumlah transaksi unik, jumlah eksemplar buku, jumlah anggota unik)"""

    return (
        len({b["id_peminjaman"] for b in daftar}),
        sum(b["jumlah"] for b in daftar),
        len({b["id_anggota"] for b in daftar}),
    )


# ==================================================
# HALAMAN
# ==================================================

class HalamanLaporan:

    def __init__(self, app, induk):

        self.app = app
        self.data = None
        self.tab_aktif = "belum_kembali"
        self.kartu = {}

        try:
            t.terapkan_style(app.root)
        except Exception:
            pass  # style bawaan tetap dipakai

        t.Header(
            induk, "LAPORAN PEMINJAMAN",
            "Rekap peminjaman bulanan dan unduh dalam format Excel"
        ).pack(fill="x")

        # Pembagi: bagian atas (filter + indikator) dan tabel bisa ditarik
        pembagi = t.Pembagi(induk)
        pembagi.pack(fill="both", expand=True, padx=14, pady=(14, 14))

        self.bangun_filter(pembagi.atas_isi)
        self.bangun_pengajuan(pembagi.atas_isi)
        self.bangun_kartu(pembagi.atas_isi)
        self.bangun_tabel(pembagi.bawah)

        self.muat()

    # ==================== BAGIAN-BAGIAN HALAMAN ====================

    def bangun_filter(self, induk):

        bar = tk.Frame(
            induk, bg=PUTIH,
            highlightbackground=ABU_MUDA, highlightthickness=1
        )
        bar.pack(fill="x", padx=6)

        isi = tk.Frame(bar, bg=PUTIH, padx=16, pady=12)
        isi.pack(fill="x")

        hari_ini = date.today()

        self.var_bulan = tk.StringVar(value=NAMA_BULAN[hari_ini.month - 1])
        self.var_tahun = tk.StringVar(value=str(hari_ini.year))
        self.var_catatan = tk.StringVar()

        def label(teks):
            return tk.Label(
                isi, text=teks, bg=PUTIH, fg=ABU,
                font=(FONT, 9, "bold")
            )

        label("Bulan:").pack(side="left")

        ttk.Combobox(
            isi, textvariable=self.var_bulan, state="readonly", width=12,
            values=NAMA_BULAN, font=(FONT, 10)
        ).pack(side="left", padx=(8, 16), ipady=3)

        label("Tahun:").pack(side="left")

        ttk.Combobox(
            isi, textvariable=self.var_tahun, state="readonly", width=7,
            values=[str(y) for y in range(hari_ini.year - 5, hari_ini.year + 1)],
            font=(FONT, 10)
        ).pack(side="left", padx=(8, 16), ipady=3)

        t.Tombol(isi, "Tampilkan", BIRU, self.muat).pack(side="left")

        t.Tombol(
            isi, "Unduh Excel", HIJAU, self.unduh
        ).pack(side="right")

        t.Tombol(
            isi, "Kirim ke Operator", BIRU_TUA, self.kirim
        ).pack(side="right", padx=(0, 8))

        # Catatan opsional untuk sheet Ringkasan (+ keterangan periode di
        # kanan, di baris ini supaya tidak berebut tempat dengan tombol).
        baris2 = tk.Frame(bar, bg=PUTIH, padx=16)
        baris2.pack(fill="x", pady=(0, 12))

        self.label_acuan = tk.Label(
            baris2, text="", bg=PUTIH, fg=ABU, font=(FONT, 9)
        )
        self.label_acuan.pack(side="right", padx=(16, 0))

        tk.Label(
            baris2, text="Catatan Excel (opsional):", bg=PUTIH, fg=ABU,
            font=(FONT, 9, "bold")
        ).pack(side="left")

        tk.Entry(
            baris2, textvariable=self.var_catatan,
            font=(FONT, 10), bg=PUTIH, fg=ABU_GELAP,
            insertbackground=BIRU, relief="flat", bd=0,
            highlightthickness=1, highlightbackground="#CBD5E1",
            highlightcolor=BIRU
        ).pack(side="left", fill="x", expand=True, padx=(8, 0), ipady=4)

    def bangun_pengajuan(self, induk):

        strip = tk.Frame(induk, bg=LATAR)
        strip.pack(fill="x", padx=6, pady=(10, 0))

        tk.Label(
            strip, text="Pengajuan bulan ini:", bg=LATAR, fg=ABU_GELAP,
            font=(FONT, 9, "bold")
        ).pack(side="left")

        self.label_pengajuan = {}

        for kunci, warna_bg, warna_fg in (
            ("menunggu", "#FEF3C7", "#92400E"),
            ("disetujui", "#DCFCE7", "#166534"),
            ("ditolak", "#FEE2E2", "#991B1B"),
            ("total", "#DBEAFE", "#1D4ED8"),
        ):
            lbl = tk.Label(
                strip, text="", bg=warna_bg, fg=warna_fg,
                font=(FONT, 9, "bold"), padx=10, pady=3
            )
            lbl.pack(side="left", padx=(8, 0))

            self.label_pengajuan[kunci] = lbl

    def bangun_kartu(self, induk):
        """
        Lima kartu indikator dengan gaya yang sama seperti kartu statistik di
        halaman Petugas (t.buat_kartu): garis aksen di kiri, judul kecil,
        angka besar berwarna. Kartu bisa diklik untuk memilih isi tabel.
        """

        baris = tk.Frame(induk, bg=LATAR)
        baris.pack(fill="x", pady=(10, 10))

        for i, (kunci, judul, warna) in enumerate(KARTU):

            baris.columnconfigure(i, weight=1, uniform="kartu")

            # buat_kartu memakai pack. Kartu dibuat di induk `baris` lewat
            # induk atasnya (`induk`), lalu dipindah ke grid milik `baris`
            # supaya kelima kartu sama lebar.
            lbl_angka = t.buat_kartu(induk, judul.upper(), "–", warna)

            # Susunan buat_kartu: kartu > isi > label angka.
            isi = lbl_angka.master
            kartu = isi.master

            kartu.pack_forget()
            kartu.grid(in_=baris, row=0, column=i, sticky="nsew", padx=6)

            # Tebal bingkai tetap 2 px; warna bingkai menandai kartu aktif.
            kartu.config(highlightthickness=2, cursor="hand2")

            # Tiga baris pendek (tidak terpotong walau jendela sempit) dan
            # tinggi tetap supaya kelima kartu selalu sama tinggi.
            lbl_sub = tk.Label(
                isi, text="", bg=PUTIH, fg=ABU,
                font=(FONT, 8), anchor="w", justify="left", height=3
            )
            lbl_sub.pack(anchor="w")

            self.kartu[kunci] = {
                "frame": kartu,
                "angka": lbl_angka,
                "sub": lbl_sub,
                "warna": warna,
            }

            self._pasang_klik(kartu, kunci)

    def _pasang_klik(self, widget, kunci):

        widget.bind("<Button-1>", lambda e, k=kunci: self.pilih_tab(k))

        for anak in widget.winfo_children():
            self._pasang_klik(anak, kunci)

    def bangun_tabel(self, induk):

        panel, area = t.buat_panel(induk)
        panel.pack(fill="both", expand=True, padx=6)

        kepala = tk.Frame(area, bg=PUTIH)
        kepala.pack(fill="x", pady=(0, 12))

        tk.Frame(kepala, bg=BIRU, width=4, height=20).pack(side="left")

        self.label_judul_tabel = tk.Label(
            kepala, text="", font=(FONT, 13, "bold"), bg=PUTIH, fg=BIRU_TUA
        )
        self.label_judul_tabel.pack(side="left", padx=(8, 0))

        self.label_info_tabel = tk.Label(
            kepala, text="", bg=PUTIH, fg=ABU, font=(FONT, 9)
        )
        self.label_info_tabel.pack(side="right")

        # Kolom awal; kolom diganti setiap kali kartu lain dipilih.
        self.tree = t.buat_tabel(
            area, KOLOM_TABEL[self.tab_aktif], scroll_x=True
        )

        for kode, (bg, fg) in WARNA_BARIS.items():
            self.tree.tag_configure(kode, background=bg, foreground=fg)

        # Lebar kolom ikut lebar tabel (tidak ada kolom yang terpotong).
        self.tree.bind(
            "<Configure>",
            lambda e: pas_kolom(self.tree, KOLOM_TABEL[self.tab_aktif])
        )

    # ==================== MEMUAT DATA ====================

    def muat(self):

        bulan = NAMA_BULAN.index(self.var_bulan.get()) + 1
        tahun = int(self.var_tahun.get())

        hari_ini = date.today()

        if (tahun, bulan) > (hari_ini.year, hari_ini.month):

            messagebox.showwarning(
                "Periode Belum Berlangsung",
                "Laporan hanya dapat dibuat untuk bulan berjalan "
                "atau bulan yang sudah lewat.",
                parent=self.app.root
            )
            return

        try:
            self.data = LaporanPeminjaman().kumpulkan(
                tahun, bulan,
                hari_jatuh_tempo=HARI_JATUH_TEMPO,
                dibuat_oleh=self.app.nama,
                role=self.app.role,
            )

        except Exception as e:

            self.data = None

            messagebox.showerror(
                "Gagal Memuat Laporan",
                f"Data laporan tidak dapat diambil:\n\n{e}\n\n"
                "Jika pesannya menyebut kolom yang tidak dikenal, sesuaikan "
                "KOL_PENGAJUAN / KOL_PETUGAS di laporan_peminjaman.py.",
                parent=self.app.root
            )

            self.kosongkan()
            return

        self.tampilkan()

    def kosongkan(self):

        for kunci in self.kartu:
            self.kartu[kunci]["angka"].config(text="–")
            self.kartu[kunci]["sub"].config(text="")

        for lbl in self.label_pengajuan.values():
            lbl.config(text="")

        self.label_acuan.config(text="")
        self.tree.delete(*self.tree.get_children())
        self.label_info_tabel.config(text="")

    def tampilkan(self):

        d = self.data

        self.label_acuan.config(
            text=(
                f"Periode {d['nama_bulan']}  ·  "
                f"acuan {format_tanggal(d['acuan'])}"
            )
        )

        p = d["pengajuan"]

        self.label_pengajuan["menunggu"].config(text=f"Menunggu  {p['menunggu']}")
        self.label_pengajuan["disetujui"].config(text=f"Disetujui  {p['disetujui']}")
        self.label_pengajuan["ditolak"].config(text=f"Ditolak  {p['ditolak']}")
        self.label_pengajuan["total"].config(
            text=f"Total  {p['menunggu'] + p['disetujui'] + p['ditolak']}"
        )

        for kunci, kartu in self.kartu.items():

            transaksi, buku, anggota = ringkas_lembar(d["lembar"][kunci])

            kartu["angka"].config(text=str(transaksi))
            kartu["sub"].config(
                text=f"transaksi\n{buku} buku\n{anggota} anggota"
            )

        self.pilih_tab(self.tab_aktif)

    # ==================== TABEL ====================

    def pilih_tab(self, kunci):

        self.tab_aktif = kunci

        for k, kartu in self.kartu.items():
            kartu["frame"].config(
                highlightbackground=kartu["warna"] if k == kunci else ABU_MUDA
            )

        self.label_judul_tabel.config(text=JUDUL_TABEL[kunci])

        kolom = KOLOM_TABEL[kunci]

        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = [k[0] for k in kolom]

        for kode, judul, lebar, rata in kolom:
            self.tree.heading(kode, text=judul, anchor=rata)
            self.tree.column(kode, width=lebar, minwidth=60, anchor=rata)

        pas_kolom(self.tree, kolom)

        if self.data is None:
            return

        daftar = self.data["lembar"][kunci]

        for indeks, baris in enumerate(daftar[:BATAS_BARIS]):

            # Baris "aman" memakai warna selang-seling seperti tabel lain;
            # status lain tetap berwarna sesuai kodenya.
            if baris["kode"] == "aman":
                tag = "genap" if indeks % 2 == 0 else "ganjil"
            else:
                tag = baris["kode"]

            self.tree.insert(
                "", "end",
                values=[nilai_sel(baris, k[0]) for k in kolom],
                tags=(tag,)
            )

        if not daftar:
            self.label_info_tabel.config(text="Tidak ada data.")

        elif len(daftar) > BATAS_BARIS:
            self.label_info_tabel.config(
                text=(
                    f"Menampilkan {BATAS_BARIS} dari {len(daftar)} baris. "
                    "Unduh Excel untuk data lengkap."
                )
            )

        else:
            self.label_info_tabel.config(text=f"{len(daftar)} baris")

    # ==================== KIRIM KE OPERATOR ====================

    def kirim(self):

        if self.data is None:

            messagebox.showinfo(
                "Kirim ke Operator",
                "Tampilkan laporan terlebih dahulu.",
                parent=self.app.root
            )
            return

        d = self.data

        if not messagebox.askyesno(
            "Kirim ke Operator",
            f"Kirim laporan {d['nama_bulan']} ke operator?\n\n"
            "Operator dapat membukanya sebagai file Excel di menu "
            "Laporan Masuk.",
            parent=self.app.root
        ):
            return

        try:
            from laporan.laporan_excel import buat_excel

        except ImportError as e:

            messagebox.showerror(
                "Pembuat Excel Belum Siap",
                f"{e}\n\nPastikan file excel_laporan.py ada di folder laporan/ "
                "dan pustaka openpyxl terpasang:\n\npip install openpyxl",
                parent=self.app.root
            )
            return

        catatan = self.var_catatan.get().strip()

        data = dict(d)
        data["catatan"] = catatan
        data["dibuat_pada"] = datetime.now()

        nama_file = f"Laporan_Peminjaman_{d['tahun']}-{d['bulan']:02d}.xlsx"

        try:
            LaporanTerkirim().kirim(
                d["tahun"], d["bulan"], nama_file, buat_excel(data),
                catatan, self.app.id_petugas, self.app.nama
            )

        except Exception as e:

            messagebox.showerror(
                "Gagal Mengirim",
                f"Laporan tidak dapat dikirim:\n\n{e}",
                parent=self.app.root
            )
            return

        messagebox.showinfo(
            "Terkirim",
            f"Laporan {d['nama_bulan']} sudah dikirim ke operator.",
            parent=self.app.root
        )

    # ==================== UNDUH EXCEL ====================

    def unduh(self):

        if self.data is None:

            messagebox.showinfo(
                "Unduh Excel",
                "Tampilkan laporan terlebih dahulu.",
                parent=self.app.root
            )
            return

        try:
            from laporan.laporan_excel import buat_excel

        except ImportError as e:

            messagebox.showerror(
                "Pembuat Excel Belum Siap",
                f"{e}\n\nPastikan file excel_laporan.py ada di folder laporan/ "
                "dan pustaka openpyxl terpasang:\n\npip install openpyxl",
                parent=self.app.root
            )
            return

        nama_awal = (
            f"Laporan_Peminjaman_{self.data['tahun']}-"
            f"{self.data['bulan']:02d}.xlsx"
        )

        lokasi = filedialog.asksaveasfilename(
            parent=self.app.root,
            title="Simpan Laporan Excel",
            defaultextension=".xlsx",
            initialfile=nama_awal,
            filetypes=[("Excel Workbook", "*.xlsx")]
        )

        if not lokasi:
            return

        data = dict(self.data)
        data["catatan"] = self.var_catatan.get().strip()
        data["dibuat_pada"] = datetime.now()

        try:
            Path(lokasi).write_bytes(buat_excel(data))

        except PermissionError:

            messagebox.showerror(
                "Gagal Menyimpan",
                "File tidak dapat ditulis. Jika file tersebut sedang dibuka "
                "di Excel, tutup dulu lalu coba lagi.",
                parent=self.app.root
            )
            return

        except Exception as e:

            messagebox.showerror(
                "Gagal Membuat Excel",
                f"Laporan tidak dapat dibuat:\n\n{e}",
                parent=self.app.root
            )
            return

        if messagebox.askyesno(
            "Laporan Tersimpan",
            f"Laporan berhasil disimpan:\n{lokasi}\n\nBuka sekarang?",
            parent=self.app.root
        ):
            try:
                os.startfile(lokasi)  # Windows
            except (AttributeError, OSError):
                pass