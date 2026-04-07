import React from 'react';

export default function Home() {
  const sampleData = [
    { date: '2024-03-20', ticker: 'GOTO', name: 'Patrick Walujo', role: 'Direksi', action: 'BUY', shares: '1,000,000', price: '70', value: '70,000,000', ownership: '+0.01%', score: '8' },
    { date: '2024-03-19', ticker: 'TLKM', name: 'Ririek Adriansyah', role: 'Direksi', action: 'SELL', shares: '500,000', price: '3,800', value: '1,900,000,000', ownership: '-0.005%', score: '2' },
  ];

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
        <div className="overflow-x-auto">
          <table className="w-full border-collapse border border-border-custom">
            <thead>
              <tr className="bg-[#161B22] text-left">
                <th className="p-3 border border-border-custom">Date</th>
                <th className="p-3 border border-border-custom">Ticker</th>
                <th className="p-3 border border-border-custom">Insider Name</th>
                <th className="p-3 border border-border-custom">Role</th>
                <th className="p-3 border border-border-custom">Action</th>
                <th className="p-3 border border-border-custom">Shares</th>
                <th className="p-3 border border-border-custom">Price</th>
                <th className="p-3 border border-border-custom">Value</th>
                <th className="p-3 border border-border-custom">Own Change</th>
                <th className="p-3 border border-border-custom">Score</th>
              </tr>
            </thead>
            <tbody>
              {sampleData.map((row, idx) => (
                <tr key={idx} className="hover:bg-[#161B22] transition-colors">
                  <td className="p-3 border border-border-custom">{row.date}</td>
                  <td className="p-3 border border-border-custom font-bold text-blue-400">{row.ticker}</td>
                  <td className="p-3 border border-border-custom">{row.name}</td>
                  <td className="p-3 border border-border-custom italic">{row.role}</td>
                  <td className={`p-3 border border-border-custom font-bold ${row.action === 'BUY' ? 'text-buy' : 'text-sell'}`}>
                    {row.action}
                  </td>
                  <td className="p-3 border border-border-custom text-right">{row.shares}</td>
                  <td className="p-3 border border-border-custom text-right">{row.price}</td>
                  <td className="p-3 border border-border-custom text-right font-mono">{row.value}</td>
                  <td className={`p-3 border border-border-custom text-right ${row.ownership.startsWith('+') ? 'text-buy' : 'text-sell'}`}>
                    {row.ownership}
                  </td>
                  <td className="p-3 border border-border-custom text-center">
                    <span className="bg-gray-700 px-2 py-1 rounded text-xs">{row.score}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  );
}
