'use client';

import React, { useEffect, useState } from 'react';

interface InsiderTransaction {
  date: string;
  ticker: string;
  insider_name: string;
  role: string;
  transaction_type: string;
  shares: number;
  price: number;
  value: number;
  ownership_change_pct: number;
  score: number;
}

export default function Home() {
  const [data, setData] = useState<InsiderTransaction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/insider/latest`);
        if (!response.ok) throw new Error('Failed to fetch data');
        const json = await response.json();
        setData(json);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const formatNumber = (num: number) => new Intl.NumberFormat('id-ID').format(num);

  return (
    <div className="min-h-screen bg-background text-foreground p-4 font-sans">
      <header className="sticky top-0 z-10 bg-background border-b border-border-custom py-4 flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight">IDX OpenInsider</h1>
        <div className="flex gap-4">
          <input 
            type="text" 
            placeholder="Search Ticker..." 
            className="bg-[#161B22] border border-border-custom rounded px-3 py-1 focus:outline-none focus:ring-2 focus:ring-buy/50"
          />
        </div>
      </header>

      <main className="mt-8">
        {loading ? (
          <div className="flex justify-center py-10">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-buy"></div>
          </div>
        ) : error ? (
          <div className="bg-red-900/20 border border-red-500 text-red-500 p-4 rounded">
            Error loading data: {error}
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse border border-border-custom text-sm">
              <thead>
                <tr className="bg-[#161B22] text-left">
                  <th className="p-3 border border-border-custom">Date</th>
                  <th className="p-3 border border-border-custom">Ticker</th>
                  <th className="p-3 border border-border-custom">Insider Name</th>
                  <th className="p-3 border border-border-custom">Role</th>
                  <th className="p-3 border border-border-custom">Action</th>
                  <th className="p-3 border border-border-custom text-right">Shares</th>
                  <th className="p-3 border border-border-custom text-right">Price</th>
                  <th className="p-3 border border-border-custom text-right">Value (IDR)</th>
                  <th className="p-3 border border-border-custom text-right">Score</th>
                </tr>
              </thead>
              <tbody>
                {data.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="p-10 text-center text-gray-500">No insider activity found.</td>
                  </tr>
                ) : (
                  data.map((row, idx) => (
                    <tr key={idx} className="hover:bg-[#161B22] transition-colors border-b border-border-custom">
                      <td className="p-3 whitespace-nowrap">{row.date}</td>
                      <td className="p-3 font-bold text-blue-400">{row.ticker}</td>
                      <td className="p-3">{row.insider_name}</td>
                      <td className="p-3 italic text-gray-400">{row.role}</td>
                      <td className={`p-3 font-bold ${row.transaction_type === 'BUY' ? 'text-buy' : 'text-sell'}`}>
                        {row.transaction_type}
                      </td>
                      <td className="p-3 text-right tabular-nums">{formatNumber(row.shares)}</td>
                      <td className="p-3 text-right tabular-nums">{formatNumber(row.price)}</td>
                      <td className="p-3 text-right font-mono text-gray-300">{formatNumber(row.value)}</td>
                      <td className="p-3 text-center">
                        <span className={`px-2 py-1 rounded text-xs font-bold ${
                          row.score >= 5 ? 'bg-buy/20 text-buy' : 
                          row.score > 0 ? 'bg-blue-900/20 text-blue-400' : 
                          'bg-gray-800 text-gray-400'
                        }`}>
                          {row.score > 0 ? `+${row.score}` : row.score}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </main>
    </div>
  );
}
