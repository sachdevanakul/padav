import { useEffect, useState } from 'react'

type SwitchProps = {
  checked?: boolean
  onChange?: (checked: boolean) => void
  disabled?: boolean
  className?: string
}

export function Switch({ checked = false, onChange, disabled = false, className }: SwitchProps) {
  const [isChecked, setChecked] = useState<boolean>(checked)

  useEffect(() => {
    if (onChange) onChange(isChecked)
  }, [isChecked])

  const handleClick = () => {
    if (!disabled) {
      setChecked(!isChecked)
    }
  }

  return <button
    type="button"
    role="switch"
    aria-checked={isChecked}
    disabled={disabled}
    className={`pdv-switch ${isChecked ? 'is-checked' : ''} ${className ?? ''}`}
    onClick={handleClick}
  ><span aria-hidden="true" /></button>
}