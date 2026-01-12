#!/usr/bin/env python3
"""Migration script: Move files from global storage to project-scoped storage.

This script migrates the file storage architecture from:
  - backend/uploads/{filename}.epub
  - backend/outputs/{project_id}_*.epub

To:
  - projects/{project_id}/uploads/original.epub
  - projects/{project_id}/uploads/reference.epub
  - projects/{project_id}/exports/translated.epub
  - projects/{project_id}/exports/bilingual.epub

Run this script BEFORE starting the updated backend server:
    python scripts/migrate_to_project_storage.py

Optional: Dry run mode (no changes):
    python scripts/migrate_to_project_storage.py --dry-run
"""

import argparse
import shutil
import sqlite3
from pathlib import Path
from typing import Optional


# Paths
SCRIPT_DIR = Path(__file__).parent
BACKEND_DIR = SCRIPT_DIR.parent
REPO_ROOT = BACKEND_DIR.parent
DB_PATH = BACKEND_DIR / "epub_translator.db"
PROJECTS_BASE = REPO_ROOT / "projects"
OLD_UPLOADS_DIR = BACKEND_DIR / "uploads"
OLD_OUTPUTS_DIR = BACKEND_DIR / "outputs"


def get_project_dirs(project_id: str) -> dict[str, Path]:
    """Get all directory paths for a project."""
    project_dir = PROJECTS_BASE / project_id
    return {
        "root": project_dir,
        "uploads": project_dir / "uploads",
        "exports": project_dir / "exports",
        "prompts": project_dir / "prompts",
    }


def initialize_project_structure(project_id: str, dry_run: bool = False) -> None:
    """Initialize directory structure for a project."""
    dirs = get_project_dirs(project_id)

    for dir_name, dir_path in dirs.items():
        if dir_path.exists():
            print(f"  [EXISTS] {dir_path}")
        else:
            if not dry_run:
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"  [CREATE] {dir_path}")
            else:
                print(f"  [WOULD CREATE] {dir_path}")

    # Create prompt subdirectories
    if not dry_run:
        prompts_dir = dirs["prompts"]
        for subdir in ["analysis", "translation", "optimization", "proofreading"]:
            (prompts_dir / subdir).mkdir(exist_ok=True)


def move_file(source: Path, dest: Path, dry_run: bool = False) -> bool:
    """Move a file from source to destination.

    Args:
        source: Source file path
        dest: Destination file path
        dry_run: If True, only print what would happen

    Returns:
        True if file was moved (or would be moved), False otherwise
    """
    if not source.exists():
        return False

    if dest.exists():
        print(f"  [SKIP] {dest.name} already exists at destination")
        return False

    if not dry_run:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(dest))
        print(f"  [MOVE] {source.name} -> {dest}")
    else:
        print(f"  [WOULD MOVE] {source.name} -> {dest}")

    return True


def migrate_project(project: dict, dry_run: bool = False) -> dict:
    """Migrate files for a single project.

    Args:
        project: Project data from database
        dry_run: If True, only print what would happen

    Returns:
        Dict with migration results and new file paths
    """
    project_id = project["id"]
    project_name = project["name"]
    original_file_path = project.get("original_file_path")

    print(f"\n{'='*80}")
    print(f"Project: {project_name} (ID: {project_id})")
    print(f"{'='*80}")

    result = {
        "project_id": project_id,
        "original_moved": False,
        "reference_moved": False,
        "new_original_path": None,
        "new_reference_path": None,
    }

    # Initialize project structure
    print("\n[1] Initializing project directory structure...")
    initialize_project_structure(project_id, dry_run)

    # Move original EPUB
    print("\n[2] Moving original EPUB...")
    if original_file_path:
        old_original = Path(original_file_path)
        new_original = get_project_dirs(project_id)["uploads"] / "original.epub"

        if move_file(old_original, new_original, dry_run):
            result["original_moved"] = True
            result["new_original_path"] = str(new_original)
    else:
        print("  [SKIP] No original file path in database")

    # Move reference EPUB (check for pattern: ref_{project_id}_*.epub)
    print("\n[3] Moving reference EPUB...")
    reference_pattern = f"ref_{project_id}_*.epub"
    reference_files = list(OLD_UPLOADS_DIR.glob(reference_pattern))

    if reference_files:
        old_reference = reference_files[0]  # Take first match
        new_reference = get_project_dirs(project_id)["uploads"] / "reference.epub"

        if move_file(old_reference, new_reference, dry_run):
            result["reference_moved"] = True
            result["new_reference_path"] = str(new_reference)
    else:
        print(f"  [SKIP] No reference files matching {reference_pattern}")

    # Move export files (from backend/outputs to projects/{id}/exports)
    print("\n[4] Moving export files...")
    export_patterns = [
        f"{project_id}_bilingual.epub",
        f"{project_id}_bilingual_v2.epub",
        f"{project_id}_translated.epub",
    ]

    exports_moved = 0
    for pattern in export_patterns:
        old_export = OLD_OUTPUTS_DIR / pattern
        if old_export.exists():
            # Simplify filename in new location
            if "bilingual" in pattern:
                new_name = "bilingual.epub"
            elif "translated" in pattern:
                new_name = "translated.epub"
            else:
                new_name = pattern

            new_export = get_project_dirs(project_id)["exports"] / new_name

            if move_file(old_export, new_export, dry_run):
                exports_moved += 1

    result["exports_moved"] = exports_moved

    return result


