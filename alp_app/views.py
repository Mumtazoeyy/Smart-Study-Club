# alp_app/views.py

from django.shortcuts import render, redirect 
from django.contrib.auth import login 
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm 
from django.contrib import messages 
from django.http import JsonResponse
from django.db import transaction
from django.db.models import Avg, Count # Import fungsi agregasi

# --- IMPORT MODEL YANG BENAR ---
# Import dari App alp_app
from .models import Category, Enrollment, Course, Lesson, Quiz 
# Import dari App profiles yang baru
from profiles_app.models import Profile 
from allauth.account.decorators import login_required

# alp_app/views.py
from django.db.models import Count
from django.contrib.auth.models import User
from .models import Course, Enrollment, Discussion

# alp_app/views.py

def custom_404(request, exception):
    return render(request, '404.html', status=404)

def custom_500(request):
    return render(request, '500.html', status=500)

def trigger_error(request):
    # Ini akan memaksa server error 500 karena pembagian nol
    return 1 / 0

def home_master(request):
    """Merender halaman Home Master dengan data statistik riil."""
    
    total_peserta = Enrollment.objects.count()
    total_kursus = Course.objects.count()
    total_ulasan = Enrollment.objects.filter(rating__gt=0).count()
    total_diskusi = Discussion.objects.count()
    total_categories = Category.objects.count()
    total_lessons = Lesson.objects.count()
    total_quizzes = Quiz.objects.count()

    # 5. Kursus Terpopuler
    popular_courses = Course.objects.annotate(
        num_students=Count('enrollment') 
    ).order_by('-num_students')[:4]

    # Ambil 3 pendaftaran terbaru yang memberi rating 4 atau 5
    real_testimonials = Enrollment.objects.filter(rating__gte=4).order_by('-id')[:3]

    context = {
        'total_students': total_peserta,
        'total_courses': total_kursus,
        'courses': popular_courses,
        'review_count': total_ulasan,
        'total_discussions': total_diskusi, # Kirim variabel ini ke template
        'testimonials': real_testimonials, # Kirim ke template
        'total_categories': total_categories,
        'total_lessons': total_lessons,
        'total_quizzes': total_quizzes,
    }
    
    return render(request, 'home_master.html', context)

def home1(request):
    """Merender Homepage Versi 1 (home1.html)."""
    return render(request, 'home1.html') 

def hom2(request):
    """Merender Homepage Versi 2 (home2.html)."""
    return render(request, 'home2.html') 

def home3(request):
    # Diurutkan dari yang siswanya paling banyak ke paling sedikit
    courses = Course.objects.all().order_by('-num_students')[:4]
    return render(request, 'home3.html', {'courses': courses})

def home4(request):
    """Merender Homepage Versi 4 (home4.html)."""
    return render(request, 'home4.html') 

def home5(request):
    """Merender Homepage Versi 5 (home5.html)."""
    return render(request, 'home5.html')

def home6(request):
    """Merender Homepage Versi 6 (home6.html)."""
    return render(request, 'home6.html')

# --- FUNGSI 1: KHUSUS FEEDBACK/RATING ---
@login_required
def feedback_view(request):
    if request.method == 'POST':
        course_id = request.POST.get('course')
        rating_value = request.POST.get('rating')
        content = request.POST.get('content')

        if course_id and rating_value and content:
            try:
                course = Course.objects.get(id=course_id)
                enrollment, _ = Enrollment.objects.get_or_create(user=request.user, course=course)
                enrollment.rating = int(rating_value)
                enrollment.save()
                
                # Simpan juga ke Discussion sebagai record ulasan
                Discussion.objects.create(course=course, user=request.user, content=content)
                
                messages.success(request, "Ulasan berhasil dikirim!")
                return redirect('feedback_view')
            except Exception as e:
                messages.error(request, f"Gagal: {str(e)}")

    all_courses = Course.objects.all().order_by('title')
    # Filter 3 ulasan terbaru milik sendiri
    my_feedbacks = Enrollment.objects.filter(user=request.user, rating__gt=0).order_by('-last_accessed')[:3]
    
    return render(request, 'feedback.html', {
        'courses': all_courses, 
        'feedbacks': my_feedbacks
    })

# --- FUNGSI 2: KHUSUS FORUM DISKUSI (YANG SEMPAT HILANG) ---
@login_required
def discussion_view(request):
    # 1. Ambil filter dari parameter URL (?filter=id)
    course_filter = request.GET.get('filter')
    
    # 2. Ambil semua materi untuk bar filter
    courses = Course.objects.all()
    
    # 3. Ambil diskusi utama (yang bukan balasan / parent__isnull=True)
    if course_filter and course_filter != 'all':
        discussions = Discussion.objects.filter(
            course_id=course_filter, 
            parent__isnull=True
        ).order_by('-created_at')
        # Hitung total balasan khusus untuk course yang difilter
        total_replies = Discussion.objects.filter(course_id=course_filter, parent__isnull=False).count()
    else:
        discussions = Discussion.objects.filter(
            parent__isnull=True
        ).order_by('-created_at')
        # Hitung total seluruh balasan di database
        total_replies = Discussion.objects.filter(parent__isnull=False).count()
    
    context = {
        'courses': courses,
        'comments': discussions, 
        'comments_count': discussions.count(), # Tambahkan ini untuk angka "Total Komentar"
        'total_replies': total_replies,       # Tambahkan ini untuk angka "Total Balasan"
    }
    return render(request, 'discussion.html', context)

