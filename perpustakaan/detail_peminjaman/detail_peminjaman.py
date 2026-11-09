from datetime import date
from koneksi import Database


class DetailPeminjaman:

    # hanya_lihat=True (operator): semua operasi yang mengubah data ditolak.
    def __init__(self, hanya_lihat=False):
        self.db = Database()
        self.hanya_lihat = hanya_lihat

    def _pastikan_boleh_ubah(self):
        if self.hanya_lihat:
            raise PermissionError(
                "Anda hanya dapat melihat detail peminjaman."
            )

    # ==================================================
    # MEMBUAT ID DETAIL
    # ==================================================

    def buat_id(self, cursor):

        cursor.execute("""
            SELECT MAX(
                CAST(SUBSTRING(id_detail, 4) AS UNSIGNED)
            )
            FROM detail_peminjaman
        """)

        hasil = cursor.fetchone()
        nomor = (hasil[0] or 0) + 1

        return f"DTL{nomor:03d}"

    # ==================================================
    # MENAMPILKAN DATA DETAIL
    # ==================================================

    def tampilkan(self, peminjaman_id):

        conn = self.db.hubungkan()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT
                    d.id_detail,
                    d.peminjaman_id,
                    d.buku_id,
                    b.judul,
                    d.jumlah,
                    d.tanggal_jatuh_tempo,
                    d.tanggal_kembali

                FROM detail_peminjaman AS d

                JOIN buku AS b
                    ON d.buku_id = b.id_buku

                WHERE d.peminjaman_id = %s

                ORDER BY d.id_detail
            """, (peminjaman_id,))

            return cursor.fetchall()

        finally:
            cursor.close()
            conn.close()

    # ==================================================
    # MENAMBAHKAN DETAIL PEMINJAMAN
    # ==================================================

    def tambah(self, peminjaman_id, buku_id, jumlah):

        self._pastikan_boleh_ubah()

        if not isinstance(peminjaman_id, str) or not peminjaman_id.strip():
            raise ValueError("ID peminjaman harus diisi.")

        if not isinstance(buku_id, str) or not buku_id.strip():
            raise ValueError("ID buku harus diisi.")

        peminjaman_id = peminjaman_id.strip()
        buku_id = buku_id.strip()

        try:
            jumlah = int(jumlah)
        except (ValueError, TypeError):
            raise ValueError("Jumlah buku harus berupa angka.")

        if jumlah <= 0:
            raise ValueError("Jumlah buku harus lebih dari 0.")

        conn = self.db.hubungkan()
        cursor = conn.cursor()

        try:

            # Mengunci transaksi peminjaman
            cursor.execute("""
                SELECT status_peminjaman
                FROM peminjaman
                WHERE id_peminjaman = %s
                FOR UPDATE
            """, (peminjaman_id,))

            transaksi = cursor.fetchone()

            if not transaksi:
                raise ValueError(
                    "Transaksi peminjaman tidak ditemukan."
                )

            if transaksi[0] != "menunggu":
                raise ValueError(
                    "Detail hanya dapat ditambahkan pada "
                    "peminjaman berstatus menunggu."
                )

            # Memeriksa keberadaan buku
            cursor.execute("""
                SELECT id_buku
                FROM buku
                WHERE id_buku = %s
            """, (buku_id,))

            if not cursor.fetchone():
                raise ValueError("Buku tidak ditemukan.")

            # Memeriksa apakah buku sudah ada dalam transaksi
            cursor.execute("""
                SELECT id_detail
                FROM detail_peminjaman
                WHERE peminjaman_id = %s
                AND buku_id = %s
            """, (peminjaman_id, buku_id))

            if cursor.fetchone():
                raise ValueError(
                    "Buku tersebut sudah ada dalam transaksi ini. "
                    "Gunakan fitur ubah jumlah."
                )

            # Membuat ID detail baru
            id_baru = self.buat_id(cursor)

            # Menyimpan detail peminjaman
            cursor.execute("""
                INSERT INTO detail_peminjaman (
                    id_detail,
                    peminjaman_id,
                    buku_id,
                    jumlah,
                    tanggal_jatuh_tempo,
                    tanggal_kembali
                )

                VALUES (%s, %s, %s, %s, NULL, NULL)
            """, (
                id_baru,
                peminjaman_id,
                buku_id,
                jumlah
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
    # MENGUBAH JUMLAH BUKU
    # ==================================================

    def ubah(self, id_detail, jumlah):

        self._pastikan_boleh_ubah()

        if not isinstance(id_detail, str) or not id_detail.strip():
            raise ValueError("ID detail harus diisi.")

        id_detail = id_detail.strip()

        try:
            jumlah = int(jumlah)
        except (ValueError, TypeError):
            raise ValueError("Jumlah buku harus berupa angka.")

        if jumlah <= 0:
            raise ValueError("Jumlah buku harus lebih dari 0.")

        conn = self.db.hubungkan()
        cursor = conn.cursor()

        try:

            # Mengambil ID transaksi dari detail
            cursor.execute("""
                SELECT peminjaman_id
                FROM detail_peminjaman
                WHERE id_detail = %s
            """, (id_detail,))

            detail = cursor.fetchone()

            if not detail:
                raise ValueError(
                    "Detail peminjaman tidak ditemukan."
                )

            peminjaman_id = detail[0]

            # Mengunci transaksi utama
            cursor.execute("""
                SELECT status_peminjaman
                FROM peminjaman
                WHERE id_peminjaman = %s
                FOR UPDATE
            """, (peminjaman_id,))

            transaksi = cursor.fetchone()

            if not transaksi:
                raise ValueError(
                    "Transaksi peminjaman tidak ditemukan."
                )

            if transaksi[0] != "menunggu":
                raise ValueError(
                    "Jumlah buku hanya dapat diubah pada "
                    "peminjaman berstatus menunggu."
                )

            # Mengunci dan memastikan detail masih tersedia
            cursor.execute("""
                SELECT id_detail
                FROM detail_peminjaman
                WHERE id_detail = %s
                AND peminjaman_id = %s
                FOR UPDATE
            """, (id_detail, peminjaman_id))

            if not cursor.fetchone():
                raise ValueError(
                    "Detail peminjaman tidak ditemukan."
                )

            # Memperbarui jumlah buku
            cursor.execute("""
                UPDATE detail_peminjaman
                SET jumlah = %s
                WHERE id_detail = %s
            """, (jumlah, id_detail))

            conn.commit()

        except Exception:
            conn.rollback()
            raise

        finally:
            cursor.close()
            conn.close()

    # ==================================================
    # MENGHAPUS DETAIL PEMINJAMAN
    # ==================================================

    def hapus(self, id_detail):

        self._pastikan_boleh_ubah()

        if not isinstance(id_detail, str) or not id_detail.strip():
            raise ValueError("ID detail harus diisi.")

        id_detail = id_detail.strip()

        conn = self.db.hubungkan()
        cursor = conn.cursor()

        try:

            # Mengambil ID transaksi dari detail
            cursor.execute("""
                SELECT peminjaman_id
                FROM detail_peminjaman
                WHERE id_detail = %s
            """, (id_detail,))

            detail = cursor.fetchone()

            if not detail:
                raise ValueError(
                    "Detail peminjaman tidak ditemukan."
                )

            peminjaman_id = detail[0]

            # Mengunci transaksi utama
            cursor.execute("""
                SELECT status_peminjaman
                FROM peminjaman
                WHERE id_peminjaman = %s
                FOR UPDATE
            """, (peminjaman_id,))

            transaksi = cursor.fetchone()

            if not transaksi:
                raise ValueError(
                    "Transaksi peminjaman tidak ditemukan."
                )

            if transaksi[0] != "menunggu":
                raise ValueError(
                    "Detail hanya dapat dihapus pada "
                    "peminjaman berstatus menunggu."
                )

            # Mengunci dan memastikan detail masih tersedia
            cursor.execute("""
                SELECT id_detail
                FROM detail_peminjaman
                WHERE id_detail = %s
                AND peminjaman_id = %s
                FOR UPDATE
            """, (id_detail, peminjaman_id))

            if not cursor.fetchone():
                raise ValueError(
                    "Detail peminjaman tidak ditemukan."
                )

            # Menghapus detail buku
            cursor.execute("""
                DELETE FROM detail_peminjaman
                WHERE id_detail = %s
            """, (id_detail,))

            conn.commit()

        except Exception:
            conn.rollback()
            raise

        finally:
            cursor.close()
            conn.close()

    # ==================================================
    # PENGEMBALIAN SELURUH BUKU DALAM SATU TRANSAKSI
    # ==================================================

    def kembalikan(self, peminjaman_id):

        self._pastikan_boleh_ubah()

        if not isinstance(peminjaman_id, str) or not peminjaman_id.strip():
            raise ValueError("ID peminjaman harus diisi.")

        peminjaman_id = peminjaman_id.strip()

        conn = self.db.hubungkan()
        cursor = conn.cursor()

        try:

            # Mengunci transaksi peminjaman
            cursor.execute("""
                SELECT status_peminjaman
                FROM peminjaman
                WHERE id_peminjaman = %s
                FOR UPDATE
            """, (peminjaman_id,))

            transaksi = cursor.fetchone()

            if not transaksi:
                raise ValueError(
                    "Transaksi peminjaman tidak ditemukan."
                )

            if transaksi[0] != "dipinjam":
                raise ValueError(
                    "Pengembalian hanya dapat dilakukan pada "
                    "peminjaman berstatus dipinjam."
                )

            # Mengambil dan mengunci seluruh detail buku
            cursor.execute("""
                SELECT
                    buku_id,
                    jumlah,
                    tanggal_kembali

                FROM detail_peminjaman

                WHERE peminjaman_id = %s
                FOR UPDATE
            """, (peminjaman_id,))

            daftar_buku = cursor.fetchall()

            if not daftar_buku:
                raise ValueError(
                    "Tidak ada buku dalam transaksi ini."
                )

            # Memastikan semua detail belum dikembalikan
            for buku_id, jumlah, tanggal_kembali in daftar_buku:

                if tanggal_kembali is not None:
                    raise ValueError(
                        "Ditemukan buku yang sudah memiliki "
                        "tanggal pengembalian. Periksa transaksi "
                        "sebelum melanjutkan."
                    )

                if jumlah is None or jumlah <= 0:
                    raise ValueError(
                        f"Jumlah buku {buku_id} tidak valid."
                    )

            # Menentukan tanggal pengembalian
            tanggal_kembali_sekarang = date.today()

            # Mengembalikan stok seluruh buku
            for buku_id, jumlah, _ in daftar_buku:

                cursor.execute("""
                    UPDATE buku

                    SET stok_tersedia = stok_tersedia + %s

                    WHERE id_buku = %s
                """, (jumlah, buku_id))

                if cursor.rowcount != 1:
                    raise ValueError(
                        f"Buku dengan ID {buku_id} "
                        "tidak ditemukan atau stok gagal diperbarui."
                    )

            # Mengisi tanggal pengembalian seluruh detail
            cursor.execute("""
                UPDATE detail_peminjaman

                SET tanggal_kembali = %s

                WHERE peminjaman_id = %s
                AND tanggal_kembali IS NULL
            """, (
                tanggal_kembali_sekarang,
                peminjaman_id
            ))

            if cursor.rowcount != len(daftar_buku):
                raise ValueError(
                    "Tanggal pengembalian gagal diperbarui "
                    "untuk seluruh buku."
                )

            # Mengubah status transaksi menjadi selesai
            cursor.execute("""
                UPDATE peminjaman

                SET status_peminjaman = 'selesai'

                WHERE id_peminjaman = %s
                AND status_peminjaman = 'dipinjam'
            """, (peminjaman_id,))

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