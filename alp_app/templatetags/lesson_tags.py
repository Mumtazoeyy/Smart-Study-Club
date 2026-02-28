import re
from django import template
from ..models import Lesson

register = template.Library()

@register.filter
def youtube_embed(value):
    if not value:
        return ""
    
    # Regex ini lebih akurat untuk mengambil 11 karakter ID YouTube
    regex = r"(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/|\/shorts\/)([^\"&?\/\s]{11})"
    match = re.search(regex, value)
    
    if match:
        video_id = match.group(1)
        # Tambahkan parameter origin untuk membantu koneksi localhost
        return f"https://www.youtube.com/embed/{video_id}?rel=0&modestbranding=1"
    
    return value

@register.simple_tag
def get_next_lesson_url(lesson):
    """Mencari URL pelajaran berikutnya (Next)."""
    try:
        next_lesson = Lesson.objects.filter(
            module=lesson.module,
            order__gt=lesson.order
        ).order_by('order').first()

        if next_lesson:
            return next_lesson.get_absolute_url()
        
        next_module = lesson.module.course.module_set.filter(
            order__gt=lesson.module.order
        ).order_by('order').first()

        if next_module:
            first_lesson_in_next_module = next_module.lesson_set.order_by('order').first()
            if first_lesson_in_next_module:
                return first_lesson_in_next_module.get_absolute_url()
        
        return lesson.module.course.get_absolute_url()
    except Exception:
        return lesson.module.course.get_absolute_url()
    
@register.simple_tag
def check_next_is_quiz(lesson):
    """Cek apakah lesson berikutnya punya konten kuis"""
    try:
        next_lesson = Lesson.objects.filter(
            module=lesson.module,
            order__gt=lesson.order
        ).order_by('order').first()
        
        if next_lesson and next_lesson.content_type == 'quiz':
            return True
        return False
    except:
        return False

@register.simple_tag
def get_previous_lesson_url(lesson):
    """Mencari URL pelajaran sebelumnya (Previous)."""
    try:
        prev_lesson = Lesson.objects.filter(
            module=lesson.module,
            order__lt=lesson.order
        ).order_by('-order').first()

        if prev_lesson:
            return prev_lesson.get_absolute_url()

        prev_module = lesson.module.course.module_set.filter(
            order__lt=lesson.module.order
        ).order_by('-order').first()

        if prev_module:
            last_lesson_in_prev_module = prev_module.lesson_set.order_by('-order').first()
            if last_lesson_in_prev_module:
                return last_lesson_in_prev_module.get_absolute_url()
        
        return None
    except Exception:
        return None

@register.filter
def is_completed_by(lesson, user):
    """Mengecek apakah user sudah menyelesaikan materi ini."""
    if not user or not user.is_authenticated:
        return False
    return lesson.lessoncompletion_set.filter(user=user).exists()