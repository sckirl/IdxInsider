'use client';

import React, { useEffect, useState, useCallback } from 'react';

interface InsiderTransaction {
  id: number;
  date: string;
  ticker: string;
  insider_name: string;
  role: string;
  transaction_type: string;
  shares: string | number;
  price: string | number;
  value: string | number;
  score: number;
  score_reasons?: string; // JSON string
  rvol?: number;
  is_buyback?: boolean;
  price_history?: string; // JSON array
}

interface ClusterGroup {
  ticker: string;
  insider_count: number;
  transaction_count: number;
  last_date: string;
  total_value: number;
  insiders: string[];
  activity: InsiderTransaction[];
}

export default function Home() {
  const [viewMode, setViewMode] = useState<'recent' | 'cluster'>('recent');
  const [data, setData] = useState<InsiderTransaction[]>([]);
  const [clusters, setClusters] = useState<ClusterGroup[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isScraping, setIsScraping] = useState(false);
  
  // Cluster Filters
  const [minInsiders, setMinInsiders] = useState(2);
  const [clusterDays, setClusterDays] = useState(30);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
      
      if (viewMode === 'recent') {
        const response = await fetch(`${apiUrl}/insider/latest`, { cache: 'no-store' });
        if (!response.ok) throw new Error(`API Error: ${response.status}`);
        const json = await response.json();
        setData(json);
      } else {
        const response = await fetch(`${apiUrl}/insider/clusters?min_insiders=${minInsiders}&days=${clusterDays}`, { cache: 'no-store' });
        if (!response.ok) throw new Error(`API Error: ${response.status}`);
        const json = await response.json();
        setClusters(json);
      }
    } catch (err) {
      console.error('Fetch error:', err);
      setError(err instanceof Error ? err.message : 'Unknown connection error');
    } finally {
      setLoading(false);
    }
  }, [viewMode, minInsiders, clusterDays]);

  const triggerFullScrape = async () => {
    if (!confirm("This will scrape the FULL year 2026. It may take several minutes. Continue?")) return;
    setIsScraping(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
      const response = await fetch(`${apiUrl}/insider/scrape?full_year=true`);
      if (response.ok) {
        alert("Full 2026 Scraper triggered! Monitoring IDX history now.");
      } else {
        throw new Error("Failed to trigger full scrape");
      }
    } catch (err) {
      alert("Error: " + (err instanceof Error ? err.message : "Unknown error"));
    } finally {
      setIsScraping(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const formatNumber = (num: string | number) => {
    const n = typeof num === 'string' ? parseFloat(num) : num;
    if (isNaN(n)) return '0';
    return new Intl.NumberFormat('id-ID').format(n);
  };

  const filteredData = data.filter(t => 
    t.ticker.toUpperCase().includes(searchTerm.toUpperCase()) || 
    t.insider_name.toUpperCase().includes(searchTerm.toUpperCase())
  );

  return (
    <div className="min-h-screen bg-[#0D1117] text-[#C9D1D9] p-4 font-sans text-sm">
      <header className="sticky top-0 z-10 bg-[#0D1117]/90 backdrop-blur border-b border-[#30363D] py-3 flex items-center justify-between px-4">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 bg-blue-600 rounded flex items-center justify-center font-bold text-white text-xs">IX</div>
            <h1 className="text-lg font-bold tracking-tight text-[#F0F6FC]">IDX OpenInsider</h1>
          </div>
          
          <nav className="flex bg-[#161B22] rounded-lg p-1 border border-[#30363D]">
            <button 
              onClick={() => setViewMode('recent')}
              className={`px-4 py-1 rounded-md transition-all ${viewMode === 'recent' ? 'bg-[#21262D] text-white shadow-sm' : 'text-[#8B949E] hover:text-[#C9D1D9]'}`}
            >
              Latest Feed
            </button>
            <button 
              onClick={() => setViewMode('cluster')}
              className={`px-4 py-1 rounded-md transition-all ${viewMode === 'cluster' ? 'bg-[#21262D] text-white shadow-sm' : 'text-[#8B949E] hover:text-[#C9D1D9]'}`}
            >
              Cluster Buys 🔥
            </button>
          </nav>
        </div>

        <div className="flex gap-4 items-center">
          <div className="relative">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-[#8B949E]">🔍</span>
            <input 
              type="text" 
              placeholder="Filter Ticker/Name..." 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="bg-[#0D1117] border border-[#30363D] rounded-md pl-9 pr-4 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-500 text-xs w-64"
            />
          </div>
          <button 
            onClick={triggerFullScrape}
            disabled={isScraping}
            className={`text-xs bg-blue-600/10 text-blue-400 border border-blue-500/20 px-3 py-1.5 rounded hover:bg-blue-600/20 transition-all ${isScraping ? 'opacity-50' : ''}`}
          >
            {isScraping ? 'Scraping 2026...' : 'Scrape Full 2026'}
          </button>
        </div>
      </header>

      <main className="mt-6 max-w-[1600px] mx-auto px-4">
        {viewMode === 'cluster' && (
          <div className="mb-6 flex gap-6 items-center bg-[#161B22] p-4 rounded-lg border border-[#30363D]">
            <div className="flex flex-col gap-1">
              <label className="text-[10px] uppercase font-bold text-[#8B949E]">Min Unique Insiders</label>
              <input 
                type="number" 
                value={minInsiders} 
                onChange={(e) => setMinInsiders(parseInt(e.target.value))}
                className="bg-[#0D1117] border border-[#30363D] rounded px-2 py-1 w-20 text-white"
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-[10px] uppercase font-bold text-[#8B949E]">Rolling Window (Days)</label>
              <select 
                value={clusterDays} 
                onChange={(e) => setClusterDays(parseInt(e.target.value))}
                className="bg-[#0D1117] border border-[#30363D] rounded px-2 py-1 text-white"
              >
                <option value={7}>7 Days</option>
                <option value={30}>30 Days</option>
                <option value={90}>90 Days</option>
              </select>
            </div>
            <div className="ml-auto text-right">
              <p className="text-xs text-blue-400 font-medium">Found {clusters.length} Cluster Signals</p>
              <p className="text-[10px] text-[#8B949E]">Tracking high-conviction accumulation</p>
            </div>
          </div>
        )}

        {loading && (data.length === 0 && clusters.length === 0) ? (
          <div className="py-20 text-center text-[#8B949E] animate-pulse text-lg">
            📡 Synchronizing Institutional Intelligence...
          </div>
        ) : error ? (
          <div className="bg-red-900/10 border border-red-500/50 text-red-400 p-6 rounded-lg text-center">
            <p className="font-medium">Connection Error: {error}</p>
            <button onClick={fetchData} className="mt-4 bg-red-500 text-white px-4 py-1 rounded text-sm">Retry</button>
          </div>
        ) : viewMode === 'recent' ? (
          <div className="overflow-hidden rounded-lg border border-[#30363D] bg-[#161B22]">
            <table className="w-full border-collapse">
              <thead>
                <tr className="bg-[#0D1117] text-left border-b border-[#30363D]">
                  <th className="p-3 font-semibold text-[#8B949E]">Date</th>
                  <th className="p-3 font-semibold text-[#8B949E]">Ticker</th>
                  <th className="p-3 font-semibold text-[#8B949E]">Insider Name</th>
                  <th className="p-3 font-semibold text-[#8B949E]">Role</th>
                  <th className="p-3 font-semibold text-[#8B949E]">Action</th>
                  <th className="p-3 font-semibold text-[#8B949E] text-right">Value (IDR)</th>
                  <th className="p-3 font-semibold text-[#8B949E] text-center">RVOL</th>
                  <th className="p-3 font-semibold text-[#8B949E] text-center">Score</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#30363D]">
                {filteredData.map((row) => {
                  const reasons = row.score_reasons ? JSON.parse(row.score_reasons) : [];
                  return (
                    <tr key={row.id} className="hover:bg-[#1C2128] transition-colors group">
                      <td className="p-3 text-[#8B949E] whitespace-nowrap">{row.date}</td>
                      <td className="p-3">
                        <div className="flex flex-col">
                          <span className="font-bold text-blue-400">{row.ticker}</span>
                          {row.is_buyback && (
                            <span className="text-[8px] bg-purple-500/20 text-purple-400 border border-purple-500/30 px-1 rounded-sm mt-1 w-fit font-bold">
                              BUYBACK
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="p-3 font-medium text-[#F0F6FC]">{row.insider_name}</td>
                      <td className="p-3 text-[10px] text-[#8B949E] uppercase tracking-wider">{row.role?.replace('_', ' ')}</td>
                      <td className="p-3">
                        <span className={`px-2 py-0.5 rounded-sm text-[10px] font-bold ${
                          row.transaction_type === 'BUY' ? 'text-green-400 bg-green-400/10' : 'text-red-400 bg-red-400/10'
                        }`}>{row.transaction_type}</span>
                      </td>
                      <td className="p-3 text-right font-mono text-[#F0F6FC]">{formatNumber(row.value)}</td>
                      <td className="p-3 text-center">
                        {row.rvol && (
                          <span className={`text-[10px] font-bold ${row.rvol >= 2 ? 'text-orange-400' : 'text-[#8B949E]'}`}>
                            {row.rvol}x
                          </span>
                        )}
                      </td>
                      <td className="p-3 text-center">
                        <div className="relative inline-block group/tooltip">
                          <span className={`w-6 h-6 inline-flex items-center justify-center rounded-full text-[10px] font-bold cursor-help transition-all ${
                            row.score >= 5 ? 'bg-green-600 text-white shadow-[0_0_8px_rgba(22,163,74,0.4)]' : 'bg-[#30363D] text-[#8B949E]'
                          }`}>
                            {row.score > 0 ? `+${row.score}` : row.score}
                          </span>
                          
                          {/* Tooltip */}
                          <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-3 w-56 bg-[#21262D] border border-[#30363D] p-3 rounded-lg shadow-2xl opacity-0 invisible group-hover/tooltip:opacity-100 group-hover/tooltip:visible transition-all z-50 pointer-events-none">
                            <p className="text-[10px] font-bold text-white mb-2 border-b border-[#30363D] pb-1 uppercase tracking-tighter">Conviction Breakdown</p>
                            <ul className="space-y-1.5">
                              {reasons.map((r: string, i: number) => (
                                <li key={i} className="text-[10px] text-[#8B949E] flex justify-between gap-4">
                                  <span className="text-left">{r}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {clusters.map((cluster) => (
              <div key={cluster.ticker} className="bg-[#161B22] border border-[#30363D] rounded-lg overflow-hidden flex flex-col hover:border-blue-500/50 transition-colors">
                <div className="p-4 border-b border-[#30363D] flex justify-between items-start bg-[#0D1117]">
                  <div>
                    <h3 className="text-xl font-bold text-blue-400">{cluster.ticker}</h3>
                    <p className="text-[10px] text-[#8B949E] uppercase tracking-widest mt-1">High-Conviction Accumulation</p>
                  </div>
                  <div className="text-right">
                    <span className="bg-green-500/20 text-green-400 border border-green-500/30 px-2 py-1 rounded-md text-xs font-bold">
                      {cluster.insider_count} unique buyers
                    </span>
                    <p className="text-[10px] text-[#8B949E] mt-2">Latest: {cluster.last_date}</p>
                  </div>
                </div>
                <div className="p-4 flex-1">
                  <div className="flex justify-between mb-4">
                    <span className="text-[#8B949E]">30D Total Value:</span>
                    <span className="font-mono text-[#F0F6FC] font-bold">IDR {formatNumber(cluster.total_value)}</span>
                  </div>
                  <div className="space-y-2">
                    <p className="text-[10px] font-bold text-[#8B949E] uppercase">Participating Insiders:</p>
                    <div className="flex flex-wrap gap-1">
                      {cluster.insiders.map(name => (
                        <span key={name} className="bg-[#30363D] text-[#C9D1D9] px-2 py-0.5 rounded text-[10px]">{name}</span>
                      ))}
                    </div>
                  </div>
                </div>
                <div className="p-2 bg-[#0D1117]/50 border-t border-[#30363D] flex gap-2">
                   <button 
                    onClick={() => {
                      setSearchTerm(cluster.ticker);
                      setViewMode('recent');
                    }}
                    className="flex-1 bg-blue-600/10 text-blue-400 text-[10px] font-bold py-2 rounded hover:bg-blue-600/20"
                   >
                     INSPECT TRANSACTIONS
                   </button>
                   <a 
                    href={`https://stockbit.com/symbol/${cluster.ticker}`}
                    target="_blank"
                    className="bg-[#21262D] text-[#C9D1D9] text-[10px] font-bold px-3 py-2 rounded hover:bg-[#30363D]"
                   >
                     TRADE ↗
                   </a>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
