import hashlib
import re
import secrets
from koneksi import Database


MIN_PANJANG_PASSWORD = 6

# Sama dengan aturan di halaman Profil Saya (anggota)
POLA_TELEPON = re.compile(r"^[0-9+\-\s]{8,20}$")


class Anggota:
    def __init__(self): self.db = Database()

    def buat_hash_password(self, password):
        """Menyimpan password dalam bentuk hash, bukan teks asli."""
        salt = secrets.token_hex(16)
        hasil = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            600000
        ).hex()
        return f"pbkdf2_sha256$600000${salt}${hasil}"

    def buat_id(self, cursor):
        cursor.execute("""
            SELECT MAX(CAST(SUBSTRING(id_anggota, 4) AS UNSIGNED))
            FROM anggota WHERE id_anggota REGEXP '^AGT[0-9]+$'
        """)
        hasil = cursor.fetchone()[0]
        nomor = (hasil or 0) + 1
        return f"AGT{nomor:03d}"

    # ==================== PEMERIKSAAN ====================

    @staticmethod
    def _cek_telepon(telepon):
        if telepon and not POLA_TELEPON.match(telepon):
            raise ValueError(
                "Nomor telepon hanya boleh berisi angka, spasi, tanda + dan -, "
                "dengan panjang 8 sampai 20 karakter."
            )

    @staticmethod
    def _cek_password(password):
        if password and len(password) < MIN_PANJANG_PASSWORD:
            raise ValueError(
                f"Password minimal {MIN_PANJANG_PASSWORD} karakter."
            )

    @staticmethod
    def _cek_username(cursor, username, kecuali=None):
        """Username tidak boleh dipakai anggota lain."""
        if not username:
            return
        if kecuali is None:
            cursor.execute(
                "SELECT 1 FROM anggota WHERE username = %s LIMIT 1",
                (username,))
        else:
            cursor.execute(
                "SELECT 1 FROM anggota "
                "WHERE username = %s AND id_anggota <> %s LIMIT 1",
                (username, kecuali))
        if cursor.fetchone() is not None:
            raise ValueError(f"Username '{username}' sudah dipakai.")

    # ==================== TAMPILKAN ====================

    def tampilkan(self, kata_kunci=""):
        conn = self.db.hubungkan()
        try:
            cursor = conn.cursor()
            sql = """
                SELECT id_anggota, nama, alamat, no_telepon, username, tanggal_daftar
                FROM anggota
            """
            if kata_kunci.strip():
                sql += """
                    WHERE id_anggota LIKE %s
                       OR nama LIKE %s
                       OR no_telepon LIKE %s
                       OR username LIKE %s
                """
                pola = f"%{kata_kunci.strip()}%"
                cursor.execute(
                    sql + " ORDER BY nama",
                    (pola, pola, pola, pola)
                )
            else:
                cursor.execute(sql + " ORDER BY nama")
            return cursor.fetchall()
        finally:
            cursor.close()
            conn.close()

    # ==================== TAMBAH ====================

    def tambah(self, data):
        nama = data["nama"].strip()
        alamat = data["alamat"].strip() or None
        telepon = data["no_telepon"].strip() or None
        username = data["username"].strip() or None
        password = data["password"]
        if not nama:
            raise ValueError("Nama anggota wajib diisi.")
        if username and not password:
            raise ValueError(
                "Password wajib diisi jika username digunakan."
            )
        if password and not username:
            raise ValueError(
                "Isi username terlebih dahulu jika menggunakan password."
            )
        self._cek_telepon(telepon)
        self._cek_password(password)
        conn = self.db.hubungkan()
        cursor = None
        try:
            cursor = conn.cursor()
            self._cek_username(cursor, username)
            id_anggota = self.buat_id(cursor)
            password_hash = (
                self.buat_hash_password(password)
                if password else None
            )
            cursor.execute("""
                INSERT INTO anggota (id_anggota, nama, alamat, no_telepon, username, password_hash, tanggal_daftar)
                VALUES (%s, %s, %s, %s, %s, %s, CURDATE())
            """, (id_anggota, nama, alamat, telepon, username, password_hash))
            conn.commit()
            return id_anggota
        except Exception:
            conn.rollback()
            raise
        finally:
            if cursor is not None:
                cursor.close()
            conn.close()

    # ==================== UBAH ====================

    def ubah(self, id_anggota, data):
        nama = data["nama"].strip()
        alamat = data["alamat"].strip() or None
        telepon = data["no_telepon"].strip() or None
        username = data["username"].strip() or None
        password = data["password"]
        if not nama:
            raise ValueError("Nama anggota wajib diisi.")
        if password and not username:
            raise ValueError(
                "Isi username terlebih dahulu jika mengganti password."
            )
        self._cek_telepon(telepon)
        self._cek_password(password)
        conn = self.db.hubungkan()
        cursor = None
        try:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT password_hash FROM anggota "
                "WHERE id_anggota = %s FOR UPDATE",
                (id_anggota,))
            baris = cursor.fetchone()
            if baris is None:
                raise ValueError("Data anggota tidak ditemukan.")

            # Akun baru (belum punya password) wajib diberi password.
            if username and not password and baris[0] is None:
                raise ValueError(
                    "Anggota ini belum memiliki password. "
                    "Isi password untuk mengaktifkan akunnya."
                )

            self._cek_username(cursor, username, kecuali=id_anggota)

            if password:
                password_hash = self.buat_hash_password(password)
                cursor.execute("""
                    UPDATE anggota SET nama = %s, alamat = %s, no_telepon = %s, username = %s, password_hash = %s WHERE id_anggota = %s
                """, (
                    nama, alamat, telepon, username, password_hash, id_anggota))
            else:
                cursor.execute("""
                    UPDATE anggota SET nama = %s, alamat = %s, no_telepon = %s, username = %s WHERE id_anggota = %s
                """, (
                    nama, alamat, telepon, username, id_anggota))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            if cursor is not None:
                cursor.close()
            conn.close()

    # ==================== HAPUS ====================

    def hapus(self, id_anggota):
        conn = self.db.hubungkan()
        cursor = None
        try:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM anggota WHERE id_anggota = %s",
                (id_anggota,))
            if cursor.rowcount == 0:
                raise ValueError("Data anggota tidak ditemukan.")
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            if cursor is not None:
                cursor.close()
            conn.close()