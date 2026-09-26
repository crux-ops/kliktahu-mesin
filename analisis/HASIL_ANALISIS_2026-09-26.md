# KlikTahu - Analisis Mendalam 26 September 2026

**Data:** 1.420 frasa unik gabungan dari 4 sumber (18-19 Sep 2026) + validasi eksternal 26 Sep 2026.
**Hasil:** antrean Ep27-Ep36 + paket metadata siap pakai (`PAKET_METADATA.md`).
**Cara jalan ulang:** `python3 analisis/analisis_mendalam.py` (tidak butuh internet).

---

## 1. Ringkasan eksekutif

1. **Tubuh manusia tetap ladang utama** (284 frasa, 5 topik di 15 besar). Disusul antariksa, teknologi, bumi, fisika.
2. **Ep27 = "Kenapa Orang Ngorok?"** - 34 frasa dan semuanya frasa pendek (sinyal volume paling ekstrem di seluruh data).
3. **6 topik baru ditemukan** dari penggalian ulang: luka sembuh, air kencing kuning, lutut bunyi, nasi basi, habis makan ngantuk, ketindihan.
4. **2 jebakan besar dihindari:** "bintang" (penonton bola, bukan sains) dan "misteri gunung" (penonton sinetron). Keduanya terlihat besar sebelum dibersihkan.
5. **Slot eksperimen teknologi** (Ep36, angle sinyal HP) menguji niche volume-terbesar (#1, 46 frasa) tanpa mempertaruhkan identitas channel.

---

## 2. Metode (lebih dalam dari sapuan sebelumnya)

| Aspek | Sapuan lama (18 Sep) | Analisis ini (26 Sep) |
|---|---|---|
| Frasa | 977 (1 sumber) | **1.420 (4 sumber digabung + dedup)** |
| Provenance mesin | tidak ada | 587 frasa bertanda Google/YouTube |
| Topik dinilai | ~16 kata | **54 topik berniche + sinonim** |
| Sinyal skor | 4 | **6 (VOL, CERUK, NIAT, LINTAS, TONTON, BARU)** |
| Pembersihan | tidak ada | **14 topik dibersihkan dari 20+ pola cemaran** |
| Sinyal liar | tidak ada | kata sering di luar topik -> 6 topik baru |
| Validasi luar | tidak ada | tren Shorts 2026 + kompetitor + kalender langit |

**Sumber frasa:** `klaster_besar.json` (977) + `peta_kata_kunci_2026-09-19.json` (per-seed G/Y)
+ `klaster_terbaru.json` (570) + `klaster_2026-09-19.json` (per-niche + bobot).
Hasil gabungan + provenance: `gabungan_frasa_2026-09-26.json`.

**Formula skor (0-100):** `VOL*30 + CERUK*25 + NIAT*15 + LINTAS*10 + TONTON*10 + BARU*10`

- **VOL** = volume (frasa unik + bonus frasa pendek <= 5 kata). Frasa pendek yang muncul
  dari seed pendek = volume pencarian besar (Google/YouTube hanya menyarankan yang ramai).
- **CERUK** = kecocokan ceruk KlikTahu: mekanisme bisa dijelaskan tuntas (0-3) + potensi
  visual diagram (0-3), dikurangi penalti musiman/berita. Satu-satunya komponen kurasi,
  dan nilainya terdokumentasi per topik di `analisis_mendalam.py`.
- **NIAT** = penanda niat: bahaya/aman/cara/kapan/berapa/hari ini/padahal/tiba-tiba/dsb.
- **LINTAS** = % frasa yang muncul di Google DAN YouTube (ada yang mencari DAN menonton).
- **TONTON** = % frasa dari YouTube (niat menonton).
- **BARU** = 10 jika belum dibahas (Ep21-26 dikecualikan dari antrean).

**Kejujuran data:** 833 frasa sapuan besar tidak menyimpan info mesin asal. Topik yang
frasanya tanpa provenance memakai rata-rata global (LINTAS 1,98 / TONTON 4,68 dari 587
frasa berprovenance) - ditandai di kode, bukan nol. Topik tanpa frasa sama sekali tetap nol.

---

## 3. Peringkat niche (di mana ladang views terbesar)

| # | Niche | Frasa | Top-5 skor | Skor max | Vonis |
|---:|---|---:|---:|---:|---|
| 1 | **Tubuh manusia** | 284 | 277,0 | 61,4 (ngorok) | **Ladang utama.** 60% antrean dari sini. |
| 2 | **Luar angkasa** | 76 | 252,5 | 56,3 (lubang hitam) | **Evergreen abadi.** Visual paling megah. |
| 3 | **Teknologi** | 119 | 245,6 | 63,5 (internet) | **Volume terbesar, ceruk lemah.** 1 slot eksperimen saja. |
| 4 | **Bumi & cuaca** | 88 | 221,0 | 55,4 (petir) | Kuat + dramatis. |
| 5 | **Fisika dasar** | 51 | 213,0 | 53,8 (kapal) | Kecil tapi tajam, semua CERUK 10. |
| 6 | **Laut & misteri** | 52 | 171,0 | 58,9 (palung) | Skor max tinggi, ekor tipis. |
| 7 | Hewan | 15 | 105,7 | 39,1 (anjing) | Pendukung. Kucing sudah dibahas. |
| 8 | Sejarah & misteri | 26 | 83,5 | 45,4 (piramida) | Sesekali. Banyak jebakan (lihat bag. 6). |
| 9 | Purba | 12 | 48,4 | 48,4 (megalodon) | Satu amunisi (megalodon), dinosaurus sudah. |

Bacaan: penonton Indonesia paling penasaran pada **badannya sendiri**, lalu pada
**hal besar yang jauh** (angkasa, laut dalam), lalu pada **benda sehari-hari yang
ngadat** (sinyal, baterai). Urutan inilah yang dipakai menyusun antrean.

---

## 4. Peringkat topik (25 besar, yang sudah dibahas ditandai)

S = penanda PR sekolah, I = "menurut islam", H = humor (jokes/gombal/meme).

| # | Topik | Skor | Jml | Pdk | GY | Y | Niat | C | S | I | H | Status |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | internet (sinyal/wifi) | 63,5 | 46 | 30 | 7 | 13 | 17 | 3,3 | 0 | 0 | 0 | Ep36 eksperimen |
| 2 | **ngorok** | 61,4 | 34 | 34 | 2 | 10 | 2 | 8,7 | 0 | 0 | 0 | **Ep27** |
| 3 | palung mariana | 58,9 | 17 | 16 | 5 | 12 | 4 | 10 | 0 | 0 | 0 | Ep28 |
| 4 | baterai HP | 58,0 | 36 | 9 | 3 | 10 | 14 | 5,3 | 0 | 0 | 0 | cadangan |
| 5 | lubang hitam | 56,3 | 27 | 18 | 6 | 13 | 0 | 10 | 0 | 0 | 0 | Ep29 |
| 6 | petir | 55,4 | 18 | 15 | 5 | 10 | 0 | 10 | 0 | 1 | 0 | Ep30 |
| 7 | otak | 54,4 | 11 | 5 | 2 | 3 | 11 | 10 | 0 | 0 | 0 | Ep31 |
| 8 | matahari | 54,4 | 13 | 9 | 1 | 1 | 12 | 10 | 0 | 0 | 0 | Ep32 |
| 9 | kapal besi | 53,8 | 14 | 10 | 4 | 8 | 3 | 10 | 0 | 0 | 0 | Ep33 |
| 10 | demam | 53,6 | 19 | 13 | 5 | 10 | 2 | 8,7 | 0 | 0 | 0 | Ep34 |
| 11 | mata berkedip | 53,4 | 32 | 25 | 4 | 10 | 0 | 6,7 | 0 | 0 | 0 | kit kata kunci |
| 12 | uban | 53,0 | 24 | 15 | 6 | 11 | 1 | 8,7 | 0 | 1 | 0 | Ep35 |
| 13 | cegukan | 52,7 | 20 | 17 | 5 | 10 | 5 | 6,7 | 0 | 0 | 0 | kit kata kunci |
| 14 | pesawat | 51,6 | 16 | 6 | 2 | 7 | 4 | 10 | 0 | 1 | 0 | kit kata kunci |
| 15 | laut asin | 50,5 | 23 | 10 | 3 | 8 | 1 | 8,7 | 0 | 1 | 5 | kit kata kunci |
| 16 | telinga berdenging | 49,8 | 30 | 21 | 3 | 10 | 3 | 5,3 | 0 | 10 | 0 | kit kata kunci |
| 17 | jantung berdebar | 49,6 | 18 | 12 | 0 | 0 | 2 | 8,7 | 0 | 0 | 0 | kit kata kunci |
| 18 | megalodon | 48,4 | 12 | 12 | 3 | 9 | 1 | 8,0 | 0 | 0 | 0 | cadangan |
| 19 | aurora | 47,6 | 13 | 10 | 2 | 5 | 0 | 10 | 0 | 0 | 0 | cadangan |
| 20 | gerhana | 47,2 | 7 | 5 | 1 | 3 | 1 | 9,0 | 0 | 0 | 0 | cadangan (angle: gerhana matahari) |
| 21 | hujan | 46,9 | 26 | 22 | 0 | 0 | 3 | 7,7 | 0 | 0 | 0 | cadangan (niat menonton lemah) |
| 22 | roket mendarat | 45,9 | 4 | 4 | 1 | 2 | 1 | 10 | 0 | 0 | 0 | cadangan |
| 23 | gigi berlubang | 45,6 | 20 | 16 | 0 | 0 | 1 | 6,7 | 0 | 0 | 0 | cadangan |
| 24 | gunung meletus | 45,4 | 10 | 10 | 0 | 0 | 0 | 9,0 | 0 | 0 | 0 | cadangan |
| 25 | piramida | 45,4 | 13 | 9 | 4 | 7 | 0 | 8,0 | 0 | 0 | 3 | cadangan |

Sudah dibahas (tetap dimonitor, tidak masuk antrean): mimpi 60,2 (Ep21, Ep25),
bulan 60,9 (Ep24), kucing 45,5 (Ep23), gempa 44,0 (Ep22), dinosaurus 38,8 (Ep26).

---

## 5. Temuan baru (tidak ada di analisis sebelumnya)

| Topik baru | Frasa | Contoh | Potensi |
|---|---|---|---|
| Kenapa luka gatal saat sembuh? | 6 | `kenapa luka kalau mau sembuh gatal`, `kenapa luka bernanah` | 41,5 - antrian tubuh |
| Kenapa jari keriput kena air? | 11 | `kenapa jari tangan keriput padahal masih muda` | 34,1 - pendek & lucu |
| Kenapa air kencing kuning? | 8 | `kenapa air kencing berbusa`, `...berwarna merah` | 34,4 - tabu = klik |
| Kenapa lutut bunyi krek? | 7 | `kenapa lutut bunyi krek krek`, `...terasa ngilu` | 34,1 - hook suara |
| Kenapa nasi cepat basi? | 5 | `kenapa nasi di mejikom cepat basi` | 32,0 - dapur = semua orang |
| Kenapa habis makan ngantuk? | 3 | `kenapa habis makan ngantuk`, `...mual` | 31,9 - sangat relatable |
| Ketindihan saat tidur | 1 | `apa itu mimpi ketindihan` | 32,3 - butuh sapuan lanjutan |

Semuanya dari niche tubuh (memperkuat vonis niche #1). Empat di antaranya tanpa
provenance (skor kemungkinan underrated) - wajib masuk seed sapuan berikutnya.

---

## 6. Jebakan yang dihindari (hemat 4+ episode gagal)

| Topik | Kelihatannya | Kenyataannya | Keputusan |
|---|---|---|---|
| bintang | 11 frasa "berapa jumlah bintang" | 6 di antaranya bola (persib, spanyol), bendera, FB stars | skor dibersihkan 44,8, tidak masuk antrean |
| misteri gunung | 17 frasa misteri lokal | 4 frasa penonton sinetron ("full episode", "episode 309") | turun ke 38,1, arsip |
| bulan (umum) | 49 frasa | tercampur lagu "bulan madu di awan biru" | sudah dibahas juga (Ep24) |
| megalodon | 17 frasa | film + game Roblox ("fisch", "fish it") ikut menyumbang | dibersihkan, tetap cadangan (fosilnya nyata) |
| darah | "kenapa darah merah" | TIDAK ADA yang mencari; adanya keluhan "keluar darah" | ditolak - supply tanpa demand |
| listrik | "dari mana listrik berasal" | 1 frasa: genset rusak | ditolak - tanpa demand |
| harga | 24 frasa | berita ekonomi (beras, emas, ayam) | ditolak - bukan ceruk |
| haid | 8 frasa | intim + butuh nasihat medis | ditolak - risiko brand |
| hantu | 7 frasa | klenik + "lucu" | ditolak - lawan brand sains |
| nyamuk, bom atom, merinding, bersin | klasik | NOL frasa + seed kosong (tidak ada demand terukur) | ditolak sampai ada data |
| gempa "hari ini" | niat tinggi | berita bencana, basi dalam sehari | sudah dibahas (Ep22), tidak diulang |

Pola "menurut islam" (telinga 10x, uban, laut asin, pesawat, petir, palung 3x):
bukan jebakan, tapi aturan main - jawab sainsnya tuntas, tambah satu baris
menyejukkan di deskripsi bila perlu, jangan pernah menyerang keyakinan.

---

## 7. Pola niat menjadi aturan metadata (dipakai di semua paket)

1. **"padahal" = celah penasaran.** `padahal berat`, `padahal terbuat dari besi`,
   `padahal sudah makan`, `padahal mulut tertutup` - kalimat ini masuk judul/deskripsi
   apa adanya. Otak penonton Shorts berhenti scroll untuk "padahal".
2. **"bahaya" = penutup + komentar.** `kenapa ngorok berbahaya`, jantung + "cemas/sesak".
   Tutup video dengan "kapan harus ke dokter" (1 adegan), jadikan pertanyaan pin.
3. **Parenting = retensi.** `demam anak naik turun`, `bayi cegukan ... cara mengatasinya`.
   Orang tua menonton sampai habis dan menyimpan video.
4. **PR sekolah = evergreen.** `bagaimana pelangi terbentuk kelas 5`, `jelaskan`, `ips`.
   Kata "kelas 5" dan "tugas" masuk tag beberapa episode.
5. **Jokes = umpan tag.** `jokes bapak-bapak`, `tebakan`, `gombal` (laut asin 5x, piramida 3x).
   Jangan dilawan - jadikan tag + satu baris deskripsi supaya video ikut muncul.
6. **Mitos lokal = sudut + tag.** Ka'bah-pesawat, kedutan kiri/kanan, uban-usia-muda,
   "matahari buatan china" (fusi). Dibahas sainsnya, dihormati rasanya.
7. **Baris 1 deskripsi = kata kunci utama apa adanya.** Bukan kalimat puitis.
   Contoh: `Kenapa orang ngorok? Ini penjelasan paling sederhananya.`
8. **Hanya ASCII** di semua paket (tanpa emoji/panah/simbol) supaya aman ditempel.

---

## 8. Validasi eksternal (26 Sep 2026)

- **Shorts sains = niche viral Indonesia 2026.** "Fakta unik dan mengejutkan (sejarah,
  sains)" dan "konten edukasi informal (facts, sejarah, sains)" disebut di antara niche
  Shorts paling berkembang di Indonesia 2026 [1](https://blog.buzzerpanel.id/youtube-shorts-cara-viral-dapat-banyak-views-2026/) [2](https://blog.buzzerpanel.id/youtube-shorts-masterclass-2026-strategi-viral-monetisasi/).
  Shorts Indonesia disebut pasar pertumbuhan tercepat di Asia Tenggara [3](https://blog.buzzerpanel.id/cara-membuat-youtube-shorts-viral-2026-2/).
- **Metode autocomplete tervalidasi.** Panduan Shorts 2026 menyebut YouTube search
  autocomplete sebagai alat riset tren real-time [2](https://blog.buzzerpanel.id/youtube-shorts-masterclass-2026-strategi-viral-monetisasi/) - persis mesin riset repo ini.
- **Kompetitor main long-form, bukan Shorts.** Kok Bisa? (1,1 jt+ subs), Neuron, Sisi Terang,
  Hujan Tanda Tanya semuanya format panjang [4](https://saintif.com/channel-youtube-edukasi/) [5](https://tugumalang.id/5-channel-youtube-edukatif-yang-menjelaskan-fenomena-sehari-hari/).
  KlikTahu Shorts-first = jalur berbeda, bukan tabrakan.
- **Mitos uban sedang viral.** Dokter (dr Saddam Ismail, Jan 2026) dan detikJogja aktif
  meluruskan "cabut uban bikin tambah banyak" [6](https://tourism.owrite.id/cabut-uban-bikin-tambah-banyak-mitos-atau-fakta) [7](https://www.detik.com/jogja/berita/d-7485551/benarkah-rambut-putih-tidak-boleh-dicabut-cek-fakta-dan-akibatnya) -
  Ep35 menunggangi gelombang yang sudah berjalan.
- **Kail kalender langit.** Hujan meteor Geminid Desember 2026 disebut hujan meteor terbaik
  tahun ini dan terlihat dari Indonesia [8](https://www.acehground.com/teknologi/fenomena-astronomi-2026-gerhana-bulan-supermoon-dan-hujan-meteor-akan-hiasi-langit-indonesia/) -
  jendela rilis ideal untuk episode hujan meteor (butuh sapuan lanjutan, data kini tipis).

---

## 9. Antrean Ep27-Ep36 (urutan rilis disarankan)

Niche diselang-seling supaya penonton tidak lelah satu tema.

| Ep | Topik (skor) | Judul utama | Kenapa di sini |
|----|---|---|---|
| 27 | ngorok (61,4) | Kenapa Orang Ngorok? | volume terkuat + ceruk kuat; 34/34 frasa pendek |
| 28 | palung (58,9) | Sedalam Apa Palung Mariana? | CERUK 10; "misteri laut dalam" = retensi |
| 29 | lubang hitam (56,3) | Apa Itu Lubang Hitam? | CERUK 10; evergreen abadi; `apa isi...` = hook |
| 30 | petir (55,4) | Kenapa Petir Menyambar Manusia? | CERUK 10; visual paling dramatis |
| 31 | otak (54,4) | Bagaimana Cara Kerja Otak? | niat 11; mitos kanan/kiri = komentar |
| 32 | matahari (54,4) | Seberapa Besar Matahari? | niat 12; angka raksasa = share |
| 33 | kapal (53,8) | Kenapa Kapal Besi Tidak Tenggelam? | CERUK 10; hook Titanic |
| 34 | demam (53,6) | Kenapa Demam Naik Turun? | parenting; ditonton sampai habis |
| 35 | uban (53,0) | Kenapa Uban Tidak Boleh Dicabut? | mitos viral berjalan; gatal = klik |
| 36 | internet (63,5*) | Kenapa Sinyal HP Tiba-tiba Hilang? | *skor volume; slot eksperimen teknologi |

Paket lengkap (3 judul + deskripsi + tag + hashtag + komentar pin + sudut cerita):
`analisis/PAKET_METADATA.md`. Mata (53,4), cegukan (52,7), pesawat (51,6), laut asin
(50,5), telinga (49,8), jantung (49,6) dapat kit kata kunci di dokumen yang sama dan
boleh tukar posisi dengan Ep34-36 bila produksi butuh variasi.

---

## 10. Cadangan, bayangan, dan seed sapuan lanjutan

**Cadangan terdekat:** baterai HP (58,0 - angle kimia+panas), megalodon (48,4),
aurora (47,6), gerhana matahari (47,2 - bukan bulan, itu sudah Ep24), gigi (45,6),
gunung meletus (45,4), piramida (45,4), gravitasi (45,1), luka sembuh (41,5),
pelangi (41,7 - PR sekolah).

**Kandidat bayangan (butuh sapuan lanjutan sebelum diproduksi):** hujan meteor/Geminid,
ketindihan, tsunami, kencing kuning, lutut krek, nasi basi, habis makan ngantuk,
jari keriput, menguap, segitiga bermuda, roket mendarat.

**Seed sapuan berikutnya** (tambahkan ke `sapuan_besar.py` / `sapuan_mendalam.py`):
`ketindihan, hujan meteor, geminid, tsunami, kencing, lutut, nasi basi, habis makan,
jari keriput, menguap, roket, jantung berdebar, gigi berlubang, gunung meletus,
luka sembuh, tidur` + awalan pendek `ke, ti, hu, ja, lu, na, mo, su, ro, ga`.

---

## 11. Keterbatasan & cara jalan ulang

1. Data autocomplete ditarik 18-19 Sep 2026 (8 hari lalu) - masih segar untuk topik
   evergreen, tapi sapuan ulang disarankan tiap 2-4 minggu atau sebelum batch produksi.
2. Autocomplete mengukur **demand**, bukan **kompetisi**. Klaim "peluang" = demand tinggi
   + angle belum jenuh di Shorts Indonesia (cek manual 5 menit per topik sebelum produksi).
3. Sandbox ini tidak bisa mencapai Google/YouTube (firewall) - sapuan harus dijalankan
   dari komputer dengan internet normal: `python3 analisis/sapuan_besar.py`, lalu
   `python3 analisis/analisis_mendalam.py` (urut otomatis, tanpa internet).
4. Skor CERUK adalah kurasi manusia (terdokumentasi di kode) - boleh diperdebatkan,
   rumusnya terbuka.

**File output:** `gabungan_frasa_2026-09-26.json` (1.420 frasa + provenance),
`skor_topik_2026-09-26.json` (54 topik + 6 sinyal + 12 frasa top),
`skor_niche_2026-09-26.json` (9 niche).
