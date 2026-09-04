import re
from typing import List, Dict


def parse_srs_modules(srs_text: str) -> List[Dict[str, str]]:
    """Parse SRS text into a list of modules with name and description."""
    modules = []
    lines = srs_text.split("\n")

    current_module = None
    current_desc_lines = []

    for line in lines:
        header_match = re.match(r"^#{1,3}\s+(?:Module\s+\d+[:\s]+)(.+)", line)
        section_match = re.match(r"^#{1,3}\s+(\d+\.?\d*)\s+(.+)", line)
        bullet_match = re.match(r"^\s*[-*]\s+(.+)", line)

        if header_match or (section_match and _is_module_section(section_match.group(2))):
            if current_module:
                modules.append({
                    "name": current_module,
                    "description": " ".join(current_desc_lines).strip(),
                })
            current_module = (header_match.group(1) if header_match else section_match.group(2)).strip()
            current_desc_lines = []
        elif bullet_match and current_module:
            current_desc_lines.append(bullet_match.group(1))
        elif current_module and line.strip() and not line.startswith("#"):
            current_desc_lines.append(line.strip())

    if current_module:
        modules.append({
            "name": current_module,
            "description": " ".join(current_desc_lines).strip(),
        })

    if not modules:
        modules = _generate_default_modules(srs_text)

    return modules


def _is_module_section(title: str) -> bool:
    keywords = [
        "module", "service", "component", "feature", "system",
        "authentication", "database", "api", "frontend", "backend",
        "user", "payment", "notification", "search", "admin",
    ]
    return any(kw in title.lower() for kw in keywords)


def _generate_default_modules(srs_text: str) -> List[Dict[str, str]]:
    """Generate default modules from SRS when structured parsing fails."""
    sentences = re.split(r"[.!?]+", srs_text)
    modules = []
    seen = set()

    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) > 20 and any(
            kw in sentence.lower()
            for kw in ["should", "must", "shall", "require", "need", "implement", "build"]
        ):
            name = sentence[:60].strip()
            if name not in seen and len(modules) < 10:
                seen.add(name)
                modules.append({"name": name, "description": sentence})

    if not modules:
        modules = [
            {"name": "Module 1: Core Setup", "description": "Initial project setup and configuration"},
            {"name": "Module 2: User Interface", "description": "Frontend components and pages"},
            {"name": "Module 3: Backend API", "description": "REST API endpoints and business logic"},
            {"name": "Module 4: Database", "description": "Data models and database integration"},
            {"name": "Module 5: Authentication", "description": "User auth and authorization"},
        ]

    return modules


def generate_srs_from_text(text: str) -> str:
    """Generate a structured SRS from raw text input."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    srs = "# Software Requirements Specification\n\n"
    srs += "## 1. Introduction\n\n"

    if paragraphs:
        srs += f"### 1.1 Purpose\n{paragraphs[0]}\n\n"
    else:
        srs += "### 1.1 Purpose\nThis document describes the software requirements for the proposed system.\n\n"

    srs += "### 1.2 Scope\n"
    srs += "The system shall provide the core functionality described in the input document.\n\n"

    srs += "## 2. Overall Description\n\n"
    srs += "### 2.1 Product Perspective\n"
    srs += "The system is a web-based application with frontend and backend components.\n\n"

    if len(paragraphs) > 1:
        srs += "### 2.2 Functional Requirements\n\n"
        for i, para in enumerate(paragraphs[1:], 1):
            srs += f"**Module {i}**\n{para}\n\n"

    srs += "## 3. System Features\n\n"
    srs += "- Web-based user interface\n"
    srs += "- RESTful API backend\n"
    srs += "- Database integration\n"
    srs += "- Authentication and authorization\n"
    srs += "- Responsive design\n\n"

    srs += "## 4. External Interfaces\n\n"
    srs += "- **User Interface**: Web browser\n"
    srs += "- **API Interface**: REST/JSON\n"
    srs += "- **AI Interface**: Pluggable LLM providers\n\n"

    return srs