@login_required
def like_comment(request, comment_id):
    if request.method == "POST":
        comment = get_object_or_404(Discussion, id=comment_id)
        
        if comment.likes.filter(id=request.user.id).exists():
            comment.likes.remove(request.user)
            liked = False
        else:
            comment.likes.add(request.user)
            liked = True
        
        # Logika deteksi AJAX yang lebih kuat
        is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or \
                  request.content_type == 'application/json'

        if is_ajax:
            return JsonResponse({
                'liked': liked,
                'total_likes': comment.likes.count()
            })
            
    # Fallback jika bukan AJAX (misal JavaScript di browser dimatikan)
    return redirect(request.META.get('HTTP_REFERER', 'discussion_view'))

@login_required
def reply_comment(request, comment_id):
    if request.method == "POST":
        parent_comment = get_object_or_404(Discussion, id=comment_id)
        content = request.POST.get('content')
        
        if content:
            # Simpan balasan ke model Discussion dengan parent yang sesuai
            Discussion.objects.create(
                user=request.user,
                course=parent_comment.course,
                parent=parent_comment,
                content=content
            )
            
    return redirect(request.META.get('HTTP_REFERER', 'discussion_view'))

@login_required
def post_comment(request):
    if request.method == "POST":
        course_id = request.POST.get('course_id')
        content = request.POST.get('content')
        
        if course_id and content:
            try:
                course = get_object_or_404(Course, id=course_id)
                # Membuat thread utama (parent adalah None)
                Discussion.objects.create(
                    user=request.user,
                    course=course,
                    content=content,
                    parent=None  
                )
                messages.success(request, "Diskusi baru berhasil dibuat!")
            except Exception as e:
                messages.error(request, f"Gagal membuat diskusi: {e}")
                
    return redirect('discussion_view')

# VIEW KELAS: Pastikan nama fungsi persis 'kelas_view'
def kelas_view(request):
    """Menampilkan halaman katalog kelas."""
    context = {
        'judul_halaman': 'Katalog Kelas',
    }
    return render(request, 'kelas.html', context)

from django.shortcuts import render

def support_view(request):
    return render(request, 'support.html')

def about_view(request):
    return render(request, 'about.html')

# --- Login View ---
def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':  # AJAX request
            form = AuthenticationForm(request, data=request.POST)
            if form.is_valid():
                user = form.get_user()
                login(request, user)
                return JsonResponse({'success': True, 'redirect_url': '/'})
            else:
                errors = form.non_field_errors()
                error_message = errors[0] if errors else "Username atau password salah."
                return JsonResponse({'success': False, 'message': error_message})
        else:
            # Normal form submit (fallback)
            form = AuthenticationForm(request, data=request.POST)
            if form.is_valid():
                user = form.get_user()
                login(request, user)
                return redirect('home')
            else:
                messages.error(request, "Username atau password salah.")
    else:
        form = AuthenticationForm()

    return render(request, 'signin.html', {'form': form}) # Ini akan merender signin.html

# alp_app/views.py

# alp_app/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.http import JsonResponse
from django.contrib import messages
from .forms import ExtendedSignupForm  # Form yang mewarisi SignupForm Allauth

# Import model
from .models import Enrollment, Course
from profiles_app.models import Profile 

# alp_app/views.py

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        # Gunakan form kustom Anda
        form = ExtendedSignupForm(request.POST) 
        
        if form.is_valid():
            # KUNCI UTAMA: Gunakan form.save(request) agar logika Allauth jalan
            # Ini akan menyimpan Username, Password, dan menjalankan def save di forms.py
            user = form.save(request)
            
            # Login otomatis dengan backend Allauth agar sinkron
            login(request, user, backend='allauth.account.auth_backends.AuthenticationBackend')
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'redirect_url': '/'})
            
            return redirect('home')
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors.get_json_data()})
            
            messages.error(request, "Terjadi kesalahan pada form pendaftaran.")
    else:
        form = ExtendedSignupForm()

    return render(request, 'signup.html', {'form': form})

# alp_app/views.py

from django.shortcuts import render
from django.views.generic import ListView, DetailView
from django.db.models import Q
# Import semua Model yang digunakan
from .models import Course, Enrollment, Module, Lesson

# ----------------------------------------------------
# 1. VIEW UNTUK DAFTAR KELAS (course_list)
# ----------------------------------------------------

# alp_app/views.py
from .models import Course, Category # Tambahkan Category

from django.views.generic import ListView
from django.db.models import Q
from .models import Course, Category  # Pastikan Category diimport

class ClassListView(ListView):
    model = Course 
    template_name = 'class.html' 
    context_object_name = 'class_list' 
    paginate_by = 12 

    def get_queryset(self):
        # Mengambil queryset dasar dan mengurutkannya berdasarkan judul
        queryset = super().get_queryset().order_by('title') 
        
        # Mengambil parameter filter dari URL
        search_query = self.request.GET.get('q')
        category_id = self.request.GET.get('category')
        level_filter = self.request.GET.get('level')
        
        # Logika Pencarian: mencari kata kunci di judul atau deskripsi
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) | Q(description__icontains=search_query)
            ).distinct()
        
        # Logika Filter Kategori: menyaring berdasarkan ID kategori
        if category_id:
            queryset = queryset.filter(category_id=category_id)
            
        # Logika Filter Level: menyaring berdasarkan tingkat kesulitan
        if level_filter:
            queryset = queryset.filter(level=level_filter)
            
        return queryset

    def get_context_data(self, **kwargs):
        """Menambahkan daftar kategori ke context agar bisa ditampilkan di dropdown filter."""
        context = super().get_context_data(**kwargs)
        # Mengambil semua objek kategori dari database
        context['categories'] = Category.objects.all()

        return context
    
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import F, Func 
from .models import Quiz, Question, QuizResult

