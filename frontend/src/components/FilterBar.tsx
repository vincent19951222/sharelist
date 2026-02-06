import React from 'react';
import { Priority } from '@/types';

interface FilterBarProps {
  currentFilter: 'all' | Priority;
  onFilterChange: (filter: 'all' | Priority) => void;
}

const filters: { value: 'all' | Priority; label: string; count: number }[] = [
  { value: 'all', label: 'All', count: 0 },
  { value: 'high', label: 'High', count: 0 },
  { value: 'medium', label: 'Medium', count: 0 },
  { value: 'low', label: 'Low', count: 0 },
];

export default function FilterBar({ currentFilter, onFilterChange }: FilterBarProps) {
  return (
    <div className="flex items-center gap-2 px-4 py-2 border-b bg-muted/30">
      <span className="text-sm font-medium text-muted-foreground mr-2">Filter:</span>
      <div className="flex gap-1">
        {filters.map((filter) => (
          <button
            key={filter.value}
            onClick={() => onFilterChange(filter.value)}
            className={`
              px-3 py-1 rounded-md text-sm font-medium transition-all
              ${currentFilter === filter.value
                ? 'bg-primary text-primary-foreground shadow-sm'
                : 'bg-background text-muted-foreground hover:bg-muted'
              }
            `}
          >
            {filter.label}
          </button>
        ))}
      </div>
    </div>
  );
}
