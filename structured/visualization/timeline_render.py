# visualization/timeline_render.py
from PyQt5 import QtCore, QtGui, QtWidgets

class TimelineRenderer:
    """Рисует диаграмму задач на QGraphicsScene."""
    def __init__(self):
        pass

    def _align_to_step(self, qdate: QtCore.QDate, step_days: int, ceil=False) -> QtCore.QDate:
        epoch = QtCore.QDate(2000, 1, 1)
        days = epoch.daysTo(qdate)
        if ceil:
            k = (days + (step_days - 1)) // step_days
        else:
            k = days // step_days
        return epoch.addDays(k * step_days)

    def _ensure_min_span(self, start_d, end_d, step_days, px_per_day, min_divisions, viewport_width, left_pad, right_pad):
        span_days_min_div = min_divisions * step_days
        needed_px = max(0, viewport_width - (left_pad + right_pad))
        span_days_min_view = int((needed_px / max(px_per_day, 0.001)) + 0.999)
        base_span = start_d.daysTo(end_d)
        span_days = max(base_span, span_days_min_div, span_days_min_view)
        axis_start = start_d
        axis_end = axis_start.addDays(span_days)
        axis_end = self._align_to_step(axis_end, step_days, ceil=True)
        return axis_start, axis_end

    def draw(self, scene: QtWidgets.QGraphicsScene, tasks, step_days: int, viewport_w: int):
        """
        tasks: список словарей {id, title, s_text, m_text, a_text, r_text, start_date, end_date}
        step_days: 1 | 7 | 14 | 30
        """
        # подготовка данных
        parsed = []
        for t in tasks:
            s = t.get("start_date"); e = t.get("end_date")
            if not s or not e:
                continue
            sd = QtCore.QDate.fromString(s, "yyyy-MM-dd")
            ed = QtCore.QDate.fromString(e, "yyyy-MM-dd")
            if not (sd.isValid() and ed.isValid()):
                continue
            tip = (
                f"{t.get('title')}\n"
                f"S: {t.get('s_text') or '-'}\nM: {t.get('m_text') or '-'}\nA: {t.get('a_text') or '-'}\nR: {t.get('r_text') or '-'}\n"
                f"{sd.toString('yyyy-MM-dd')} → {ed.toString('yyyy-MM-dd')}"
            )
            parsed.append((t["id"], t.get("title") or f"Задача {t['id']}", sd, ed, tip))

        if not parsed:
            txt = scene.addText("Нет задач с корректными датами")
            txt.setDefaultTextColor(QtGui.QColor("#cdd6f4"))
            txt.setPos(20, 20)
            scene.setSceneRect(0, 0, 600, 200)
            return

        px_per_day = 3.6 * (30 / step_days)
        left_pad, right_pad = 40, 40
        y = 20
        bar_h = 35
        spacing = 60

        min_task_date = min(p[2] for p in parsed)
        max_task_date = max(p[3] for p in parsed).addDays(1)

        axis_start_date = self._align_to_step(min_task_date, step_days, ceil=False)
        axis_end_date_raw = self._align_to_step(max_task_date, step_days, ceil=True)

        axis_start_date, axis_end_date = self._ensure_min_span(
            axis_start_date, axis_end_date_raw, step_days, px_per_day,
            min_divisions=10, viewport_width=viewport_w,
            left_pad=left_pad, right_pad=right_pad
        )

        total_days_boundary = axis_start_date.daysTo(axis_end_date)
        axis_start_x = left_pad
        axis_end_x = axis_start_x + total_days_boundary * px_per_day

        # блоки задач
        for tid, title, sd, ed, tip in parsed:
            x = axis_start_x + axis_start_date.daysTo(sd) * px_per_day
            w = max(15, sd.daysTo(ed.addDays(1)) * px_per_day)
            rect = scene.addRect(QtCore.QRectF(x, y, w, bar_h),
                                 QtGui.QPen(QtGui.QColor("#89b4fa"), 2),
                                 QtGui.QBrush(QtGui.QColor(70, 130, 180)))
            rect.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
            rect.setData(0, tid)
            rect.setToolTip(tip)

            txt = scene.addText(title)
            txt.setDefaultTextColor(QtGui.QColor("#cdd6f4"))
            f = txt.font(); f.setPointSize(9); f.setBold(True)
            txt.setFont(f)
            txt.setPos(x + 8, y + 6)

            dtx = scene.addText(f"{sd.toString('dd.MM')} → {ed.toString('dd.MM')}")
            dtx.setDefaultTextColor(QtGui.QColor("#a6adc8"))
            dtx.setFont(QtGui.QFont("Segoe UI", 8))
            dtx.setPos(x + 8, y + 22)

            y += spacing

        # ось времени
        axis_y = y + 15
        scene.addLine(axis_start_x, axis_y, axis_end_x, axis_y, QtGui.QPen(QtGui.QColor("#585b70"), 2))

        tick_font = QtGui.QFont("Segoe UI", 10)
        fm = QtGui.QFontMetrics(tick_font)

        current = axis_start_date
        while current < axis_end_date:
            x = axis_start_x + axis_start_date.daysTo(current) * px_per_day
            scene.addLine(x, axis_y - 5, x, axis_y + 5, QtGui.QPen(QtGui.QColor("#89b4fa")))
            lbl = scene.addText(current.toString("dd.MM"))
            lbl.setFont(tick_font)
            lbl.setDefaultTextColor(QtGui.QColor("#bac2de"))
            try:
                half = fm.horizontalAdvance("00.00") / 2
            except AttributeError:
                half = fm.width("00.00") / 2
            lbl.setPos(x - half, axis_y + 8)
            current = current.addDays(step_days)

        last_text = axis_end_date.addDays(-1).toString("dd.MM")
        try:
            last_half = fm.horizontalAdvance(last_text) / 2
        except AttributeError:
            last_half = fm.width(last_text) / 2
        last_x = axis_end_x
        scene.addLine(last_x, axis_y - 5, last_x, axis_y + 5, QtGui.QPen(QtGui.QColor("#89b4fa")))
        last_lbl = scene.addText(last_text)
        last_lbl.setFont(tick_font)
        last_lbl.setDefaultTextColor(QtGui.QColor("#bac2de"))
        last_lbl.setPos(last_x - last_half, axis_y + 8)

        tail_pad = last_half + 20
        scene_w = max(axis_end_x + tail_pad + right_pad, viewport_w + 1)
        scene.setSceneRect(0, 0, scene_w, axis_y + 60)
