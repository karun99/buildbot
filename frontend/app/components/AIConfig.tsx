"use client";

import { useState, useEffect, useCallback } from "react";

export interface AIConfig {
  provider: string;
  baseUrl: string;
  apiKey: string;
  model: string;
}

const PROVIDERS = [
  {
    id: "ollama",
    name: "Ollama (Local)",
    defaultUrl: "http://localhost:11434",
    needsKey: false,
    defaultModel: "llama3.1",
  },
  {
    id: "llama_cpp",
    name: "llama.cpp (Local)",
    defaultUrl: "http://localhost:8080/v1",
    needsKey: false,
    defaultModel: "default",
  },
  {
    id: "oobabooga",
    name: "Oobabooga (Local)",
    defaultUrl: "http://localhost:5000/v1",
    needsKey: false,
    defaultModel: "default",
  },
  {
    id: "openrouter",
    name: "OpenRouter (Cloud)",
    defaultUrl: "https://openrouter.ai/api/v1",
    needsKey: true,
    defaultModel: "meta-llama/llama-3.1-8b-instruct",
  },
  {
    id: "nvidia_nim",
    name: "NVIDIA NIM (Cloud)",
    defaultUrl: "https://integrate.api.nvidia.com/v1",
    needsKey: true,
    defaultModel: "meta/llama-3.1-8b-instruct",
  },
];

const STORAGE_KEY = "buildbot-ai-config";

export default function AIConfigPanel({
  onConfigChange,
}: {
  onConfigChange: (config: AIConfig) => void;
}) {
  const [config, setConfig] = useState<AIConfig>({
    provider: "ollama",
    baseUrl: "http://localhost:11434",
    apiKey: "",
    model: "llama3.1",
  });
  const [isOpen, setIsOpen] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        setConfig(parsed);
        onConfigChange(parsed);
      } catch {}
    }
  }, []);

  const handleProviderChange = useCallback(
    (providerId: string) => {
      const provider = PROVIDERS.find((p) => p.id === providerId);
      if (provider) {
        const newConfig: AIConfig = {
          provider: providerId,
          baseUrl: provider.defaultUrl,
          apiKey: "",
          model: provider.defaultModel,
        };
        setConfig(newConfig);
      }
    },
    []
  );

  const handleSave = () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(config));
    onConfigChange(config);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const currentProvider = PROVIDERS.find((p) => p.id === config.provider);

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="btn-secondary flex items-center gap-2 text-sm"
      >
        <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse-dot" />
        AI: {currentProvider?.name || config.provider}
      </button>

      {isOpen && (
        <div className="absolute right-0 top-full mt-2 w-96 bg-white rounded-xl shadow-lg border border-gray-200 p-6 z-50 animate-slide-in">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">AI Configuration</h3>
            <button
              onClick={() => setIsOpen(false)}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Provider
              </label>
              <select
                value={config.provider}
                onChange={(e) => handleProviderChange(e.target.value)}
                className="input"
              >
                {PROVIDERS.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Base URL
              </label>
              <input
                type="text"
                value={config.baseUrl}
                onChange={(e) =>
                  setConfig({ ...config, baseUrl: e.target.value })
                }
                className="input"
                placeholder="http://localhost:11434"
              />
            </div>

            {currentProvider?.needsKey && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  API Key
                </label>
                <input
                  type="password"
                  value={config.apiKey}
                  onChange={(e) =>
                    setConfig({ ...config, apiKey: e.target.value })
                  }
                  className="input"
                  placeholder="sk-..."
                />
                <p className="text-xs text-gray-500 mt-1">
                  Stored in your browser only. Never sent to BuildBot.
                </p>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Model
              </label>
              <input
                type="text"
                value={config.model}
                onChange={(e) =>
                  setConfig({ ...config, model: e.target.value })
                }
                className="input"
                placeholder={currentProvider?.defaultModel || "model-name"}
              />
            </div>

            <button
              onClick={handleSave}
              className="btn-primary w-full flex items-center justify-center gap-2"
            >
              {saved ? (
                <>✓ Saved</>
              ) : (
                <>Save Configuration</>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
