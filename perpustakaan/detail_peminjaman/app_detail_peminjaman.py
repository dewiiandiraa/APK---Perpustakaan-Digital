import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import tkinter as tk
from tkinter import messagebox

from detail_peminjaman.detail_peminjaman import DetailPeminjaman
from peminjaman.peminjaman import Peminjaman
import tema as t
from tema import BIRU, HIJAU, MERAH, ABU, PUTIH, LATAR


class AppDetailPeminjaman:
    """
    hanya_lihat=False : petugas  -> kelola buku & pengembalian
    hanya_lihat=True  : operator -> hanya melihat isi transaksi
    """

    def __init__(
        self, root, id_peminjaman, model=None, callback=None,
        hanya_lihat=False
    ):

        self.root = root
        self.id_peminjaman = id_peminjaman
        self.callback = callback
        self.hanya_lihat = hanya_lihat

        self.model = (
            model if model is not None
            else DetailPeminjaman(hanya_lihat=hanya_lihat)
        )

        # Model yang dikirim dari luar pun dikunci pada mode hanya lihat
        if hanya_lihat:
            self.model.hanya_lihat = True

        self.model_peminjaman = Peminjaman(hanya_lihat=hanya_lihat)

        self.id_terpilih = None
        self.mode_mandiri = False

        # ==================== JENDELA ====================

        self.window = tk.Toplevel(self.root)
        t.atur_jendela(
            self.window, "Sistem Perpustakaan - Detail Peminjaman",
            "1120x740", (980, 640)
        )

        self.window.protocol(
            "WM_DELETE_WINDOW",
            self.tutup
        )

        self.buat_tampilan()

        self.window.update_idletasks()
        self.window.deiconify()
        self.window.lift()
        self.window.focus_force()

        self.window.after(100, self.muat_data)

    # ==================== TAMPILAN ====================

    def buat_tampilan(self):

        t.Header(
            self.window,
            "DETAIL PEMINJAMAN",
            f"ID Peminjaman: {self.id_peminjaman}"
            + ("   ·   hanya dapat dilihat" if self.hanya_lihat else "")
        ).pack(fill="x")

        konten = tk.Frame(self.window, bg=LATAR)
        konten.pack(fill="both", expand=True, padx=20, pady=18)

        # ==================== FORM ====================

        pembagi = t.Pembagi(konten)

        panel_form, form = t.buat_panel(
            pembagi.atas_isi,
            "Informasi Buku" if self.hanya_lihat
            else "Form Detail Peminjaman"
        )
        panel_form.pack(fill="x")

        self.var_id_detail = tk.StringVar(value="Otomatis")
        self.var_peminjaman = tk.StringVar(value=self.id_peminjaman)
        self.var_buku = tk.StringVar()
        self.var_jumlah = tk.StringVar(value="1")
        self.var_jatuh_tempo = tk.StringVar(value="Belum ditentukan")
        self.var_kembali = tk.StringVar(value="Belum dikembalikan")

        # Mode hanya lihat: seluruh isian hanya dapat dibaca
        ro = self.hanya_lihat

        # Baris pertama
        t.buat_field(form, "ID Detail", self.var_id_detail, 0, 0, readonly=True)
        t.buat_field(form, "ID Peminjaman", self.var_peminjaman, 0, 1, readonly=True)
        t.buat_field(form, "ID Buku", self.var_buku, 0, 2, readonly=ro)

        # Baris kedua
        t.buat_field(form, "Jumlah", self.var_jumlah, 1, 0, readonly=ro)
        t.buat_field(
            form, "Tanggal Jatuh Tempo", self.var_jatuh_tempo, 1, 1,
            readonly=True
        )
        t.buat_field(
            form, "Tanggal Kembali", self.var_kembali, 1, 2,
            readonly=True
        )

        t.rata(form, 3)

        # ==================== TOMBOL CRUD (hanya petugas) ====================

        if not self.hanya_lihat:

            tombol = tk.Frame(form, bg=PUTIH)
            tombol.grid(row=2, column=0, columnspan=3, sticky="w", pady=(4, 0))

            self.btn_tambah = t.Tombol(tombol, "Tambah", HIJAU, self.tambah)
            self.btn_tambah.pack(side="left", padx=(6, 4))

            self.btn_ubah = t.Tombol(tombol, "Ubah Jumlah", BIRU, self.ubah)
            self.btn_ubah.pack(side="left", padx=4)

            self.btn_hapus = t.Tombol(tombol, "Hapus", MERAH, self.hapus)
            self.btn_hapus.pack(side="left", padx=4)

            self.btn_bersihkan = t.Tombol(
                tombol, "Bersihkan", ABU, self.bersihkan
            )
            self.btn_bersihkan.pack(side="left", padx=4)

        # ==================== TOMBOL BAWAH ====================

        bawah = tk.Frame(konten, bg=LATAR)
        bawah.pack(side="bottom", fill="x", pady=(14, 0))

        if not self.hanya_lihat:

            self.btn_kembalikan = t.Tombol(
                bawah, "Pengembalian Buku", HIJAU, self.kembalikan
            )
            self.btn_kembalikan.pack(side="left")

        self.btn_refresh = t.Tombol(
            bawah, "Refresh", BIRU, self.muat_data
        )
        self.btn_refresh.pack(side="left", padx=0 if self.hanya_lihat else 8)

        self.btn_tutup = t.Tombol(bawah, "Tutup", ABU, self.tutup)
        self.btn_tutup.pack(side="right")

        # ==================== TABEL ====================

        pembagi.pack(fill="both", expand=True)

        panel_tabel, area_tabel = t.buat_panel(
            pembagi.bawah, "Daftar Buku dalam Transaksi"
        )
        panel_tabel.pack(fill="both", expand=True)

        self.tabel = t.buat_tabel(
            area_tabel,
            [
                ("id_detail", "ID Detail", 90, "center"),
                ("peminjaman_id", "ID Peminjaman", 115, "center"),
                ("buku_id", "ID Buku", 90, "center"),
                ("judul", "Judul Buku", 220, "w"),
                ("jumlah", "Jumlah", 75, "center"),
                ("jatuh_tempo", "Tanggal Jatuh Tempo", 150, "center"),
                ("kembali", "Tanggal Kembali", 150, "center"),
            ]
        )

        self.tabel.bind("<<TreeviewSelect>>", self.pilih_data)

    # ==================== PENGATURAN TOMBOL ====================

    def atur_tombol(self):

        # Mode hanya lihat tidak memiliki tombol pengubah data.
        if self.hanya_lihat:
            return

        try:
            data = self.model_peminjaman.detail_transaksi(
                self.id_peminjaman
            )

            if not data:
                raise Exception(
                    "Data peminjaman tidak ditemukan."
                )

            status = data[6]

            # Nonaktifkan seluruh tombol transaksi terlebih dahulu.

            self.btn_tambah.config(state="disabled")
            self.btn_ubah.config(state="disabled")
            self.btn_hapus.config(state="disabled")
            self.btn_kembalikan.config(state="disabled")

            # Status menunggu: buku masih dapat dikelola.

            if status == "menunggu":

                self.btn_tambah.config(state="normal")
                self.btn_ubah.config(state="normal")
                self.btn_hapus.config(state="normal")

            # Status dipinjam: hanya dapat melakukan pengembalian.

            elif status == "dipinjam":

                self.btn_kembalikan.config(state="normal")

        except Exception as e:

            self.btn_tambah.config(state="disabled")
            self.btn_ubah.config(state="disabled")
            self.btn_hapus.config(state="disabled")
            self.btn_kembalikan.config(state="disabled")

            messagebox.showerror(
                "Kesalahan",
                f"Gagal memeriksa status peminjaman:\n{e}",
                parent=self.window
            )

    # ==================== CALLBACK ====================

    def perbarui_induk(self):

        if self.callback:

            try:
                self.callback()

            except Exception as e:

                messagebox.showwarning(
                    "Peringatan",
                    f"Tampilan transaksi gagal diperbarui:\n{e}",
                    parent=self.window
                )

    # ==================== MEMUAT DATA ====================

    def muat_data(self, pilih_buku=None):

        if not self.window.winfo_exists():
            return

        # Bersihkan form dan pilihan sebelumnya.

        self.bersihkan()

        # Hapus semua baris lama agar tidak terjadi duplikasi.

        for item in self.tabel.get_children():
            self.tabel.delete(item)

        try:

            # Ambil data terbaru dari database.

            data = self.model.tampilkan(
                self.id_peminjaman
            )

            # Masukkan data terbaru ke Treeview.

            for indeks, baris in enumerate(data):

                tag = "genap" if indeks % 2 == 0 else "ganjil"

                self.tabel.insert(
                    "",
                    "end",
                    values=baris,
                    tags=(tag,)
                )

            # Pilih kembali buku yang baru ditambahkan.

            if pilih_buku:

                for item in self.tabel.get_children():

                    nilai = self.tabel.item(
                        item,
                        "values"
                    )

                    if str(nilai[2]) == str(pilih_buku):

                        self.tabel.selection_set(item)
                        self.tabel.focus(item)
                        self.tabel.see(item)

                        self.pilih_data()
                        break

        except Exception as e:

            messagebox.showerror(
                "Kesalahan",
                f"Gagal memuat detail peminjaman:\n{e}",
                parent=self.window
            )

        finally:

            # Periksa status transaksi dan atur tombol.

            self.atur_tombol()

    # ==================== MEMILIH DATA ====================

    def pilih_data(self, event=None):

        pilihan = self.tabel.selection()

        if not pilihan:
            return

        nilai = self.tabel.item(
            pilihan[0],
            "values"
        )

        self.id_terpilih = nilai[0]

        self.var_id_detail.set(nilai[0])
        self.var_peminjaman.set(nilai[1])
        self.var_buku.set(nilai[2])
        self.var_jumlah.set(str(nilai[4]))

        self.var_jatuh_tempo.set(
            nilai[5] if nilai[5] else "Belum ditentukan"
        )

        self.var_kembali.set(
            nilai[6] if nilai[6] else "Belum dikembalikan"
        )

    # ==================== TAMBAH ====================

    def tambah(self):

        id_buku = self.var_buku.get().strip()

        if not id_buku:

            messagebox.showwarning(
                "Peringatan",
                "ID Buku harus diisi.",
                parent=self.window
            )
            return

        try:

            self.model.tambah(
                self.id_peminjaman,
                id_buku,
                self.var_jumlah.get()
            )

            self.muat_data(
                pilih_buku=id_buku
            )

            self.perbarui_induk()

            messagebox.showinfo(
                "Berhasil",
                "Detail buku berhasil ditambahkan.",
                parent=self.window
            )

        except Exception as e:

            messagebox.showerror(
                "Gagal Menambahkan",
                str(e),
                parent=self.window
            )

    # ==================== UBAH JUMLAH ====================

    def ubah(self):

        if not self.id_terpilih:

            messagebox.showwarning(
                "Peringatan",
                "Pilih detail buku yang ingin diubah.",
                parent=self.window
            )
            return

        try:

            self.model.ubah(
                self.id_terpilih,
                self.var_jumlah.get()
            )

            self.muat_data()

            self.perbarui_induk()

            messagebox.showinfo(
                "Berhasil",
                "Jumlah buku berhasil diubah.",
                parent=self.window
            )

        except Exception as e:

            messagebox.showerror(
                "Gagal Mengubah",
                str(e),
                parent=self.window
            )

    # ==================== HAPUS ====================

    def hapus(self):

        if not self.id_terpilih:

            messagebox.showwarning(
                "Peringatan",
                "Pilih detail buku yang ingin dihapus.",
                parent=self.window
            )
            return

        konfirmasi = messagebox.askyesno(
            "Konfirmasi",
            f"Yakin ingin menghapus detail {self.id_terpilih}?",
            parent=self.window
        )

        if not konfirmasi:
            return

        try:

            self.model.hapus(
                self.id_terpilih
            )

            self.muat_data()

            self.perbarui_induk()

            messagebox.showinfo(
                "Berhasil",
                "Detail peminjaman berhasil dihapus.",
                parent=self.window
            )

        except Exception as e:

            messagebox.showerror(
                "Gagal Menghapus",
                str(e),
                parent=self.window
            )

    # ==================== PENGEMBALIAN ====================

    def kembalikan(self):

        konfirmasi = messagebox.askyesno(
            "Konfirmasi Pengembalian",
            f"Yakin ingin mengembalikan seluruh buku "
            f"dalam transaksi {self.id_peminjaman}?\n\n"
            "Seluruh stok buku akan dikembalikan dan "
            "status peminjaman akan berubah menjadi SELESAI.",
            parent=self.window
        )

        if not konfirmasi:
            return

        try:

            # Proses pengembalian seluruh buku dalam satu transaksi.

            self.model.kembalikan(
                self.id_peminjaman
            )

            # Muat ulang tabel untuk menampilkan tanggal kembali.

            self.muat_data()

            # Perbarui daftar transaksi pada jendela utama.

            self.perbarui_induk()

            messagebox.showinfo(
                "Berhasil",
                "Seluruh buku dalam transaksi berhasil dikembalikan.",
                parent=self.window
            )

        except Exception as e:

            messagebox.showerror(
                "Gagal Mengembalikan",
                str(e),
                parent=self.window
            )

    # ==================== BERSIHKAN ====================

    def bersihkan(self):

        self.id_terpilih = None

        self.var_id_detail.set("Otomatis")
        self.var_peminjaman.set(self.id_peminjaman)
        self.var_buku.set("")
        self.var_jumlah.set("1")
        self.var_jatuh_tempo.set("Belum ditentukan")
        self.var_kembali.set("Belum dikembalikan")

        # Hanya menghapus pilihan, bukan isi tabel.

        for pilihan in self.tabel.selection():
            self.tabel.selection_remove(pilihan)

    # ==================== TUTUP ====================

    def tutup(self):

        if self.window.winfo_exists():
            self.window.destroy()

        if self.mode_mandiri:
            self.root.destroy()


# ==================== MENJALANKAN PROGRAM ====================

if __name__ == "__main__":

    root = tk.Tk()
    root.withdraw()

    aplikasi = AppDetailPeminjaman(
        root,
        id_peminjaman="PJM001"
    )

    aplikasi.mode_mandiri = True

    root.mainloop()