import { useState, useEffect, useRef } from "react";
import axios from "axios";
import { io } from "socket.io-client";
import { motion, AnimatePresence } from "framer-motion";

export default function App() {
  const [status, setStatus] = useState("Healthy");
  const [reason, setReason] = useState("No incidents");
  const [mttr, setMttr] = useState("-");
  const [confidence, setConfidence] = useState(0);
  const [websiteUrl, setWebsiteUrl] = useState("");
  const [monitoredSites, setMonitoredSites] = useState([]);
  const [currentDiagnosis, setCurrentDiagnosis] = useState(null);
  const [logs, setLogs] = useState([]);
  const [aiThinking, setAiThinking] = useState(false);
  const [patternRecognition, setPatternRecognition] = useState(null);
  const logRef = useRef(null);

  useEffect(() => {
    const socket = io("http://localhost:5001");

    socket.on("status_update", (data) => {
      if (data.status) setStatus(data.status);
    });

    socket.on("kubectl_log", (line) => {
      setLogs((prev) => [...prev.slice(-200), line]);
    });

    return () => socket.disconnect();
  }, []);

  useEffect(() => {
    if (logRef.current) {
      logRef.current.scrollTop = logRef.current.scrollHeight;
    }
  }, [logs]);

  const checkWebsite = async () => {
    if (!websiteUrl) {
      alert("Please enter a website URL");
      return;
    }

    setLogs([]);
    setStatus("Analyzing...");
    setAiThinking(true);
    setPatternRecognition(null);
    const startTime = Date.now();

    try {
      const res = await axios.post("http://localhost:5001/check-website", {
        url: websiteUrl,
      });

      const endTime = Date.now();
      const scanTime = ((endTime - startTime) / 1000).toFixed(2);
      setMttr(`${scanTime}s`);

      setCurrentDiagnosis(res.data.diagnosis);
      setConfidence(res.data.diagnosis.confidence);
      setReason(res.data.diagnosis.root_cause);
      setAiThinking(false);
      
      // Show pattern recognition
      setPatternRecognition({
        detected: true,
        patterns: [
          `Status Code: ${res.data.result.status === 'error' ? 'Error Detected' : 'Healthy'}`,
          `Response Time: ${res.data.result.response_time}ms`,
          `Confidence: ${res.data.diagnosis.confidence}%`
        ]
      });
      
      if (res.data.result.status === "healthy") {
        setStatus("Healthy");
      } else {
        setStatus("Issues Detected");
      }
    } catch (err) {
      console.error(err);
      setStatus("Issues Detected");
      setAiThinking(false);
      const endTime = Date.now();
      const scanTime = ((endTime - startTime) / 1000).toFixed(2);
      setMttr(`${scanTime}s`);
    }
  };

  const simulateFailure = async () => {
    setLogs([]);
    setStatus("Simulating...");

    try {
      await axios.post("http://localhost:5001/inject", {
        url: websiteUrl || "http://httpstat.us/500",
      });
    } catch (err) {
      console.error(err);
    }
  };

  const startMonitoring = async () => {
    if (!websiteUrl) {
      alert("Please enter a website URL");
      return;
    }

    try {
      await axios.post("http://localhost:5001/monitor", {
        url: websiteUrl,
      });

      if (!monitoredSites.includes(websiteUrl)) {
        setMonitoredSites([...monitoredSites, websiteUrl]);
      }

      alert(`Started monitoring ${websiteUrl}`);
    } catch (err) {
      console.error(err);
    }
  };

  const autoHeal = async () => {
    if (!websiteUrl) {
      alert("Please enter a website URL");
      return;
    }

    setLogs([]);
    setStatus("Auto-Healing...");

    try {
      const res = await axios.post("http://localhost:5001/auto-heal", {
        url: websiteUrl,
      });

      if (res.data.success) {
        setStatus("Healthy");
        alert(`Auto-healing completed in ${res.data.healing_time}`);
      } else {
        alert(res.data.message);
      }
    } catch (err) {
      console.error(err);
      setStatus("Error");
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 text-white p-8">
      <motion.div
        initial={{ opacity: 0, y: -40 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center mb-10"
      >
        <h1 className="text-6xl font-bold mb-3 bg-gradient-to-r from-white via-white to-white bg-clip-text text-transparent">
          💫 AuroraAI
        </h1>
        <p className="text-xl text-gray-300 font-semibold mb-2">
          Illuminate Infrastructure. Eliminate Downtime.
        </p>
        <p className="text-gray-400 text-sm">
          Beautiful Intelligence • Instant Detection • Auto-Healing
        </p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-gray-800/50 backdrop-blur-lg p-6 rounded-2xl shadow-2xl mb-6 border border-purple-500/30"
      >
        <h2 className="text-2xl font-semibold mb-4">Enter Website URL</h2>
        
        <div className="flex gap-3 mb-4">
          <input
            type="text"
            value={websiteUrl}
            onChange={(e) => setWebsiteUrl(e.target.value)}
            placeholder="https://example.com or http://httpstat.us/500"
            className="flex-1 px-4 py-3 bg-gray-900 border border-gray-700 rounded-xl focus:outline-none focus:border-purple-500 text-white"
          />
        </div>

        <div className="flex gap-3 flex-wrap">
          <motion.button
            whileTap={{ scale: 0.95 }}
            whileHover={{ scale: 1.02 }}
            onClick={checkWebsite}
            className="bg-blue-600 px-6 py-3 rounded-xl hover:bg-blue-700 font-semibold"
          >
             Check Now
          </motion.button>

          <motion.button
            whileTap={{ scale: 0.95 }}
            whileHover={{ scale: 1.02 }}
            onClick={startMonitoring}
            className="bg-green-600 px-6 py-3 rounded-xl hover:bg-green-700 font-semibold"
          >
             Monitor 24/7
          </motion.button>

          {status === "Issues Detected" && (
            <motion.button
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              whileTap={{ scale: 0.95 }}
              whileHover={{ scale: 1.02 }}
              onClick={autoHeal}
              className="bg-purple-600 px-6 py-3 rounded-xl hover:bg-purple-700 font-semibold"
            >
              ✨ Auto-Heal
            </motion.button>
          )}

          <motion.button
            whileTap={{ scale: 0.95 }}
            whileHover={{ scale: 1.02 }}
            onClick={() => window.location.reload()}
            className="bg-gray-600 px-6 py-3 rounded-xl hover:bg-gray-700 font-semibold"
          >
             Refresh
          </motion.button>
        </div>

        <div className="mt-4 flex gap-2 flex-wrap">
          <span className="text-gray-400 text-sm">Quick test:</span>
          {["http://httpstat.us/500", "http://httpstat.us/503", "http://httpstat.us/404"].map((url) => (
            <button
              key={url}
              onClick={() => setWebsiteUrl(url)}
              className="text-xs bg-gray-700 px-3 py-1 rounded-lg hover:bg-gray-600"
            >
              {url.split("/").pop()}
            </button>
          ))}
        </div>
      </motion.div>

      {patternRecognition && (
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-gradient-to-r from-purple-900/50 to-pink-900/50 backdrop-blur-lg p-6 rounded-2xl shadow-2xl mb-6 border border-purple-500/50"
        >
          <h2 className="text-2xl font-semibold mb-4 flex items-center">
            🧠 AI Pattern Recognition
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {patternRecognition.patterns.map((pattern, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: idx * 0.1 }}
                className="bg-black/30 p-4 rounded-xl border border-purple-400/30"
              >
                <p className="text-purple-300 text-sm font-mono">{pattern}</p>
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      <motion.div
        layout
        className="bg-gray-800/50 backdrop-blur-lg p-6 rounded-2xl shadow-2xl mb-6 border border-purple-500/30"
      >
        <h2 className="text-2xl font-semibold mb-4">System Status</h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gray-900/50 p-4 rounded-xl">
            <p className="text-gray-400 text-sm mb-1">Status</p>
            <p
              className={`text-2xl font-bold ${
                status === "Healthy"
                  ? "text-green-400"
                  : status === "Issues Detected"
                  ? "text-red-400"
                  : "text-yellow-400"
              }`}
            >
              {status}
            </p>
          </div>

          <div className="bg-gray-900/50 p-4 rounded-xl">
            <p className="text-gray-400 text-sm mb-1">MTTR</p>
            <p className="text-2xl font-bold text-blue-400">{mttr}</p>
          </div>

          <div className="bg-gray-900/50 p-4 rounded-xl">
            <p className="text-gray-400 text-sm mb-1">AI Confidence</p>
            <p className="text-2xl font-bold text-purple-400">{confidence}%</p>
          </div>
        </div>

        {websiteUrl && (
          <div className="mt-4 bg-gray-900/50 p-4 rounded-xl">
            <p className="text-gray-400 text-sm mb-1">Scanned URL</p>
            <p className="text-sm text-blue-400 truncate">{websiteUrl}</p>
          </div>
        )}
      </motion.div>

      <div className="bg-black/70 p-6 rounded-2xl border border-green-500/30 mb-6">
        <h3 className="text-2xl font-bold text-green-400 mb-3">
          📡 Live Analysis Stream
        </h3>

        <div
          ref={logRef}
          className="bg-black rounded-lg p-4 font-mono text-sm text-green-400 h-80 overflow-y-auto"
        >
          {logs.length === 0 ? (
            <p className="text-gray-500">Waiting for analysis...</p>
          ) : (
            logs.map((log, idx) => (
              <div key={idx} className="mb-1">
                {log}
              </div>
            ))
          )}
        </div>
      </div>

      <AnimatePresence>
        {currentDiagnosis && (
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="bg-gradient-to-r from-slate-900/50 to-blue-900/50 p-6 rounded-2xl border border-purple-500/50"
          >
            <h3 className="text-2xl font-bold mb-6">Diagnosis</h3>

            <div className="space-y-6">
              <div>
                <h4 className="text-lg font-semibold text-cyan-400 mb-2">
                  🔍 What Happened
                </h4>
                <p className="text-gray-300 font-semibold mb-3">{currentDiagnosis.root_cause}</p>
                
                {currentDiagnosis.error_explanation && (
                  <div className="bg-slate-800/70 p-4 rounded-lg border border-yellow-500/30">
                    <h5 className="text-yellow-400 font-semibold mb-2">📖 Why This Happened:</h5>
                    <p className="text-gray-300 leading-relaxed">{currentDiagnosis.error_explanation}</p>
                  </div>
                )}
              </div>

              <div>
                <h4 className="text-lg font-semibold text-green-400 mb-2">
                  🔧 Recommended Fixes
                </h4>
                <ul className="space-y-2">
                  {currentDiagnosis.fix_steps.map((step, idx) => (
                    <li key={idx} className="flex items-start">
                      <span className="text-green-400 mr-2">•</span>
                      <span className="text-gray-300">{step}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="bg-blue-900/30 p-4 rounded-lg border border-blue-500/30">
                <p className="text-gray-400 text-sm">
                   <span className="font-semibold">Estimated Fix Time:</span>{" "}
                  <span className="text-blue-400">{currentDiagnosis.estimated_fix_time}</span>
                </p>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {monitoredSites.length > 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="bg-gray-800/50 backdrop-blur-lg p-6 rounded-2xl border border-purple-500/30 mt-6"
        >
          <h3 className="text-xl font-semibold mb-4">📡 Monitored Sites</h3>
          <div className="space-y-2">
            {monitoredSites.map((site, idx) => (
              <div key={idx} className="bg-gray-900/50 p-3 rounded-lg flex items-center justify-between">
                <span className="text-gray-300 truncate">{site}</span>
                <span className="text-green-400 text-sm">● Active</span>
              </div>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
}
