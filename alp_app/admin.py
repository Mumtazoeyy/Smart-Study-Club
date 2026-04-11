# alp_app/admin.py

from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.safestring import mark_safe
from .models import (
    Course, Module, Lesson, Enrollment, Category, Quiz, Question, QuizResult, LessonCompletion, StudySession, StudyHistory, Discussion, SupportReport, Topic
)
from profiles_app.models import Profile
from django.core.exceptions import ObjectDoesNotExist

import csv  # Tambahkan ini
from django.http import HttpResponse
from django.utils.timezone import localtime, now
from django.utils import timezone
from django.urls import path

# =========================================================
# 1. LOGIKA INLINES
# =========================================================

class EnrollmentInline(admin.TabularInline):
    model = Enrollment
    extra = 1
    # Gunakan 'formatted_theta' agar tampilan di tabel ringkas
    readonly_fields = ('last_accessed', 'average_score', 'formatted_theta', 'total_study_time')
    can_delete = True
    classes = ['inline-history']
    fields = (
        'course', 
        'rating', 
        'progress_percentage', 
        'average_score', 
        'formatted_theta', # Memanggil fungsi pembulatan di bawah
        'total_study_time', 
        'last_accessed'
    )

    def formatted_theta(self, obj):
        return round(obj.theta_result, 2) if obj.theta_result else 0.0
    formatted_theta.short_description = 'Theta (IRT)'

class QuizResultInline(admin.TabularInline):
    model = QuizResult
    extra = 1
    readonly_fields = ('date', 'formatted_theta')
    can_delete = True
    classes = ['inline-history']
    # Ganti theta_result (DB) menjadi formatted_theta (Fungsi)
    fields = ('course', 'quiz', 'score', 'total_questions', 'formatted_theta', 'date')

    def formatted_theta(self, obj):
        if obj.theta_result is not None:
            return round(float(obj.theta_result), 2)
        return "0.0"
    formatted_theta.short_description = 'Theta Result'

class LessonCompletionInline(admin.TabularInline):
    model = LessonCompletion
    extra = 1
    readonly_fields = ('completed_at',)
    can_delete = True
    classes = ['inline-history']
    fields = ('lesson', 'completed_at')

class StudyHistoryInline(admin.TabularInline):
    model = StudyHistory
    extra = 1
    readonly_fields = ('timestamp',)
    can_delete = True
    classes = ['inline-history']
    fields = ('activity_name', 'link', 'timestamp')
# =========================================================
# 2. CATEGORY ADMIN
# =========================================================

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    list_display_links = ('id', 'name')
    search_fields = ('name',)
    ordering = ('name',)

# =========================================================
# 3. USER ADMIN (Custom)
# =========================================================

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Informasi Tambahan (Kelas)'

    # Field ini memanggil fungsi @property dari models.py
    readonly_fields = (
        'get_calculated_theta',
        'get_calculated_time',
        'get_calculated_avg',
        'perubahan_waktu_belajar'
    )

    # Menentukan urutan tampilan field di form Admin
    fields = (
        'kelas', 'nama_lengkap', 'foto', 'level', 'bio',
        'get_calculated_theta', 
        'get_calculated_time', 
        'get_calculated_avg'
    )

