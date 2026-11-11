import { useEffect, useRef, useState } from 'react'

/**
 * Counts down from a server-provided number of seconds.
 * Uses the monotonic clock (performance.now) so changing the device clock cannot extend a test.
 * `onExpire` fires exactly once.
 */
export function useCountdown(initialSeconds: number | null, onExpire: () => void) {
  const deadline = useRef<number | null>(null)
  const expired = useRef(false)
  const expireRef = useRef(onExpire)
  expireRef.current = onExpire
  const [left, setLeft] = useState<number | null>(initialSeconds)

  useEffect(() => {
    if (initialSeconds === null) return
    deadline.current = performance.now() + initialSeconds * 1000
    expired.current = false
    const tick = () => {
      const remaining = Math.max(0, Math.ceil(((deadline.current ?? 0) - performance.now()) / 1000))
      setLeft(remaining)
      if (remaining === 0 && !expired.current) {
        expired.current = true
        expireRef.current()
      }
    }
    tick()
    const id = window.setInterval(tick, 500)
    return () => window.clearInterval(id)
  }, [initialSeconds])

  return left
}