# IMPORT LOGIKA CORE
from core_alp.irt_engine import update_theta_mle 
from dashboard_app.models import StudyHistory 
from .utils import mark_lesson_complete_logic 

@login_required
def quiz_detail(request, quiz_pk):
    quiz = get_object_or_404(Quiz, pk=quiz_pk)
    lesson = quiz.lesson 
    user_profile = request.user.user_profile
    
    # --- 1. FITUR RESET (COBA LAGI) ---
    is_reset = request.GET.get('reset')
    if is_reset:
        # Hapus sesi kuis
        for key in ['quiz_step', 'correct_answers', 'answered_ids', 'wrong_topics']:
            request.session.pop(key, None)
        request.session.modified = True
        
        # Hapus hasil lama agar tidak kena "Bypass Riwayat" di bawah
        QuizResult.objects.filter(user=request.user, quiz=quiz).delete()
        
        # Redirect ke URL kuis yang bersih
        return redirect('quiz_detail', quiz_pk=quiz.pk)

    # --- 2. FITUR LANGSUNG KE SCORE (CEK RIWAYAT) ---
    # Sekarang ini hanya akan jalan kalau QuizResult ADA (berarti tidak sedang di-reset)
    existing_result = QuizResult.objects.filter(user=request.user, quiz=quiz).last()
    if existing_result:
        materi_awal = Lesson.objects.filter(module=lesson.module).exclude(content_type='quiz').order_by('order').first()
        next_lesson = Lesson.objects.filter(module=lesson.module, order__gt=lesson.order).order_by('order').first()
        
        # Logika modul berikutnya jika lesson habis
        if not next_lesson:
            next_mod = Module.objects.filter(course=lesson.module.course, order__gt=lesson.module.order).order_by('order').first()
            if next_mod:
                next_lesson = Lesson.objects.filter(module=next_mod).order_by('order').first()

        return render(request, 'quiz/quiz_score.html', {
            'score': existing_result.score,
            'total': existing_result.total_questions,
            'percentage': (existing_result.score / existing_result.total_questions * 100) if existing_result.total_questions > 0 else 0,
            'is_passed': True, 
            'theta_akhir': existing_result.theta_result,
            'quiz': quiz,
            'wrong_topics': [], 
            'materi_awal': materi_awal or quiz.lesson,
            'next_lesson': next_lesson,
        })
    
    # --- 3. LOGIKA KUIS BERJALAN ---
    total_soal_db = Question.objects.filter(quiz=quiz).count()
    MAX_QUESTIONS = min(total_soal_db, 10)
    MIN_PASS_SCORE = 70 

    def get_review_lesson():
        materi = Lesson.objects.filter(
            module=quiz.lesson.module
        ).exclude(content_type='quiz').order_by('order').first()
        return materi or quiz.lesson

    # Cari lesson berikutnya (untuk tombol Lanjut)
    next_lesson = Lesson.objects.filter(
        module=lesson.module,
        order__gt=lesson.order
    ).order_by('order').first()

    if not next_lesson:
        next_module = Module.objects.filter(
            course=lesson.module.course,
            order__gt=lesson.module.order
        ).order_by('order').first()
        if next_module:
            next_lesson = Lesson.objects.filter(module=next_module).order_by('order').first()

    # Inisialisasi Sesi jika baru mulai
    if 'quiz_step' not in request.session:
        request.session['quiz_step'] = 1
        request.session['correct_answers'] = 0
        request.session['answered_ids'] = [] 
        request.session['wrong_topics'] = []
        request.session.modified = True

    if request.method == 'POST':
        question_id = request.POST.get('question_id')
        user_answer = request.POST.get('answer')
        
        if not question_id:
            return redirect('quiz_detail', quiz_pk=quiz.pk)

        question = get_object_or_404(Question, id=question_id)
        answered_ids = request.session.get('answered_ids', [])
        
        if int(question_id) not in answered_ids:
            answered_ids.append(int(question_id))
            request.session['answered_ids'] = answered_ids
        
            is_correct = (user_answer == question.correct_answer)
            if is_correct:
                request.session['correct_answers'] += 1
            else:
                wrong_topics = request.session.get('wrong_topics', [])
                if question.topic and question.topic not in wrong_topics:
                    wrong_topics.append(question.topic)
                    request.session['wrong_topics'] = wrong_topics
            
            new_theta = update_theta_mle(
                current_theta=user_profile.ability_score,
                question_beta=question.difficulty_level,
                is_correct=is_correct
            )
            user_profile.ability_score = new_theta
            user_profile.save()
            
            request.session['quiz_step'] = len(answered_ids) + 1
            request.session.modified = True

        # CEK APAKAH KUIS SELESAI
        if len(answered_ids) >= MAX_QUESTIONS:
            user_score = request.session.get('correct_answers', 0)
            final_wrong_topics = request.session.get('wrong_topics', [])
            score_percentage = (user_score / MAX_QUESTIONS) * 100 if MAX_QUESTIONS > 0 else 0
            is_passed = score_percentage >= MIN_PASS_SCORE
            
            # Gunakan update_or_create agar jika diulang, data diperbarui bukan menumpuk
            QuizResult.objects.update_or_create(
                user=request.user, quiz=quiz,
                defaults={
                    'course': lesson.module.course,
                    'score': user_score,
                    'total_questions': MAX_QUESTIONS,
                    'theta_result': user_profile.ability_score
                }
            )

            for key in ['quiz_step', 'correct_answers', 'answered_ids', 'wrong_topics']:
                request.session.pop(key, None)
            request.session.modified = True

            if is_passed:
                mark_lesson_complete_logic(request.user, lesson.pk)
            
            return render(request, 'quiz/quiz_score.html', {
                'score': user_score,
                'total': MAX_QUESTIONS,
                'percentage': score_percentage,
                'is_passed': is_passed,
                'theta_akhir': user_profile.ability_score,
                'quiz': quiz,
                'wrong_topics': final_wrong_topics,
                'materi_awal': get_review_lesson(),
                'next_lesson': next_lesson,
            })

    # SELEKSI SOAL ADAPTIF
    answered_ids = request.session.get('answered_ids', [])
    next_question = Question.objects.filter(quiz=quiz).exclude(id__in=answered_ids).annotate(
        selisih=Func(F('difficulty_level') - user_profile.ability_score, function='ABS')
    ).order_by('selisih').first()

    if not next_question:
        user_score = request.session.get('correct_answers', 0)
        actual_total = len(answered_ids)
        score_percentage = (user_score / actual_total) * 100 if actual_total > 0 else 0
        
        for key in ['quiz_step', 'correct_answers', 'answered_ids', 'wrong_topics']:
            request.session.pop(key, None)
        request.session.modified = True

        return render(request, 'quiz/quiz_score.html', {
            'score': user_score,
            'total': actual_total,
            'percentage': score_percentage,
            'is_passed': score_percentage >= MIN_PASS_SCORE,
            'theta_akhir': user_profile.ability_score,
            'quiz': quiz,
            'wrong_topics': [],
            'materi_awal': get_review_lesson(),
            'next_lesson': next_lesson,
        })

    context = {
        'quiz': quiz,
        'question': next_question, 
        'step': len(answered_ids) + 1,
        'total_questions': MAX_QUESTIONS,
        'question_range': list(range(1, MAX_QUESTIONS + 1)),
        'total_steps': MAX_QUESTIONS,
    }
    return render(request, 'quiz/quiz_detail.html', context)

