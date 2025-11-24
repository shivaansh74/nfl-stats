'use client';

import { useState } from 'react';
import Header from '@/components/Header';
import SearchInput from '@/components/SearchInput';
import ExampleChips from '@/components/ExampleChips';
import ResultCard from '@/components/ResultCard';

export default function Home() {
  const [query, setQuery] = useState('');
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSearch = async (searchQuery?: string) => {
    const q = searchQuery || query;
    if (!q.trim()) return;

    if (searchQuery) setQuery(searchQuery);

    setLoading(true);
    setError('');
    setResult(null);

    try {
      const response = await fetch('http://localhost:8000/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: q })
      });

      const data = await response.json();

      if (data.success) {
        setResult(data);
      } else {
        setError(data.error || 'Failed to process query');
      }
    } catch (err) {
      setError('Failed to connect to API. Make sure the backend is running on port 8000.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-white">
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        <Header />

        <div className="mt-12">
          <SearchInput
            value={query}
            onChange={setQuery}
            onSearch={() => handleSearch()}
            loading={loading}
          />

          {!result && !loading && <ExampleChips onSelect={handleSearch} />}
        </div>

        {/* Error Message */}
        {error && (
          <div className="mt-8 max-w-2xl mx-auto p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-800 text-sm">{error}</p>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="mt-12 text-center">
            <div className="inline-block w-8 h-8 border-4 border-gray-200 border-t-blue-600 rounded-full animate-spin"></div>
            <p className="mt-3 text-gray-600 text-sm">Searching...</p>
          </div>
        )}

        {/* Results */}
        {result && !loading && (
          <ResultCard
            content={result.output}
            html={result.html_output}
            query={result.query}
            data={result.data}
          />
        )}

        {/* Footer */}
        <footer className="mt-16 text-center text-gray-500 text-xs border-t border-gray-200 pt-8">
          <p>NFL Stats • Data from ESPN & nflverse</p>
        </footer>
      </div>
    </main>
  );
}
