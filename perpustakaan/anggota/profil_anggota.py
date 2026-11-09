import sys
from pathlib import Path

FOLDER_INI = Path(__file__).resolve().parent
ROOT_DIR = FOLDER_INI.parent

for _jalur in (FOLDER_INI, ROOT_DIR):
    if str(_jalur) not in sys.path:
        sys.path.insert(0, str(_jalur))

import hashlib
import hmac
import re
import secrets
import tkinter as tk
from tkinter import messagebox

from PIL import ImageTk

import tema as t
from koneksi import Database

from umum_anggota import (
    BIRU, BIRU_TUA, ABU, ABU_GELAP, ABU_MUDA, PUTIH, LATAR, MERAH_HEX,
    AreaGulir, buat_bulat, ke_tanggal, format_tanggal,
)
from peminjaman.riwayat_peminjaman import JadwalPengembalian


# ==================== PENGATURAN ====================

MIN_PANJANG_PASSWORD = 6
ITERASI_HASH = 260_000        # login menerima 1 .. 2.000.000
POLA_TELEPON = re.compile(r"^[0-9+\-\s]{8,20}$")   # kolom no_telepon: varchar(20)


# ==================================================
# HASH PASSWORD (format sama dengan login_anggota.py)
#   pbkdf2_sha256$iterasi$salt$hash
# ==================================================

def buat_hash(password):

    salt = secrets.token_hex(16)

    hasil = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        ITERASI_HASH
    ).hex()

    return f"pbkdf2_sha256${ITERASI_HASH}${salt}${hasil}"


def cocok(password, password_hash):

    try:
        algoritma, iterasi, salt, hash_asli = str(password_hash).split("$")

        if algoritma != "pbkdf2_sha256":
            return False

        iterasi = int(iterasi)

        if iterasi <= 0 or iterasi > 2_000_000:
            return False

        hasil = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            iterasi
        ).hex()

        return hmac.compare_digest(hasil, hash_asli)

    except (ValueError, TypeError, AttributeError):
        return False


# ==================================================
# MODEL
# ==================================================

class ProfilAnggota:

    def __init__(self):
        self.db = Database()

    def ambil(self, id_anggota):

        conn = self.db.hubungkan()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT
                    id_anggota,
                    nama,
                    alamat,
                    no_telepon,
                    username,
                    tanggal_daftar
                FROM anggota
                WHERE id_anggota = %s
            """, (id_anggota,))

            baris = cursor.fetchone()

            if baris is None:
                raise ValueError("Data anggota tidak ditemukan.")

            return {
                "id": str(baris[0]),
                "nama": str(baris[1] or ""),
                "alamat": "" if baris[2] is None else str(baris[2]),
                "telepon": "" if baris[3] is None else str(baris[3]),
                "username": str(baris[4] or ""),
                "tanggal_daftar": ke_tanggal(baris[5]),
            }

        finally:
            cursor.close()
            conn.close()

    def simpan_kontak(self, id_anggota, telepon, alamat):

        conn = self.db.hubungkan()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                UPDATE anggota
                SET no_telepon = %s, alamat = %s
                WHERE id_anggota = %s
            """, (telepon or None, alamat or None, id_anggota))

            conn.commit()

        finally:
            cursor.close()
            conn.close()

    def ganti_password(self, id_anggota, lama, baru):

        conn = self.db.hubungkan()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT password_hash FROM anggota WHERE id_anggota = %s",
                (id_anggota,)
            )

            baris = cursor.fetchone()

            if baris is None:
                raise ValueError("Data anggota tidak ditemukan.")

            if not cocok(lama, baris[0]):
                raise ValueError("Password lama tidak sesuai.")

            cursor.execute(
                "UPDATE anggota SET password_hash = %s WHERE id_anggota = %s",
                (buat_hash(baru), id_anggota)
            )

            conn.commit()

        finally:
            cursor.close()
            conn.close()


# ==================================================
# KOMPONEN KECIL
# ==================================================

def buat_input(parent, variabel=None, show=None, lebar=42):
    """Kotak isian bergaya sama dengan dashboard (garis tepi, fokus biru)."""

    return tk.Entry(
        parent,
        textvariable=variabel,
        width=lebar,
        show=show or "",
        font=("Segoe UI", 10),
        bg=PUTIH,
        fg=ABU_GELAP,
        insertbackground=BIRU,
        relief="flat",
        bd=0,
        highlightthickness=1,
        highlightbackground="#CBD5E1",
        highlightcolor=BIRU
    )


def label_kecil(parent, teks):

    return tk.Label(
        parent, text=teks, font=("Segoe UI", 9, "bold"),
        bg=PUTIH, fg=ABU, anchor="w"
    )


def judul_bagian(parent, teks, keterangan=""):

    tk.Label(
        parent, text=teks, font=("Segoe UI", 13, "bold"),
        bg=PUTIH, fg=BIRU_TUA, anchor="w"
    ).pack(anchor="w")

    if keterangan:
        tk.Label(
            parent, text=keterangan, font=("Segoe UI", 9),
            bg=PUTIH, fg=ABU, anchor="w"
        ).pack(anchor="w", pady=(2, 0))

    tk.Frame(parent, bg=ABU_MUDA, height=1).pack(fill="x", pady=(10, 12))


