import sys
from pathlib import Path

FOLDER_INI = Path(__file__).resolve().parent
ROOT_DIR = FOLDER_INI.parent

for _jalur in (FOLDER_INI, ROOT_DIR):
    if str(_jalur) not in sys.path:
        sys.path.insert(0, str(_jalur))

import tkinter as tk
from tkinter import ttk
from datetime import date, datetime

from PIL import (
    Image, ImageChops, ImageDraw, ImageFont, ImageOps
)

try:
    import pillow_avif  # noqa: F401
except ImportError:
    pass

import tema as t


# ==================== PALET WARNA (SAMA DENGAN DASHBOARD PETUGAS) ====================

BIRU_TUA = "#17365D"
BIRU = "#2563EB"
BIRU_MUDA = "#EFF6FF"

PUTIH = "#FFFFFF"
LATAR = "#F1F5F9"
ABU = "#64748B"
ABU_GELAP = "#334155"
ABU_MUDA = "#E2E8F0"

HIJAU = "#16A34A"
ORANYE = "#D97706"
MERAH_HEX = "#DC2626"

PANEL = (31, 100, 190)
LINGKARAN_TERANG = (46, 115, 203)
GRADIEN_ATAS = (31, 111, 208)
GRADIEN_BAWAH = (10, 72, 150)
MERAH = (185, 28, 28)
MERAH_HOVER = (220, 38, 38)

PANEL_HEX = "#1F64BE"
TEKS_MENU = "#DCE9FA"
TEKS_REDUP = "#BFD6F2"

SW = 250               # lebar sidebar
DURASI_ANIMASI = 0.22  # detik

# ==================== PENGATURAN ====================

MENU_ANGGOTA = ["Katalog Buku", "Jadwal Pengembalian", "Profil Saya"]

HARI_SEGERA = 3          # "segera jatuh tempo" bila sisa <= 3 hari
UKURAN_KARTU = (170, 230)
UKURAN_DETAIL = (250, 340)
UKURAN_MINI = (62, 84)

EKSTENSI_SAMPUL = (".jpg", ".jpeg", ".png", ".webp", ".avif")
NAMA_LOGO = (
    "assets/logo/logo-perpustakaan.png",
    "logo-perpustakaan.png",
)


def _folder_proyek():
    """Folder proyek = folder yang berisi 'assets' (file ini atau induknya)."""

    folder = Path(__file__).resolve().parent

    for kandidat in (folder, folder.parent):
        if (kandidat / "assets").exists():
            return kandidat

    return folder.parent


FOLDER_PROYEK = _folder_proyek()
FOLDER_SAMPUL = FOLDER_PROYEK / "assets" / "sampul"


# ==================================================
# TANGGAL & TEKS
# ==================================================

def ke_tanggal(nilai):

    if nilai is None or nilai == "":
        return None

    if isinstance(nilai, datetime):
        return nilai.date()

    if isinstance(nilai, date):
        return nilai

    for format_ in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d-%m-%Y"):
        try:
            return datetime.strptime(str(nilai), format_).date()
        except ValueError:
            continue

    return None


def format_tanggal(tanggal):
    return tanggal.strftime("%d-%m-%Y") if tanggal else "-"


def potong(teks, n):

    teks = str(teks)

    return teks if len(teks) <= n else teks[:n - 1].rstrip() + "…"


# ==================================================
# FUNGSI GAMBAR (PIL)
# ==================================================

def cari_logo():

    folder = Path(__file__).resolve().parent

    for induk in (folder, folder.parent):
        for nama in NAMA_LOGO:
            lokasi = induk / nama
            if lokasi.exists():
                return lokasi

    return None


def buat_pil(w, h, fill, r=12):
    """Kotak membulat (anti-alias)."""

    s = 4
    img = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))

    ImageDraw.Draw(img).rounded_rectangle(
        [0, 0, w * s - 1, h * s - 1], radius=r * s, fill=fill
    )

    return img.resize((w, h), Image.LANCZOS)