@login_required
def lesson_content(request, lesson_pk):
    # Ambil objek Lesson, atau tampilkan 404 jika tidak ditemukan
    lesson = get_object_or_404(Lesson, pk=lesson_pk)
    
    # Cek apakah user terdaftar di course ini (Prasyarat keamanan)
    course = lesson.module.course
    try:
        enrollment = Enrollment.objects.get(user=request.user, course=course)
    except Enrollment.DoesNotExist:
        # Jika belum terdaftar, redirect ke halaman detail kelas
        return redirect('course_detail', pk=course.pk)

    # Jika tipe konten adalah 'quiz', langsung redirect ke view kuis
    if lesson.content_type == 'quiz' and hasattr(lesson, 'quiz'):
        return redirect('quiz_detail', quiz_pk=lesson.quiz.pk)

    # =========================================================
    # 🌟 LOGIKA HISTORY (MENNCATAT RIWAYAT BELAJAR)
    # =========================================================
    # Ambil riwayat terakhir user untuk menghindari duplikasi saat refresh
    last_history = StudyHistory.objects.filter(user=request.user).first()
    activity_msg = f"Mempelajari: {lesson.title}"
    
    if not last_history or last_history.activity_name != activity_msg:
        StudyHistory.objects.create(
            user=request.user,
            activity_name=activity_msg,
            link=request.path  # Menyimpan URL materi saat ini
        )
    # =========================================================

    context = {
        'lesson': lesson,
        'module': lesson.module,
        'course': course,
    }
    
    # SEMUA tipe materi (teks maupun video) sekarang menggunakan SATU template gabungan ini
    return render(request, 'lesson/lesson_detail.html', context)

# alp_app/views.py (Tambahkan kode ini)
from django.contrib import messages
from .models import Course, Enrollment # Pastikan Enrollment sudah diimport

@login_required
def course_enroll(request, course_pk):
    # Ambil objek Course
    course = get_object_or_404(Course, pk=course_pk)

    # 1. Cek apakah user sudah terdaftar
    is_enrolled = Enrollment.objects.filter(user=request.user, course=course).exists()

    if is_enrolled:
        # Jika sudah terdaftar, beri pesan dan kembali ke detail kelas
        messages.info(request, f"Anda sudah terdaftar di kelas '{course.title}'.")
    else:
        # 2. Jika belum, buat objek Enrollment baru
        try:
            Enrollment.objects.create(user=request.user, course=course)
            
            # Beri pesan sukses
            messages.success(request, f"🎉 Selamat! Anda berhasil mendaftar di kelas '{course.title}'.")
            
        except Exception as e:
            # Penanganan error jika ada masalah database
            messages.error(request, f"Gagal mendaftar. Terjadi kesalahan: {e}")
            
    # 3. Redirect kembali ke halaman detail kelas
    return redirect('course_detail', pk=course.pk)

# alp_app/views.py

# alp_app/views.py

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.http import JsonResponse
from .utils import mark_lesson_complete_logic 

# ... (Pastikan Anda sudah mengimpor model lain yang dibutuhkan di sini)

