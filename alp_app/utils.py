# alp_app/utils.py

import datetime
from decimal import Decimal
from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404
from profiles_app.models import Profile 
from .models import Lesson, LessonCompletion, Enrollment, Module

def recalculate_enrollment_progress(enrollment):
    """Menghitung ulang persentase progres enrollment."""
    course = enrollment.course
    
    # 1. Hitung total pelajaran dalam Course
    total_lessons_in_course = Lesson.objects.filter(
        module__course=course
    ).count()

    if total_lessons_in_course == 0:
        enrollment.progress_percentage = Decimal('0.00') 
        enrollment.save()
        return

    # 2. Hitung pelajaran yang sudah diselesaikan oleh pengguna di kursus ini
    lessons_completed_count = LessonCompletion.objects.filter(
        user=enrollment.user,
        lesson__module__course=course
    ).count()

    # 3. Hitung Persentase
    progress_float = (lessons_completed_count / total_lessons_in_course) * 100
    
    # Konversi float ke Decimal dan bulatkan ke 2 angka di belakang koma
    progress_decimal = Decimal(str(progress_float))
    
    # 4. Simpan ke Enrollment
    enrollment.progress_percentage = round(progress_decimal, 2)
    enrollment.save()


def mark_lesson_complete_logic(user, lesson_id):
    """
    Menandai pelajaran sebagai selesai, menambah waktu belajar di profil,
    dan memperbarui persentase progres kursus.
    """
    try:
        lesson = get_object_or_404(Lesson, pk=lesson_id)
        
        # 1. Buat catatan penyelesaian (LessonCompletion)
        # Menggunakan timezone-aware now jika memungkinkan, atau datetime.datetime.now()
        completion, created = LessonCompletion.objects.get_or_create(
            user=user,
            lesson=lesson,
            defaults={'completed_at': datetime.datetime.now()}
        )
        
        # HANYA LANJUTKAN LOGIKA UPDATE JIKA BARU PERTAMA KALI DISELESAIKAN
        if created:
            # 2. Perbarui Statistik Global Pengguna (Total Waktu Belajar)
            try:
                # Menggunakan filter/first untuk menghindari error jika profile belum ada
                user_profile = Profile.objects.filter(user=user).first()
                if user_profile:
                    # Asumsi: Setiap pelajaran yang selesai menambah 0.17 jam (~10 menit)
                    waktu_belajar = Decimal('0.17') 
                    user_profile.total_waktu_belajar += waktu_belajar 
                    user_profile.save()
            except Exception as profile_err:
                print(f"Gagal update profil: {profile_err}")
                
            # 3. Perbarui Progres Enrollment
            try:
                enrollment = Enrollment.objects.get(
                    user=user, 
                    course=lesson.module.course
                )
                recalculate_enrollment_progress(enrollment)
            except Enrollment.DoesNotExist:
                pass

            return True, "Pelajaran berhasil diselesaikan!"
        else:
            return True, "Pelajaran sudah diselesaikan sebelumnya."
            
    except Exception as e:
        return False, f"Terjadi kesalahan: {str(e)}"
    
# Di alp_app/utils.py, tambahkan logika keputusan
def get_adaptive_recommendation(user):
    theta = user.user_profile.ability_score
    if theta < -1.0:
        return "Jalur Remedial: Penguatan konsep dasar."
    elif theta > 1.5:
        return "Jalur Akselerasi: Materi pengayaan."
    else:
        return "Jalur Standar: Lanjut ke modul berikutnya."