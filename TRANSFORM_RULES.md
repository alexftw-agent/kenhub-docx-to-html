# DOCX → Kenhub Admin HTML Transformation Rules

Based on analysis of 5 sample pairs (DOCX source + target admin HTML).

## Content Types

### Articles (samples 01, 03)
- Standard anatomy articles
- No `learning-path` wrapper
- Have `article-table-of-contents`, `article-infobox`, `article-meta-content`

### Study Units (samples 02, 04, 05)
- Wrapped in `<div class="learning-path">...</div>`
- Start with learning objectives in `<div class="highlighted-box">`
- May have quizzes, overview images

## DOCX Paragraph Styles → HTML

| DOCX Style | HTML Output |
|---|---|
| `Title` or `Heading 1` | **Skipped** (title is metadata, not in body HTML) |
| `Heading 2` | `<h2>heading text</h2>` |
| `Heading 3` | `<h3>heading text</h3>` |
| `normal` (with numPr) | `<li>` inside `<ul>` or `<ol>` |
| `normal` (regular) | `<p>paragraph text</p>` |
| Empty paragraph | **Skipped** |

## Run Formatting → HTML

| DOCX Format | HTML |
|---|---|
| Bold run | `<strong>text</strong>` |
| Italic run | `<em>text</em>` |
| Bold+Italic | `<strong><em>text</em></strong>` |
| Plain run | raw text |

## Lists

- Paragraphs with `numPr` in XML → list items
- Consecutive list items grouped into `<ul>` (unordered) or `<ol>` (ordered)
- numPr `numId` determines which list they belong to
- Need to detect ordered vs unordered from the numbering definition

## Tables → `<table class="facts-table">`

```html
<table class="facts-table">
  <caption>Caption text from first merged row</caption>
  <tbody>
    <tr>
      <td>Label</td>
      <td>Value with<br>line breaks</td>
    </tr>
  </tbody>
</table>
```

- First row is usually caption (merged cells)
- Some cells use `<th>` instead of `<td>` (inconsistent, but appears for header-like first column)
- Bold text within cells → `<strong>`
- Line breaks within cells → `<br>`
- Some tables have `data-terminology-language="english"` or `"latin"` attribute

## Special Markers in DOCX → Widget Placeholders

These are text patterns in the DOCX that map to specific HTML widget divs. The converter should output placeholder comments or the actual div structure.

| DOCX Pattern | HTML Output |
|---|---|
| `[Video: ...]` | `<div class="embedded-video-container embedded-widget" data-controller="embedded_video" data-embedded_video-id-value="XXXX" isvisible="true"></div>` |
| `[Table of Contents]` / `[Table of contents]` | `<div class="article-table-of-contents" data-skip-algolia="1">Table of Contents</div>` |
| `[Green highlight ...] slug1,slug2` | `<div class="image-gallery-container embedded-widget outset-left open" data-image-slugs="slug1,slug2"></div>` |
| `[Highlights gallery ...] slug1,slug2` | `<div class="image-gallery-container embedded-widget outset-left open" data-image-slugs="slug1,slug2"></div>` |
| `Gallery: term1, term2, term3` | `<div class="image-gallery-container embedded-widget open" data-image-slugs="slug1,slug2,slug3"></div>` |
| `[Blue box: text]` | `<div class="highlighted-box"><p>text</p></div>` |
| `[Caption text]Following text` (overview images) | `<div class="overview-images-container embedded-widget" data-overview-image-ids="XXXX">...</div>` — **These need manual ID assignment**, converter outputs placeholder |
| `[LINK TO VIDEO]` | Placeholder: `<!-- VIDEO EMBED: Add video ID -->` |
| Content box links like `/en/study/...` | `<div class="contentbox-container" data-contentbox-link="/en/study/..." data-skip-algolia="1">/en/study/...</div>` |
| Quiz references | `<div class="embedded-quiz-container embedded-widget" data-quiz-id="XXXX"></div>` — placeholder |

## Metadata Lines (Stripped from output)

These appear at the top of some DOCX files and should NOT appear in the HTML body:
- `Title: ...`
- `Description: ...`
- `SEO title: ...`
- `SEO description: ...`
- `Container: ...`
- `Position: ...`

## Wrappers

### Study Units
If the DOCX has "Learning objectives" heading or starts with learning objectives pattern:
```html
<div class="highlighted-box">
  <p><strong>Learning objectives</strong></p>
  <p>After completing this study unit, you will be able to:</p>
  <ol>
    <li>...</li>
  </ol>
</div>
<div class="learning-path">
  <!-- rest of content -->
</div>
```

### Article Clinical Box
Text marked as clinical/infobox:
```html
<div class="article-infobox">
  <h2>Title</h2>
  <p>Content...</p>
</div>
```

### Sources Section
```html
<div class="article-meta-content">
  <h2>Sources</h2>
  <div class="quality-commitment" data-skip-algolia="1">...</div>
  <p>References:</p>
  <ul><li>...</li></ul>
</div>
```

## Key Observations

1. **Links are NOT in the DOCX** — they're added manually in admin after pasting. The converter does NOT need to create `<a>` tags.
2. **Widget IDs** (video IDs, image IDs, quiz IDs) are NOT in the DOCX — those are assigned in admin. Converter outputs placeholders.
3. **Image slugs** ARE sometimes in the DOCX (after gallery markers like `[Green highlight ...] slug1,slug2`)
4. **The converter's job is to produce clean, correctly-structured HTML** that can be pasted into the admin. Interactive elements are added afterward.
