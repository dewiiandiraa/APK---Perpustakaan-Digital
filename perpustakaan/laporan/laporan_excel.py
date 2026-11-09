from datetime import date, datetime
from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter


# ==================== GAYA ====================

FONT = "Arial"

NAVY = "17365D"
ABU = "64748B"
ABU_GELAP = "334155"
GARIS = "CBD5E1"
ZEBRA = "F6F9FE"

FORMAT_TANGGAL = "DD-MM-YYYY"
FORMAT_ANGKA = "#,##0"

# kode status -> (warna latar, warna teks)
WARNA_STATUS = {
    "terlambat": ("FEE2E2", "991B1B"),
    "segera": ("FEF3C7", "92400E"),
    "aman": ("DBEAFE", "1D4ED8"),
    "dikembalikan": ("DCFCE7", "166534"),
    "dikembalikan_terlambat": ("FFEDD5", "9A3412"),
}

TIPIS = Side(style="thin", color=GARIS)
BINGKAI = Border(left=TIPIS, right=TIPIS, top=TIPIS, bottom=TIPIS)


def _font(tebal=False, ukuran=10, warna="000000", miring=False):
    return Font(name=FONT, bold=tebal, size=ukuran, color=warna, italic=miring)


def _isi(warna):
    return PatternFill("solid", start_color=warna, end_color=warna)


# ==================== DEFINISI KOLOM ====================
# (judul kolom, kunci data, lebar, tipe)  tipe: teks | angka | tanggal | status

KOLOM_PEMINJAMAN = [
    ("No", "no", 6, "angka"),
    ("ID Peminjaman", "id_peminjaman", 15, "teks"),
    ("ID Anggota", "id_anggota", 12, "teks"),
    ("Nama Anggota", "nama", 26, "teks"),
    ("No. Telepon", "telepon", 16, "teks"),
    ("ID Buku", "id_buku", 10, "teks"),
    ("Judul Buku", "judul", 34, "teks"),
    ("Jumlah", "jumlah", 9, "angka"),
    ("Tgl Pengajuan", "tgl_pengajuan", 14, "tanggal"),
    ("Tgl Pinjam", "tgl_pinjam", 13, "tanggal"),
    ("Jatuh Tempo", "jatuh_tempo", 13, "tanggal"),
    ("Tgl Kembali", "kembali", 13, "tanggal"),
    ("Status", "status", 28, "status"),
    ("Petugas", "petugas", 20, "teks"),
]

KOLOM_BELUM = [
    ("No", "no", 6, "angka"),
    ("ID Anggota", "id_anggota", 12, "teks"),
    ("Nama Anggota", "nama", 26, "teks"),
    ("No. Telepon", "telepon", 16, "teks"),
    ("Alamat", "alamat", 34, "teks"),
    ("ID Peminjaman", "id_peminjaman", 15, "teks"),
    ("ID Buku", "id_buku", 10, "teks"),
    ("Judul Buku", "judul", 34, "teks"),
    ("Jumlah", "jumlah", 9, "angka"),
    ("Tgl Pinjam", "tgl_pinjam", 13, "tanggal"),
    ("Jatuh Tempo", "jatuh_tempo", 13, "tanggal"),
    ("Sisa Hari", "sisa", 11, "angka"),
    ("Status", "status", 24, "status"),
]

KOLOM_TERLAMBAT = [
    k if k[1] != "sisa" else ("Hari Terlambat", "hari_terlambat", 15, "angka")
    for k in KOLOM_BELUM
]

KOLOM_DIKEMBALIKAN = [
    ("No", "no", 6, "angka"),
    ("ID Peminjaman", "id_peminjaman", 15, "teks"),
    ("ID Anggota", "id_anggota", 12, "teks"),
    ("Nama Anggota", "nama", 26, "teks"),
    ("ID Buku", "id_buku", 10, "teks"),
    ("Judul Buku", "judul", 34, "teks"),
    ("Jumlah", "jumlah", 9, "angka"),
    ("Tgl Pinjam", "tgl_pinjam", 13, "tanggal"),
    ("Jatuh Tempo", "jatuh_tempo", 13, "tanggal"),
    ("Tgl Kembali", "kembali", 13, "tanggal"),
    ("Keterangan", "keterangan_kembali", 24, "status"),
]