@login_required
def mark_lesson_complete(request, lesson_id):
    # Hanya izinkan permintaan POST
    if request.method == 'POST':
        user = request.user
        
        success, message = mark_lesson_complete_logic(user, lesson_id)
        
        # Jika dipanggil via AJAX, kembalikan JSON
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            if success:
                return JsonResponse({'status': 'success', 'message': message})
            else:
                return JsonResponse({'status': 'error', 'message': message}, status=400)
        
        # Jika bukan AJAX, arahkan pengguna kembali
        if success:
            # Arahkan ke halaman detail pelajaran atau ke modul berikutnya
            return redirect('lesson_detail', pk=lesson_id) # Ganti dengan nama URL yang benar
        else:
            return redirect('dashboard') # Arahkan ke tempat aman jika gagal
            
    return JsonResponse({'status': 'error', 'message': 'Hanya menerima POST request.'}, status=405)

import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import StudySession
from django.utils import timezone
import math

@csrf_exempt
def update_study_time(request):
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return JsonResponse({'status': 'unauthorized'}, status=401)
            
        try:
            data = json.loads(request.body)
            durasi_detik = int(data.get('duration', 0))
            
            if durasi_detik < 10: # Abaikan jika kurang dari 10 detik
                return JsonResponse({'status': 'ignored'})

            # Konversi ke menit. Karena model kamu IntegerField, 
            # kita gunakan math.ceil (pembulatan ke atas) supaya 30 detik tetap jadi 1 menit.
            durasi_menit = math.ceil(durasi_detik / 60)

            # Simpan sesi baru
            StudySession.objects.create(
                user=request.user,
                duration=durasi_menit,
                # date otomatis terisi auto_now_add
            )
            return JsonResponse({'status': 'success', 'minutes': durasi_menit})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
            
    return JsonResponse({'status': 'invalid_method'}, status=405)

# alp_app/views.py
from django.db.models import F, Func
from .models import Question, QuizResult
from core_alp.irt_engine import update_theta_mle # Sesuaikan path importnya

def get_next_adaptive_question(user, quiz, request): # Tambahkan parameter request
    """Mencari soal yang kesulitannya (Beta) paling mendekati kemampuan (Theta) user"""
    user_theta = user.user_profile.ability_score
    
    # 1. Ambil daftar ID soal yang sudah dijawab dari session
    answered_ids = request.session.get('answered_question_ids', [])
    
    # 2. Cari soal yang belum dijawab & paling mendekati kemampuan user (Langkah 8 Flowchart)
    from django.db.models import F, Func
    next_question = Question.objects.filter(quiz=quiz).exclude(id__in=answered_ids).annotate(
        selisih=Func(F('difficulty_level') - user_theta, function='ABS')
    ).order_by('selisih').first()
    
    return next_question

# Tambahkan logika ini di dalam view yang memproses jawaban kuis
from core_alp.irt_engine import update_theta_mle

def submit_answer(request, question_id):
    user_profile = request.user.user_profile
    question = get_object_or_404(Question, pk=question_id)
    is_correct = (request.POST.get('answer') == question.correct_answer)
    
    # 1. Update Theta secara Real-time (Sesuai Flowchart Langkah 10)
    new_theta = update_theta_mle(
        current_theta=user_profile.ability_score,
        question_beta=question.difficulty_level, # Ini adalah parameter Beta (β)
        is_correct=is_correct
    )
    
    # 2. Simpan skor baru ke profil siswa
    user_profile.ability_score = new_theta
    user_profile.save()
    
    # 3. Langkah 11 Flowchart: Cek apakah kuis selesai atau cari soal berikutnya
    # yang tingkat kesulitannya (β) mendekati new_theta

@login_required
def exam_adaptive(request, quiz_pk):
    # Ambil kuis referensi sebagai pintu masuk ujian
    quiz = get_object_or_404(Quiz, pk=quiz_pk)
    user_profile = request.user.user_profile
    
    # --- PERUBAHAN: AMBIL OBJEK COURSE ---
    # Menarik seluruh soal yang bernaung di bawah Course yang sama
    course = quiz.lesson.module.course 
    
    # 1. Ambil SEMUA soal yang ada dalam Course ini (lintas semua modul dan pelajaran)
    total_soal_course = Question.objects.filter(quiz__lesson__module__course=course)
    total_count = total_soal_course.count()
    
    # Kriteria penghentian: Maksimal 20 soal agar mencakup lebih banyak materi dari seluruh modul
    MAX_QUESTIONS = min(total_count, 20) 

    if 'exam_step' not in request.session or request.GET.get('reset'):
        request.session['exam_step'] = 1
        request.session['exam_correct'] = 0
        request.session['exam_answered_ids'] = []

    if request.method == 'POST':
        question_id = request.POST.get('question_id')
        user_answer = request.POST.get('answer')
        
        if not question_id:
            return redirect('exam_adaptive', quiz_pk=quiz.pk)
            
        question = get_object_or_404(Question, id=question_id)
        
        # Update Theta via IRT Engine (Langkah 10 Flowchart)
        is_correct = (user_answer == question.correct_answer)
        if is_correct: 
            request.session['exam_correct'] += 1
        
        user_profile.ability_score = update_theta_mle(
            user_profile.ability_score, question.difficulty_level, is_correct
        )
        user_profile.save()

        # Catat ID agar soal tidak mengulang dalam satu sesi ujian
        answered_ids = request.session.get('exam_answered_ids', [])
        if int(question_id) not in answered_ids:
            answered_ids.append(int(question_id))
            request.session['exam_answered_ids'] = answered_ids
        
        request.session['exam_step'] += 1

        # Cek Selesai (Langkah 11-12 Flowchart)
        if request.session['exam_step'] > MAX_QUESTIONS:
            return proses_hasil_ujian(request, quiz, MAX_QUESTIONS)

    # 4. Seleksi Soal Berikutnya dari SELURUH bank soal COURSE (beta ≈ theta)
    next_q = total_soal_course.exclude(
        id__in=request.session.get('exam_answered_ids', [])
    ).annotate(
        selisih=Func(F('difficulty_level') - user_profile.ability_score, function='ABS')
    ).order_by('selisih').first()

    # Fallback jika soal habis sebelum mencapai MAX_QUESTIONS
    if not next_q:
        return proses_hasil_ujian(request, quiz, len(request.session.get('exam_answered_ids', [])))

    return render(request, 'quiz/quiz_detail.html', {
        'quiz': quiz, 
        'question': next_q, 
        'step': request.session['exam_step'], 
        'total_steps': MAX_QUESTIONS
    })

