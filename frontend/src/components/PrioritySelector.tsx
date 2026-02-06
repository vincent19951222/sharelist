import React from 'react';
import { Priority } from './PriorityBadge';

interface PrioritySelectorProps {
  value: Priority;
  onChange: (priority: Priority) => void;
  disabled?: boolean;
}

const priorityOptions: { value: Priority; label: string; icon: string; activeClass: string }[] = [
  { value: "high", label: "High", icon: "🔴", activeClass: "border-red-500 bg-red-50 text-red-700" },
  { value: "medium", label: "Medium", icon: "🟡", activeClass: "border-yellow-500 bg-yellow-50 text-yellow-700" },
  { value: "low", label: "Low", icon: "🟢", activeClass: "border-green-500 bg-green-50 text-green-700" }
];

export default function PrioritySelector({ value, onChange, disabled = false }: PrioritySelectorProps) {
  return (
    <div className="flex items-center gap-2">
      <label className="text-sm font-medium text-muted-foreground">Priority:</label>
      <div className="flex gap-2">
        {priorityOptions.map((option) => (
          <button
            key={option.value}
            type="button"
            onClick={() => onChange(option.value)}
            disabled={disabled}
            className={`
              px-3 py-1.5 rounded-full text-sm font-medium transition-all
              border flex items-center gap-1.5 shadow-sm
              ${disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer hover:scale-105 active:scale-95"}
              ${
                value === option.value
                  ? `${option.activeClass} ring-1 ring-offset-1 ring-transparent`
                  : "border-gray-200 bg-white text-gray-600 hover:bg-gray-50"
              }
            `}
            title={option.label}
          >
            <span className="text-xs">{option.icon}</span>
            <span>{option.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
