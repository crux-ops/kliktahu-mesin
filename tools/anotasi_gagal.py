"""Kirim ekor log uji sebagai anotasi GitHub (terbaca lewat API).

Dipakai CI agar penyebab gagal bisa dibaca dari luar tanpa unduh log.
Contoh: python tools/anotasi_gagal.py 1 hasil-uji.txt
"""
import sys


def main():
    kode = sys.argv[1] if len(sys.argv) > 1 else "?"
    berkas = sys.argv[2] if len(sys.argv) > 2 else "hasil-uji.txt"
    try:
        with open(berkas, encoding="utf-8", errors="replace") as f:
            txt = f.read()
    except OSError:
        txt = "(berkas log tidak ada)"
    ekor = txt[-2200:]
    ekor = ekor.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    print(f"::error file=.github/workflows/test.yml,line=1,"
          f"title=Ekor log uji (kode {kode})::{ekor}")


if __name__ == "__main__":
    main()