def update_database(results: list[dict], dry_run: bool = False) -> None:
    """Update database with new file paths.

    Args:
        results: List of migration results
        dry_run: If True, only print SQL statements
    """
    print(f"\n{'='*80}")
    print("DATABASE UPDATE")
    print(f"{'='*80}\n")

    if not DB_PATH.exists():
        print(f"ERROR: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        for result in results:
            if result["new_original_path"]:
                project_id = result["project_id"]
                new_path = result["new_original_path"]

                sql = f"UPDATE projects SET original_file_path = ? WHERE id = ?"
                print(f"  [UPDATE] Project {project_id}: original_file_path = {new_path}")

                if not dry_run:
                    cursor.execute(sql, (new_path, project_id))
                else:
                    print(f"  [SQL] {sql}")

        if not dry_run:
            conn.commit()
            print("\n[SUCCESS] Database updated")
        else:
            print("\n[DRY RUN] No database changes made")

    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] Database update failed: {e}")
        raise
    finally:
        conn.close()


def main():
    """Run the migration."""
    parser = argparse.ArgumentParser(
        description="Migrate EPUB files to project-scoped storage"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    args = parser.parse_args()

    dry_run = args.dry_run

    if dry_run:
        print("\n" + "="*80)
        print("DRY RUN MODE - No changes will be made")
        print("="*80 + "\n")

    # Check database exists
    if not DB_PATH.exists():
        print(f"ERROR: Database not found at {DB_PATH}")
        print("Please run this script from the backend directory.")
        return 1

    # Load all projects from database
    print("Loading projects from database...")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT id, name, original_file_path FROM projects")
    projects = [dict(row) for row in cursor.fetchall()]
    conn.close()

    if not projects:
        print("No projects found in database.")
        return 0

    print(f"Found {len(projects)} project(s) to migrate\n")

    # Migrate each project
    results = []
    for project in projects:
        try:
            result = migrate_project(project, dry_run)
            results.append(result)
        except Exception as e:
            print(f"\n[ERROR] Failed to migrate project {project['id']}: {e}")
            print("Continuing with other projects...\n")

    # Update database with new paths
    if results:
        update_database(results, dry_run)

    # Print summary
    print(f"\n{'='*80}")
    print("MIGRATION SUMMARY")
    print(f"{'='*80}\n")

    total_originals = sum(1 for r in results if r["original_moved"])
    total_references = sum(1 for r in results if r["reference_moved"])
    total_exports = sum(r["exports_moved"] for r in results)

    print(f"Projects migrated: {len(results)}")
    print(f"Original EPUBs moved: {total_originals}")
    print(f"Reference EPUBs moved: {total_references}")
    print(f"Export files moved: {total_exports}")

    if dry_run:
        print("\n[DRY RUN] No actual changes were made.")
        print("Run without --dry-run to perform the migration.")
    else:
        print("\n[SUCCESS] Migration completed!")
        print("\nNext steps:")
        print("1. Start the backend server with the updated code")
        print("2. Test uploading a new EPUB file")
        print("3. Test exporting a translated EPUB")
        print("4. Verify project deletion removes all files")

    return 0


if __name__ == "__main__":
    exit(main())
