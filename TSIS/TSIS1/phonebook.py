#!/usr/bin/env python3
"""
phonebook.py — PhoneBook Extended (TSIS 1)

Features added on top of Practice 7-8:
  • Extended schema  : phones table, groups table, email, birthday
  • Console filters  : by group, by email, sort by name/birthday/date
  • Paginated nav    : next / prev / quit console loop
  • Export to JSON   : full contact dump with phones + group
  • Import from JSON : with duplicate handling (skip / overwrite)
  • Extended CSV     : handles email, birthday, group, phone type
  • Procedures       : add_phone, move_to_group
  • Function         : search_contacts (name + email + all phones)

NOT re-implemented (already in Practice 7-8):
  CRUD, CSV import (basic), pattern-search, upsert, bulk-insert,
  paginated DB function, delete by username/phone.
"""

import csv
import json
import sys
from datetime import date, datetime
from pathlib import Path

import psycopg2
import psycopg2.extras

from config import DB_CONFIG, PAGE_SIZE
from connect import get_connection, init_schema

# ─────────────────────────────────────────────────────────────
# Utility helpers
# ─────────────────────────────────────────────────────────────

def _fmt_row(row: dict) -> str:
    """Return a single-line display string for a contact row."""
    phones = row.get("phones_list") or row.get("phones") or "—"
    bday   = row.get("birthday") or "—"
    email  = row.get("email") or "—"
    group  = row.get("group_name") or "—"
    return (
        f"  [{row.get('contact_id') or row.get('id')}] "
        f"{row['name']} | {email} | bday: {bday} | "
        f"group: {group} | phones: {phones}"
    )


def _input(prompt: str) -> str:
    return input(prompt).strip()


def _choose(prompt: str, choices: list[str]) -> str:
    """Keep asking until the user enters a valid choice."""
    while True:
        val = _input(f"{prompt} [{'/'.join(choices)}]: ").lower()
        if val in choices:
            return val
        print(f"  Please enter one of: {choices}")


# ─────────────────────────────────────────────────────────────
# 3.1  Add a contact (extended model)
# ─────────────────────────────────────────────────────────────

