import time

def is_suspicious_speed(user_id, difficulty, elapsed_sec: float) -> bool:
    if elapsed_sec < 0.5:
        return True
    if difficulty >= 4 and elapsed_sec < 0.8:
        return True
    return False