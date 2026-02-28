# alp_app/urls.py

from django.urls import path
from . import views
from .views import ClassListView
from django.shortcuts import render

urlpatterns = [
    path('', views.home_master, name='home_master'), 

    path('accounts/login/', views.login_view, name='login_view'),
    path('accounts/signup/', views.signup_view, name='signup_view'),

    path('classes/', views.ClassListView.as_view(), name='course_list'),
    path('classes/<int:pk>/', views.ClassDetailView.as_view(), name='course_detail'),

    path('classes/', ClassListView.as_view(), name='class_list'),

    path('quiz/<int:quiz_pk>/', views.quiz_detail, name='quiz_detail'),
    path('lesson/<int:lesson_pk>/', views.lesson_content, name='lesson_content'),
    path('exam/<int:quiz_pk>/', views.exam_adaptive, name='exam_adaptive'),

    path('enroll/<int:course_pk>/', views.course_enroll, name='course_enroll'),

    path('lesson/complete/<int:lesson_id>/', views.mark_lesson_complete, name='mark_lesson_complete'),

    path('update-study-time/', views.update_study_time, name='update_study_time'),

    path('save-rating/<int:course_id>/', views.save_rating, name='save_rating'),

    path('support/', views.support_view, name='support'),
    path('about/', views.about_view, name='about'),

    path('my-courses/', views.my_courses_view, name='my_courses'),

    path('remedial/<int:course_pk>/', views.remedial_quiz, name='remedial_quiz'),

    path('sertifikat/', views.sertifikat_view, name='lihat_sertifikat'),
    path('sertifikat/<int:quiz_id>/', views.sertifikat_view, name='sertifikat_detail'),
    path('sertifikat/list/', views.list_sertifikat_view, name='list_sertifikat'),

    path('post-discussion/<int:course_id>/', views.post_discussion, name='post_discussion'),

    path('feedback/', views.feedback_view, name='feedback_view'),
    path('discussion/', views.discussion_view, name='discussion_view'),
    path('discussion/post/', views.post_comment, name='post_comment'),
    path('discussion/like/<int:comment_id>/', views.like_comment, name='like_comment'),
    path('discussion/reply/<int:comment_id>/', views.reply_comment, name='reply_comment'),

    path('trigger-500/', views.trigger_error, name='test_500'),

    path('terms/', lambda r: render(r, 'legal/terms.html'), name='terms'),
    path('privacy/', lambda r: render(r, 'legal/privacy.html'), name='privacy'),
    path('sitemap/', lambda r: render(r, 'legal/sitemap_view.html'), name='sitemap'),
]

handler404 = 'alp_app.views.custom_404'
handler500 = 'alp_app.views.custom_500'