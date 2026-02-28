# alp_app/admin.py

from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.safestring import mark_safe
from .models import (
    Course, Module, Lesson, Enrollment, Category, Quiz, Question, QuizResult, LessonCompletion, StudySession, Discussion, SupportReport,
)
from profiles_app.models import Profile
from django.core.exceptions import ObjectDoesNotExist

import csv  # Tambahkan ini
from django.http import HttpResponse  
from django.utils.timezone import localtime, now 
from django.utils import timezone 

# =========================================================
# 1. LOGIKA INLINES
# =========================================================

class EnrollmentInline(admin.TabularInline):
    model = Enrollment
    extra = 0
    readonly_fields = ('course', 'progress_percentage', 'last_accessed')
    can_delete = True
    classes = ['inline-history']
    fields = ('course', 'rating', 'progress_percentage', 'last_accessed')

class QuizResultInline(admin.TabularInline):
    model = QuizResult
    extra = 0
    readonly_fields = ('quiz', 'score', 'total_questions', 'theta_result', 'date')
    can_delete = True
    classes = ['inline-history']

class LessonCompletionInline(admin.TabularInline):
    model = LessonCompletion
    extra = 0
    readonly_fields = ('lesson', 'completed_at')
    can_delete = True
    classes = ['inline-history']

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
    
    # Field ini akan muncul sebagai teks statis di Admin (Tidak bisa diketik)
    readonly_fields = (
        'ability_score', 
        'total_waktu_belajar', 
        'nilai_rata_rata',
        'perubahan_waktu_belajar'
    )
    
    # Menentukan urutan tampilan field di form Admin
    fields = (
        'kelas', 'nama_lengkap', 'foto', 'level', 'bio', 
        'ability_score', 'total_waktu_belajar', 'nilai_rata_rata'
    )

# Pastikan untuk unregister User bawaan sebelum mendaftarkan kembali yang kustom
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline, EnrollmentInline, QuizResultInline, LessonCompletionInline)
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
                    theta_fix = str(res.theta_result).replace('.', ',')
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
        js_code = """
        <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
        <script>
        $(document).ready(function() {
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
        extra_context['title'] = mark_safe(str(self.model._meta.verbose_name_plural.capitalize()) + js_code)
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
    fields = ('text', 'topic', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer', 'difficulty_level')

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

