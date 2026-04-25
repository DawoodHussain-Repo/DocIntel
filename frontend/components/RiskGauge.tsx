"use client";

import { useEffect, useState } from "react";
import { RadialBar, RadialBarChart } from "recharts";

import { cn } from "@/lib/utils";

function gaugeColor(score: number) {
  if (score >= 70) return "#EF4444";
  if (score >= 40) return "#F59E0B";
  return "#10B981";
}

export function RiskGauge(props: {
  score: number;
  className?: string;
  textClassName?: string;
}) {
  const { score, className, textClassName } = props;
  const [animated, setAnimated] = useState(0);

  useEffect(() => {
    const target = Math.max(0, Math.min(100, score));
    const start = performance.now();
    const duration = 1000;
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      setAnimated(Math.round(eased * target));
      if (t < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }, [score]);

  const data = [{ name: "risk", value: animated, fill: gaugeColor(score) }];

  return (
    <div className={cn("relative h-28 w-28", className)}>
      <RadialBarChart
        width={112}
        height={112}
        innerRadius="72%"
        outerRadius="100%"
        data={data}
        startAngle={90}
        endAngle={-270}
      >
        <RadialBar dataKey="value" cornerRadius={999} background={{ fill: "#E5E7EB" }} />
      </RadialBarChart>
      <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
        <p className={cn("font-serif text-[1.75rem] leading-none text-text", textClassName)}>
          {animated}
        </p>
      </div>
    </div>
  );
}
