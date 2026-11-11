type Props = {
  total: number
  current: number
  isAnswered: (index: number) => boolean
  isMarked: (index: number) => boolean
  onSelect: (index: number) => void
  labels: { answered: string; notAnswered: string; marked: string; question: string; palette: string }
}

export function QuestionPalette({ total, current, isAnswered, isMarked, onSelect, labels }: Props) {
  return <div className="tx-palette-grid" role="group" aria-label={labels.palette}>
    {Array.from({ length: total }, (_, index) => {
      const answered = isAnswered(index)
      const marked = isMarked(index)
      const state = [answered ? labels.answered : labels.notAnswered, marked ? labels.marked : ''].filter(Boolean).join(', ')
      return <button
        key={index}
        type="button"
        className={`tx-dot ${answered ? 'is-answered' : ''} ${marked ? 'is-marked' : ''} ${index === current ? 'is-current' : ''}`}
        aria-label={`${labels.question} ${index + 1}: ${state}`}
        aria-current={index === current ? 'step' : undefined}
        onClick={() => onSelect(index)}
      >{index + 1}</button>
    })}
  </div>
}