# ==================================================
# HALAMAN
# ==================================================

class HalamanProfil:

    def __init__(self, app, induk):

        self.app = app
        self.model = ProfilAnggota()
        self.img_avatar = ImageTk.PhotoImage(buat_bulat(76, (23, 54, 93)))

        t.Header(
            induk, "PROFIL SAYA",
            "Lihat data diri, ubah kontak, dan ganti password"
        ).pack(fill="x")

        wadah = tk.Frame(induk, bg=LATAR)
        wadah.pack(fill="both", expand=True, padx=22, pady=(18, 12))

        area = AreaGulir(wadah)
        area.luar.pack(fill="both", expand=True)
        app.area_gulir = area

        self.isi = area.isi

        try:
            self.data = self.model.ambil(app.id_anggota)

        except Exception as e:

            tk.Label(
                self.isi,
                text=f"Profil belum dapat dimuat.\n\nDetail: {e}",
                font=("Segoe UI", 10), bg=LATAR, fg=MERAH_HEX,
                justify="left"
            ).pack(anchor="w", padx=8, pady=20)

            return

        self.bangun_kepala()
        self.bangun_ringkasan()
        self.bangun_data_diri()
        self.bangun_password()

    # ==================== KEPALA PROFIL ====================

    def bangun_kepala(self):

        d = self.data

        kartu = tk.Frame(
            self.isi, bg=PUTIH,
            highlightbackground=ABU_MUDA, highlightthickness=1
        )
        kartu.pack(fill="x", padx=6, pady=(0, 12))

        isi = tk.Frame(kartu, bg=PUTIH, padx=22, pady=20)
        isi.pack(fill="x")

        tk.Label(
            isi, image=self.img_avatar,
            text=(d["nama"].strip()[:1] or "?").upper(),
            compound="center", font=("Segoe UI", 26, "bold"),
            fg=PUTIH, bg=PUTIH, bd=0
        ).pack(side="left", padx=(0, 20))

        teks = tk.Frame(isi, bg=PUTIH)
        teks.pack(side="left")

        tk.Label(
            teks, text=d["nama"], font=("Segoe UI", 18, "bold"),
            bg=PUTIH, fg=BIRU_TUA, anchor="w"
        ).pack(anchor="w")

        tk.Label(
            teks,
            text=(
                f"Anggota  ·  @{d['username']}  ·  "
                f"Terdaftar sejak {format_tanggal(d['tanggal_daftar'])}"
            ),
            font=("Segoe UI", 10), bg=PUTIH, fg=ABU, anchor="w"
        ).pack(anchor="w", pady=(4, 0))

    # ==================== RINGKASAN ====================

    def bangun_ringkasan(self):

        try:
            data = JadwalPengembalian().ambil(self.app.id_anggota)
            r = JadwalPengembalian.ringkasan(data)
            total, dipinjam, terlambat = len(data), r["dipinjam"], r["terlambat"]

        except Exception:
            total = dipinjam = terlambat = "-"

        statistik = tk.Frame(self.isi, bg=LATAR)
        statistik.pack(fill="x", padx=6, pady=(0, 12))

        t.buat_kartu(statistik, "TOTAL PEMINJAMAN", str(total), BIRU)
        t.buat_kartu(statistik, "SEDANG DIPINJAM", str(dipinjam), "#D97706")
        t.buat_kartu(statistik, "TERLAMBAT", str(terlambat), MERAH_HEX)

    # ==================== DATA DIRI & KONTAK ====================

    def bangun_data_diri(self):

        d = self.data

        panel, isi = t.buat_panel(self.isi)
        panel.pack(fill="x", padx=6, pady=(0, 12))

        judul_bagian(
            isi, "Data Diri",
            "Nama dan ID hanya dapat diubah oleh petugas perpustakaan."
        )

        # --- hanya dibaca ---
        baris_info = [
            ("ID Anggota", d["id"]),
            ("Nama", d["nama"]),
            ("Username", d["username"]),
            ("Tanggal Daftar", format_tanggal(d["tanggal_daftar"])),
        ]

        for label, nilai in baris_info:

            baris = tk.Frame(isi, bg=PUTIH)
            baris.pack(fill="x", pady=5)

            tk.Label(
                baris, text=label, width=16, anchor="w",
                font=("Segoe UI", 9, "bold"), bg=PUTIH, fg=ABU
            ).pack(side="left")

            tk.Label(
                baris, text=nilai or "-", anchor="w",
                font=("Segoe UI", 11), bg=PUTIH, fg=BIRU_TUA
            ).pack(side="left")

        tk.Frame(isi, bg=ABU_MUDA, height=1).pack(fill="x", pady=(12, 14))

        # --- boleh diubah ---
        tk.Label(
            isi, text="Kontak (dapat Anda ubah)",
            font=("Segoe UI", 11, "bold"), bg=PUTIH, fg=BIRU_TUA
        ).pack(anchor="w", pady=(0, 8))

        label_kecil(isi, "No. Telepon").pack(anchor="w")

        self.var_telepon = tk.StringVar(value=d["telepon"])
        buat_input(isi, self.var_telepon).pack(
            anchor="w", pady=(4, 10), ipady=6
        )

        label_kecil(isi, "Alamat").pack(anchor="w")

        self.teks_alamat = tk.Text(
            isi, width=42, height=3, wrap="word",
            font=("Segoe UI", 10), bg=PUTIH, fg=ABU_GELAP,
            insertbackground=BIRU, relief="flat", bd=0,
            highlightthickness=1, highlightbackground="#CBD5E1",
            highlightcolor=BIRU, padx=6, pady=6
        )
        self.teks_alamat.pack(anchor="w", pady=(4, 14))
        self.teks_alamat.insert("1.0", d["alamat"])

        t.Tombol(
            isi, "Simpan Kontak", BIRU, self.simpan_kontak
        ).pack(anchor="w")

    def simpan_kontak(self):

        telepon = self.var_telepon.get().strip()
        alamat = self.teks_alamat.get("1.0", "end").strip()

        if telepon and not POLA_TELEPON.match(telepon):

            messagebox.showwarning(
                "Data Tidak Valid",
                "No. telepon hanya boleh berisi angka, spasi, tanda + dan -,\n"
                "dengan panjang 8 sampai 20 karakter.",
                parent=self.app.root
            )
            return

        try:
            self.model.simpan_kontak(self.app.id_anggota, telepon, alamat)

        except Exception as e:

            messagebox.showerror(
                "Kesalahan",
                f"Kontak gagal disimpan:\n{e}",
                parent=self.app.root
            )
            return

        self.data["telepon"] = telepon
        self.data["alamat"] = alamat

        messagebox.showinfo(
            "Berhasil", "Kontak Anda sudah diperbarui.",
            parent=self.app.root
        )

    # ==================== GANTI PASSWORD ====================

    def bangun_password(self):

        panel, isi = t.buat_panel(self.isi)
        panel.pack(fill="x", padx=6, pady=(0, 12))

        judul_bagian(
            isi, "Ganti Password",
            f"Gunakan minimal {MIN_PANJANG_PASSWORD} karakter."
        )

        self.var_lama = tk.StringVar()
        self.var_baru = tk.StringVar()
        self.var_ulang = tk.StringVar()
        self.var_lihat = tk.BooleanVar(value=False)

        self.input_password = []

        for teks, variabel in (
            ("Password Lama", self.var_lama),
            ("Password Baru", self.var_baru),
            ("Ulangi Password Baru", self.var_ulang),
        ):
            label_kecil(isi, teks).pack(anchor="w")

            kotak = buat_input(isi, variabel, show="*")
            kotak.pack(anchor="w", pady=(4, 10), ipady=6)

            self.input_password.append(kotak)

        tk.Checkbutton(
            isi, text="Tampilkan password", variable=self.var_lihat,
            command=self.atur_tampil, font=("Segoe UI", 9),
            bg=PUTIH, fg=ABU_GELAP, activebackground=PUTIH,
            selectcolor=PUTIH, relief="flat", bd=0,
            highlightthickness=0, cursor="hand2"
        ).pack(anchor="w", pady=(0, 14))

        t.Tombol(
            isi, "Ganti Password", BIRU_TUA, self.simpan_password
        ).pack(anchor="w")

    def atur_tampil(self):

        for kotak in self.input_password:
            kotak.config(show="" if self.var_lihat.get() else "*")

    def simpan_password(self):

        lama = self.var_lama.get()
        baru = self.var_baru.get()
        ulang = self.var_ulang.get()

        def tolak(pesan):
            messagebox.showwarning(
                "Ganti Password", pesan, parent=self.app.root
            )

        if not lama or not baru or not ulang:
            return tolak("Semua kolom password wajib diisi.")

        if len(baru) < MIN_PANJANG_PASSWORD:
            return tolak(
                f"Password baru minimal {MIN_PANJANG_PASSWORD} karakter."
            )

        if baru != ulang:
            return tolak("Password baru dan pengulangannya tidak sama.")

        if baru == lama:
            return tolak("Password baru harus berbeda dari password lama.")

        try:
            self.model.ganti_password(self.app.id_anggota, lama, baru)

        except ValueError as e:
            return tolak(str(e))

        except Exception as e:

            messagebox.showerror(
                "Kesalahan",
                f"Password gagal diganti:\n{e}",
                parent=self.app.root
            )
            return

        for variabel in (self.var_lama, self.var_baru, self.var_ulang):
            variabel.set("")

        messagebox.showinfo(
            "Berhasil",
            "Password berhasil diganti.\n"
            "Gunakan password baru saat login berikutnya.",
            parent=self.app.root
        )