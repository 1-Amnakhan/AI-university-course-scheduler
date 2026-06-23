# solver.py
# Backtracking search with MRV heuristic and Forward Checking

import copy
from csp import is_consistent

# Global counter to track nodes explored
nodes_explored = 0


def select_unassigned_var(variables, domains, assignment):
    """
    MRV (Minimum Remaining Values) heuristic:
    Choose the unassigned variable with the fewest legal values left in its domain.
    Ties broken by the order they appear in the variable list.
    """
    unassigned = [v for v in variables if v not in assignment]
    return min(unassigned, key=lambda v: len(domains[v]))


def forward_check(var, value, domains, assignment, variables_meta):
    """
    After assigning var=value, remove from every *unassigned* variable's domain
    any value that would immediately violate a constraint with this new assignment.

    Returns:
        pruned  : dict  { neighbor_var: [list of values removed] }
                  (needed so we can restore them on backtrack)
        failure : True if any domain was wiped out (dead end detected early)
    """
    pruned = {}
    t_new, r_new = value
    course_new = variables_meta[var]

    for other_var in domains:
        if other_var in assignment or other_var == var:
            continue

        course_other = variables_meta[other_var]
        to_remove = []

        for (t_other, r_other) in domains[other_var]:
            if t_other == t_new:
                # Would clash: same room
                if r_other == r_new:
                    to_remove.append((t_other, r_other))
                    continue
                # Would clash: same teacher
                if course_other["teacher"] == course_new["teacher"]:
                    to_remove.append((t_other, r_other))
                    continue
                # Would clash: same course double-booked
                if course_other["id"] == course_new["id"]:
                    to_remove.append((t_other, r_other))
                    continue

        if to_remove:
            pruned[other_var] = to_remove
            for val in to_remove:
                domains[other_var].remove(val)

            # Domain wipe-out: dead end, signal failure immediately
            if len(domains[other_var]) == 0:
                return pruned, True   # failure

    return pruned, False  # no failure


def restore_domains(pruned, domains):
    """Undo the pruning done by forward_check when we backtrack."""
    for var, removed_values in pruned.items():
        domains[var].extend(removed_values)


def backtrack(assignment, variables, domains, variables_meta):
    global nodes_explored

    if len(assignment) == len(variables):
        return assignment  # complete solution found

    var = select_unassigned_var(variables, domains, assignment)
    nodes_explored += 1

    for value in list(domains[var]):   # iterate over a copy (forward-check modifies domains)
        if is_consistent(var, value, assignment, variables_meta):
            assignment[var] = value

            # Forward checking: prune domains of unassigned neighbors
            pruned, failure = forward_check(var, value, domains, assignment, variables_meta)

            if not failure:
                result = backtrack(assignment, variables, domains, variables_meta)
                if result is not None:
                    return result

            # Backtrack: undo assignment and restore pruned values
            del assignment[var]
            restore_domains(pruned, domains)

    return None  # no valid assignment found from this state


def solve(variables, domains, variables_meta):
    """Entry point. Returns solution dict or None."""
    global nodes_explored
    nodes_explored = 0
    # Work on a deep copy so original domains are preserved
    domains_copy = copy.deepcopy(domains)
    solution = backtrack({}, variables, domains_copy, variables_meta)
    return solution, nodes_explored
