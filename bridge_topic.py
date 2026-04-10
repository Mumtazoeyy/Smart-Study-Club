import os
import django

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core_alp.settings')
django.setup()

from alp_app.models import Question, Topic

def pindahkan_data():
    questions = Question.objects.all()
    total = questions.count()
    print(f"Menghubungkan {total} soal ke tabel Topic baru...")
    
    count = 0
    for q in questions:
        if q.topic:
            # Mencoba get_or_create hanya dengan nama
            # Ini menghindari error jika field 'created_at' tidak ada di models.py
            topic_obj, created = Topic.objects.get_or_create(name=q.topic)
            
            # Hubungkan ke field baru topic_relation
            q.topic_relation = topic_obj
            q.save()
            count += 1
            
    print(f"Selesai! {count} soal sekarang sudah terhubung ke tabel Topic.")

if __name__ == "__main__":
    pindahkan_data()