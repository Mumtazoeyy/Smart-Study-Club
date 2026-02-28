# alp_app/models.py

from django.db import models
from django.contrib.auth.models import User
from django.conf import settings 
from django.urls import reverse 

# -----------------------------------------------
# 1. MODEL KURIKULUM (Kelas, Modul, Pelajaran)
# -----------------------------------------------
class Category(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nama Kategori")
    slug = models.SlugField(unique=True, null=True, blank=True)

    def __str__(self):
        return self.name    
    
class Course(models.Model):
    title = models.CharField(max_length=200, verbose_name="Judul Kelas")
    description = models.TextField(verbose_name="Deskripsi Singkat")
    course_code = models.CharField(max_length=10, unique=True, verbose_name="Kode Kursus")
    thumbnail = models.ImageField(upload_to='course_thumbnails/', null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='courses')
    level = models.CharField(max_length=20, choices=[('Dasar', 'Dasar'), ('Menengah', 'Menengah'), ('Lanjut', 'Lanjut')], default='Dasar')
    
    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('course_detail', args=[self.pk])


class Module(models.Model):
    course = models.ForeignKey(Course, related_name='modules', on_delete=models.CASCADE)
    title = models.CharField(max_length=200, verbose_name="Judul Bab/Modul")
    order = models.IntegerField(default=0, verbose_name="Urutan")

    class Meta:
        ordering = ['order']
        unique_together = ('course', 'order')

    def __str__(self):
        return f"{self.course.title}: Modul {self.order} - {self.title}"

class Lesson(models.Model):
    module = models.ForeignKey(Module, related_name='lessons', on_delete=models.CASCADE)
    title = models.CharField(max_length=255, verbose_name="Judul Pelajaran")
    is_quiz = models.BooleanField(default=False, help_text="Centang jika materi ini adalah Kuis")

    # --- FIELD MATERI & MEDIA ---
    # Cukup definisikan satu kali saja per nama field
    content = models.TextField(blank=True, null=True, verbose_name="Isi Materi / Deskripsi")
    image = models.ImageField(upload_to='lessons/images/', null=True, blank=True, verbose_name="Gambar Materi")
    video_url = models.URLField(
        blank=True, 
        null=True, 
        verbose_name="URL Video YouTube", 
        help_text="Contoh: https://www.youtube.com/embed/..."
    )

    # --- PENGATURAN KONTEN ---
    content_type = models.CharField(
        max_length=50, 
        choices=[('video', 'Video'), ('text', 'Teks/Artikel'), ('quiz', 'Kuis')], 
        default='text'
    )
    order = models.IntegerField(default=0, verbose_name="Urutan")

    class Meta:
        ordering = ['module', 'order']
        unique_together = ('module', 'order')

    def __str__(self):
        return f"{self.module.title}: {self.title} ({self.content_type})"

    def get_absolute_url(self):
        return reverse('lesson_content', args=[self.pk])
    
    def save(self, *args, **kwargs):
        # Jika tipe konten adalah 'quiz', otomatis True. Jika BUKAN, otomatis False.
        if self.content_type == 'quiz':
            self.is_quiz = True
        else:
            self.is_quiz = False
            
        super().save(*args, **kwargs)

# -----------------------------------------------
# 2. MODEL KUIS (Quiz dan Pertanyaan)
# -----------------------------------------------

class Quiz(models.Model):
    lesson = models.OneToOneField(
        'Lesson', 
        on_delete=models.CASCADE, 
        related_name='quiz', 
        limit_choices_to={'content_type': 'quiz'},
        verbose_name="Terkait dengan Pelajaran"
    )
    title = models.CharField(max_length=200, verbose_name="Judul Kuis")
    description = models.TextField(blank=True, verbose_name="Instruksi Kuis")
    is_quiz = models.BooleanField(default=True)

    def __str__(self):
        return f"Kuis: {self.title} ({self.lesson.title})"

class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions', verbose_name="Kuis")
    text = models.TextField(verbose_name="Teks Pertanyaan")
    
    # --- TAMBAHAN UNTUK REMEDIAL TERFOKUS ---
    topic = models.CharField(
        max_length=100, 
        default="Umum", 
        verbose_name="Topik/Pokok Materi",
        help_text="Contoh: Aljabar, Struktur Kalimat, Geometri, dll. Digunakan untuk saran belajar jika jawaban salah."
    )

    # Opsi Jawaban
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    
    CORRECT_CHOICES = [('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')]
    correct_answer = models.CharField(max_length=1, choices=CORRECT_CHOICES, verbose_name="Jawaban Benar")

    # --- TAMBAHAN UNTUK ADAPTIVE LEARNING (IRT MODEL RASCH) ---
    difficulty_level = models.FloatField(
        default=0.0, 
        verbose_name="Tingkat Kesulitan (Beta)",
        help_text="Gunakan nilai antara -3.0 (mudah) hingga +3.0 (sulit). 0.0 adalah tingkat kesulitan rata-rata."
    )

    def __str__(self):
        # Saya tambahkan self.topic di sini agar di halaman Admin Anda bisa langsung tahu topik soal tersebut
        return f"[{self.topic}] {self.quiz.title} - #{self.id} (β: {self.difficulty_level})"

# -----------------------------------------------
# 3. MODEL TRACKING (Enrollment, Session, Result)
# -----------------------------------------------

class Enrollment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, verbose_name="Kelas yang Diikuti")
    progress_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, verbose_name="Persentase Progres")
    last_accessed = models.DateTimeField(auto_now=True, verbose_name="Terakhir Diakses")
    rating = models.IntegerField(default=0) # Tambahkan ini
    
    class Meta:
        unique_together = ('user', 'course')
        ordering = ['-last_accessed']

    def __str__(self):
        return f"{self.user.username} - {self.course.title}"

