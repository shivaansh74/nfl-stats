'use client';

import { motion } from 'framer-motion';

interface PlayerCardProps {
    data: {
        type: string;
        data: {
            name: string;
            position: string;
            team: string | null;
            status: string | null;
            age?: number;
            college?: string;
            height?: string;
            weight?: string;
            years_exp?: number;
            rookie_season?: string;
        };
        player: any;
    };
}

export default function PlayerCard({ data }: PlayerCardProps) {
    const { data: bio } = data;

    const formatHeight = (inches: string) => {
        const totalInches = parseInt(inches);
        const feet = Math.floor(totalInches / 12);
        const remainingInches = totalInches % 12;
        return `${feet}'${remainingInches}"`;
    };

    return (
        <div className="w-full max-w-md mx-auto bg-white rounded-2xl overflow-hidden border border-gray-200 shadow-lg">
            {/* Header */}
            <div className="p-6 bg-gradient-to-r from-blue-50 to-indigo-50 border-b border-gray-200 text-center">
                <div className="inline-flex items-center justify-center w-20 h-20 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 text-white text-3xl font-black mb-3 shadow-lg">
                    {bio.name.charAt(0)}
                </div>
                <h2 className="text-2xl font-bold text-gray-900">{bio.name}</h2>
                <p className="text-gray-600 font-medium mt-1">{bio.team || 'Free Agent'} • {bio.position}</p>
                <div className={`inline-block mt-2 px-3 py-1 rounded-full text-xs font-bold ${bio.status === 'Active'
                        ? 'bg-green-100 text-green-700 border border-green-300'
                        : 'bg-gray-100 text-gray-600 border border-gray-300'
                    }`}>
                    {bio.status || 'Active'}
                </div>
            </div>

            {/* Stats Grid */}
            <div className="p-6 grid grid-cols-2 gap-4">
                {bio.age && (
                    <div className="text-center p-3 bg-gray-50 rounded-lg border border-gray-200">
                        <div className="text-2xl font-bold text-blue-600">{bio.age}</div>
                        <div className="text-xs text-gray-600 uppercase tracking-wide mt-1">Age</div>
                    </div>
                )}

                {bio.years_exp && (
                    <div className="text-center p-3 bg-gray-50 rounded-lg border border-gray-200">
                        <div className="text-2xl font-bold text-blue-600">{bio.years_exp}</div>
                        <div className="text-xs text-gray-600 uppercase tracking-wide mt-1">Years Exp</div>
                    </div>
                )}

                {bio.height && (
                    <div className="text-center p-3 bg-gray-50 rounded-lg border border-gray-200">
                        <div className="text-2xl font-bold text-blue-600">{formatHeight(bio.height)}</div>
                        <div className="text-xs text-gray-600 uppercase tracking-wide mt-1">Height</div>
                    </div>
                )}

                {bio.weight && (
                    <div className="text-center p-3 bg-gray-50 rounded-lg border border-gray-200">
                        <div className="text-2xl font-bold text-blue-600">{bio.weight}</div>
                        <div className="text-xs text-gray-600 uppercase tracking-wide mt-1">Weight (lbs)</div>
                    </div>
                )}
            </div>

            {/* Additional Info */}
            <div className="px-6 pb-6 space-y-2">
                {bio.college && (
                    <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg border border-gray-200">
                        <span className="text-sm text-gray-600">College</span>
                        <span className="font-semibold text-gray-900">{bio.college}</span>
                    </div>
                )}

                {bio.rookie_season && (
                    <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg border border-gray-200">
                        <span className="text-sm text-gray-600">Rookie Season</span>
                        <span className="font-semibold text-gray-900">{bio.rookie_season}</span>
                    </div>
                )}
            </div>
        </div>
    );
}
