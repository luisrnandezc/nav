# UI Styles

The `ui` app owns shared CSS primitives for internal staff-facing pages.

Use `ui/css/core.css` for new pages that should follow the FMS/SMS visual
language:

```html
{% include "ui/includes/core_css.html" %}
```

App-specific CSS should still live in each app when it describes domain
layouts or behavior, such as evaluation forms, scheduling calendars, or
maintenance-specific report cards.

Current layers:

- `tokens.css`: colors, spacing, radii, common design values.
- `base.css`: page reset, body defaults, text/input inheritance.
- `layout.css`: page containers, headers, panels, section headers.
- `components.css`: buttons, lists, cards, detail rows, badges, empty states.
- `forms.css`: shared input, select, textarea, and form-grid primitives.
- `utilities.css`: small reusable utility classes.
