from datetime import date, timedelta
from koneksi import Database


class Peminjaman:

    # hanya_lihat=True (operator): semua operasi yang mengubah data ditolak.
    def __init__(self, hanya_lihat=False):
        self.db = Database()
        self.hanya_lihat = hanya_lihat

    def _pastikan_boleh_ubah(self):
        if self.hanya_lihat:
            raise PermissionError(
                "Anda hanya dapat melihat data peminjaman."
            )

    # ==================================================
    # MEMBUAT ID PEMINJAMAN
    # ==================================================

    def buat_id(self, cursor):

        cursor.execute("""
            SELECT MAX(
                CAST(SUBSTRING(id_peminjaman, 4) AS UNSIGNED)
            )
            FROM peminjaman
        """)

        hasil = cursor.fetchone()
        nomor = (hasil[0] or 0) + 1

        return f"PJM{nomor:03d}"

    # ==================================================
    # MENAMPILKAN DATA PEMINJAMAN
    # ==================================================

    def tampilkan(self, keyword=""):

        conn = self.db.hubungkan()
        cursor = conn.cursor()

        try:
            pencarian = f"%{str(keyword).strip()}%"

            cursor.execute("""
                SELECT
                    p.id_peminjaman,
                    a.nama,
                    COALESCE(pt.nama, '-'),
                    p.tanggal_pengajuan,
                    p.tanggal_pinjam,
                    p.status_peminjaman

                FROM peminjaman AS p

                JOIN anggota AS a
                    ON p.anggota_id = a.id_anggota

                LEFT JOIN petugas AS pt
                    ON p.petugas_id = pt.id_petugas

                WHERE
                    p.id_peminjaman LIKE %s
                    OR a.nama LIKE %s
                    OR COALESCE(pt.nama, '') LIKE %s
                    OR p.status_peminjaman LIKE %s

                ORDER BY
                    p.tanggal_pengajuan DESC,
                    p.id_peminjaman DESC
            """, (
                pencarian,
                pencarian,
                pencarian,
                pencarian
            ))

            return cursor.fetchall()

        finally:
            cursor.close()
            conn.close()

    # ==================================================
    # MENAMPILKAN DETAIL SATU TRANSAKSI
    # ==================================================

    def detail_transaksi(self, id_peminjaman):

        conn = self.db.hubungkan()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT
                    p.id_peminjaman,
                    p.anggota_id,
                    a.nama,
                    COALESCE(pt.nama, '-'),
                    p.tanggal_pengajuan,
                    p.tanggal_pinjam,
                    p.status_peminjaman

                FROM peminjaman AS p

                JOIN anggota AS a
                    ON p.anggota_id = a.id_anggota

                LEFT JOIN petugas AS pt
                    ON p.petugas_id = pt.id_petugas

                WHERE p.id_peminjaman = %s
            """, (id_peminjaman,))

            return cursor.fetchone()

        finally:
            cursor.close()
            conn.close()

    # ==================================================
    # MENAMBAHKAN PEMINJAMAN
    # ==================================================

    def tambah(self, anggota_id):

        self._pastikan_boleh_ubah()

        anggota_id = str(anggota_id).strip()

        if not anggota_id:
            raise ValueError("ID anggota harus diisi.")

        conn = self.db.hubungkan()
        cursor = conn.cursor()

        try:

            # Memeriksa anggota
            cursor.execute("""
                SELECT id_anggota
                FROM anggota
                WHERE id_anggota = %s
            """, (anggota_id,))

            anggota = cursor.fetchone()

            if not anggota:
                raise ValueError("ID anggota tidak ditemukan.")

            # Membuat ID baru
            id_baru = self.buat_id(cursor)

            # Menyimpan transaksi peminjaman
            cursor.execute("""
                INSERT INTO peminjaman (
                    id_peminjaman,
                    anggota_id,
                    petugas_id,
                    tanggal_pengajuan,
                    tanggal_pinjam,
                    status_peminjaman
                )

                VALUES (%s, %s, NULL, %s, NULL, 'menunggu')
            """, (
                id_baru,
                anggota_id,
                date.today()
            ))

            conn.commit()

            return id_baru

        except Exception:
            conn.rollback()
            raise

        finally:
            cursor.close()
            conn.close()

    # ==================================================
    # MEMPROSES PEMINJAMAN
    # ==================================================

    def proses_peminjaman(self, id_peminjaman, id_petugas):

        self._pastikan_boleh_ubah()

        id_peminjaman = str(id_peminjaman).strip()
        id_petugas = str(id_petugas).strip()

        if not id_peminjaman:
            raise ValueError("ID peminjaman harus diisi.")

        if not id_petugas:
            raise ValueError("ID petugas harus diisi.")

        conn = self.db.hubungkan()
        cursor = conn.cursor()

        try:

            # Mengunci transaksi peminjaman
            cursor.execute("""
                SELECT status_peminjaman
                FROM peminjaman
                WHERE id_peminjaman = %s
                FOR UPDATE
            """, (id_peminjaman,))

            transaksi = cursor.fetchone()

            if not transaksi:
                raise ValueError("Data peminjaman tidak ditemukan.")

            if transaksi[0] != "menunggu":
                raise ValueError(
                    "Hanya peminjaman berstatus menunggu "
                    "yang dapat diproses."
                )

            # Memeriksa petugas
            cursor.execute("""
                SELECT id_petugas
                FROM petugas
                WHERE id_petugas = %s
            """, (id_petugas,))

            if not cursor.fetchone():
                raise ValueError("ID petugas tidak ditemukan.")

            # Mengambil seluruh buku dalam transaksi
            cursor.execute("""
                SELECT buku_id, jumlah
                FROM detail_peminjaman
                WHERE peminjaman_id = %s
                FOR UPDATE
            """, (id_peminjaman,))

            daftar_buku = cursor.fetchall()

            if not daftar_buku:
                raise ValueError(
                    "Belum ada buku yang ditambahkan "
                    "ke detail peminjaman."
                )

            # Menentukan tanggal peminjaman dan jatuh tempo
            tanggal_pinjam = date.today()
            tanggal_jatuh_tempo = tanggal_pinjam + timedelta(days=30)

            # Memeriksa dan mengurangi stok setiap buku
            for buku_id, jumlah in daftar_buku:

                # Memastikan jumlah buku valid
                if jumlah is None or jumlah <= 0:
                    raise ValueError(
                        f"Jumlah buku dengan ID {buku_id} "
                        "tidak valid."
                    )

                # Mengunci data stok buku
                cursor.execute("""
                    SELECT stok_tersedia
                    FROM buku
                    WHERE id_buku = %s
                    FOR UPDATE
                """, (buku_id,))

                buku = cursor.fetchone()

                if not buku:
                    raise ValueError(
                        f"Buku dengan ID {buku_id} tidak ditemukan."
                    )

                stok = buku[0]

                if stok is None or stok < jumlah:
                    raise ValueError(
                        f"Stok buku {buku_id} tidak mencukupi. "
                        f"Stok tersedia: {stok}, "
                        f"jumlah diminta: {jumlah}."
                    )

                # Mengurangi stok dengan kondisi pengaman
                cursor.execute("""
                    UPDATE buku
                    SET stok_tersedia = stok_tersedia - %s
                    WHERE id_buku = %s
                    AND stok_tersedia >= %s
                """, (
                    jumlah,
                    buku_id,
                    jumlah
                ))

                if cursor.rowcount != 1:
                    raise ValueError(
                        f"Gagal memperbarui stok buku {buku_id}. "
                        "Silakan periksa kembali stok yang tersedia."
                    )

            # Mengisi tanggal jatuh tempo seluruh detail buku
            cursor.execute("""
                UPDATE detail_peminjaman
                SET tanggal_jatuh_tempo = %s
                WHERE peminjaman_id = %s
            """, (
                tanggal_jatuh_tempo,
                id_peminjaman
            ))

            # Mengubah transaksi menjadi peminjaman aktif
            cursor.execute("""
                UPDATE peminjaman

                SET
                    petugas_id = %s,
                    tanggal_pinjam = %s,
                    status_peminjaman = 'dipinjam'

                WHERE id_peminjaman = %s
                AND status_peminjaman = 'menunggu'
            """, (
                id_petugas,
                tanggal_pinjam,
                id_peminjaman
            ))

            if cursor.rowcount != 1:
                raise ValueError(
                    "Status peminjaman gagal diperbarui."
                )

            conn.commit()

        except Exception:
            conn.rollback()
            raise

        finally:
            cursor.close()
            conn.close()

    # ==================================================
    # MENOLAK PEMINJAMAN
    # ==================================================

    def tolak(self, id_peminjaman, id_petugas):

        self._pastikan_boleh_ubah()

        id_peminjaman = str(id_peminjaman).strip()
        id_petugas = str(id_petugas).strip()

        if not id_peminjaman:
            raise ValueError("ID peminjaman harus diisi.")

        if not id_petugas:
            raise ValueError("ID petugas harus diisi.")

        conn = self.db.hubungkan()
        cursor = conn.cursor()

        try:

            # Memeriksa dan mengunci transaksi
            cursor.execute("""
                SELECT status_peminjaman
                FROM peminjaman
                WHERE id_peminjaman = %s
                FOR UPDATE
            """, (id_peminjaman,))

            transaksi = cursor.fetchone()

            if not transaksi:
                raise ValueError("Data peminjaman tidak ditemukan.")

            if transaksi[0] != "menunggu":
                raise ValueError(
                    "Hanya peminjaman berstatus menunggu "
                    "yang dapat ditolak."
                )

            # Memeriksa petugas
            cursor.execute("""
                SELECT id_petugas
                FROM petugas
                WHERE id_petugas = %s
            """, (id_petugas,))

            if not cursor.fetchone():
                raise ValueError("ID petugas tidak ditemukan.")

            # Mengubah status menjadi ditolak
            cursor.execute("""
                UPDATE peminjaman

                SET
                    petugas_id = %s,
                    status_peminjaman = 'ditolak'

                WHERE id_peminjaman = %s
                AND status_peminjaman = 'menunggu'
            """, (
                id_petugas,
                id_peminjaman
            ))

            if cursor.rowcount != 1:
                raise ValueError("Status peminjaman gagal diperbarui.")

            conn.commit()

        except Exception:
            conn.rollback()
            raise

        finally:
            cursor.close()
            conn.close()

    # ==================================================
    # MENGHAPUS PEMINJAMAN
    # ==================================================

    def hapus(self, id_peminjaman):

        self._pastikan_boleh_ubah()

        id_peminjaman = str(id_peminjaman).strip()
        if not id_peminjaman:
            raise ValueError("ID peminjaman harus diisi.")
        conn = self.db.hubungkan()
        cursor = conn.cursor()
        try:
            # Memeriksa dan mengunci transaksi
            cursor.execute("""
                SELECT status_peminjaman
                FROM peminjaman
                WHERE id_peminjaman = %s
                FOR UPDATE
            """, (id_peminjaman,))

            transaksi = cursor.fetchone()

            if not transaksi:
                raise ValueError("Data peminjaman tidak ditemukan.")

            if transaksi[0] != "menunggu":
                raise ValueError(
                    "Hanya peminjaman berstatus menunggu "
                    "yang dapat dihapus."
                )

            # Menghapus detail terlebih dahulu karena FK RESTRICT
            cursor.execute("""
                DELETE FROM detail_peminjaman
                WHERE peminjaman_id = %s
            """, (id_peminjaman,))

            # Menghapus transaksi utama
            cursor.execute("""
                DELETE FROM peminjaman
                WHERE id_peminjaman = %s
            """, (id_peminjaman,))

            conn.commit()

        except Exception:
            conn.rollback()
            raise

        finally:
            cursor.close()
            conn.close()

    # ==================================================
    # STATISTIK PEMINJAMAN
    # ==================================================

    def statistik(self):
        conn = self.db.hubungkan()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT COUNT(*),
                    COALESCE(SUM(status_peminjaman = 'menunggu'), 0),
                    COALESCE(SUM(status_peminjaman = 'dipinjam'), 0),
                    COALESCE(SUM(status_peminjaman = 'ditolak'), 0),
                    COALESCE(SUM(status_peminjaman = 'selesai'), 0)
                FROM peminjaman""")
            hasil = cursor.fetchone()
            return {
                "total": hasil[0] or 0,
                "menunggu": hasil[1] or 0,
                "dipinjam": hasil[2] or 0,
                "ditolak": hasil[3] or 0,
                "selesai": hasil[4] or 0
            }
        finally:
            cursor.close()
            conn.close()