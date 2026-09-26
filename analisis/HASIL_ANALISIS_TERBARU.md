# KlikTahu - Analisis Kata Kunci Terbaru (real-time)

**Ditarik:** 18 September 2026 (pukul 11.0x WIB) · **Sumber:** Google Autocomplete (hl=id, gl=id) + YouTube Autocomplete (ds=yt, gl=id)
**Frasa unik terkumpul:** 977 (16 awalan pendek + 26 topik) - sebelumnya 584, jadi cakupan naik ~67%.
**Cara jalan ulang:** `python3 analisis/sapuan_besar.py` lalu `python3 analisis/peringkat_topik.py`

---

## 1. Cara skor dihitung (4 sinyal, bukan satu angka)

| sinyal | arti | kenapa penting |
|---|---|---|
| **jml** | berapa frasa unik menyebut topik itu | ukuran permintaan pasar, bukan satu frasa |
| **kuat** | frasa pendek (maks 5 kata) yang muncul bahkan dari awalan sangat pendek ("kenapa ng") | frasa pendek = volume pencarian besar |
| **niat** | frasa dengan penanda niat: hari ini / malam ini / bahaya / aman / kapan / berapa / cara | penanda jenis video yang dicari (penjelasan, urgensi, panduan) |
| **sains** | kecocokan dengan ceruk KlikTahu: ada mekanisme, bisa dijelaskan tuntas dari nol | menjaga channel tetap satu arah (sains & misteri), bukan berita harian |

Skor = `jml + kuat*0,7 + niat*0,9 + sains*3`

---

## 2. Peringkat topik (hasil sapuan hari ini)

| # | topik | jml | kuat | niat | sains | skor | status |
|---:|---|---:|---:|---:|---:|---:|---|
| 1 | kucing | 34 | 25 | 1 | 2,0 | 58,4 | sudah dibahas (Ep23) |
| 2 | gempa | 21 | 16 | 7 | 3,0 | 47,5 | sudah dibahas (Ep22) |
| 3 | **ngorok / mendengkur** | 22 | 22 | 4 | 2,0 | 47,0 | **belum - kandidat utama** |
| 4 | harga (naik) | 25 | 25 | 1 | 1,0 | 46,4 | berita ekonomi, tidak cocok ceruk |
| 5 | hujan / petir | 20 | 20 | 5 | 2,5 | 46,0 | belum - kandidat kuat |
| 6 | mimpi | 21 | 15 | 4 | 3,0 | 44,1 | sudah dibahas (Ep21, Ep25) |
| 7 | tidur | 22 | 21 | 0 | 2,0 | 42,7 | tumpang tindih dengan ngorok |
| 8 | cegukan | 20 | 17 | 4 | 2,0 | 41,5 | belum |
| 9 | **pesawat (berat bisa terbang)** | 16 | 6 | 15 | 2,5 | 41,2 | belum - niat sangat tinggi |
| 10 | baterai cepat habis | 22 | 9 | 8 | 1,5 | 40,0 | belum (teknologi) |
| 11 | air laut asin | 21 | 11 | 1 | 2,5 | 37,1 | belum |
| 12 | demam | 19 | 13 | 3 | 2,0 | 36,8 | belum |
| 13 | gigi berlubang | 20 | 16 | 1 | 1,5 | 36,6 | belum |
| 14 | jantung berdebar | 19 | 13 | 1 | 2,0 | 35,0 | belum |
| 15 | burung terbang | 16 | 6 | 16 | 0,0 | 34,6 | belum |

Daftar lengkap 977 frasa + skor mentah: `analisis/klaster_besar.json`, `analisis/peringkat_topik.json`.

**Contoh frasa terkuat per kandidat baru:**