class QuizResult(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey('Course', on_delete=models.CASCADE) 
    quiz = models.ForeignKey('Quiz', on_delete=models.CASCADE, null=True, blank=True)
    score = models.IntegerField(verbose_name="Skor Benar")
    total_questions = models.IntegerField(default=0, verbose_name="Total Pertanyaan")
    theta_result = models.FloatField(default=0.0) # Menyimpan nilai Theta saat kuis selesai
    date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Hasil Kuis {self.user.username} (Skor: {self.score}/{self.total_questions})"
    
class LessonCompletion(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'lesson')

class StudySession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    duration = models.IntegerField(help_text="Durasi dalam menit")
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Sesi Belajar {self.user.username} ({self.duration} menit)"
    
class Discussion(models.Model):
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='discussions')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    likes = models.ManyToManyField(User, related_name='discussion_likes', blank=True)
    # Field untuk fitur balas (Self-referencing)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at'] # Urutan waktu agar percakapan mengalir kebawah

    def __str__(self):
        return f"{self.user.username}: {self.content[:20]}"

    def get_all_replies(self):
        """
        Fungsi rekursif untuk mengambil semua balasan (anak, cucu, cicit, dst)
        dalam satu list flat agar bisa ditampilkan di HTML.
        """
        all_replies = []
        # Ambil balasan langsung dari pesan ini
        direct_replies = self.replies.all().order_by('created_at')
        
        for reply in direct_replies:
            # Masukkan balasan langsung ke daftar
            all_replies.append(reply)
            # REKURSI: Panggil fungsi ini lagi untuk mencari anak dari balasan ini
            all_replies.extend(reply.get_all_replies())
            
        return all_replies
    
    def get_total_replies_count(self):
        return len(self.get_all_replies())
    
class SupportReport(models.Model):
    # 1. Definisikan list pilihan status
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Proses', 'Proses'),
        ('Selesai', 'Selesai'),
    ]

    nama = models.CharField(max_length=100)
    email = models.EmailField()
    kategori = models.CharField(max_length=50)
    pesan = models.TextField()
    
    # 2. Tambahkan parameter 'choices' di sini agar muncul dropdown
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='Pending'
    ) 
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Support Report"
        verbose_name_plural = "Support Reports"

    def __str__(self):
        return f"{self.nama} - {self.kategori}"
    