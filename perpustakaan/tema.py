import tkinter as tk
from tkinter import ttk


# ==================== PALET WARNA ====================

BIRU_TUA = "#17365D"
BIRU = "#2563EB"
BIRU_GRAD = "#1F66C1"
BIRU_PANEL = "#EAF2FC"
BIRU_MUDA = "#EFF6FF"

PUTIH = "#FFFFFF"
LATAR = "#F1F5F9"
BORDER = "#E2E8F0"
ABU = "#64748B"
ABU_GELAP = "#334155"
NONAKTIF = "#E2E8F0"

HIJAU = "#16A34A"
MERAH = "#DC2626"
ORANYE = "#D97706"

FONT = "Segoe UI"


# ==================== FUNGSI WARNA ====================

def _rgb(hex_warna):
    h = hex_warna.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def campur(a, b, t):
    """Campur dua warna hex. t=0 -> a, t=1 -> b."""
    ra, rb = _rgb(a), _rgb(b)
    return "#%02x%02x%02x" % tuple(int(x + (y - x) * t) for x, y in zip(ra, rb))


def gelapkan(hex_warna, faktor=0.12):
    return campur(hex_warna, "#000000", faktor)


# ==================== JENDELA & STYLE ====================

def terapkan_style(root=None):
    """Gaya ttk (tabel, scrollbar, combobox) yang seragam."""

    s = ttk.Style(root)

    try:
        s.theme_use("clam")
    except tk.TclError:
        pass

    s.configure(
        "Treeview",
        font=(FONT, 10),
        rowheight=34,
        background=PUTIH,
        fieldbackground=PUTIH,
        foreground=ABU_GELAP,
        borderwidth=0,
        relief="flat"
    )
    s.map(
        "Treeview",
        background=[("selected", "#DBEAFE")],
        foreground=[("selected", BIRU_TUA)]
    )

    s.configure(
        "Treeview.Heading",
        font=(FONT, 10, "bold"),
        background=BIRU_TUA,
        foreground=PUTIH,
        relief="flat",
        borderwidth=0,
        padding=(10, 9)
    )
    s.map("Treeview.Heading", background=[("active", BIRU)])

    for arah in ("Vertical", "Horizontal"):
        s.configure(
            f"{arah}.TScrollbar",
            background="#CBD5E1",
            troughcolor=LATAR,
            bordercolor=LATAR,
            lightcolor="#CBD5E1",
            darkcolor="#CBD5E1",
            arrowcolor=ABU,
            relief="flat",
            gripcount=0
        )
        s.map(f"{arah}.TScrollbar", background=[("active", "#94A3B8")])

    s.configure(
        "TCombobox",
        fieldbackground="#F8FAFC",
        background="#F8FAFC",
        bordercolor="#CBD5E1",
        lightcolor="#CBD5E1",
        darkcolor="#CBD5E1",
        arrowcolor=ABU,
        padding=6
    )
    s.map(
        "TCombobox",
        bordercolor=[("focus", BIRU)],
        fieldbackground=[("readonly", "#F8FAFC")]
    )

    if root is not None:
        root.option_add("*TCombobox*Listbox.font", (FONT, 10))


def atur_jendela(root, judul, geometri=None, minimal=None):
    """
    Mengatur jendela. Jika `root` berupa Frame (mis. ditanam di dashboard),
    pengaturan judul/ukuran dilewati otomatis.
    """

    root.configure(bg=LATAR)

    if isinstance(root, (tk.Tk, tk.Toplevel)):
        root.title(judul)
        if geometri:
            root.geometry(geometri)
        if minimal:
            root.minsize(*minimal)

    terapkan_style(root)


# ==================== KOMPONEN ====================