def proses_hasil_ujian(request, quiz, total_steps):
    score = request.session.get('exam_correct', 0)
    percentage = (score / total_steps) * 100
    is_passed = percentage >= 70
    
    # --- TAMBAHKAN LOGIKA INI ---
    # Cari materi pertama dari modul kuis ini untuk tombol "Review Materi"
    from .models import Lesson # Pastikan import ini ada jika di luar file models
    materi_awal = Lesson.objects.filter(
        module=quiz.lesson.module
    ).exclude(content_type='quiz').order_by('order').first()

    # Jika modul tidak punya materi (hanya kuis), fallback ke lesson kuis itu sendiri
    if not materi_awal:
        materi_awal = quiz.lesson
    # ----------------------------

    # Ambil rekomendasi berdasarkan Theta terbaru
    rekomendasi = "Lanjut ke Modul Berikutnya" if is_passed else "Jalur Remedial: Pelajari kembali dasar materi."
    
    # Simpan ke Database (Jangan lupa ini supaya score tersimpan permanen)
    from .models import QuizResult
    QuizResult.objects.update_or_create(
        user=request.user, quiz=quiz,
        defaults={
            'course': quiz.lesson.module.course,
            'score': score,
            'total_questions': total_steps,
            'theta_result': request.user.user_profile.ability_score
        }
    )

    # Bersihkan sesi ujian
    keys_to_clear = ['exam_step', 'exam_correct', 'exam_answered_ids', 'exam_wrong_topics']
    for key in keys_to_clear:
        if key in request.session:
            del request.session[key]
    request.session.modified = True

    return render(request, 'quiz/quiz_score.html', {
        'score': score, 
        'total': total_steps, 
        'percentage': percentage,
        'is_passed': is_passed, 
        'rekomendasi': rekomendasi, 
        'quiz': quiz,
        'materi_awal': materi_awal, # <-- SEKARANG SUDAH ADA, GA BAKAL ERROR LAGI
        'theta_akhir': request.user.user_profile.ability_score, # Tambahkan ini juga untuk tampilan score
        'is_exam': total_steps >= 20,
    })
# alp_app/views.py

@login_required
def remedial_quiz(request, course_pk):

    user_profile = request.user.user_profile
    course = get_object_or_404(Course, pk=course_pk)
    
    # 1. Ambil topik yang salah dari kuis sebelumnya (disimpan di session)
    # Jika session kosong (misal karena refresh), kita ambil default 'Umum'
    last_wrong_topics = request.session.get('last_wrong_topics', [])
    
    if not last_wrong_topics:
        messages.info(request, "Tidak ada data remedial. Silakan selesaikan kuis utama terlebih dahulu.")
        return redirect('course_detail', pk=course_pk)

    # 2. Cari bank soal yang sesuai dengan topik-topik salah tersebut di Course ini
    # Kita gunakan filter 'topic__in' untuk mencakup semua pokok inti yang gagal dikuasai
    remedial_pool = Question.objects.filter(
        quiz__lesson__module__course=course,
        topic__in=last_wrong_topics
    )
    
    total_available = remedial_pool.count()
    if total_available == 0:
        messages.warning(request, "Bank soal untuk topik remedial tersebut belum tersedia.")
        return redirect('course_detail', pk=course_pk)

    # 3. Batasi jumlah soal remedial (misal 5 soal agar fokus)
    MAX_REMEDIAL = min(total_available, 5)

    # 4. Inisialisasi Sesi Remedial (Mirip quiz_detail tapi khusus remedial)
    if 'remedial_step' not in request.session or request.GET.get('reset'):
        request.session['remedial_step'] = 1
        request.session['remedial_correct'] = 0
        request.session['remedial_answered_ids'] = []

    # 5. Logika POST (Proses Jawaban)
    if request.method == 'POST':
        question_id = request.POST.get('question_id')
        user_answer = request.POST.get('answer')
        question = get_object_or_404(Question, id=question_id)
        
        is_correct = (user_answer == question.correct_answer)
        if is_correct:
            request.session['remedial_correct'] += 1
            
        # Tetap update Theta agar kemampuan siswa tetap terpantau
        user_profile.ability_score = update_theta_mle(
            user_profile.ability_score, 
            question.difficulty_level, 
            is_correct
        )
        user_profile.save()

        request.session['remedial_answered_ids'].append(int(question_id))
        request.session['remedial_step'] += 1

        # Cek Selesai
        if request.session['remedial_step'] > MAX_REMEDIAL:
            score = request.session['remedial_correct']
            
            # Bersihkan sesi remedial
            del request.session['remedial_step']
            del request.session['remedial_correct']
            del request.session['remedial_answered_ids']
            # Topik salah tetap dipertahankan sampai user sukses remedial atau pindah kuis
            
            return render(request, 'quiz/quiz_score.html', {
                'score': score,
                'total': MAX_REMEDIAL,
                'percentage': (score / MAX_REMEDIAL) * 100,
                'is_remedial': True,
                'course': course
            })

    # 6. Seleksi Soal Remedial Berikutnya (ADAPTIF: Beta ≈ Theta)
    answered_ids = request.session.get('remedial_answered_ids', [])
    next_q = remedial_pool.exclude(id__in=answered_ids).annotate(
        selisih=Func(F('difficulty_level') - user_profile.ability_score, function='ABS')
    ).order_by('selisih').first()

    if not next_q:
        return redirect('course_detail', pk=course_pk)

    return render(request, 'quiz/quiz_detail.html', {
        'question': next_q,
        'step': request.session['remedial_step'],
        'total_steps': MAX_REMEDIAL,
        'is_remedial': True,
        'judul_kuis': f"Latihan Remedial: {', '.join(last_wrong_topics)}"
    })

