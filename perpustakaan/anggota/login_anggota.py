import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import tkinter as tk
from tkinter import messagebox
from pathlib import Path
import hashlib
import hmac

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageTk

from koneksi import Database


# ==================================================
# LOGIN ANGGOTA
# Desain sama dengan login petugas, warna dibalik:
#   latar biru  -> latar terang
#   kartu putih -> kartu biru (warna panel login petugas)
#   panel biru  -> panel putih
# ==================================================

# ==================== PALET WARNA ====================

NAVY = "#17365D"          # teks & ikon gelap
KARTU = "#1F64BE"         # warna kartu (sama dengan panel login petugas)
KARTU_FIELD = "#2E73CB"   # kotak input & lingkaran dekoratif
BIRU = "#2563EB"

PUTIH = "#FFFFFF"
ABU = "#64748B"
ABU_GELAP = "#334155"
ABU_PLACEHOLDER = "#94A3B8"
TEKS_TERANG = "#D6E6FA"
TEKS_LEMBUT = "#E8F1FC"
LINK = "#DBEAFE"

NAVY_RGB = (23, 54, 93)
KARTU_RGB = (31, 100, 190)
KARTU_FIELD_RGB = (46, 115, 203)
BIRU_PUDAR = (225, 236, 250)


# ==================== UKURAN LAYOUT ====================

W, H = 1000, 650
CX, CY, CW, CH = 90, 70, 820, 510
FX, FW = 545, 310

# Anggota hanya punya satu jenis akun.
DAFTAR_ROLE = [("Anggota", "anggota")]

NAMA_LOGO = (
    "assets/logo/logo-perpustakaan.png",
    "logo-perpustakaan.png",
    "logo-login.png",
)

FILE_INGAT = ".login_anggota_ingat"


# ==================================================
# FUNGSI GAMBAR (PIL)
# ==================================================

def cari_logo():

    folder_file = Path(__file__).resolve().parent

    # Cari di folder file ini, lalu di folder induknya (folder proyek).
    for folder in (folder_file, folder_file.parent):
        for nama in NAMA_LOGO:
            lokasi = folder / nama
            if lokasi.exists():
                return lokasi

    return None


