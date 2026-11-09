import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import hashlib
import hmac
import secrets
import tkinter as tk
from tkinter import ttk, messagebox

from PIL import Image, ImageDraw, ImageTk

import tema as t
from koneksi import Database


# ==================== PENGATURAN ====================

MIN_PANJANG_PASSWORD = 6
ITERASI_HASH = 260_000

AKSES_MENU = {
    "petugas": "Data Buku, Data Anggota, Peminjaman, Data Petugas",
    "operator": "Data Buku, Data Anggota, Peminjaman",
}

# (latar chip, teks chip)
WARNA_ROLE = {
    "petugas": ("#DBEAFE", "#1D4ED8"),
    "operator": ("#DCFCE7", "#166534"),
}

BIRU = t.BIRU
BIRU_TUA = t.BIRU_TUA
ABU = t.ABU
ABU_GELAP = t.ABU_GELAP
ABU_MUDA = t.BORDER
PUTIH = t.PUTIH
LATAR = t.LATAR
MERAH_HEX = t.MERAH
ORANYE = t.ORANYE
FONT = t.FONT

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

class ProfilPetugas:

    def __init__(self):
        self.db = Database()

    def ambil(self, id_petugas):

        conn = self.db.hubungkan()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT
                    id_petugas,
                    nama,
                    username,
                    role
                FROM petugas
                WHERE id_petugas = %s
            """, (id_petugas,))

            baris = cursor.fetchone()

            if baris is None:
                raise ValueError("Data petugas tidak ditemukan.")

            return {
                "id": str(baris[0]),
                "nama": str(baris[1] or ""),
                "username": str(baris[2] or ""),
                "role": str(baris[3] or "").strip().lower(),
            }

        finally:
            cursor.close()
            conn.close()

    def ringkasan(self, id_petugas):
        """Jumlah transaksi yang diproses / ditolak oleh petugas ini."""

        conn = self.db.hubungkan()
        cursor = conn.cursor()

        try:
            # status_peminjaman: menunggu / disetujui / ditolak / selesai
            # (disetujui = sedang dipinjam)
            cursor.execute("""
                SELECT status_peminjaman, COUNT(*)
                FROM peminjaman
                WHERE petugas_id = %s
                GROUP BY status_peminjaman
            """, (id_petugas,))

            jumlah = {str(s).lower(): int(n) for s, n in cursor.fetchall()}

            return {
                "total": sum(jumlah.values()),
                "dipinjam": jumlah.get("disetujui", 0),
                "selesai": jumlah.get("selesai", 0),
            }

        finally:
            cursor.close()
            conn.close()

    def ganti_password(self, id_petugas, lama, baru):

        conn = self.db.hubungkan()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "SELECT password_hash FROM petugas WHERE id_petugas = %s",
                (id_petugas,)
            )

            baris = cursor.fetchone()

            if baris is None:
                raise ValueError("Data petugas tidak ditemukan.")

            if not cocok(lama, baris[0]):
                raise ValueError("Password lama tidak sesuai.")

            cursor.execute(
                "UPDATE petugas SET password_hash = %s WHERE id_petugas = %s",
                (buat_hash(baru), id_petugas)
            )

            conn.commit()

        finally:
            cursor.close()
            conn.close()


# ==================================================
# KOMPONEN KECIL
# ==================================================

def buat_bulat(diameter, warna):
    """Lingkaran polos (anti-alias) untuk avatar."""

    s = 4
    img = Image.new("RGBA", (diameter * s, diameter * s), (0, 0, 0, 0))

    ImageDraw.Draw(img).ellipse(
        [0, 0, diameter * s - 1, diameter * s - 1], fill=warna
    )

    return img.resize((diameter, diameter), Image.LANCZOS)


class AreaGulir:
    """Kanvas dengan scrollbar + roda mouse. Isi diletakkan di `self.isi`."""

    def __init__(self, parent):

        self.luar = tk.Frame(parent, bg=LATAR)

        self.canvas = tk.Canvas(
            self.luar, bg=LATAR, highlightthickness=0, bd=0
        )
        self.scroll = ttk.Scrollbar(
            self.luar, orient="vertical", command=self.canvas.yview
        )
        self.canvas.configure(yscrollcommand=self.scroll.set)

        self.scroll.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.isi = tk.Frame(self.canvas, bg=LATAR)
        self.jendela = self.canvas.create_window(
            (0, 0), window=self.isi, anchor="nw"
        )

        self.isi.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfigure(self.jendela, width=e.width)
        )

        # Satu pengikat global; halaman berikutnya akan menggantinya.
        self.canvas.bind_all("<MouseWheel>", self._roda)

    def _roda(self, event):

        try:
            if not self.luar.winfo_exists():
                return

            widget = self.luar.winfo_containing(event.x_root, event.y_root)

            while widget is not None:
                if widget is self.luar:
                    break
                widget = widget.master
            else:
                return  # pointer di luar area ini

            if self.isi.winfo_height() > self.canvas.winfo_height():
                self.canvas.yview_scroll(int(-event.delta / 120), "units")

        except (tk.TclError, KeyError):
            pass


def label_kecil(parent, teks):

    return tk.Label(
        parent, text=teks, font=(FONT, 9, "bold"),
        bg=PUTIH, fg=ABU, anchor="w"
    )


def judul_bagian(parent, teks, keterangan=""):

    tk.Label(
        parent, text=teks, font=(FONT, 13, "bold"),
        bg=PUTIH, fg=BIRU_TUA, anchor="w"
    ).pack(anchor="w")

    if keterangan:
        tk.Label(
            parent, text=keterangan, font=(FONT, 9),
            bg=PUTIH, fg=ABU, anchor="w"
        ).pack(anchor="w", pady=(2, 0))

    tk.Frame(parent, bg=ABU_MUDA, height=1).pack(fill="x", pady=(10, 12))


# ==================================================
# HALAMAN
# ==================================================

class HalamanProfilPetugas:
    """
    Dipanggil dari dashboard petugas, misalnya:

        from petugas.profil_petugas import HalamanProfilPetugas
        HalamanProfilPetugas(self, induk)

    `app` (dashboard) harus punya: .root, .id_petugas, .role
    dan (opsional) .pilih_menu(nama).
    """

    def __init__(self, app, induk):

        self.app = app
        self.model = ProfilPetugas()
        self.img_avatar = ImageTk.PhotoImage(buat_bulat(76, (23, 54, 93)))

        role_sesi = str(getattr(app, "role", "")).strip().lower()

        t.terapkan_style(app.root)

        t.Header(
            induk, "PROFIL SAYA",
            f"Data akun {role_sesi.capitalize() or 'pengguna'} "
            "dan pengaturan password"
        ).pack(fill="x")

        wadah = tk.Frame(induk, bg=LATAR)
        wadah.pack(fill="both", expand=True, padx=22, pady=(18, 12))

        area = AreaGulir(wadah)
        area.luar.pack(fill="both", expand=True)

        self.isi = area.isi

        try:
            self.data = self.model.ambil(app.id_petugas)

        except Exception as e:

            tk.Label(
                self.isi,
                text=f"Profil belum dapat dimuat.\n\nDetail: {e}",
                font=(FONT, 10), bg=LATAR, fg=MERAH_HEX, justify="left"
            ).pack(anchor="w", padx=8, pady=20)

            return

        # Role dari database dianggap paling benar
        self.role = self.data["role"] or role_sesi

        self.bangun_kepala()
        self.bangun_ringkasan()
        self.bangun_data_akun()
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
            compound="center", font=(FONT, 26, "bold"),
            fg=PUTIH, bg=PUTIH, bd=0
        ).pack(side="left", padx=(0, 20))

        teks = tk.Frame(isi, bg=PUTIH)
        teks.pack(side="left")

        tk.Label(
            teks, text=d["nama"], font=(FONT, 18, "bold"),
            bg=PUTIH, fg=BIRU_TUA, anchor="w"
        ).pack(anchor="w")

        baris = tk.Frame(teks, bg=PUTIH)
        baris.pack(anchor="w", pady=(6, 0))

        bg_chip, fg_chip = WARNA_ROLE.get(self.role, ("#E2E8F0", "#334155"))

        tk.Label(
            baris, text=f"  {self.role.capitalize()}  ",
            font=(FONT, 9, "bold"), bg=bg_chip, fg=fg_chip, pady=2
        ).pack(side="left")

        tk.Label(
            baris, text=f"@{d['username']}   ·   ID {d['id']}",
            font=(FONT, 10), bg=PUTIH, fg=ABU
        ).pack(side="left", padx=(10, 0))

    # ==================== RINGKASAN ====================

    def bangun_ringkasan(self):

        try:
            r = self.model.ringkasan(self.app.id_petugas)
            total, dipinjam, selesai = r["total"], r["dipinjam"], r["selesai"]

        except Exception:
            total = dipinjam = selesai = "-"

        statistik = tk.Frame(self.isi, bg=LATAR)
        statistik.pack(fill="x", padx=6, pady=(0, 12))

        t.buat_kartu(statistik, "TRANSAKSI DITANGANI", str(total), BIRU)
        t.buat_kartu(statistik, "SEDANG DIPINJAM", str(dipinjam), ORANYE)
        t.buat_kartu(statistik, "SELESAI", str(selesai), t.HIJAU)

    # ==================== DATA AKUN ====================

    def bangun_data_akun(self):

        d = self.data

        panel, isi = t.buat_panel(self.isi)
        panel.pack(fill="x", padx=6, pady=(0, 12))

        if self.role == "petugas":
            keterangan = (
                "Untuk mengubah nama, username, atau role, "
                "gunakan menu Data Petugas."
            )
        else:
            keterangan = (
                "Nama, username, dan role hanya dapat diubah "
                "oleh Petugas melalui menu Data Petugas."
            )

        judul_bagian(isi, "Data Akun", keterangan)

        baris_info = [
            ("ID Petugas", d["id"]),
            ("Nama", d["nama"]),
            ("Username", d["username"]),
            ("Role", self.role.capitalize()),
            ("Akses Menu", AKSES_MENU.get(self.role, "-")),
        ]

        for label, nilai in baris_info:

            baris = tk.Frame(isi, bg=PUTIH)
            baris.pack(fill="x", pady=5)

            tk.Label(
                baris, text=label, width=16, anchor="w",
                font=(FONT, 9, "bold"), bg=PUTIH, fg=ABU
            ).pack(side="left")

            tk.Label(
                baris, text=nilai or "-", anchor="w",
                font=(FONT, 11), bg=PUTIH, fg=BIRU_TUA
            ).pack(side="left")

        # Pintasan hanya untuk role petugas
        if self.role == "petugas" and hasattr(self.app, "pilih_menu"):

            tk.Frame(isi, bg=ABU_MUDA, height=1).pack(fill="x", pady=(12, 14))

            t.Tombol(
                isi, "Buka Data Petugas", BIRU,
                lambda: self.app.pilih_menu("Data Petugas")
            ).pack(anchor="w")

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

            kotak = t.buat_entry(isi, variabel, show="*", width=42)
            kotak.pack(anchor="w", pady=(4, 10), ipady=6)

            self.input_password.append(kotak)

        tk.Checkbutton(
            isi, text="Tampilkan password", variable=self.var_lihat,
            command=self.atur_tampil, font=(FONT, 9),
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
            self.model.ganti_password(self.app.id_petugas, lama, baru)

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