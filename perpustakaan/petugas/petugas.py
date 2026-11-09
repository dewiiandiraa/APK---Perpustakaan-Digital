import hashlib
import hmac
import secrets

from koneksi import Database


MIN_PANJANG_PASSWORD = 6


class Petugas:
    def __init__(self):
        self.db = Database()

    # Membuat hash password
    def buat_hash_password(self, password):
        salt = secrets.token_hex(16)

        hasil = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            600000
        ).hex()

        return f"pbkdf2_sha256$600000${salt}${hasil}"

    # Memeriksa password terhadap hash yang tersimpan
    def verifikasi_password(self, password, tersimpan):
        try:
            algoritma, putaran, salt, hasil = tersimpan.split("$")

            if algoritma != "pbkdf2_sha256":
                return False

            hitung = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                salt.encode("utf-8"),
                int(putaran)
            ).hex()

            return hmac.compare_digest(hitung, hasil)

        except (ValueError, AttributeError):
            return False

    # Login: mengembalikan dict session, atau None kalau gagal
    def login(self, username, password):
        username = username.strip()

        if not username or not password:
            raise ValueError("Username dan password wajib diisi.")

        conn = self.db.hubungkan()

        try:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id_petugas, nama, username, role, password_hash
                FROM petugas
                WHERE username = %s
            """, (username,))

            baris = cursor.fetchone()

        finally:
            cursor.close()
            conn.close()

        if not baris or not self.verifikasi_password(password, baris[4]):
            return None

        return {
            "id_petugas": baris[0],
            "nama": baris[1],
            "username": baris[2],
            "role": baris[3],
        }

    # Membuat ID petugas otomatis
    def buat_id(self, cursor):
        cursor.execute("""
            SELECT MAX(
                CAST(SUBSTRING(id_petugas, 4) AS UNSIGNED)
            )
            FROM petugas
            WHERE id_petugas REGEXP '^PTG[0-9]+$'
        """)

        hasil = cursor.fetchone()[0]
        nomor = (hasil or 0) + 1

        return f"PTG{nomor:03d}"

    # ==================== PEMERIKSAAN ====================

    @staticmethod
    def _cek_password(password):
        if len(password) < MIN_PANJANG_PASSWORD:
            raise ValueError(
                f"Password minimal {MIN_PANJANG_PASSWORD} karakter."
            )

    @staticmethod
    def _cek_username(cursor, username, kecuali=None):
        """Username tidak boleh dipakai petugas lain."""

        if kecuali is None:
            cursor.execute(
                "SELECT 1 FROM petugas WHERE username = %s LIMIT 1",
                (username,)
            )
        else:
            cursor.execute(
                "SELECT 1 FROM petugas "
                "WHERE username = %s AND id_petugas <> %s LIMIT 1",
                (username, kecuali)
            )

        if cursor.fetchone() is not None:
            raise ValueError(f"Username '{username}' sudah dipakai.")

    @staticmethod
    def _jumlah_operator(cursor):
        cursor.execute(
            "SELECT COUNT(*) FROM petugas WHERE role = 'operator' FOR UPDATE"
        )

        return int(cursor.fetchone()[0])

    @staticmethod
    def _role_petugas(cursor, id_petugas):
        """Role petugas (dikunci untuk transaksi ini); error bila tidak ada."""

        cursor.execute(
            "SELECT role FROM petugas WHERE id_petugas = %s FOR UPDATE",
            (id_petugas,)
        )

        baris = cursor.fetchone()

        if baris is None:
            raise ValueError("Data petugas tidak ditemukan.")

        return str(baris[0]).strip().lower()

    # Menampilkan dan mencari data petugas
    def tampilkan(self, kata_kunci=""):
        conn = self.db.hubungkan()

        try:
            cursor = conn.cursor()

            sql = """
                SELECT
                    id_petugas,
                    nama,
                    username,
                    role
                FROM petugas
            """

            if kata_kunci.strip():
                pola = f"%{kata_kunci.strip()}%"

                sql += """
                    WHERE id_petugas LIKE %s
                       OR nama LIKE %s
                       OR username LIKE %s
                       OR role LIKE %s
                """

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

    # Menambahkan petugas
    def tambah(self, data):
        nama = data["nama"].strip()
        username = data["username"].strip()
        password = data["password"]
        role = data["role"].strip().lower()

        if not nama:
            raise ValueError("Nama petugas wajib diisi.")

        if not username:
            raise ValueError("Username wajib diisi.")

        if not password:
            raise ValueError("Password wajib diisi.")

        self._cek_password(password)

        if role not in ("operator", "petugas"):
            raise ValueError("Role harus operator atau petugas.")

        conn = self.db.hubungkan()

        try:
            cursor = conn.cursor()

            self._cek_username(cursor, username)

            id_petugas = self.buat_id(cursor)
            password_hash = self.buat_hash_password(password)

            cursor.execute("""
                INSERT INTO petugas (
                    id_petugas,
                    nama,
                    username,
                    password_hash,
                    role
                )
                VALUES (%s, %s, %s, %s, %s)
            """, (
                id_petugas,
                nama,
                username,
                password_hash,
                role
            ))

            conn.commit()
            return id_petugas

        except Exception:
            conn.rollback()
            raise

        finally:
            cursor.close()
            conn.close()

    # Mengubah data petugas
    # id_pelaku = ID akun yang sedang login (untuk pengaman akun sendiri)
    def ubah(self, id_petugas, data, id_pelaku=None):
        nama = data["nama"].strip()
        username = data["username"].strip()
        password = data["password"]
        role = data["role"].strip().lower()

        if not nama:
            raise ValueError("Nama petugas wajib diisi.")

        if not username:
            raise ValueError("Username wajib diisi.")

        if role not in ("operator", "petugas"):
            raise ValueError("Role harus operator atau petugas.")

        if password:
            self._cek_password(password)

        conn = self.db.hubungkan()

        try:
            cursor = conn.cursor()

            role_lama = self._role_petugas(cursor, id_petugas)

            if role != role_lama:

                # Akun sendiri: role tidak boleh diubah (bisa terkunci keluar)
                if id_pelaku is not None and str(id_pelaku) == str(id_petugas):
                    raise ValueError(
                        "Anda tidak dapat mengubah role akun Anda sendiri."
                    )

                # Sistem harus selalu punya minimal satu operator
                if (
                    role_lama == "operator"
                    and self._jumlah_operator(cursor) <= 1
                ):
                    raise ValueError(
                        "Role operator terakhir tidak dapat diubah. "
                        "Sistem harus memiliki minimal satu operator."
                    )

            self._cek_username(cursor, username, kecuali=id_petugas)

            if password:
                password_hash = self.buat_hash_password(password)

                cursor.execute("""
                    UPDATE petugas
                    SET nama = %s,
                        username = %s,
                        password_hash = %s,
                        role = %s
                    WHERE id_petugas = %s
                """, (
                    nama,
                    username,
                    password_hash,
                    role,
                    id_petugas
                ))

            else:
                cursor.execute("""
                    UPDATE petugas
                    SET nama = %s,
                        username = %s,
                        role = %s
                    WHERE id_petugas = %s
                """, (
                    nama,
                    username,
                    role,
                    id_petugas
                ))

            conn.commit()

        except Exception:
            conn.rollback()
            raise

        finally:
            cursor.close()
            conn.close()

    # Menghapus petugas
    def hapus(self, id_petugas, id_pelaku=None):

        if id_pelaku is not None and str(id_pelaku) == str(id_petugas):
            raise ValueError("Anda tidak dapat menghapus akun Anda sendiri.")

        conn = self.db.hubungkan()

        try:
            cursor = conn.cursor()

            role = self._role_petugas(cursor, id_petugas)

            # Sistem harus selalu punya minimal satu operator
            if role == "operator" and self._jumlah_operator(cursor) <= 1:
                raise ValueError(
                    "Operator terakhir tidak dapat dihapus. "
                    "Sistem harus memiliki minimal satu operator."
                )

            cursor.execute("""
                DELETE FROM petugas
                WHERE id_petugas = %s
            """, (id_petugas,))

            if cursor.rowcount == 0:
                raise ValueError("Data petugas tidak ditemukan.")

            conn.commit()

        except Exception:
            conn.rollback()
            raise

        finally:
            cursor.close()
            conn.close()