def buat_bulat(d, fill):
    """Lingkaran polos (anti-alias)."""

    s = 4
    img = Image.new("RGBA", (d * s, d * s), (0, 0, 0, 0))

    ImageDraw.Draw(img).ellipse([0, 0, d * s - 1, d * s - 1], fill=fill)

    return img.resize((d, d), Image.LANCZOS)


def buat_hamburger(fill, ukuran=44):
    """Tombol ikon garis tiga (hamburger menu)."""

    s = 4
    u = ukuran * s

    img = Image.new("RGBA", (u, u), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    d.rounded_rectangle([0, 0, u - 1, u - 1], radius=10 * s, fill=fill)

    lebar, tebal, jarak = 20 * s, 3 * s, 7 * s
    x0 = (u - lebar) // 2
    cy = u // 2

    for dy in (-jarak, 0, jarak):
        d.rounded_rectangle(
            [x0, cy + dy - tebal // 2, x0 + lebar, cy + dy + tebal // 2],
            radius=tebal // 2,
            fill=(23, 54, 93, 255)
        )

    return img.resize((ukuran, ukuran), Image.LANCZOS)


def buat_bg_sidebar(w, h):
    """Panel biru dengan lingkaran dekoratif, seperti sisi kiri login."""

    s = 2

    img = Image.new("RGBA", (w * s, h * s), PANEL + (255,))
    d = ImageDraw.Draw(img)

    def lingkaran(cx, cy, r, warna):
        d.ellipse(
            [(cx - r) * s, (cy - r) * s, (cx + r) * s, (cy + r) * s],
            fill=warna
        )

    lingkaran(20, h - 20, 125, LINGKARAN_TERANG)
    lingkaran(w - 10, h - 150, 55, LINGKARAN_TERANG)
    lingkaran(w - 30, 40, 38, LINGKARAN_TERANG)

    return img.resize((w, h), Image.LANCZOS)


def buat_logo_badge(d=60):
    """Badge bulat berisi logo (atau kosong bila logo tidak ada)."""

    s = 4
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

    img = Image.new("RGBA", (d * s, d * s), (0, 0, 0, 0))

    ImageDraw.Draw(img).ellipse([0, 0, d * s - 1, d * s - 1], fill=warna_badge)

    if logo is not None:
        lebar = int(d * s * 0.8)
        tinggi = int(logo.height * lebar / logo.width)

        if tinggi > d * s * 0.8:
            tinggi = int(d * s * 0.8)
            lebar = int(logo.width * tinggi / logo.height)

        logo = logo.resize((lebar, tinggi), Image.LANCZOS)
        img.paste(logo, ((d * s - lebar) // 2, (d * s - tinggi) // 2))

    return img.resize((d, d), Image.LANCZOS), logo is not None


def buat_banner(w, h):
    """Banner gradient biru dengan lingkaran dekoratif."""

    s = 2

    atas = Image.new("RGB", (w * s, h * s), GRADIEN_ATAS)
    bawah = Image.new("RGB", (w * s, h * s), GRADIEN_BAWAH)

    gradien = Image.linear_gradient("L").resize((w * s, h * s))
    img = Image.composite(bawah, atas, gradien).convert("RGBA")

    hiasan = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(hiasan)

    def lingkaran(cx, cy, r, alpha):
        d.ellipse(
            [(cx - r) * s, (cy - r) * s, (cx + r) * s, (cy + r) * s],
            fill=(255, 255, 255, alpha)
        )

    lingkaran(w - 60, h + 10, 110, 22)
    lingkaran(w - 190, -10, 60, 18)
    lingkaran(40, h + 30, 70, 14)

    img = Image.alpha_composite(img, hiasan)

    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, w * s - 1, h * s - 1], radius=20 * s, fill=255
    )
    img.putalpha(mask)

    return img.resize((w, h), Image.LANCZOS)


# ==================== SAMPUL BUKU ====================

PALET_SAMPUL = [
    ("#17365D", "#2563EB"),
    ("#0F5E59", "#2DAA96"),
    ("#5B21B6", "#A78BFA"),
    ("#B45309", "#FBBF24"),
    ("#9F1239", "#F472B6"),
    ("#1E40AF", "#60A5FA"),
]


def _font(ukuran, tebal=True):

    daftar = (
        ("segoeuib.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf")
        if tebal else
        ("segoeui.ttf", "arial.ttf", "DejaVuSans.ttf")
    )

    for nama in daftar:
        try:
            return ImageFont.truetype(nama, ukuran)
        except OSError:
            continue

    return ImageFont.load_default()


def _sampul_polos(kunci, judul, w, h, S):
    """Sampul pengganti bila buku belum punya gambar."""

    atas, bawah = PALET_SAMPUL[
        sum(ord(c) for c in str(kunci)) % len(PALET_SAMPUL)
    ]

    gradien = Image.linear_gradient("L").resize((w, h))
    img = Image.composite(
        Image.new("RGB", (w, h), bawah),
        Image.new("RGB", (w, h), atas),
        gradien
    )

    d = ImageDraw.Draw(img)

    # Punggung buku
    punggung = 14 * S
    d.rectangle([0, 0, punggung, h], fill=t.gelapkan(atas, 0.35))

    font = _font(int(h * 0.072))
    maks = (w - punggung) * 0.78

    baris, sekarang = [], ""

    for kata in str(judul).split():
        uji = (sekarang + " " + kata).strip()

        if sekarang and d.textlength(uji, font=font) > maks:
            baris.append(sekarang)
            sekarang = kata
        else:
            sekarang = uji

    if sekarang:
        baris.append(sekarang)

    baris = baris[:5]

    tinggi_baris = int(h * 0.095)
    y = int(h * 0.22)
    tengah = punggung + (w - punggung) / 2

    for teks in baris:
        lebar = d.textlength(teks, font=font)
        d.text((tengah - lebar / 2, y), teks, font=font, fill="#FFFFFF")
        y += tinggi_baris

    d.line(
        [tengah - w * 0.12, y + tinggi_baris * 0.2,
         tengah + w * 0.12, y + tinggi_baris * 0.2],
        fill="#FFFFFF", width=max(2, S)
    )

    kecil = _font(int(h * 0.04), tebal=False)
    teks = "PERPUSTAKAAN DIGITAL"
    lebar = d.textlength(teks, font=kecil)
    d.text((tengah - lebar / 2, h * 0.92), teks, font=kecil, fill="#DCE8F8")

    return img


def buat_gambar_sampul(kunci, judul, w, h):
    """Gambar sampul dari assets/sampul/<id_buku>.jpg, atau sampul pengganti."""

    S = 3
    gambar = None

    for ekstensi in EKSTENSI_SAMPUL:
        lokasi = FOLDER_SAMPUL / f"{kunci}{ekstensi}"

        if lokasi.exists():
            try:
                gambar = ImageOps.fit(
                    Image.open(lokasi).convert("RGB"),
                    (w * S, h * S),
                    Image.LANCZOS
                )
            except Exception as e:
                # Format tidak didukung / file rusak -> pakai sampul pengganti
                print(f"[Sampul] Gagal membuka {lokasi.name}: {e}")
                gambar = None
            break

    if gambar is None:
        gambar = _sampul_polos(kunci, judul, w * S, h * S, S)

    mask = Image.new("L", gambar.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, gambar.width - 1, gambar.height - 1],
        radius=12 * S, fill=255
    )

    gambar = gambar.convert("RGBA")
    gambar.putalpha(mask)

    return gambar.resize((w, h), Image.LANCZOS)


# ==================================================
# AREA YANG BISA DIGULIR
# ==================================================

class AreaGulir:
    """Kanvas dengan scrollbar. Isi diletakkan di `self.isi`."""

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
        self.canvas.bind("<Configure>", self._ubah_lebar)

        self.pada_lebar = None

    def _ubah_lebar(self, event):

        self.canvas.itemconfigure(self.jendela, width=event.width)

        if self.pada_lebar is not None:
            self.pada_lebar(event.width)

    def lebar(self):
        return self.canvas.winfo_width()

    def ke_atas(self):
        self.canvas.yview_moveto(0)

    def gulir(self, event):
        """Dipanggil dari bind_all roda mouse milik dashboard."""

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

        except tk.TclError:
            pass