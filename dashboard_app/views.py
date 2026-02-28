from django.shortcuts import render, redirect, get_object_or_404
from allauth.account.decorators import login_required
from profiles_app.models import Profile 
from alp_app.models import Enrollment, Course, StudySession, QuizResult 
from .models import StudyHistory  
from django.db.models import Avg, Sum 
from datetime import timedelta
import json
from django.utils import timezone
from django.urls import reverse
from django.contrib import messages

# dashboard_app/views.py

@login_required
def dashboard_view(request):
    user = request.user
    
    # --- 1. Akses Profile ---
    try:
        profile = user.user_profile
    except Profile.DoesNotExist:
        profile = Profile.objects.create(user=user)
    
    # --- 1.1 HITUNG PERSENTASE KEMAMPUAN (UNTUK HEADER DASHBOARD) ---
    # Rumus Normalisasi: Range Theta -3.0 s/d 3.0 (Total rentang 6)
    # Persentase = ((Skor_Sekarang - Skor_Minimal) / Rentang) * 100
    theta_val = float(profile.ability_score)
    ability_percentage = ((theta_val + 3) / 6) * 100
    # Pastikan tetap di range 0-100
    ability_percentage = max(min(ability_percentage, 100), 0)

    # --- 2. Query Enrollment ---
    enrolled_courses = Enrollment.objects.filter(user=user).select_related('course').order_by('-last_accessed')
    
    today = timezone.now().date()
    
    # --- 2.1. Waktu Belajar ---
    sejak_seminggu_lalu = today - timedelta(days=7)
    
    # Total menit keseluruhan
    total_study_minutes = StudySession.objects.filter(user=user).aggregate(Sum('duration'))['duration__sum'] or 0

    # Menit minggu ini
    current_week_duration_min = StudySession.objects.filter(
        user=user, 
        date__gte=sejak_seminggu_lalu
    ).aggregate(Sum('duration'))['duration__sum'] or 0
    
    indikator_waktu_str = f"Minggu ini: {int(current_week_duration_min)} menit"
    
    # --- 2.2. Nilai Rata-rata ---
    average_score = QuizResult.objects.filter(user=user).aggregate(Avg('score'))['score__avg']
    nilai_rata_rata_persen = round(average_score, 1) if average_score is not None else 'N/A'
    
    if average_score is not None and average_score < 70:
        indikator_nilai_str = "Rata-rata di bawah 70%. Fokus pada review!"
    elif average_score is not None:
        indikator_nilai_str = "Performa stabil dan bagus."
    else:
        indikator_nilai_str = "Belum ada kuis yang dikerjakan."

    # --- 2.3. Rekomendasi Cerdas ---
    rekomendasi_cerdas = None
    if enrolled_courses.exists():
        pilihan = enrolled_courses.filter(progress_percentage__lt=100).first()
        if pilihan:
            msg = "Mulai materi pertama!" if pilihan.progress_percentage == 0 else f"Lanjutkan progres ({int(pilihan.progress_percentage)}%)"
            rekomendasi_cerdas = {
                'title': f"{'Mulai' if pilihan.progress_percentage == 0 else 'Lanjutkan'}: {pilihan.course.title}",
                'link': reverse('course_detail', kwargs={'pk': pilihan.course.pk}), 
                'pesan': msg
            }
    
    # --- 2.4. Data List Kelas ---
    terakhir_diakses_msg = "Belum ada kelas yang diakses"
    terakhir_diakses = enrolled_courses.first()
    if terakhir_diakses:
        terakhir_diakses_msg = f"Terakhir: {terakhir_diakses.course.title}"

    kelas_aktif_data = [] 
    for enrollment in enrolled_courses:
        prog_int = int(enrollment.progress_percentage)
        kelas_aktif_data.append({
            'nama': enrollment.course.title,
            'progress': prog_int, 
            'link': reverse('course_detail', kwargs={'pk': enrollment.course.pk}), 
            'status_visual': 'Selesai' if prog_int >= 100 else 'Dimulai', 
            'status_color': 'text-green-600' if prog_int >= 100 else 'text-blue-600',
        })
        
    history_list = StudyHistory.objects.filter(user=user).order_by('-timestamp')[:5]
        
    # --- 2.5. DATA CHART.JS ---
    chart_labels_list = []
    chart_data_scores_list = []
    chart_data_minutes_list = []

    for i in range(6, -1, -1):
        target_date = today - timedelta(days=i)
        chart_labels_list.append(target_date.strftime('%d %b'))
        study_day = StudySession.objects.filter(user=user, date=target_date).aggregate(Sum('duration'))['duration__sum'] or 0
        chart_data_minutes_list.append(float(study_day))
        quiz_day = QuizResult.objects.filter(user=user, date=target_date).aggregate(Avg('score'))['score__avg'] or 0
        chart_data_scores_list.append(float(quiz_day))

    # --- 2.6. LOGIKA PANGKAT/STATUS PELAJAR (SINKRON DENGAN MODEL) ---
    # Kita panggil fungsi yang sudah kita buat di models.py agar hasilnya 100% sama dengan base.html
    pangkat_nama = profile.get_hierarchy_name
    
    # Menentukan style visual berdasarkan nama pangkat dari model
    pangkat_styles = {
        "Pelajar Setia": {"color": "text-purple-600 bg-purple-50", "ring": "ring-purple-400", "desc": "Sudah menghabiskan banyak waktu mengasah skill."},
        "Pelajar Teladan": {"color": "text-green-600 bg-green-50", "ring": "ring-green-400", "desc": "Sangat aktif dengan nilai yang memuaskan!"},
        "Pelajar Aktif": {"color": "text-blue-600 bg-blue-50", "ring": "ring-blue-400", "desc": "Terus tingkatkan progresmu!"},
        "Pelajar Pemula": {"color": "text-blue-500 bg-blue-50", "ring": "ring-blue-300", "desc": "Sedang membangun kebiasaan belajar."},
        "Pelajar Baru": {"color": "text-gray-500 bg-gray-100", "ring": "ring-gray-300", "desc": "Baru memulai perjalanan belajar."}
    }
    
    style = pangkat_styles.get(pangkat_nama, pangkat_styles["Pelajar Baru"])
    pangkat_color = style["color"]
    pangkat_ring = style["ring"]
    pangkat_deskripsi = style["desc"]

    # --- LOGIKA NEXT MILESTONE (MENGGUNAKAN DATA PROFILE) ---
    # Kita gunakan menit akumulatif dari database agar sinkron
    total_min = int(float(profile.total_waktu_belajar) * 60)
    next_milestone = {}

    if total_min == 0:
        target_min = 1
        next_milestone = {'target': target_min, 'text': 'Belajar 1 menit untuk jadi Pemula'}
        progress_to_next = 0
    elif total_min < 60:
        target_min = 60
        next_milestone = {'target': target_min, 'text': f'{60 - total_min} menit lagi untuk jadi Pelajar Aktif'}
        progress_to_next = (total_min / 60) * 100
    elif total_min < 300:
        target_min = 300
        next_milestone = {'target': target_min, 'text': f'{300 - total_min} menit lagi untuk jadi Pelajar Setia'}
        progress_to_next = (total_min / 300) * 100
    else:
        next_milestone = {'target': total_min, 'text': 'Kamu telah mencapai status tertinggi!'}
        progress_to_next = 100
        
    # --- LOGIKA MODAL THETA (KEMAMPUAN) ---
    theta_val = float(profile.ability_score)
    
    if theta_val < -1.0:
        theta_status = "Beginner"
        theta_desc = "Kamu sedang membangun fondasi dasar. Teruslah berlatih!"
    elif -1.0 <= theta_val < 1.0:
        theta_status = "Intermediate"
        theta_desc = "Kemampuanmu sudah stabil. Siap untuk tantangan lebih berat!"
    else:
        theta_status = "Expert"
        theta_desc = "Luar biasa! Kamu menguasai materi dengan sangat baik."

    context = {
        'profile': profile,
        'user': user,
        'ability_percentage': ability_percentage, # VARIABEL PENTING UNTUK HEADER
        'total_waktu_belajar_menit': int(total_study_minutes), 
        'nilai_rata_rata': nilai_rata_rata_persen,
        'jumlah_kelas_aktif': enrolled_courses.count(),
        'indikator_waktu': indikator_waktu_str, 
        'indikator_kelas': terakhir_diakses_msg,
        'indikator_nilai': indikator_nilai_str,
        'rekomendasi': rekomendasi_cerdas,
        'kelas_aktif': kelas_aktif_data, 
        'history_list': history_list,
        'chart_labels': json.dumps(chart_labels_list),
        'chart_data_scores': json.dumps(chart_data_scores_list),
        'chart_data_hours': json.dumps(chart_data_minutes_list),
        'pangkat': {
            'nama': pangkat_nama,
            'color_class': pangkat_color,
            'ring_class': pangkat_ring,
            'deskripsi': pangkat_deskripsi
        },
        'next_milestone': next_milestone,
        'progress_to_next': min(progress_to_next, 100),
    }
    context.update({
        'theta_info': {
            'status': theta_status,
            'desc': theta_desc,
        }
    })
    
    return render(request, 'dashboard.html', context)

