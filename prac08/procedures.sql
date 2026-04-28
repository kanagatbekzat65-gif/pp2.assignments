CREATE OR REPLACE PROCEDURE upsert_contact(p_name VARCHAR, p_phone VARCHAR)
LANGUAGE plpgsql AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM phonebook WHERE first_name = p_name) THEN
        UPDATE phonebook SET phone_number = p_phone WHERE first_name = p_name;
        RAISE NOTICE 'Жаңартылды: %', p_name;
    ELSE
        INSERT INTO phonebook(first_name, phone_number) VALUES(p_name, p_phone);
        RAISE NOTICE 'Қосылды: %', p_name;
    END IF;
END;
$$;

CREATE OR REPLACE PROCEDURE insert_many_users(
    p_names  VARCHAR[],
    p_phones VARCHAR[]
)
LANGUAGE plpgsql AS $$
DECLARE
    i       INT;
    v_name  VARCHAR;
    v_phone VARCHAR;
BEGIN
    
    CREATE TEMP TABLE IF NOT EXISTS invalid_contacts (
        first_name   VARCHAR,
        phone_number VARCHAR,
        reason       TEXT
    ) ON COMMIT DELETE ROWS;

    FOR i IN 1 .. array_length(p_names, 1) LOOP
        v_name  := p_names[i];
        v_phone := p_phones[i];

        
        IF v_phone !~ '^\+?[\d\s\-]{7,15}$' THEN
            INSERT INTO invalid_contacts(first_name, phone_number, reason)
            VALUES (v_name, v_phone, 'Қате телефон форматы');
            RAISE NOTICE 'Қате формат — өткізіп жіберілді: % / %', v_name, v_phone;

        ELSIF EXISTS (SELECT 1 FROM phonebook WHERE first_name = v_name) THEN
            
            UPDATE phonebook SET phone_number = v_phone WHERE first_name = v_name;
            RAISE NOTICE 'Жаңартылды: %', v_name;

        ELSE
            
            INSERT INTO phonebook(first_name, phone_number) VALUES(v_name, v_phone);
            RAISE NOTICE 'Қосылды: %', v_name;
        END IF;
    END LOOP;
END;
$$;


CREATE OR REPLACE PROCEDURE delete_contact(p_name VARCHAR DEFAULT NULL,
                                           p_phone VARCHAR DEFAULT NULL)
LANGUAGE plpgsql AS $$
DECLARE
    deleted_count INT;
BEGIN
    DELETE FROM phonebook
    WHERE (p_name  IS NOT NULL AND first_name   = p_name)
       OR (p_phone IS NOT NULL AND phone_number = p_phone);

    GET DIAGNOSTICS deleted_count = ROW_COUNT;

    IF deleted_count = 0 THEN
        RAISE NOTICE 'Контакт табылмады.';
    ELSE
        RAISE NOTICE '% контакт өшірілді.', deleted_count;
    END IF;
END;
$$;



