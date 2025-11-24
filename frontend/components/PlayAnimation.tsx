'use client';

import { useEffect, useRef, useState } from 'react';

interface PlayData {
    type: string;
    yards: number;
    touchdown: boolean;
    description: string;
    yardline_100?: number;
    season?: number;
    week?: number;
    opponent?: string;
    passer?: string;
    receiver?: string;
}

interface PlayAnimationProps {
    playData: PlayData;
}

export default function PlayAnimation({ playData }: PlayAnimationProps) {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const [isPlaying, setIsPlaying] = useState(false);
    const [progress, setProgress] = useState(0);

    useEffect(() => {
        if (!isPlaying) return;

        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        // Animation parameters
        const duration = 3000; // 3 seconds
        const startTime = Date.now();

        // Field dimensions (scaled to canvas)
        const fieldWidth = canvas.width;
        const fieldHeight = canvas.height;
        const yardWidth = fieldWidth / 120; // 120 yards total (100 + 2 endzones)

        // Calculate positions
        const startYardline = playData.yardline_100 || 75; // Default to own 25
        const startX = (110 - startYardline) * yardWidth;
        const endX = startX + (playData.yards * yardWidth);

        // Parse direction from description
        const desc = playData.description?.toLowerCase() || '';
        let startY = fieldHeight / 2;
        let endY = fieldHeight / 2;

        if (desc.includes('left')) {
            endY = fieldHeight * 0.75;
        } else if (desc.includes('right')) {
            endY = fieldHeight * 0.25;
        } else if (desc.includes('middle') || desc.includes('center')) {
            endY = fieldHeight / 2;
        }

        const animate = () => {
            const elapsed = Date.now() - startTime;
            const t = Math.min(elapsed / duration, 1);
            setProgress(t);

            // Clear canvas
            ctx.clearRect(0, 0, fieldWidth, fieldHeight);

            // Draw field
            drawField(ctx, fieldWidth, fieldHeight, yardWidth);

            // Draw player path
            drawPlayerPath(ctx, startX, startY, endX, endY, t);

            // Draw ball if passing play
            if (playData.type === 'receiving' || playData.type === 'passing') {
                drawBall(ctx, startX, startY, endX, endY, t);
            }

            if (t < 1) {
                requestAnimationFrame(animate);
            } else {
                setIsPlaying(false);
            }
        };

        animate();
    }, [isPlaying, playData]);

    const drawField = (
        ctx: CanvasRenderingContext2D,
        width: number,
        height: number,
        yardWidth: number
    ) => {
        // Field background
        ctx.fillStyle = '#2d5016';
        ctx.fillRect(0, 0, width, height);

        // Endzones
        ctx.fillStyle = 'rgba(0, 100, 200, 0.3)';
        ctx.fillRect(0, 0, 10 * yardWidth, height);
        ctx.fillRect(110 * yardWidth, 0, 10 * yardWidth, height);

        // Yard lines
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.5)';
        ctx.lineWidth = 1;

        for (let i = 10; i <= 110; i += 10) {
            const x = i * yardWidth;
            ctx.beginPath();
            ctx.moveTo(x, 0);
            ctx.lineTo(x, height);
            ctx.stroke();

            // Yard numbers
            if (i >= 20 && i <= 100) {
                const yardNum = i <= 50 ? i - 10 : 110 - i;
                ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
                ctx.font = '14px Arial';
                ctx.textAlign = 'center';
                ctx.fillText(yardNum.toString(), x, height / 2);
            }
        }

        // Hash marks
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
        for (let i = 10; i < 110; i++) {
            const x = i * yardWidth;
            ctx.beginPath();
            ctx.moveTo(x, height * 0.3);
            ctx.lineTo(x, height * 0.32);
            ctx.stroke();
            ctx.beginPath();
            ctx.moveTo(x, height * 0.68);
            ctx.lineTo(x, height * 0.7);
            ctx.stroke();
        }
    };

    const drawPlayerPath = (
        ctx: CanvasRenderingContext2D,
        startX: number,
        startY: number,
        endX: number,
        endY: number,
        t: number
    ) => {
        // Draw route line
        ctx.strokeStyle = 'rgba(255, 215, 0, 0.5)';
        ctx.lineWidth = 3;
        ctx.setLineDash([5, 5]);
        ctx.beginPath();
        ctx.moveTo(startX, startY);
        ctx.lineTo(endX, endY);
        ctx.stroke();
        ctx.setLineDash([]);

        // Draw player (animated)
        const currentX = startX + (endX - startX) * easeInOutQuad(t);
        const currentY = startY + (endY - startY) * easeInOutQuad(t);

        // Player circle
        ctx.fillStyle = '#FFD700';
        ctx.beginPath();
        ctx.arc(currentX, currentY, 8, 0, Math.PI * 2);
        ctx.fill();

        // Player number/label
        ctx.fillStyle = '#000';
        ctx.font = 'bold 10px Arial';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText('●', currentX, currentY);

        // Trail effect
        if (t > 0.1) {
            for (let i = 0; i < 5; i++) {
                const trailT = Math.max(0, t - (i * 0.05));
                const trailX = startX + (endX - startX) * easeInOutQuad(trailT);
                const trailY = startY + (endY - startY) * easeInOutQuad(trailT);
                const alpha = 0.3 - (i * 0.05);

                ctx.fillStyle = `rgba(255, 215, 0, ${alpha})`;
                ctx.beginPath();
                ctx.arc(trailX, trailY, 6, 0, Math.PI * 2);
                ctx.fill();
            }
        }

        // Touchdown celebration
        if (playData.touchdown && t > 0.95) {
            ctx.fillStyle = 'rgba(255, 215, 0, 0.8)';
            ctx.font = 'bold 24px Arial';
            ctx.textAlign = 'center';
            ctx.fillText('🏈 TOUCHDOWN!', currentX, currentY - 30);
        }
    };

    const drawBall = (
        ctx: CanvasRenderingContext2D,
        startX: number,
        startY: number,
        endX: number,
        endY: number,
        t: number
    ) => {
        // Ball travels in an arc for passing plays
        const ballT = Math.min(t * 1.5, 1); // Ball travels faster
        const ballX = startX + (endX - startX) * ballT;

        // Parabolic arc
        const arcHeight = 50;
        const ballY = startY + (endY - startY) * ballT - (arcHeight * Math.sin(ballT * Math.PI));

        // Draw ball
        ctx.fillStyle = '#8B4513';
        ctx.beginPath();
        ctx.ellipse(ballX, ballY, 5, 7, Math.PI / 4, 0, Math.PI * 2);
        ctx.fill();

        // Ball laces
        ctx.strokeStyle = '#FFF';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(ballX - 2, ballY);
        ctx.lineTo(ballX + 2, ballY);
        ctx.stroke();
    };

    const easeInOutQuad = (t: number): number => {
        return t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
    };

    return (
        <div className="w-full bg-gray-900 rounded-lg p-4 shadow-xl">
            <div className="mb-4 flex items-center justify-between">
                <div className="text-white">
                    <h3 className="text-lg font-bold">
                        {playData.type === 'receiving' ? '📡' : playData.type === 'rushing' ? '🏃' : '🎯'}
                        {' '}{playData.yards} Yard {playData.type.charAt(0).toUpperCase() + playData.type.slice(1)}
                        {playData.touchdown && ' 🏈'}
                    </h3>
                    {playData.passer && (
                        <p className="text-sm text-gray-400">From: {playData.passer}</p>
                    )}
                    {playData.receiver && (
                        <p className="text-sm text-gray-400">To: {playData.receiver}</p>
                    )}
                </div>
                <button
                    onClick={() => {
                        setProgress(0);
                        setIsPlaying(true);
                    }}
                    disabled={isPlaying}
                    className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 text-white rounded-lg font-semibold transition-colors"
                >
                    {isPlaying ? '▶️ Playing...' : '▶️ Replay'}
                </button>
            </div>

            <canvas
                ref={canvasRef}
                width={800}
                height={300}
                className="w-full border-2 border-gray-700 rounded-lg bg-gray-800"
            />

            {/* Progress bar */}
            <div className="mt-3 w-full bg-gray-700 rounded-full h-2">
                <div
                    className="bg-green-500 h-2 rounded-full transition-all duration-100"
                    style={{ width: `${progress * 100}%` }}
                />
            </div>

            {/* Play description */}
            <div className="mt-3 text-gray-300 text-sm bg-gray-800 p-3 rounded-lg">
                <p className="italic">{playData.description}</p>
            </div>
        </div>
    );
}
