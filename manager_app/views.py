import re
import csv
from docx import Document

from django.shortcuts import render
from django.db import transaction
from django.db.models import Avg, Count
from django.contrib import messages
from django.contrib.auth.models import User

from alp_app.models import (
    Course, Module, Lesson, Enrollment, 
    Quiz, Question, SupportReport
)

def admin_dashboard(request):
    # 1. Statistik Ringkas
    total_siswa = User.objects.count()
    total_materi_aktif = Course.objects.count()
    
    # 2. Hitung Efektivitas (Persentase dari Rating)
    avg_rating = Enrollment.objects.aggregate(Avg('rating'))['rating__avg'] or 0
    efektivitas_persen = int((avg_rating / 5) * 100) if avg_rating > 0 else 0
    
    # 3. Laporan Masalah (DIUBAH: Mengambil data dari SupportReport)
    # Menghitung semua laporan support yang masuk
    total_masalah = SupportReport.objects.exclude(status='Selesai').count()

    # 4. Tabel Materi Terpopuler
    materi_populer = Course.objects.annotate(
        total_user=Count('enrollment', distinct=True),
        rating_rata=Avg('enrollment__rating'),
        jml_modul=Count('modules', distinct=True),
        jml_lesson=Count('modules__lessons', distinct=True)
    ).order_by('-total_user')[:5]

    context = {
        'total_siswa': total_siswa,
        'total_materi_aktif': total_materi_aktif,
        'efektivitas': efektivitas_persen,
        'rating_global': round(avg_rating, 1),
        'total_masalah': total_masalah, # Sekarang ini isinya jumlah SupportReport
        'materi_populer': materi_populer,
    }
    return render(request, 'manager/dashboard.html', context)

def import_materi_view(request):
    courses = Course.objects.all()

    if request.method == 'POST':
        file = request.FILES.get('file_materi')
        course_id = request.POST.get('course_id')
        selected_module_id = request.POST.get('module_select')

        if not file or not course_id:
            messages.error(request, "Pilih Course dan File .docx!")
        else:
            try:
                with transaction.atomic():
                    selected_course = Course.objects.get(id=course_id)
                    doc = Document(file)
                    
                    current_module = None
                    if selected_module_id and selected_module_id != 'none':
                        current_module = Module.objects.get(id=selected_module_id)

                    current_lesson = None
                    current_quiz_obj = None # Simpan objek kuis aktif di sini

                    for p in doc.paragraphs:
                        text = p.text.strip()
                        if not text: continue 

                        # --- DETEKSI MODULE ---
                        if text.upper().startswith('[MODULE]'):
                            if selected_module_id == 'none':
                                module_title = text[8:].strip()
                                m_order = Module.objects.filter(course=selected_course).count() + 1
                                current_module = Module.objects.create(course=selected_course, title=module_title, order=m_order)
                            continue

                        # --- DETEKSI LESSON ---
                        elif text.upper().startswith('[LESSON]'):
                            if not current_module: continue
                            lesson_title = text[8:].strip()
                            l_order = Lesson.objects.filter(module=current_module).count() + 1
                            current_lesson = Lesson.objects.create(
                                module=current_module, title=lesson_title, content="",
                                content_type='text', order=l_order, is_quiz=False
                            )
                            current_quiz_obj = None # Matikan mode kuis
                            continue

                        # --- DETEKSI QUIZ ---
                        elif text.upper().startswith('[QUIZ]'):
                            if not current_module: continue
                            quiz_title = text[6:].strip()
                            l_order = Lesson.objects.filter(module=current_module).count() + 1
                            current_lesson = Lesson.objects.create(
                                module=current_module, title=quiz_title, content="Kuis Otomatis",
                                content_type='quiz', order=l_order, is_quiz=True
                            )
                            # Simpan ke variabel agar Question bisa merujuk ke sini
                            current_quiz_obj = Quiz.objects.create(lesson=current_lesson, title=quiz_title, is_quiz=True)
                            continue

                        # --- DETEKSI PERTANYAAN (Khusus dalam mode Quiz) ---
                        elif current_quiz_obj and "JAWABAN:" in text.upper():
                            # Regex untuk memecah Pertanyaan, Opsi A, B, C, D, dan Jawaban
                            pattern = r'(?:Pertanyaan\s*\d+:\s*)?(.*?)\s*A\.\s*(.*?)\s*B\.\s*(.*?)\s*C\.\s*(.*?)\s*D\.\s*(.*?)\s*Jawaban:\s*([A-D])'
                            match = re.search(pattern, text, re.IGNORECASE)
                            
                            if match:
                                Question.objects.create(
                                    quiz=current_quiz_obj,
                                    text=match.group(1).strip(),
                                    option_a=match.group(2).strip(),
                                    option_b=match.group(3).strip(),
                                    option_c=match.group(4).strip(),
                                    option_d=match.group(5).strip(),
                                    correct_answer=match.group(6).upper(),
                                    topic="Umum"
                                )
                            continue

                        # --- ISI KONTEN LESSON ---
                        else:
                            if current_lesson and not current_lesson.is_quiz:
                                separator = "\n\n" if current_lesson.content else ""
                                current_lesson.content += separator + text
                                current_lesson.save()

                    messages.success(request, f"Sukses mengimpor materi dan kuis!")

            except Exception as e:
                messages.error(request, f"Gagal Import: {str(e)}")

    return render(request, 'manager/import_materi.html', {'courses': courses})