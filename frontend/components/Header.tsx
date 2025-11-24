'use client';

export default function Header() {
    return (
        <header className="w-full py-6 text-center">
            <div className="flex items-center justify-center gap-2 mb-2">
                <span className="text-3xl">🏈</span>
                <h1 className="text-3xl font-bold text-gray-900">
                    NFL Stats
                </h1>
            </div>
            <p className="text-gray-600 text-sm">
                Natural language search for NFL statistics
            </p>
        </header>
    );
}
