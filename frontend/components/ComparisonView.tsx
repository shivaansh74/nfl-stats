'use client';

import { motion } from 'framer-motion';

interface PlayerStats {
    name: string;
    team: string;
    position: string;
    games: number;
    averages: Record<string, number>;
    totals: Record<string, number>;
    headers: string[];
}

interface ComparisonData {
    type: string;
    data: PlayerStats[];
    season: string;
}

interface ComparisonViewProps {
    data: ComparisonData;
}

export default function ComparisonView({ data }: ComparisonViewProps) {
    const { data: players, season } = data;
    const [p1, p2] = players;

    return (
        <div className="w-full bg-white rounded-2xl overflow-hidden border border-gray-200 shadow-lg">
            {/* Header */}
            <div className="p-6 bg-gradient-to-r from-gray-50 to-gray-100 border-b border-gray-200">
                <h2 className="text-2xl font-bold text-gray-900 text-center mb-2">
                    ⚔️ Season Stats Comparison
                </h2>
                <p className="text-gray-600 text-center text-sm">{season} Season</p>
            </div>

            {/* Player Headers */}
            <div className="grid grid-cols-2 gap-4 p-6 bg-gray-50">
                {/* Player 1 */}
                <div className="text-center">
                    <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-br from-green-500 to-emerald-600 text-white text-3xl font-black mb-3 shadow-lg">
                        {p1.name.charAt(0)}
                    </div>
                    <h3 className="text-xl font-bold text-gray-900">{p1.name}</h3>
                    <div className="flex items-center justify-center gap-2 mt-2 text-sm">
                        <span className="bg-gray-200 text-gray-800 px-3 py-1 rounded-full font-mono">{p1.team}</span>
                        <span className="text-gray-600">{p1.position}</span>
                    </div>
                    <p className="text-gray-500 text-xs mt-1">{p1.games} games</p>
                </div>

                {/* Player 2 */}
                <div className="text-center">
                    <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 text-white text-3xl font-black mb-3 shadow-lg">
                        {p2.name.charAt(0)}
                    </div>
                    <h3 className="text-xl font-bold text-gray-900">{p2.name}</h3>
                    <div className="flex items-center justify-center gap-2 mt-2 text-sm">
                        <span className="bg-gray-200 text-gray-800 px-3 py-1 rounded-full font-mono">{p2.team}</span>
                        <span className="text-gray-600">{p2.position}</span>
                    </div>
                    <p className="text-gray-500 text-xs mt-1">{p2.games} games</p>
                </div>
            </div>

            {/* Stats Grid */}
            <div className="p-6 space-y-3">
                {p1.headers.map((stat, idx) => {
                    const val1 = p1.averages[stat] || 0;
                    const val2 = p2.averages[stat] || 0;

                    // Determine winner (lower is better for INT)
                    let winner: 'p1' | 'p2' | 'tie' = 'tie';
                    if (stat === 'INT') {
                        winner = val1 < val2 ? 'p1' : val1 > val2 ? 'p2' : 'tie';
                    } else {
                        winner = val1 > val2 ? 'p1' : val1 < val2 ? 'p2' : 'tie';
                    }

                    return (
                        <motion.div
                            key={stat}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: idx * 0.05 }}
                            className="grid grid-cols-3 gap-4 items-center p-4 bg-gray-50 rounded-xl border border-gray-200 hover:bg-gray-100 transition-colors"
                        >
                            {/* Player 1 Value */}
                            <div className={`text-right font-mono font-bold text-lg ${winner === 'p1' ? 'text-green-600' : 'text-gray-500'
                                }`}>
                                {val1.toFixed(1)}
                                {winner === 'p1' && <span className="ml-2">👑</span>}
                            </div>

                            {/* Stat Name */}
                            <div className="text-center">
                                <span className="text-gray-700 font-semibold text-sm">{stat}</span>
                            </div>

                            {/* Player 2 Value */}
                            <div className={`text-left font-mono font-bold text-lg ${winner === 'p2' ? 'text-blue-600' : 'text-gray-500'
                                }`}>
                                {winner === 'p2' && <span className="mr-2">👑</span>}
                                {val2.toFixed(1)}
                            </div>
                        </motion.div>
                    );
                })}
            </div>
        </div>
    );
}