# Pastikan untuk unregister User bawaan sebelum mendaftarkan kembali yang kustom
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline, EnrollmentInline, QuizResultInline, LessonCompletionInline, StudyHistoryInline)
    list_display = BaseUserAdmin.list_display + ('get_kelas',)
    list_filter = BaseUserAdmin.list_filter + ('is_staff', 'is_superuser', 'user_profile__kelas')

    # 1. Baris actions (tetap sama)
    actions = ['export_progres_csv']

    # 2. Fungsi yang sudah diperbaiki agar mengambil data PALING BARU
    def export_progres_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse
        from django.utils.timezone import localtime
        from django.utils import timezone

        # Memastikan data paling mutakhir dari database
        queryset = queryset.all()

        # Nama file sederhana sesuai permintaan: progres_(namauser).csv
        if queryset.count() == 1:
            filename = f"progres_{queryset.first().username}.csv"
        else:
            filename = "progres_kolektif_siswa.csv"

        response = HttpResponse(content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        # Anti-Cache agar data selalu real-time
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response.write(u'\ufeff'.encode('utf8'))

        writer = csv.writer(response, delimiter=';', quoting=csv.QUOTE_MINIMAL)

        # Header Kolom
        writer.writerow(['Username', 'Nama Lengkap', 'Kelas', 'Ability Score (Theta)', 'Kuis', 'Skor', 'Total Soal', 'Tanggal & Waktu'])

        for user in queryset:
            profile = getattr(user, 'user_profile', None)
            nama_lengkap = profile.nama_lengkap if profile else user.username
            kelas = profile.get_kelas_display() if profile and profile.kelas else "-"

            # Ambil data real-time langsung dari database
            results = QuizResult.objects.filter(user=user).all().order_by('date')

            if results.exists():
                for res in results:
                    theta_rounded = round(res.theta_result, 2) if res.theta_result else 0.0
                    theta_fix = str(theta_rounded).replace('.', ',')
                    waktu_lokal = localtime(res.date).strftime('%d/%m/%Y %H:%M:%S')
                    writer.writerow([
                        user.username,
                        nama_lengkap,
                        kelas,
                        theta_fix,
                        res.quiz.title,
                        res.score,
                        res.total_questions,
                        f" {waktu_lokal}"
                    ])
            else:
                writer.writerow([user.username, nama_lengkap, kelas, "0", "Data Tidak Ditemukan", 0, 0, "-"])

        # --- BAGIAN KETERANGAN LAPORAN (FOOTER) ---
        waktu_ekstraksi = localtime(timezone.now())
        writer.writerow([])
        writer.writerow(['DOKUMEN RIWAYAT AKTIVITAS - SMART STUDY CLUB'])
        writer.writerow(['Kode Laporan', f'SSC-{waktu_ekstraksi.strftime("%Y%m%d-%H%M%S")}'])
        writer.writerow(['Jenis Data', 'Laporan Perkembangan Nilai Siswa dari Hasil Kuis'])
        writer.writerow(['Waktu Download', waktu_ekstraksi.strftime('%d/%m/%Y jam %H:%M:%S WIB')])
        writer.writerow(['Metode Penilaian', 'Item Response Theory (IRT) - Pemodelan Probabilitas'])
        writer.writerow(['Skala Nilai', 'Skor Kemampuan (Theta) berada pada rentang -4.00 sampai +4.00'])
        writer.writerow(['Sumber Data', 'Database Server (Tersinkronisasi Otomatis/Real-Time)'])
        writer.writerow(['Status Dokumen', 'Sah - Dihasilkan otomatis oleh sistem aplikasi'])
        writer.writerow(['*** AKHIR DOKUMEN ***'])

        return response

    export_progres_csv.short_description = "Download CSV Progres User"

    def generate_random_history(self, request, object_id):
        import random
        from django.utils import timezone
        from django.db.models import Avg, Sum
        from django.shortcuts import redirect
        from django.contrib import messages
        # Import model sesuai file models.py kamu
        from .models import Course, Module, Lesson, StudyHistory, LessonCompletion, Enrollment, QuizResult

        actual_id = object_id.split('/')[0]
        user = self.get_object(request, actual_id)
        
        # 1. Pilih Course secara acak
        course = Course.objects.order_by('?').first()
        if not course:
            self.message_user(request, "Gagal: Tidak ada Course tersedia!", messages.ERROR)
            return redirect("..")

        # 2. Daftarkan User (Enrollment) jika belum ada
        enrollment, created = Enrollment.objects.get_or_create(
            user=user,
            course=course,
            defaults={'last_accessed': timezone.now()}
        )

        # 3. Ambil 2 Modul pertama agar urut
        modules = Module.objects.filter(course=course).order_by('id')[:2]
        
        for module in modules:
            lessons = Lesson.objects.filter(module=module).order_by('id')
            for lesson in lessons:
                # Tambah ke History
                StudyHistory.objects.get_or_create(
                    user=user,
                    activity_name=f"{module.title}: {lesson.title}",
                    link=f"/course/lesson/{lesson.id}/"
                )
                # Tambah ke Completion
                LessonCompletion.objects.get_or_create(user=user, lesson=lesson)

                # Jika ada kuis, buat hasil kuis dengan skor bervariasi
                if hasattr(lesson, 'quiz') and lesson.quiz:
                    QuizResult.objects.get_or_create(
                        user=user,
                        quiz=lesson.quiz,
                        course=course,
                        defaults={
                            'score': random.choice([70, 80, 85, 90, 100]),
                            'total_questions': 10,
                            'theta_result': random.uniform(0.1, 1.5), 
                            'date': timezone.now()
                        }
                    )

        # =========================================================
        # 4. LOGIKA UPDATE DATABASE ASLI
        # =========================================================
        
        # Hitung Progress secara nyata (karena progress_percentage adalah field DB asli)
        total_lessons_in_course = Lesson.objects.filter(module__course=course).count()
        user_completed = LessonCompletion.objects.filter(user=user, lesson__module__course=course).count()
        
        actual_progress = 0
        if total_lessons_in_course > 0:
            actual_progress = (user_completed / total_lessons_in_course) * 100

        # Simpan hanya ke field yang ada di database (bukan property)
        enrollment.progress_percentage = actual_progress
        enrollment.last_accessed = timezone.now()
        enrollment.save()

        # Update juga field point di Profile jika ada (ini field DB asli)
        profile = getattr(user, 'user_profile', None)
        if profile:
            # Contoh menambah poin setiap kali generate history
            profile.points += 10
            profile.save()

        self.message_user(request, f"Berhasil! Data '{course.title}' digenerate. Statistik akan otomatis terhitung di tampilan.", messages.SUCCESS)
        return redirect("..")
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<path:object_id>/generate-history/', self.admin_site.admin_view(self.generate_random_history), name='generate-random-history'),
        ]
        return custom_urls + urls
    
    def get_kelas(self, obj):
        # Ambil label kelas dari model Profile via related_name 'user_profile'
        try:
            if hasattr(obj, 'user_profile') and obj.user_profile.kelas:
                return obj.user_profile.get_kelas_display()
        except:
            pass
        return "-"
    get_kelas.short_description = 'Kelas'

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        
        # Ambil teks judul (User)
        title_text = str(self.model._meta.verbose_name.capitalize())
        
        # Generate URL
        generate_url = f"./generate-history/"
        
        # EDIT: Tambahkan 'display:none' dan ID 'magic-btn' pada tombol
        btn_style = "display:none; background: #28a745; color: white; padding: 5px 15px; border-radius: 4px; text-decoration: none; font-size: 12px; margin-left: 20px; vertical-align: middle; font-weight: normal;"
        magic_button = f'<a id="magic-btn" href="{generate_url}" style="{btn_style}">🎲 Generate Random History</a>'
        
        # EDIT: Bungkus judul dengan span dan ID agar bisa diklik
        trigger_title = f'<span id="toggle-trigger" style="cursor:pointer;">{title_text}</span>'

        js_code = """
        <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
        <script>
        $(document).ready(function() {
            // FITUR BARU: Klik judul untuk memunculkan/menyembunyikan tombol
            $('#toggle-trigger').on('click', function() {
                $('#magic-btn').toggle();
            });

            $('.inline-group h2').each(function() {
                var header = $(this);
                var actionHtml = `
                    <div class="custom-inline-actions" style="margin: 10px 0; padding: 8px; background: #ebebeb; border-radius: 4px; display: flex; align-items: center; gap: 10px;">
                        <span class="all-btn" style="color: #447e9b; font-weight: bold; cursor: pointer; text-decoration: underline;">All</span>
                        <span style="color: #ddd;">|</span>
                        <span style="font-size: 11px; color: #666;">Aksi:</span>
                        <select class="action-select" style="padding: 2px;">
                            <option value="">---------</option>
                            <option value="delete">Hapus Terpilih</option>
                        </select>
                        <button type="button" class="go-btn" style="background: #ba2121; color: white; border: none; padding: 3px 10px; cursor: pointer; border-radius: 3px; font-weight: bold;">Go</button>
                    </div>`;
                header.after(actionHtml);
            });
            $(document).on('click', '.all-btn', function() {
                $(this).closest('.inline-group').find('td.delete input[type="checkbox"]').prop('checked', true);
            });
            $(document).on('click', '.go-btn', function() {
                var select = $(this).siblings('.action-select').val();
                if (select === 'delete') {
                    var checkedCount = $(this).closest('.inline-group').find('td.delete input[type="checkbox"]:checked').length;
                    if (checkedCount > 0) {
                        if (confirm('Hapus ' + checkedCount + ' baris riwayat? Klik Save untuk konfirmasi.')) {
                            $('input[name="_continue"]').click();
                        }
                    } else { alert('Pilih data terlebih dahulu!'); }
                }
            });
        });
        </script>
        """
        
        # Menggabungkan Judul yang bisa diklik, Tombol Tersembunyi, dan JS Code
        extra_context['title'] = mark_safe(f"{trigger_title} {magic_button} {js_code}")
        
        return super().change_view(request, object_id, form_url, extra_context)

