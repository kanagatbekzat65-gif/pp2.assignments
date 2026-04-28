-- ============================================================
-- PhoneBook Stored Procedures & Functions (TSIS 1)
-- NOTE: Procedures from Practice 8 (upsert, bulk-insert,
--       paginated query, delete by username/phone) are NOT
--       re-implemented here per the task requirements.
-- ============================================================


-- ------------------------------------------------------------
-- 1. add_phone
--    Adds a phone number (with type) to an existing contact.
-- ------------------------------------------------------------
CREATE OR REPLACE PROCEDURE add_phone(
    p_contact_name VARCHAR,
    p_phone        VARCHAR,
    p_type         VARCHAR DEFAULT 'mobile'
)
LANGUAGE plpgsql AS $$
DECLARE
    v_contact_id INTEGER;
BEGIN
    -- Validate type
    IF p_type NOT IN ('home', 'work', 'mobile') THEN
        RAISE EXCEPTION 'Invalid phone type "%". Allowed: home, work, mobile.', p_type;
    END IF;

    -- Look up the contact
    SELECT id INTO v_contact_id
    FROM   contacts
    WHERE  name = p_contact_name
    LIMIT  1;

    IF v_contact_id IS NULL THEN
        RAISE EXCEPTION 'Contact "%" not found.', p_contact_name;
    END IF;

    -- Avoid exact duplicate (same number + type for same contact)
    IF EXISTS (
        SELECT 1 FROM phones
        WHERE  contact_id = v_contact_id
          AND  phone      = p_phone
          AND  type       = p_type
    ) THEN
        RAISE NOTICE 'Phone "%" (%) already exists for contact "%". Skipped.',
            p_phone, p_type, p_contact_name;
        RETURN;
    END IF;

    INSERT INTO phones (contact_id, phone, type)
    VALUES (v_contact_id, p_phone, p_type);

    RAISE NOTICE 'Added phone "%" (%) to contact "%".',
        p_phone, p_type, p_contact_name;
END;
$$;


-- ------------------------------------------------------------
-- 2. move_to_group
--    Moves a contact to the named group.
--    Creates the group if it does not exist.
-- ------------------------------------------------------------
CREATE OR REPLACE PROCEDURE move_to_group(
    p_contact_name VARCHAR,
    p_group_name   VARCHAR
)
LANGUAGE plpgsql AS $$
DECLARE
    v_contact_id INTEGER;
    v_group_id   INTEGER;
BEGIN
    -- Find (or create) the group
    SELECT id INTO v_group_id
    FROM   groups
    WHERE  name = p_group_name;

    IF v_group_id IS NULL THEN
        INSERT INTO groups (name)
        VALUES (p_group_name)
        RETURNING id INTO v_group_id;
        RAISE NOTICE 'Created new group "%".', p_group_name;
    END IF;

    -- Find the contact
    SELECT id INTO v_contact_id
    FROM   contacts
    WHERE  name = p_contact_name
    LIMIT  1;

    IF v_contact_id IS NULL THEN
        RAISE EXCEPTION 'Contact "%" not found.', p_contact_name;
    END IF;

    -- Update
    UPDATE contacts
    SET    group_id = v_group_id
    WHERE  id       = v_contact_id;

    RAISE NOTICE 'Moved contact "%" to group "%".', p_contact_name, p_group_name;
END;
$$;


-- ------------------------------------------------------------
-- 3. search_contacts
--    Extended pattern search covering: name, email, and ALL
--    phone numbers in the phones table.
--    Returns a result-set of matching contacts (with phones).
-- ------------------------------------------------------------
CREATE OR REPLACE FUNCTION search_contacts(p_query TEXT)
RETURNS TABLE (
    contact_id  INTEGER,
    name        VARCHAR,
    email       VARCHAR,
    birthday    DATE,
    group_name  VARCHAR,
    phones_list TEXT,
    created_at  TIMESTAMP
)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT ON (c.id)
           c.id,
           c.name,
           c.email,
           c.birthday,
           g.name                               AS group_name,
           STRING_AGG(p.phone || ' (' || COALESCE(p.type,'?') || ')',
                      ', ')
               OVER (PARTITION BY c.id)         AS phones_list,
           c.created_at
    FROM   contacts c
    LEFT JOIN groups g  ON g.id = c.group_id
    LEFT JOIN phones p  ON p.contact_id = c.id
    WHERE  c.name  ILIKE '%' || p_query || '%'
        OR c.email ILIKE '%' || p_query || '%'
        OR p.phone ILIKE '%' || p_query || '%'
    ORDER  BY c.id, c.name;
END;
$$;
