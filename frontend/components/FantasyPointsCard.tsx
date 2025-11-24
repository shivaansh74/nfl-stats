'use client';

import { motion } from 'framer-motion';

interface FantasyPointsProps {
    data: {
        type: string;
        data: {
            total: number;
            breakdown: Record<string, number>;
            player: {
                display_name: string;
                position: string;
                team_abbr: string;
            };
            season: string;
        };
    };
}

export default function FantasyPointsCard({ data }: FantasyPointsProps) {
    const { total, breakdown, player, season } = data.data;

    // Sort breakdown by points descending
    const sortedBreakdown = Object.entries(breakdown)
        .sort(([, a], [, b]) => b - a);

    return (
        <div className="w-full bg-slate-900/80 backdrop-blur-md rounded-2xl overflow-hidden border border-slate-700 shadow-2xl">
            {/* Header */}
            <div className="relative p-6 bg-gradient-to-r from-purple-900/50 to-indigo-900/50 border-b border-slate-700">
                <div className="absolute top-0 right-0 p-4 opacity-10">
                    <span className="text-8xl">🏈</span>
                </div>

                <div className="relative z-10 flex justify-between items-start">
                    <div>
                        <h2 className="text-2xl font-bold text-white mb-1">{player.display_name}</h2>
                        <div className="flex items-center gap-2 text-slate-300 text-sm">
                            <span className="bg-slate-800 px-2 py-0.5 rounded border border-slate-600 font-mono">{player.team_abbr}</span>
                            <span>•</span>
                            <span>{player.position}</span>
                            <span>•</span>
                            <span className="text-purple-300">{season} Season</span>
                        </div>
                    </div>

                    <div className="text-right">
                        <div className="text-xs text-purple-300 uppercase tracking-wider font-semibold mb-1">Total Points (PPR)</div>
                        <div className="text-5xl font-black text-transparent bg-clip-text bg-gradient-to-br from-white to-purple-200 drop-shadow-lg">
                            {total.toFixed(1)}
                        </div>
                    </div>
                </div>
            </div>

            {/* Breakdown */}
            <div className="p-6">
                <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">Scoring Breakdown</h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {sortedBreakdown.map(([category, points], index) => (
                        <motion.div
                            key={category}
                            initial={{ opacity: 0, x: -10 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: index * 0.05 }}
                            className="flex items-center justify-between p-3 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:bg-slate-800/60 transition-colors"
                        >
                            <span className="text-slate-300 font-medium">{category}</span>
                            <div className="flex items-center gap-2">
                                <div className="h-1.5 w-16 bg-slate-700 rounded-full overflow-hidden">
                                    <motion.div
                                        initial={{ width: 0 }}
                                        animate={{ width: `${Math.min(100, (points / total) * 100 * 3)}%` }} // Scale up for visibility
                                        className="h-full bg-purple-500 rounded-full"
                                    />
                                </div>
                                <span className="text-white font-mono font-bold w-12 text-right">{points.toFixed(1)}</span>
                            </div>
                        </motion.div>
                    ))}
                </div>
            </div>
        </div>
    );
}