# =========================================================
# 4. KONTEN HIERARKIS & COURSE
# =========================================================

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'course_code', 'category', 'level')
    list_filter = ('category', 'level')
    search_fields = ('title', 'course_code')

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 3
    fields = ('text', 'topic_relation', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer', 'difficulty_level')

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    # Gunakan topic_relation agar muncul dropdown Topic
    list_display = ('id', 'quiz', 'text_preview', 'topic_relation', 'difficulty_level')
    list_filter = ('topic_relation', 'quiz')
    search_fields = ('text', 'topic_relation__name')

    def text_preview(self, obj):
        return obj.text[:50] + "..." if obj.text else "-"
    text_preview.short_description = 'Isi Pertanyaan'
    
@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'lesson', 'is_quiz')
    inlines = [QuestionInline]
    list_filter = ('lesson__module__course',)

    list_editable = ('is_quiz',)

class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1
    fields = ('title', 'content_type', 'order')
    show_change_link = True

@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order')
    list_filter = ('course',)
    inlines = [LessonInline]

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'content_type', 'image_preview')
    list_filter = ('module__course', 'content_type')

    fields = ('module', 'title', 'content', 'image', 'video_url', 'content_type', 'order', 'is_quiz')

    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="50" height="50" style="object-fit: cover; border-radius: 4px;" />')
        return "No Image"
    image_preview.short_description = 'Preview'

