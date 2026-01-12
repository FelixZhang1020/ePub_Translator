import { useEffect, useState } from 'react'
import { Outlet, useParams, useNavigate, useLocation } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, Loader2, Settings } from 'lucide-react'
import { api } from '../../services/api/client'
import { useTranslation, useAppStore } from '../../stores/appStore'

// Map database step name to URL path
const getRoutePathFromStep = (step: string): string => {
  const stepToRoute: Record<string, string> = {
    'analysis': 'analysis',
    'translation': 'translate',
    'proofreading': 'proofread',
    'export': 'export'
  }
  return stepToRoute[step] || 'analysis'
}

export function ProjectLayout() {
  const { projectId } = useParams<{ projectId: string }>()
  const navigate = useNavigate()
  const location = useLocation()
  const { t } = useTranslation()
  const setTranslationProgress = useAppStore((state) => state.setTranslationProgress)
  const setWorkflowStatus = useAppStore((state) => state.setWorkflowStatus)
  const setIsAnalyzing = useAppStore((state) => state.setIsAnalyzing)

  // Map URL path to database step name
  const getCurrentStepFromPath = (): string => {
    const path = location.pathname
    if (path.includes('/analysis')) return 'analysis'
    if (path.includes('/translate')) return 'translation'
    if (path.includes('/proofread')) return 'proofreading'
    if (path.includes('/export')) return 'export'
    return 'analysis'
  }

  const [currentStep, setCurrentStep] = useState(getCurrentStepFromPath())

  // Fetch project info
  const { data: project, isLoading: projectLoading } = useQuery({
    queryKey: ['project', projectId],
    queryFn: () => api.getProject(projectId!),
    enabled: !!projectId,
  })

  // Fetch workflow status
  const { data: workflowStatus, isLoading: statusLoading, refetch: refetchWorkflow } = useQuery({
    queryKey: ['workflowStatus', projectId],
    queryFn: () => api.getWorkflowStatus(projectId!),
    enabled: !!projectId,
    refetchInterval: 5000, // Refresh every 5 seconds
  })

  // Check if translation is in progress
  const translationProgress = workflowStatus?.translation_progress
  const isTranslating = translationProgress?.status === 'processing' || translationProgress?.status === 'pending'

  // Refetch more frequently when translation is in progress
  const { data: activeWorkflowStatus } = useQuery({
    queryKey: ['workflowStatus-active', projectId],
    queryFn: () => api.getWorkflowStatus(projectId!),
    enabled: !!projectId && isTranslating,
    refetchInterval: isTranslating ? 2000 : false, // Refresh every 2 seconds while translating
  })

  // Use active status when available and translating
  const effectiveWorkflowStatus = isTranslating && activeWorkflowStatus ? activeWorkflowStatus : workflowStatus
  const effectiveTranslationProgress = effectiveWorkflowStatus?.translation_progress
  const effectiveIsTranslating = effectiveTranslationProgress?.status === 'processing' || effectiveTranslationProgress?.status === 'pending'

  // Update current step when URL changes
  useEffect(() => {
    setCurrentStep(getCurrentStepFromPath())
  }, [location.pathname])

  // Validate stage access and redirect if necessary
  useEffect(() => {
    if (!workflowStatus || !projectId) return

    const currentPath = getCurrentStepFromPath()

    // Define stage access rules
    const canAccessStage = (stage: string): boolean => {
      if (stage === 'analysis') return true
      if (stage === 'translation') return workflowStatus.analysis_completed ?? false
      if (stage === 'proofreading') return workflowStatus.translation_completed ?? false
      if (stage === 'export') return workflowStatus.proofreading_completed ?? false
      return false
    }

    // Redirect if trying to access a locked stage
    if (!canAccessStage(currentPath)) {
      // Find the furthest accessible stage
      const stages = ['analysis', 'translation', 'proofreading', 'export']
      let redirectStage = 'analysis'

      for (const stage of stages) {
        if (canAccessStage(stage)) {
          redirectStage = stage
        } else {
          break
        }
      }

      // Only redirect if we're not already on the correct stage
      if (currentPath !== redirectStage) {
        const routePath = getRoutePathFromStep(redirectStage)
        navigate(`/project/${projectId}/${routePath}`, { replace: true })
      }
    }
  }, [location.pathname, workflowStatus, projectId, navigate])

  // Sync translation progress to global store for header display
  useEffect(() => {
    if (effectiveIsTranslating && effectiveTranslationProgress && project && projectId) {
      setTranslationProgress({
        projectId,
        projectName: project.name,
        status: effectiveTranslationProgress.status || 'processing',
        progress: effectiveTranslationProgress.progress,
        completed_paragraphs: effectiveTranslationProgress.completed_paragraphs,
        total_paragraphs: effectiveTranslationProgress.total_paragraphs,
      })
    } else {
      setTranslationProgress(null)
    }
  }, [effectiveIsTranslating, effectiveTranslationProgress, project, projectId, setTranslationProgress])

  // Check if analysis is in progress
  const analysisProgress = effectiveWorkflowStatus?.analysis_progress
  const isAnalyzing = !!(analysisProgress?.has_task && analysisProgress?.status === 'processing')

  // Sync workflow status to global store for header display
  useEffect(() => {
    if (projectId && effectiveWorkflowStatus) {
      const analysisProgress = effectiveWorkflowStatus.analysis_progress
      const translationProgress = effectiveWorkflowStatus.translation_progress
      const proofreadingProgress = effectiveWorkflowStatus.proofreading_progress

      // Sync analysis running state to global store
      setIsAnalyzing(isAnalyzing)

      setWorkflowStatus({
        projectId,
        currentStep: currentStep as 'analysis' | 'translation' | 'proofreading' | 'export',
        analysisCompleted: effectiveWorkflowStatus.analysis_completed ?? false,
        translationCompleted: effectiveWorkflowStatus.translation_completed ?? false,
        proofreadingCompleted: effectiveWorkflowStatus.proofreading_completed ?? false,
        analysisProgress: analysisProgress ? {
          exists: analysisProgress.exists ?? false,
          confirmed: analysisProgress.confirmed ?? false,
        } : undefined,
        translationProgress: translationProgress ? {
          hasTask: translationProgress.has_task ?? false,
          status: translationProgress.status,
          progress: translationProgress.progress ?? 0,
          completedParagraphs: translationProgress.completed_paragraphs ?? 0,
          totalParagraphs: translationProgress.total_paragraphs ?? 0,
        } : undefined,
        proofreadingProgress: proofreadingProgress ? {
          hasSession: proofreadingProgress.has_session ?? false,
          status: proofreadingProgress.status,
          roundNumber: proofreadingProgress.round_number,
          progress: proofreadingProgress.progress ?? 0,
          pendingSuggestions: proofreadingProgress.pending_suggestions ?? 0,
        } : undefined,
      })
    }
  }, [projectId, currentStep, effectiveWorkflowStatus, isAnalyzing, setWorkflowStatus, setIsAnalyzing])

  // Clear progress and workflow status when leaving the project
  useEffect(() => {
    return () => {
      setTranslationProgress(null)
      setWorkflowStatus(null)
    }
  }, [setTranslationProgress, setWorkflowStatus])

  if (projectLoading || statusLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    )
  }

  if (!project) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
          {t('common.error')}
        </h2>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Project not found
        </p>
        <button
          onClick={() => navigate('/')}
          className="mt-4 text-blue-600 hover:text-blue-700"
        >
          {t('nav.home')}
        </button>
      </div>
    )
  }

  // Check if on translate page for wider layout
  const isTranslatePage = location.pathname.includes('/translate')
  // Check if on export page for full-height layout
  const isExportPage = location.pathname.includes('/export')

  return (
    <div className={isTranslatePage || isExportPage ? 'w-full h-full flex flex-col' : 'max-w-6xl mx-auto'}>
      {/* Header - unified format for all pages */}
      <div className={isTranslatePage || isExportPage ? 'mb-2 flex-shrink-0' : 'mb-6'}>
        {/* Breadcrumb - consistent across all pages */}
        <button
          onClick={() => navigate('/')}
          className="flex items-center gap-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 mb-2"
        >
          <ArrowLeft className="w-4 h-4" />
          {t('nav.home')}
        </button>

        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {project.name}
              </h1>
              {project.author && (
                <p className="text-gray-600 dark:text-gray-400 mt-1">
                  {t('common.by')} {project.author}
                </p>
              )}
            </div>
            <button
              onClick={() => navigate(`/project/${projectId}/parameters`)}
              className="ml-3 p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-700 rounded transition-colors"
              title={t('parameterReview.title')}
            >
              <Settings className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Page Content */}
      <div className={`${isTranslatePage || isExportPage
          ? 'flex-1 min-h-0 overflow-hidden'
          : 'mt-8'
        }`}>
        <Outlet context={{ project, workflowStatus: effectiveWorkflowStatus, refetchWorkflow }} />
      </div>
    </div>
  )
}
