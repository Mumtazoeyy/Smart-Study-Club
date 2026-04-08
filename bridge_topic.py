import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core_alp.settings')
django.setup()

from alp_app.models import Question, Topic

def pindahkan_data():
    questions = Question.objects.all()
    print(f"Menghubungkan {questions.count()} soal ke tabel Topic baru...")
    
    for q in questions:
        if q.topic:
            # Ambil atau buat nama topik di tabel Topic
            topic_obj, created = Topic.objects.get_or_create(name=q.topic)
            # Hubungkan ke field baru topic_relation
            q.topic_relation = topic_obj
            q.save()
            
    print("Selesai! Semua soal sekarang sudah terhubung secara dinamis.")

if __name__ == "__main__":
    pindahkan_data()