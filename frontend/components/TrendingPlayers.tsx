'use client';

interface TrendingPlayer {
    name: string;
    position?: string;
    team?: string;
    count: number;
}

interface TrendingData {
    type: string;
    data: TrendingPlayer[];
}

interface TrendingPlayersProps {
    data: TrendingData;
}

export default function TrendingPlayers({ data }: TrendingPlayersProps) {
    const { data: players } = data;

    return (
        <div className="w-full bg-white rounded-xl overflow-hidden border border-gray-200 shadow-md">
            <div className="p-4 bg-gradient-to-r from-orange-50 to-red-50 border-b border-gray-200 flex justify-between items-center">
                <h3 className="text-lg font-bold text-gray-900">🔥 Trending Players (Most Added)</h3>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 p-4">
                {players.map((player, index) => (
                    <div
                        key={index}
                        className="flex items-center justify-between p-3 bg-gray-50 border border-gray-200 rounded-lg hover:bg-gray-100 transition-colors"
                    >
                        <div className="flex items-center gap-3">
                            <div className={`
                                w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm
                                ${index === 0 ? 'bg-yellow-100 text-yellow-700 border-2 border-yellow-400' :
                                    index === 1 ? 'bg-gray-200 text-gray-700 border-2 border-gray-400' :
                                        index === 2 ? 'bg-orange-100 text-orange-700 border-2 border-orange-400' :
                                            'bg-gray-100 text-gray-600 border border-gray-300'}
                            `}>
                                {index + 1}
                            </div>
                            <div>
                                <div className="font-semibold text-gray-900">{player.name}</div>
                                <div className="text-xs text-gray-600">
                                    {player.team || 'FA'} • {player.position || 'N/A'}
                                </div>
                            </div>
                        </div>
                        <div className="text-right">
                            <div className="text-green-600 font-mono font-bold text-sm">+{player.count}</div>
                            <div className="text-[10px] text-gray-500 uppercase">Adds</div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
