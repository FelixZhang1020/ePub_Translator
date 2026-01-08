import { Check, BookOpen, Languages, FileCheck, Download, Loader2 } from 'lucide-react'
import { useTranslation } from '../../stores/appStore'

interface Step {
  id: string
  label: string
  icon: React.ReactNode
}

interface TranslationProgressInfo {
  hasTask: boolean
  status?: string
  progress: number
  completedParagraphs: number
  totalParagraphs: number
}

interface StepIndicatorProps {
  currentStep: string
  analysisCompleted: boolean
  translationCompleted: boolean
  proofreadingCompleted: boolean
  translationProgress?: TranslationProgressInfo
  onStepClick?: (step: string) => void
}

export function StepIndicator({
  currentStep,
  analysisCompleted,
  translationCompleted,
  proofreadingCompleted,
  translationProgress,
  onStepClick,
}: StepIndicatorProps) {
  const { t } = useTranslation()

  const steps: Step[] = [
    { id: 'analysis', label: t('workflow.analysis'), icon: <BookOpen className="w-5 h-5" /> },
    { id: 'translation', label: t('workflow.translation'), icon: <Languages className="w-5 h-5" /> },
    { id: 'proofreading', label: t('workflow.proofreading'), icon: <FileCheck className="w-5 h-5" /> },
    { id: 'export', label: t('workflow.export'), icon: <Download className="w-5 h-5" /> },
  ]

  // Status types:
  // - completed: Step is fully done (green checkmark)
  // - in_progress: Step is actively being processed (animated)
  // - current: On this step but not processing
  // - upcoming: Not accessible yet
  const getStepStatus = (stepId: string): 'completed' | 'in_progress' | 'current' | 'upcoming' => {
    // Analysis: completed when confirmed, regardless of current page
    if (stepId === 'analysis') {
      if (analysisCompleted) return 'completed'
      if (currentStep === 'analysis') return 'current'
      return 'upcoming'
    }

    // Translation: completed when done, in_progress when has partial content
    if (stepId === 'translation') {
      if (translationCompleted) return 'completed'
      // Check if translation is in progress (has partial content or actively processing)
      if (translationProgress?.hasTask) {
        const isProcessing = translationProgress.status === 'processing' || translationProgress.status === 'pending'
        const hasPartialContent = translationProgress.completedParagraphs > 0
        if (isProcessing || hasPartialContent) return 'in_progress'
      }
      if (currentStep === 'translation') return 'current'
      return 'upcoming'
    }

    // Proofreading and Export: keep simple for now
    if (stepId === 'proofreading') {
      if (proofreadingCompleted) return 'completed'
      if (currentStep === 'proofreading') return 'current'
      return 'upcoming'
    }

    if (stepId === 'export') {
      if (currentStep === 'export') return 'current'
      return 'upcoming'
    }

    return 'upcoming'
  }

  const canNavigate = (stepId: string): boolean => {
    const stepOrder = ['analysis', 'translation', 'proofreading', 'export']
    const currentIndex = stepOrder.indexOf(currentStep)
    const targetIndex = stepOrder.indexOf(stepId)

    // Can always go back
    if (targetIndex <= currentIndex) return true

    // Can move forward only if prerequisites are met
    if (stepId === 'translation') return analysisCompleted
    if (stepId === 'proofreading') return translationCompleted
    if (stepId === 'export') return true // Can preview export anytime after proofreading started

    return false
  }

  return (
    <nav aria-label={t('common.progress')} className="mb-8">
      <ol className="flex items-center justify-center">
        {steps.map((step, index) => {
          const status = getStepStatus(step.id)
          const canClick = canNavigate(step.id)

          return (
            <li key={step.id} className="relative flex items-center">
              {/* Connector line */}
              {index > 0 && (
                <div
                  className={`absolute right-full w-16 h-0.5 -translate-y-1/2 top-1/2 ${
                    getStepStatus(steps[index - 1].id) === 'completed'
                      ? 'bg-blue-600 dark:bg-blue-500'
                      : getStepStatus(steps[index - 1].id) === 'in_progress'
                      ? 'bg-amber-400 dark:bg-amber-500'
                      : 'bg-gray-200 dark:bg-gray-700'
                  }`}
                />
              )}

              {/* Step button */}
              <button
                onClick={() => canClick && onStepClick?.(step.id)}
                disabled={!canClick}
                className={`
                  relative flex flex-col items-center group
                  ${canClick ? 'cursor-pointer' : 'cursor-not-allowed'}
                `}
              >
                {/* Circle */}
                <span
                  className={`
                    flex items-center justify-center w-12 h-12 rounded-full border-2 transition-all
                    ${
                      status === 'completed'
                        ? 'bg-blue-600 border-blue-600 text-white'
                        : status === 'in_progress'
                        ? 'border-amber-500 text-amber-600 bg-amber-50 dark:bg-amber-900/20 animate-pulse'
                        : status === 'current'
                        ? 'border-blue-600 text-blue-600 bg-blue-50 dark:bg-blue-900/20'
                        : 'border-gray-300 dark:border-gray-600 text-gray-400 dark:text-gray-500'
                    }
                    ${canClick && status !== 'completed' && status !== 'in_progress' ? 'group-hover:border-blue-500 group-hover:text-blue-500' : ''}
                  `}
                >
                  {status === 'completed' ? (
                    <Check className="w-6 h-6" />
                  ) : status === 'in_progress' ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    step.icon
                  )}
                </span>

                {/* Label */}
                <span
                  className={`
                    mt-2 text-sm font-medium whitespace-nowrap
                    ${
                      status === 'in_progress'
                        ? 'text-amber-600 dark:text-amber-400'
                        : status === 'current'
                        ? 'text-blue-600 dark:text-blue-400'
                        : status === 'completed'
                        ? 'text-gray-900 dark:text-gray-100'
                        : 'text-gray-400 dark:text-gray-500'
                    }
                  `}
                >
                  {step.label}
                </span>
              </button>

              {/* Spacer for connector */}
              {index < steps.length - 1 && <div className="w-16" />}
            </li>
          )
        })}
      </ol>
    </nav>
  )
}