def buat_background():
    """Latar terang + kartu biru tua dengan panel putih di kiri."""

    S = 3

    # ---- Latar gradasi terang ----
    atas = Image.new("RGB", (W, H), (246, 249, 253))
    bawah = Image.new("RGB", (W, H), (213, 227, 245))
    gradien = Image.linear_gradient("L").resize((W, H))
    bg = Image.composite(bawah, atas, gradien).convert("RGBA")

    # ---- Bayangan kartu ----
    bayangan = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(bayangan).rounded_rectangle(
        [CX, CY + 14, CX + CW, CY + CH + 14],
        radius=26,
        fill=(10, 40, 90, 85)
    )
    bayangan = bayangan.filter(ImageFilter.GaussianBlur(16))
    bg = Image.alpha_composite(bg, bayangan)

    # ---- Kartu ----
    kartu = Image.new("RGBA", (CW * S, CH * S), KARTU_RGB + (255,))
    d = ImageDraw.Draw(kartu)

    def lingkaran(cx, cy, r, warna):
        d.ellipse(
            [(cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S],
            fill=warna
        )

    # Panel kiri putih
    d.rectangle([0, 0, 470 * S, CH * S], fill=(255, 255, 255))

    # Lengkungan area form (biru tua menjorok ke panel putih)
    d.ellipse([350 * S, -45 * S, 830 * S, 555 * S], fill=KARTU_RGB)

    # Lingkaran dekoratif
    lingkaran(30, 500, 125, BIRU_PUDAR)
    lingkaran(305, 435, 70, BIRU_PUDAR)
    lingkaran(790, 485, 70, KARTU_FIELD_RGB)

    # Logo
    warna_badge = (255, 255, 255)
    logo = None
    lokasi = cari_logo()

    if lokasi is not None:
        try:
            logo = Image.open(lokasi).convert("RGB")
            warna_badge = logo.getpixel((2, 2))

            selisih = ImageChops.difference(
                logo, Image.new("RGB", logo.size, warna_badge)
            )
            kotak = selisih.point(lambda p: 255 if p > 12 else 0).getbbox()

            if kotak:
                logo = logo.crop(kotak)

        except (OSError, ValueError):
            logo = None

    bx, by, br = 185, 205, 128

    # Lingkaran tipis di belakang badge supaya logo terlihat jelas
    lingkaran(bx, by, br + 14, BIRU_PUDAR)
    lingkaran(bx, by, br, warna_badge)

    if logo is not None:
        lebar = 205 * S
        tinggi = int(logo.height * lebar / logo.width)
        logo = logo.resize((lebar, tinggi), Image.LANCZOS)
        kartu.paste(logo, (bx * S - lebar // 2, by * S - tinggi // 2))

    # Mask sudut membulat
    mask = Image.new("L", kartu.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, CW * S - 1, CH * S - 1], radius=24 * S, fill=255
    )
    kartu.putalpha(mask)
    kartu = kartu.resize((CW, CH), Image.LANCZOS)

    bg.paste(kartu, (CX, CY), kartu)

    return bg.convert("RGB"), logo is not None


def buat_kotak(w, h, fill, outline=None, r=10, ikon=None,
               warna_ikon=(200, 220, 245)):
    """Kotak membulat (field / tombol) dengan ikon opsional."""

    s = 4
    img = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    if outline:
        d.rounded_rectangle(
            [0, 0, w * s - 1, h * s - 1], radius=r * s,
            fill=fill, outline=outline, width=2 * s
        )
    else:
        d.rounded_rectangle(
            [0, 0, w * s - 1, h * s - 1], radius=r * s, fill=fill
        )

    cx, cy = 26 * s, (h // 2) * s

    if ikon == "user":
        d.ellipse([cx - 5 * s, cy - 11 * s, cx + 5 * s, cy - 1 * s],
                  fill=warna_ikon)
        d.pieslice([cx - 10 * s, cy + 1 * s, cx + 10 * s, cy + 21 * s],
                   180, 360, fill=warna_ikon)

    elif ikon == "lock":
        d.arc([cx - 6 * s, cy - 12 * s, cx + 6 * s, cy + 3 * s],
              180, 360, fill=warna_ikon, width=2 * s)
        d.rounded_rectangle([cx - 9 * s, cy - 2 * s, cx + 9 * s, cy + 10 * s],
                            radius=2 * s, fill=warna_ikon)

    return img.resize((w, h), Image.LANCZOS)


def buat_segmen(w, h, n, aktif):
    """Tombol pilihan jenis akun (segmen aktif berwarna putih)."""

    s = 4
    img = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    d.rounded_rectangle(
        [0, 0, w * s - 1, h * s - 1], radius=10 * s, fill=KARTU_FIELD_RGB
    )

    lebar = (w - 8) / n
    x0 = 4 + lebar * aktif

    d.rounded_rectangle(
        [x0 * s, 4 * s, (x0 + lebar) * s - 1, (h - 4) * s - 1],
        radius=8 * s, fill=(255, 255, 255)
    )

    return img.resize((w, h), Image.LANCZOS)


# ==================================================
# MODEL LOGIN ANGGOTA
# ==================================================

class LoginAnggota:

    def __init__(self):
        self.db = Database()

    def verifikasi_password(self, password, password_hash):

        try:
            algoritma, iterasi, salt, hash_asli = password_hash.split("$")

            if algoritma != "pbkdf2_sha256":
                return False

            iterasi = int(iterasi)

            if iterasi <= 0 or iterasi > 2000000:
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

    def autentikasi(self, username, password):

        username = username.strip()

        if not username or not password:
            raise ValueError("Username dan password wajib diisi.")

        conn = self.db.hubungkan()
        cursor = None

        try:
            cursor = conn.cursor()

            # SESUAIKAN nama kolom password jika berbeda di tabel anggota.
            cursor.execute("""
                SELECT
                    id_anggota,
                    nama,
                    username,
                    password_hash
                FROM anggota
                WHERE username = %s
            """, (username,))

            data = cursor.fetchone()

            if data is None:
                raise ValueError("Username atau password salah.")

            id_anggota, nama, username_db, password_hash = data

            if not self.verifikasi_password(password, password_hash):
                raise ValueError("Username atau password salah.")

            return {
                "id_anggota": id_anggota,
                "nama": nama,
                "username": username_db,
                "role": "anggota"
            }

        finally:
            if cursor is not None:
                cursor.close()

            conn.close()


# ==================================================
# GUI LOGIN ANGGOTA
# ==================================================

class AppLoginAnggota:

    def __init__(self, root, on_login_success=None):

        self.root = root
        self.model = LoginAnggota()
        self.on_login_success = on_login_success

        self.root.title("Sign in Anggota | Perpustakaan Digital")
        self.root.geometry(f"{W}x{H}")
        self.root.resizable(False, False)

        self.var_username = tk.StringVar()
        self.var_password = tk.StringVar()
        self.var_lihat_password = tk.BooleanVar(value=False)
        self.var_ingat = tk.BooleanVar(value=False)

        self.role_index = 0
        self.gambar = []

        self.buat_tampilan()
        self.muat_username_tersimpan()
        self.posisikan_jendela()

    def posisikan_jendela(self):

        self.root.update_idletasks()

        x = (self.root.winfo_screenwidth() - W) // 2
        y = (self.root.winfo_screenheight() - H) // 2

        self.root.geometry(f"{W}x{H}+{x}+{y}")

    # ==================== TAMPILAN UTAMA ====================

    def buat_tampilan(self):

        self.canvas = tk.Canvas(
            self.root, width=W, height=H, highlightthickness=0, bd=0
        )
        self.canvas.pack()

        bg, ada_logo = buat_background()
        self.bg_img = ImageTk.PhotoImage(bg)
        self.canvas.create_image(0, 0, image=self.bg_img, anchor="nw")

        if not ada_logo:
            self.canvas.create_text(
                CX + 185, CY + 205,
                text="Logo tidak ditemukan",
                font=("Segoe UI", 10),
                fill=ABU
            )

        self.buat_form()

        self.canvas.create_text(
            W // 2, CY + CH + 38,
            text="Sistem Informasi Manajemen Perpustakaan",
            font=("Segoe UI", 8),
            fill=ABU
        )

    # ==================== FORM LOGIN ====================

    def buat_form(self):

        c = self.canvas

        c.create_text(
            FX, CY + 84, anchor="nw",
            text="Sign in",
            font=("Segoe UI", 25, "bold"),
            fill=PUTIH
        )

        c.create_text(
            FX, CY + 136, anchor="nw",
            text="Masuk untuk menjelajahi katalog buku",
            font=("Segoe UI", 9),
            fill=TEKS_TERANG
        )

        self.buat_pilihan_role(CY + 170)

        self.entry_username, _ = self.buat_field(
            CY + 226, "user", "Username", self.var_username
        )
        self.entry_password, self.lbl_show = self.buat_field(
            CY + 286, "lock", "Password", self.var_password,
            show="*", toggle=True
        )

        # Ingat saya
        cek = tk.Checkbutton(
            c,
            text="Ingat saya",
            variable=self.var_ingat,
            font=("Segoe UI", 8),
            bg=KARTU,
            fg=TEKS_LEMBUT,
            activebackground=KARTU,
            activeforeground=PUTIH,
            selectcolor=PUTIH,
            cursor="hand2",
            relief="flat",
            bd=0,
            highlightthickness=0
        )
        c.create_window(FX - 4, CY + 356, window=cek, anchor="w")

        # Lupa password
        lupa = tk.Label(
            c,
            text="Lupa password?",
            font=("Segoe UI", 8, "bold"),
            bg=KARTU,
            fg=LINK,
            cursor="hand2"
        )
        lupa.bind("<Button-1>", lambda e: self.lupa_password())
        c.create_window(FX + FW, CY + 356, window=lupa, anchor="e")

        # Tombol sign in
        self.buat_tombol(CY + 380, "Sign in", self.proses_login)

        self.root.bind("<Return>", lambda event: self.proses_login())
        self.entry_username.focus_set()

    # ==================== PILIHAN JENIS AKUN ====================

    def buat_pilihan_role(self, y):

        c = self.canvas

        h = 40
        n = len(DAFTAR_ROLE)
        lebar = (FW - 8) / n

        self.img_role = [
            ImageTk.PhotoImage(buat_segmen(FW, h, n, i)) for i in range(n)
        ]

        self.item_role = c.create_image(
            FX, y, image=self.img_role[0], anchor="nw"
        )

        self.teks_role = []

        for i, (label, _) in enumerate(DAFTAR_ROLE):
            t = c.create_text(
                FX + 4 + lebar * i + lebar / 2, y + h / 2,
                text=label,
                font=("Segoe UI", 10, "bold")
            )
            self.teks_role.append(t)

        self.pilih_role(0)

    def pilih_role(self, index):

        self.role_index = index
        self.canvas.itemconfigure(self.item_role, image=self.img_role[index])

        for i, t in enumerate(self.teks_role):
            self.canvas.itemconfigure(
                t, fill=NAVY if i == index else TEKS_TERANG
            )

    # ==================== FIELD INPUT ====================

    def buat_field(self, y, ikon, placeholder, var, show=None, toggle=False):

        c = self.canvas
        h = 46

        normal = ImageTk.PhotoImage(
            buat_kotak(FW, h, KARTU_FIELD_RGB, ikon=ikon,
                       warna_ikon=(200, 220, 245))
        )
        fokus = ImageTk.PhotoImage(
            buat_kotak(FW, h, (255, 255, 255), outline=BIRU, ikon=ikon,
                       warna_ikon=NAVY_RGB)
        )
        self.gambar += [normal, fokus]

        item = c.create_image(FX, y, image=normal, anchor="nw")

        kanan = 62 if toggle else 16

        entry = tk.Entry(
            c,
            textvariable=var,
            font=("Segoe UI", 10),
            bg=KARTU_FIELD,
            fg=PUTIH,
            insertbackground=PUTIH,
            relief="flat",
            bd=0,
            highlightthickness=0,
            show=show or ""
        )
        c.create_window(FX + 50, y + h / 2, window=entry, anchor="w",
                        width=FW - 50 - kanan, height=26)

        lbl = tk.Label(
            c, text=placeholder, font=("Segoe UI", 10),
            bg=KARTU_FIELD, fg=TEKS_TERANG, cursor="xterm"
        )
        lbl_win = c.create_window(FX + 50, y + h / 2, window=lbl, anchor="w")
        lbl.bind("<Button-1>", lambda e: entry.focus_set())

        def perbarui_placeholder(*_):
            c.itemconfigure(lbl_win, state="hidden" if var.get() else "normal")

        var.trace_add("write", perbarui_placeholder)

        lbl_show = None

        if toggle:
            lbl_show = tk.Label(
                c, text="SHOW", font=("Segoe UI", 8, "bold"),
                bg=KARTU_FIELD, fg=TEKS_LEMBUT, cursor="hand2"
            )
            lbl_show.bind("<Button-1>", lambda e: self.atur_password())
            c.create_window(FX + FW - 16, y + h / 2, window=lbl_show,
                            anchor="e")

        def saat_fokus(aktif):

            c.itemconfigure(item, image=fokus if aktif else normal)

            bg = PUTIH if aktif else KARTU_FIELD

            entry.config(
                bg=bg,
                fg=ABU_GELAP if aktif else PUTIH,
                insertbackground=BIRU if aktif else PUTIH
            )
            lbl.config(bg=bg, fg=ABU_PLACEHOLDER if aktif else TEKS_TERANG)

            if lbl_show is not None:
                lbl_show.config(bg=bg, fg=NAVY if aktif else TEKS_LEMBUT)

        entry.bind("<FocusIn>", lambda e: saat_fokus(True))
        entry.bind("<FocusOut>", lambda e: saat_fokus(False))

        perbarui_placeholder()

        return entry, lbl_show

    # ==================== TOMBOL ====================

    def buat_tombol(self, y, teks, perintah):

        c = self.canvas
        h = 44

        normal = ImageTk.PhotoImage(buat_kotak(FW, h, (255, 255, 255)))
        hover = ImageTk.PhotoImage(buat_kotak(FW, h, (219, 234, 254)))
        self.gambar += [normal, hover]

        tag = f"tombol_{y}"

        item = c.create_image(FX, y, image=normal, anchor="nw", tags=tag)
        c.create_text(FX + FW / 2, y + h / 2, text=teks,
                      font=("Segoe UI", 10, "bold"),
                      fill=NAVY, tags=tag)

        def masuk(_):
            c.itemconfigure(item, image=hover)
            c.config(cursor="hand2")

        def keluar(_):
            c.itemconfigure(item, image=normal)
            c.config(cursor="")

        c.tag_bind(tag, "<Enter>", masuk)
        c.tag_bind(tag, "<Leave>", keluar)
        c.tag_bind(tag, "<Button-1>", lambda e: perintah())

    # ==================== AKSI KECIL ====================

    def atur_password(self):

        lihat = not self.var_lihat_password.get()
        self.var_lihat_password.set(lihat)

        self.entry_password.config(show="" if lihat else "*")
        self.lbl_show.config(text="HIDE" if lihat else "SHOW")

    def lupa_password(self):

        self.info(
            "Lupa Password",
            "Silakan hubungi petugas perpustakaan\n"
            "untuk mereset password Anda."
        )

    def info(self, judul, pesan):

        messagebox.showinfo(judul, pesan, parent=self.root)

    # ==================== INGAT USERNAME ====================

    def muat_username_tersimpan(self):

        try:
            lokasi = Path(__file__).resolve().with_name(FILE_INGAT)

            if lokasi.exists():
                nama = lokasi.read_text(encoding="utf-8").strip()

                if nama:
                    self.var_username.set(nama)
                    self.var_ingat.set(True)
                    self.entry_password.focus_set()

        except OSError:
            pass

    def simpan_username(self, username):

        lokasi = Path(__file__).resolve().with_name(FILE_INGAT)

        try:
            if self.var_ingat.get():
                lokasi.write_text(username, encoding="utf-8")
            elif lokasi.exists():
                lokasi.unlink()

        except OSError:
            pass

    # ==================== PROSES LOGIN ====================

    def proses_login(self):

        username = self.var_username.get().strip()
        password = self.var_password.get()

        try:
            session = self.model.autentikasi(username, password)
            self.simpan_username(session["username"])

            # Tanpa callback: tampilkan informasi login saja.
            if self.on_login_success is None:

                messagebox.showinfo(
                    "Login Berhasil",
                    f"Selamat datang, {session['nama']}!\n\n"
                    f"Username : {session['username']}\n"
                    f"ID Anggota : {session['id_anggota']}",
                    parent=self.root
                )

                self.var_password.set("")
                self.entry_password.focus_set()
                return

            # Kirim data sesi, lalu hentikan mainloop
            # (jendela ditutup oleh pemanggil, seperti login petugas).
            self.on_login_success(session)
            self.root.quit()

        except ValueError as e:

            messagebox.showwarning(
                "Login Gagal", str(e), parent=self.root
            )

            self.var_password.set("")
            self.entry_password.focus_set()

        except Exception as e:

            messagebox.showerror(
                "Kesalahan",
                f"Tidak dapat melakukan login:\n{e}",
                parent=self.root
            )


# ==================================================
# PROGRAM UTAMA (uji coba tampilan login saja)
# ==================================================

if __name__ == "__main__":

    root = tk.Tk()
    app = AppLoginAnggota(root)
    root.mainloop()