def add_contact_interactive():
    """Console wizard for adding a new contact with the extended model."""
    print("\n── Add Contact ──────────────────────────────────")
    name     = _input("Name          : ")
    email    = _input("Email         : ") or None
    birthday = _input("Birthday (YYYY-MM-DD, blank to skip): ") or None
    group    = _input("Group (Family/Work/Friend/Other, blank=Other): ") or "Other"

    phones = []
    print("Enter phone numbers (blank name to stop):")
    while True:
        phone = _input("  Phone number (blank to stop): ")
        if not phone:
            break
        ptype = _choose("  Type", ["home", "work", "mobile"])
        phones.append((phone, ptype))

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Ensure group exists
            cur.execute(
                "INSERT INTO groups (name) VALUES (%s) ON CONFLICT (name) DO NOTHING",
                (group,)
            )
            cur.execute("SELECT id FROM groups WHERE name = %s", (group,))
            group_id = cur.fetchone()[0]

            # Insert contact
            cur.execute(
                """
                INSERT INTO contacts (name, email, birthday, group_id)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (name, email, birthday, group_id)
            )
            contact_id = cur.fetchone()[0]

            # Insert phones
            for ph, pt in phones:
                cur.execute(
                    "INSERT INTO phones (contact_id, phone, type) VALUES (%s, %s, %s)",
                    (contact_id, ph, pt)
                )
        conn.commit()
        print(f"  ✓ Contact '{name}' added (id={contact_id}).")
    except Exception as exc:
        conn.rollback()
        print(f"  ✗ Error: {exc}")
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────
# 3.2  Advanced Console Search & Filter
# ─────────────────────────────────────────────────────────────

def _contacts_query(
    group_name: str | None = None,
    email_query: str | None = None,
    sort_by: str = "name",      # name | birthday | date
    limit: int = PAGE_SIZE,
    offset: int = 0,
) -> list[dict]:
    """
    Flexible query returning contacts with their phones aggregated.
    Supports group filter, email partial match, and sort order.
    """
    sort_map = {
        "name":     "c.name ASC",
        "birthday": "c.birthday ASC NULLS LAST",
        "date":     "c.created_at DESC",
    }
    order = sort_map.get(sort_by, "c.name ASC")

    sql = f"""
        SELECT
            c.id            AS contact_id,
            c.name,
            c.email,
            c.birthday,
            g.name          AS group_name,
            STRING_AGG(p.phone || ' (' || COALESCE(p.type,'?') || ')',
                       ', ' ORDER BY p.id) AS phones_list,
            c.created_at
        FROM   contacts c
        LEFT JOIN groups g ON g.id = c.group_id
        LEFT JOIN phones p ON p.contact_id = c.id
        WHERE  (%s IS NULL OR g.name = %s)
          AND  (%s IS NULL OR c.email ILIKE '%%' || %s || '%%')
        GROUP BY c.id, c.name, c.email, c.birthday, g.name, c.created_at
        ORDER BY {order}
        LIMIT  %s OFFSET %s
    """
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, (
                group_name, group_name,
                email_query, email_query,
                limit, offset,
            ))
            return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def filter_by_group():
    """Show contacts filtered by a chosen group."""
    print("\n── Filter by Group ──────────────────────────────")
    group = _input("Group name (Family/Work/Friend/Other): ")
    sort  = _choose("Sort by", ["name", "birthday", "date"])
    rows  = _contacts_query(group_name=group, sort_by=sort)
    if not rows:
        print("  No contacts found in that group.")
    else:
        for r in rows:
            print(_fmt_row(r))


def search_by_email():
    """Partial email search using Python-side query."""
    print("\n── Search by Email ──────────────────────────────")
    query = _input("Email fragment: ")
    sort  = _choose("Sort by", ["name", "birthday", "date"])
    rows  = _contacts_query(email_query=query, sort_by=sort)
    if not rows:
        print("  No contacts found.")
    else:
        for r in rows:
            print(_fmt_row(r))


def paginated_navigation():
    """
    Console loop wrapping the existing paginated DB query.
    Uses the paginated_contacts function from Practice 8.
    Navigates with next / prev / quit.
    """
    print("\n── Paginated Contact Browser ────────────────────")
    sort  = _choose("Sort by", ["name", "birthday", "date"])
    group = _input("Filter by group (blank = all): ") or None
    email = _input("Filter by email fragment (blank = all): ") or None

    page = 0
    while True:
        offset = page * PAGE_SIZE
        rows   = _contacts_query(
            group_name=group, email_query=email,
            sort_by=sort, limit=PAGE_SIZE, offset=offset
        )
        if not rows and page == 0:
            print("  No contacts found.")
            return

        print(f"\n  — Page {page + 1} —")
        if not rows:
            print("  (no more results)")
        else:
            for r in rows:
                print(_fmt_row(r))

        nav = _choose("Navigate", ["next", "prev", "quit"])
        if nav == "quit":
            return
        elif nav == "next":
            if rows:
                page += 1
            else:
                print("  Already at the last page.")
        elif nav == "prev":
            if page > 0:
                page -= 1
            else:
                print("  Already at the first page.")


# ─────────────────────────────────────────────────────────────
# 3.3  Import / Export
# ─────────────────────────────────────────────────────────────

def export_to_json(filepath: str = "contacts_export.json"):
    """Export all contacts (with phones and group) to JSON."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT
                    c.id, c.name, c.email,
                    c.birthday::TEXT AS birthday,
                    g.name           AS group_name,
                    c.created_at::TEXT AS created_at
                FROM   contacts c
                LEFT JOIN groups g ON g.id = c.group_id
                ORDER BY c.id
            """)
            contacts = [dict(r) for r in cur.fetchall()]

            for contact in contacts:
                cur.execute(
                    "SELECT phone, type FROM phones WHERE contact_id = %s ORDER BY id",
                    (contact["id"],)
                )
                contact["phones"] = [dict(p) for p in cur.fetchall()]

        path = Path(filepath)
        path.write_text(
            json.dumps(contacts, indent=2, default=str),
            encoding="utf-8"
        )
        print(f"  ✓ Exported {len(contacts)} contacts to '{filepath}'.")
    finally:
        conn.close()


def import_from_json(filepath: str = "contacts_export.json"):
    """
    Import contacts from a JSON file.
    On duplicate name, ask the user: skip or overwrite.
    """
    path = Path(filepath)
    if not path.exists():
        print(f"  ✗ File '{filepath}' not found.")
        return

    contacts = json.loads(path.read_text(encoding="utf-8"))
    print(f"\n── JSON Import: {len(contacts)} records from '{filepath}' ──")

    conn = get_connection()
    try:
        for record in contacts:
            name     = record.get("name", "").strip()
            email    = record.get("email") or None
            birthday = record.get("birthday") or None
            group    = record.get("group_name") or "Other"
            phones   = record.get("phones", [])   # [{phone, type}, ...]

            if not name:
                print("  ⚠ Skipping record with empty name.")
                continue

            with conn.cursor() as cur:
                # Check for duplicate
                cur.execute("SELECT id FROM contacts WHERE name = %s LIMIT 1", (name,))
                existing = cur.fetchone()

                if existing:
                    action = _choose(
                        f"  Contact '{name}' already exists. Action",
                        ["skip", "overwrite"]
                    )
                    if action == "skip":
                        print(f"  → Skipped '{name}'.")
                        continue

                    contact_id = existing[0]
                    # Overwrite: update contact fields and replace phones
                    cur.execute(
                        "UPDATE contacts SET email=%s, birthday=%s WHERE id=%s",
                        (email, birthday, contact_id)
                    )
                    cur.execute("DELETE FROM phones WHERE contact_id=%s", (contact_id,))
                    print(f"  → Overwriting '{name}'.")
                else:
                    # Ensure group
                    cur.execute(
                        "INSERT INTO groups (name) VALUES (%s) ON CONFLICT (name) DO NOTHING",
                        (group,)
                    )
                    cur.execute("SELECT id FROM groups WHERE name = %s", (group,))
                    group_id = cur.fetchone()[0]

                    cur.execute(
                        """
                        INSERT INTO contacts (name, email, birthday, group_id)
                        VALUES (%s, %s, %s, %s) RETURNING id
                        """,
                        (name, email, birthday, group_id)
                    )
                    contact_id = cur.fetchone()[0]
                    print(f"  → Inserted '{name}'.")

                # Re-insert phones
                for ph in phones:
                    ptype = ph.get("type", "mobile")
                    if ptype not in ("home", "work", "mobile"):
                        ptype = "mobile"
                    cur.execute(
                        "INSERT INTO phones (contact_id, phone, type) VALUES (%s, %s, %s)",
                        (contact_id, ph.get("phone"), ptype)
                    )

            conn.commit()

        print("  ✓ JSON import complete.")
    except Exception as exc:
        conn.rollback()
        print(f"  ✗ Import error: {exc}")
    finally:
        conn.close()


def import_csv_extended(filepath: str = "contacts.csv"):
    """
    Extended CSV importer supporting:
      name, email, birthday, group, phone, phone_type
    One row = one phone number; multiple rows for the same
    contact name add multiple phones to the same contact.
    """
    path = Path(filepath)
    if not path.exists():
        print(f"  ✗ File '{filepath}' not found.")
        return

    required_fields = {"name", "phone"}
    inserted = skipped = 0

    conn = get_connection()
    try:
        with open(filepath, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            if not required_fields.issubset(set(reader.fieldnames or [])):
                print(f"  ✗ CSV must contain at least: {required_fields}")
                return

            for row in reader:
                name     = (row.get("name") or "").strip()
                phone    = (row.get("phone") or "").strip()
                email    = (row.get("email") or "").strip() or None
                birthday = (row.get("birthday") or "").strip() or None
                group    = (row.get("group") or "Other").strip()
                ptype    = (row.get("phone_type") or "mobile").strip().lower()

                if not name or not phone:
                    print(f"  ⚠ Skipping row — missing name or phone: {row}")
                    skipped += 1
                    continue

                if ptype not in ("home", "work", "mobile"):
                    ptype = "mobile"

                with conn.cursor() as cur:
                    # Ensure group
                    cur.execute(
                        "INSERT INTO groups (name) VALUES (%s) ON CONFLICT (name) DO NOTHING",
                        (group,)
                    )
                    cur.execute("SELECT id FROM groups WHERE name = %s", (group,))
                    group_id = cur.fetchone()[0]

                    # Upsert contact (by name)
                    cur.execute("""
                        INSERT INTO contacts (name, email, birthday, group_id)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (name) DO UPDATE
                            SET email    = EXCLUDED.email,
                                birthday = EXCLUDED.birthday,
                                group_id = EXCLUDED.group_id
                        RETURNING id
                    """, (name, email, birthday, group_id))
                    contact_id = cur.fetchone()[0]

                    # Add phone if not duplicate
                    cur.execute("""
                        INSERT INTO phones (contact_id, phone, type)
                        SELECT %s, %s, %s
                        WHERE NOT EXISTS (
                            SELECT 1 FROM phones
                            WHERE contact_id = %s AND phone = %s AND type = %s
                        )
                    """, (contact_id, phone, ptype, contact_id, phone, ptype))

                conn.commit()
                inserted += 1

        print(f"  ✓ CSV import done — {inserted} processed, {skipped} skipped.")
    except Exception as exc:
        conn.rollback()
        print(f"  ✗ CSV import error: {exc}")
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────
# 3.4  Stored Procedure wrappers
# ─────────────────────────────────────────────────────────────

def call_add_phone():
    """Console wrapper for the add_phone stored procedure."""
    print("\n── Add Phone Number ─────────────────────────────")
    contact_name = _input("Contact name : ")
    phone        = _input("Phone number : ")
    ptype        = _choose("Type", ["home", "work", "mobile"])

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "CALL add_phone(%s, %s, %s)",
                (contact_name, phone, ptype)
            )
        conn.commit()
        print(f"  ✓ Procedure executed.")
    except Exception as exc:
        conn.rollback()
        print(f"  ✗ Error: {exc}")
    finally:
        conn.close()


def call_move_to_group():
    """Console wrapper for the move_to_group stored procedure."""
    print("\n── Move Contact to Group ────────────────────────")
    contact_name = _input("Contact name : ")
    group_name   = _input("Group name   : ")

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "CALL move_to_group(%s, %s)",
                (contact_name, group_name)
            )
        conn.commit()
        print(f"  ✓ Procedure executed.")
    except Exception as exc:
        conn.rollback()
        print(f"  ✗ Error: {exc}")
    finally:
        conn.close()


def call_search_contacts():
    """Console wrapper for the search_contacts DB function."""
    print("\n── Search Contacts (name + email + phones) ──────")
    query = _input("Search query : ")

    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM search_contacts(%s)", (query,))
            rows = cur.fetchall()

        if not rows:
            print("  No matches found.")
        else:
            for r in rows:
                print(_fmt_row(dict(r)))
    except Exception as exc:
        print(f"  ✗ Error: {exc}")
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────
# Main menu
# ─────────────────────────────────────────────────────────────

MENU = """
╔══════════════════════════════════════════════╗
║         PhoneBook Extended  (TSIS 1)         ║
╠══════════════════════════════════════════════╣
║  Contact Management                          ║
║    1. Add contact (extended model)           ║
║    2. Add phone to existing contact          ║
║    3. Move contact to group                  ║
╠══════════════════════════════════════════════╣
║  Search & Filter                             ║
║    4. Search (name / email / phone)          ║
║    5. Filter by group                        ║
║    6. Search by email                        ║
║    7. Browse with pagination (next/prev)     ║
╠══════════════════════════════════════════════╣
║  Import / Export                             ║
║    8. Export all contacts to JSON            ║
║    9. Import contacts from JSON              ║
║   10. Import from extended CSV               ║
╠══════════════════════════════════════════════╣
║    0. Exit                                   ║
╚══════════════════════════════════════════════╝
"""

HANDLERS = {
    "1":  add_contact_interactive,
    "2":  call_add_phone,
    "3":  call_move_to_group,
    "4":  call_search_contacts,
    "5":  filter_by_group,
    "6":  search_by_email,
    "7":  paginated_navigation,
    "8":  lambda: export_to_json(_input("Output file [contacts_export.json]: ") or "contacts_export.json"),
    "9":  lambda: import_from_json(_input("Input file [contacts_export.json]: ") or "contacts_export.json"),
    "10": lambda: import_csv_extended(_input("CSV file [contacts.csv]: ") or "contacts.csv"),
}


def main():
    print("Initializing database schema …")
    try:
        init_schema()
    except Exception:
        print("Could not apply schema. Check DB_CONFIG in config.py and retry.")
        sys.exit(1)

    while True:
        print(MENU)
        choice = _input("Choose an option: ")
        if choice == "0":
            print("Goodbye!")
            break
        handler = HANDLERS.get(choice)
        if handler:
            handler()
        else:
            print("  Invalid option — try again.")


if __name__ == "__main__":
    main()
