import { useState } from 'react'

type Tab = {
  value: string
  label: string
  disabled?: boolean
}

type TabsProps = {
  anableLeftIcon?: boolean
  values: Tab[]
  defaultValue?: string
  onValueChange?: (value: string) => void
  className?: string
}

export function Tabs({ values, defaultValue, onValueChange, className = '' }: TabsProps) {
  const [value, setValue] = useState<string>(defaultValue || values[0]?.value || '')

  return (
    <div className={`pdv-tabs pdv-flex pdv-items-center pdv-border pdv-border-gray-200 pdv-rounded-md pdv-overflow-hidden ${className}`} role="tablist">
      {values.map((item) => (
        <button
          key={item.value}
          type="button"
          role="tab"
          aria-selected={value === item.value}
          className={`
            pdv-tab pdv-inline-flex pdv-items-center pdv-justify-center
            pdv-text-sm pdv-font-medium pdv-text-gray-500 pdv-transition-colors
            ${value === item.value ? 'pdv-text-primary' : 'pdv-text-gray-500'}
            ${item.disabled ? 'pdv-pointer-events-none pdv-opacity-50' : ''}
          `}
          onClick={() => {
            if (!item.disabled) {
              setValue(item.value)
              onValueChange?.(item.value)
            }
          }}
          disabled={item.disabled}
        >
          {item.label}
        </button>
      ))}
    </div>
  )
}