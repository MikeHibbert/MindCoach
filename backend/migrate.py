#!/usr/bin/env python3
"""
Database migration runner for the Personalized Learning Path Generator
"""

import os
import sys
import importlib.util
from pathlib import Path

def get_migration_files():
    """Get all migration files in order"""
    migrations_dir = Path(__file__).parent / 'migrations'
    if not migrations_dir.exists():
        return []
    
    migration_files = []
    for file in migrations_dir.glob('*.py'):
        if file.name != '__init__.py':
            migration_files.append(file)
    
    return sorted(migration_files)

def run_migration(migration_file, action='upgrade'):
    """Run a specific migration file"""
    spec = importlib.util.spec_from_file_location("migration", migration_file)
    migration_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration_module)
    
    if action == 'upgrade' and hasattr(migration_module, 'upgrade'):
        migration_module.upgrade()
    elif action == 'downgrade' and hasattr(migration_module, 'downgrade'):
        migration_module.downgrade()
    else:
        print(f"Action '{action}' not supported in {migration_file.name}")

def main():
    """Main migration runner"""
    if len(sys.argv) < 2:
        print("Usage: python migrate.py [upgrade|downgrade] [migration_name]")
        print("       python migrate.py upgrade - Run all pending migrations")
        print("       python migrate.py downgrade - Rollback last migration")
        return
    
    action = sys.argv[1]
    migration_files = get_migration_files()
    
    if not migration_files:
        print("No migration files found in migrations/ directory")
        return
    
    if len(sys.argv) > 2:
        # Run specific migration
        migration_name = sys.argv[2]
        target_file = None
        for file in migration_files:
            if migration_name in file.name:
                target_file = file
                break
        
        if target_file:
            print(f"Running {action} for {target_file.name}")
            run_migration(target_file, action)
        else:
            print(f"Migration '{migration_name}' not found")
    else:
        # Run all migrations
        if action == 'upgrade':
            print("Running all migrations...")
            for migration_file in migration_files:
                print(f"\nApplying {migration_file.name}")
                run_migration(migration_file, action)
        elif action == 'downgrade':
            print("Rolling back last migration...")
            if migration_files:
                last_migration = migration_files[-1]
                print(f"\nRolling back {last_migration.name}")
                run_migration(last_migration, action)

if __name__ == '__main__':
    main()