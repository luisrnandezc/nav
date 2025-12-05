from django import template

register = template.Library()

# Evaluations are stored as SEVERITY+PROBABILITY (e.g. "A3", "D4").
# The sets below are defined in that same order for simplicity.
RED_SET = {'A5', 'B5', 'C5', 'A4', 'B4', 'A3'}
ORANGE_SET = {'D5', 'E5', 'C4', 'D4', 'E4', 'B3', 'C3', 'D3', 'A2', 'B2', 'C2', 'A1'}
GREEN_SET = {'E3', 'D2', 'E2', 'B1', 'C1', 'D1', 'E1'}

@register.filter
def risk_color(evaluation):
    if not evaluation:
        return ''
    eval_str = str(evaluation).upper().strip()

    if eval_str in RED_SET:
        return 'badge-red'
    if eval_str in ORANGE_SET:
        return 'badge-orange'
    if eval_str in GREEN_SET:
        return 'badge-green'
    return ''  # default styling