from datetime import datetime

def validate_task(payload: dict):
    title = (payload.get("title") or "").strip()
    s = payload.get("start_date")
    e = payload.get("end_date")

    if not title:
        return False, "Название цели обязательно."

    try:
        sd = datetime.strptime(s, "%Y-%m-%d")
        ed = datetime.strptime(e, "%Y-%m-%d")
    except Exception:
        return False, "Неверный формат дат. Используйте dd.mm.yyyy ."

    if ed < sd:
        return False, "Дата окончания раньше даты начала."

    if not (payload.get("s_text") or payload.get("m_text") or payload.get("a_text") or payload.get("r_text")):
        return False, "Заполните хотя бы один пункт SMART."

    return True, ""
