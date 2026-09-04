import os
import uuid
import json
from typing import Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from llm_client import LLMClient
from collabuild_utils import generate_srs_from_text, parse_srs_modules

app = FastAPI(title="BuildBot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GenerateCodeRequest(BaseModel):
    provider: str = "ollama"
    model: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    module_name: str
    module_description: str
    srs_content: str


class ResearchRequest(BaseModel):
    tech_stack: str
    module_name: Optional[str] = None


class GenerateAllRequest(BaseModel):
    provider: str = "ollama"
    model: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    srs_content: str
    modules: list[dict]


@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "BuildBot API",
        "version": "1.0.0",
    }


@app.post("/api/generate-plan")
async def generate_plan(
    file: Optional[UploadFile] = File(None),
    idea: Optional[str] = Form(None),
):
    if not file and not idea:
        raise HTTPException(
            status_code=400,
            detail="Please upload a file or provide a project idea.",
        )

    raw_text = ""
    if file:
        content = await file.read()
        try:
            raw_text = content.decode("utf-8")
        except UnicodeDecodeError:
            raw_text = content.decode("latin-1")
    elif idea:
        raw_text = idea

    srs = generate_srs_from_text(raw_text)
    modules = parse_srs_modules(srs)

    for mod in modules:
        mod["id"] = str(uuid.uuid4())[:8]
        mod["completed"] = False

    return {
        "srs": srs,
        "modules": modules,
        "summary": f"Generated SRS with {len(modules)} modules from input.",
    }


@app.post("/api/research")
async def research(req: ResearchRequest):
    queries = [
        f"{req.tech_stack} best practices",
        f"{req.tech_stack} architecture patterns",
        f"{req.module_name or 'web app'} tutorial guide",
    ]

    results = []
    for q in queries:
        results.append({
            "title": f"Search: {q}",
            "url": f"https://www.google.com/search?q={q.replace(' ', '+')}",
            "snippet": f"Results for '{q}' - click to search on Google.",
            "source": "web",
        })

    return {
        "results": results,
        "tech_stack": req.tech_stack,
    }


@app.post("/api/generate-code")
async def generate_code(req: GenerateCodeRequest):
    system_prompt = """You are BuildBot, an expert software engineer. Generate clean, production-ready code.
Output only the code in a markdown code block with the appropriate language tag.
Include comments for complex logic. Follow best practices."""

    user_prompt = f"""Generate code for the module: {req.module_name}
Description: {req.module_description}

Based on this SRS:
{req.srs_content[:3000]}
"""
    if req.research:
        user_prompt += f"\n\nUse these best practices:\n{req.research}"

    client = LLMClient(
        provider=req.provider,
        model=req.model,
        api_key=req.api_key,
        base_url=req.base_url,
    )

    try:
        code = await client.generate(user_prompt, system_prompt)
        return {
            "code": code,
            "module": req.module_name,
            "status": "success",
        }
    except Exception as e:
        return {
            "code": f"# Error generating code: {str(e)}\n# Please check your AI provider settings.",
            "module": req.module_name,
            "status": "error",
            "error": str(e),
        }


@app.post("/api/generate-all")
async def generate_all(req: GenerateAllRequest):
    client = LLMClient(
        provider=req.provider,
        model=req.model,
        api_key=req.api_key,
        base_url=req.base_url,
    )

    results = []
    for module in req.modules:
        system_prompt = "You are BuildBot, an expert software engineer. Generate clean code."
        user_prompt = f"""Generate code for: {module['name']}
Description: {module.get('description', 'No description')}
SRS context: {req.srs_content[:2000]}
Output only code in a markdown block."""
        try:
            code = await client.generate(user_prompt, system_prompt)
            results.append({"module": module["name"], "code": code, "status": "success"})
        except Exception as e:
            results.append({"module": module["name"], "code": "", "status": "error", "error": str(e)})

    return {"results": results}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
