import sys
import traceback
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import tkinter as tk

from ikon import pasang_ikon

# File login/dashboard anggota ada di folder anggota/; bila tidak ada,
# dicoba di folder proyek.
try:
    from anggota.login_anggota import AppLoginAnggota
    from anggota.dashboard_anggota import AppDashboardAnggota
except ImportError:
    from anggota.login_anggota import AppLoginAnggota
    from anggota.dashboard_anggota import AppDashboardAnggota


def catat(teks):

    print(teks, flush=True)

    try:
        with open(ROOT_DIR / "jejak.txt", "a", encoding="utf-8") as f:
            f.write(teks + "\n")
    except OSError:
        pass


def lapor_error(jenis, nilai, jejak):

    catat(
        "ERROR DI DALAM EVENT TKINTER:\n"
        + "".join(traceback.format_exception(jenis, nilai, jejak))
    )


def hancurkan(root):

    try:
        root.destroy()
    except tk.TclError:
        pass  # jendela sudah ditutup


def buat_jendela():

    root = tk.Tk()
    pasang_ikon(root)
    root.report_callback_exception = lapor_error

    return root


def jalankan():

    while True:

        # ---------- Login ----------
        hasil = {}

        root = buat_jendela()

        AppLoginAnggota(
            root,
            on_login_success=lambda sesi: hasil.update(session=sesi)
        )

        root.mainloop()
        hancurkan(root)

        if "session" not in hasil:
            break  # jendela login ditutup

        # ---------- Dashboard ----------
        root = buat_jendela()

        dashboard = AppDashboardAnggota(root, hasil["session"])

        root.mainloop()

        logout = getattr(dashboard, "logout", False)
        hancurkan(root)

        if not logout:
            break  # jendela dashboard ditutup


if __name__ == "__main__":

    try:
        jalankan()

    except Exception:
        catat("ERROR PROGRAM:\n" + traceback.format_exc())
        raise