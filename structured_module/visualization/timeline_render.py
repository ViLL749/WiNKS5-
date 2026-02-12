from PyQt5 import QtCore, QtGui, QtWidgets
import operator


# Вспомогательные функции
def align_to_step(qdate: QtCore.QDate, step_days: int, ceil=False):
    """
    Выравнивает дату по шагу step_days начиная с "эпохи" 2000-01-01.
    Если ceil=True, округляет вверх, иначе вниз.
    """
    epoch = QtCore.QDate(2000, 1, 1)
    days = epoch.daysTo(qdate)
    k = (days + (step_days - 1)) // step_days if ceil else days // step_days
    return epoch.addDays(k * step_days)


def ensure_min_span(start_d, end_d, step_days, px_per_day,
                    min_divisions, viewport_width, left_pad, right_pad):
    """
    Вычисляет минимальный span (длина оси) по условиям:
    - минимум min_divisions делений
    - минимум по ширине viewport
    Возвращает скорректированные axis_start и axis_end
    """
    span_days_min_div = min_divisions * step_days
    needed_px = max(0, viewport_width - (left_pad + right_pad))
    span_days_min_view = int((needed_px / max(px_per_day, 0.001)) + 0.999)
    base = start_d.daysTo(end_d)
    span = max(base, span_days_min_div, span_days_min_view)
    axis_start = start_d
    axis_end = align_to_step(axis_start.addDays(span), step_days, ceil=True)
    return axis_start, axis_end