# --- Fungsi lainnya tetap ---
@login_required
def delete_history_item(request, pk):
    try:
        history = StudyHistory.objects.get(pk=pk, user=request.user)
        history.delete()
        messages.success(request, "Riwayat berhasil dihapus.")
    except StudyHistory.DoesNotExist:
        messages.error(request, "Data tidak ditemukan.")
    
    # KODE KRUSIALNYA DI SINI:
    # redirect balik ke halaman asal (History), bukan ke Dashboard
    return redirect(request.META.get('HTTP_REFERER', 'history_full_view'))

@login_required
def clear_all_history(request):
    StudyHistory.objects.filter(user=request.user).delete()
    messages.success(request, "Semua riwayat telah dibersihkan.")
    return redirect('dashboard')

from django.core.paginator import Paginator
# Pastikan import ini merujuk ke StudyHistory, bukan History
from .models import StudyHistory 

@login_required
def history_full_view(request):
    # Ganti 'History' menjadi 'StudyHistory'
    history_qs = StudyHistory.objects.filter(user=request.user).order_by('-timestamp')
    
    # Sistem Halaman (Pagination) - 10 data per halaman
    paginator = Paginator(history_qs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'history.html', {'all_history': page_obj})

# dashboard_app/views.py
from django.shortcuts import render
from django.contrib.auth.models import User
from django.db.models import Avg
from alp_app.models import QuizResult # Pastikan path import sesuai dengan folder app Anda

def leaderboard_view(request):
    # .exclude(user__is_staff=True) akan membuang semua akun admin/staff dari daftar
    # .exclude(user__is_superuser=True) untuk memastikan superuser juga hilang
    leaderboard_data = Profile.objects.select_related('user')\
        .exclude(user__is_staff=True)\
        .exclude(user__is_superuser=True)\
        .order_by('-ability_score')[:10]

    return render(request, 'leaderboard.html', {
        'leaderboard_data': leaderboard_data
    })