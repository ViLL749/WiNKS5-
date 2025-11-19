from PyQt5 import QtCore, QtGui, QtWidgets


# Функции для выравнивания оси
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


import operator
from PyQt5 import QtCore, QtGui, QtWidgets


# Функция отрисовки таймлайна
def draw_timeline(scene, tasks, step_days, viewport_w):
    parsed = []
    today = QtCore.QDate.currentDate()

    # Фильтруем задачи с валидными датами
    valid_tasks = []
    for t in tasks:
        s = t.get("start_date")
        e = t.get("end_date")
        if not s or not e:
            continue
        sd = QtCore.QDate.fromString(s, "yyyy-MM-dd")
        ed = QtCore.QDate.fromString(e, "yyyy-MM-dd")
        if not (sd.isValid() and ed.isValid()):
            continue
        t["_sd"] = sd
        t["_ed"] = ed
        valid_tasks.append(t)

    if not valid_tasks:
        txt = scene.addText("Нет задач с корректными датами")
        txt.setDefaultTextColor(QtGui.QColor("#cdd6f4"))
        txt.setPos(20, 20)
        scene.setSceneRect(0, 0, 600, 200)
        return

    # Сортировка по актуальности
    ongoing_tasks = [t for t in valid_tasks if t["_ed"] >= today]
    past_tasks = [t for t in valid_tasks if t["_ed"] < today]

    # Берем до 5 задач из ongoing, затем, если нужно, добавляем из past
    ongoing_tasks.sort(key=operator.itemgetter("_ed"))  # ближе к сегодня – раньше
    past_tasks.sort(key=operator.itemgetter("_ed"), reverse=True)

    selected_tasks = ongoing_tasks[:5]
    if len(selected_tasks) < 5:
        needed = 5 - len(selected_tasks)
        selected_tasks += past_tasks[:neede
    # Делаем реверс для визуализации сверху вниз
    selected_tasks = list(reversed(selected_tasks))

    # Подготовка parsed для отрисовки
    for t in selected_tasks:
        sd = t["_sd"]
        ed = t["_ed"]
        tip = (f"{t.get('title')}\n"
               f"S: {t.get('s_text') or '-'}\n"
               f"M: {t.get('m_text') or '-'}\n"
               f"A: {t.get('a_text') or '-'}\n"
               f"R: {t.get('r_text') or '-'}\n"
               f"{sd.toString('dd.MM.yyyy')} → {ed.toString('dd.MM.yyyy')}")
        parsed.append((t["id"], t.get("title") or f"Задача {t['id']}", sd, ed, tip))

    # Настройки визуализации
    px_per_day = 3.6 * (30 / step_days) # ширина одного дня в пикселях
    left_pad, right_pad = 40, 40
    y = 20 # начальная координата по вертикали
    bar_h = 35 # высота бара задачи
    spacing = 60 # расстояние между задачами

    # Определяем диапазон оси
    min_date = min(p[2] for p in parsed)
    max_date = max(p[3] for p in parsed).addDays(1)

    axis_start = align_to_step(min_date, step_days)
    axis_end_raw = align_to_step(max_date, step_days, ceil=True)

    axis_start, axis_end = ensure_min_span(
        axis_start, axis_end_raw, step_days, px_per_day,
        min_divisions=10, viewport_width=viewport_w,
        left_pad=left_pad, right_pad=right_pad
    )

    total_days = axis_start.daysTo(axis_end)
    axis_start_x = left_pad
    axis_end_x = axis_start_x + total_days * px_per_day

    # Отрисовка баров задач
    for tid, title, sd, ed, tip in parsed:
        x = axis_start_x + axis_start.daysTo(sd) * px_per_day
        w = max(15, sd.daysTo(ed.addDays(1)) * px_per_day)

        rect = scene.addRect(QtCore.QRectF(x, y, w, bar_h),
                             QtGui.QPen(QtGui.QColor("#89b4fa"), 2),
                             QtGui.QBrush(QtGui.QColor(70, 130, 180)))
        rect.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        rect.setData(0, tid)
        rect.setToolTip(tip)

        txt = scene.addText(title)
        txt.setDefaultTextColor(QtGui.QColor("#cdd6f4"))
        f = txt.font();
        f.setPointSize(9);
        f.setBold(True)
        txt.setFont(f)
        txt.setPos(x + 8, y + 6)

        dtx = scene.addText(f"{sd.toString('dd.MM.yyyy')} → {ed.toString('dd.MM.yyyy')}")
        dtx.setDefaultTextColor(QtGui.QColor("#a6adc8"))
        dtx.setFont(QtGui.QFont("Segoe UI", 8))
        dtx.setPos(x + 8, y + 22)

        y += spacing

    # Отрисовка оси времени
    axis_y = y + 15
    scene.addLine(axis_start_x, axis_y, axis_end_x, axis_y,
                  QtGui.QPen(QtGui.QColor("#585b70"), 2))

    tick_font = QtGui.QFont("Segoe UI", 10)
    fm = QtGui.QFontMetrics(tick_font)

    # Рисуем деления оси
    cur = axis_start
    while cur < axis_end:
        x = axis_start_x + axis_start.daysTo(cur) * px_per_day
        scene.addLine(x, axis_y - 5, x, axis_y + 5, QtGui.QPen(QtGui.QColor("#89b4fa")))
        label = scene.addText(cur.toString("dd.MM"))
        label.setFont(tick_font)
        label.setDefaultTextColor(QtGui.QColor("#bac2de"))
        half = fm.horizontalAdvance("00.00") / 2
        label.setPos(x - half, axis_y + 8)
        cur = cur.addDays(step_days)

    # Последнее деление
    last_txt = axis_end.addDays(-1).toString("dd.MM")
    last_x = axis_end_x
    scene.addLine(last_x, axis_y - 5, last_x, axis_y + 5,
                  QtGui.QPen(QtGui.QColor("#89b4fa")))

    lab2 = scene.addText(last_txt)
    lab2.setFont(tick_font)
    lab2.setDefaultTextColor(QtGui.QColor("#bac2de"))
    last_half = fm.horizontalAdvance(last_txt) / 2
    lab2.setPos(last_x - last_half, axis_y + 8)

    # Устанавливаем размеры сцены
    tail_pad = last_half + 20
    scene_w = max(axis_end_x + tail_pad + right_pad, viewport_w + 1)
    scene.setSceneRect(0, 0, scene_w, axis_y + 60)
