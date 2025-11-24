'use client';

interface ExampleChipsProps {
    onSelect: (query: string) => void;
}

const EXAMPLES = [
    "Mahomes vs Allen 2024",
    "Saquon Barkley stats",
    "Eagles starting QB",
    "Trending players",
    "Lamar Jackson MVP"
];

export default function ExampleChips({ onSelect }: ExampleChipsProps) {
    return (
        <div className="w-full max-w-2xl mx-auto mt-6">
            <p className="text-gray-500 text-xs mb-3 text-center">Try these:</p>
            <div className="flex flex-wrap justify-center gap-2">
                {EXAMPLES.map((example, i) => (
                    <button
                        key={i}
                        onClick={() => onSelect(example)}
                        className="px-3 py-1.5 bg-gray-100 hover:bg-gray-200 border border-gray-300 rounded-md text-sm text-gray-700 transition-colors"
                    >
                        {example}
                    </button>
                ))}
            </div>
        </div>
    );
}