class Header(tk.Canvas):
    """
    Header gradasi biru dengan lingkaran dekoratif (seperti halaman login).

    Jika induknya bukan jendela (artinya halaman ditanam di dashboard yang
    sudah punya top bar), header otomatis disembunyikan supaya tidak dobel.
    """

    def __init__(self, parent, judul, subjudul="", tinggi=100):

        tersemat = not isinstance(parent, (tk.Tk, tk.Toplevel))

        super().__init__(
            parent,
            height=1 if tersemat else tinggi,
            highlightthickness=0,
            bd=0,
            bg=LATAR if tersemat else BIRU_TUA
        )

        self.judul = judul
        self.subjudul = subjudul
        self.tersemat = tersemat

        if not tersemat:
            self.bind("<Configure>", self._gambar)

    def _gambar(self, event):

        self.delete("all")
        w, h = event.width, event.height

        langkah = 6
        for x in range(0, w, langkah):
            self.create_rectangle(
                x, 0, x + langkah, h,
                fill=campur(BIRU_TUA, BIRU_GRAD, x / max(w, 1)),
                outline=""
            )

        self.create_oval(
            w - 230, -90, w - 60, 80,
            fill=campur(BIRU_GRAD, "#FFFFFF", 0.08), outline=""
        )
        self.create_oval(
            w - 130, 25, w + 40, 195,
            fill=campur(BIRU_GRAD, "#FFFFFF", 0.14), outline=""
        )

        self.create_text(
            30, h * 0.38, anchor="w", text=self.judul,
            font=(FONT, 20, "bold"), fill=PUTIH
        )
        self.create_text(
            32, h * 0.72, anchor="w", text=self.subjudul,
            font=(FONT, 10), fill="#CFE0F7"
        )


class Tombol(tk.Button):
    """Tombol datar dengan efek hover & tampilan nonaktif otomatis."""

    def __init__(self, parent, teks, warna, perintah, **kw):

        self.warna = warna

        super().__init__(
            parent,
            text=teks,
            command=perintah,
            bg=warna,
            fg=PUTIH,
            activebackground=gelapkan(warna),
            activeforeground=PUTIH,
            disabledforeground="#94A3B8",
            font=(FONT, 9, "bold"),
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=18,
            pady=9,
            **kw
        )

        self.bind("<Enter>", self._masuk)
        self.bind("<Leave>", self._keluar)

    def _masuk(self, event):
        if str(self.cget("state")) != "disabled":
            super().configure(bg=gelapkan(self.warna))

    def _keluar(self, event):
        if str(self.cget("state")) != "disabled":
            super().configure(bg=self.warna)

    def configure(self, cnf=None, **kw):

        hasil = super().configure(cnf, **kw)

        if "state" in kw:
            if kw["state"] == "disabled":
                super().configure(bg=NONAKTIF, cursor="arrow")
            else:
                super().configure(bg=self.warna, cursor="hand2")

        return hasil

    config = configure


def buat_kartu(parent, judul, nilai, warna):
    """Kartu statistik dengan garis aksen di kiri. Mengembalikan label nilai."""

    kartu = tk.Frame(
        parent, bg=PUTIH, highlightbackground=BORDER, highlightthickness=1
    )
    kartu.pack(side="left", fill="x", expand=True, padx=6)

    tk.Frame(kartu, bg=warna, width=5).pack(side="left", fill="y")

    isi = tk.Frame(kartu, bg=PUTIH, padx=16, pady=12)
    isi.pack(side="left", fill="both", expand=True)

    tk.Label(
        isi, text=judul, bg=PUTIH, fg=ABU, font=(FONT, 8, "bold")
    ).pack(anchor="w")

    label = tk.Label(
        isi, text=nilai, bg=PUTIH, fg=warna, font=(FONT, 24, "bold")
    )
    label.pack(anchor="w")

    return label


def buat_panel(parent, judul=None):
    """Panel putih berbingkai. Mengembalikan (bingkai_luar, bagian_isi)."""

    luar = tk.Frame(
        parent, bg=PUTIH, highlightbackground=BORDER, highlightthickness=1
    )

    if judul:
        bar = tk.Frame(luar, bg=PUTIH)
        bar.pack(fill="x", padx=20, pady=(16, 0))

        tk.Frame(bar, bg=BIRU, width=4, height=20).pack(side="left")
        tk.Label(
            bar, text=judul, font=(FONT, 12, "bold"), bg=PUTIH, fg=BIRU_TUA
        ).pack(side="left", padx=(8, 0))

    isi = tk.Frame(luar, bg=PUTIH, padx=20, pady=14)
    isi.pack(fill="both", expand=True)

    return luar, isi


