import { Slider } from '@/components/ui/slider'
import { DEFAULT_THRESHOLD, MIN_THRESHOLD } from '@/lib/constants'

interface Props {
  value: number
  onChange: (value: number) => void
}

export function ThresholdSlider({ value, onChange }: Props) {
  return (
    <div className="space-y-3">
      <div className="flex items-baseline justify-between gap-4">
        <label htmlFor="threshold" className="text-sm font-medium">
          Similarity threshold
        </label>
        <span className="font-mono text-sm tabular-nums">{value.toFixed(2)}</span>
      </div>
      <Slider
        id="threshold"
        min={MIN_THRESHOLD}
        max={1}
        step={0.01}
        value={[value]}
        onValueChange={([v]) => onChange(v)}
      />
      <p className="text-xs text-muted-foreground">
        Higher means stricter: fewer false matches, but more missed duplicates. Default{' '}
        {DEFAULT_THRESHOLD}.
      </p>
    </div>
  )
}
