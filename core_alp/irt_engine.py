# core_alp/irt_engine.py
import math

def calculate_probability(theta, beta):
    """Rumus Model Rasch: P(theta) = e^(theta-beta) / (1 + e^(theta-beta))"""
    try:
        exponent = math.exp(theta - beta)
        return exponent / (1 + exponent)
    except OverflowError:
        return 1.0 if theta > beta else 0.0

def update_theta_mle(current_theta, question_beta, is_correct):
    """Update skor kemampuan (Theta) berdasarkan jawaban siswa"""
    learning_rate = 0.5 
    probability = calculate_probability(current_theta, question_beta)
    
    actual = 1.0 if is_correct else 0.0
    new_theta = current_theta + learning_rate * (actual - probability)
    
    # Batasi agar tetap di range standar IRT -3.0 sampai 3.0
    return max(min(round(new_theta, 2), 3.0), -3.0)