def buat_entry(parent, variabel, show="", readonly=False, width=None):

    opsi = {"width": width} if width else {}

    entry = tk.Entry(
        parent,
        textvariable=variabel,
        font=(FONT, 10),
        bg="#F8FAFC",
        fg=ABU_GELAP,
        insertbackground=BIRU,
        relief="flat",
        bd=0,
        highlightthickness=1,
        highlightbackground="#CBD5E1",
        highlightcolor=BIRU,
        show=show,
        **opsi
    )

    if readonly:
        entry.configure(
            state="readonly",
            readonlybackground="#EEF2F7",
            fg=ABU
        )

    return entry


def buat_field(parent, judul, variabel, baris, kolom,
               show="", readonly=False, span=1):
    """Label kecil + kotak input, ditempatkan di grid."""

    bingkai = tk.Frame(parent, bg=PUTIH)
    bingkai.grid(
        row=baris, column=kolom, columnspan=span,
        sticky="ew", padx=6, pady=(0, 10)
    )

    tk.Label(
        bingkai, text=judul, font=(FONT, 9, "bold"),
        bg=PUTIH, fg=ABU_GELAP
    ).pack(anchor="w", pady=(0, 5))

    entry = buat_entry(bingkai, variabel, show=show, readonly=readonly)
    entry.pack(fill="x", ipady=7)

    return entry


def buat_combo(parent, judul, variabel, nilai, baris, kolom):

    bingkai = tk.Frame(parent, bg=PUTIH)
    bingkai.grid(row=baris, column=kolom, sticky="ew", padx=6, pady=(0, 10))

    tk.Label(
        bingkai, text=judul, font=(FONT, 9, "bold"),
        bg=PUTIH, fg=ABU_GELAP
    ).pack(anchor="w", pady=(0, 5))

    combo = ttk.Combobox(
        bingkai, textvariable=variabel, values=nilai,
        state="readonly", font=(FONT, 10)
    )
    combo.pack(fill="x", ipady=4)

    return combo


def rata(form, jumlah_kolom):
    """Membagi lebar kolom form secara merata."""

    for i in range(jumlah_kolom):
        form.grid_columnconfigure(i, weight=1, uniform="field")


def buat_pencarian(parent, judul, variabel, perintah):
    """Baris judul tabel + kotak pencarian di kanan."""

    baris = tk.Frame(parent, bg=PUTIH)
    baris.pack(fill="x", pady=(0, 12))

    tk.Frame(baris, bg=BIRU, width=4, height=20).pack(side="left")
    tk.Label(
        baris, text=judul, font=(FONT, 13, "bold"),
        bg=PUTIH, fg=BIRU_TUA
    ).pack(side="left", padx=(8, 0))

    entry = buat_entry(baris, variabel, width=30)
    entry.pack(side="right", ipady=5)

    tk.Label(
        baris, text="Cari:", bg=PUTIH, fg=ABU, font=(FONT, 9)
    ).pack(side="right", padx=(0, 8))

    entry.bind("<KeyRelease>", lambda event: perintah())

    return entry


def buat_tabel(parent, kolom, scroll_x=False):
    """
    Tabel Treeview bergaris zebra.
    kolom: daftar (id, judul, lebar, anchor)
    """

    bingkai = tk.Frame(parent, bg=PUTIH)
    bingkai.pack(fill="both", expand=True)

    tabel = ttk.Treeview(
        bingkai,
        columns=[k[0] for k in kolom],
        show="headings",
        selectmode="browse"
    )

    for id_kolom, judul, lebar, anchor in kolom:
        tabel.heading(id_kolom, text=judul, anchor=anchor)
        tabel.column(id_kolom, width=lebar, minwidth=60, anchor=anchor)

    scroll_y = ttk.Scrollbar(
        bingkai, orient="vertical", command=tabel.yview
    )
    tabel.configure(yscrollcommand=scroll_y.set)

    bingkai.grid_rowconfigure(0, weight=1)
    bingkai.grid_columnconfigure(0, weight=1)

    tabel.grid(row=0, column=0, sticky="nsew")
    scroll_y.grid(row=0, column=1, sticky="ns")

    if scroll_x:
        scroll_h = ttk.Scrollbar(
            bingkai, orient="horizontal", command=tabel.xview
        )
        tabel.configure(xscrollcommand=scroll_h.set)
        scroll_h.grid(row=1, column=0, sticky="ew")

    tabel.tag_configure("genap", background=PUTIH)
    tabel.tag_configure("ganjil", background="#F4F8FE")

    return tabel


