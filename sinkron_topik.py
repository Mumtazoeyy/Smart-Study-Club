import os
import django

# Ganti 'core_alp' jika nama folder project utama kamu berbeda
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core_alp.settings')
django.setup()

from alp_app.models import Question

def sinkronkan_total():
    # Kali ini kita ambil SEMUA soal (Question.objects.all()) 
    # untuk memastikan labelnya seragam sesuai keyword
    questions = Question.objects.all()
    
    print(f"Memulai sinkronisasi total untuk {questions.count()} soal...\n")
    
    count = 0
    for q in questions:
        # Kita ambil teks soal dan judul kuis untuk dicocokkan
        txt = q.text.lower() if q.text else ""
        title = q.quiz.title.lower() if q.quiz else ""
        
        old_topic = q.topic # Simpan untuk perbandingan
        
        # MAPPING BERDASARKAN KATA KUNCI (Keyword Matching)
        if any(k in txt or k in title for k in ['suhu', 'kalor', 'pemuaian', 'celcius']):
            q.topic = 'Suhu dan Kalor'
        elif any(k in txt or k in title for k in ['energi', 'fotosintesis', 'makanan', 'metabolisme']):
            q.topic = 'Energi Sistem Kehidupan'
        elif any(k in txt or k in title for k in ['sel', 'organisasi', 'jaringan', 'organ']):
            q.topic = 'Organisasi Kehidupan'
        elif any(k in txt or k in title for k in ['ekosistem', 'jaring-jaring', 'rantai', 'interaksi']):
            q.topic = 'Ekosistem'
        elif any(k in txt or k in title for k in ['pencemaran', 'limbah', 'polusi', 'lingkungan']):
            q.topic = 'Pencemaran Lingkungan'
        elif any(k in txt or k in title for k in ['tata surya', 'planet', 'gerhana', 'orbit']):
            q.topic = 'Tata Surya'
        elif any(k in txt or k in title for k in ['zat', 'wujud', 'perubahan']):
            q.topic = 'Zat dan Perubahannya'
        else:
            # Jika tidak ada yang cocok, gunakan judul Kuisnya sebagai topik
            # Ini mencegah topik menjadi kosong
            q.topic = q.quiz.title if q.quiz else 'Umum'
            
        q.save()
        count += 1
        print(f"[{count}] Updated: {q.text[:30]}... -> {q.topic}")

    print(f"\nSelesai! {count} soal telah disinkronkan.")

if __name__ == "__main__":
    sinkronkan_total()