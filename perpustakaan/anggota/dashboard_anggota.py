import sys
from pathlib import Path

FOLDER_INI = Path(__file__).resolve().parent
ROOT_DIR = FOLDER_INI.parent

for _jalur in (FOLDER_INI, ROOT_DIR):
    if str(_jalur) not in sys.path:
        sys.path.insert(0, str(_jalur))

import time
import tkinter as tk
from tkinter import messagebox

from PIL import ImageTk

import tema as t

from umum_anggota import (
    BIRU_TUA, ABU, ABU_GELAP, ABU_MUDA, PUTIH, LATAR,
    LINGKARAN_TERANG, MERAH, MERAH_HOVER,
    PANEL_HEX, TEKS_MENU, TEKS_REDUP,
    SW, DURASI_ANIMASI, MENU_ANGGOTA,
    buat_pil, buat_bulat, buat_hamburger, buat_bg_sidebar,
    buat_logo_badge, buat_gambar_sampul,
)

class AppDashboardAnggota:
    def __init__(self, root, session):

        self.root = root
        self.session = session
        self.logout = False

        self.role = "anggota"
        self.nama = session.get("nama", "Anggota")
        self.username = session.get("username", "")
        self.id_anggota = session.get("id_anggota")

        self.menu = MENU_ANGGOTA
        self.aktif = self.menu[0]

        self.sidebar_terbuka = True
        self.sedang_animasi = False
        self.posisi_x = SW

        # Dipakai bersama oleh halaman-halaman
        self.redraw_banner = None      # diisi halaman yang punya banner
        self.area_gulir = None         # diisi halaman yang bisa digulir
        self.halaman_aktif = None      # menjaga objek halaman tetap hidup
        self.cache_gambar = {}
        self.filter_simpan = ("", "Semua kategori")  # filter katalog

        self.root.title("Dashboard Anggota | Perpustakaan Digital")
        self.root.configure(bg=LATAR)
        self.root.minsize(960, 600)

        self.root.protocol("WM_DELETE_WINDOW", self.tutup_dashboard)

        t.terapkan_style(self.root)

        # Roda mouse untuk area gulir yang sedang aktif
        self.root.bind_all("<MouseWheel>", self._roda_mouse)

        self.siapkan_gambar()

        self.buat_sidebar()
        self.buat_area_utama()

        self.pilih_menu(self.aktif)
        self.posisikan_jendela(1180, 720)

    def _roda_mouse(self, event):

        if self.area_gulir is not None:
            self.area_gulir.gulir(event)

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

        self.img_avatar = ImageTk.PhotoImage(buat_bulat(40, (23, 54, 93)))

        self.img_burger = ImageTk.PhotoImage(
            buat_hamburger((255, 255, 255, 255))
        )
        self.img_burger_hover = ImageTk.PhotoImage(
            buat_hamburger((226, 236, 250, 255))
        )

        self.img_bg_sidebar = None
        self.tinggi_sidebar = 0

    def sampul(self, id_buku, judul, ukuran):
        """PhotoImage sampul (di-cache supaya tidak dibuat berulang)."""

        kunci = (id_buku, ukuran)

        if kunci not in self.cache_gambar:
            self.cache_gambar[kunci] = ImageTk.PhotoImage(
                buat_gambar_sampul(id_buku, judul, ukuran[0], ukuran[1])
            )

        return self.cache_gambar[kunci]

    # ==================== POSISI JENDELA ====================

    def posisikan_jendela(self, lebar, tinggi):

        self.root.update_idletasks()

        x = (self.root.winfo_screenwidth() - lebar) // 2
        y = (self.root.winfo_screenheight() - tinggi) // 2

        self.root.geometry(f"{lebar}x{tinggi}+{x}+{y}")

    # ==================================================
    # SIDEBAR
    # ==================================================

    def buat_sidebar(self):

        self.side = tk.Canvas(
            self.root, width=SW, bg=PANEL_HEX, highlightthickness=0, bd=0
        )

        self.side.place(x=0, y=0, width=SW, relheight=1)

        self.item_pill = {}
        self.item_teks = {}

        self.side.bind("<Configure>", self.gambar_sidebar)

    def gambar_sidebar(self, event=None):

        h = self.side.winfo_height()

        if h < 100 or h == self.tinggi_sidebar:
            return

        self.tinggi_sidebar = h

        c = self.side
        c.delete("all")

        self.item_pill = {}
        self.item_teks = {}

        self.img_bg_sidebar = ImageTk.PhotoImage(buat_bg_sidebar(SW, h))
        c.create_image(0, 0, image=self.img_bg_sidebar, anchor="nw")

        # Logo + nama aplikasi
        c.create_image(22, 28, image=self.img_badge, anchor="nw")

        c.create_text(
            94, 58, anchor="w",
            text="Perpustakaan\nDigital",
            font=("Segoe UI", 13, "bold"),
            fill=PUTIH
        )

        # Label panel
        c.create_image(22, 108, image=self.img_chip, anchor="nw")

        c.create_text(
            22 + 64, 108 + 13,
            text="Panel Anggota",
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
                x, y, image=self.img_pil_hover, anchor="nw",
                state="hidden", tags=tag
            )

            teks = c.create_text(
                x + 20, y + 21, anchor="w",
                text=nama,
                font=("Segoe UI", 10),
                fill=TEKS_MENU,
                tags=tag
            )

            self.item_pill[nama] = pill
            self.item_teks[nama] = teks

            c.tag_bind(tag, "<Button-1>", lambda e, n=nama: self.pilih_menu(n))
            c.tag_bind(tag, "<Enter>", lambda e, n=nama: self.hover_menu(n, True))
            c.tag_bind(tag, "<Leave>", lambda e, n=nama: self.hover_menu(n, False))

        # Tombol logout
        y_logout = h - 84

        logout = c.create_image(
            x, y_logout, image=self.img_logout, anchor="nw", tags="logout"
        )

        c.create_text(
            x + (SW - 36) / 2, y_logout + 22,
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
        c.tag_bind("logout", "<Button-1>", lambda e: self.proses_logout())

        # Teks kecil di bawah, seperti footer login
        c.create_text(
            SW // 2, h - 22,
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
        self.utama.place_configure(x=x, width=-x)

    def toggle_sidebar(self):
        """Tutup / buka sidebar dengan animasi."""

        if self.sedang_animasi:
            return

        self.sidebar_terbuka = not self.sidebar_terbuka

        if self.sidebar_terbuka:

            self.animasi_sidebar(self.posisi_x, SW)

        else:

            # Konten dilebarkan SEKALI di awal (sidebar masih menutupi),
            # lalu hanya sidebar yang digeser keluar.
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

        waktu = (time.perf_counter() - mulai) / DURASI_ANIMASI

        if waktu >= 1:
            x = ke
        else:
            x = dari + (ke - dari) * (1 - (1 - waktu) ** 3)

        self.side.place_configure(x=int(round(x)))

        if waktu < 1:
            self.root.after(
                8, lambda: self.geser_sidebar_keluar(dari, ke, mulai)
            )
            return

        self.posisi_x = 0
        self.sedang_animasi = False

    def animasi_sidebar(self, dari, ke, mulai=None):

        if mulai is None:
            mulai = time.perf_counter()
            self.sedang_animasi = True

        waktu = (time.perf_counter() - mulai) / DURASI_ANIMASI

        if waktu >= 1:
            x = ke
        else:
            x = dari + (ke - dari) * (1 - (1 - waktu) ** 3)

        self.atur_posisi(int(round(x)))

        if waktu < 1:
            self.root.after(
                8, lambda: self.animasi_sidebar(dari, ke, mulai)
            )
            return

        self.sedang_animasi = False

        if self.redraw_banner is not None:
            self.redraw_banner()

    def warnai_menu(self):

        for nama, pill in self.item_pill.items():

            teks = self.item_teks[nama]

            if nama == self.aktif:

                self.side.itemconfigure(
                    pill, image=self.img_pil_aktif, state="normal"
                )
                self.side.itemconfigure(
                    teks, fill=BIRU_TUA, font=("Segoe UI", 10, "bold")
                )

            else:

                self.side.itemconfigure(pill, state="hidden")
                self.side.itemconfigure(
                    teks, fill=TEKS_MENU, font=("Segoe UI", 10)
                )

    def hover_menu(self, nama, masuk):

        self.side.config(cursor="hand2" if masuk else "")

        if nama == self.aktif:
            return

        pill = self.item_pill.get(nama)

        if pill is None:
            return

        if masuk:
            self.side.itemconfigure(
                pill, image=self.img_pil_hover, state="normal"
            )
        else:
            self.side.itemconfigure(pill, state="hidden")

    # ==================================================
    # AREA UTAMA
    # ==================================================

    def buat_area_utama(self):

        utama = tk.Frame(self.root, bg=LATAR)
        self.utama = utama

        utama.place(x=SW, y=0, relwidth=1, width=-SW, relheight=1)

        # Top bar
        topbar = tk.Frame(utama, bg=PUTIH, height=70)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)

        tombol_burger = tk.Label(
            topbar, image=self.img_burger, bg=PUTIH, bd=0, cursor="hand2"
        )
        tombol_burger.pack(side="left", padx=(20, 0))

        tombol_burger.bind("<Button-1>", lambda e: self.toggle_sidebar())
        tombol_burger.bind(
            "<Enter>",
            lambda e: tombol_burger.config(image=self.img_burger_hover)
        )
        tombol_burger.bind(
            "<Leave>",
            lambda e: tombol_burger.config(image=self.img_burger)
        )

        self.judul = tk.Label(
            topbar, text="Katalog Buku",
            font=("Segoe UI", 18, "bold"), bg=PUTIH, fg=BIRU_TUA
        )
        self.judul.pack(side="left", padx=16)

        # Info pengguna: avatar bulat + nama
        info = tk.Frame(topbar, bg=PUTIH)
        info.pack(side="right", padx=28)

        inisial = (self.nama.strip()[:1] or "?").upper()

        avatar = tk.Label(
            info, image=self.img_avatar, text=inisial, compound="center",
            font=("Segoe UI", 12, "bold"), fg=PUTIH, bg=PUTIH, bd=0
        )
        avatar.pack(side="right", padx=(12, 0))

        teks_info = tk.Frame(info, bg=PUTIH)
        teks_info.pack(side="right")

        lbl_nama = tk.Label(
            teks_info, text=self.nama, font=("Segoe UI", 10, "bold"),
            bg=PUTIH, fg=ABU_GELAP, anchor="e"
        )
        lbl_nama.pack(anchor="e")

        lbl_user = tk.Label(
            teks_info, text=f"Anggota  ·  @{self.username}",
            font=("Segoe UI", 8), bg=PUTIH, fg=ABU, anchor="e"
        )
        lbl_user.pack(anchor="e")

        # Klik avatar / nama untuk membuka profil
        for widget in (avatar, lbl_nama, lbl_user):
            widget.config(cursor="hand2")
            widget.bind(
                "<Button-1>", lambda e: self.pilih_menu("Profil Saya")
            )

        tk.Frame(utama, bg=ABU_MUDA, height=1).pack(fill="x")

        # Tempat isi halaman
        self.konten = tk.Frame(utama, bg=LATAR)
        self.konten.pack(fill="both", expand=True)

    # ==================================================
    # NAVIGASI HALAMAN
    # ==================================================

    def kosongkan_konten(self):

        self.redraw_banner = None
        self.area_gulir = None
        self.halaman_aktif = None

        for widget in self.konten.winfo_children():
            widget.destroy()

    def pilih_menu(self, nama):

        self.aktif = nama
        self.warnai_menu()
        self.judul.config(text=nama)

        self.kosongkan_konten()

        try:
            self.buka_halaman(nama)

        except Exception as e:

            self.kosongkan_konten()

            messagebox.showerror(
                "Gagal Membuka Halaman",
                f"Halaman {nama} tidak dapat dimuat:\n\n{e}",
                parent=self.root
            )

    def buka_halaman(self, nama):
        """
        Memuat halaman sesuai menu. Import dilakukan saat halaman dibuka
        agar kesalahan satu file tidak menghalangi dashboard tampil.
        """

        if nama == "Katalog Buku":

            from buku.katalog_buku import HalamanKatalog

            self.halaman_aktif = HalamanKatalog(self, self.konten)

        elif nama == "Jadwal Pengembalian":

            from peminjaman.riwayat_peminjaman import HalamanJadwal

            self.halaman_aktif = HalamanJadwal(self, self.konten)

        elif nama == "Profil Saya":

            from profil_anggota import HalamanProfil

            self.halaman_aktif = HalamanProfil(self, self.konten)

        else:

            raise ValueError(f"Menu {nama} tidak ditemukan.")

    def buka_detail(self, buku):
        """Halaman detail satu buku (dipanggil dari katalog)."""

        self.judul.config(text="Detail Buku")

        self.kosongkan_konten()

        try:
            from buku.detail_buku import HalamanDetail

            self.halaman_aktif = HalamanDetail(self, self.konten, buku)

        except Exception as e:

            messagebox.showerror(
                "Gagal Membuka Halaman",
                f"Detail buku tidak dapat dimuat:\n\n{e}",
                parent=self.root
            )

            self.pilih_menu("Katalog Buku")

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

            # Hentikan mainloop; pemanggil yang menghancurkan jendela.
            self.root.quit()

    def tutup_dashboard(self):

        self.logout = False

        # Tutup aplikasi tanpa kembali ke halaman login.
        self.root.quit()