# utils/attendance.py
"""
Utility functions for guard attendance management
"""

def get_attendance_status(shift):
    """
    Calculate the attendance status for a guard shift
    
    Priority:
    1. Manual override (if set by admin)
    2. Automatic status based on check-in/check-out
    
    Returns:
        str: Status code ('present', 'absent', 'late', 'leave', 'on_duty', 'completed')
    """
    
    # 1. Check for manual override first (highest priority)
    if shift.attendance_override and shift.attendance_override != 'auto':
        return shift.attendance_override
    
    # 2. Automatic status based on check-in/check-out
    if shift.check_out:
        # Shift completed
        return 'completed'
    
    if shift.check_in:
        # Currently on duty
        return 'on_duty'
    
    # 3. No check-in = absent
    return 'absent'


def get_attendance_status_display(shift):
    """
    Get human-readable display text for attendance status
    
    Returns:
        str: Display text with emoji
    """
    status = get_attendance_status(shift)
    
    status_map = {
        'present': '✓ Present',
        'absent': '✗ Absent',
        'late': '⏰ Late',
        'leave': '📅 Leave',
        'on_duty': '🟢 On Duty',
        'completed': '✅ Completed'
    }
    
    display = status_map.get(status, '❓ Unknown')
    
    # Add "(Manual)" suffix if manually overridden
    if shift.attendance_override and shift.attendance_override != 'auto':
        display += ' (Manual)'
    
    return display


def get_attendance_status_class(shift):
    """
    Get CSS class for attendance status badge
    
    Returns:
        str: CSS class name
    """
    status = get_attendance_status(shift)
    
    class_map = {
        'present': 'status-present',
        'absent': 'status-absent',
        'late': 'status-late',
        'leave': 'status-leave',
        'on_duty': 'status-present',
        'completed': 'status-present'
    }
    
    return class_map.get(status, 'status-absent')