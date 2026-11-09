import time
import tkinter as tk
from tkinter import messagebox
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageTk

from koneksi import Database


# ==================== PALET WARNA (SAMA DENGAN LOGIN) ====================

BIRU_TUA = "#17365D"
BIRU = "#2563EB"
BIRU_MUDA = "#EFF6FF"

PUTIH = "#FFFFFF"
LATAR = "#F1F5F9"
ABU = "#64748B"
ABU_GELAP = "#334155"
ABU_MUDA = "#E2E8F0"

# Warna RGB yang sama dengan panel kiri di halaman login
PANEL = (31, 100, 190)
LINGKARAN_TERANG = (46, 115, 203)
GRADIEN_ATAS = (31, 111, 208)
GRADIEN_BAWAH = (10, 72, 150)
MERAH = (185, 28, 28)
MERAH_HOVER = (220, 38, 38)

PANEL_HEX = "#1F64BE"
TEKS_MENU = "#DCE9FA"
TEKS_REDUP = "#BFD6F2"

SW = 250  # lebar sidebar
DURASI_ANIMASI = 0.22  # detik

NAMA_LOGO = ("assets.logo.logo-perpustakaan.png", "assets/logo/logo-perpustakaan.png")

QUERY_RINGKASAN = {
    "buku": "SELECT COUNT(*) FROM buku",

    "anggota": "SELECT COUNT(*) FROM anggota",

    "dipinjam": """
        SELECT COUNT(*) FROM peminjaman
        WHERE status_peminjaman = 'dipinjam'
    """,

    # Tanggal jatuh tempo ada di detail_peminjaman (per buku).
    "terlambat": """
        SELECT COUNT(DISTINCT p.id_peminjaman)
        FROM peminjaman AS p
        JOIN detail_peminjaman AS d
            ON d.peminjaman_id = p.id_peminjaman
        WHERE p.status_peminjaman = 'dipinjam'
          AND d.tanggal_kembali IS NULL
          AND d.tanggal_jatuh_tempo < CURDATE()
    """,
}


# ==================== MENU BERDASARKAN ROLE ====================

MENU = {
    "petugas": [
        "Beranda",
        "Data Buku",
        "Data Anggota",
        "Peminjaman",
        "Laporan",
        "Data Petugas",
        "Profil Saya",
    ],

    "operator": [
        "Beranda",
        "Data Buku",
        "Data Anggota",
        "Data Petugas",
        "Peminjaman",
        "Laporan Masuk",
        "Profil Saya",
    ],
}


# ==================================================
# FUNGSI GAMBAR (PIL)
# ==================================================

def cari_logo():
    folder = Path(__file__).resolve().parent

    for nama in NAMA_LOGO:
        lokasi = folder / nama

        if lokasi.exists():
            return lokasi

    return None


def buat_pil(w, h, fill, r=12):
    """Kotak membulat (anti-alias)."""

    s = 4

    img = Image.new("RGBA", (w * s, h * s), (0, 0, 0, 0))

    ImageDraw.Draw(img).rounded_rectangle(
        [0, 0, w * s - 1, h * s - 1],
        radius=r * s,
        fill=fill
    )

    return img.resize((w, h), Image.LANCZOS)


def buat_bulat(d, fill):
    """Lingkaran polos (anti-alias)."""

    s = 4

    img = Image.new("RGBA", (d * s, d * s), (0, 0, 0, 0))

    ImageDraw.Draw(img).ellipse(
        [0, 0, d * s - 1, d * s - 1],
        fill=fill
    )

    return img.resize((d, d), Image.LANCZOS)