def _daftar_lembar(hari):
    """(kunci data, nama sheet, judul, kolom, warna tab)"""

    return [
        ("belum_kembali", "Belum Kembali",
         "Anggota yang Belum Mengembalikan Buku",
         KOLOM_BELUM, "F59E0B"),
        ("terlambat", "Terlambat",
         "Peminjaman yang Terlambat Dikembalikan",
         KOLOM_TERLAMBAT, "DC2626"),
        ("jatuh_tempo", "Jatuh Tempo",
         f"Buku yang Jatuh Tempo dalam {hari} Hari ke Depan",
         KOLOM_BELUM, "D97706"),
        ("peminjaman", "Peminjaman",
         "Seluruh Peminjaman pada Bulan Ini",
         KOLOM_PEMINJAMAN, "2563EB"),
        ("dikembalikan", "Dikembalikan",
         "Buku yang Dikembalikan pada Bulan Ini",
         KOLOM_DIKEMBALIKAN, "16A34A"),
    ]


# ==================== SHEET DATA ====================

def _tulis_data(ws, judul, subjudul, kolom, baris, warna_tab):
    """Menulis satu sheet data. Mengembalikan info baris & huruf kolom."""

    ws.sheet_properties.tabColor = warna_tab
    ws.sheet_view.showGridLines = False

    huruf = {k[1]: get_column_letter(i) for i, k in enumerate(kolom, start=1)}

    ws["A1"] = judul
    ws["A1"].font = _font(True, 14, NAVY)

    ws["A2"] = subjudul
    ws["A2"].font = _font(False, 10, ABU)

    baris_header = 4
    awal = 5

    for i, (nama, kunci, lebar, tipe) in enumerate(kolom, start=1):

        sel = ws.cell(row=baris_header, column=i, value=nama)
        sel.font = _font(True, 10, "FFFFFF")
        sel.fill = _isi(NAVY)
        sel.alignment = Alignment(
            horizontal="center", vertical="center", wrap_text=True
        )
        sel.border = BINGKAI

        ws.column_dimensions[get_column_letter(i)].width = lebar

    ws.row_dimensions[baris_header].height = 24

    if not baris:

        ws.cell(row=awal, column=1, value="Tidak ada data untuk kategori ini.")
        ws.cell(row=awal, column=1).font = _font(False, 10, ABU, miring=True)
        ws.freeze_panes = "A5"

        return {"awal": awal, "akhir": None, "huruf": huruf}

    for nomor, data in enumerate(baris, start=1):

        r = awal + nomor - 1

        for i, (nama, kunci, lebar, tipe) in enumerate(kolom, start=1):

            nilai = nomor if kunci == "no" else data.get(kunci)

            sel = ws.cell(row=r, column=i)
            sel.border = BINGKAI
            sel.font = _font()

            if nomor % 2 == 0:
                sel.fill = _isi(ZEBRA)

            if tipe == "tanggal":

                if isinstance(nilai, (date, datetime)):
                    sel.value = nilai
                    sel.number_format = FORMAT_TANGGAL
                else:
                    sel.value = "-"

                sel.alignment = Alignment(horizontal="center", vertical="top")

            elif tipe == "angka":

                sel.value = nilai if nilai is not None else "-"
                sel.number_format = FORMAT_ANGKA
                sel.alignment = Alignment(horizontal="center", vertical="top")

            elif tipe == "status":

                sel.value = nilai if nilai else "-"
                sel.alignment = Alignment(horizontal="center", vertical="top")

                warna = WARNA_STATUS.get(data.get("kode"))

                if warna:
                    sel.fill = _isi(warna[0])
                    sel.font = _font(True, 10, warna[1])

            else:

                sel.value = nilai if nilai not in (None, "") else "-"
                sel.alignment = Alignment(
                    horizontal="left", vertical="top", wrap_text=True
                )

    akhir = awal + len(baris) - 1

    # Baris total (rumus)
    total = akhir + 2

    ws.cell(row=total, column=1, value="Total").font = _font(True, 10, NAVY)

    if "jumlah" in huruf:

        h = huruf["jumlah"]

        sel = ws[f"{h}{total}"]
        sel.value = f"=SUM({h}{awal}:{h}{akhir})"
        sel.font = _font(True, 10, NAVY)
        sel.number_format = FORMAT_ANGKA
        sel.alignment = Alignment(horizontal="center")

    ws.freeze_panes = "A5"
    ws.auto_filter.ref = f"A{baris_header}:{get_column_letter(len(kolom))}{akhir}"

    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True

    return {"awal": awal, "akhir": akhir, "huruf": huruf}


