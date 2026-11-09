import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
    
import tkinter as tk
from tkinter import messagebox

from peminjaman.peminjaman import Peminjaman
from detail_peminjaman.app_detail_peminjaman import AppDetailPeminjaman
from peminjaman.struk_peminjaman import StrukPeminjaman
import tema as t
from tema import (
    BIRU, BIRU_TUA, HIJAU, MERAH, ORANYE, ABU, PUTIH, LATAR
)


# ==================================================
# HALAMAN UTAMA PEMINJAMAN
# ==================================================

class AppPeminjaman:
    """
    hanya_lihat=False : petugas  -> CRUD penuh
    hanya_lihat=True  : operator -> hanya melihat daftar dan detail
    """

    def __init__(self, root, id_petugas, hanya_lihat=False):

        self.root = root
        t.atur_jendela(
            root, "Sistem Perpustakaan - Data Peminjaman",
            "1180x740", (1020, 640)
        )

        self.model = Peminjaman(hanya_lihat=hanya_lihat)
        self.id_petugas = id_petugas
        self.hanya_lihat = hanya_lihat
        self.id_terpilih = None

        # Referensi jendela detail peminjaman
        self.jendela_detail = None

        self.buat_tampilan()
        self.muat_data()

    # ==================== TAMPILAN ====================

    def buat_tampilan(self):

        t.Header(
            self.root,
            "DATA PEMINJAMAN",
            "Daftar transaksi peminjaman buku (hanya dapat dilihat)"
            if self.hanya_lihat else
            "Kelola transaksi peminjaman buku perpustakaan"
        ).pack(fill="x")

        # ==================== STATISTIK ====================

        # Pembagi: bagian atas (statistik + form) dan tabel bisa ditarik
        pembagi = t.Pembagi(self.root)
        pembagi.pack(fill="both", expand=True, padx=14, pady=(14, 14))

        statistik = tk.Frame(pembagi.atas_isi, bg=LATAR)
        statistik.pack(fill="x", pady=(0, 10))

        self.label_total = t.buat_kartu(
            statistik, "TOTAL PEMINJAMAN", "0", BIRU
        )
        self.label_menunggu = t.buat_kartu(
            statistik, "MENUNGGU", "0", ORANYE
        )
        self.label_dipinjam = t.buat_kartu(
            statistik, "DIPINJAM", "0", HIJAU
        )
        self.label_ditolak = t.buat_kartu(
            statistik, "DITOLAK", "0", MERAH
        )
        self.label_selesai = t.buat_kartu(
            statistik, "SELESAI", "0", BIRU_TUA
        )

        # ==================== KONTEN ====================

        konten = pembagi.atas_isi

        self.var_anggota = tk.StringVar()

        if self.hanya_lihat:
            self.buat_panel_lihat(konten)
        else:
            self.buat_form(konten)

        # ==================== TABEL ====================

        panel_tabel, area_tabel = t.buat_panel(pembagi.bawah)
        panel_tabel.pack(fill="both", expand=True, padx=6)

        self.var_cari = tk.StringVar()
        t.buat_pencarian(
            area_tabel, "Daftar Transaksi Peminjaman",
            self.var_cari, self.muat_data
        )

        self.tabel = t.buat_tabel(
            area_tabel,
            [
                ("id", "ID Peminjaman", 130, "center"),
                ("anggota", "Nama Anggota", 190, "w"),
                ("petugas", "Petugas", 160, "w"),
                ("pengajuan", "Tanggal Pengajuan", 150, "center"),
                ("pinjam", "Tanggal Pinjam", 150, "center"),
                ("status", "Status Peminjaman", 150, "center"),
            ]
        )

        # Warna status
        self.tabel.tag_configure("menunggu", foreground=ORANYE)
        self.tabel.tag_configure("dipinjam", foreground=HIJAU)
        self.tabel.tag_configure("ditolak", foreground=MERAH)
        self.tabel.tag_configure("selesai", foreground=BIRU_TUA)

        self.tabel.bind("<<TreeviewSelect>>", self.pilih_data)

        self.atur_tombol(None)

    # ---------- form (petugas: CRUD penuh) ----------

    def buat_form(self, konten):

        panel_form, form = t.buat_panel(
            konten, "Form Transaksi Peminjaman"
        )
        panel_form.pack(fill="x", padx=6)

        t.buat_field(form, "ID Anggota", self.var_anggota, 0, 0)
        form.grid_columnconfigure(0, minsize=300)

        tombol = tk.Frame(form, bg=PUTIH)
        tombol.grid(row=0, column=1, sticky="sw", padx=10, pady=(0, 10))

        t.Tombol(
            tombol, "Tambah", HIJAU, self.tambah
        ).pack(side="left", padx=4)

        self.btn_detail = t.Tombol(
            tombol, "Detail Peminjaman", BIRU, self.buka_detail
        )
        self.btn_detail.pack(side="left", padx=4)

        self.btn_proses = t.Tombol(
            tombol, "Proses Peminjaman", HIJAU, self.proses_peminjaman
        )
        self.btn_proses.pack(side="left", padx=4)

        self.btn_tolak = t.Tombol(
            tombol, "Tolak", MERAH, self.tolak
        )
        self.btn_tolak.pack(side="left", padx=4)

        self.btn_hapus = t.Tombol(
            tombol, "Hapus", ABU, self.hapus
        )
        self.btn_hapus.pack(side="left", padx=4)

        t.Tombol(
            tombol, "Bersihkan", ABU, self.bersihkan
        ).pack(side="left", padx=4)

    # ---------- panel lihat (operator: hanya melihat) ----------

    def buat_panel_lihat(self, konten):

        panel, isi = t.buat_panel(konten, "Transaksi Terpilih")
        panel.pack(fill="x", padx=6)

        isi.grid_columnconfigure(0, weight=1)

        self.var_info = tk.StringVar()

        tk.Label(
            isi, textvariable=self.var_info, anchor="w",
            bg=PUTIH, fg="#334155", font=("Segoe UI", 10)
        ).grid(row=0, column=0, sticky="w", padx=6, pady=(0, 10))

        self.btn_detail = t.Tombol(
            isi, "Lihat Detail Peminjaman", BIRU, self.buka_detail
        )
        self.btn_detail.grid(row=0, column=1, sticky="e", padx=6, pady=(0, 10))

        self.perbarui_info(None)

    def perbarui_info(self, nilai):
        """Teks ringkasan transaksi terpilih (hanya mode lihat)."""

        if not self.hanya_lihat:
            return

        if nilai is None:
            self.var_info.set(
                "Pilih transaksi pada tabel untuk melihat detailnya."
            )
        else:
            self.var_info.set(
                f"{nilai[0]}   ·   {nilai[1]}   ·   status: {nilai[5]}"
            )

    # ==================== MENGATUR TOMBOL ====================

    def atur_tombol(self, status):

        self.btn_detail.config(state="disabled")

        if not self.hanya_lihat:
            self.btn_proses.config(state="disabled")
            self.btn_tolak.config(state="disabled")
            self.btn_hapus.config(state="disabled")

        if status is None:
            return

        # Semua role boleh melihat detail
        self.btn_detail.config(state="normal")

        if self.hanya_lihat:
            return

        if str(status).lower() == "menunggu":

            self.btn_proses.config(state="normal")
            self.btn_tolak.config(state="normal")
            self.btn_hapus.config(state="normal")

    # ==================== MEMUAT DATA ====================

    def muat_data(self):

        try:
            data = self.model.tampilkan(
                self.var_cari.get()
            )

            for item in self.tabel.get_children():
                self.tabel.delete(item)

            self.id_terpilih = None
            self.var_anggota.set("")

            self.atur_tombol(None)
            self.perbarui_info(None)

            for indeks, baris in enumerate(data):

                tag_baris = (
                    "genap" if indeks % 2 == 0 else "ganjil"
                )

                status = str(baris[5]).lower()

                self.tabel.insert(
                    "",
                    "end",
                    values=tuple(
                        "-" if nilai is None else nilai
                        for nilai in baris
                    ),
                    tags=(tag_baris, status)
                )

            self.muat_statistik()

        except Exception as e:
            messagebox.showerror(
                "Kesalahan",
                f"Gagal memuat data peminjaman:\n{e}",
                parent=self.root
            )

    def muat_statistik(self):

        data = self.model.statistik()

        self.label_total.config(text=str(data["total"]))
        self.label_menunggu.config(text=str(data["menunggu"]))
        self.label_dipinjam.config(text=str(data["dipinjam"]))
        self.label_ditolak.config(text=str(data["ditolak"]))
        self.label_selesai.config(text=str(data["selesai"]))

    # ==================== MEMILIH DATA ====================

    def pilih_data(self, event=None):

        pilihan = self.tabel.selection()

        if not pilihan:
            self.id_terpilih = None
            self.var_anggota.set("")
            self.atur_tombol(None)
            self.perbarui_info(None)
            return

        nilai = self.tabel.item(
            pilihan[0],
            "values"
        )

        self.id_terpilih = nilai[0]

        status = nilai[5]

        self.atur_tombol(status)
        self.perbarui_info(nilai)

        try:
            self.var_anggota.set(
                self.ambil_id_anggota(self.id_terpilih)
            )

        except Exception as e:
            messagebox.showerror(
                "Kesalahan",
                f"Gagal mengambil ID anggota:\n{e}",
                parent=self.root
            )

    def ambil_id_anggota(self, id_peminjaman):

        conn = self.model.db.hubungkan()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT anggota_id
                FROM peminjaman
                WHERE id_peminjaman = %s
            """, (id_peminjaman,))

            hasil = cursor.fetchone()

            return hasil[0] if hasil else ""

        finally:
            cursor.close()
            conn.close()

    # ==================== MENGELOLA JENDELA DETAIL ====================

    def tutup_jendela_detail(self, id_peminjaman=None):

        if self.jendela_detail is None:
            return

        try:
            if self.jendela_detail.window.winfo_exists():

                if (
                    id_peminjaman is not None
                    and self.jendela_detail.id_peminjaman
                    != id_peminjaman
                ):
                    return

                self.jendela_detail.tutup()

        except tk.TclError:
            pass

        self.jendela_detail = None

    # ==================== MENAMBAHKAN PEMINJAMAN ====================

    def tambah(self):

        try:
            id_baru = self.model.tambah(
                self.var_anggota.get()
            )

            messagebox.showinfo(
                "Berhasil",
                f"Transaksi peminjaman berhasil dibuat.\n"
                f"ID: {id_baru}\n\n"
                "Silakan tambahkan buku melalui Detail Peminjaman.",
                parent=self.root
            )

            self.muat_data()

        except Exception as e:
            messagebox.showerror(
                "Gagal Menambahkan Peminjaman",
                str(e),
                parent=self.root
            )

    # ==================== MEMBUKA DETAIL PEMINJAMAN ====================

    def buka_detail(self):

        if not self.id_terpilih:
            messagebox.showwarning(
                "Peringatan",
                "Pilih transaksi peminjaman terlebih dahulu.",
                parent=self.root
            )
            return

        try:

            if self.jendela_detail is not None:

                if self.jendela_detail.window.winfo_exists():

                    if (
                        self.jendela_detail.id_peminjaman
                        == self.id_terpilih
                    ):

                        self.jendela_detail.window.deiconify()
                        self.jendela_detail.window.lift()
                        self.jendela_detail.window.focus_force()

                        return

                    self.tutup_jendela_detail()

                else:
                    self.jendela_detail = None

            opsi = {"callback": self.muat_data}

            # Operator: jendela detail dibuka tanpa tombol pengubah data
            if self.hanya_lihat:
                opsi["hanya_lihat"] = True

            try:
                self.jendela_detail = AppDetailPeminjaman(
                    self.root,
                    self.id_terpilih,
                    **opsi
                )

            except TypeError as e:

                # File detail lama belum mengenal mode hanya lihat:
                # jangan buka jendela yang bisa mengubah data.
                if self.hanya_lihat and "hanya_lihat" in str(e):
                    raise RuntimeError(
                        "Jendela detail belum mendukung mode hanya lihat. "
                        "Perbarui app_detail_peminjaman.py."
                    )

                raise

        except Exception as e:

            self.jendela_detail = None

            messagebox.showerror(
                "Kesalahan",
                f"Gagal membuka detail peminjaman:\n{e}",
                parent=self.root
            )

    # ==================== MEMPROSES PEMINJAMAN ====================

    def proses_peminjaman(self):

        if not self.id_terpilih:
            messagebox.showwarning(
                "Peringatan",
                "Pilih transaksi peminjaman terlebih dahulu.",
                parent=self.root
            )
            return

        id_peminjaman = self.id_terpilih

        konfirmasi = messagebox.askyesno(
            "Konfirmasi",
            f"Yakin ingin memproses peminjaman {id_peminjaman}?\n\n"
            "Pastikan seluruh buku sudah dimasukkan ke dalam detail "
            "peminjaman dan buku akan diserahkan kepada anggota.",
            parent=self.root
        )

        if not konfirmasi:
            return

        # TAHAP 1: PROSES TRANSAKSI DATABASE

        try:

            self.model.proses_peminjaman(
                id_peminjaman,
                self.id_petugas
            )

        except Exception as e:

            messagebox.showerror(
                "Gagal Memproses Peminjaman",
                str(e),
                parent=self.root
            )
            return

        # TAHAP 2: MEMPERBARUI TAMPILAN

        self.tutup_jendela_detail(id_peminjaman)

        self.muat_data()

        messagebox.showinfo(
            "Berhasil",
            f"Peminjaman {id_peminjaman} berhasil diproses.\n"
            "Stok buku telah diperbarui dan tanggal jatuh tempo "
            "telah ditentukan.",
            parent=self.root
        )

        # TAHAP 3: MEMBUAT STRUK PEMINJAMAN

        try:

            struk = StrukPeminjaman()

            struk.buka_struk(id_peminjaman)

        except Exception as e:

            messagebox.showwarning(
                "Struk Tidak Berhasil Dibuat",
                "Transaksi peminjaman berhasil diproses, "
                "tetapi struk gagal dibuat.\n\n"
                f"Detail kesalahan:\n{e}",
                parent=self.root
            )

    # ==================== MENOLAK PEMINJAMAN ====================

    def tolak(self):

        if not self.id_terpilih:
            messagebox.showwarning(
                "Peringatan",
                "Pilih transaksi peminjaman terlebih dahulu.",
                parent=self.root
            )
            return

        id_peminjaman = self.id_terpilih

        konfirmasi = messagebox.askyesno(
            "Konfirmasi",
            f"Yakin ingin menolak {id_peminjaman}?",
            parent=self.root
        )

        if not konfirmasi:
            return

        try:

            self.model.tolak(
                id_peminjaman,
                self.id_petugas
            )

            self.tutup_jendela_detail(id_peminjaman)

            self.muat_data()

            messagebox.showinfo(
                "Berhasil",
                "Pengajuan peminjaman berhasil ditolak.",
                parent=self.root
            )

        except Exception as e:

            messagebox.showerror(
                "Gagal Menolak",
                str(e),
                parent=self.root
            )

    # ==================== MENGHAPUS PEMINJAMAN ====================

    def hapus(self):

        if not self.id_terpilih:
            messagebox.showwarning(
                "Peringatan",
                "Pilih transaksi peminjaman terlebih dahulu.",
                parent=self.root
            )
            return

        id_peminjaman = self.id_terpilih

        konfirmasi = messagebox.askyesno(
            "Konfirmasi",
            f"Yakin ingin menghapus {id_peminjaman}?",
            parent=self.root
        )

        if not konfirmasi:
            return

        try:

            self.model.hapus(id_peminjaman)

            self.tutup_jendela_detail(id_peminjaman)

            self.muat_data()

            messagebox.showinfo(
                "Berhasil",
                "Transaksi peminjaman berhasil dihapus.",
                parent=self.root
            )

        except Exception as e:

            messagebox.showerror(
                "Gagal Menghapus",
                str(e),
                parent=self.root
            )

    # ==================== MEMBERSIHKAN FORM ====================

    def bersihkan(self):

        self.id_terpilih = None
        self.var_anggota.set("")

        for pilihan in self.tabel.selection():
            self.tabel.selection_remove(pilihan)

        self.atur_tombol(None)


# ==================================================
# MENJALANKAN PROGRAM
# ==================================================

if __name__ == "__main__":

    root = tk.Tk()

    app = AppPeminjaman(
        root,
        id_petugas="PTG001"
    )

    root.mainloop()