# Основная функция
def draw_timeline(scene, tasks, step_days, viewport_w, ui_scale=1.0, dark_theme=True):
    """
    Рисует таймлайн задач в QGraphicsScene.
    """
    parsed = []
    today = QtCore.QDate.currentDate()

    # Цвета и стили
    if dark_theme:
        rect_brush_color = QtGui.QColor(70, 130, 180)
        rect_pen_color = QtGui.QColor("#89b4fa")
        text_color_main = QtGui.QColor("#cdd6f4")
        axis_color = QtGui.QColor("#585b70")
        tick_color = QtGui.QColor("#89b4fa")
        tick_text_color = QtGui.QColor("#bac2de")
        grid_color = QtGui.QColor(128, 128, 128, 40)
    else:
        rect_brush_color = QtGui.QColor(135, 206, 250)
        rect_pen_color = QtGui.QColor("#3399ff")
        text_color_main = QtGui.QColor("#1e1e2e")
        axis_color = QtGui.QColor("#a0a0a0")
        tick_color = QtGui.QColor("#3399ff")
        tick_text_color = QtGui.QColor("#2a2a2a")
        grid_color = QtGui.QColor(150, 150, 150, 60)

    # Фильтрация задач
    valid_tasks = []
    for t in tasks:
        s, e = t.get("start_date"), t.get("end_date")
        if not s or not e:
            continue
        sd, ed = QtCore.QDate.fromString(s, "yyyy-MM-dd"), QtCore.QDate.fromString(e, "yyyy-MM-dd")
        if not (sd.isValid() and ed.isValid()):
            continue
        t["_sd"], t["_ed"] = sd, ed
        valid_tasks.append(t)

    if not valid_tasks:
        msg = "Нет задач с корректными датами"
        txt = scene.addText(msg)
        txt.setDefaultTextColor(text_color_main)
        font = QtGui.QFont()
        font.setPointSize(int(16 * ui_scale))
        txt.setFont(font)
        scene.setSceneRect(0, 0, viewport_w, 300 * ui_scale)
        txt.setPos((viewport_w - txt.boundingRect().width()) / 2, 100 * ui_scale)
        return

    # Сортировка (показываем топ-5 актуальных)
    ongoing_tasks = [t for t in valid_tasks if t["_ed"] >= today]
    past_tasks = [t for t in valid_tasks if t["_ed"] < today]
    ongoing_tasks.sort(key=operator.itemgetter("_ed"))
    past_tasks.sort(key=operator.itemgetter("_ed"), reverse=True)
    selected_tasks = ongoing_tasks[:5]
    if len(selected_tasks) < 5:
        selected_tasks += past_tasks[:5 - len(selected_tasks)]
    selected_tasks = list(reversed(selected_tasks))

    for t in selected_tasks:
        sd, ed = t["_sd"], t["_ed"]
        tip = (f"{t.get('title')}\n"
               f"S: {t.get('s_text') or '-'}\n"
               f"M: {t.get('m_text') or '-'}\n"
               f"A: {t.get('a_text') or '-'}\n"
               f"R: {t.get('r_text') or '-'}\n"
               f"{sd.toString('dd.MM.yyyy')} → {ed.toString('dd.MM.yyyy')}")
        parsed.append((t["id"], t.get("title") or f"Задача {t['id']}", sd, ed, tip))

    # Настройки размеров
    px_per_day = 3.6 * (30 / step_days) * ui_scale
    left_pad, right_pad = 40 * ui_scale, 40 * ui_scale
    y_start, bar_h, spacing = 20 * ui_scale, 35 * ui_scale, 60 * ui_scale
    current_y = y_start

    min_date = min(p[2] for p in parsed)
    max_date = max(p[3] for p in parsed).addDays(1)

    axis_start = align_to_step(min_date, step_days)
    axis_end_raw = align_to_step(max_date, step_days, ceil=True)
    axis_start, axis_end = ensure_min_span(axis_start, axis_end_raw, step_days, px_per_day,
                                           min_divisions=10, viewport_width=viewport_w,
                                           left_pad=left_pad, right_pad=right_pad)

    total_days = axis_start.daysTo(axis_end)
    axis_start_x = left_pad
    axis_end_x = left_pad + total_days * px_per_day

    # 1. РИСУЕМ БАРЫ ЗАДАЧ
    for tid, title, sd, ed, tip in parsed:
        x = axis_start_x + axis_start.daysTo(sd) * px_per_day
        w = max(15 * ui_scale, sd.daysTo(ed.addDays(1)) * px_per_day)

        rect = scene.addRect(QtCore.QRectF(x, current_y, w, bar_h),
                             QtGui.QPen(rect_pen_color, 2),
                             QtGui.QBrush(rect_brush_color))
        rect.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        rect.setData(0, tid)
        rect.setToolTip(tip)

        txt = scene.addText(title)
        f = txt.font()
        f.setPointSize(int(9 * ui_scale))
        f.setBold(True)
        txt.setFont(f)
        txt.setDefaultTextColor(text_color_main)
        txt.setPos(x + 8 * ui_scale, current_y + (bar_h - txt.boundingRect().height()) / 2)

        current_y += spacing

    # 2. ОСЬ ВРЕМЕНИ И СЕТКА
    axis_y = current_y + 15 * ui_scale
    grid_pen = QtGui.QPen(grid_color, 1, QtCore.Qt.DotLine)
    scene.addLine(axis_start_x, axis_y, axis_end_x, axis_y, QtGui.QPen(axis_color, 2))

    tick_font = QtGui.QFont("Arial", int(10 * ui_scale))
    fm = QtGui.QFontMetrics(tick_font)

    cur = axis_start
    while cur <= axis_end:
        x = axis_start_x + axis_start.daysTo(cur) * px_per_day

        # Вертикальная сетка
        scene.addLine(x, 0, x, axis_y, grid_pen)

        # Деление на оси
        scene.addLine(x, axis_y - 5 * ui_scale, x, axis_y + 5 * ui_scale, QtGui.QPen(tick_color))

        # Текст даты
        date_str = cur.toString("dd.MM")
        label = scene.addText(date_str)
        label.setFont(tick_font)
        label.setDefaultTextColor(tick_text_color)
        tw = fm.horizontalAdvance(date_str)
        label.setPos(x - tw / 2, axis_y + 8 * ui_scale)

        # Линия "Сегодня"
        if cur == today:
            today_pen = QtGui.QPen(QtGui.QColor("#ff5555"), 2)
            scene.addLine(x, 0, x, axis_y + 25 * ui_scale, today_pen)

        cur = cur.addDays(step_days)

    # Установка границ сцены
    scene.setSceneRect(0, 0, max(axis_end_x + right_pad, viewport_w), axis_y + 60 * ui_scale)