def buat_hamburger(fill, ukuran=44):
    """Tombol ikon garis tiga (hamburger menu)."""

    s = 4
    u = ukuran * s

    img = Image.new("RGBA", (u, u), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    d.rounded_rectangle(
        [0, 0, u - 1, u - 1],
        radius=10 * s,
        fill=fill
    )

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
            [
                (cx - r) * s,
                (cy - r) * s,
                (cx + r) * s,
                (cy + r) * s
            ],
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
                logo,
                Image.new("RGB", logo.size, warna_badge)
            )

            kotak = selisih.point(
                lambda p: 255 if p > 12 else 0
            ).getbbox()

            if kotak:
                logo = logo.crop(kotak)

        except (OSError, ValueError):
            logo = None

    img = Image.new("RGBA", (d * s, d * s), (0, 0, 0, 0))

    ImageDraw.Draw(img).ellipse(
        [0, 0, d * s - 1, d * s - 1],
        fill=warna_badge
    )

    if logo is not None:
        lebar = int(d * s * 0.8)
        tinggi = int(logo.height * lebar / logo.width)

        if tinggi > d * s * 0.8:
            tinggi = int(d * s * 0.8)
            lebar = int(logo.width * tinggi / logo.height)

        logo = logo.resize((lebar, tinggi), Image.LANCZOS)

        img.paste(
            logo,
            ((d * s - lebar) // 2, (d * s - tinggi) // 2)
        )

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
            [
                (cx - r) * s,
                (cy - r) * s,
                (cx + r) * s,
                (cy + r) * s
            ],
            fill=(255, 255, 255, alpha)
        )

    lingkaran(w - 60, h + 10, 110, 22)
    lingkaran(w - 190, -10, 60, 18)
    lingkaran(40, h + 30, 70, 14)

    img = Image.alpha_composite(img, hiasan)

    mask = Image.new("L", img.size, 0)

    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, w * s - 1, h * s - 1],
        radius=20 * s,
        fill=255
    )

    img.putalpha(mask)

    return img.resize((w, h), Image.LANCZOS)


# ==================================================
# CLASS DASHBOARD
# ==================================================