class Pembagi(tk.Frame):
    """
    Dua bagian (atas & bawah) yang dipisahkan garis yang bisa ditarik.
      - isi bagian atas  -> taruh di  pembagi.atas_isi
      - isi bagian bawah -> taruh di  pembagi.bawah   (mis. tabel)
    Tarik garis ke atas untuk memperluas tabel, klik 2x untuk
    menyembunyikan / menampilkan kembali bagian atas.
    """

    TINGGI_HANDLE = 26
    MIN_BAWAH = 150

    def __init__(self, parent):

        super().__init__(parent, bg=LATAR)

        self._simpan = None
        self._aktif = False

        self.atas = tk.Frame(self, bg=LATAR, height=1)
        self.atas.pack_propagate(False)

        self.atas_isi = tk.Frame(self.atas, bg=LATAR)
        self.atas_isi.place(x=0, y=0, relwidth=1.0)
        self.atas_isi.bind("<Configure>", lambda e: self._geser())

        self.handle = tk.Canvas(
            self,
            height=self.TINGGI_HANDLE,
            bg=LATAR,
            highlightthickness=0,
            bd=0,
            cursor="sb_v_double_arrow"
        )

        self.bawah = tk.Frame(self, bg=LATAR)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.atas.grid(row=0, column=0, sticky="ew")
        self.handle.grid(row=1, column=0, sticky="ew")
        self.bawah.grid(row=2, column=0, sticky="nsew")

        self.handle.bind("<Configure>", lambda e: self._gambar())
        self.handle.bind("<B1-Motion>", self._tarik)
        self.handle.bind("<Double-Button-1>", self._toggle)
        self.handle.bind("<Enter>", lambda e: self._warna(True))
        self.handle.bind("<Leave>", lambda e: self._warna(False))

        self.bind("<Configure>", self._jaga)

        self.after(100, self._awal)

    # ---------- ukuran ----------

    def _tinggi_alami(self):
        return self.atas_isi.winfo_reqheight() + 8

    def _atur(self, tinggi):

        maks = self.winfo_height() - self.TINGGI_HANDLE - self.MIN_BAWAH
        tinggi = int(max(1, min(tinggi, maks)))

        self.atas.configure(height=tinggi)
        self._geser(tinggi)

    def _geser(self, tinggi=None):
        """
        Saat bagian atas dipersempit, isinya ikut bergeser ke atas
        (bagian bawah isi tetap terlihat), bukan terpotong di bawah.
        """

        try:
            if tinggi is None:
                tinggi = int(self.atas.cget("height"))

            y = min(0, tinggi - self._tinggi_alami())
            self.atas_isi.place_configure(y=y)
        except tk.TclError:
            pass

    def _awal(self):

        # Di dashboard, halaman bisa saja sudah dihancurkan (pindah menu)
        # sebelum timer 100 ms ini berjalan.
        try:
            if not self.winfo_exists():
                return

            self.update_idletasks()
            self._atur(self._tinggi_alami())

        except tk.TclError:
            pass

    def _jaga(self, event):

        # Saat jendela mengecil, pastikan tabel tidak ikut terhimpit.
        if event.widget is self:
            self._atur(int(self.atas.cget("height")))

    # ---------- interaksi ----------

    def _tarik(self, event):

        y = event.y_root - self.atas.winfo_rooty()
        self._atur(y - self.TINGGI_HANDLE // 2)

    def _toggle(self, event=None):

        tinggi = int(self.atas.cget("height"))

        if tinggi > 5:
            self._simpan = tinggi
            self._atur(1)
        else:
            self._atur(self._simpan or self._tinggi_alami())

    def _warna(self, aktif):

        self._aktif = aktif
        self._gambar()

    # ---------- tampilan garis ----------

    def _gambar(self):

        c = self.handle
        c.delete("all")

        w = c.winfo_width()
        y = self.TINGGI_HANDLE // 2
        cx = w / 2

        c.create_line(
            cx - 200, y, cx - 160, y,
            width=5, capstyle="round",
            fill=BIRU if self._aktif else "#B6C4D6"
        )

        c.create_text(
            cx - 148, y, anchor="w",
            text="Tarik untuk mengubah ukuran tabel  ·  "
                 "klik 2× untuk menyembunyikan bagian atas",
            font=(FONT, 8),
            fill=BIRU if self._aktif else ABU
        )