"""Preliminary geometry and budget logic; NEVER a certified engineering design."""
from decimal import Decimal, ROUND_HALF_UP

def plot_preview(width_m: float, depth_m: float, setback_front=0, setback_back=0, setback_left=0, setback_right=0):
    if not (3 <= width_m <= 1000 and 3 <= depth_m <= 1000):
        raise ValueError('Land dimensions must be between 3 and 1000 metres')
    if min(setback_front,setback_back,setback_left,setback_right) < 0:
        raise ValueError('Setbacks cannot be negative')
    footprint_w = max(0, width_m - setback_left - setback_right)
    footprint_d = max(0, depth_m - setback_front - setback_back)
    return {'plot_area_m2': round(width_m*depth_m,2), 'illustrative_envelope_m2':round(footprint_w*footprint_d,2),
            'footprint_width_m':round(footprint_w,2), 'footprint_depth_m':round(footprint_d,2),
            'regulatory_verified':False, 'drawing_approved':False}

def line_cost(quantity, approved_unit_rate):
    if approved_unit_rate is None: return None
    q, r = Decimal(str(quantity)), Decimal(str(approved_unit_rate))
    if q < 0 or r < 0: raise ValueError('Negative amount not allowed')
    return str((q*r).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
