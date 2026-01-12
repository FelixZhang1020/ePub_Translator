# Prompt Template Variables Reference

This document describes all available variables for prompt templates, organized by stage.

## Quick Reference

| Stage | Available Variable Categories |
|-------|------------------------------|
| **Analysis** | Project, Content, Meta, User |
| **Translation** | Project, Content, Context, Pipeline, Derived, Meta, User |
| **Optimization** | Project, Content, Pipeline, Derived, Meta, User |
| **Proofreading** | Project, Content, Derived, Meta, User |

## Variable Categories

### Project
Static metadata from the ePub project (available in all stages)

### Content
Current paragraph or text being processed

### Context
Surrounding paragraphs for translation continuity (only in Translation)

### Pipeline
Output from previous processing steps

### Derived
Values extracted from analysis results (NOT available in Analysis stage)

### Meta
Runtime computed values

### User
Custom variables defined per project

---

## Analysis Stage

Variables available when generating analysis results.

### Project Variables (4)
| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `{{project.title}}` | string | Book title from ePub metadata | "Knowing God" |
| `{{project.author}}` | string | Author name from ePub metadata | "J.I. Packer" |
| `{{project.source_language}}` | string | Source language of the book | "en" |
| `{{project.target_language}}` | string | Target translation language | "zh-CN" |

### Content Variables (1)
| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `{{content.sample_paragraphs}}` | string | Sample paragraphs for book analysis (REQUIRED) | "Paragraph 1: The knowledge of God..." |

### Meta Variables (1)
| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `{{meta.stage}}` | string | Current processing stage | "analysis" |

### User Variables
| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `{{user.macros}}` | object | Custom macro definitions for reuse | `{"book_info": "{{project.title}}"}` |
| `{{user.*}}` | any | Any custom variables defined in project variables.json | - |

---

## Translation Stage

Variables available when generating translations.

### Project Variables (4)
| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `{{project.title}}` | string | Book title | "Knowing God" |
| `{{project.author}}` | string | Author name | "J.I. Packer" |
| `{{project.author_background}}` | string | Custom author background information | "J.I. Packer (1926-2020) was a British-born Canadian evangelical theologian..." |
| `{{project.source_language}}` | string | Source language | "en" |
| `{{project.target_language}}` | string | Target translation language | "zh-CN" |

### Content Variables (3)
| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `{{content.source}}` | string | Source text to be translated (REQUIRED) | "The grace of God is infinite and eternal." |
| `{{content.chapter_title}}` | string | Title of the current chapter | "Chapter 1: Knowing and Being Known" |
| `{{content.source_text}}` | string | Legacy alias for content.source | (same as above) |

### Context Variables (3)
| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `{{context.previous_source}}` | string | Previous paragraph source text | "In the previous chapter, we discussed..." |
| `{{context.previous_target}}` | string | Previous paragraph translation | "在前一章中，我们讨论了..." |
| `{{context.next_source}}` | string | Next paragraph source text | "Building on this foundation..." |

### Pipeline Variables (1)
| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `{{pipeline.reference_translation}}` | string | Reference translation from existing sources | "神的恩典是无穷无尽的。" |

### Derived Variables (19)
All extracted from analysis results:

| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `{{derived.author_name}}` | string | Author name extracted from analysis | "J.I. Packer" |
| `{{derived.author_biography}}` | string | Author biography | "British-born Canadian evangelical theologian (1926-2020)" |
| `{{derived.writing_style}}` | string | Writing style | "Academic theological prose with pastoral warmth" |
| `{{derived.tone}}` | string | Tone of the writing | "Reverent, instructive, encouraging" |
| `{{derived.target_audience}}` | string | Target audience | "Seminary students and lay theologians" |
| `{{derived.genre_conventions}}` | string | Genre conventions | "Systematic theology with scriptural exposition" |
| `{{derived.terminology_table}}` | terminology | Formatted terminology table | "- grace: 恩典\n- covenant: 圣约" |
| `{{derived.priority_order}}` | array | Translation priority order | `["信", "达", "雅"]` |
| `{{derived.faithfulness_boundary}}` | string | Content that must be translated literally | "Technical terms, Scripture quotes, data" |
| `{{derived.permissible_adaptation}}` | string | Areas where adaptation is allowed | "Sentence restructuring, connector optimization" |
| `{{derived.red_lines}}` | string | Prohibited translation behaviors | "Adding commentary, omitting content, changing stance" |
| `{{derived.style_constraints}}` | string | Style and tone constraints | "Avoid colloquialisms, maintain formal register" |
| `{{derived.custom_guidelines}}` | array | Custom translation guidelines | `["Always capitalize references to God"]` |
| `{{derived.has_analysis}}` | boolean | Whether analysis exists | true |
| `{{derived.has_writing_style}}` | boolean | Whether writing style is defined | true |
| `{{derived.has_tone}}` | boolean | Whether tone is defined | true |
| `{{derived.has_terminology}}` | boolean | Whether terminology table exists | true |
| `{{derived.has_target_audience}}` | boolean | Whether target audience is defined | true |
| `{{derived.has_genre_conventions}}` | boolean | Whether genre conventions are defined | true |
| `{{derived.has_translation_principles}}` | boolean | Whether translation principles are defined | true |
| `{{derived.has_custom_guidelines}}` | boolean | Whether custom guidelines exist | false |
| `{{derived.has_style_constraints}}` | boolean | Whether style constraints exist | false |

### Meta Variables (5)
| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `{{meta.word_count}}` | number | Word count of the source text | 156 |
| `{{meta.char_count}}` | number | Character count of the source text | 892 |
| `{{meta.paragraph_index}}` | number | Index of current paragraph within chapter | 5 |
| `{{meta.chapter_index}}` | number | Index of current chapter | 3 |
| `{{meta.stage}}` | string | Current processing stage | "translation" |

### User Variables
| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `{{user.glossary}}` | object | Custom terminology glossary | `{"covenant": "圣约"}` |
| `{{user.special_instructions}}` | string | Special handling instructions | "This book contains many Puritan-era references..." |
| `{{user.macros}}` | object | Custom macro definitions | `{"book_info": "{{project.title}}"}` |
| `{{user.*}}` | any | Any custom variables defined in project | - |

---

## Optimization Stage

Variables available when optimizing translations based on suggestions.

### Project Variables (3)
| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `{{project.title}}` | string | Book title | "Knowing God" |
| `{{project.author}}` | string | Author name | "J.I. Packer" |
| `{{project.target_language}}` | string | Target translation language | "zh-CN" |

### Content Variables (3)
| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `{{content.source}}` | string | Source text | "The grace of God is infinite and eternal." |
| `{{content.target}}` | string | Current translation | "神的恩典是无限而永恒的。" |
| `{{content.chapter_title}}` | string | Current chapter title | "Chapter 1: Knowing and Being Known" |

### Pipeline Variables (1)
| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `{{pipeline.suggested_changes}}` | string | User-confirmed suggestions for optimization | "Change '无穷无尽' to '无限而永恒' for better accuracy." |

### Derived Variables (10)
| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `{{derived.author_name}}` | string | Author name from analysis | "J.I. Packer" |
| `{{derived.author_biography}}` | string | Author biography | "British-born Canadian evangelical theologian (1926-2020)" |
| `{{derived.writing_style}}` | string | Writing style | "Academic theological prose with pastoral warmth" |
| `{{derived.tone}}` | string | Tone of the writing | "Reverent, instructive, encouraging" |
| `{{derived.terminology_table}}` | terminology | Formatted terminology table | "- grace: 恩典\n- covenant: 圣约" |
| `{{derived.has_analysis}}` | boolean | Whether analysis exists | true |
| `{{derived.has_writing_style}}` | boolean | Whether writing style is defined | true |
| `{{derived.has_tone}}` | boolean | Whether tone is defined | true |
| `{{derived.has_terminology}}` | boolean | Whether terminology table exists | true |

