'use client';

interface Leader {
    player: string;
    team: string;
    position: string;
    stat_value: number;
    games: number;
}

interface LeaderboardData {
    type: string;
    data: Leader[];
    stat: string;
    season: string;
}

interface LeaderboardTableProps {
    data: LeaderboardData;
}

export default function LeaderboardTable({ data }: LeaderboardTableProps) {
    const { data: leaders, stat, season } = data;

    return (
        <div className="w-full bg-white rounded-xl overflow-hidden border border-gray-200 shadow-md">
            <div className="p-4 bg-gradient-to-r from-blue-50 to-indigo-50 border-b border-gray-200 flex justify-between items-center">
                <h3 className="text-lg font-bold text-gray-900">🏆 {stat} Leaders ({season})</h3>
            </div>

            <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                    <thead>
                        <tr className="bg-gray-50 text-gray-600 text-xs uppercase tracking-wider">
                            <th className="p-3 text-center w-16">Rank</th>
                            <th className="p-3">Player</th>
                            <th className="p-3 text-center">Team</th>
                            <th className="p-3 text-right">{stat}</th>
                            <th className="p-3 text-right">Games</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                        {leaders.map((leader, index) => {
                            const rank = index + 1;
                            let rankIcon = <span className="text-gray-500 font-mono">#{rank}</span>;
                            if (rank === 1) rankIcon = <span className="text-2xl">🥇</span>;
                            if (rank === 2) rankIcon = <span className="text-2xl">🥈</span>;
                            if (rank === 3) rankIcon = <span className="text-2xl">🥉</span>;

                            return (
                                <tr key={index} className="hover:bg-gray-50 transition-colors">
                                    <td className="p-3 text-center font-bold">{rankIcon}</td>
                                    <td className="p-3">
                                        <div className="font-semibold text-gray-900">{leader.player}</div>
                                        <div className="text-xs text-gray-500">{leader.position}</div>
                                    </td>
                                    <td className="p-3 text-center">
                                        <span className="inline-block px-2 py-1 rounded bg-gray-100 text-xs font-mono text-gray-700 border border-gray-200">
                                            {leader.team}
                                        </span>
                                    </td>
                                    <td className="p-3 text-right font-mono font-bold text-blue-600">
                                        {leader.stat_value.toLocaleString()}
                                    </td>
                                    <td className="p-3 text-right font-mono text-gray-600">
                                        {leader.games}
                                    </td>
                                </tr>
                            );
                        })}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
