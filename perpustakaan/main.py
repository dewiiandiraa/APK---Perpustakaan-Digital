import faulthandler
import traceback
import tkinter as tk
from ikon import pasang_ikon

faulthandler.enable()


def catat(teks):
    print(teks, flush=True)

    try:
        with open("jejak.txt", "a", encoding="utf-8") as f:
            f.write(teks + "\n")
    except OSError:
        pass


def lapor_callback(jenis, nilai, jejak):
    catat(
        "ERROR DI DALAM EVENT TKINTER:\n" +
        "".join(traceback.format_exception(jenis, nilai, jejak))
    )


def jalankan():

    from login import AppLogin
    from dashboard import AppDashboard

    while True:

        hasil = {}

        def saat_login(sesi):
            catat("[1b] callback login dipanggil")
            hasil["session"] = sesi

        catat("[1] membuka jendela login")

        root = tk.Tk()
        pasang_ikon(root)                                  # ← BARU (1)
        root.report_callback_exception = lapor_callback

        AppLogin(root, on_login_success=saat_login)

        root.mainloop()

        # Hancurkan root setelah mainloop selesai
        try:
            root.destroy()
        except tk.TclError:
            pass

        catat(
            f"[2] jendela login selesai, "
            f"session = {hasil.get('session')}"
        )

        if "session" not in hasil:
            catat("-> Login ditutup tanpa sesi, program berhenti")
            break

        catat("[3] membuat dashboard")

        root = tk.Tk()
        pasang_ikon(root)                                  # ← BARU (2)
        root.report_callback_exception = lapor_callback

        dashboard = AppDashboard(root, hasil["session"])

        catat("[4] dashboard berhasil dibuat, masuk mainloop")

        root.mainloop()

        catat(
            f"[5] dashboard ditutup, logout = {dashboard.logout}"
        )

        try:
            root.destroy()
        except tk.TclError:
            pass

        if not dashboard.logout:
            break


if __name__ == "__main__":

    open("jejak.txt", "w", encoding="utf-8").close()

    try:
        jalankan()
        catat("[SELESAI] program berakhir normal")

    except Exception:
        catat("ERROR PROGRAM:\n" + traceback.format_exc())