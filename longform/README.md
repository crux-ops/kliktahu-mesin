# KlikTahu Long-form

Ini **jalur terpisah** untuk video YouTube 16:9. Tidak memakai folder `episodes/` dan tidak mengubah mesin Shorts.

## Episode 01
`ep01_besar_tapi_miskin/` membahas mengapa negara besar seperti Indonesia belum otomatis sejahtera, lalu membandingkannya secara hati-hati dengan Singapura. Naskah sengaja menghindari klaim angka yang menyesatkan; angka terbaru harus ditambahkan dari BPS, World Bank, IMF, dan SingStat saat produksi final.

## Preview / animatic
```bash
pip install -r requirements.txt
python3 longform/render_longform.py --preview
python3 longform/render_longform.py --render
```

Output preview dan animatic berada di folder episode. Animatic ini adalah storyboard bergerak 16:9, belum final VO. Audio final sebaiknya direkam per scene dari field `vo` agar transisi, subtitle, dan durasi dapat dikunci berdasarkan rekaman nyata.

## Arah artistik
Editorial dokumenter modern: latar navy, aksen hangat, jaringan garis seperti peta/institusi, typography Poppins, jeda napas antar argumen, dan perbandingan Singapura yang kontekstual—bukan clickbait atau penghinaan.