- ngorok: `kenapa anak tidur ngorok`, `kenapa ayam bisa ngorok`, `kenapa ngorok`, `kenapa tidur mendengkur`
- pesawat: `kenapa pesawat berat bisa terbang`, `kenapa pesawat bisa terbang`, `kenapa burung bisa terbang`
- hujan: `kenapa hujan`, `kenapa hujan ada petir`, `kenapa hujan bikin sakit`
- cegukan: `kenapa bayi cegukan`, `kenapa cegukan terus`, `kenapa cegukan tidak berhenti`
- baterai: `kenapa baterai cepat habis`, `kenapa baterai cepat habis dan panas`

---

## 3. Rekomendasi episode berikutnya

**Ep27 - utama: "Kenapa Orang Ngorok?"** (skor 47,0)
- 22 frasa, semuanya frasa pendek, dan pertanyaan ini menyangkut penonton sendiri + pasangan/keluarga
  (retensi tinggi: penonton menonton untuk orang terdekat, bukan cuma dirinya).
- Bisa dijelaskan tuntas dari nol: jalan napas menyempit saat tidur, getaran langit-langit lunak,
  otot tenggorokan mengendur di fase tidur dalam, hubungan ke berat badan/alkohol/posisi tidur.
- Sudut "bahaya" sudah muncul di data (`kenapa ngorok berbahaya`) - bisa ditutup dengan bagian
  "kapan ngorok perlu diperiksa ke dokter" (sleep apnea), tetap satu arah topik.

**Ep28 - cadangan terdekat: "Kenapa Pesawat Berat Bisa Terbang?"** (skor 41,2)
- Sinyal niat tertinggi di seluruh data (15 frasa berniat); fisika gaya angkat mudah dibuat visual
  besar (sayap, aliran udara, empat gaya), sangat cocok dengan gaya diagram penuh layar.

**Ep29 - cadangan sosial: "Kenapa Hujan Bikin Sakit?"** (skor 46,0)
- Ada penanda niat (petir, sakit), bisa digabung jadi satu tema: "kenapa hujan disertai petir, dan
  kenapa kita gampang sakit saat musim hujan".

---

## 4. Kata kunci siap pakai (untuk judul, deskripsi, tag)

| video | kata kunci judul | kata kunci deskripsi | tag inti |
|---|---|---|---|
| Ep27 ngorok | `kenapa orang ngorok`, `kenapa ngorok`, `kenapa tidur mendengkur` | `kenapa anak tidur ngorok`, `kenapa ngorok berbahaya`, `cara mengatasi ngorok` | ngorok, mendengkur, sleep apnea, tidur sehat, kesehatan tidur |
| Ep28 pesawat | `kenapa pesawat bisa terbang`, `kenapa pesawat berat bisa terbang` | `gaya angkat pesawat`, `kenapa pesawat tidak jatuh`, `kenapa burung bisa terbang` | pesawat, gaya angkat, aerodinamika, fisika, sains |
| Ep29 hujan | `kenapa hujan ada petir`, `kenapa hujan bikin sakit` | `kenapa hujan`, `kenapa petir terjadi`, `kenapa musim hujan gampang sakit` | hujan, petir, cuaca, imun, sains |

---

## 5. Catatan penting untuk pertumbuhan channel

1. **Awalan pendek = volume besar.** Frasa yang muncul dari awalan 5 karakter ("kenapa ng", "kenapa pe")
   hampir pasti dicari banyak orang. Selalu dahulukan frasa jenis ini di judul.
2. **Hindari tema berita harian** (kategori "harga naik" paling besar tapi skor sains rendah):
   pencariannya melonjak lalu mati, sementara Shorts menumpuk tayangan dari video lama.
3. **Satu topik satu arah, tapi tiap episode menutup satu pertanyaan turunan.** Contoh: Ep26 dinosaurus
   menutup "kenapa punah" + "kenapa burung selamat"; Ep27 ngorok menutup "kenapa terjadi" + "kapan bahaya".
4. **Jadwal ulang analisis:** jalankan `sapuan_besar.py` + `peringkat_topik.py` setiap 3-5 episode supaya
   tren baru masuk sebelum kompetitor memakai kata kunci yang sama.
