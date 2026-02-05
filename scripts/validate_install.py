#!/usr/bin/env python3
"""Validate NornWeave package installation.

This script validates that the package installs correctly and all
features work as expected. Run in an isolated virtual environment.

Usage:
    # Test base install
    python scripts/validate_install.py --base

    # Test with postgres extra
    python scripts/validate_install.py --postgres

    # Test with mcp extra
    python scripts/validate_install.py --mcp

    # Test all
    python scripts/validate_install.py --all
"""

import argparse
import subprocess
import sys


class Colors:
    """ANSI color codes for terminal output."""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    RESET = "\033[0m"


def print_success(msg: str) -> None:
    """Print success message in green."""
    print(f"{Colors.GREEN}✓ {msg}{Colors.RESET}")


def print_error(msg: str) -> None:
    """Print error message in red."""
    print(f"{Colors.RED}✗ {msg}{Colors.RESET}")


def print_warning(msg: str) -> None:
    """Print warning message in yellow."""
    print(f"{Colors.YELLOW}⚠ {msg}{Colors.RESET}")


def test_base_import() -> bool:
    """Test that base package imports without PostgreSQL deps."""
    print("\n--- Testing base import ---")

    try:
        import nornweave  # noqa: F401

        print_success("import nornweave succeeded")
    except ImportError as e:
        print_error(f"import nornweave failed: {e}")
        return False

    # Check that asyncpg is NOT installed (should be in postgres extra only)
    try:
        import asyncpg  # noqa: F401

        print_warning("asyncpg is installed (expected only with [postgres] extra)")
    except ImportError:
        print_success("asyncpg is not installed (correct for base install)")

    # Check that psycopg2 is NOT installed
    try:
        import psycopg2  # noqa: F401

        print_warning("psycopg2 is installed (expected only with [postgres] extra)")
    except ImportError:
        print_success("psycopg2 is not installed (correct for base install)")

    return True


def test_cli_entrypoint() -> bool:
    """Test that CLI entry point works."""
    print("\n--- Testing CLI entry point ---")

    try:
        result = subprocess.run(
            ["nornweave", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            print_success("nornweave --help works")
        else:
            print_error(f"nornweave --help failed: {result.stderr}")
            return False

        result = subprocess.run(
            ["nornweave", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            print_success(f"nornweave --version works: {result.stdout.strip()}")
        else:
            print_error(f"nornweave --version failed: {result.stderr}")
            return False

    except FileNotFoundError:
        print_error("nornweave command not found")
        return False
    except subprocess.TimeoutExpired:
        print_error("nornweave command timed out")
        return False

    return True


def test_postgres_extra() -> bool:
    """Test that postgres extra provides PostgreSQL support."""
    print("\n--- Testing postgres extra ---")

    try:
        import asyncpg  # noqa: F401

        print_success("asyncpg is installed")
    except ImportError:
        print_error("asyncpg is NOT installed (install with: pip install nornweave[postgres])")
        return False

    try:
        import psycopg2  # noqa: F401

        print_success("psycopg2 is installed")
    except ImportError:
        print_error("psycopg2 is NOT installed (install with: pip install nornweave[postgres])")
        return False

    # Test PostgresAdapter import
    try:
        from nornweave.urdr.adapters.postgres import PostgresAdapter  # noqa: F401

        print_success("PostgresAdapter import succeeded")
    except ImportError as e:
        print_error(f"PostgresAdapter import failed: {e}")
        return False

    return True


def test_mcp_extra() -> bool:
    """Test that mcp extra provides MCP server support."""
    print("\n--- Testing mcp extra ---")

    try:
        import mcp  # noqa: F401

        print_success("mcp is installed")
    except ImportError:
        print_error("mcp is NOT installed (install with: pip install nornweave[mcp])")
        return False

    try:
        import fastmcp  # noqa: F401

        print_success("fastmcp is installed")
    except ImportError:
        print_error("fastmcp is NOT installed (install with: pip install nornweave[mcp])")
        return False

    # Test MCP server import
    try:
        from nornweave.huginn.server import serve  # noqa: F401

        print_success("MCP server import succeeded")
    except ImportError as e:
        print_error(f"MCP server import failed: {e}")
        return False

    # Test CLI mcp subcommand
    try:
        result = subprocess.run(
            ["nornweave", "mcp", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            print_success("nornweave mcp --help works")
        else:
            print_error(f"nornweave mcp --help failed: {result.stderr}")
            return False
    except FileNotFoundError:
        print_error("nornweave command not found")
        return False
    except subprocess.TimeoutExpired:
        print_error("nornweave mcp command timed out")
        return False

    return True


def test_mcp_without_extra() -> bool:
    """Test that MCP shows clear error without extra installed."""
    print("\n--- Testing MCP error without extra ---")

    # Try to import MCP server - should fail
    try:
        from nornweave.huginn.server import serve  # noqa: F401

        print_warning("MCP server imported (mcp extra may be installed)")
        return True
    except ImportError:
        print_success("MCP server import failed as expected (mcp extra not installed)")

    # Test CLI gives helpful error
    try:
        result = subprocess.run(
            ["nornweave", "mcp"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if "pip install nornweave[mcp]" in result.stderr:
            print_success("CLI shows helpful install hint")
        elif result.returncode != 0:
            print_success("CLI fails gracefully without MCP extra")
        else:
            print_warning("CLI succeeded unexpectedly")
    except Exception as e:
        print_warning(f"Could not test CLI: {e}")

    return True


def main() -> int:
    """Run validation tests."""
    parser = argparse.ArgumentParser(description="Validate NornWeave installation")
    parser.add_argument("--base", action="store_true", help="Test base installation")
    parser.add_argument("--postgres", action="store_true", help="Test postgres extra")
    parser.add_argument("--mcp", action="store_true", help="Test mcp extra")
    parser.add_argument("--all", action="store_true", help="Run all tests")

    args = parser.parse_args()

    # Default to base test if no args provided
    if not any([args.base, args.postgres, args.mcp, args.all]):
        args.base = True

    results: list[tuple[str, bool]] = []

    print("=" * 50)
    print("NornWeave Installation Validation")
    print("=" * 50)

    if args.base or args.all:
        results.append(("Base import", test_base_import()))
        results.append(("CLI entry point", test_cli_entrypoint()))
        if not args.postgres and not args.mcp and not args.all:
            results.append(("MCP without extra", test_mcp_without_extra()))

    if args.postgres or args.all:
        results.append(("PostgreSQL extra", test_postgres_extra()))

    if args.mcp or args.all:
        results.append(("MCP extra", test_mcp_extra()))

    # Summary
    print("\n" + "=" * 50)
    print("Summary")
    print("=" * 50)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = f"{Colors.GREEN}PASS{Colors.RESET}" if success else f"{Colors.RED}FAIL{Colors.RESET}"
        print(f"  {name}: {status}")

    print()
    if passed == total:
        print(f"{Colors.GREEN}All {total} tests passed!{Colors.RESET}")
        return 0
    else:
        print(f"{Colors.RED}{total - passed} of {total} tests failed{Colors.RESET}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
