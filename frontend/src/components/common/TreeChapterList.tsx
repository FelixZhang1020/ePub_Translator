import { useState, useMemo, useEffect } from 'react'
import { ChevronRight, ChevronDown, FileText, Folder, FolderOpen } from 'lucide-react'
import { TocItem } from '../../services/api/client'
import { useTranslation } from '../../stores/appStore'

interface FontClasses {
  base: string
  xs: string
  sm: string
  label: string
  paragraph: string
}

interface TreeChapterListProps {
  toc: TocItem[]
  selectedChapterId: string | null
  onSelectChapter: (chapterId: string) => void
  fontClasses?: FontClasses
  expandAll?: boolean
  compact?: boolean
  minimal?: boolean
  showCheckboxes?: boolean
  selectedChapterIds?: Set<string>
  chapterStatsMap?: Map<string, { translated: number; total: number }>
}

interface TocNodeProps {
  item: TocItem
  level: number
  selectedChapterId: string | null
  onSelectChapter: (chapterId: string) => void
  defaultExpanded?: boolean
  expandAll?: boolean
  compact?: boolean
  minimal?: boolean
  fontClasses?: FontClasses
  showCheckboxes?: boolean
  selectedChapterIds?: Set<string>
  chapterStatsMap?: Map<string, { translated: number; total: number }>
}