@admin.register(StudySession)
class StudySessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'duration', 'date')
    list_filter = ('date', 'user')

# =========================================================
# 5. DISKUSI
# =========================================================

class ReplyInline(admin.TabularInline):
    model = Discussion
    extra = 0
    fields = ('user', 'content', 'created_at')
    readonly_fields = ('created_at',)
    fk_name = 'parent'

@admin.register(Discussion)
class DiscussionAdmin(admin.ModelAdmin):
    list_display = ('user', 'short_content', 'course', 'is_reply', 'created_at')
    list_filter = ('course', 'created_at', 'user')
    search_fields = ('content', 'user__username')
    inlines = [ReplyInline]

    def is_reply(self, obj):
        return obj.parent is not None
    is_reply.boolean = True

    def short_content(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(parent__isnull=True)

# Di bagian bawah admin.py
@admin.register(SupportReport)
class SupportReportAdmin(admin.ModelAdmin):
    # Kolom yang muncul di daftar tabel utama
    list_display = ('nama', 'kategori', 'status', 'created_at')

    # Kolom status bisa diedit langsung (Dropdown akan otomatis muncul karena 'choices' di model)
    list_editable = ('status',)

    list_filter = ('status', 'kategori', 'created_at')
    search_fields = ('nama', 'pesan', 'email')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

# Pastikan UserAnswer di-import agar tidak muncul NameError
from .models import UserAnswer

@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    # 'theta_at_time' sudah dihapus agar tidak AttributeError
    list_display = ('user', 'question', 'is_correct', 'created_at')
    list_filter = ('is_correct', 'created_at')
    search_fields = ('user__username', 'question__text')

@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('name',) # Menampilkan kolom nama topik
    search_fields = ('name',) # Agar bisa cari topik berdasarkan nama
