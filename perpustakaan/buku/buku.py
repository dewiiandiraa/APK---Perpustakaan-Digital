from koneksi import Database

class Buku:
    def __init__(self):
        self.db = Database()

    def tampilkan(self, kata_kunci=""):
        koneksi = self.db.hubungkan()
        try:
            cursor = koneksi.cursor()
            kata = f"%{kata_kunci.strip()}%"
            cursor.execute("""
                SELECT id_buku, judul, penulis, penerbit,
                       tahun_terbit, kategori,
                       stok_total, stok_tersedia
                FROM buku
                WHERE id_buku LIKE %s
                   OR judul LIKE %s
                   OR penulis LIKE %s
                   OR kategori LIKE %s
                ORDER BY id_buku
            """, (kata, kata, kata, kata))

            return cursor.fetchall()

        finally:
            koneksi.close()

    def buat_id(self, cursor):
        cursor.execute("""
            SELECT MAX(CAST(SUBSTRING(id_buku, 3) AS UNSIGNED))
            FROM buku
            WHERE id_buku REGEXP '^BK[0-9]+$'
        """)

        hasil = cursor.fetchone()[0]
        nomor = (hasil or 0) + 1

        return f"BK{nomor:03d}"

    def tambah(self, data):
        judul = data["judul"].strip()
        penulis = data["penulis"].strip()

        if not judul or not penulis:
            raise ValueError("Judul dan penulis wajib diisi.")

        tahun = data["tahun_terbit"].strip()
        stok = data["stok_total"].strip()

        try:
            tahun = int(tahun) if tahun else None
            stok = int(stok)
        except ValueError:
            raise ValueError("Tahun dan stok harus berupa angka.")

        if tahun is not None and not 1901 <= tahun <= 2155:
            raise ValueError("Tahun harus antara 1901 dan 2155.")

        if stok < 0:
            raise ValueError("Stok tidak boleh negatif.")

        koneksi = self.db.hubungkan()

        try:
            cursor = koneksi.cursor()
            id_buku = self.buat_id(cursor)

            cursor.execute("""
                INSERT INTO buku (
                    id_buku, judul, penulis, penerbit,
                    tahun_terbit, kategori, stok_total, stok_tersedia
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                id_buku,
                judul,
                penulis,
                data["penerbit"].strip() or None,
                tahun,
                data["kategori"].strip() or None,
                stok,
                stok
            ))

            koneksi.commit()
            return id_buku

        except Exception:
            koneksi.rollback()
            raise

        finally:
            koneksi.close()

    def ubah(self, id_buku, data):
        judul = data["judul"].strip()
        penulis = data["penulis"].strip()

        if not judul or not penulis:
            raise ValueError("Judul dan penulis wajib diisi.")

        tahun = data["tahun_terbit"].strip()
        stok = data["stok_total"].strip()

        try:
            tahun = int(tahun) if tahun else None
            stok = int(stok)
        except ValueError:
            raise ValueError("Tahun dan stok harus berupa angka.")

        if tahun is not None and not 1901 <= tahun <= 2155:
            raise ValueError("Tahun harus antara 1901 dan 2155.")

        if stok < 0:
            raise ValueError("Stok tidak boleh negatif.")

        koneksi = self.db.hubungkan()

        try:
            cursor = koneksi.cursor()

            cursor.execute("""
                SELECT stok_total, stok_tersedia
                FROM buku
                WHERE id_buku = %s
                FOR UPDATE
            """, (id_buku,))

            hasil = cursor.fetchone()

            if hasil is None:
                raise ValueError("Buku tidak ditemukan.")

            stok_lama, tersedia_lama = hasil
            sedang_dipinjam = stok_lama - tersedia_lama

            if stok < sedang_dipinjam:
                raise ValueError(
                    f"Stok total tidak boleh kurang dari jumlah "
                    f"yang sedang dipinjam ({sedang_dipinjam})."
                )

            tersedia_baru = stok - sedang_dipinjam

            cursor.execute("""
                UPDATE buku
                SET judul = %s,
                    penulis = %s,
                    penerbit = %s,
                    tahun_terbit = %s,
                    kategori = %s,
                    stok_total = %s,
                    stok_tersedia = %s
                WHERE id_buku = %s
            """, (
                judul,
                penulis,
                data["penerbit"].strip() or None,
                tahun,
                data["kategori"].strip() or None,
                stok,
                tersedia_baru,
                id_buku
            ))

            koneksi.commit()

        except Exception:
            koneksi.rollback()
            raise

        finally:
            koneksi.close()

    def hapus(self, id_buku):
        koneksi = self.db.hubungkan()

        try:
            cursor = koneksi.cursor()

            cursor.execute(
                "DELETE FROM buku WHERE id_buku = %s",
                (id_buku,)
            )

            if cursor.rowcount == 0:
                raise ValueError("Buku tidak ditemukan.")

            koneksi.commit()

        except Exception:
            koneksi.rollback()
            raise

        finally:
            koneksi.close()