function TocNode({
  item,
  level,
  selectedChapterId,
  onSelectChapter,
  defaultExpanded = true,
  expandAll = false,
  compact = false,
  minimal = false,
  fontClasses,
  showCheckboxes = false,
  selectedChapterIds,
  chapterStatsMap,
}: TocNodeProps) {
  const { t } = useTranslation()

  // Check if this node or any descendant contains the selected chapter
  const containsSelected = useMemo(() => {
    const checkSelected = (node: TocItem): boolean => {
      if (node.chapter_id === selectedChapterId) return true
      return node.children?.some(checkSelected) ?? false
    }
    return checkSelected(item)
  }, [item, selectedChapterId])

  // Auto-expand when contains selected chapter
  const [isExpanded, setIsExpanded] = useState(defaultExpanded || containsSelected)

  const hasChildren = item.children && item.children.length > 0
  const isClickable = item.chapter_id !== null
  const isDirectlySelected = item.chapter_id === selectedChapterId

  // For checkbox mode: collect all chapter IDs under this node (recursively)
  const childChapterIds = useMemo(() => {
    if (!showCheckboxes) return []

    const collectChapterIds = (node: TocItem): string[] => {
      const ids: string[] = []
      // Add this node's chapter_id if it exists
      if (node.chapter_id) {
        ids.push(node.chapter_id)
      }
      // Recursively collect from all children
      if (node.children && node.children.length > 0) {
        node.children.forEach(child => {
          ids.push(...collectChapterIds(child))
        })
      }
      return ids
    }

    // For parent nodes, collect all descendant chapter IDs and deduplicate
    // (parent and child might share the same chapter_id)
    // For leaf nodes, just return the node's own ID
    let ids: string[] = []
    if (hasChildren) {
      ids = collectChapterIds(item)
    } else if (item.chapter_id) {
      ids = [item.chapter_id]
    }

    // Deduplicate using Set to prevent toggling the same ID multiple times
    return Array.from(new Set(ids))
  }, [item, showCheckboxes, hasChildren])

  // Check if all/some/none of children are selected
  const allChildrenSelected = useMemo(() => {
    if (!showCheckboxes || childChapterIds.length === 0) return false
    return childChapterIds.every(id => selectedChapterIds?.has(id))
  }, [showCheckboxes, childChapterIds, selectedChapterIds])

  const someChildrenSelected = useMemo(() => {
    if (!showCheckboxes || childChapterIds.length === 0) return false
    return childChapterIds.some(id => selectedChapterIds?.has(id)) && !allChildrenSelected
  }, [showCheckboxes, childChapterIds, selectedChapterIds, allChildrenSelected])

  // Check if any child is directly selected
  const hasSelectedChild = useMemo(() => {
    if (!hasChildren) return false
    return item.children.some(child => child.chapter_id === selectedChapterId)
  }, [item.children, selectedChapterId, hasChildren])

  // Only show as selected if directly selected AND no child is selected
  // This prevents parent sections from being highlighted when their children are selected
  const isSelected = isDirectlySelected && !hasSelectedChild

  // Auto-expand when this node contains the selected chapter
  useEffect(() => {
    if (containsSelected && !expandAll && !minimal) {
      setIsExpanded(true)
    }
  }, [containsSelected, expandAll, minimal])

  // Sync with expandAll prop
  useEffect(() => {
    if (expandAll) {
      setIsExpanded(true)
    } else if (!containsSelected) {
      // When collapsing all, only collapse nodes that don't contain selected chapter
      setIsExpanded(false)
    }
  }, [expandAll, containsSelected])

  const handleClick = () => {
    // In checkbox mode, clicking the row should only expand/collapse
    // Selection should only happen via checkbox clicks
    if (showCheckboxes) {
      if (hasChildren && !expandAll && !minimal) {
        setIsExpanded(!isExpanded)
      }
      // Don't call onSelectChapter in checkbox mode - only checkboxes should handle selection
      return
    }

    // Normal mode (no checkboxes) - clicking selects the chapter
    if (isClickable) {
      onSelectChapter(item.chapter_id!)
    } else if (hasChildren && !expandAll && !minimal) {
      setIsExpanded(!isExpanded)
    }
  }

  const handleToggle = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (!expandAll && !minimal) {
      setIsExpanded(!isExpanded)
    }
  }

  const textSizeClass = minimal ? 'text-[10px]' : (fontClasses?.paragraph || 'text-sm')
  const badgeSizeClass = fontClasses?.xs || 'text-xs'
  const isOpen = expandAll ? true : (minimal ? true : isExpanded)
  const paddingClasses = minimal ? 'py-[1px] px-1' : (compact ? 'py-1 px-1.5' : 'py-1.5 px-2')
  const leadingClass = minimal ? 'leading-tight' : ''
  const titleWeightClass = minimal ? (isSelected ? 'font-semibold' : 'font-normal') : (compact ? 'font-normal' : 'font-medium')
  const selectedSizeClass = minimal && isSelected ? 'text-xs' : ''
  const idleTextClass = compact ? 'text-gray-500 dark:text-gray-400' : 'text-gray-700 dark:text-gray-300'
  const groupTextClass = compact ? 'text-gray-500 dark:text-gray-400' : 'text-gray-600 dark:text-gray-400'
  // In checkbox mode, row is only clickable for expand/collapse (if has children) or not clickable at all
  // In normal mode, row is clickable if chapter has content
  const cursorClass = showCheckboxes
    ? (hasChildren ? 'cursor-pointer' : 'cursor-default')
    : (isClickable ? 'cursor-pointer' : 'cursor-default')
  const transitionClass = minimal ? '' : 'transition-colors'
  const selectedBgClass = minimal && isSelected ? 'bg-amber-100 dark:bg-amber-900/40' : ''

  return (
    <div>
      <div
        onClick={handleClick}
        className={`
          relative flex items-center gap-1 ${textSizeClass} ${leadingClass} ${cursorClass} ${transitionClass} ${paddingClasses} rounded
          ${!minimal && !showCheckboxes && isSelected ? 'bg-blue-100 text-blue-800 dark:bg-blue-800 dark:text-blue-50 font-semibold' : ''}
          ${!minimal && !showCheckboxes && !isSelected && isClickable ? `hover:bg-gray-50 dark:hover:bg-gray-700/50 ${idleTextClass}` : ''}
          ${!minimal && showCheckboxes ? `hover:bg-gray-50 dark:hover:bg-gray-700/50 ${idleTextClass}` : ''}
          ${!minimal && !isClickable && !hasChildren ? 'text-gray-400 dark:text-gray-500 cursor-default' : ''}
          ${!minimal && !isClickable && hasChildren ? groupTextClass : ''}
          ${selectedBgClass}
        `}
        style={{ paddingLeft: `${level * 16 + 8}px` }}
      >
        {/* Selected indicator - only show in non-checkbox mode */}
        {!minimal && !showCheckboxes && isSelected && (
          <div className="absolute left-0 top-0 bottom-0 w-1 bg-blue-600 dark:bg-blue-400 rounded-l" />
        )}
        {/* Expand/collapse toggle for items with children */}
        {hasChildren && !minimal ? (
          <button
            onClick={handleToggle}
            className="p-0.5 hover:bg-gray-200 dark:hover:bg-gray-600 rounded"
          >
            {isOpen ? (
              <ChevronDown className="w-3.5 h-3.5" />
            ) : (
              <ChevronRight className="w-3.5 h-3.5" />
            )}
          </button>
        ) : (
          <span className="w-4" /> // Spacer for alignment
        )}

        {/* Checkbox */}
        {showCheckboxes && (isClickable || hasChildren) && (
          <input
            type="checkbox"
            checked={
              item.chapter_id
                ? selectedChapterIds?.has(item.chapter_id) || false
                : allChildrenSelected
            }
            ref={(el) => {
              if (el) {
                el.indeterminate = hasChildren && someChildrenSelected
              }
            }}
            onChange={(e) => {
              e.stopPropagation()
              if (hasChildren) {
                // Node with children - toggle all descendants
                // If ANY children are selected (all or some), deselect all
                // If NO children are selected, select all
                const anyChildrenSelected = childChapterIds.some(id => selectedChapterIds?.has(id))

                if (anyChildrenSelected) {
                  // Deselect all descendants
                  childChapterIds.forEach(id => {
                    if (selectedChapterIds?.has(id)) {
                      onSelectChapter(id)
                    }
                  })
                } else {
                  // Select all descendants
                  childChapterIds.forEach(id => {
                    if (!selectedChapterIds?.has(id)) {
                      onSelectChapter(id)
                    }
                  })
                }
              } else if (item.chapter_id) {
                // Leaf node with no children - just toggle this chapter
                onSelectChapter(item.chapter_id)
              }
            }}
            className="mr-2 rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500"
          />
        )}

        {/* Icon */}
        {!showCheckboxes && hasChildren && !minimal ? (
          isOpen ? (
            <FolderOpen className="w-4 h-4 text-amber-500" />
          ) : (
            <Folder className="w-4 h-4 text-amber-500" />
          )
        ) : !showCheckboxes && !minimal ? (
          <FileText className={`w-4 h-4 ${isClickable ? 'text-blue-500' : 'text-gray-400'}`} />
        ) : null}

        {/* Title */}
        <span className={`truncate flex-1 ${titleWeightClass} ${selectedSizeClass}`}>
          {item.title || t('preview.untitled')}
        </span>

        {/* Chapter stats (translated/total) */}
        {!minimal && item.chapter_id && chapterStatsMap?.has(item.chapter_id) && (
          <span className={`${badgeSizeClass} text-gray-500 dark:text-gray-400 ml-1 whitespace-nowrap`}>
            {chapterStatsMap.get(item.chapter_id)!.translated} / {chapterStatsMap.get(item.chapter_id)!.total}
          </span>
        )}

        {/* Paragraph count badge (fallback) */}
        {!minimal && !chapterStatsMap && item.paragraph_count !== null && item.paragraph_count > 0 && (
          <span className={`${badgeSizeClass} text-gray-400 dark:text-gray-500 ml-1`}>
            {item.paragraph_count}
          </span>
        )}
      </div>

      {/* Children */}
      {hasChildren && isOpen && (
        <div>
          {item.children.map((child, index) => (
            <TocNode
              key={`${child.href || child.title}-${index}`}
              item={child}
              level={level + 1}
              selectedChapterId={selectedChapterId}
              onSelectChapter={onSelectChapter}
              defaultExpanded={expandAll ? true : containsSelected}
              expandAll={expandAll}
              compact={compact}
              minimal={minimal}
              fontClasses={fontClasses}
              showCheckboxes={showCheckboxes}
              selectedChapterIds={selectedChapterIds}
              chapterStatsMap={chapterStatsMap}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export function TreeChapterList({
  toc,
  selectedChapterId,
  onSelectChapter,
  fontClasses,
  expandAll = false,
  compact = false,
  minimal = false,
  showCheckboxes = false,
  selectedChapterIds,
  chapterStatsMap,
}: TreeChapterListProps) {
  const { t } = useTranslation()

  const textSizeClass = fontClasses?.paragraph || 'text-sm'

  if (!toc || toc.length === 0) {
    return (
      <div className={`text-gray-500 dark:text-gray-400 ${textSizeClass} p-4 text-center`}>
        {t('preview.noChapters')}
      </div>
    )
  }

  return (
    <div className="space-y-0.5">
      {toc.map((item, index) => (
        <TocNode
          key={`${item.href || item.title}-${index}`}
          item={item}
          level={0}
          selectedChapterId={selectedChapterId}
          onSelectChapter={onSelectChapter}
          defaultExpanded={expandAll}
          expandAll={expandAll}
          compact={compact}
          minimal={minimal}
          fontClasses={fontClasses}
          showCheckboxes={showCheckboxes}
          selectedChapterIds={selectedChapterIds}
          chapterStatsMap={chapterStatsMap}
        />
      ))}
    </div>
  )
}
