import tkinter as tk
from io import BytesIO
from tkinter import filedialog, messagebox

from PIL import Image, ImageOps, ImageTk

from buku import Buku
import tema as t
from tema import BIRU, HIJAU, MERAH, ABU, LATAR

try:
    from buku.sampul_buku import SampulBuku
except ImportError:
    from sampul_buku import SampulBuku


UKURAN_PRATINJAU = (120, 160)


class AplikasiPerpustakaan:

    def __init__(self, root, hanya_lihat=False):
        self.root = root
        t.atur_jendela(
            root, "Sistem Perpustakaan - Data Buku",
            "1100x740", (980, 640)
        )

        self.model = Buku()
        self.sampul = SampulBuku()
        self.hanya_lihat = hanya_lihat

        self.id_terpilih = None
        self.foto_baru = None      # JPEG hasil olahan yang belum disimpan
        self.img_pratinjau = None  # referensi agar gambar tidak hilang

        self.buat_tampilan()
        self.muat_data()

    # ==================== TAMPILAN ====================

    def buat_tampilan(self):

        t.Header(
            self.root, "DATA BUKU",
            "Daftar buku perpustakaan (hanya dapat dilihat)"
            if self.hanya_lihat else
            "Kelola data buku perpustakaan"
        ).pack(fill="x")

        # Statistik
        # Pembagi: bagian atas (statistik + form) dan tabel bisa ditarik
        pembagi = t.Pembagi(self.root)
        pembagi.pack(fill="both", expand=True, padx=14, pady=(14, 14))

        statistik = tk.Frame(pembagi.atas_isi, bg=LATAR)
        statistik.pack(fill="x", pady=(0, 10))

        self.label_jumlah_buku = t.buat_kartu(
            statistik, "JUMLAH JUDUL BUKU", "0", BIRU
        )
        self.label_total_stok = t.buat_kartu(
            statistik, "TOTAL STOK BUKU", "0", HIJAU
        )

        # Konten utama
        konten = pembagi.atas_isi

        self.var_judul = tk.StringVar()
        self.var_penulis = tk.StringVar()
        self.var_penerbit = tk.StringVar()
        self.var_tahun = tk.StringVar()
        self.var_kategori = tk.StringVar()
        self.var_stok = tk.StringVar()

        if self.hanya_lihat:
            self.buat_detail(konten)
        else:
            self.buat_form(konten)

        # ==================== TABEL BUKU ====================

        panel_tabel, area_tabel = t.buat_panel(pembagi.bawah)
        panel_tabel.pack(fill="both", expand=True, padx=6)

        self.var_cari = tk.StringVar()
        t.buat_pencarian(
            area_tabel, "Daftar Buku", self.var_cari, self.muat_data
        )

        self.tabel = t.buat_tabel(
            area_tabel,
            [
                ("id_buku", "ID Buku", 90, "center"),
                ("judul", "Judul Buku", 210, "w"),
                ("penulis", "Penulis", 140, "w"),
                ("penerbit", "Penerbit", 140, "w"),
                ("tahun_terbit", "Tahun", 80, "center"),
                ("kategori", "Kategori", 115, "w"),
                ("stok_total", "Stok Total", 100, "center"),
                ("stok_tersedia", "Stok Tersedia", 115, "center"),
            ],
            scroll_x=True
        )

        self.tabel.bind("<<TreeviewSelect>>", self.pilih_buku)

    # ---------- form (operator: CRUD penuh) ----------

    def buat_form(self, konten):

        panel_form, form = t.buat_panel(konten, "Form Data Buku")
        panel_form.pack(fill="x", padx=6)

        t.buat_field(form, "Judul Buku", self.var_judul, 0, 0)
        t.buat_field(form, "Penulis", self.var_penulis, 0, 1)
        t.buat_field(form, "Penerbit", self.var_penerbit, 0, 2)

        t.buat_field(form, "Tahun Terbit", self.var_tahun, 1, 0)
        t.buat_field(form, "Kategori", self.var_kategori, 1, 1)
        t.buat_field(form, "Stok Total", self.var_stok, 1, 2)

        t.rata(form, 3)

        # Tombol aksi
        tombol = tk.Frame(form, bg="#FFFFFF")
        tombol.grid(row=2, column=0, columnspan=3, sticky="w")

        t.Tombol(tombol, "Tambah", HIJAU, self.tambah).pack(side="left", padx=(6, 4))
        t.Tombol(tombol, "Ubah", BIRU, self.ubah).pack(side="left", padx=4)
        t.Tombol(tombol, "Hapus", MERAH, self.hapus).pack(side="left", padx=4)
        t.Tombol(tombol, "Bersihkan", ABU, self.bersihkan).pack(side="left", padx=4)

        # Foto sampul (di sisi kanan form)
        sisi = tk.Frame(form, bg="#FFFFFF")
        sisi.grid(row=0, column=3, rowspan=3, padx=(24, 6), sticky="n")

        judul_foto = tk.Frame(sisi, bg="#FFFFFF")
        judul_foto.pack(anchor="w", fill="x", pady=(0, 4))

        tk.Label(
            judul_foto, text="Foto Sampul", bg="#FFFFFF", fg="#64748B",
            font=("Segoe UI", 9, "bold")
        ).pack(side="left")

        tk.Label(
            judul_foto, text="JPG/PNG/WEBP/AVIF",
            bg="#FFFFFF", fg="#94A3B8", font=("Segoe UI", 7)
        ).pack(side="left", padx=(6, 0))

        self.buat_kotak_foto(sisi)

        tombol_foto = tk.Frame(sisi, bg="#FFFFFF")
        tombol_foto.pack(anchor="w", pady=(6, 0))

        t.Tombol(tombol_foto, "Pilih Foto", BIRU, self.pilih_foto).pack(side="left")
        t.Tombol(tombol_foto, "Hapus Foto", ABU, self.hapus_foto).pack(
            side="left", padx=(6, 0)
        )

    # ---------- detail (petugas: hanya lihat) ----------

    def buat_detail(self, konten):

        panel, isi = t.buat_panel(konten, "Detail Buku")
        panel.pack(fill="x", padx=6)

        kiri = tk.Frame(isi, bg="#FFFFFF")
        kiri.grid(row=0, column=0, sticky="n", padx=(6, 24), pady=4)

        self.buat_kotak_foto(kiri)

        kanan = tk.Frame(isi, bg="#FFFFFF")
        kanan.grid(row=0, column=1, sticky="nw")

        tk.Label(
            kanan, textvariable=self.var_judul,
            font=("Segoe UI", 15, "bold"), bg="#FFFFFF", fg="#17365D",
            wraplength=640, justify="left", anchor="w"
        ).pack(anchor="w")

        tk.Label(
            kanan,
            text="Pilih buku pada tabel di bawah untuk melihat detailnya.",
            font=("Segoe UI", 9), bg="#FFFFFF", fg="#64748B"
        ).pack(anchor="w", pady=(2, 8))

        for label, variabel in (
            ("Penulis", self.var_penulis),
            ("Penerbit", self.var_penerbit),
            ("Tahun Terbit", self.var_tahun),
            ("Kategori", self.var_kategori),
            ("Stok Total", self.var_stok),
        ):
            baris = tk.Frame(kanan, bg="#FFFFFF")
            baris.pack(anchor="w", pady=2)

            tk.Label(
                baris, text=label, width=14, anchor="w",
                font=("Segoe UI", 9, "bold"), bg="#FFFFFF", fg="#64748B"
            ).pack(side="left")

            tk.Label(
                baris, textvariable=variabel, anchor="w",
                font=("Segoe UI", 10), bg="#FFFFFF", fg="#17365D"
            ).pack(side="left")

    # ---------- kotak pratinjau foto ----------

    def buat_kotak_foto(self, parent):

        lebar, tinggi = UKURAN_PRATINJAU

        kotak = tk.Frame(
            parent, width=lebar + 2, height=tinggi + 2, bg="#F1F5F9",
            highlightbackground="#CBD5E1", highlightthickness=1
        )
        kotak.pack(anchor="w")
        kotak.pack_propagate(False)

        self.label_foto = tk.Label(
            kotak, text="Belum ada foto", bg="#F1F5F9", fg="#94A3B8",
            font=("Segoe UI", 9)
        )
        self.label_foto.pack(fill="both", expand=True)

    def tampil_pratinjau(self, isi):
        """Menampilkan foto (bytes) di kotak pratinjau; None = kosong."""

        if isi is None:
            self.img_pratinjau = None
            self.label_foto.config(image="", text="Belum ada foto")
            return

        try:
            gambar = Image.open(BytesIO(isi)).convert("RGB")
            gambar = ImageOps.fit(gambar, UKURAN_PRATINJAU, Image.LANCZOS)

            self.img_pratinjau = ImageTk.PhotoImage(gambar)
            self.label_foto.config(image=self.img_pratinjau, text="")

        except Exception:
            self.img_pratinjau = None
            self.label_foto.config(image="", text="Foto tidak\ndapat dibaca")

    # ==================== DATA ====================

    def ambil_form(self):
        return {
            "judul": self.var_judul.get(),
            "penulis": self.var_penulis.get(),
            "penerbit": self.var_penerbit.get(),
            "tahun_terbit": self.var_tahun.get(),
            "kategori": self.var_kategori.get(),
            "stok_total": self.var_stok.get()
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
                    values=tuple(
                        "" if nilai is None else nilai
                        for nilai in baris
                    ),
                    tags=(tag,)
                )

            # Statistik seluruh data buku
            semua_buku = self.model.tampilkan("")

            total_judul = len(semua_buku)

            total_stok = sum(
                int(baris[6] or 0)
                for baris in semua_buku
            )

            self.label_jumlah_buku.config(text=f"{total_judul:,}")
            self.label_total_stok.config(text=f"{total_stok:,}")

        except Exception as e:
            messagebox.showerror(
                "Kesalahan",
                f"Gagal memuat data buku:\n{e}"
            )

    def pilih_buku(self, event=None):
        pilihan = self.tabel.selection()

        if not pilihan:
            return

        data = self.tabel.item(pilihan[0], "values")

        self.id_terpilih = data[0]

        self.var_judul.set(data[1])
        self.var_penulis.set(data[2])
        self.var_penerbit.set(data[3])
        self.var_tahun.set(data[4])
        self.var_kategori.set(data[5])
        self.var_stok.set(data[6])

        # Foto buku yang dipilih (foto yang belum disimpan dibuang)
        self.foto_baru = None
        self.tampil_pratinjau(self.sampul.ambil(self.id_terpilih))

    # ==================== FOTO SAMPUL ====================

    def pilih_foto(self):

        lokasi = filedialog.askopenfilename(
            parent=self.root.winfo_toplevel(),
            title="Pilih Foto Sampul Buku",
            filetypes=[
                ("Gambar", "*.jpg *.jpeg *.png *.webp *.avif"),
                ("Semua file", "*.*"),
            ]
        )

        if not lokasi:
            return

        try:
            isi = SampulBuku.proses(lokasi)

        except ValueError as e:
            messagebox.showwarning("Foto Tidak Dapat Dipakai", str(e))
            return

        self.foto_baru = isi
        self.tampil_pratinjau(isi)

    def hapus_foto(self):
        """
        Klik pertama membatalkan foto yang baru dipilih (belum disimpan).
        Bila tidak ada, menghapus foto tersimpan milik buku yang dipilih.
        """

        if self.foto_baru is not None:

            self.foto_baru = None

            self.tampil_pratinjau(
                self.sampul.ambil(self.id_terpilih)
                if self.id_terpilih else None
            )
            return

        if not self.id_terpilih:
            messagebox.showwarning(
                "Peringatan",
                "Pilih buku yang fotonya ingin dihapus."
            )
            return

        if not self.sampul.ada(self.id_terpilih):
            messagebox.showinfo(
                "Informasi", "Buku ini belum memiliki foto sampul."
            )
            return

        if not messagebox.askyesno(
            "Konfirmasi",
            f"Hapus foto sampul buku {self.id_terpilih}?"
        ):
            return

        peringatan = self.sampul.hapus(self.id_terpilih)

        self.tampil_pratinjau(None)

        if peringatan:
            messagebox.showwarning("Peringatan", peringatan)

    def simpan_foto(self, id_buku):
        """Menyimpan foto yang dipilih (bila ada). Mengembalikan teks peringatan/None."""

        if self.foto_baru is None:
            return None

        try:
            return self.sampul.simpan(id_buku, self.foto_baru)

        except OSError as e:
            return f"Foto gagal disimpan ke folder assets/sampul:\n{e}"

    # ==================== CRUD ====================

    def tambah(self):
        try:
            id_baru = self.model.tambah(self.ambil_form())

            pesan = f"Buku berhasil ditambahkan.\nID Buku: {id_baru}"
            peringatan = self.simpan_foto(id_baru)

            messagebox.showinfo("Berhasil", pesan)

            if peringatan:
                messagebox.showwarning("Foto Sampul", peringatan)

            self.bersihkan()
            self.muat_data()

        except Exception as e:
            messagebox.showerror(
                "Gagal menambahkan buku",
                str(e)
            )

    def ubah(self):
        if not self.id_terpilih:
            messagebox.showwarning(
                "Peringatan",
                "Pilih data buku yang ingin diubah."
            )
            return

        try:
            self.model.ubah(
                self.id_terpilih,
                self.ambil_form()
            )

            peringatan = self.simpan_foto(self.id_terpilih)

            messagebox.showinfo(
                "Berhasil",
                "Data buku berhasil diperbarui."
            )

            if peringatan:
                messagebox.showwarning("Foto Sampul", peringatan)

            self.bersihkan()
            self.muat_data()

        except Exception as e:
            messagebox.showerror(
                "Gagal mengubah buku",
                str(e)
            )

    def hapus(self):
        if not self.id_terpilih:
            messagebox.showwarning(
                "Peringatan",
                "Pilih data buku yang ingin dihapus."
            )
            return

        konfirmasi = messagebox.askyesno(
            "Konfirmasi",
            f"Yakin ingin menghapus buku {self.id_terpilih}?"
        )

        if not konfirmasi:
            return

        try:
            self.model.hapus(self.id_terpilih)

        except Exception as e:
            messagebox.showerror(
                "Gagal menghapus buku",
                "Buku mungkin masih digunakan dalam "
                "transaksi peminjaman.\n\n"
                f"Detail: {e}"
            )
            return

        # Foto ikut dihapus setelah bukunya benar-benar terhapus
        peringatan = self.sampul.hapus(self.id_terpilih)

        messagebox.showinfo(
            "Berhasil",
            "Data buku berhasil dihapus."
        )

        if peringatan:
            messagebox.showwarning("Foto Sampul", peringatan)

        self.bersihkan()
        self.muat_data()

    def bersihkan(self):
        self.id_terpilih = None
        self.foto_baru = None

        self.var_judul.set("")
        self.var_penulis.set("")
        self.var_penerbit.set("")
        self.var_tahun.set("")
        self.var_kategori.set("")
        self.var_stok.set("")

        self.tampil_pratinjau(None)

        for pilihan in self.tabel.selection():
            self.tabel.selection_remove(pilihan)


if __name__ == "__main__":
    root = tk.Tk()
    aplikasi = AplikasiPerpustakaan(root)
    root.mainloop()