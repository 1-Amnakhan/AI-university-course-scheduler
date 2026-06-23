# csp.py
# CSP model builder and constraint checker

def build_csp(courses, rooms, time_slots):
    """
    Returns:
        variables      : list of variable names, e.g. ["AI_S1", "AI_S2", "OS_S1", ...]
        domains        : dict  var -> list of (timeslot, room) tuples
        variables_meta : dict  var -> course dict  (so we can look up teacher later)
    """
    variables = []
    domains = {}
    variables_meta = {}

    for course in courses:
        for s in range(course["sessions_per_week"]):
            var = f"{course['id']}_S{s+1}"
            variables.append(var)
            domains[var] = [(t, r) for t in time_slots for r in rooms]
            variables_meta[var] = course

    return variables, domains, variables_meta


def is_consistent(var, value, assignment, variables_meta):
    """
    Check all hard constraints between `var=value` and everything already assigned.
    Hard constraints:
      1. No two sessions share the same room at the same time.
      2. No teacher teaches two sessions at the same time.
      3. No course has two sessions at the same time slot (same course, different session).
    """
    t_new, r_new = value
    course_new = variables_meta[var]

    for assigned_var, (t_assigned, r_assigned) in assignment.items():
        course_assigned = variables_meta[assigned_var]

        if t_new == t_assigned:
            # Constraint 1: room clash
            if r_new == r_assigned:
                return False
            # Constraint 2: teacher clash
            if course_new["teacher"] == course_assigned["teacher"]:
                return False
            # Constraint 3: same course double-booked at same slot
            if course_new["id"] == course_assigned["id"]:
                return False

    return True
