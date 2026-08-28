# Nightingale Visual System

The Care Note uses a calm editorial interface inspired by the supplied patient
history wireframe. It borrows the reference's hierarchy and material language,
not its content or product structure. Clinical readability, provenance, role
boundaries, and accessible interaction states remain authoritative.

## Dark mode

| Role | Value |
|---|---|
| Page background | `#102322` |
| Primary card | `#1D302F` |
| Secondary card/input | `#243B39` |
| Primary text | `#FFFFFF` |
| Secondary text | `#CDCDCD` |
| Focus/accent | `#36FFDB` |

Turquoise is reserved for primary actions, focus states, selected controls,
timeline markers, and small status emphasis. It is not used as a large
decorative fill except for the primary call to action.

## Daylight mode

Daylight mode keeps the same spacing, typography, and component hierarchy with
a clean mineral palette:

| Role | Value |
|---|---|
| Page background | `#EDF6F2` |
| Primary card | `#FFFFFF` |
| Secondary card/input | `#F5FAF8` |
| Primary text | `#16312F` |
| Secondary text | `#617773` |
| Accessible focus/accent | `#087C6C` |

The daylight accent is deliberately darker than the dark-mode turquoise so
text, borders, and controls retain sufficient contrast on white surfaces.

## Shared rules

- DM Sans is bundled locally; headings use light weights, uppercase treatment,
  tight tracking, and generous surrounding space.
- Cards use 20–28 px radii, thin low-contrast borders, and quiet shadows.
- Body copy stays compact, but form labels and clinical content remain legible.
- Risk, authorship, provenance, and status are never communicated by color
  alone; labels and text remain present.
- Keyboard focus uses a visible accent ring in both themes.
- Theme selection begins with the system preference and persists locally.