### Meta Variables (3)
| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `{{meta.word_count}}` | number | Word count of the source text | 156 |
| `{{meta.char_count}}` | number | Character count of the source text | 892 |
| `{{meta.stage}}` | string | Current processing stage | "optimization" |

### User Variables
| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `{{user.special_instructions}}` | string | Special handling instructions | "This book contains many Puritan-era references..." |
| `{{user.macros}}` | object | Custom macro definitions | `{"book_info": "{{project.title}}"}` |
| `{{user.*}}` | any | Any custom variables defined in project | - |

---

## Proofreading Stage

Variables available when proofreading final translations.

### Project Variables (2)
| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `{{project.title}}` | string | Book title | "Knowing God" |
| `{{project.author}}` | string | Author name | "J.I. Packer" |

### Content Variables (3)
| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `{{content.source}}` | string | Source text | "The grace of God is infinite and eternal." |
| `{{content.target}}` | string | Current translation | "神的恩典是无限而永恒的。" |
| `{{content.chapter_title}}` | string | Current chapter title | "Chapter 1: Knowing and Being Known" |

### Derived Variables (10)
| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `{{derived.author_name}}` | string | Author name from analysis | "J.I. Packer" |
| `{{derived.author_biography}}` | string | Author biography | "British-born Canadian evangelical theologian (1926-2020)" |
| `{{derived.writing_style}}` | string | Writing style | "Academic theological prose with pastoral warmth" |
| `{{derived.tone}}` | string | Tone of the writing | "Reverent, instructive, encouraging" |
| `{{derived.terminology_table}}` | terminology | Formatted terminology table | "- grace: 恩典\n- covenant: 圣约" |
| `{{derived.has_analysis}}` | boolean | Whether analysis exists | true |
| `{{derived.has_writing_style}}` | boolean | Whether writing style is defined | true |
| `{{derived.has_tone}}` | boolean | Whether tone is defined | true |
| `{{derived.has_terminology}}` | boolean | Whether terminology table exists | true |

### Meta Variables (3)
| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `{{meta.paragraph_index}}` | number | Index of current paragraph within chapter | 5 |
| `{{meta.chapter_index}}` | number | Index of current chapter | 3 |
| `{{meta.stage}}` | string | Current processing stage | "proofreading" |

### User Variables
| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| `{{user.glossary}}` | object | Custom terminology glossary | `{"covenant": "圣约"}` |
| `{{user.special_instructions}}` | string | Special handling instructions | "This book contains many Puritan-era references..." |
| `{{user.macros}}` | object | Custom macro definitions | `{"book_info": "{{project.title}}"}` |
| `{{user.*}}` | any | Any custom variables defined in project | - |

---

## Template Syntax

### Basic Variables
```handlebars
{{variable}}              # Simple variable
{{namespace.variable}}    # Namespaced variable (recommended)
{{variable | default:"fallback value"}}  # With fallback
```

### Conditionals
```handlebars
{{#if variable}}
  Content when variable exists
{{/if}}

{{#if variable}}
  Content when variable exists
{{#else}}
  Content when variable doesn't exist
{{/if}}

{{#if var1 && var2}}
  Content when BOTH variables exist
{{/if}}

{{#if var1 || var2}}
  Content when EITHER variable exists
{{/if}}

{{#unless variable}}
  Content when variable doesn't exist
{{/unless}}
```

### Loops
```handlebars
{{#each array}}
  {{this}}
{{/each}}

{{#each array}}
  Item {{@index}}: {{this}}
{{/each}}

{{#each dictionary}}
  {{@key}}: {{this}}
{{/each}}
```

### Macros
```handlebars
{{@macro_name}}  # Insert predefined macro
```

**Default Macros:**
- `{{@book_info}}` → `"{{project.title}} by {{project.author}}"`
- `{{@style_guide}}` → Formatted style and tone section
- `{{@terminology_section}}` → Formatted terminology table section

