import html
import tempfile
import webbrowser

from pathlib import Path

from koneksi import Database


# ==============================================
# GAYA TAMPILAN STRUK (CSS)
# ==============================================

STYLE = """
* {
    box-sizing: border-box;
}

body {
    margin: 0;
    padding: 30px 16px;
    background: linear-gradient(180deg, #1f6fd0 0%, #0a4896 100%);
    background-attachment: fixed;
    font-family: "Segoe UI", Arial, sans-serif;
    color: #1e293b;
    -webkit-print-color-adjust: exact;
    print-color-adjust: exact;
}

.struk {
    width: 100%;
    max-width: 640px;
    margin: auto;
    background: white;
    border-radius: 18px;
    overflow: hidden;
    box-shadow: 0 20px 50px rgba(0, 20, 60, 0.35);
}

.header {
    position: relative;
    overflow: hidden;
    padding: 30px 35px;
    background: linear-gradient(120deg, #17365d 0%, #1f66c1 100%);
    color: white;
}

.header::before,
.header::after {
    content: "";
    position: absolute;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.09);
}

.header::before {
    width: 190px;
    height: 190px;
    right: -50px;
    top: -80px;
}

.header::after {
    width: 150px;
    height: 150px;
    right: 60px;
    bottom: -90px;
}

.header h1 {
    position: relative;
    margin: 0;
    font-size: 22px;
    letter-spacing: 2px;
}

.header p {
    position: relative;
    margin: 7px 0 0;
    font-size: 12px;
    color: #cfe0f7;
}

.isi {
    padding: 30px 35px 35px;
}

.judul {
    margin-bottom: 22px;
}

.judul h2 {
    margin: 0 0 5px;
    font-size: 17px;
    color: #17365d;
}

.judul p {
    margin: 0;
    font-size: 12px;
    color: #64748b;
}

.informasi {
    width: 100%;
    margin-bottom: 24px;
    padding: 14px 16px;
    background: #f1f5f9;
    border-radius: 12px;
    font-size: 13px;
    border-collapse: separate;
}

.informasi td {
    padding: 6px 0;
    vertical-align: top;
}

.informasi td:first-child {
    width: 150px;
    color: #64748b;
}

.informasi td:nth-child(2) {
    width: 15px;
    color: #64748b;
}

table.daftar {
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
}

.daftar th {
    background: #17365d;
    color: white;
    padding: 11px;
    text-align: left;
}

.daftar th:first-child {
    border-radius: 8px 0 0 0;
}

.daftar th:last-child {
    border-radius: 0 8px 0 0;
}

.daftar td {
    padding: 11px;
    border-bottom: 1px solid #e2e8f0;
}

.daftar tbody tr:nth-child(even) td {
    background: #f6f9fe;
}

.daftar th:first-child,
.daftar td:first-child {
    width: 45px;
    text-align: center;
}

.jumlah {
    text-align: center;
    width: 75px;
}

.total {
    margin-top: 16px;
    text-align: right;
    font-size: 13px;
    font-weight: bold;
    color: #17365d;
}

.pengingat {
    margin-top: 25px;
    padding: 14px 16px;
    background: #eff6ff;
    border-left: 4px solid #2563eb;
    border-radius: 0 10px 10px 0;
    font-size: 12px;
    line-height: 1.6;
}

.footer {
    margin-top: 28px;
    padding-top: 15px;
    border-top: 1px solid #e2e8f0;
    text-align: center;
    font-size: 11px;
    color: #64748b;
    line-height: 1.6;
}

.tombol {
    display: block;
    margin: 22px auto 0;
    padding: 12px 26px;
    background: #17365d;
    color: white;
    border: none;
    border-radius: 10px;
    cursor: pointer;
    font-size: 13px;
    font-weight: bold;
}

.tombol:hover {
    background: #2563eb;
}

@media print {
    @page {
        size: A5;
        margin: 12mm;
    }

    body {
        padding: 0;
        background: white;
    }

    .struk {
        max-width: none;
        border-radius: 0;
        box-shadow: none;
    }

    .tombol {
        display: none;
    }
}
"""