class AppDashboard:

    def __init__(self, root, session):

        self.root = root
        self.session = session
        self.logout = False

        # Memastikan data sesi tersedia
        self.role = str(
            session.get("role", "")
        ).strip().lower()

        self.nama = session.get("nama", "Pengguna")
        self.username = session.get("username", "")

        self.id_petugas = (
            session.get("id_petugas")
            or session.get("id")
        )

        # Validasi role
        if self.role not in MENU:
            raise ValueError(
                f"Role pengguna tidak dikenali: {self.role}"
            )

        self.menu = MENU[self.role]
        self.aktif = "Beranda"

        self.sidebar_terbuka = True
        self.sedang_animasi = False
        self.posisi_x = SW
        self.redraw_banner = None

        # Pengaturan jendela
        self.root.title(
            f"Dashboard {self.role.capitalize()} | Perpustakaan Digital"
        )

        self.root.configure(bg=LATAR)

        # Tinggi minimum disesuaikan agar 7 menu tidak menimpa tombol Logout
        self.root.minsize(960, 600)

        # Penutupan jendela ditangani melalui fungsi sendiri
        self.root.protocol(
            "WM_DELETE_WINDOW",
            self.tutup_dashboard
        )

        self.siapkan_gambar()

        self.buat_sidebar()
        self.buat_area_utama()

        self.pilih_menu("Beranda")
        self.posisikan_jendela(1120, 680)

    # ==================== GAMBAR YANG DIPAKAI BERULANG ====================

    def siapkan_gambar(self):

        lebar_pil = SW - 36

        self.img_pil_aktif = ImageTk.PhotoImage(
            buat_pil(lebar_pil, 42, (255, 255, 255), r=12)
        )

        self.img_pil_hover = ImageTk.PhotoImage(
            buat_pil(lebar_pil, 42, LINGKARAN_TERANG, r=12)
        )

        self.img_chip = ImageTk.PhotoImage(
            buat_pil(128, 26, LINGKARAN_TERANG, r=13)
        )

        self.img_logout = ImageTk.PhotoImage(
            buat_pil(lebar_pil, 44, MERAH, r=12)
        )

        self.img_logout_hover = ImageTk.PhotoImage(
            buat_pil(lebar_pil, 44, MERAH_HOVER, r=12)
        )

        badge, self.ada_logo = buat_logo_badge(60)
        self.img_badge = ImageTk.PhotoImage(badge)

        self.img_avatar = ImageTk.PhotoImage(
            buat_bulat(40, (23, 54, 93))
        )

        self.img_burger = ImageTk.PhotoImage(
            buat_hamburger((255, 255, 255, 255))
        )

        self.img_burger_hover = ImageTk.PhotoImage(
            buat_hamburger((226, 236, 250, 255))
        )

        self.img_bg_sidebar = None
        self.tinggi_sidebar = 0

    # ==================== POSISI JENDELA ====================

    def posisikan_jendela(self, lebar, tinggi):

        self.root.update_idletasks()

        x = (
            self.root.winfo_screenwidth() - lebar
        ) // 2

        y = (
            self.root.winfo_screenheight() - tinggi
        ) // 2

        self.root.geometry(
            f"{lebar}x{tinggi}+{x}+{y}"
        )

    # ==================================================
    # SIDEBAR
    # ==================================================

    def buat_sidebar(self):

        self.side = tk.Canvas(
            self.root,
            width=SW,
            bg=PANEL_HEX,
            highlightthickness=0,
            bd=0
        )

        self.side.place(
            x=0,
            y=0,
            width=SW,
            relheight=1
        )

        self.item_pill = {}
        self.item_teks = {}

        # Sidebar digambar ulang mengikuti tinggi jendela
        self.side.bind(
            "<Configure>",
            self.gambar_sidebar
        )

    def gambar_sidebar(self, event=None):

        h = self.side.winfo_height()

        if h < 100 or h == self.tinggi_sidebar:
            return

        self.tinggi_sidebar = h

        c = self.side
        c.delete("all")

        self.item_pill = {}
        self.item_teks = {}

        # Latar panel + lingkaran dekoratif
        self.img_bg_sidebar = ImageTk.PhotoImage(
            buat_bg_sidebar(SW, h)
        )

        c.create_image(
            0,
            0,
            image=self.img_bg_sidebar,
            anchor="nw"
        )

        # Logo + nama aplikasi
        c.create_image(
            22,
            28,
            image=self.img_badge,
            anchor="nw"
        )

        c.create_text(
            94,
            58,
            anchor="w",
            text="Perpustakaan\nDigital",
            font=("Segoe UI", 13, "bold"),
            fill=PUTIH
        )

        # Label panel
        c.create_image(
            22,
            108,
            image=self.img_chip,
            anchor="nw"
        )

        c.create_text(
            22 + 64,
            108 + 13,
            text=f"Panel {self.role.capitalize()}",
            font=("Segoe UI", 8, "bold"),
            fill=PUTIH
        )

        # Daftar menu
        y0 = 160
        langkah = 48
        x = 18

        for i, nama in enumerate(self.menu):

            y = y0 + i * langkah
            tag = f"menu_{i}"

            pill = c.create_image(
                x,
                y,
                image=self.img_pil_hover,
                anchor="nw",
                state="hidden",
                tags=tag
            )

            teks = c.create_text(
                x + 20,
                y + 21,
                anchor="w",
                text=nama,
                font=("Segoe UI", 10),
                fill=TEKS_MENU,
                tags=tag
            )

            self.item_pill[nama] = pill
            self.item_teks[nama] = teks

            c.tag_bind(
                tag,
                "<Button-1>",
                lambda e, n=nama: self.pilih_menu(n)
            )

            c.tag_bind(
                tag,
                "<Enter>",
                lambda e, n=nama: self.hover_menu(n, True)
            )

            c.tag_bind(
                tag,
                "<Leave>",
                lambda e, n=nama: self.hover_menu(n, False)
            )

        # Tombol logout
        y_logout = h - 84

        logout = c.create_image(
            x,
            y_logout,
            image=self.img_logout,
            anchor="nw",
            tags="logout"
        )

        c.create_text(
            x + (SW - 36) / 2,
            y_logout + 22,
            text="Logout",
            font=("Segoe UI", 10, "bold"),
            fill=PUTIH,
            tags="logout"
        )

        def masuk(_):
            c.itemconfigure(logout, image=self.img_logout_hover)
            c.config(cursor="hand2")

        def keluar(_):
            c.itemconfigure(logout, image=self.img_logout)
            c.config(cursor="")

        c.tag_bind("logout", "<Enter>", masuk)
        c.tag_bind("logout", "<Leave>", keluar)

        c.tag_bind(
            "logout",
            "<Button-1>",
            lambda e: self.proses_logout()
        )

        # Teks kecil di bawah, seperti footer login
        c.create_text(
            SW // 2,
            h - 22,
            text="Sistem Informasi Manajemen\nPerpustakaan",
            font=("Segoe UI", 7),
            fill=TEKS_REDUP,
            justify="center"
        )

        self.warnai_menu()

    def atur_posisi(self, x):
        """Geser sidebar dan konten. x = lebar sidebar yang terlihat."""

        self.posisi_x = x

        self.side.place_configure(x=x - SW)

        self.utama.place_configure(
            x=x,
            width=-x
        )

    def toggle_sidebar(self):
        """Tutup / buka sidebar dengan animasi."""

        if self.sedang_animasi:
            return

        self.sidebar_terbuka = not self.sidebar_terbuka

        if self.sidebar_terbuka:

            # Membuka: konten bergeser mengikuti sidebar
            self.animasi_sidebar(self.posisi_x, SW)

        else:

            # Menutup: konten dilebarkan SEKALI di awal (sidebar masih
            # menutupi), lalu hanya sidebar yang digeser keluar. Dengan
            # begitu isi halaman tidak digambar ulang di setiap frame.
            self.utama.place_configure(x=0, width=0)

            tk.Misc.lift(self.side)

            self.root.update_idletasks()

            if self.redraw_banner is not None:
                self.redraw_banner()

            self.geser_sidebar_keluar(0, -SW)

    def geser_sidebar_keluar(self, dari, ke, mulai=None):

        if mulai is None:
            mulai = time.perf_counter()
            self.sedang_animasi = True

        t = (time.perf_counter() - mulai) / DURASI_ANIMASI

        if t >= 1:
            x = ke
        else:
            x = dari + (ke - dari) * (1 - (1 - t) ** 3)

        self.side.place_configure(x=int(round(x)))

        if t < 1:

            self.root.after(
                8,
                lambda: self.geser_sidebar_keluar(dari, ke, mulai)
            )

            return

        self.posisi_x = 0
        self.sedang_animasi = False

    def animasi_sidebar(self, dari, ke, mulai=None):

        if mulai is None:
            mulai = time.perf_counter()
            self.sedang_animasi = True

        t = (time.perf_counter() - mulai) / DURASI_ANIMASI

        if t >= 1:
            x = ke
        else:
            # ease-out cubic: cepat di awal, melambat di akhir
            x = dari + (ke - dari) * (1 - (1 - t) ** 3)

        self.atur_posisi(int(round(x)))

        if t < 1:

            self.root.after(
                8,
                lambda: self.animasi_sidebar(dari, ke, mulai)
            )

            return

        self.sedang_animasi = False

        # Gambar ulang banner sekali saja setelah animasi selesai
        if self.redraw_banner is not None:
            self.redraw_banner()

    def warnai_menu(self):

        for nama, pill in self.item_pill.items():

            teks = self.item_teks[nama]

            if nama == self.aktif:

                self.side.itemconfigure(
                    pill,
                    image=self.img_pil_aktif,
                    state="normal"
                )

                self.side.itemconfigure(
                    teks,
                    fill=BIRU_TUA,
                    font=("Segoe UI", 10, "bold")
                )

            else:

                self.side.itemconfigure(
                    pill,
                    state="hidden"
                )

                self.side.itemconfigure(
                    teks,
                    fill=TEKS_MENU,
                    font=("Segoe UI", 10)
                )

    def hover_menu(self, nama, masuk):

        self.side.config(
            cursor="hand2" if masuk else ""
        )

        if nama == self.aktif:
            return

        pill = self.item_pill.get(nama)

        if pill is None:
            return

        if masuk:

            self.side.itemconfigure(
                pill,
                image=self.img_pil_hover,
                state="normal"
            )

        else:

            self.side.itemconfigure(
                pill,
                state="hidden"
            )

    # ==================================================
    # AREA UTAMA
    # ==================================================

    def buat_area_utama(self):

        utama = tk.Frame(
            self.root,
            bg=LATAR
        )

        self.utama = utama

        utama.place(
            x=SW,
            y=0,
            relwidth=1,
            width=-SW,
            relheight=1
        )

        # Top bar
        topbar = tk.Frame(
            utama,
            bg=PUTIH,
            height=70
        )

        topbar.pack(fill="x")
        topbar.pack_propagate(False)

        # Tombol hamburger untuk membuka / menutup sidebar
        tombol_burger = tk.Label(
            topbar,
            image=self.img_burger,
            bg=PUTIH,
            bd=0,
            cursor="hand2"
        )

        tombol_burger.pack(
            side="left",
            padx=(20, 0)
        )

        tombol_burger.bind(
            "<Button-1>",
            lambda e: self.toggle_sidebar()
        )

        tombol_burger.bind(
            "<Enter>",
            lambda e: tombol_burger.config(image=self.img_burger_hover)
        )

        tombol_burger.bind(
            "<Leave>",
            lambda e: tombol_burger.config(image=self.img_burger)
        )

        self.judul = tk.Label(
            topbar,
            text="Dashboard",
            font=("Segoe UI", 18, "bold"),
            bg=PUTIH,
            fg=BIRU_TUA
        )

        self.judul.pack(
            side="left",
            padx=16
        )

        # Info pengguna: avatar bulat + nama
        info = tk.Frame(
            topbar,
            bg=PUTIH
        )

        info.pack(
            side="right",
            padx=28
        )

        inisial = (self.nama.strip()[:1] or "?").upper()

        tk.Label(
            info,
            image=self.img_avatar,
            text=inisial,
            compound="center",
            font=("Segoe UI", 12, "bold"),
            fg=PUTIH,
            bg=PUTIH,
            bd=0
        ).pack(side="right", padx=(12, 0))

        teks_info = tk.Frame(
            info,
            bg=PUTIH
        )

        teks_info.pack(side="right")

        tk.Label(
            teks_info,
            text=self.nama,
            font=("Segoe UI", 10, "bold"),
            bg=PUTIH,
            fg=ABU_GELAP,
            anchor="e"
        ).pack(anchor="e")

        tk.Label(
            teks_info,
            text=f"{self.role.capitalize()}  ·  @{self.username}",
            font=("Segoe UI", 8),
            bg=PUTIH,
            fg=ABU,
            anchor="e"
        ).pack(anchor="e")

        # Avatar dan nama di pojok kanan atas dapat diklik -> Profil Saya
        def pasang_klik(widget):

            widget.config(cursor="hand2")

            widget.bind(
                "<Button-1>",
                lambda e: self.pilih_menu("Profil Saya")
            )

            for anak in widget.winfo_children():
                pasang_klik(anak)

        pasang_klik(info)

        tk.Frame(
            utama,
            bg=ABU_MUDA,
            height=1
        ).pack(fill="x")

        # Tempat isi halaman
        self.konten = tk.Frame(
            utama,
            bg=LATAR
        )

        self.konten.pack(
            fill="both",
            expand=True
        )

    # ==================================================
    # NAVIGASI HALAMAN
    # ==================================================

    def pilih_menu(self, nama):

        self.aktif = nama

        self.warnai_menu()

        self.judul.config(
            text="Dashboard" if nama == "Beranda" else nama
        )

        # Hapus halaman sebelumnya
        self.redraw_banner = None

        for widget in self.konten.winfo_children():
            widget.destroy()

        # Beranda
        if nama == "Beranda":

            wadah = tk.Frame(
                self.konten,
                bg=LATAR
            )

            wadah.pack(
                fill="both",
                expand=True,
                padx=28,
                pady=24
            )

            self.halaman_beranda(wadah)
            return

        # Halaman data
        wadah = tk.Frame(
            self.konten,
            bg=LATAR
        )

        wadah.pack(
            fill="both",
            expand=True
        )

        try:
            self.buka_halaman(nama, wadah)

        except Exception as e:

            wadah.destroy()

            messagebox.showerror(
                "Gagal Membuka Halaman",
                f"Halaman {nama} tidak dapat dimuat:\n\n{e}",
                parent=self.root
            )

            self.halaman_kosong(
                nama,
                f"Halaman {nama} gagal dimuat."
            )

    def buka_halaman(self, nama, induk):
        """
        Memuat halaman sesuai menu yang dipilih.
        Import dilakukan saat halaman dibuka agar
        kesalahan satu modul tidak langsung menghalangi
        dashboard ditampilkan.
        """

        if nama == "Data Buku":

            from buku.app_buku import AplikasiPerpustakaan

            # Operator: CRUD penuh. Petugas: hanya melihat.
            AplikasiPerpustakaan(
                induk,
                hanya_lihat=(self.role == "petugas")
            )

        elif nama == "Data Anggota":

            from anggota.app_anggota import AppAnggota

            AppAnggota(induk)

        elif nama == "Peminjaman":

            from peminjaman.app_peminjaman import AppPeminjaman

            # Petugas: CRUD penuh. Operator: hanya melihat.
            AppPeminjaman(
                induk,
                self.id_petugas,
                hanya_lihat=(self.role == "operator")
            )

        elif nama == "Laporan":

            if self.role != "petugas":
                raise PermissionError(
                    "Anda tidak memiliki akses ke halaman Laporan."
                )

            from laporan.app_laporan import HalamanLaporan

            HalamanLaporan(self, induk)

        elif nama == "Laporan Masuk":

            if self.role != "operator":
                raise PermissionError(
                    "Halaman Laporan Masuk khusus untuk operator."
                )

            from laporan.laporan_masuk import HalamanLaporanMasuk

            HalamanLaporanMasuk(self, induk)

        elif nama == "Data Petugas":

            from petugas.app_petugas import AppPetugas

            # Operator: CRUD penuh. Petugas: hanya melihat.
            AppPetugas(
                induk,
                hanya_lihat=(self.role == "petugas"),
                id_sendiri=self.id_petugas
            )

        elif nama == "Profil Saya":

            from petugas.profil_petugas import HalamanProfilPetugas

            HalamanProfilPetugas(self, induk)

        else:

            raise ValueError(
                f"Menu {nama} tidak ditemukan."
            )

    # ==================================================
    # BERANDA
    # ==================================================

    def ambil_ringkasan(self):
        """
        Mengambil angka ringkasan dari database.
        Bila sebuah query gagal, nilainya "–" dan Beranda tetap tampil.
        """

        hasil = {kunci: "–" for kunci in QUERY_RINGKASAN}

        try:
            conn = Database().hubungkan()
        except Exception as e:
            print(f"[Beranda] Gagal terhubung ke database: {e}")
            return hasil

        try:
            for kunci, query in QUERY_RINGKASAN.items():

                cursor = None

                try:
                    cursor = conn.cursor()
                    cursor.execute(query)
                    baris = cursor.fetchone()
                    hasil[kunci] = str(baris[0]) if baris else "0"

                except Exception as e:
                    print(f"[Beranda] Query '{kunci}' gagal: {e}")

                finally:
                    if cursor is not None:
                        cursor.close()

        finally:
            conn.close()

        return hasil

    def strip_laporan_baru(self, induk):
        """Pemberitahuan laporan baru dari petugas (khusus operator)."""

        try:
            from laporan.laporan_kirim import LaporanTerkirim

            jumlah = LaporanTerkirim().jumlah_baru()

        except Exception as e:
            print(f"[Beranda] Gagal memeriksa laporan baru: {e}")
            return

        if not jumlah:
            return

        strip = tk.Frame(induk, bg="#DBEAFE", padx=16, pady=10)
        strip.pack(fill="x", pady=(14, 0))

        tk.Label(
            strip,
            text=f"Ada {jumlah} laporan baru dari petugas.",
            font=("Segoe UI", 9, "bold"),
            bg="#DBEAFE", fg="#1D4ED8"
        ).pack(side="left")

        buka = tk.Label(
            strip, text="Buka Laporan Masuk  →",
            font=("Segoe UI", 9, "bold"),
            bg="#DBEAFE", fg="#1D4ED8", cursor="hand2"
        )
        buka.pack(side="right")

        buka.bind(
            "<Button-1>",
            lambda e: self.pilih_menu("Laporan Masuk")
        )

    def halaman_beranda(self, induk):

        # Banner sambutan (gradient biru seperti background login)
        banner = tk.Canvas(
            induk,
            height=140,
            bg=LATAR,
            highlightthickness=0,
            bd=0
        )

        banner.pack(fill="x")

        lebar_terakhir = [0]

        def gambar_banner(event=None):

            if self.sedang_animasi:
                return

            try:
                w = banner.winfo_width()
            except tk.TclError:
                return

            if w < 100 or w == lebar_terakhir[0]:
                return

            lebar_terakhir[0] = w

            banner.delete("all")

            self.img_banner = ImageTk.PhotoImage(
                buat_banner(w, 140)
            )

            banner.create_image(
                0,
                0,
                image=self.img_banner,
                anchor="nw"
            )

            banner.create_text(
                34,
                52,
                anchor="w",
                text=f"Selamat datang, {self.nama}!",
                font=("Segoe UI", 20, "bold"),
                fill=PUTIH
            )

            banner.create_text(
                34,
                90,
                anchor="w",
                text=f"Anda masuk sebagai {self.role.capitalize()}.",
                font=("Segoe UI", 10),
                fill="#DBEAFE"
            )

        jadwal = [None]

        def saat_ubah(event=None):

            # Tunda sedikit agar tidak menggambar ulang di setiap perubahan ukuran
            if jadwal[0] is not None:
                banner.after_cancel(jadwal[0])

            jadwal[0] = banner.after(40, gambar_banner)

        banner.bind("<Configure>", saat_ubah)

        self.redraw_banner = gambar_banner

        # Pemberitahuan laporan baru (khusus operator)
        if self.role == "operator":
            self.strip_laporan_baru(induk)

        # Kartu ringkasan
        baris = tk.Frame(
            induk,
            bg=LATAR
        )

        baris.pack(
            fill="x",
            pady=(22, 0)
        )

        ringkasan = [
            ("Total Buku", "#2563EB", "buku"),
            ("Total Anggota", "#0EA5E9", "anggota"),
            ("Sedang Dipinjam", "#F59E0B", "dipinjam"),
            ("Terlambat", "#DC2626", "terlambat"),
        ]

        data = self.ambil_ringkasan()

        for i, (judul, warna, kunci) in enumerate(ringkasan):

            baris.columnconfigure(
                i,
                weight=1,
                uniform="kartu"
            )

            kartu = tk.Frame(
                baris,
                bg=PUTIH,
                highlightbackground=ABU_MUDA,
                highlightthickness=1
            )

            kartu.grid(
                row=0,
                column=i,
                sticky="nsew",
                padx=(
                    0 if i == 0 else 8,
                    0 if i == len(ringkasan) - 1 else 8
                )
            )

            # Garis warna di sisi kiri kartu
            tk.Frame(
                kartu,
                bg=warna,
                width=5
            ).pack(side="left", fill="y")

            isi = tk.Frame(
                kartu,
                bg=PUTIH,
                padx=18,
                pady=18
            )

            isi.pack(side="left", fill="both", expand=True)

            tk.Label(
                isi,
                text=judul,
                font=("Segoe UI", 9),
                bg=PUTIH,
                fg=ABU
            ).pack(anchor="w")

            nilai = data.get(kunci, "–")

            # Angka terlambat dibuat merah bila ada
            warna_nilai = (
                "#DC2626"
                if kunci == "terlambat" and nilai not in ("–", "0")
                else BIRU_TUA
            )

            tk.Label(
                isi,
                text=nilai,
                font=("Segoe UI", 24, "bold"),
                bg=PUTIH,
                fg=warna_nilai
            ).pack(
                anchor="w",
                pady=(6, 0)
            )

    # ==================================================
    # HALAMAN PLACEHOLDER
    # ==================================================

    def halaman_kosong(self, nama, pesan=None, induk=None):

        if induk is None:

            induk = tk.Frame(
                self.konten,
                bg=LATAR
            )

            induk.pack(
                fill="both",
                expand=True,
                padx=28,
                pady=24
            )

        kartu = tk.Frame(
            induk,
            bg=PUTIH,
            highlightbackground=ABU_MUDA,
            highlightthickness=1
        )

        kartu.pack(
            fill="x",
            padx=28,
            pady=24
        )

        tk.Frame(
            kartu,
            bg=BIRU,
            width=5
        ).pack(side="left", fill="y")

        isi = tk.Frame(
            kartu,
            bg=PUTIH,
            padx=24,
            pady=24
        )

        isi.pack(side="left", fill="both", expand=True)

        tk.Label(
            isi,
            text=nama,
            font=("Segoe UI", 14, "bold"),
            bg=PUTIH,
            fg=BIRU_TUA
        ).pack(anchor="w")

        tk.Label(
            isi,
            text=pesan or f"Halaman {nama} belum dibuat.",
            font=("Segoe UI", 10),
            bg=PUTIH,
            fg=ABU
        ).pack(
            anchor="w",
            pady=(6, 0)
        )

    # ==================================================
    # LOGOUT DAN TUTUP DASHBOARD
    # ==================================================

    def proses_logout(self):

        konfirmasi = messagebox.askyesno(
            "Logout",
            "Apakah Anda yakin ingin keluar dari akun ini?",
            parent=self.root
        )

        if konfirmasi:

            self.logout = True

            # Hentikan mainloop.
            # main.py akan menghancurkan jendela setelahnya.
            self.root.quit()

    def tutup_dashboard(self):

        self.logout = False

        # Tutup aplikasi tanpa kembali ke halaman login.
        self.root.quit()