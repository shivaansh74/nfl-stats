'use client';

import { motion } from 'framer-motion';
import { useState, useMemo } from 'react';
import PlayAnimation from './PlayAnimation';
import ComparisonView from './ComparisonView';
import PlayerCard from './PlayerCard';

import LeaderboardTable from './LeaderboardTable';
import TrendingPlayers from './TrendingPlayers';
import FantasyPointsCard from './FantasyPointsCard';
import RosterView from './RosterView';

interface ResultCardProps {
    content: string;
    html?: string;
    query: string;
    data?: any;
}

export default function ResultCard({ content, html, query, data }: ResultCardProps) {
    const [copied, setCopied] = useState(false);
    const [showRaw, setShowRaw] = useState(false);

    const handleCopy = () => {
        navigator.clipboard.writeText(content);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    // Detect if this is a longest play query and extract play data
    const playData = useMemo(() => {
        const lowerQuery = query.toLowerCase();
        const isLongestPlay = lowerQuery.includes('longest') &&
            (lowerQuery.includes('catch') || lowerQuery.includes('run') ||
                lowerQuery.includes('pass') || lowerQuery.includes('reception'));

        if (!isLongestPlay) return null;

        // Try to parse play data from content
        try {
            // Look for key patterns in the output
            const yardMatch = content.match(/Distance[:\s]+(\d+)\s+yards/i);
            const touchdownMatch = content.match(/TOUCHDOWN/i);
            const opponentMatch = content.match(/Opponent[:\s]+(\w+)/i);
            const weekMatch = content.match(/Week[:\s]+(\d+)/i);
            const seasonMatch = content.match(/Season[:\s]+(\d+)/i);
            const passerMatch = content.match(/From[:\s]+([^\n]+)/i);
            const receiverMatch = content.match(/To[:\s]+([^\n]+)/i);
            const descMatch = content.match(/Play[:\s]+([^\n]+)/i);

            let playType = 'rushing';
            if (lowerQuery.includes('catch') || lowerQuery.includes('reception')) {
                playType = 'receiving';
            } else if (lowerQuery.includes('pass')) {
                playType = 'passing';
            }

            return {
                type: playType,
                yards: yardMatch ? parseInt(yardMatch[1]) : 0,
                touchdown: !!touchdownMatch,
                description: descMatch ? descMatch[1].trim() : '',
                opponent: opponentMatch ? opponentMatch[1] : '',
                week: weekMatch ? parseInt(weekMatch[1]) : undefined,
                season: seasonMatch ? parseInt(seasonMatch[1]) : undefined,
                passer: passerMatch ? passerMatch[1].trim() : undefined,
                receiver: receiverMatch ? receiverMatch[1].trim() : undefined,
                yardline_100: undefined // We'll need to pass this from the API
            };
        } catch (e) {
            return null;
        }
    }, [query, content]);

    // Render Rich Views if data is available
    if (data) {
        if (data.type === 'comparison') {
            return (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="w-full max-w-4xl mx-auto mt-8"
                >
                    <ComparisonView data={data} />

                    <div className="mt-4 text-center">
                        <button
                            onClick={() => setShowRaw(!showRaw)}
                            className="text-xs text-slate-500 hover:text-slate-300 underline"
                        >
                            {showRaw ? 'Hide Raw Output' : 'Show Raw Output'}
                        </button>
                    </div>

                    {showRaw && (
                        <div className="mt-4 bg-slate-950/90 border border-slate-800 rounded-xl overflow-hidden p-4">
                            <pre className="font-mono text-xs text-slate-400 whitespace-pre-wrap">{content}</pre>
                        </div>
                    )}
                </motion.div>
            );
        }

        if (data.type === 'bio') {
            return (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="w-full max-w-4xl mx-auto mt-8"
                >
                    <PlayerCard data={data} />
                </motion.div>
            );
        }

        if (data.type === 'league_leaders') {
            return (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="w-full max-w-4xl mx-auto mt-8"
                >
                    <LeaderboardTable data={data} />
                </motion.div>
            );
        }

        if (data.type === 'trending') {
            return (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="w-full max-w-4xl mx-auto mt-8"
                >
                    <TrendingPlayers data={data} />
                </motion.div>
            );
        }

        if (data.type === 'fantasy_points') {
            return (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="w-full max-w-4xl mx-auto mt-8"
                >
                    <FantasyPointsCard data={data} />
                </motion.div>
            );
        }

        if (data.type === 'roster') {
            return (
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="w-full max-w-4xl mx-auto mt-8"
                >
                    <RosterView data={data} />
                </motion.div>
            );
        }
    }

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="w-full max-w-4xl mx-auto mt-8"
        >
            <div className="bg-white border border-gray-200 rounded-2xl overflow-hidden shadow-lg">
                {/* Window Header */}
                <div className="flex items-center justify-between px-4 py-3 bg-gray-50 border-b border-gray-200">
                    <div className="flex items-center gap-2">
                        <div className="flex gap-1.5">
                            <div className="w-3 h-3 rounded-full bg-red-100 border border-red-300" />
                            <div className="w-3 h-3 rounded-full bg-yellow-100 border border-yellow-300" />
                            <div className="w-3 h-3 rounded-full bg-green-100 border border-green-300" />
                        </div>
                        <span className="ml-3 text-xs font-mono text-gray-500">nfl-stats-cli — {query}</span>
                    </div>

                    <button
                        onClick={handleCopy}
                        className="text-xs font-medium text-gray-600 hover:text-gray-900 transition-colors flex items-center gap-1.5 px-2 py-1 rounded hover:bg-gray-100"
                    >
                        {copied ? (
                            <>
                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-3.5 h-3.5 text-green-600">
                                    <path fillRule="evenodd" d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z" clipRule="evenodd" />
                                </svg>
                                <span className="text-green-600">Copied</span>
                            </>
                        ) : (
                            <>
                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-3.5 h-3.5">
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 17.25v3.375c0 .621-.504 1.125-1.125 1.125h-9.75a1.125 1.125 0 01-1.125-1.125V7.875c0-.621.504-1.125 1.125-1.125H6.75a9.06 9.06 0 011.5.124m7.5 10.376h3.375c.621 0 1.125-.504 1.125-1.125V11.25c0-4.46-3.243-8.161-7.5-8.876a9.06 9.06 0 00-1.5-.124H9.375c-.621 0-1.125.504-1.125 1.125v3.5m7.5 10.375H9.375a1.125 1.125 0 01-1.125-1.125v-9.25m12 6.625v-1.875a3.375 3.375 0 00-3.375-3.375h-1.5" />
                                </svg>
                                <span>Copy Output</span>
                            </>
                        )}
                    </button>
                </div>

                {/* Content */}
                <div className="p-6 bg-white">
                    {playData ? (
                        <div className="mb-6">
                            <PlayAnimation playData={playData} />
                        </div>
                    ) : null}

                    {html ? (
                        <div
                            className="prose prose-sm max-w-none [&_pre]:bg-gray-50 [&_pre]:border [&_pre]:border-gray-200 [&_pre]:rounded-lg [&_pre]:p-4 [&_pre]:text-gray-900 [&_table]:border [&_table]:border-gray-200 [&_th]:bg-gray-50 [&_th]:text-gray-900 [&_td]:text-gray-700"
                            dangerouslySetInnerHTML={{ __html: html }}
                        />
                    ) : (
                        <pre className="font-mono text-sm text-gray-700 whitespace-pre-wrap bg-gray-50 p-4 rounded-lg border border-gray-200">
                            {content}
                        </pre>
                    )}
                </div>
            </div>
        </motion.div>
    );
}
