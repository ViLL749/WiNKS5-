# visualization/animator_controller.py
class AnimatorController:
    """
    Заглушка под анимации/плавность.
    Сейчас просто возвращает целевой индекс увеличения/уменьшения масштаба.
    Если захочешь — сюда можно добавить QPropertyAnimation.
    """
    def apply_zoom_index(self, current_index: int, target_index: int) -> int:
        return target_index
