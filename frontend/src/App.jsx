import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell
} from 'recharts';
import { Satellite, Zap, Brain, Radio } from 'lucide-react';
import './index.css';

const API = 'http://localhost:8000';

/* ── Clock ────────────────────────────────────────────────────────────── */
function MissionClock() {
  const [now, setNow] = useState(new Date());
  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(t);
  }, []);
  const pad = n => String(n).padStart(2, '0');
  const utc = `MET ${pad(now.getUTCHours())}:${pad(now.getUTCMinutes())}:${pad(now.getUTCSeconds())} UTC`;
  return <span className="topbar-meta">{utc}</span>;
}

/* ── Score bar ────────────────────────────────────────────────────────── */
function ScoreRow({ label, value, type, weight }) {
  return (
    <div className="score-row">
      <div className="score-row-label">
        <span>{label} <span style={{ opacity: 0.5 }}>×{weight}</span></span>
        <span className="sv">{value != null ? value.toFixed(1) : '—'}</span>
      </div>
      <div className="score-track">
        <div
          className={`score-fill ${type}`}
          style={{ width: `${Math.max(0, Math.min(100, value || 0))}%` }}
        />
      </div>
    </div>
  );
}

/* ── Chart tooltip ────────────────────────────────────────────────────── */
function ChartTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div style={{
      background: '#0c0e0c',
      border: '1px solid #3d4f3a',
      padding: '0.55rem 0.75rem',
      fontFamily: "'Share Tech Mono', monospace",
      fontSize: '0.68rem',
      lineHeight: '1.7',
      color: '#cdd6c8',
    }}>
      <div style={{ color: '#e8a422', letterSpacing: '0.08em' }}>{d.id}</div>
      <div>SCENE  <strong>{d.scene?.toUpperCase()}</strong></div>
      <div>IV     <strong style={{ color: '#e8a422' }}>{d.information_value?.toFixed(1)}</strong></div>
      <div>NOVL   <strong>{d.novelty_score?.toFixed(1)}</strong></div>
      <div>SIZE   <strong>{d.compressed_size_mb?.toFixed(0)} MB</strong></div>
      <div>V/MB   <strong style={{ color: '#5acc6e' }}>{d.value_per_mb?.toFixed(3)}</strong></div>
      <div>ACT    <strong>{d.action}</strong></div>
    </div>
  );
}

/* ── Transformer Analysis Panel ───────────────────────────────────────── */
function TransformerPanel({ obs }) {
  const weights = obs?.weights || { semantic: 0.25, novelty: 0.25, urgency: 0.30, mission: 0.15, quality: 0.05 };

  const actionClass = !obs ? 'pending'
    : obs.action === 'Transmit' ? 'transmit'
    : obs.action === 'Delay'   ? 'delay'
    : obs.action === 'Discard' ? 'discard'
    : 'pending';

  const actionLabel = !obs ? '—'
    : obs.action === 'Transmit' ? '▶  TRANSMIT NOW'
    : obs.action === 'Delay'   ? '◀  DELAYED'
    : obs.action === 'Discard' ? '✕  DISCARDED'
    : '·  PENDING OPTIMIZATION';

  return (
    <>
      <div className="section-header">
        <span className="sh-dot" /> <Brain size={11} /> Transformer Analysis
      </div>

      {!obs ? (
        <div className="transformer-panel">
          <div className="xfm-empty">
            <Radio size={28} style={{ opacity: 0.15 }} />
            <span>— NO OBSERVATION SELECTED —</span>
            <span style={{ opacity: 0.5, fontSize: '0.6rem' }}>
              Click any row or map marker<br />to inspect Transformer output
            </span>
          </div>
        </div>
      ) : (
        <div className="transformer-panel">
          {/* Header */}
          <div>
            <div className="xfm-scene-name">
              {obs.scene === 'Wildfire' ? '⚠ ' : obs.scene === 'Flood' ? '⚠ ' : '◉ '}
              {obs.scene?.toUpperCase()}
            </div>
            <div className="xfm-id-line">
              {obs.id} · {obs.timestamp?.slice(0, 19).replace('T', ' ')}
            </div>
            <div style={{ marginTop: '0.4rem' }}>
              <span className="model-tag">clip-vit-base-patch32</span>
            </div>
          </div>

          {/* Score bars */}
          <div className="score-rows">
            <ScoreRow label="Semantic Relevance" value={obs.semantic_score}    type="semantic" weight={weights.semantic} />
            <ScoreRow label="Novelty"            value={obs.novelty_score}     type="novelty"  weight={weights.novelty} />
            <ScoreRow label="Urgency"            value={obs.urgency}           type="urgency"  weight={weights.urgency} />
            <ScoreRow label="Mission Relevance"  value={obs.mission_relevance} type="mission"  weight={weights.mission} />
            <ScoreRow label="Data Quality"       value={obs.data_quality}      type="quality"  weight={weights.quality} />
          </div>

          {/* IV readout */}
          <div className="iv-readout">
            <div>
              <div className="iv-readout-label">Information Value</div>
              <div style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: '0.58rem', color: '#a06e10', marginTop: '0.1rem' }}>
                Σ (score × weight)
              </div>
            </div>
            <div className="iv-readout-number">{obs.information_value?.toFixed(1)}</div>
          </div>

          {/* Size + Value/MB */}
          <div className="meta-row">
            <div className="meta-cell">
              <div className="meta-cell-label">Compressed</div>
              <div className="meta-cell-value">{obs.compressed_size_mb?.toFixed(1)} MB</div>
              <div style={{ fontFamily: "'Share Tech Mono', monospace", fontSize: '0.55rem', color: '#6a7e68', marginTop: '0.1rem' }}>
                {obs.compression_quality}
              </div>
            </div>
            <div className="meta-cell">
              <div className="meta-cell-label">Value / MB</div>
              <div className="meta-cell-value">{obs.value_per_mb?.toFixed(3)}</div>
            </div>
            <div className="meta-cell">
              <div className="meta-cell-label">Original</div>
              <div className="meta-cell-value" style={{ color: '#6a7e68' }}>
                {obs.original_size_mb?.toFixed(1)} MB
              </div>
            </div>
          </div>

          {/* Decision */}
          <div className={`decision-block ${actionClass}`}>
            <div className="decision-status">{actionLabel}</div>
            <div className="decision-reason">{obs.reason || '—'}</div>
          </div>

          {/* Weights */}
          <div className="weights-line">
            <span style={{ color: '#6a7e68' }}>WEIGHTS:</span>
            {Object.entries(weights).map(([k, v]) => (
              <span key={k} className="w-chip">{k.slice(0,3).toUpperCase()} {v}</span>
            ))}
          </div>
        </div>
      )}
    </>
  );
}