### Type Formatting
```handlebars
{{variable:list}}        # Format as bullet list
{{variable:table}}       # Format as markdown table
{{variable:terminology}} # Format as "term: translation" pairs
{{variable:json}}        # Format as pretty JSON
{{variable:inline}}      # Format as comma-separated values
```

---

## Legacy Aliases (Deprecated but Still Supported)

For backward compatibility, these aliases still work but should not be used in new templates:

| Legacy Name | Canonical Name | Available In |
|-------------|----------------|--------------|
| `{{source_text}}` | `{{content.source}}` | Translation, Optimization |
| `{{original_text}}` | `{{content.source}}` | Proofreading |
| `{{translated_text}}` | `{{content.target}}` | Optimization, Proofreading |
| `{{existing_translation}}` | `{{content.target}}` | Optimization, Proofreading |
| `{{previous_translation}}` | `{{context.previous_target}}` | Translation |
| `{{previous_original}}` | `{{context.previous_source}}` | Translation |

**Recommendation:** Use canonical names (with namespace prefix) in all new templates.

---

## Best Practices

### 1. Always Use Namespaced Names
```handlebars
# Good
{{content.source}}
{{derived.terminology_table}}

# Avoid (legacy style)
{{source_text}}
{{terminology_table}}
```

### 2. Check Existence Before Use
```handlebars
# For optional derived variables
{{#if derived.has_terminology}}
### Terminology
{{derived.terminology_table}}
{{/if}}
```

### 3. Provide Fallbacks for Optional Fields
```handlebars
{{project.author_background | default:"No author information available"}}
```

### 4. Use Conditionals for Stage-Aware Content
```handlebars
{{#if context.previous_source}}
**Previous Context:**
{{context.previous_source}}
{{/if}}
```

### 5. Required Variables by Stage

**Analysis:**
- `{{content.sample_paragraphs}}` - MUST be present

**Translation:**
- `{{content.source}}` - MUST be present

**Optimization:**
- `{{content.source}}` - MUST be present
- `{{content.target}}` - MUST be present

**Proofreading:**
- `{{content.source}}` - MUST be present
- `{{content.target}}` - MUST be present

---

## Common Patterns

### Book Information Header
```handlebars
**Book:** {{project.title}}
**Author:** {{project.author}}
{{#if project.author_background}}

**About the Author:**
{{project.author_background}}
{{/if}}
```

### Terminology Integration
```handlebars
{{#if derived.has_terminology}}
## Key Terminology

{{derived.terminology_table}}

Please use these standardized translations consistently.
{{/if}}
```

### Context-Aware Translation
```handlebars
{{#if context.previous_source}}
**Previous Paragraph (Original):**
{{context.previous_source}}

**Previous Paragraph (Translation):**
{{context.previous_target}}

---
{{/if}}

**Current Paragraph to Translate:**
{{content.source}}
```

### Style Guide Integration
```handlebars
{{#if derived.has_analysis}}
## Translation Guidelines

{{#if derived.writing_style}}
**Writing Style:** {{derived.writing_style}}
{{/if}}

{{#if derived.tone}}
**Tone:** {{derived.tone}}
{{/if}}

{{#if derived.has_translation_principles}}
### Translation Principles

**Priority Order:** {{derived.priority_order}}

**Faithfulness Boundary:** {{derived.faithfulness_boundary}}

**Permissible Adaptations:** {{derived.permissible_adaptation}}

**Red Lines:** {{derived.red_lines}}
{{/if}}
{{/if}}
```

---

## Validation

The system will automatically validate templates:
- Check for undefined variables
- Check for unclosed blocks
- Check for mismatched brackets
- Warn about stage-inappropriate variables

Use the preview function in the UI to test your templates before saving.

---

## See Also

- `metadata.json` - Template metadata and descriptions
- `defaults.json` - Default template selection by stage
- `shared/variable-schema.json` - Machine-readable variable schema
