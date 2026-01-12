#!/usr/bin/env python3
"""Test script: Upload EPUB and verify project-scoped storage."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, delete
from app.models.database import Project
from app.models.database.base import async_session_maker
from app.core.epub import EPUBParserV2
from app.core.project_storage import ProjectStorage
import shutil


async def test_upload():
    """Simulate EPUB upload and verify storage structure."""

    print("="*80)
    print("TESTING PROJECT-SCOPED STORAGE")
    print("="*80 + "\n")

    # Paths
    test_epub = Path(__file__).parent / "test_storage.epub"
    if not test_epub.exists():
        print(f"❌ Test EPUB not found: {test_epub}")
        print("Run create_test_epub.py first")
        return 1

    print(f"📁 Test EPUB: {test_epub}")
    print(f"   Size: {test_epub.stat().st_size} bytes\n")

    async with async_session_maker() as db:
        try:
            # Step 1: Parse EPUB
            print("[1] Parsing EPUB...")
            parser = EPUBParserV2(test_epub)
            metadata = await parser.get_metadata()
            chapters = await parser.extract_chapters()

            # Try to extract TOC, but don't fail if it doesn't work
            try:
                toc_structure = parser.extract_toc_structure()
            except Exception as e:
                print(f"    ⚠️  TOC extraction failed (not critical): {e}")
                toc_structure = []

            print(f"    Title: {metadata.get('title')}")
            print(f"    Author: {metadata.get('author')}")
            print(f"    Chapters: {len(chapters)}")
            print(f"    Language: {metadata.get('language')}\n")

            # Step 2: Create project in database
            print("[2] Creating project in database...")
            project = Project(
                name=metadata.get("title", "test_storage.epub"),
                original_filename="test_storage.epub",
                original_file_path="",  # Will be set after moving file
                epub_title=metadata.get("title"),
                epub_author=metadata.get("author"),
                epub_language=metadata.get("language"),
                epub_metadata=metadata,
                toc_structure=toc_structure,
                total_chapters=len(chapters),
            )
            db.add(project)
            await db.flush()  # Get project.id

            print(f"    Project ID: {project.id}")
            print(f"    Project Name: {project.name}\n")

            # Step 3: Initialize project directory structure
            print("[3] Initializing project directory structure...")
            ProjectStorage.initialize_project_structure(project.id)

            project_dir = ProjectStorage.get_project_dir(project.id)
            print(f"    Project directory: {project_dir}")

            # Check created directories
            for subdir in ["uploads", "exports", "prompts"]:
                path = project_dir / subdir
                status = "✅" if path.exists() else "❌"
                print(f"    {status} {subdir}/")

            print()

            # Step 4: Copy EPUB to project storage
            print("[4] Copying EPUB to project storage...")
            final_path = ProjectStorage.get_original_epub_path(project.id)
            shutil.copy(str(test_epub), str(final_path))

            print(f"    Source: {test_epub}")
            print(f"    Destination: {final_path}")
            print(f"    File exists: {'✅' if final_path.exists() else '❌'}")
            print(f"    Size: {final_path.stat().st_size} bytes\n")

            # Update project with final file path
            project.original_file_path = str(final_path)

            # Step 5: Save chapters and paragraphs
            print("[5] Saving chapters and paragraphs to database...")
            total_paragraphs = await parser.save_to_db(db, project.id, chapters)
            project.total_paragraphs = total_paragraphs

            print(f"    Total paragraphs: {total_paragraphs}\n")

            await db.commit()

            # Step 6: Verify storage structure
            print("[6] Verifying storage structure...")
            print(f"\n    📁 {project_dir}")
            print(f"    ├── uploads/")
            print(f"    │   └── original.epub {'✅' if final_path.exists() else '❌'}")
            print(f"    ├── exports/ {'✅' if (project_dir / 'exports').exists() else '❌'}")
            print(f"    ├── prompts/ {'✅' if (project_dir / 'prompts').exists() else '❌'}")
            print(f"    │   ├── analysis/ {'✅' if (project_dir / 'prompts' / 'analysis').exists() else '❌'}")
            print(f"    │   ├── translation/ {'✅' if (project_dir / 'prompts' / 'translation').exists() else '❌'}")
            print(f"    │   ├── optimization/ {'✅' if (project_dir / 'prompts' / 'optimization').exists() else '❌'}")
            print(f"    │   └── proofreading/ {'✅' if (project_dir / 'prompts' / 'proofreading').exists() else '❌'}")
            print()

            # Step 7: Check database record
            print("[7] Verifying database record...")
            result = await db.execute(select(Project).where(Project.id == project.id))
            saved_project = result.scalar_one()

            print(f"    ID: {saved_project.id}")
            print(f"    Name: {saved_project.name}")
            print(f"    File path: {saved_project.original_file_path}")
            print(f"    Total chapters: {saved_project.total_chapters}")
            print(f"    Total paragraphs: {saved_project.total_paragraphs}\n")

            # Step 8: Cleanup (optional - comment out to keep the test project)
            print("[8] Cleanup test project...")
            cleanup = input("    Delete test project? (y/N): ").strip().lower()

            if cleanup == 'y':
                # Delete from database
                await db.execute(delete(Project).where(Project.id == project.id))
                await db.commit()
                print("    ✅ Deleted from database")

                # Delete project directory
                ProjectStorage.delete_project(project.id)
                print("    ✅ Deleted project directory")
            else:
                print("    ℹ️  Keeping test project for manual inspection")
                print(f"    Project ID: {project.id}")

            print("\n" + "="*80)
            print("✅ TEST COMPLETED SUCCESSFULLY")
            print("="*80)

            return 0

        except Exception as e:
            await db.rollback()
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            return 1


if __name__ == "__main__":
    exit(asyncio.run(test_upload()))
