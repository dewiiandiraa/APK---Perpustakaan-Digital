import sys
from pathlib import Path

LOKASI = (
    "assets/logo/app.ico",
    "assets/app.ico",
    "app.ico",
)


def cari_ikon():

    folder = Path(__file__).resolve().parent

    for nama in LOKASI:

        lokasi = folder / nama

        if lokasi.exists():
            return lokasi

    return None


def pasang_ikon(root):
    """Pasang app.ico pada jendela (Tk atau Toplevel). Tidak pernah error."""

    lokasi = cari_ikon()

    if lokasi is None:
        return

    try:
        if sys.platform.startswith("win"):
            root.iconbitmap(default=str(lokasi))
            return

        # Mac / Linux: .ico dibaca lewat Pillow
        from PIL import Image, ImageTk

        gambar = Image.open(lokasi)
        ukuran = gambar.info.get("sizes") or {gambar.size}
        gambar.size = max(ukuran)

        foto = ImageTk.PhotoImage(gambar.convert("RGBA"), master=root)
        root.iconphoto(True, foto)
        root._ikon = foto

    except Exception:
        pass