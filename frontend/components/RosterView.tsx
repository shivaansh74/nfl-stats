'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';

interface RosterViewProps {
    data: {
        type: string;
        data: {
            team: {
                name: string;
                abbr: string;
                logo?: string;
            };
            position: string;
            players: Array<{
                display_name: string;
                position: string;
                jersey?: string;
                experience?: number;
                college?: string;
                status?: string;
                height?: string;
                weight?: string;
                headshot_url?: string;
                rookie_season?: string;
            }>;
        };
    };
}

export default function RosterView({ data }: RosterViewProps) {
    const { team, position, players } = data.data;
    const [selectedPlayer, setSelectedPlayer] = useState<any>(null);

    // If showing full roster (position === "ALL"), group by position
    if (position === "ALL") {
        // Group players by position
        const byPosition: Record<string, typeof players> = {};
        players.forEach(player => {
            const pos = player.position || 'N/A';
            if (!byPosition[pos]) byPosition[pos] = [];
            byPosition[pos].push(player);
        });

        const positionOrder = ['QB', 'RB', 'WR', 'TE', 'C', 'G', 'T', 'OL', 'DE', 'DT', 'DL', 'LB', 'CB', 'S', 'DB', 'K', 'P', 'LS'];

        return (
            <>
                <div className="w-full bg-white rounded-xl overflow-hidden border border-gray-200 shadow-md">
                    <div className="p-4 bg-blue-600 text-white">
                        <h3 className="text-xl font-bold">🏈 {team.name}</h3>
                        <p className="text-sm text-blue-100 mt-1">2024-25 Season • {players.length} Players</p>
                    </div>

                    <div className="p-4 space-y-6">
                        {positionOrder.map(pos => {
                            if (!byPosition[pos] || byPosition[pos].length === 0) return null;

                            return (
                                <div key={pos}>
                                    <h4 className="text-sm font-bold text-gray-700 mb-3 pb-2 border-b border-gray-200">
                                        {pos} ({byPosition[pos].length})
                                    </h4>
                                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                                        {byPosition[pos].map((player, idx) => (
                                            <div
                                                key={idx}
                                                className="flex items-center gap-2 p-2 bg-gray-50 rounded border border-gray-200 hover:bg-blue-50 hover:border-blue-200 cursor-pointer transition-colors"
                                                onClick={() => setSelectedPlayer(player)}
                                            >
                                                <div className="w-10 h-10 flex-shrink-0 rounded-full overflow-hidden bg-gray-200 border border-gray-300">
                                                    {player.headshot_url ? (
                                                        <img src={player.headshot_url} alt={player.display_name} className="w-full h-full object-cover" />
                                                    ) : (
                                                        <div className="w-full h-full flex items-center justify-center bg-blue-600 text-white font-bold text-xs">
                                                            {player.jersey || '—'}
                                                        </div>
                                                    )}
                                                </div>
                                                <div className="flex-1 min-w-0">
                                                    <div className="font-medium text-sm text-gray-900 truncate">
                                                        {player.display_name}
                                                    </div>
                                                    <div className="text-xs text-gray-500 truncate">
                                                        #{player.jersey || '—'} • {player.height || '—'} • {player.weight || '—'}
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            );
                        })}

                        {/* Show any other positions not in the standard order */}
                        {Object.keys(byPosition)
                            .filter(pos => !positionOrder.includes(pos))
                            .map(pos => (
                                <div key={pos}>
                                    <h4 className="text-sm font-bold text-gray-700 mb-3 pb-2 border-b border-gray-200">
                                        {pos} ({byPosition[pos].length})
                                    </h4>
                                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
                                        {byPosition[pos].map((player, idx) => (
                                            <div
                                                key={idx}
                                                className="flex items-center gap-2 p-2 bg-gray-50 rounded border border-gray-200 hover:bg-blue-50 hover:border-blue-200 cursor-pointer transition-colors"
                                                onClick={() => setSelectedPlayer(player)}
                                            >
                                                <div className="w-10 h-10 flex-shrink-0 rounded-full overflow-hidden bg-gray-200 border border-gray-300">
                                                    {player.headshot_url ? (
                                                        <img src={player.headshot_url} alt={player.display_name} className="w-full h-full object-cover" />
                                                    ) : (
                                                        <div className="w-full h-full flex items-center justify-center bg-blue-600 text-white font-bold text-xs">
                                                            {player.jersey || '—'}
                                                        </div>
                                                    )}
                                                </div>
                                                <div className="flex-1 min-w-0">
                                                    <div className="font-medium text-sm text-gray-900 truncate">
                                                        {player.display_name}
                                                    </div>
                                                    <div className="text-xs text-gray-500 truncate">
                                                        #{player.jersey || '—'} • {player.height || '—'} • {player.weight || '—'}
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            ))}
                    </div>
                </div>
                <PlayerBioModal player={selectedPlayer} team={team} onClose={() => setSelectedPlayer(null)} />
            </>
        );
    }

    // Check if this is a grouped position display (e.g., LB showing WLB, SLB, etc.)
    const isGrouped = (data.data as any).grouped;

    if (isGrouped && players && players.length > 0) {
        // Group players by their specific position
        const byPosition: Record<string, typeof players> = {};
        players.forEach(player => {
            const pos = player.position || 'N/A';
            if (!byPosition[pos]) byPosition[pos] = [];
            byPosition[pos].push(player);
        });

        return (
            <>
                <div className="w-full bg-white rounded-xl overflow-hidden border border-gray-200 shadow-md">
                    <div className="p-4 bg-blue-600 text-white">
                        <h3 className="text-xl font-bold">🏈 {team.name} {position}s</h3>
                        <p className="text-sm text-blue-100 mt-1">{players.length} Players</p>
                    </div>

                    <div className="p-4 space-y-6">
                        {Object.keys(byPosition).sort().map(specificPos => {
                            const posPlayers = byPosition[specificPos];

                            return (
                                <div key={specificPos}>
                                    <h4 className="text-sm font-bold text-gray-700 mb-3 pb-2 border-b border-gray-200">
                                        {specificPos} ({posPlayers.length})
                                    </h4>
                                    <div className="space-y-2">
                                        {posPlayers.map((player, idx) => (
                                            <div
                                                key={idx}
                                                className="flex items-center gap-3 p-2 bg-gray-50 border border-gray-200 rounded cursor-pointer hover:bg-blue-50 hover:border-blue-200 transition-colors"
                                                onClick={() => setSelectedPlayer(player)}
                                            >
                                                <div className="w-10 h-10 flex-shrink-0 rounded-full overflow-hidden bg-white border border-gray-300">
                                                    {player.headshot_url ? (
                                                        <img src={player.headshot_url} alt={player.display_name} className="w-full h-full object-cover" />
                                                    ) : (
                                                        <div className="w-full h-full flex items-center justify-center bg-blue-600 text-white font-bold text-sm">
                                                            {player.jersey || '—'}
                                                        </div>
                                                    )}
                                                </div>
                                                <div className="flex-1 min-w-0">
                                                    <div className="font-medium text-gray-900 text-sm">
                                                        {idx + 1}. {player.display_name}
                                                    </div>
                                                    <div className="text-xs text-gray-600">
                                                        #{player.jersey || '—'} • {player.height || '—'} • {player.weight || '—'}
                                                    </div>
                                                    <div className="text-xs text-gray-500">
                                                        {player.experience ? `${player.experience} yrs` : 'Rookie'} • {player.college || 'N/A'}
                                                    </div>
                                                </div>
                                                <div className="flex-shrink-0">
                                                    {player.status?.toUpperCase() === 'ACT' ? (
                                                        <span className="text-green-500 text-xl">✓</span>
                                                    ) : (
                                                        <span className="text-gray-400 text-xl">○</span>
                                                    )}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
                <PlayerBioModal player={selectedPlayer} team={team} onClose={() => setSelectedPlayer(null)} />
            </>
        );
    }

    // Single position view
    if (!players || players.length === 0) {
        return (
            <div className="w-full bg-white rounded-xl p-8 text-center border border-gray-200">
                <p className="text-gray-500">No players found for this position.</p>
            </div>
        );
    }

    const starter = players[0];
    const depth = players.slice(1);

    return (
        <>
            <div className="w-full bg-white rounded-xl overflow-hidden border border-gray-200 shadow-md">
                <div className="p-4 bg-blue-600 text-white">
                    <h3 className="text-lg font-bold">{team.name} {position}</h3>
                </div>

                <div className="p-4 space-y-4">
                    {/* Starter */}
                    <div>
                        <div className="text-xs font-bold text-green-600 uppercase mb-2">Starter</div>
                        <div
                            className="flex items-center gap-3 p-3 bg-green-50 border-2 border-green-200 rounded-lg cursor-pointer hover:bg-green-100 transition-colors"
                            onClick={() => setSelectedPlayer(starter)}
                        >
                            <div className="w-16 h-16 flex-shrink-0 rounded-full overflow-hidden bg-white border-2 border-green-200 shadow-sm">
                                {starter.headshot_url ? (
                                    <img src={starter.headshot_url} alt={starter.display_name} className="w-full h-full object-cover" />
                                ) : (
                                    <div className="w-full h-full flex items-center justify-center bg-green-600 text-white font-bold text-xl">
                                        {starter.jersey || '—'}
                                    </div>
                                )}
                            </div>
                            <div>
                                <div className="font-bold text-gray-900 text-lg">{starter.display_name}</div>
                                <div className="text-sm text-gray-600 font-medium">
                                    #{starter.jersey || '—'} • {starter.position} • {starter.height || '—'} • {starter.weight || '—'}
                                </div>
                                <div className="text-xs text-gray-500 mt-1">
                                    {starter.experience ? `${starter.experience} yrs` : 'Rookie'} • {starter.college || 'N/A'}
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Depth */}
                    {depth.length > 0 && (
                        <div>
                            <div className="text-xs font-bold text-gray-500 uppercase mb-2">Depth</div>
                            <div className="space-y-2">
                                {depth.map((player, idx) => (
                                    <div
                                        key={idx}
                                        className="flex items-center gap-3 p-2 bg-gray-50 border border-gray-200 rounded cursor-pointer hover:bg-gray-100 transition-colors"
                                        onClick={() => setSelectedPlayer(player)}
                                    >
                                        <div className="w-10 h-10 flex-shrink-0 rounded-full overflow-hidden bg-white border border-gray-300">
                                            {player.headshot_url ? (
                                                <img src={player.headshot_url} alt={player.display_name} className="w-full h-full object-cover" />
                                            ) : (
                                                <div className="w-full h-full flex items-center justify-center bg-gray-600 text-white font-bold text-sm">
                                                    {player.jersey || '—'}
                                                </div>
                                            )}
                                        </div>
                                        <div>
                                            <div className="font-medium text-gray-900 text-sm">{player.display_name}</div>
                                            <div className="text-xs text-gray-600">
                                                #{player.jersey || '—'} • {player.position} • {player.height || '—'} • {player.weight || '—'}
                                            </div>
                                            <div className="text-xs text-gray-500">
                                                {player.experience ? `${player.experience} yrs` : 'Rookie'} • {player.college || 'N/A'}
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            </div>
            <PlayerBioModal player={selectedPlayer} team={team} onClose={() => setSelectedPlayer(null)} />
        </>
    );
}

function PlayerBioModal({ player, team, onClose }: { player: any, team: any, onClose: () => void }) {
    if (!player) return null;

    return (
        <AnimatePresence>
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm" onClick={onClose}>
                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    onClick={(e) => e.stopPropagation()}
                    className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden relative"
                >
                    <button
                        onClick={onClose}
                        className="absolute top-4 right-4 p-2 bg-black/20 hover:bg-black/40 text-white rounded-full transition-colors z-10"
                    >
                        <X size={20} />
                    </button>

                    {/* Header with Image */}
                    <div className="relative h-48 bg-gradient-to-br from-blue-600 to-indigo-800">
                        <div className="absolute inset-0 opacity-20 bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')]"></div>
                        <div className="absolute -bottom-12 left-1/2 -translate-x-1/2">
                            <div className="w-32 h-32 rounded-full border-4 border-white shadow-lg overflow-hidden bg-white">
                                {player.headshot_url ? (
                                    <img src={player.headshot_url} alt={player.display_name} className="w-full h-full object-cover" />
                                ) : (
                                    <div className="w-full h-full flex items-center justify-center bg-gray-200 text-gray-400 text-4xl font-bold">
                                        {player.display_name.charAt(0)}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Content */}
                    <div className="pt-16 pb-8 px-6 text-center">
                        <h2 className="text-2xl font-bold text-gray-900">{player.display_name}</h2>
                        <p className="text-blue-600 font-medium">
                            #{player.jersey || '—'} • {player.position} • {team.name}
                        </p>

                        <div className="mt-6 grid grid-cols-2 gap-4">
                            <div className="p-3 bg-gray-50 rounded-xl border border-gray-100">
                                <div className="text-sm text-gray-500 uppercase tracking-wider font-semibold">Height</div>
                                <div className="text-lg font-bold text-gray-900">{player.height || '—'}</div>
                            </div>
                            <div className="p-3 bg-gray-50 rounded-xl border border-gray-100">
                                <div className="text-sm text-gray-500 uppercase tracking-wider font-semibold">Weight</div>
                                <div className="text-lg font-bold text-gray-900">{player.weight || '—'}</div>
                            </div>
                            <div className="p-3 bg-gray-50 rounded-xl border border-gray-100">
                                <div className="text-sm text-gray-500 uppercase tracking-wider font-semibold">Experience</div>
                                <div className="text-lg font-bold text-gray-900">{player.experience ? `${player.experience} yrs` : 'Rookie'}</div>
                            </div>
                            <div className="p-3 bg-gray-50 rounded-xl border border-gray-100">
                                <div className="text-sm text-gray-500 uppercase tracking-wider font-semibold">College</div>
                                <div className="text-lg font-bold text-gray-900 truncate" title={player.college}>{player.college || '—'}</div>
                            </div>
                        </div>

                        {player.status && (
                            <div className="mt-6">
                                <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${player.status === 'Active' || player.status === 'ACT'
                                    ? 'bg-green-100 text-green-800'
                                    : 'bg-yellow-100 text-yellow-800'
                                    }`}>
                                    Status: {player.status}
                                </div>
                            </div>
                        )}
                    </div>
                </motion.div>
            </div>
        </AnimatePresence>
    );
}
