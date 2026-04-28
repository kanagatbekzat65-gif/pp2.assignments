import psycopg2
import csv
from config import load_config



def get_connection():
    return psycopg2.connect(**load_config())



def insert_from_csv(file_path):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                names, phones = [], []
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    next(reader)  
                    for row in reader:
                        names.append(row[0])
                        phones.append(row[1])

                
                cur.execute(
                    "CALL insert_many_users(%s::VARCHAR[], %s::VARCHAR[])",
                    (names, phones)
                )
                
                cur.execute("SELECT * FROM invalid_contacts")
                bad = cur.fetchall()
                if bad:
                    print("\nҚате форматтағы контакттар:")
                    for row in bad:
                        print(f"  Аты: {row[0]}, Телефон: {row[1]}, Себебі: {row[2]}")
                else:
                    print("Барлық контакттар сәтті жүктелді!")
            conn.commit()
    except Exception as e:
        print(f"CSV қатесі: {e}")



def upsert_contact(name, phone):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("CALL upsert_contact(%s, %s)", (name, phone))
            conn.commit()
            print("Операция сәтті орындалды!")
    except Exception as e:
        print(f"Upsert қатесі: {e}")



def search_contacts(pattern):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM get_contacts_by_pattern(%s)", (pattern,)
                )
                rows = cur.fetchall()
                if rows:
                    print(f"\n{'ID':<5} {'Аты':<20} {'Телефон':<15}")
                    print("-" * 42)
                    for row in rows:
                        print(f"{row[0]:<5} {row[1]:<20} {row[2]:<15}")
                else:
                    print("Контакт табылмады.")
    except Exception as e:
        print(f"Іздеу қатесі: {e}")



def show_paginated(page=1, page_size=5):
    offset = (page - 1) * page_size
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT * FROM get_contacts_paginated(%s, %s)",
                    (page_size, offset)
                )
                rows = cur.fetchall()
                if rows:
                    print(f"\n── {page}-бет ──────────────────────────")
                    print(f"{'ID':<5} {'Аты':<20} {'Телефон':<15}")
                    print("-" * 42)
                    for row in rows:
                        print(f"{row[0]:<5} {row[1]:<20} {row[2]:<15}")
                else:
                    print("Бұл бетте деректер жоқ.")
    except Exception as e:
        print(f"Pagination қатесі: {e}")



def delete_contact(name_or_phone):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                
                if name_or_phone.replace('+', '').replace(' ', '').isdigit():
                    cur.execute(
                        "CALL delete_contact(p_phone := %s)", (name_or_phone,)
                    )
                else:
                    cur.execute(
                        "CALL delete_contact(p_name := %s)", (name_or_phone,)
                    )
            conn.commit()
            print("Өшіру операциясы орындалды.")
    except Exception as e:
        print(f"Өшіру қатесі: {e}")


def main():
    while True:
        print("\n╔══════════════════════════╗")
        print("║      PhoneBook Menu      ║")
        print("╠══════════════════════════╣")
        print("║ 1. Контакт қосу / жаңарту║")
        print("║ 2. CSV-ден жүктеу        ║")
        print("║ 3. Іздеу (pattern)       ║")
        print("║ 4. Беттеп қарау          ║")
        print("║ 5. Контакт өшіру         ║")
        print("║ 0. Шығу                  ║")
        print("╚══════════════════════════╝")

        choice = input("Таңдауыңыз: ").strip()

        if choice == '1':
            name  = input("Аты: ").strip()
            phone = input("Телефон: ").strip()
            upsert_contact(name, phone)
        elif choice == '2':
            insert_from_csv('contacts.csv')
        elif choice == '3':
            pattern = input("Іздеу сөзі (аты немесе нөмір): ").strip()
            search_contacts(pattern)
        elif choice == '4':
            try:
                page = int(input("Бет нөмірі (1-ден бастап): ").strip())
            except ValueError:
                page = 1
            show_paginated(page)
        elif choice == '5':
            val = input("Аты немесе телефоны: ").strip()
            delete_contact(val)
        elif choice == '0':
            print("Сау болыңыз!")
            break
        else:
            print("Қате таңдау, қайта көріңіз.")


if __name__ == "__main__":
    main()
