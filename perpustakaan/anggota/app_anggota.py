import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import tkinter as tk
from tkinter import messagebox

from anggota.anggota import Anggota
import tema as t
from tema import BIRU, HIJAU, MERAH, ORANYE, ABU, PUTIH, LATAR, FONT

class AppAnggota:
    def __init__(self, root):
        self.root = root
        t.atur_jendela(
            root, "Sistem Perpustakaan - Data Anggota",
            "1100x720", (980, 620)
        )

        self.model = Anggota()
        self.id_terpilih = None

        self.buat_tampilan()
        self.muat_data()

    # ==================== TAMPILAN ====================
    def buat_tampilan(self):
        t.Header(
            self.root, "DATA ANGGOTA", "Kelola data anggota perpustakaan"
        ).pack(fill="x")
        # Kartu statistik
        # Pembagi: bagian atas (statistik + form) dan tabel bisa ditarik
        pembagi = t.Pembagi(self.root)
        pembagi.pack(fill="both", expand=True, padx=14, pady=(14, 14))
        statistik = tk.Frame(pembagi.atas_isi, bg=LATAR)
        statistik.pack(fill="x", pady=(0, 10))
        self.label_total = t.buat_kartu(
            statistik, "TOTAL ANGGOTA", "0", BIRU
        )
        self.label_akun = t.buat_kartu(
            statistik, "ANGGOTA DENGAN AKUN", "0", HIJAU
        )
        self.label_tanpa_akun = t.buat_kartu(
            statistik, "ANGGOTA TANPA AKUN", "0", ORANYE
        )

        # Konten utama
        konten = pembagi.atas_isi

        # Form anggota
        panel_form, form = t.buat_panel(konten, "Form Data Anggota")
        panel_form.pack(fill="x", padx=6)

        self.var_nama = tk.StringVar()
        self.var_alamat = tk.StringVar()
        self.var_telepon = tk.StringVar()
        self.var_username = tk.StringVar()
        self.var_password = tk.StringVar()

        daftar_field = [
            ("Nama Anggota *", self.var_nama, False),
            ("Alamat", self.var_alamat, False),
            ("Nomor Telepon", self.var_telepon, False),
            ("Username (opsional)", self.var_username, False),
            ("Password (opsional)", self.var_password, True),
        ]

        for kolom, (judul, variabel, rahasia) in enumerate(daftar_field):
            t.buat_field(
                form, judul, variabel, 0, kolom,
                show="*" if rahasia else ""
            )

        t.rata(form, len(daftar_field))

        tk.Label(
            form,
            text="Saat mengubah data, kosongkan password jika tidak ingin menggantinya.",
            bg=PUTIH,
            fg=ABU,
            font=(FONT, 9)
        ).grid(
            row=1, column=0, columnspan=5,
            sticky="w", padx=6, pady=(0, 10)
        )

        # Tombol CRUD
        tombol = tk.Frame(form, bg=PUTIH)
        tombol.grid(row=2, column=0, columnspan=5, sticky="w")

        t.Tombol(tombol, "Tambah", HIJAU, self.tambah).pack(side="left", padx=(6, 4))
        t.Tombol(tombol, "Ubah", BIRU, self.ubah).pack(side="left", padx=4)
        t.Tombol(tombol, "Hapus", MERAH, self.hapus).pack(side="left", padx=4)
        t.Tombol(tombol, "Bersihkan", ABU, self.bersihkan).pack(side="left", padx=4)

        # Tabel data anggota
        panel_tabel, area_tabel = t.buat_panel(pembagi.bawah)
        panel_tabel.pack(fill="both", expand=True, padx=6)

        self.var_cari = tk.StringVar()
        t.buat_pencarian(
            area_tabel, "Daftar Anggota", self.var_cari, self.muat_data
        )

        self.tabel = t.buat_tabel(
            area_tabel,
            [
                ("id_anggota", "ID Anggota", 100, "center"),
                ("nama", "Nama Anggota", 170, "w"),
                ("alamat", "Alamat", 220, "w"),
                ("no_telepon", "Nomor Telepon", 140, "w"),
                ("username", "Username", 140, "w"),
                ("tanggal_daftar", "Tanggal Daftar", 140, "center"),
            ],
            scroll_x=True
        )

        self.tabel.bind("<<TreeviewSelect>>", self.pilih_data)

    # ==================== DATA ====================

    def ambil_form(self):
        return {
            "nama": self.var_nama.get().strip(),
            "alamat": self.var_alamat.get().strip(),
            "no_telepon": self.var_telepon.get().strip(),
            "username": self.var_username.get().strip(),
            "password": self.var_password.get()
        }

    def muat_data(self):
        try:
            data = self.model.tampilkan(self.var_cari.get())

            for item in self.tabel.get_children():
                self.tabel.delete(item)

            for indeks, baris in enumerate(data):
                tag = "genap" if indeks % 2 == 0 else "ganjil"
                self.tabel.insert(
                    "",
                    "end",
                    values=tuple("" if nilai is None else nilai for nilai in baris),
                    tags=(tag,)
                )

            semua = self.model.tampilkan("")
            jumlah_akun = sum(1 for baris in semua if len(baris) > 4 and baris[4])
            jumlah_tanpa_akun = len(semua) - jumlah_akun

            self.label_total.config(text=str(len(semua)))
            self.label_akun.config(text=str(jumlah_akun))
            self.label_tanpa_akun.config(text=str(jumlah_tanpa_akun))

        except Exception as e:
            messagebox.showerror(
                "Kesalahan",
                f"Gagal memuat data anggota:\n{e}"
            )

    def tambah(self):
        try:
            data = self.ambil_form()
            if not data["nama"]:
                messagebox.showwarning(
                    "Data Belum Lengkap",
                    "Nama anggota wajib diisi."
                )
                return

            id_baru = self.model.tambah(data)
            messagebox.showinfo(
                "Berhasil",
                f"Data anggota berhasil ditambahkan.\nID: {id_baru}"
            )
            self.bersihkan()
            self.muat_data()

        except Exception as e:
            messagebox.showerror(
                "Gagal Menambahkan Anggota",
                str(e)
            )

    def pilih_data(self, event=None):
        pilihan = self.tabel.selection()
        if not pilihan:
            return

        nilai = self.tabel.item(pilihan[0], "values")
        if not nilai:
            return

        self.id_terpilih = nilai[0]
        self.var_nama.set(nilai[1])
        self.var_alamat.set(nilai[2])
        self.var_telepon.set(nilai[3])
        self.var_username.set(nilai[4])
        # Password sengaja dikosongkan demi keamanan.
        self.var_password.set("")

    def ubah(self):
        if not self.id_terpilih:
            messagebox.showwarning(
                "Peringatan",
                "Pilih data anggota yang ingin diubah."
            )
            return

        try:
            data = self.ambil_form()
            if not data["nama"]:
                messagebox.showwarning(
                    "Data Belum Lengkap",
                    "Nama anggota wajib diisi."
                )
                return

            self.model.ubah(self.id_terpilih, data)
            messagebox.showinfo(
                "Berhasil",
                "Data anggota berhasil diperbarui."
            )
            self.bersihkan()
            self.muat_data()

        except Exception as e:
            messagebox.showerror(
                "Gagal Mengubah Anggota",
                str(e)
            )

    def hapus(self):
        if not self.id_terpilih:
            messagebox.showwarning(
                "Peringatan",
                "Pilih data anggota yang ingin dihapus."
            )
            return

        konfirmasi = messagebox.askyesno(
            "Konfirmasi",
            f"Yakin ingin menghapus anggota {self.id_terpilih}?"
        )
        if not konfirmasi:
            return

        try:
            self.model.hapus(self.id_terpilih)
            messagebox.showinfo(
                "Berhasil",
                "Data anggota berhasil dihapus."
            )
            self.bersihkan()
            self.muat_data()

        except Exception as e:
            messagebox.showerror(
                "Gagal Menghapus Anggota",
                "Anggota mungkin masih digunakan oleh data peminjaman.\n\n"
                f"Detail: {e}"
            )

    def bersihkan(self):
        self.id_terpilih = None
        self.var_nama.set("")
        self.var_alamat.set("")
        self.var_telepon.set("")
        self.var_username.set("")
        self.var_password.set("")

        for pilihan in self.tabel.selection():
            self.tabel.selection_remove(pilihan)


if __name__ == "__main__":
    root = tk.Tk()
    app = AppAnggota(root)
    root.mainloop()