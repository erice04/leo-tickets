#!/usr/bin/env python3
"""Import legacy flat-file data into PostgreSQL."""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from app.auth.permissions import Role
from app.extensions import db
from app.models import AllowedEmail, EventSettings, ScanLog, YaleStudent
from app.services.users import create_or_update_user


def _read_lines(path):
    if not os.path.isfile(path):
        return []
    with open(path, encoding="utf-8") as file:
        return [line.strip() for line in file if line.strip()]


def _resolve_data_file(data_dir: str, filename: str) -> str:
    candidates = [filename]
    if filename.endswith(".txt"):
        candidates.append(filename.replace(".txt", ".example.txt"))

    for base in (data_dir, os.path.join("archive", "data")):
        for name in candidates:
            path = os.path.join(base, name)
            if os.path.isfile(path):
                return path
    return os.path.join(data_dir, filename)


def seed_event_settings(data_dir):
    title_path = os.path.join(data_dir, "ticket_info.txt")
    status_path = os.path.join(data_dir, "status.json")

    title = "Event"
    if os.path.isfile(title_path):
        with open(title_path, encoding="utf-8") as file:
            title = file.read().strip() or title

    image_visible = True
    if os.path.isfile(status_path):
        with open(status_path, encoding="utf-8") as file:
            image_visible = json.load(file).get("image_visible", True)

    settings = EventSettings.get()
    settings.title = title
    settings.image_visible = image_visible
    db.session.commit()
    print(f"Event settings: title={title!r}, image_visible={image_visible}")


def seed_allowed_emails(data_dir):
    path = _resolve_data_file(data_dir, "emails.txt")
    emails = [line.lower() for line in _read_lines(path)]
    AllowedEmail.query.delete()
    for email in emails:
        db.session.add(AllowedEmail(email=email))
    db.session.commit()
    print(f"Allowed emails: {len(emails)}")


def seed_staff_users(data_dir):
    path = _resolve_data_file(data_dir, "admin.txt")
    emails = [line.lower() for line in _read_lines(path)]
    for email in emails:
        create_or_update_user(email, [Role.ADMIN.value])
    print(f"Staff users (admin role): {len(emails)}")


def seed_yale_directory(data_dir):
    path = _resolve_data_file(data_dir, "yale_directory.txt")
    if not os.path.isfile(path):
        print("No yale_directory.txt found, skipping.")
        return

    YaleStudent.query.delete()
    db.session.commit()

    batch = []
    batch_size = 1000
    count = 0
    seen: set[str] = set()

    with open(path, encoding="utf-8") as file:
        for line in file:
            fields = line.strip().split("\t")
            if len(fields) < 5:
                continue
            email = fields[0].strip().lower()
            if not email or email == "none" or email in seen:
                continue
            seen.add(email)

            while len(fields) < 8:
                fields.append(None)

            batch.append(
                YaleStudent(
                    email=email,
                    name=fields[1] if fields[1] != "None" else None,
                    image_url=fields[2] if fields[2] != "None" else None,
                    year=fields[3] if fields[3] != "None" else None,
                    netid=fields[4] if fields[4] != "None" else None,
                    birthday=fields[5] if fields[5] != "None" else None,
                    major=fields[6] if fields[6] != "None" else None,
                    address=fields[7] if fields[7] != "None" else None,
                )
            )
            count += 1

            if len(batch) >= batch_size:
                db.session.bulk_save_objects(batch)
                db.session.commit()
                batch.clear()
                print(f"  ... {count} students")

    if batch:
        db.session.bulk_save_objects(batch)
        db.session.commit()

    print(f"Yale directory: {count} students")


def seed_scan_logs_from_excel(data_dir):
    excel_path = _resolve_data_file(data_dir, "scanner_log.xlsx")
    if not os.path.isfile(excel_path):
        print("No scanner_log.xlsx found, skipping scan log import.")
        return

    try:
        import pandas as pd
    except ImportError:
        print("pandas not installed; skipping scanner_log.xlsx import.")
        return

    df = pd.read_excel(excel_path)
    ScanLog.query.delete()

    for _, row in df.iterrows():
        email = str(row.get("Data", "")).strip().lower()
        timestamp = row.get("Timestamp")
        if not email:
            continue
        if hasattr(timestamp, "to_pydatetime"):
            timestamp = timestamp.to_pydatetime()
        db.session.add(ScanLog(email=email, scanned_at=timestamp))

    db.session.commit()
    print(f"Scan logs: {len(df)} rows imported")


def main():
    parser = argparse.ArgumentParser(description="Seed PostgreSQL from legacy data files")
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--skip-directory", action="store_true")
    parser.add_argument("--skip-scans", action="store_true")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        db.create_all()
        seed_event_settings(args.data_dir)
        seed_allowed_emails(args.data_dir)
        seed_staff_users(args.data_dir)
        if not args.skip_directory:
            seed_yale_directory(args.data_dir)
        if not args.skip_scans:
            seed_scan_logs_from_excel(args.data_dir)

    print("Done.")


if __name__ == "__main__":
    main()
