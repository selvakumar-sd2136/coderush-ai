import { useEffect, useRef } from "react";

// Running game: scenery scrolls forever, the runner moves towards the flag as `progress` (0..1) grows.
export default function Game({ progress = 0 }) {
  const ref = useRef(null);
  const prog = useRef(progress);
  prog.current = progress;

  useEffect(() => {
    const c = ref.current, g = c.getContext("2d");
    let t = 0, x = 30, raf;
    const loop = () => {
      t++;
      const W = c.width, H = c.height, gy = H - 30;
      g.fillStyle = "#1b2a5a"; g.fillRect(0, 0, W, H);
      g.fillStyle = "#2a3f85";
      for (let i = 0; i < 8; i++) {
        const bx = ((((i * 90 - t * 0.6) % (W + 90)) + W + 90) % (W + 90)) - 90, bh = 40 + ((i * 37) % 55);
        g.fillRect(bx, gy - bh, 50, bh);
      }
      g.fillStyle = "#2e8b3d"; g.fillRect(0, gy, W, 30);
      g.fillStyle = "#ffd23f";
      for (let i = 0; i < 4; i++) { g.beginPath(); g.arc(W * 0.35 + i * 50, gy - 45, 7, 0, Math.PI * 2); g.fill(); }
      g.fillStyle = "#fff"; g.fillRect(W - 30, gy - 55, 4, 55);
      g.fillStyle = "#111"; g.fillRect(W - 26, gy - 55, 22, 14);
      x += (30 + (W - 90) * prog.current - x) * 0.05;
      const bob = Math.abs(Math.sin(t * 0.25)) * 6;
      g.fillStyle = "#e4572e"; g.fillRect(x, gy - 30 - bob, 16, 24);
      g.fillStyle = "#f3c9a0"; g.fillRect(x + 2, gy - 42 - bob, 12, 12);
      g.fillStyle = "#222"; g.fillRect(x + (t % 20 < 10 ? 1 : 9), gy - 6 - bob, 6, 6);
      raf = requestAnimationFrame(loop);
    };
    loop();
    return () => cancelAnimationFrame(raf);
  }, []);

  return <canvas ref={ref} width={440} height={150} className="game" />;
}