# ==================== SHEET RINGKASAN ====================

def _rentang(nama_sheet, huruf, awal, akhir):
    return f"'{nama_sheet}'!${huruf}${awal}:${huruf}${akhir}"


def _tulis_ringkasan(ws, data, info):

    ws.sheet_properties.tabColor = NAVY
    ws.sheet_view.showGridLines = False

    for huruf, lebar in zip("ABCDE", (40, 14, 17, 14, 78)):
        ws.column_dimensions[huruf].width = lebar

    ws["A1"] = "LAPORAN PEMINJAMAN BUKU"
    ws["A1"].font = _font(True, 16, NAVY)

    ws["A2"] = "Perpustakaan Digital  ·  Sistem Informasi Manajemen Perpustakaan"
    ws["A2"].font = _font(False, 10, ABU)

    # ---- Informasi laporan ----
    dibuat_oleh = data.get("dibuat_oleh") or "-"

    if data.get("role"):
        dibuat_oleh += f" ({str(data['role']).capitalize()})"

    info_laporan = [
        ("Periode", data["nama_bulan"], None),
        ("Tanggal acuan data", data["acuan"], FORMAT_TANGGAL),
        ("Dibuat oleh", dibuat_oleh, None),
        ("Dibuat pada", data["dibuat_pada"], "DD-MM-YYYY HH:MM"),
        ("Catatan", data.get("catatan") or "-", None),
    ]

    for i, (label, nilai, fmt) in enumerate(info_laporan, start=4):

        ws.cell(row=i, column=1, value=label).font = _font(True, 10, ABU_GELAP)

        sel = ws.cell(row=i, column=2, value=nilai)
        sel.font = _font()
        sel.alignment = Alignment(horizontal="left")

        if fmt:
            sel.number_format = fmt

    def judul_bagian(baris, teks):
        sel = ws.cell(row=baris, column=1, value=teks)
        sel.font = _font(True, 12, NAVY)

    def header(baris, judul):
        for i, teks in enumerate(judul, start=1):
            sel = ws.cell(row=baris, column=i, value=teks)
            sel.font = _font(True, 10, "FFFFFF")
            sel.fill = _isi(NAVY)
            sel.border = BINGKAI
            sel.alignment = Alignment(
                horizontal="left" if i in (1, 5) else "center",
                vertical="center", wrap_text=True
            )

    def sel_data(baris, kolom, nilai, rata="center", tebal=False, warna="000000"):
        sel = ws.cell(row=baris, column=kolom, value=nilai)
        sel.font = _font(tebal, 10, warna)
        sel.border = BINGKAI
        sel.alignment = Alignment(
            horizontal=rata, vertical="center", wrap_text=True
        )
        if kolom in (2, 3, 4):
            sel.number_format = FORMAT_ANGKA
        return sel

    # ---- A. Pengajuan ----
    judul_bagian(10, "A.  Pengajuan Peminjaman pada Bulan Ini")
    header(11, ["Indikator", "Jumlah", "", "", "Keterangan"])

    p = data["pengajuan"]

    baris_pengajuan = [
        ("Menunggu persetujuan", p["menunggu"],
         "Pengajuan yang belum diproses petugas. Nilai dari database."),
        ("Disetujui", p["disetujui"],
         "Pengajuan yang disetujui (sedang dipinjam maupun sudah selesai). "
         "Nilai dari database."),
        ("Ditolak", p["ditolak"],
         "Pengajuan yang ditolak petugas. Nilai dari database."),
    ]

    for i, (label, nilai, ket) in enumerate(baris_pengajuan, start=12):
        sel_data(i, 1, label, "left")
        sel_data(i, 2, nilai)
        sel_data(i, 3, "")
        sel_data(i, 4, "")
        sel_data(i, 5, ket, "left")

    sel_data(15, 1, "Total pengajuan", "left", True, NAVY)
    sel_data(15, 2, "=SUM(B12:B14)", "center", True, NAVY)
    sel_data(15, 3, "")
    sel_data(15, 4, "")
    sel_data(15, 5, "Jumlah seluruh pengajuan dengan tanggal pengajuan "
                    "di bulan ini.", "left")

    # ---- B. Aktivitas dan kondisi ----
    judul_bagian(17, "B.  Aktivitas dan Kondisi Peminjaman")
    header(18, ["Indikator", "Transaksi", "Buku (eksemplar)", "Anggota",
                "Keterangan"])

    baris_b = [
        ("peminjaman", "Dipinjam bulan ini", None,
         "Buku yang tanggal pinjamnya jatuh di bulan laporan."),
        ("dikembalikan", "Dikembalikan bulan ini", None,
         "Buku yang tanggal kembalinya jatuh di bulan laporan."),
        ("belum_kembali", "Belum mengembalikan", NAVY,
         "Sudah dipinjam sampai tanggal acuan dan belum dikembalikan "
         "pada tanggal acuan."),
        ("terlambat", "Terlambat", "991B1B",
         "Belum mengembalikan dan jatuh tempo sebelum tanggal acuan."),
        ("jatuh_tempo", f"Jatuh tempo ≤ {data['hari_jatuh_tempo']} hari", "92400E",
         f"Belum mengembalikan dan jatuh tempo dalam "
         f"{data['hari_jatuh_tempo']} hari sejak tanggal acuan."),
    ]

    for i, (kunci, label, warna, ket) in enumerate(baris_b, start=19):

        nama_sheet, lembar = info[kunci]
        tebal = warna is not None
        warna = warna or "000000"

        sel_data(i, 1, label, "left", tebal, warna)

        if lembar["akhir"] is None:

            for kolom in (2, 3, 4):
                sel_data(i, kolom, 0, "center", tebal, warna)

        else:

            a, b, h = lembar["awal"], lembar["akhir"], lembar["huruf"]

            def unik(huruf):
                r = _rentang(nama_sheet, huruf, a, b)
                return f"=SUMPRODUCT(1/COUNTIF({r},{r}))"

            sel_data(i, 2, unik(h["id_peminjaman"]), "center", tebal, warna)
            sel_data(
                i, 3, f"=SUM({_rentang(nama_sheet, h['jumlah'], a, b)})",
                "center", tebal, warna
            )
            sel_data(i, 4, unik(h["id_anggota"]), "center", tebal, warna)

        sel_data(i, 5, ket, "left")

    # ---- Catatan ----
    ws.cell(row=25, column=1, value="Catatan dan asumsi").font = _font(
        True, 10, ABU_GELAP
    )

    catatan = [
        "• Tanggal acuan adalah tanggal laporan dibuat; bila periode sudah "
        "lewat, tanggal acuan adalah hari terakhir bulan tersebut.",
        "• Satu transaksi dapat memuat beberapa buku. Kolom Transaksi dan "
        "Anggota dihitung unik (rumus SUMPRODUCT/COUNTIF pada sheet data).",
        "• Kolom Buku adalah jumlah eksemplar (penjumlahan kolom Jumlah).",
        "• Rincian nama dan kontak anggota ada di sheet Belum Kembali, "
        "Terlambat, dan Jatuh Tempo.",
        "• Bagian A diambil langsung dari database saat laporan dibuat "
        "(bukan rumus).",
    ]

    for i, teks in enumerate(catatan, start=26):
        sel = ws.cell(row=i, column=1, value=teks)
        sel.font = _font(False, 9, ABU)

    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True


# ==================== FUNGSI UTAMA ====================

def buat_excel(data):
    """
    Membuat workbook dari hasil LaporanPeminjaman.kumpulkan().
    Mengembalikan isi file .xlsx dalam bentuk bytes.
    """

    wb = Workbook()

    ws_ringkasan = wb.active
    ws_ringkasan.title = "Ringkasan"

    subjudul = (
        f"Periode {data['nama_bulan']}  ·  "
        f"Tanggal acuan {data['acuan'].strftime('%d-%m-%Y')}"
    )

    info = {}

    for kunci, nama, judul, kolom, warna in _daftar_lembar(
        data["hari_jatuh_tempo"]
    ):
        ws = wb.create_sheet(nama)

        lembar = _tulis_data(
            ws, judul, subjudul, kolom, data["lembar"][kunci], warna
        )

        info[kunci] = (nama, lembar)

    _tulis_ringkasan(ws_ringkasan, data, info)

    wb.calculation.fullCalcOnLoad = True

    buffer = BytesIO()
    wb.save(buffer)

    return buffer.getvalue()