# alp_app/views.py
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from django.views.generic import DetailView
from django.urls import reverse  # Tambahkan import ini
from .models import Course, Enrollment, Lesson
# alp_app/views.py
from django.db.models import Q, Avg # Pastikan Q dan Avg diimport
from django.urls import reverse

class ClassDetailView(DetailView):
    model = Course
    template_name = 'detail_class.html' 
    context_object_name = 'class_object' 
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.object
        
        # Saring diskusi utama
        context['discussions'] = course.discussions.filter(parent__isnull=True).order_by('-created_at')
        
        # --- 1. DATA RATING GLOBAL ---
        real_enrollments = Enrollment.objects.filter(course=course, rating__gt=0)
        total_real_reviews = real_enrollments.count()
        avg_rating_data = real_enrollments.aggregate(Avg('rating'))['rating__avg']
        global_avg = float(avg_rating_data) if avg_rating_data else 0.0

        # --- 2. LOGIKA USER LOGIN & NAVIGASI LANJUTKAN ---
        is_enrolled = False
        user_personal_rating = 0
        link_to_continue = None 
        
        if self.request.user.is_authenticated:
            enrollment = Enrollment.objects.filter(user=self.request.user, course=course).first()
            if enrollment:
                is_enrolled = True
                context['enrollment'] = enrollment
                user_personal_rating = enrollment.rating

                from .models import LessonCompletion
                context['completed_lessons'] = LessonCompletion.objects.filter(
                    user=self.request.user, 
                    lesson__module__course=course
                ).values_list('lesson_id', flat=True)
                
                # --- LOGIKA NAVIGASI (MENGGUNAKAN LESSONCOMPLETION) ---
                from .models import LessonCompletion, Lesson
                
                # Cari materi terakhir yang sudah diselesaikan (is_completed=True)
                last_completed = LessonCompletion.objects.filter(
                    user=self.request.user,
                    lesson__module__course=course
                ).order_by('lesson__module__order', 'lesson__order').last()

                if last_completed:
                    # Cari materi BERIKUTNYA setelah materi yang terakhir selesai
                    next_lesson = Lesson.objects.filter(module__course=course).filter(
                        Q(module__order__gt=last_completed.lesson.module.order) | 
                        Q(module__order=last_completed.lesson.module.order, order__gt=last_completed.lesson.order)
                    ).order_by('module__order', 'order').first()
                    
                    if next_lesson:
                        link_to_continue = reverse('lesson_content', args=[next_lesson.pk])
                    else:
                        # Jika sudah tamat semua, arahkan ke materi terakhir
                        link_to_continue = reverse('lesson_content', args=[last_completed.lesson.pk])
                else:
                    # Jika belum ada yang diselesaikan, ambil materi pertama di kelas ini
                    first_lesson = Lesson.objects.filter(module__course=course).order_by('module__order', 'order').first()
                    if first_lesson:
                        link_to_continue = reverse('lesson_content', args=[first_lesson.pk])
                    else:
                        link_to_continue = reverse('course_detail', args=[course.pk])

        # --- 3. FINALISASI ---
        rating_score = float(user_personal_rating) if user_personal_rating > 0 else global_avg
        context['is_enrolled'] = is_enrolled
        context['rating_score'] = rating_score
        context['total_reviews'] = total_real_reviews
        context['link_to_continue'] = link_to_continue 
        context['modules'] = course.modules.prefetch_related('lessons').all()
        
        return context

@csrf_exempt
@require_POST
@login_required
def save_rating(request, course_id):
    try:
        data = json.loads(request.body)
        stars = data.get('rating')
        
        # Cari data pendaftaran
        enrollment = Enrollment.objects.filter(user=request.user, course_id=course_id).first()
        
        if enrollment:
            enrollment.rating = int(stars)
            enrollment.save()
            return JsonResponse({'status': 'success', 'rating': stars})
        else:
            # JIKA TIDAK ADA DATA DAFTAR (ENROLLMENT)
            return JsonResponse({
                'status': 'error', 
                'message': 'Anda harus terdaftar di kelas ini untuk memberi rating.'
            }, status=403) # Kita kirim status 403 (Forbidden)
            
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    
from django.contrib.auth.decorators import login_required

@login_required # Hanya user yang login bisa buka halaman ini
def my_courses_view(request):
    # Mengambil data enrollment milik user tersebut
    user_enrollments = Enrollment.objects.filter(user=request.user)
    
    return render(request, 'my_courses.html', {
        'enrollments': user_enrollments
    })

# alp_app/views.py
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Discussion, Lesson
# alp_app/views.py
import json
from django.http import JsonResponse

