# profiles_app/admin.py
from django.contrib import admin
from .models import Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    # Daftarkan fungsi sebagai readonly agar bisa muncul di fieldsets
    readonly_fields = (
        'get_calculated_theta', 
        'get_calculated_avg', 
        'get_calculated_time',
        'get_hierarchy_name'
    )

    fieldsets = (
        (None, {
            'fields': ('user', 'foto', 'nama_lengkap', 'kelas', 'level', 'bio', 'points')
        }),
        ('Statistik Kemampuan (Sistem Otomatis)', {
            'fields': (
                'get_calculated_theta', # Memanggil fungsi hitung, bukan field database
                'get_calculated_avg',   # Memanggil fungsi hitung, bukan field database
                'get_calculated_time',  # Memanggil fungsi hitung, bukan field database
                'get_hierarchy_name'
            ),
            'description': 'Angka ini dihitung otomatis dari data kuis yang ada di bawah.'
        }),
    )