/* ── Main ─────────────────────────────────────────────────────────────── */
export default function App() {
  const [observations, setObservations] = useState([]);
  const [status, setStatus]             = useState({});
  const [selectedObs, setSelectedObs]   = useState(null);
  const [optResult, setOptResult]       = useState(null);
  const [loading, setLoading]           = useState(true);
  const [optimizing, setOptimizing]     = useState(false);
  const [simulating, setSimulating]     = useState(false);

  const fetchAll = useCallback(async () => {
    try {
      const [obsRes, statRes] = await Promise.all([
        axios.get(`${API}/observations`),
        axios.get(`${API}/satellite-status`),
      ]);
      setObservations(obsRes.data);
      setStatus(statRes.data);
      setLoading(false);
    } catch (e) { console.error(e); }
  }, []);

  useEffect(() => {
    fetchAll();
    const t = setInterval(fetchAll, 15000);
    return () => clearInterval(t);
  }, [fetchAll]);

  useEffect(() => {
    if (selectedObs) {
      const fresh = observations.find(o => o.id === selectedObs.id);
      if (fresh) setSelectedObs(fresh);
    }
  }, [observations]);

  const handleOptimize = async () => {
    setOptimizing(true);
    try {
      const res = await axios.post(`${API}/optimize`);
      setObservations(res.data.observations);
      setOptResult(res.data);
      axios.get(`${API}/satellite-status`).then(r => setStatus(r.data));
    } catch (e) { console.error(e); }
    finally { setOptimizing(false); }
  };

  const handleSimulate = async (type) => {
    setSimulating(true);
    try {
      const evRes = await axios.post(`${API}/simulate-event`, { event_type: type });
      setSelectedObs(evRes.data);
      const optRes = await axios.post(`${API}/optimize`);
      setObservations(optRes.data.observations);
      setOptResult(optRes.data);
      axios.get(`${API}/satellite-status`).then(r => setStatus(r.data));
    } catch (e) { console.error(e); }
    finally { setSimulating(false); }
  };

  // Top 15 by IV for chart
  const chartData = [...observations]
    .sort((a, b) => b.information_value - a.information_value)
    .slice(0, 15);

  const markerColor = obs => {
    if (obs.action === 'Transmit') return '#5acc6e';
    if (obs.action === 'Delay')    return '#e8a422';
    if (obs.action === 'Discard')  return '#d94f3d';
    return '#3a7a46';
  };

  const markerR = obs => {
    if (obs.scene === 'Wildfire' || obs.scene === 'Flood') return 8;
    if (obs.information_value >= 70) return 6;
    if (obs.information_value >= 45) return 4;
    return 3;
  };

  if (loading) {
    return (
      <div className="app-layout">
        <div className="topbar">
          <div className="topbar-brand">
            <span className="brand-dot" />
            OrbitIQ · Mission Control
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', flex: 1 }}>
          <div className="loading-screen">
            <Satellite size={28} style={{ color: '#e8a422', opacity: 0.5 }} />
            <div>Initialising CLIP Model — standby<span className="cursor-blink" /></div>
            <div style={{ opacity: 0.4, fontSize: '0.6rem' }}>openai/clip-vit-base-patch32 · 50 observations</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="app-layout">

      {/* ── Topbar ── */}
      <div className="topbar">
        <div className="topbar-brand">
          <span className="brand-dot" />
          <Satellite size={14} />
          OrbitIQ · Mission Control
        </div>
        <MissionClock />
        <div className="topbar-actions">
          <button className="btn btn-emergency" onClick={() => handleSimulate('wildfire')} disabled={simulating}>
            ⚠ Wildfire
          </button>
          <button className="btn btn-flood" onClick={() => handleSimulate('flood')} disabled={simulating}>
            ⚠ Flood
          </button>
          <button className="btn btn-primary" onClick={handleOptimize} disabled={optimizing}>
            <Zap size={11} /> {optimizing ? 'Running…' : 'Run Optimizer'}
          </button>
        </div>
      </div>

      {/* ── Content ── */}
      <div className="content-area">

        {/* ══ LEFT SIDEBAR ══ */}
        <div className="sidebar-left">

          {/* Satellite Status */}
          <div className="section-header">
            <span className="sh-dot" /> <Satellite size={11} /> Satellite — ORBIT-IQ-01
          </div>
          <div className="panel" style={{ padding: 0 }}>
            <div className="kpi-grid">
              <div className="kpi-card">
                <div className="kpi-label">Data Generated</div>
                <div className="kpi-value amber">{(status.data_generated_mb / 1024)?.toFixed(2)} GB</div>
              </div>
              <div className="kpi-card">
                <div className="kpi-label">Data Waiting</div>
                <div className="kpi-value">{(status.storage_used_mb / 1024)?.toFixed(2)} GB</div>
              </div>
              <div className="kpi-card">
                <div className="kpi-label">Downlink Cap</div>
                <div className="kpi-value amber">{(status.available_downlink_mb / 1024)?.toFixed(2)} GB</div>
              </div>
              <div className="kpi-card">
                <div className="kpi-label">Transmitted</div>
                <div className="kpi-value">{(status.transmitted_mb / 1024)?.toFixed(2)} GB</div>
              </div>
              <div className="kpi-card">
                <div className="kpi-label">Mission Value</div>
                <div className="kpi-value amber">{status.mission_value_delivered?.toFixed(0) ?? '—'}</div>
              </div>
              <div className="kpi-card">
                <div className="kpi-label">Value / MB</div>
                <div className="kpi-value">{status.value_per_mb?.toFixed(3) ?? '—'}</div>
              </div>
            </div>
          </div>

          {/* Optimization Result */}
          {optResult && (
            <>
              <div className="section-header">
                <span className="sh-dot" /> ILP Optimization Result
              </div>
              <div className="opt-panel">
                <div className="opt-stat-row">
                  <div className="opt-stat">
                    <div className="opt-stat-label">Selected</div>
                    <div className="opt-stat-value" style={{ color: '#5acc6e' }}>
                      {(optResult.total_size_mb / 1024)?.toFixed(2)} GB
                    </div>
                  </div>
                  <div className="opt-stat">
                    <div className="opt-stat-label">Delayed</div>
                    <div className="opt-stat-value" style={{ color: '#e8a422' }}>
                      {optResult.delayed_ids?.length} obs
                    </div>
                  </div>
                  <div className="opt-stat">
                    <div className="opt-stat-label">Discarded</div>
                    <div className="opt-stat-value" style={{ color: '#d94f3d' }}>
                      {optResult.discarded_ids?.length} obs
                    </div>
                  </div>
                </div>

                <div className="baseline-row">
                  <div className="bc-cell naive">
                    <div className="bc-title">✕ Naive FIFO</div>
                    <div className="bc-line"><span>Mission Value</span> <strong>{optResult.baseline_value?.toFixed(1)}</strong></div>
                    <div className="bc-line"><span>Size</span> <strong>{(optResult.baseline_size_mb / 1024)?.toFixed(2)} GB</strong></div>
                  </div>
                  <div className="bc-cell orbitiq">
                    <div className="bc-title">✓ OrbitIQ ILP</div>
                    <div className="bc-line"><span>Mission Value</span> <strong>{optResult.total_value?.toFixed(1)}</strong></div>
                    <div className="bc-line"><span>Size</span> <strong>{(optResult.total_size_mb / 1024)?.toFixed(2)} GB</strong></div>
                  </div>
                </div>
              </div>
            </>
          )}

          {/* Map */}
          <div className="section-header" style={{ marginTop: 'auto' }}>
            <span className="sh-dot" /> Observation Coverage Map
          </div>
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
            <div className="map-wrap" style={{ flex: 1, minHeight: 180 }}>
              <MapContainer center={[20, 0]} zoom={1} scrollWheelZoom style={{ height: '100%', width: '100%' }}>
                <TileLayer
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  attribution="&copy; OpenStreetMap"
                />
                {observations.map(obs => (
                  <CircleMarker
                    key={obs.id}
                    center={[obs.latitude, obs.longitude]}
                    radius={markerR(obs)}
                    pathOptions={{
                      color: markerColor(obs),
                      fillColor: markerColor(obs),
                      fillOpacity: 0.8,
                      weight: selectedObs?.id === obs.id ? 2 : 0.8,
                    }}
                    eventHandlers={{ click: () => setSelectedObs(obs) }}
                  >
                    <Popup>
                      <div style={{ fontFamily: 'monospace', fontSize: '0.7rem', lineHeight: '1.6' }}>
                        <strong>{obs.id}</strong><br />
                        {obs.scene}<br />
                        IV: {obs.information_value?.toFixed(1)} · {obs.action}
                      </div>
                    </Popup>
                  </CircleMarker>
                ))}
              </MapContainer>
            </div>
            <div className="map-legend">
              <span><span className="legend-dot" style={{ background: '#5acc6e' }} />Transmit</span>
              <span><span className="legend-dot" style={{ background: '#e8a422' }} />Delay</span>
              <span><span className="legend-dot" style={{ background: '#d94f3d' }} />Discard</span>
            </div>
          </div>
        </div>

        {/* ══ MAIN PANEL ══ */}
        <div className="main-panel">

          {/* Chart */}
          <div className="section-header">
            <span className="sh-dot" /> Top 15 Observations — Information Value
          </div>
          <div className="chart-area">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 4, right: 8, left: -22, bottom: 28 }}>
                <XAxis
                  dataKey="scene"
                  tick={{ fontSize: 8, fontFamily: "'Share Tech Mono', monospace", fill: '#6a7e68' }}
                  interval={0}
                  angle={-30}
                  textAnchor="end"
                />
                <YAxis
                  domain={[0, 100]}
                  tick={{ fontSize: 8, fontFamily: "'Share Tech Mono', monospace", fill: '#6a7e68' }}
                />
                <Tooltip content={<ChartTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
                <Bar dataKey="information_value" maxBarSize={28}>
                  {chartData.map((d, i) => (
                    <Cell
                      key={i}
                      fill={
                        d.action === 'Transmit' ? '#5acc6e'
                        : d.action === 'Delay'  ? '#e8a422'
                        : d.action === 'Discard'? '#d94f3d'
                        : '#3a7a46'
                      }
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Queue */}
          <div className="section-header">
            <span className="sh-dot" /> Observation Queue ({observations.length})
          </div>
          <div className="queue-wrap">
            <table className="obs-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Event</th>
                  <th>Semantic</th>
                  <th>Novelty</th>
                  <th>Urgency</th>
                  <th>Mission</th>
                  <th>IV</th>
                  <th>Size MB</th>
                  <th>Value/MB</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {observations.map(obs => (
                  <tr
                    key={obs.id}
                    className={selectedObs?.id === obs.id ? 'sel' : ''}
                    onClick={() => setSelectedObs(obs)}
                  >
                    <td className="mono">{obs.id}</td>
                    <td>
                      {(obs.scene === 'Wildfire' || obs.scene === 'Flood') && (
                        <span style={{ color: '#d94f3d', marginRight: '0.3rem' }}>⚠</span>
                      )}
                      {obs.scene}
                    </td>
                    <td className="mono">{obs.semantic_score?.toFixed(1)}</td>
                    <td className="mono">{obs.novelty_score?.toFixed(1)}</td>
                    <td className="mono">{obs.urgency?.toFixed(1)}</td>
                    <td className="mono">{obs.mission_relevance?.toFixed(1)}</td>
                    <td className="mono" style={{ color: '#e8a422', fontWeight: 600 }}>
                      {obs.information_value?.toFixed(1)}
                    </td>
                    <td className="mono">{obs.compressed_size_mb?.toFixed(1)}</td>
                    <td className="mono" style={{ color: '#5acc6e' }}>
                      {obs.value_per_mb?.toFixed(3)}
                    </td>
                    <td>
                      <span className={`badge badge-${obs.action}`}>{obs.action}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* ══ RIGHT SIDEBAR — Transformer ══ */}
        <div className="sidebar-right">
          <TransformerPanel obs={selectedObs} />
        </div>

      </div>
    </div>
  );
}