class StrukPeminjaman:

    def __init__(self):
        self.db = Database()

    # ==============================================
    # MENGAMBIL DATA PEMINJAMAN DARI DATABASE
    # ==============================================

    def ambil_data(self, id_peminjaman):

        conn = self.db.hubungkan()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT
                    p.id_peminjaman,
                    p.anggota_id,
                    a.nama,
                    COALESCE(pt.nama, '-'),
                    p.tanggal_pinjam,
                    d.tanggal_jatuh_tempo,
                    b.judul,
                    d.jumlah

                FROM peminjaman AS p

                JOIN anggota AS a
                    ON p.anggota_id = a.id_anggota

                LEFT JOIN petugas AS pt
                    ON p.petugas_id = pt.id_petugas

                JOIN detail_peminjaman AS d
                    ON p.id_peminjaman = d.peminjaman_id

                JOIN buku AS b
                    ON d.buku_id = b.id_buku

                WHERE p.id_peminjaman = %s

                ORDER BY d.id_detail
            """, (id_peminjaman,))

            data = cursor.fetchall()

            if not data:
                raise ValueError(
                    "Data peminjaman atau rincian buku tidak ditemukan."
                )

            return data

        finally:
            cursor.close()
            conn.close()

    # ==============================================
    # FORMAT TANGGAL
    # ==============================================

    def format_tanggal(self, tanggal):

        if not tanggal:
            return "-"

        return tanggal.strftime("%d-%m-%Y")

    # ==============================================
    # MEMBUAT TAMPILAN STRUK HTML
    # ==============================================

    def buat_html(self, data):

        informasi = data[0]

        id_peminjaman = informasi[0]
        id_anggota = informasi[1]
        nama_anggota = informasi[2]
        nama_petugas = informasi[3]
        tanggal_pinjam = self.format_tanggal(informasi[4])
        tanggal_jatuh_tempo = self.format_tanggal(informasi[5])

        total_buku = sum(baris[7] for baris in data)

        daftar_buku = ""

        for nomor, baris in enumerate(data, start=1):

            judul = html.escape(str(baris[6]))
            jumlah = baris[7]

            daftar_buku += f"""
                <tr>
                    <td>{nomor}</td>
                    <td>{judul}</td>
                    <td class="jumlah">{jumlah}</td>
                </tr>
            """

        return f"""
        <!DOCTYPE html>
        <html lang="id">

        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Struk {html.escape(str(id_peminjaman))}</title>

            <style>
                {STYLE}
            </style>
        </head>

        <body>

            <div class="struk">

                <div class="header">
                    <h1>PERPUSTAKAAN DIGITAL</h1>
                    <p>Layanan Peminjaman dan Pengembalian Buku</p>
                </div>

                <div class="isi">

                    <div class="judul">
                        <h2>Bukti Peminjaman Buku</h2>
                        <p>Dokumen resmi transaksi peminjaman</p>
                    </div>

                    <table class="informasi">

                        <tr>
                            <td>ID Peminjaman</td>
                            <td>:</td>
                            <td><b>{html.escape(str(id_peminjaman))}</b></td>
                        </tr>

                        <tr>
                            <td>ID Anggota</td>
                            <td>:</td>
                            <td>{html.escape(str(id_anggota))}</td>
                        </tr>

                        <tr>
                            <td>Nama Anggota</td>
                            <td>:</td>
                            <td>{html.escape(str(nama_anggota))}</td>
                        </tr>

                        <tr>
                            <td>Petugas</td>
                            <td>:</td>
                            <td>{html.escape(str(nama_petugas))}</td>
                        </tr>

                        <tr>
                            <td>Tanggal Peminjaman</td>
                            <td>:</td>
                            <td>{tanggal_pinjam}</td>
                        </tr>

                        <tr>
                            <td>Batas Pengembalian</td>
                            <td>:</td>
                            <td><b>{tanggal_jatuh_tempo}</b></td>
                        </tr>

                    </table>

                    <table class="daftar">

                        <thead>
                            <tr>
                                <th>No.</th>
                                <th>Judul Buku</th>
                                <th class="jumlah">Jumlah</th>
                            </tr>
                        </thead>

                        <tbody>
                            {daftar_buku}
                        </tbody>

                    </table>

                    <div class="total">
                        Total Buku: {total_buku}
                    </div>

                    <div class="pengingat">
                        <b>Perhatian:</b><br>
                        Harap mengembalikan seluruh buku sebelum atau
                        pada tanggal jatuh tempo yang telah ditentukan.
                        Simpan bukti peminjaman ini sebagai referensi
                        saat melakukan pengembalian buku.
                    </div>

                    <div class="footer">
                        Terima kasih telah menggunakan layanan perpustakaan.<br>
                        Mohon menjaga buku yang dipinjam dengan baik.
                    </div>

                    <button class="tombol" onclick="window.print()">
                        Cetak / Simpan PDF
                    </button>

                </div>

            </div>

        </body>
        </html>
        """

    # ==============================================
    # MENYIMPAN DAN MEMBUKA STRUK
    # ==============================================

    def buka_struk(self, id_peminjaman):

        data = self.ambil_data(id_peminjaman)

        isi_html = self.buat_html(data)

        nama_file = f"struk_{id_peminjaman}.html"

        lokasi_file = Path(tempfile.gettempdir()) / nama_file

        lokasi_file.write_text(
            isi_html,
            encoding="utf-8"
        )

        webbrowser.open(lokasi_file.as_uri())

        return lokasi_file