from django.db import models
from django.contrib.auth.models import User
from alp_app.models import Module  # Tetap sambungkan ke Module utama kita

class MasterContent(models.Model):
    """
    Model ini adalah pusat penyimpanan materi. 
    Dibuat detail agar bisa menampung berbagai tipe konten.
    """
    TYPE_CHOICES = [
        ('VIDEO', 'Video & Teks'),
        ('ARTICLE', 'Artikel Murni'),
        ('QUIZ', 'Kuis Interaktif'),
        ('HYBRID', 'Mix (Video + Artikel + Kuis)'),
    ]

    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='contents')
    title = models.CharField(max_length=255, verbose_name="Judul Materi")
    slug = models.SlugField(unique=True, blank=True)
    
    # Meta Data
    content_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='VIDEO')
    order = models.PositiveIntegerField(default=0, verbose_name="Urutan")
    is_published = models.BooleanField(default=True)
    
    # Content Fields
    video_id = models.CharField(max_length=100, blank=True, help_text="ID Youtube saja (misal: dQw4w9WgXcQ)")
    body_text = models.TextField(blank=True, verbose_name="Isi Artikel (HTML)")
    thumbnail = models.ImageField(upload_to='manager/thumbs/', null=True, blank=True)
    
    # Fitur Power: JSON Data
    # Ini akan menampung hasil convert dari file Word (Soal, Pilihan, Jawaban)
    quiz_data = models.JSONField(null=True, blank=True, help_text="Format: {'questions': [...], 'timer': 60}")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order']
        verbose_name = "Master Materi"

    def __str__(self):
        return f"[{self.content_type}] {self.title}"

class WordImportLog(models.Model):
    """
    Model untuk mencatat histori import file Word. 
    Bermanfaat untuk audit kalau ada soal yang salah masuk.
    """
    file_name = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    upload_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default="Success")
    raw_json_result = models.JSONField(null=True)

    def __str__(self):
        return f"Import: {self.file_name} by {self.uploaded_by}"