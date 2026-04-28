# PhoneBook Extended — TSIS 1

Extended PhoneBook application building on Practice 7 and Practice 8.

## Repository Structure

```
TSIS1/
├── phonebook.py      # Main application (all TSIS-1 features)
├── config.py         # DB connection settings & page size
├── connect.py        # Connection helper + schema init
├── schema.sql        # Extended DB schema (phones, groups, email, birthday)
├── procedures.sql    # New PL/pgSQL procedures and function
└── contacts.csv      # Sample CSV with extended fields
```

## What Was Added (TSIS 1 only)

| Feature | Where |
|---|---|
| `phones` table (1-to-many, with type) | `schema.sql` |
| `groups` table + FK in contacts | `schema.sql` |
| `email` and `birthday` fields | `schema.sql` |
| Filter by group (console) | `phonebook.py` → `filter_by_group()` |
| Search by email partial match | `phonebook.py` → `search_by_email()` |
| Sort by name / birthday / date | `phonebook.py` → `_contacts_query()` |
| Paginated next/prev/quit loop | `phonebook.py` → `paginated_navigation()` |
| Export all contacts → JSON | `phonebook.py` → `export_to_json()` |
| Import from JSON + skip/overwrite | `phonebook.py` → `import_from_json()` |
| Extended CSV (email, birthday, group, type) | `phonebook.py` → `import_csv_extended()` |
| Procedure `add_phone` | `procedures.sql` |
| Procedure `move_to_group` | `procedures.sql` |
| Function `search_contacts` (name+email+phones) | `procedures.sql` |

> **Not re-implemented:** Basic CRUD, original CSV import, pattern-search, upsert, bulk-insert, paginated DB function, delete by username/phone — all remain from Practice 7–8.

## Setup

### 1. Prerequisites
- PostgreSQL 13+
- Python 3.11+
- `psycopg2` (`pip install psycopg2-binary`)

### 2. Database
```sql
-- In psql:
CREATE DATABASE phonebook;
```

### 3. Configuration
Edit `config.py`:
```python
DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "dbname":   "phonebook",
    "user":     "postgres",
    "password": "your_password",
}
```

### 4. Run
```bash
python phonebook.py
```

The application automatically applies `schema.sql` and `procedures.sql` on first run (idempotent — safe to restart).

## CSV Format

```
name,email,birthday,group,phone,phone_type
Alice Johnson,alice@gmail.com,1990-04-15,Friend,+1-555-0101,mobile
Alice Johnson,alice@gmail.com,1990-04-15,Friend,+1-555-0102,home
```

One row = one phone number. Multiple rows with the same name add multiple phones to the same contact.

## JSON Format

```json
[
  {
    "id": 1,
    "name": "Alice Johnson",
    "email": "alice@gmail.com",
    "birthday": "1990-04-15",
    "group_name": "Friend",
    "phones": [
      {"phone": "+1-555-0101", "type": "mobile"},
      {"phone": "+1-555-0102", "type": "home"}
    ]
  }
]
```

## Stored Procedures

```sql
-- Add a phone to an existing contact
CALL add_phone('Alice Johnson', '+1-555-9999', 'work');

-- Move a contact to a group (creates group if missing)
CALL move_to_group('Alice Johnson', 'VIP');

-- Search across name, email, and all phones
SELECT * FROM search_contacts('gmail');
```
