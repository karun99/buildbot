"""Tests for the SRS generation and parsing helpers.

These functions are pure: they take text and return text or data, with no
network, filesystem or LLM access, so they can be tested directly.
"""

import os
import sys
import unittest

# `pythonpath = ["."]` in pyproject.toml puts the repository root on sys.path.
API_PYTHON = os.path.join("api", "python")
if os.path.isdir(API_PYTHON):
    sys.path.insert(0, API_PYTHON)

from collabuild_utils import (  # noqa: E402
    _generate_default_modules,
    _is_module_section,
    generate_srs_from_text,
    parse_srs_modules,
)

STRUCTURED_SRS = """# SRS

## 1. Introduction

Some introductory prose that is not part of any module.

## 2. Modules

### Module 1: Authentication
- Email and password signup
- Password reset via emailed token

### Module 2: Reporting
- Monthly usage rollup
- CSV export
"""


class TestParseSrsModules(unittest.TestCase):
    def test_parses_numbered_module_headers(self):
        modules = parse_srs_modules(STRUCTURED_SRS)
        names = [m["name"] for m in modules]
        self.assertIn("Authentication", names)
        self.assertIn("Reporting", names)

    def test_collects_bullets_into_description(self):
        modules = parse_srs_modules(STRUCTURED_SRS)
        auth = next(m for m in modules if m["name"] == "Authentication")
        self.assertIn("Email and password signup", auth["description"])
        self.assertIn("Password reset via emailed token", auth["description"])

    def test_every_module_has_name_and_description_keys(self):
        for module in parse_srs_modules(STRUCTURED_SRS):
            self.assertIn("name", module)
            self.assertIn("description", module)
            self.assertIsInstance(module["name"], str)
            self.assertIsInstance(module["description"], str)

    def test_module_order_is_preserved(self):
        modules = parse_srs_modules(STRUCTURED_SRS)
        names = [m["name"] for m in modules]
        self.assertLess(names.index("Authentication"), names.index("Reporting"))

    def test_falls_back_when_no_structure_found(self):
        modules = parse_srs_modules("just a wall of unstructured prose with no headings")
        self.assertGreaterEqual(len(modules), 1)
        for module in modules:
            self.assertTrue(module["name"])


class TestIsModuleSection(unittest.TestCase):
    def test_recognises_module_keywords(self):
        for title in ("User Service", "Database", "API Layer", "Authentication"):
            self.assertTrue(_is_module_section(title), title)

    def test_rejects_unrelated_titles(self):
        for title in ("Introduction", "Glossary", "References"):
            self.assertFalse(_is_module_section(title), title)

    def test_is_case_insensitive(self):
        self.assertTrue(_is_module_section("USER SERVICE"))


class TestGenerateDefaultModules(unittest.TestCase):
    def test_extracts_requirement_sentences(self):
        text = (
            "The system should authenticate users. "
            "It must store results in a database. "
            "Random prose sentence that states nothing actionable here."
        )
        modules = _generate_default_modules(text)
        names = " ".join(m["name"] for m in modules)
        self.assertIn("authenticate", names)
        self.assertIn("database", names)

    def test_falls_back_to_placeholder_set(self):
        modules = _generate_default_modules("")
        self.assertEqual(len(modules), 5)
        self.assertTrue(all(m["name"] and m["description"] for m in modules))

    def test_caps_at_ten_modules(self):
        text = " ".join(f"The system should handle requirement number {i}." for i in range(40))
        self.assertLessEqual(len(_generate_default_modules(text)), 10)


class TestGenerateSrs(unittest.TestCase):
    def test_produces_expected_top_level_sections(self):
        srs = generate_srs_from_text("First paragraph.\n\nSecond paragraph.")
        for heading in (
            "# Software Requirements Specification",
            "## 1. Introduction",
            "## 2. Overall Description",
            "## 3. System Features",
            "## 4. External Interfaces",
        ):
            self.assertIn(heading, srs)

    def test_first_paragraph_becomes_purpose(self):
        srs = generate_srs_from_text("The goal is to help students plan projects.")
        self.assertIn("The goal is to help students plan projects.", srs)

    def test_later_paragraphs_become_modules(self):
        srs = generate_srs_from_text("Intro text here.\n\nUsers can log in.\n\nReports are exported.")
        self.assertIn("**Module 1**", srs)
        self.assertIn("Users can log in.", srs)
        self.assertIn("**Module 2**", srs)
        self.assertIn("Reports are exported.", srs)

    def test_empty_input_still_yields_valid_document(self):
        srs = generate_srs_from_text("")
        self.assertIn("# Software Requirements Specification", srs)
        self.assertIn("### 1.1 Purpose", srs)

    def test_round_trips_through_the_parser(self):
        srs = generate_srs_from_text("Intro text here.\n\nUsers can log in with email.")
        modules = parse_srs_modules(srs)
        self.assertGreaterEqual(len(modules), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
