CREATE OR REPLACE FUNCTION get_contacts_by_pattern(p TEXT)
RETURNS TABLE(id INT, first_name VARCHAR, phone_number VARCHAR) AS $$
BEGIN
    RETURN QUERY
        SELECT c.id, c.first_name, c.phone_number
        FROM phonebook c
        WHERE c.first_name ILIKE '%' || p || '%'
           OR c.phone_number ILIKE '%' || p || '%';
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION get_contacts_paginated(lim INT, off INT)
RETURNS TABLE(id INT, first_name VARCHAR, phone_number VARCHAR) AS $$
BEGIN
    RETURN QUERY
        SELECT c.id, c.first_name, c.phone_number
        FROM phonebook c
        ORDER BY c.id
        LIMIT lim OFFSET off;
END;
$$ LANGUAGE plpgsql;

