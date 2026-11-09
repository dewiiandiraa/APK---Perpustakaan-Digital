import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import os
import tkinter as tk
from tkinter import messagebox

import tema as t

from laporan.laporan_kirim import (
    LaporanTerkirim, folder_unduhan, lokasi_unik
)
from laporan.laporan_peminjaman import NAMA_BULAN


BIRU_TUA = "#17365D"
BIRU = "#2563EB"
PUTIH = "#FFFFFF"
LATAR = "#F1F5F9"
ABU = "#64748B"
ABU_MUDA = "#E2E8F0"
HIJAU = "#16A34A"

FONT = t.FONT

KOLOM = [
    ("periode", "Periode", 140, "w"),
    ("pengirim", "Dikirim Oleh", 150, "w"),
    ("waktu", "Dikirim Pada", 150, "center"),
    ("catatan", "Catatan", 260, "w"),
    ("ukuran", "Ukuran", 80, "center"),
    ("status", "Status", 120, "center"),
]


KOLOM_FLEKSIBEL = ("pengirim", "catatan")


def pas_kolom(tree, kolom):
    """
    Membuat tabel pas selebar areanya (kolom paling kanan tidak terpotong).
    Hanya kolom teks (pengirim, catatan) yang melebar/menyempit; kolom
    lain tetap pada lebarnya agar judul kolomnya utuh.
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


def format_waktu(nilai):
    return nilai.strftime("%d-%m-%Y %H:%M") if nilai else "-"


def format_ukuran(byte):

    if byte < 1024 * 1024:
        return f"{max(1, round(byte / 1024))} KB"

    return f"{byte / (1024 * 1024):.1f} MB"


class HalamanLaporanMasuk:

    def __init__(self, app, induk):

        self.app = app
        self.model = LaporanTerkirim()
        self.daftar = {}

        try:
            t.terapkan_style(app.root)
        except Exception:
            pass

        t.Header(
            induk, "LAPORAN MASUK",
            "Laporan peminjaman yang dikirim petugas, siap dibuka di Excel"
        ).pack(fill="x")

        # Pembagi: bagian atas (tombol) dan tabel bisa ditarik
        pembagi = t.Pembagi(induk)
        pembagi.pack(fill="both", expand=True, padx=14, pady=(14, 14))

        self.bangun_tombol(pembagi.atas_isi)
        self.bangun_tabel(pembagi.bawah)

        self.muat()

    # ==================== BAGIAN-BAGIAN HALAMAN ====================

    def bangun_tombol(self, induk):

        panel, isi = t.buat_panel(induk, "Laporan dari Petugas")
        panel.pack(fill="x", padx=6)

        baris = tk.Frame(isi, bg=PUTIH)
        baris.pack(fill="x")

        t.Tombol(
            baris, "Unduh & Buka di Excel", HIJAU, self.unduh_terpilih
        ).pack(side="left")

        t.Tombol(
            baris, "Unduh Semua yang Baru", BIRU, self.unduh_baru
        ).pack(side="left", padx=10)

        t.Tombol(
            baris, "Muat Ulang", BIRU_TUA, self.muat
        ).pack(side="right")

        self.label_jumlah = tk.Label(
            baris, text="", bg=PUTIH, fg=ABU, font=(FONT, 9)
        )
        self.label_jumlah.pack(side="right", padx=16)

    def bangun_tabel(self, induk):

        panel, area = t.buat_panel(induk)
        panel.pack(fill="both", expand=True, padx=6)

        kepala = tk.Frame(area, bg=PUTIH)
        kepala.pack(fill="x", pady=(0, 12))

        tk.Frame(kepala, bg=BIRU, width=4, height=20).pack(side="left")
        tk.Label(
            kepala, text="Daftar Laporan Masuk",
            font=(FONT, 13, "bold"), bg=PUTIH, fg=BIRU_TUA
        ).pack(side="left", padx=(8, 0))

        # Keterangan lokasi simpan: dipasang sebelum tabel supaya selalu
        # terlihat di bawah panel, berapa pun tinggi tabelnya.
        self.label_status = tk.Label(
            area, text="", bg=PUTIH, fg=ABU, font=(FONT, 9),
            anchor="w", justify="left"
        )
        self.label_status.pack(side="bottom", fill="x", pady=(8, 0))

        self.tree = t.buat_tabel(area, KOLOM, scroll_x=True)

        # Laporan yang belum dibuka: huruf tebal berwarna biru. Warna latar
        # tidak diubah supaya baris selang-seling dan baris terpilih tetap
        # terlihat jelas.
        self.tree.tag_configure(
            "baru", foreground=BIRU, font=(FONT, 10, "bold")
        )

        # Lebar kolom ikut lebar tabel (tidak ada kolom yang terpotong).
        self.tree.bind("<Configure>", lambda e: pas_kolom(self.tree, KOLOM))

        self.tree.bind("<Double-1>", lambda e: self.unduh_terpilih())

    # ==================== DAFTAR ====================

    def muat(self):

        try:
            data = self.model.daftar()

        except Exception as e:

            messagebox.showerror(
                "Gagal Memuat",
                f"Daftar laporan tidak dapat diambil:\n\n{e}",
                parent=self.app.root
            )
            return

        self.daftar = {str(d["id"]): d for d in data}

        self.tree.delete(*self.tree.get_children())

        for indeks, d in enumerate(data):

            baru = d["dibaca_pada"] is None

            zebra = "genap" if indeks % 2 == 0 else "ganjil"
            tag = (zebra, "baru") if baru else (zebra,)

            self.tree.insert(
                "", "end", iid=str(d["id"]),
                values=[
                    f"{NAMA_BULAN[d['bulan'] - 1]} {d['tahun']}",
                    d["pengirim"],
                    format_waktu(d["dikirim_pada"]),
                    d["catatan"] or "-",
                    format_ukuran(d["ukuran"]),
                    "● Baru" if baru else "Sudah dibuka",
                ],
                tags=tag
            )

        baru_n = sum(1 for d in data if d["dibaca_pada"] is None)

        self.label_jumlah.config(
            text=f"{len(data)} laporan  ·  {baru_n} baru"
        )

        if not data:
            self.label_status.config(
                text="Belum ada laporan yang dikirim petugas."
            )

    # ==================== UNDUH ====================

    def _simpan(self, id_laporan):
        """Simpan satu laporan ke folder Downloads, tandai sudah dibuka."""

        nama_file, isi = self.model.ambil_file(id_laporan)

        lokasi = lokasi_unik(folder_unduhan(), nama_file)
        lokasi.write_bytes(isi)

        self.model.tandai_dibaca(id_laporan, self.app.nama)

        return lokasi

    def unduh_terpilih(self):

        terpilih = self.tree.selection()

        if not terpilih:

            messagebox.showinfo(
                "Unduh Laporan",
                "Pilih laporan yang ingin dibuka terlebih dahulu.",
                parent=self.app.root
            )
            return

        try:
            lokasi = self._simpan(int(terpilih[0]))

        except Exception as e:

            messagebox.showerror(
                "Gagal Mengunduh",
                f"Laporan tidak dapat disimpan:\n\n{e}",
                parent=self.app.root
            )
            return

        self.label_status.config(text=f"Tersimpan di: {lokasi}")

        self.muat()
        self.tree.selection_set(terpilih[0])

        try:
            os.startfile(lokasi)  # Windows: buka di Excel
        except (AttributeError, OSError):
            messagebox.showinfo(
                "Laporan Tersimpan",
                f"Laporan tersimpan di:\n{lokasi}",
                parent=self.app.root
            )

    def unduh_baru(self):

        baru = [d for d in self.daftar.values() if d["dibaca_pada"] is None]

        if not baru:

            messagebox.showinfo(
                "Unduh Laporan",
                "Tidak ada laporan baru.",
                parent=self.app.root
            )
            return

        tersimpan, gagal = [], []

        for d in baru:

            try:
                tersimpan.append(self._simpan(d["id"]))

            except Exception as e:
                gagal.append(f"{d['nama_file']}: {e}")

        self.muat()

        folder = folder_unduhan()

        pesan = f"{len(tersimpan)} laporan disimpan di:\n{folder}"

        if gagal:
            pesan += "\n\nGagal:\n" + "\n".join(gagal)

        self.label_status.config(
            text=f"{len(tersimpan)} laporan baru tersimpan di: {folder}"
        )

        if tersimpan and messagebox.askyesno(
            "Selesai", pesan + "\n\nBuka folder sekarang?",
            parent=self.app.root
        ):
            try:
                os.startfile(folder)  # Windows
            except (AttributeError, OSError):
                pass

        elif not tersimpan:
            messagebox.showerror("Gagal", pesan, parent=self.app.root)