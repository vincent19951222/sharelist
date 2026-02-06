import React from 'react';

export type Priority = "high" | "medium" | "low";

interface PriorityBadgeProps {
  priority?: Priority;
  size?: "sm" | "md" | "lg";
}

const priorityStyles = {
  high: {
    bg: "bg-red-100",
    text: "text-red-800",
    border: "border-red-200",
    label: "High"
  },
  medium: {
    bg: "bg-yellow-100",
    text: "text-yellow-800",
    border: "border-yellow-200",
    label: "Medium"
  },
  low: {
    bg: "bg-green-100",
    text: "text-green-800",
    border: "border-green-200",
    label: "Low"
  }
};

const sizeStyles = {
  sm: "px-2 py-0.5 text-xs",
  md: "px-2.5 py-1 text-sm",
  lg: "px-3 py-1.5 text-base"
};

export default function PriorityBadge({ priority, size = "sm" }: PriorityBadgeProps) {
  // Default to medium if priority is not set
  const safePriority: Priority = priority || "medium";
  const style = priorityStyles[safePriority];
  const sizeStyle = sizeStyles[size];

  return (
    <span
      className={`
        inline-flex items-center font-medium rounded-full border
        ${style.bg} ${style.text} ${style.border} ${sizeStyle}
      `}
      title={`Priority: ${style.label}`}
    >
      {size !== "sm" && (
        <span className="mr-1">
          {safePriority === "high" && "🔴"}
          {safePriority === "medium" && "🟡"}
          {safePriority === "low" && "🟢"}
        </span>
      )}
      {style.label}
    </span>
  );
}
