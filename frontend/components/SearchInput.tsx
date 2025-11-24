'use client';

interface SearchInputProps {
    value: string;
    onChange: (value: string) => void;
    onSearch: () => void;
    loading: boolean;
}

export default function SearchInput({ value, onChange, onSearch, loading }: SearchInputProps) {
    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !loading) {
            onSearch();
        }
    };

    return (
        <div className="w-full max-w-2xl mx-auto">
            <div className="relative">
                <input
                    type="text"
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Ask about any NFL player or team..."
                    className="w-full px-4 py-3 pr-24 text-base bg-white border-2 border-gray-300 rounded-lg text-gray-900 placeholder-gray-400 focus:outline-none focus:border-blue-500 transition-colors"
                    disabled={loading}
                />

                <button
                    onClick={onSearch}
                    disabled={loading || !value.trim()}
                    className="absolute right-2 top-2 bottom-2 px-5 bg-blue-600 hover:bg-blue-700 text-white rounded-md font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    {loading ? 'Searching...' : 'Search'}
                </button>
            </div>
        </div>
    );
}
