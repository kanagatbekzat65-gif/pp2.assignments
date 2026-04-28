import psycopg2
from prac08.config import load_config
import csv 

def insert_from_csv(file_path):
    sql = "INSERT INTO phonebook(first_name, phone_number) VALUES(%s, %s)"
    config = load_config()
    try:
        with psycopg2.connect(**config) as conn:
            with conn.cursor() as cur:
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    next(reader)  
                    for row in reader:
                        cur.execute(sql, row)
                conn.commit()
                print("CSV-ден мәліметтер жүктелді!")
    except Exception as e:
        print(f"CSV қатесі: {e}")

def create_contact(name, phone):
    sql = "INSERT INTO phonebook(first_name, phone_number) VALUES(%s, %s)"
    config = load_config()
    
    try:
        with psycopg2.connect(**config) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (name, phone))
                conn.commit()
                print("Контакт сәтті қосылды!")
    except Exception as e:
        print(f"Қате шықты: {e}")

if __name__ == "__main__":
    create_contact('Alibi', '87071112233')

def update_contact(name, new_phone):
    sql = "UPDATE phonebook SET phone_number = %s WHERE first_name = %s"
    config = load_config()
    try:
        with psycopg2.connect(**config) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (new_phone, name))
                conn.commit()
                print(f"{name} үшін жаңа нөмір сақталды.")
    except Exception as e:
        print(f"Жаңарту қатесі: {e}")

def search_contacts(pattern):
    
    sql = "SELECT * FROM phonebook WHERE first_name ILIKE %s OR phone_number LIKE %s"
    config = load_config()
    try:
        with psycopg2.connect(**config) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (f'%{pattern}%', f'{pattern}%'))
                rows = cur.fetchall()
                for row in rows:
                    print(row)
    except Exception as e:
        print(f"Іздеу қатесі: {e}")

def delete_contact(name_or_phone):
    sql = "DELETE FROM phonebook WHERE first_name = %s OR phone_number = %s"
    config = load_config()
    try:
        with psycopg2.connect(**config) as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (name_or_phone, name_or_phone))
                conn.commit()
                print("Контакт өшірілді.")
    except Exception as e:
        print(f"Өшіру қатесі: {e}")
    
def main():
    while True:
        print("\n PhoneBook")
        print("1. Контакт қосу")
        print("2. CSV-ден жүктеу")
        print("3. Іздеу")
        print("4. Нөмірді жаңарту")
        print("5. Өшіру")
        print("0. Шығу")
        
        choice = input("Таңдау жасаңыз: ")
        
        if choice == '1':
            create_contact(input("Аты: "), input("Нөмірі: "))
        elif choice == '2':
            insert_from_csv('contacts.csv')
        elif choice == '3':
            search_contacts(input("Іздеу (аты немесе нөмір басы): "))
        elif choice == '4':
            update_contact(input("Кімнің нөмірін өзгертеміз?: "), input("Жаңа нөмір: "))
        elif choice == '5':
            delete_contact(input("Өшіретін адамның аты немесе нөмірі: "))
        elif choice == '0':
            break

if __name__ == "__main__":
    main()
    
