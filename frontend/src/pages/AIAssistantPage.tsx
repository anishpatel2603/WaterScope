import React, { useState } from 'react';
import { Bot, Send, Sparkles, User, Database, Layers, ArrowRight } from 'lucide-react';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  telemetry?: {
    intervention_id?: string;
    metrics?: Record<string, any>;
    dataset?: string;
  };
}

export const AIAssistantPage: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content:
        'Welcome to the WATERSCOPE AI Watershed Intelligence Assistant. I have indexed 62 monitored intervention sites across Maharashtra, the FPCD bi-temporal dataset, and Sentinel-2 spectral indices. How can I assist your hydrological surveillance today?',
    },
  ]);
  const [inputValue, setInputValue] = useState('');

  const samplePrompts = [
    'Which farm ponds experienced drying in Akola district?',
    'Explain the 4-part composite impact index weighting for Akhatwada 10.',
    'How does the Siamese twin network prevent false positives from crop phenology?',
    'What was the surface water change in the 250m radial buffer?',
  ];

  const handleSend = (text: string) => {
    if (!text.trim()) return;

    const userMsg: Message = { role: 'user', content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInputValue('');

    // Formulate realistic domain answer
    setTimeout(() => {
      let reply: Message;
      const lower = text.toLowerCase();

      if (lower.includes('drying') || lower.includes('dried')) {
        reply = {
          role: 'assistant',
          content:
            'Based on the FPCD bi-temporal surveillance catalog, **Farm Pond Akhatwada 1 (FP-108)** in Akola district exhibited complete surface water depletion between March 2007 and March 2018. The Siamese change detection network detected class `Farm Pond Dried` with 93.6% confidence. Desiltation and embankment maintenance has been logged as **CRITICAL** in the Priority Maintenance register.',
          telemetry: {
            intervention_id: 'int-akola-akhatwada-1',
            metrics: { class: 'Farm Pond Dried', confidence: 0.936, delta_ndwi: -0.42 },
          },
        };
      } else if (lower.includes('composite') || lower.includes('weight')) {
        reply = {
          role: 'assistant',
          content:
            'The WATERSCOPE Observed Impact Index (v2.0) dynamically calculates site-specific scores using a 4-part weighted telemetry framework:\n\n1. **ML Bi-Temporal Change Detection (35%)**: ResNet-18 Siamese attention feature difference classification.\n2. **Surface Water Extent (30%)**: Physical water surface delta (m²) and NDWI spectral response.\n3. **Perimeter Vegetative Vigour (20%)**: Mean NDVI delta across the 250m radial buffer zone.\n4. **Data Quality & Provenance (15%)**: Sensor ground sampling distance (1.0m/px), EXIF dates, and cloud cover factors.\n\nScores are generated on demand per site: constructed farm ponds with expanding water bodies score highly (e.g., 95.8/100), while degraded or drying basins score low (e.g., 23.9/100).',
        };
      } else if (lower.includes('crop') || lower.includes('false positive') || lower.includes('siamese')) {
        reply = {
          role: 'assistant',
          content:
            'The Siamese Bi-Temporal Architecture uses shared twin ResNet-18 backbones that project both T0 and T1 images into a common spatial feature space. Instead of a naive pixel subtraction, it computes **multi-scale differential concatenation**: `[feat0, feat1, |feat1 - feat0|]`. This allows the decoder to differentiate between seasonal vegetation senescence (crop rotation) and permanent geometric earth excavation (farm pond bunds and water retention).',
        };
      } else {
        reply = {
          role: 'assistant',
          content:
            'In the **250m radial buffer** around target structure Akhatwada 10, multi-spectral differencing recorded a **+1,480 m² net increase in localized surface water retention**, coupled with a **+0.12 mean NDVI uplift** in surrounding vegetative biomass during the post-monsoon acquisition window.',
          telemetry: {
            intervention_id: 'int-akola-akhatwada-10',
            metrics: { buffer: '250m', delta_ndvi: 0.12, delta_water_m2: 1480 },
          },
        };
      }

      setMessages((prev) => [...prev, reply]);
    }, 500);
  };

  return (
    <div className="p-6 space-y-6 max-w-5xl mx-auto h-[calc(100vh-6rem)] flex flex-col justify-between">
      {/* Top Banner */}
      <div>
        <span className="text-xs font-bold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
          Natural Language Spatial Intelligence
        </span>
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white tracking-tight flex items-center space-x-2">
          <Bot className="w-6 h-6 text-emerald-700 dark:text-emerald-400" />
          <span>AI Geospatial Assistant</span>
        </h1>
        <p className="text-xs text-slate-600 dark:text-slate-400 mt-0.5">
          Query watershed health, bi-temporal change predictions, and buffer spectral telemetry using plain English.
        </p>
      </div>

      {/* Messages Thread Container */}
      <div className="flex-1 bg-white dark:bg-slate-900 rounded-lg border border-slate-200 dark:border-slate-800 p-4 shadow-sm overflow-y-auto space-y-4 my-4 transition-colors">
        {messages.map((m, idx) => (
          <div
            key={idx}
            className={`flex items-start space-x-3 ${
              m.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            {m.role === 'assistant' && (
              <div className="w-7 h-7 rounded-full bg-emerald-700 text-white flex items-center justify-center shrink-0 text-xs font-bold shadow-sm">
                W
              </div>
            )}

            <div
              className={`max-w-2xl rounded-lg p-3.5 text-xs ${
                m.role === 'user'
                  ? 'bg-emerald-700 text-white font-medium'
                  : 'bg-slate-50 dark:bg-slate-800 text-slate-800 dark:text-slate-200 border border-slate-200 dark:border-slate-700 shadow-sm leading-relaxed whitespace-pre-line'
              }`}
            >
              {m.content}

              {m.telemetry && (
                <div className="mt-3 pt-2.5 border-t border-slate-200 dark:border-slate-700 text-[11px] font-mono bg-white dark:bg-slate-900 p-2 rounded border border-slate-100 dark:border-slate-800 space-y-0.5">
                  <div className="text-slate-400 dark:text-slate-500 font-bold uppercase text-[9px]">
                    Telemetry Reference:
                  </div>
                  {Object.entries(m.telemetry.metrics || {}).map(([k, v]) => (
                    <div key={k} className="text-slate-700 dark:text-slate-300">
                      {k}: <strong>{String(v)}</strong>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {m.role === 'user' && (
              <div className="w-7 h-7 rounded-full bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-200 flex items-center justify-center shrink-0 text-xs font-bold">
                <User className="w-4 h-4" />
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Suggested Prompt Chips */}
      <div className="flex flex-wrap gap-2 mb-3">
        {samplePrompts.map((prompt, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(prompt)}
            className="text-[11px] bg-slate-100 dark:bg-slate-800 hover:bg-emerald-50 dark:hover:bg-emerald-950/60 text-slate-700 dark:text-slate-300 hover:text-emerald-800 dark:hover:text-emerald-300 px-3 py-1 rounded-full border border-slate-200 dark:border-slate-700 transition-colors"
          >
            {prompt}
          </button>
        ))}
      </div>

      {/* Chat Input Bar */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend(inputValue);
        }}
        className="flex items-center space-x-2"
      >
        <input
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder="Ask about farm ponds, drying trends, or buffer NDVI changes..."
          className="flex-1 p-2.5 text-xs bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-700 rounded-lg focus:outline-none focus:ring-1 focus:ring-emerald-700 text-slate-900 dark:text-white placeholder:text-slate-400 dark:placeholder:text-slate-500 shadow-sm transition-colors"
        />
        <button
          type="submit"
          className="bg-emerald-700 hover:bg-emerald-800 text-white px-4 py-2.5 rounded-lg text-xs font-bold flex items-center space-x-1.5 shadow-sm transition-colors"
        >
          <span>Query</span>
          <Send className="w-3.5 h-3.5" />
        </button>
      </form>
    </div>
  );
};
