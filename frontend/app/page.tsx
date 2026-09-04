"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import AIConfigPanel, { type AIConfig } from "./components/AIConfig";

interface Module {
  id: string;
  name: string;
  description: string;
  completed: boolean;
}

interface ResearchResult {
  title: string;
  url: string;
  snippet: string;
  source: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

export default function Home() {
  const [step, setStep] = useState<"upload" | "checklist" | "research" | "code">("upload");
  const [idea, setIdea] = useState("");
  const [srs, setSrs] = useState("");
  const [modules, setModules] = useState<Module[]>([]);
  const [selectedModule, setSelectedModule] = useState<Module | null>(null);
  const [research, setResearch] = useState<ResearchResult[]>([]);
  const [generatedCode, setGeneratedCode] = useState("");
  const [aiConfig, setAiConfig] = useState<AIConfig>({
    provider: "ollama",
    baseUrl: "http://localhost:11434",
    apiKey: "",
    model: "llama3.1",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [thinkingText, setThinkingText] = useState("");
  const [completedCount, setCompletedCount] = useState(0);
  const fileRef = useRef<HTMLInputElement>(null);
  const thinkingRef = useRef<HTMLDivElement>(null);

  const progress = modules.length > 0 ? (completedCount / modules.length) * 100 : 0;

  useEffect(() => {
    setCompletedCount(modules.filter((m) => m.completed).length);
  }, [modules]);

  const think = useCallback(async (text: string) => {
    setThinkingText("");
    for (let i = 0; i < text.length; i++) {
      await new Promise((r) => setTimeout(r, 12));
      setThinkingText(text.slice(0, i + 1));
    }
  }, []);

  const handleGeneratePlan = useCallback(async () => {
    if (!idea.trim()) return;
    setLoading(true);
    setError("");
    setStep("checklist");

    await think("Analyzing your project idea...");
    try {
      const formData = new FormData();
      formData.append("idea", idea);

      const res = await fetch(`${API_BASE}/api/generate-plan`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) throw new Error("Failed to generate plan");

      const data = await res.json();
      await think("SRS generated! Parsing modules...");
      setSrs(data.srs);
      setModules(data.modules);
      setThinkingText("");
    } catch (err: any) {
      setError(err.message || "Failed to generate plan");
      setStep("upload");
    } finally {
      setLoading(false);
    }
  }, [idea, think]);

  const handleFileUpload = useCallback(async (file: File) => {
    setLoading(true);
    setError("");
    setStep("checklist");

    await think("Reading and analyzing the research paper...");
    try {
      const formData = new FormData();
      formData.append("file", file);

      const res = await fetch(`${API_BASE}/api/generate-plan`, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) throw new Error("Failed to process file");

      const data = await res.json();
      await think("SRS extracted! Building module checklist...");
      setSrs(data.srs);
      setModules(data.modules);
      setThinkingText("");
    } catch (err: any) {
      setError(err.message || "Failed to process file");
      setStep("upload");
    } finally {
      setLoading(false);
    }
  }, [think]);

  const handleResearch = useCallback(async (module: Module) => {
    setLoading(true);
    setSelectedModule(module);
    setStep("research");
    setResearch([]);

    await think(`Researching best practices for ${module.name}...`);
    try {
      const res = await fetch(`${API_BASE}/api/research`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tech_stack: module.name,
          module_name: module.name,
        }),
      });

      if (!res.ok) throw new Error("Research failed");

      const data = await res.json();
      await think("Found relevant resources!");
      setResearch(data.results || []);
      setThinkingText("");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [think]);

  const handleGenerateCode = useCallback(async (module: Module) => {
    setLoading(true);
    setSelectedModule(module);
    setStep("code");
    setGeneratedCode("");

    await think(`Generating code for ${module.name} using ${aiConfig.provider}...`);
    try {
      const res = await fetch(`${API_BASE}/api/generate-code`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          provider: aiConfig.provider,
          model: aiConfig.model || undefined,
          api_key: aiConfig.apiKey || undefined,
          base_url: aiConfig.baseUrl || undefined,
          module_name: module.name,
          module_description: module.description,
          srs_content: srs,
        }),
      });

      if (!res.ok) throw new Error("Code generation failed");

      const data = await res.json();
      await think("Code generated successfully!");
      setGeneratedCode(data.code);
      setModules((prev) =>
        prev.map((m) =>
          m.id === module.id ? { ...m, completed: true } : m
        )
      );
      setThinkingText("");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [aiConfig, srs, think]);

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center text-white font-bold text-sm">
                B
              </div>
              <h1 className="text-xl font-bold text-gray-900">BuildBot</h1>
              <span className="badge bg-blue-100 text-blue-800">
                Student AI Assistant
              </span>
            </div>
            <div className="flex items-center gap-4">
              <a
                href="https://you-ai-project.netlify.app"
                target="_blank"
                rel="noopener"
                className="text-sm text-blue-600 hover:text-blue-800 font-medium"
              >
                Thinking Playground
              </a>
              <AIConfigPanel onConfigChange={setAiConfig} />
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {modules.length > 0 && (
          <div className="mb-8">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">
                Progress: {completedCount}/{modules.length} modules
              </span>
              <span className="text-sm text-gray-500">
                {Math.round(progress)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <div
                className="bg-blue-600 h-2.5 rounded-full transition-all duration-500"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            {error}
            <button
              onClick={() => setError("")}
              className="ml-2 text-red-500 hover:text-red-700"
            >
              ✕
            </button>
          </div>
        )}

        {thinkingText && (
          <div
            ref={thinkingRef}
            className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-4 mb-6 animate-slide-in"
          >
            <div className="flex items-center gap-2 text-blue-700">
              <span className="w-2 h-2 bg-blue-500 rounded-full animate-pulse-dot" />
              <span className="font-medium text-sm">Thinking</span>
            </div>
            <p className="text-blue-600 mt-1 text-sm">{thinkingText}</p>
          </div>
        )}

        {step === "upload" && (
          <div className="card max-w-2xl mx-auto text-center">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              From Paper to Code
            </h2>
            <p className="text-gray-600 mb-8">
              Upload a research paper or describe your project idea. BuildBot
              will generate an SRS and checklist.
            </p>

            <div
              className="border-2 border-dashed border-gray-300 rounded-xl p-8 mb-6 hover:border-blue-400 transition-colors cursor-pointer"
              onClick={() => fileRef.current?.click()}
            >
              <div className="text-4xl mb-3">📄</div>
              <p className="text-gray-600 font-medium">
                Click to upload a PDF or text file
              </p>
              <p className="text-gray-400 text-sm mt-1">
                Or drag and drop your research paper
              </p>
              <input
                ref={fileRef}
                type="file"
                accept=".pdf,.txt,.md,.doc,.docx"
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) handleFileUpload(file);
                }}
              />
            </div>

            <div className="flex items-center gap-3 mb-6">
              <div className="flex-1 h-px bg-gray-200" />
              <span className="text-sm text-gray-500">or</span>
              <div className="flex-1 h-px bg-gray-200" />
            </div>

            <textarea
              value={idea}
              onChange={(e) => setIdea(e.target.value)}
              className="input mb-4"
              rows={4}
              placeholder="Describe your project idea... (e.g., 'Build a real-time chat app with user authentication, message history, and typing indicators')"
            />

            <button
              onClick={handleGeneratePlan}
              disabled={!idea.trim() || loading}
              className="btn-primary w-full"
            >
              {loading ? "Generating..." : "Generate SRS & Checklist"}
            </button>
          </div>
        )}

        {step === "checklist" && modules.length > 0 && (
          <div className="max-w-3xl mx-auto">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900">
                Module Checklist
              </h2>
              <button
                onClick={() => setStep("upload")}
                className="btn-secondary text-sm"
              >
                ← Start Over
              </button>
            </div>

            {srs && (
              <details className="card mb-6">
                <summary className="cursor-pointer font-medium text-gray-700">
                  View Generated SRS ({srs.length} chars)
                </summary>
                <pre className="mt-4 text-sm text-gray-600 whitespace-pre-wrap">
                  {srs}
                </pre>
              </details>
            )}

            <div className="space-y-3">
              {modules.map((mod) => (
                <div
                  key={mod.id}
                  className={`card flex items-center justify-between transition-all ${
                    mod.completed ? "bg-green-50 border-green-200" : ""
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div
                      className={`w-6 h-6 rounded-full border-2 flex items-center justify-center ${
                        mod.completed
                          ? "bg-green-500 border-green-500 text-white"
                          : "border-gray-300"
                      }`}
                    >
                      {mod.completed && "✓"}
                    </div>
                    <div>
                      <h3 className="font-medium text-gray-900">{mod.name}</h3>
                      <p className="text-sm text-gray-500">{mod.description}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleResearch(mod)}
                      disabled={loading}
                      className="btn-secondary text-sm"
                    >
                      Research
                    </button>
                    <button
                      onClick={() => handleGenerateCode(mod)}
                      disabled={loading}
                      className="btn-primary text-sm"
                    >
                      Build
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {step === "research" && (
          <div className="max-w-3xl mx-auto">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900">
                Research: {selectedModule?.name}
              </h2>
              <button
                onClick={() => setStep("checklist")}
                className="btn-secondary text-sm"
              >
                ← Back to Checklist
              </button>
            </div>

            {research.length > 0 ? (
              <div className="space-y-3">
                {research.map((r, i) => (
                  <a
                    key={i}
                    href={r.url}
                    target="_blank"
                    rel="noopener"
                    className="card block hover:shadow-md transition-shadow"
                  >
                    <h3 className="font-medium text-blue-600">{r.title}</h3>
                    <p className="text-sm text-gray-600 mt-1">{r.snippet}</p>
                    <span className="badge bg-gray-100 text-gray-600 mt-2">
                      {r.source}
                    </span>
                  </a>
                ))}
              </div>
            ) : (
              !loading && (
                <p className="text-gray-500 text-center py-8">
                  No results found. Try a different approach.
                </p>
              )
            )}

            <div className="mt-6">
              <button
                onClick={() => selectedModule && handleGenerateCode(selectedModule)}
                disabled={loading || !selectedModule}
                className="btn-primary w-full"
              >
                Generate Code for {selectedModule?.name}
              </button>
            </div>
          </div>
        )}

        {step === "code" && (
          <div className="max-w-4xl mx-auto">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900">
                Generated Code: {selectedModule?.name}
              </h2>
              <button
                onClick={() => setStep("checklist")}
                className="btn-secondary text-sm"
              >
                ← Back to Checklist
              </button>
            </div>

            {generatedCode ? (
              <div className="card">
                <div className="flex items-center justify-between mb-4">
                  <span className="badge bg-green-100 text-green-800">
                    ✓ Code Generated
                  </span>
                  <button
                    onClick={() =>
                      navigator.clipboard.writeText(
                        generatedCode.replace(/```\w*\n?/g, "")
                      )
                    }
                    className="btn-secondary text-sm"
                  >
                    Copy Code
                  </button>
                </div>
                <div className="markdown-body">
                  <pre>
                    <code>
                      {generatedCode.replace(/```\w*\n?/g, "")}
                    </code>
                  </pre>
                </div>
              </div>
            ) : (
              !loading && (
                <div className="card text-center py-8 text-gray-500">
                  Click "Build" on a module to generate code.
                </div>
              )
            )}

            <div className="mt-6">
              <button
                onClick={() => setStep("checklist")}
                className="btn-primary w-full"
              >
                Return to Checklist
              </button>
            </div>
          </div>
        )}
      </main>

      <footer className="border-t border-gray-200 bg-white mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between text-sm text-gray-500">
            <p>
              Built with ♥ for students everywhere.
            </p>
            <p>
              Thinking Component:{" "}
              <a
                href="https://you-ai-project.netlify.app"
                target="_blank"
                rel="noopener"
                className="text-blue-600 hover:text-blue-800"
              >
                you-ai-project.netlify.app
              </a>
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
