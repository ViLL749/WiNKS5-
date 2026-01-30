
import sys
import os

sys.path.append(os.getcwd())

from validator import validate_task



def run_tests():
    print("=== ЗАПУСК ТЕСТИРОВАНИЯ ===\n")

    # ТЕСТ-КЕЙС 1: Проверка допустимых значений
    print("Тест-кейс 1: Проверка допустимых значений")
    payload_1 = {
        "title": "Разработка сайта",
        "start_date": "2023-10-01",
        "end_date": "2023-10-10",
        "s_text": "Сделать лендинг"
    }
    result_1, msg_1 = validate_task(payload_1)

    expected_1 = True
    status_1 = "Pass" if result_1 == expected_1 else "Fail"

    print(f"Входные данные: {payload_1['title']}, {payload_1['start_date']} -> {payload_1['end_date']}")
    print(f"Фактический результат: {result_1} (Сообщение: '{msg_1}')")
    print(f"Статус: {status_1}\n")

    # ТЕСТ-КЕЙС 2: Проверка граничных значений (Равенство дат)
    print("Тест-кейс 2: Проверка граничных значений (start == end)")
    payload_2 = {
        "title": "Задача на один день",
        "start_date": "2023-10-01",
        "end_date": "2023-10-01",
        "m_text": "Измеримый результат"
    }
    result_2, msg_2 = validate_task(payload_2)

    expected_2 = True
    status_2 = "Pass" if result_2 == expected_2 else "Fail"

    print(f"Входные данные: {payload_2['start_date']} == {payload_2['end_date']}")
    print(f"Фактический результат: {result_2} (Сообщение: '{msg_2}')")
    print(f"Статус: {status_2}\n")

    # ТЕСТ-КЕЙС 3: Проверка недопустимых значений
    print("Тест-кейс 3: Проверка недопустимых значений (Пустой Title)")
    payload_3 = {
        "title": "",  # ПУСТО
        "start_date": "2023-10-01",
        "end_date": "2023-10-05",
        "a_text": "Достижимая цель"
    }
    result_3, msg_3 = validate_task(payload_3)

    expected_3 = False
    status_3 = "Pass" if result_3 == expected_3 else "Fail"

    print(f"Входные данные: title='{payload_3['title']}'")
    print(f"Фактический результат: {result_3} (Сообщение: '{msg_3}')")
    print(f"Статус: {status_3}\n")

    # Итог
    passed_count = [status_1, status_2, status_3].count("Pass")
    print(f"=== ИТОГ: Пройдено {passed_count} из 3 тестов ===")


if __name__ == "__main__":
    run_tests()