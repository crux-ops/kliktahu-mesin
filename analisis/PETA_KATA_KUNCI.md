# Peta Kata Kunci KlikTahu - analisis real-time

> **Versi terbaru & terbesar ada di [`HASIL_ANALISIS_TERBARU.md`](HASIL_ANALISIS_TERBARU.md)** - 977 frasa, skor 4 sinyal
> (jumlah frasa, kekuatan frasa pendek, niat pencarian, kecocokan ceruk sains), lengkap dengan peringkat topik dan
> rekomendasi episode. Dokumen di bawah ini adalah **tampilan per klaster** dari sapuan 587 frasa yang dijalankan
> pada hari yang sama; keduanya saling melengkapi dan boleh dipakai bersama.

**Metode:** Google Autocomplete (hl=id, gl=id) + YouTube Autocomplete (ds=yt) -> **54 seed** -> **703 saran** -> **587 frasa unik**.
**Ditarik:** 19 September 2026. Data mentah: `analisis/peta_kata_kunci_2026-09-19.json`, hasil per klaster: `analisis/klaster_2026-09-19.json`.

**Cara menilai (bukan sekadar jumlah):**
- frasa yang tetap muncul walau seed-nya pendek = permintaan tinggi (Google hanya menyarankan yang banyak dicari)
- frasa yang muncul di **Google dan YouTube** = ada orang mencari **dan** menonton topik itu
- frasa dengan niat "penjelasan/misteri" menang daripada niat "gejala/keluhan" (lebih awet, tidak musiman)

---

## 1. Peringkat klaster (bobot = kemunculan x posisi x sumber)

| # | klaster | frasa | bobot | contoh permintaan terkuat |
|---:|---|---:|---:|---|
| 1 | tubuh manusia | 179 | 521,3 | `kenapa uban tidak boleh dicabut`, `kenapa ngorok`, `kenapa demam anak naik turun`, `kenapa cegukan terus menerus` |
| 2 | luar angkasa | 98 | 227,8 | `misteri antariksa`, `apa itu ufo`, `apa itu aurora`, `apa itu lubang hitam` |
| 3 | bumi & cuaca | 69 | 200,1 | `misteri gunung merapi`, `kenapa petir bisa terjadi`, `kenapa petir menyambar pohon/manusia` |
| 4 | teknologi | 83 | 186,1 | `kenapa sinyal hp hilang`, `kenapa internet lambat`, `bagaimana roket mendarat`, `bagaimana cara kerja wifi` |
| 5 | laut & misteri | 46 | 109,9 | `kenapa laut asin`, `misteri laut dalam`, `kenapa kapal tidak tenggelam`, `berapa dalam palung mariana` |
| 6 | dinosaurus & purba | 32 | 92,5 | `megalodon`, `megalodon vs mosasaurus`, `kenapa dinosaurus tidak ada di indonesia` |
| 7 | lain-lain (fisika dasar) | 35 | 85,5 | `kenapa langit biru`, `kenapa pesawat bisa terbang`, `apa itu gravitasi` |
| 8 | hewan | 29 | 64,6 | `kenapa kucing mengeong terus`, `kenapa anjing menggonggong tengah malam` |
| 9 | sejarah & bangunan | 16 | 36,2 | `misteri piramida mesir`, `kenapa menara pisa miring` |

**Temuan penting untuk channel:**
1. **Grup "tubuh manusia" jauh paling besar** dan hampir semuanya bisa dijelaskan sains dengan visual sederhana -> ini ladang utama KlikTahu.
2. Penonton Indonesia menyisipkan niat **"menurut islam"** pada banyak kueri sains (`kenapa laut asin menurut islam`, `kenapa dinosaurus punah menurut islam`). Strategi: jawab sainsnya tuntas, jangan menyerang keyakinan; cukup satu baris menyejukkan di deskripsi bila perlu.
3. **Misteri lokal menang** (`misteri gunung lawu/gede/padang/merapi` skor 6,6-7,0). Ini peluang besar: misteri Indonesia yang bisa dijelaskan sains.
4. Niat **film/meme** ikut menarik volume (`megalodon film`, `kenapa dinosaurus punah jokes`) - jangan dilawan, manfaatkan di judul/tag supaya video ikut muncul.
5. Kueri **"kenapa X tidak ada di Indonesia"** muncul berulang -> tambahkan **satu paragraf lokal** di deskripsi (bukan di video) untuk menangkap pencarian ini tanpa merusak alur cerita.

---

## 2. Antrean episode (berdasarkan data, siap dikerjakan)

| urut | topik | kata kunci utama | skor | kenapa layak |
|---:|---|---|---:|---|
| **Ep27** | Kenapa Uban Tidak Boleh Dicabut? | `kenapa uban tidak boleh dicabut` · `kenapa uban bikin gatal` | 7,0 | mitos + sains (melanosit, folikel), praktis, ditonton ulang |
| **Ep28** | Kenapa Petir Menyambar Manusia? | `kenapa petir bisa menyambar manusia` · `kenapa petir bersuara` | 6,8 | dramatis, gerak visual kuat (plasma, guntur, penangkal) |
| **Ep29** | Aurora: Kenapa Langit Bisa Menyala? | `apa itu aurora` · `apa itu aurora borealis` | 7,0 | visual paling cantik, cocok untuk upgrade animasi |
| **Ep30** | Misteri Gunung Padang: Piramida atau Bukit? | `misteri gunung padang` · `misteri gunung lawu` | 6,6 | misteri lokal + metode ilmiah (penanggalan karbon) |
| Ep31 | Kenapa Demam Naik Turun? | `kenapa demam anak naik turun` | 7,0 | kebutuhan mendesak orang tua, penjelasan dari nol |
| Ep32 | Megalodon: Benarkah Masih Hidup? | `megalodon` · `megalodon vs mosasaurus` | 7,0 | volume dari film, dibongkar dengan sains |
| Ep33 | Kenapa Kapal Besi Tidak Tenggelam? | `kenapa kapal tidak tenggelam padahal terbuat dari besi` | 3,9 | fisika dasar, visual jelas (massa jenis, ruang udara) |

Aturan tetap: **1 topik/1 arah**, penjelasan dari nol, VO santai (SPEED dasar 1,10 dan **per-adegan** 1,07-1,13: adegan padat angka dibaca paling santai).

---

## 3. Cara memasukkan hasil ini ke deskripsi (template wajib)

1. Baris pertama deskripsi = **kata kunci utama apa adanya** (bukan kalimat puitis). Contoh: `Kenapa dinosaurus punah? Ini penjelasan paling sederhananya.`
2. Paragraf 2 = jawaban singkat 1-2 kalimat (agar orang yang tidak menonton sampai habis tetap dapat jawabannya).
3. Paragraf 3 = poin-poin isi video (pakai tanda `-`, judul bab dengan menit).
4. Paragraf 4 = **satu paragraf lokal/konteks** yang menangkap kueri tambahan (mis. "kenapa dinosaurus tidak ada di Indonesia").
5. Baris sumber + tagar.
6. **Hanya ASCII**: tanpa emoji, tanpa panah, tanpa simbol seperti x/+-/kira-kira. Emoji dan simbol langka merusak tampilan deskripsi saat ditempel di YouTube.
