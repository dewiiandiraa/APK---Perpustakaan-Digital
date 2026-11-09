import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import tkinter as tk
from tkinter import messagebox

from petugas.petugas import Petugas
import tema as t
from tema import BIRU, HIJAU, MERAH, ORANYE, ABU, LATAR


class AppPetugas:
    def __init__(self, root, hanya_lihat=False, id_sendiri=None):
        self.root = root
        t.atur_jendela(
            root, "Sistem Perpustakaan - Data Petugas",
            "1100x700", (980, 600)
        )

        self.model = Petugas()
        self.hanya_lihat = hanya_lihat
        self.id_sendiri = None if id_sendiri is None else str(id_sendiri)
        self.id_terpilih = None

        self.buat_tampilan()
        self.muat_data()

    # ==================== TAMPILAN ====================

    def buat_tampilan(self):

        t.Header(
            self.root, "DATA PETUGAS",
            "Daftar petugas perpustakaan (hanya dapat dilihat)"
            if self.hanya_lihat else
            "Kelola data petugas perpustakaan"
        ).pack(fill="x")

        # Statistik
        # Pembagi: bagian atas (statistik + form) dan tabel bisa ditarik
        pembagi = t.Pembagi(self.root)
        pembagi.pack(fill="both", expand=True, padx=14, pady=(14, 14))

        statistik = tk.Frame(pembagi.atas_isi, bg=LATAR)
        statistik.pack(fill="x", pady=(0, 10))

        self.label_total = t.buat_kartu(
            statistik, "TOTAL PETUGAS", "0", BIRU
        )
        self.label_operator = t.buat_kartu(
            statistik, "ROLE OPERATOR", "0", HIJAU
        )
        self.label_petugas = t.buat_kartu(
            statistik, "ROLE PETUGAS", "0", ORANYE
        )

        # Konten utama
        konten = pembagi.atas_isi

        self.var_nama = tk.StringVar()
        self.var_username = tk.StringVar()
        self.var_password = tk.StringVar()
        self.var_role = tk.StringVar(value="operator")

        if not self.hanya_lihat:
            self.buat_form(konten)

        # Tabel data
        panel_tabel, area_tabel = t.buat_panel(pembagi.bawah)
        panel_tabel.pack(fill="both", expand=True, padx=6)

        self.var_cari = tk.StringVar()
        t.buat_pencarian(
            area_tabel, "Daftar Petugas", self.var_cari, self.muat_data
        )

        self.tabel = t.buat_tabel(
            area_tabel,
            [
                ("id", "ID Petugas", 110, "center"),
                ("nama", "Nama Petugas", 260, "w"),
                ("username", "Username", 220, "w"),
                ("role", "Role", 140, "center"),
            ]
        )

        # Baris akun yang sedang login diberi warna biru muda
        self.tabel.tag_configure("saya", background="#DBEAFE")

        self.tabel.bind("<<TreeviewSelect>>", self.pilih_data)

    def buat_form(self, konten):

        panel_form, form = t.buat_panel(konten, "Form Data Petugas")
        panel_form.pack(fill="x", padx=6)

        t.buat_field(form, "Nama Petugas", self.var_nama, 0, 0)
        t.buat_field(form, "Username", self.var_username, 0, 1)
        t.buat_field(form, "Password", self.var_password, 0, 2, show="*")

        self.combo_role = t.buat_combo(
            form, "Role", self.var_role, ("operator", "petugas"), 0, 3
        )

        t.rata(form, 4)

        # Tombol aksi
        tombol = tk.Frame(form, bg="#FFFFFF")
        tombol.grid(row=1, column=0, columnspan=4, sticky="w")

        t.Tombol(tombol, "Tambah", HIJAU, self.tambah).pack(side="left", padx=(6, 4))
        t.Tombol(tombol, "Ubah", BIRU, self.ubah).pack(side="left", padx=4)
        t.Tombol(tombol, "Hapus", MERAH, self.hapus).pack(side="left", padx=4)
        t.Tombol(tombol, "Bersihkan", ABU, self.bersihkan).pack(side="left", padx=4)

        tk.Label(
            form,
            text=(
                "Saat mengubah, kosongkan password bila tidak ingin "
                "menggantinya. Akun Anda sendiri tidak dapat dihapus "
                "atau diubah rolenya."
            ),
            bg="#FFFFFF", fg="#94A3B8", font=("Segoe UI", 8)
        ).grid(row=2, column=0, columnspan=4, sticky="w", padx=6, pady=(6, 0))

    # ==================== DATA ====================

    def muat_data(self):
        try:
            data = self.model.tampilkan(self.var_cari.get())

            for item in self.tabel.get_children():
                self.tabel.delete(item)

            for indeks, baris in enumerate(data):
                tag = "genap" if indeks % 2 == 0 else "ganjil"

                if self.id_sendiri is not None and str(baris[0]) == self.id_sendiri:
                    tag = "saya"

                self.tabel.insert(
                    "",
                    "end",
                    values=baris,
                    tags=(tag,)
                )

            semua = self.model.tampilkan()
            self.label_total.config(text=str(len(semua)))
            self.label_operator.config(
                text=str(sum(1 for row in semua if row[3] == "operator"))
            )
            self.label_petugas.config(
                text=str(sum(1 for row in semua if row[3] == "petugas"))
            )

        except Exception as e:
            messagebox.showerror(
                "Kesalahan",
                f"Gagal memuat data petugas:\n{e}"
            )

    def ambil_form(self):
        return {
            "nama": self.var_nama.get(),
            "username": self.var_username.get(),
            "password": self.var_password.get(),
            "role": self.var_role.get()
        }

    def tambah(self):
        try:
            id_baru = self.model.tambah(self.ambil_form())

            messagebox.showinfo(
                "Berhasil",
                f"Data petugas berhasil ditambahkan.\nID: {id_baru}"
            )

            self.bersihkan()
            self.muat_data()

        except Exception as e:
            messagebox.showerror(
                "Gagal menambahkan petugas",
                str(e)
            )

    def pilih_data(self, event=None):
        if self.hanya_lihat:
            return

        pilihan = self.tabel.selection()

        if not pilihan:
            return

        nilai = self.tabel.item(pilihan[0], "values")

        self.id_terpilih = nilai[0]
        self.var_nama.set(nilai[1])
        self.var_username.set(nilai[2])
        self.var_role.set(nilai[3])

        # Kosong berarti password tidak akan diubah.
        self.var_password.set("")

    def ubah(self):
        if not self.id_terpilih:
            messagebox.showwarning(
                "Peringatan",
                "Pilih data petugas yang ingin diubah."
            )
            return

        try:
            self.model.ubah(
                self.id_terpilih,
                self.ambil_form(),
                id_pelaku=self.id_sendiri
            )

            messagebox.showinfo(
                "Berhasil",
                "Data petugas berhasil diperbarui."
            )

            self.bersihkan()
            self.muat_data()

        except Exception as e:
            messagebox.showerror(
                "Gagal mengubah petugas",
                str(e)
            )

    def hapus(self):
        if not self.id_terpilih:
            messagebox.showwarning(
                "Peringatan",
                "Pilih data petugas yang ingin dihapus."
            )
            return

        konfirmasi = messagebox.askyesno(
            "Konfirmasi",
            f"Yakin ingin menghapus petugas {self.id_terpilih}?"
        )

        if not konfirmasi:
            return

        try:
            self.model.hapus(
                self.id_terpilih,
                id_pelaku=self.id_sendiri
            )

            messagebox.showinfo(
                "Berhasil",
                "Data petugas berhasil dihapus."
            )

            self.bersihkan()
            self.muat_data()

        except ValueError as e:
            messagebox.showwarning(
                "Tidak dapat menghapus",
                str(e)
            )

        except Exception as e:
            messagebox.showerror(
                "Gagal menghapus petugas",
                f"{e}\n\nPetugas mungkin masih digunakan "
                "oleh data peminjaman."
            )

    def bersihkan(self):
        self.id_terpilih = None
        self.var_nama.set("")
        self.var_username.set("")
        self.var_password.set("")
        self.var_role.set("operator")

        for pilihan in self.tabel.selection():
            self.tabel.selection_remove(pilihan)


if __name__ == "__main__":
    root = tk.Tk()
    app = AppPetugas(root)
    root.mainloop()