@login_required
def post_discussion(request, course_id): 
    if request.method == 'POST':
        # Cek request dari AJAX
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            try:
                data = json.loads(request.body)
                content = data.get('content')
                parent_id = data.get('parent_id') # Bisa ID Utama atau ID Balasan
                course = get_object_or_404(Course, pk=course_id)
                
                if content:
                    # 1. Cari objek bapak langsungnya
                    parent_obj = Discussion.objects.get(id=parent_id) if parent_id else None
                    
                    # 2. Simpan diskusi baru ke database
                    discussion = Discussion.objects.create(
                        course=course,
                        user=request.user,
                        content=content,
                        parent=parent_obj
                    )

                    # 3. LOGIKA UI: Cari ID "Akar Teratas" (Root ID)
                    # Ini supaya JavaScript tahu balasan ini harus ditaruh di kontainer milik siapa
                    root_id = parent_id
                    if parent_obj:
                        # Jika bapaknya punya bapak lagi, kita telusuri sampai paling atas (Root)
                        curr = parent_obj
                        while curr.parent:
                            curr = curr.parent
                        root_id = curr.id
                    
                    return JsonResponse({
                        'status': 'success',
                        'id': discussion.id,
                        'username': request.user.username,
                        'content': discussion.content,
                        'is_staff': request.user.is_staff,
                        'parent_id': root_id # Mengirim Root ID agar JS menaruh pesan di kelompok yang benar
                    })
                    
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
        
        # Fallback untuk pengiriman form tradisional tanpa AJAX
        content = request.POST.get('content')
        parent_id = request.POST.get('parent_id')
        course = get_object_or_404(Course, pk=course_id)
        if content:
            parent_obj = Discussion.objects.get(id=parent_id) if parent_id else None
            Discussion.objects.create(
                course=course, 
                user=request.user, 
                content=content, 
                parent=parent_obj
            )
            
    return redirect('course_detail', pk=course_id)

from django.shortcuts import render
from django.http import JsonResponse
from .models import SupportReport

def support_view(request):
    if request.method == 'POST':
        # Ambil data dari form
        nama = request.POST.get('name')
        email_user = request.POST.get('email')
        kategori = request.POST.get('category')
        pesan = request.POST.get('message')

        try:
            # --- 1. PROSES SIMPAN KE DATABASE (TETAP JALAN) ---
            report = SupportReport(
                nama=nama,
                email=email_user,
                kategori=kategori,
                pesan=pesan,
                status='pending'
            )
            report.save()

            # --- 2. RESPON SUKSES ---
            # Kita langsung kirim status success supaya JavaScript di HTML 
            # bisa langsung lanjut nembak Formspree buat urusan Email.
            return JsonResponse({'status': 'success'})

        except Exception as e:
            # Cetak error di terminal buat Bos cek kalau simpan DB gagal
            print(f"DATABASE ERROR: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    # Untuk Method GET
    return render(request, 'support.html')
    
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Quiz, QuizResult 

@login_required
def sertifikat_view(request, quiz_id=None):
    if quiz_id:
        # Ambil QuizResult spesifik berdasarkan ID Quiz dan User
        result = QuizResult.objects.filter(
            quiz_id=quiz_id, 
            user=request.user
        ).select_related('quiz__lesson__module__course').last()
    else:
        # Ambil hasil kuis terakhir yang pernah dikerjakan user
        result = QuizResult.objects.filter(
            user=request.user
        ).select_related('quiz__lesson__module__course').last()

    # --- LOGIKA SYARAT AKSES ---
    # 1. Jika hasil kuis tidak ditemukan
    if not result:
        messages.warning(request, "Anda belum mengerjakan kuis untuk mendapatkan sertifikat.")
        return redirect('dashboard_app:dashboard') # Sesuaikan dengan nama URL dashboard kamu

    # 2. Jika sudah ada hasil tapi skor masih 0 (Belum memenuhi syarat kelulusan)
    if result.score <= 0:
        messages.error(request, "Skor kuis Anda tidak mencukupi untuk mendapatkan sertifikat. Silakan coba lagi.")
        # Mengarahkan kembali ke halaman kelas tersebut
        return redirect('alp_app:course_detail', pk=result.quiz.lesson.module.course.pk)

    # --- JIKA LOLOS SYARAT ---
    context = {
        'quiz': result.quiz,
        'theta_akhir': result.theta_result,
        'result': result,
    }
    
    return render(request, 'sertifikat.html', context)

@login_required
def list_sertifikat_view(request):
    # 1. Ambil semua pendaftaran kelas user yang sudah 100%
    completed_enrollments = Enrollment.objects.filter(
        user=request.user,
        progress_percentage__gte=100
    ).select_related('course')

    results = []

    for enrollment in completed_enrollments:
        # 2. Cari pelajaran terakhir dari modul terakhir di kelas ini
        # Ini adalah kuis 'final validation'
        last_module = enrollment.course.modules.order_by('order').last()
        if last_module:
            last_lesson = last_module.lessons.order_by('order').last()
            
            if last_lesson and hasattr(last_lesson, 'quiz'):
                # 3. Ambil hasil kuis terbaik user untuk kuis final tersebut
                best_result = QuizResult.objects.filter(
                    user=request.user,
                    quiz=last_lesson.quiz,
                    theta_result__gt=0
                ).order_by('-theta_result').first()

                if best_result:
                    results.append(best_result)

    context = {
        'results': results,
    }
    return render(request, 'list_sertifikat.html', context)