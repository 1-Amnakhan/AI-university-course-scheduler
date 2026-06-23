# main.py
# Entry point — runs the full CSP scheduler pipeline

import time
from data import courses, rooms, time_slots
from csp import build_csp
from solver import solve
from visualize import build_dataframe, print_table, export_csv, visualize_grid


def verify_solution(solution, variables_meta):
    """
    Post-solve verification:
    Check every pair of assigned sessions for constraint violations.
    Returns a list of violation strings (empty = perfect schedule).
    """
    violations = []
    items = list(solution.items())
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            var_a, (t_a, r_a) = items[i]
            var_b, (t_b, r_b) = items[j]
            if t_a != t_b:
                continue
            ca = variables_meta[var_a]
            cb = variables_meta[var_b]
            if r_a == r_b:
                violations.append(f"ROOM CLASH: {var_a} and {var_b} both in {r_a} at {t_a}")
            if ca["teacher"] == cb["teacher"]:
                violations.append(f"TEACHER CLASH: {ca['teacher']} double-booked at {t_a} ({var_a} & {var_b})")
            if ca["id"] == cb["id"]:
                violations.append(f"COURSE CLASH: {ca['id']} has two sessions at {t_a}")
    return violations


def print_summary(courses, rooms, time_slots, elapsed, nodes, solution):
    total_sessions = sum(c["sessions_per_week"] for c in courses)
    print("\n" + "="*75)
    print("  SCHEDULER SUMMARY")
    print("="*75)
    print(f"  Courses           : {len(courses)}")
    print(f"  Total sessions    : {total_sessions}")
    print(f"  Rooms available   : {len(rooms)}")
    print(f"  Time slots        : {len(time_slots)}")
    print(f"  Nodes explored    : {nodes}")
    print(f"  Time to solve     : {elapsed:.4f} seconds")
    print(f"  Sessions assigned : {len(solution) if solution else 0} / {total_sessions}")
    print("="*75 + "\n")


def main():
    print("\n[*] Building CSP model...")
    variables, domains, variables_meta = build_csp(courses, rooms, time_slots)
    print(f"    Variables (sessions to schedule) : {len(variables)}")
    print(f"    Domain size per variable         : {len(list(domains.values())[0])} (timeslot, room) pairs")

    print("[*] Running Backtracking Search with MRV + Forward Checking...")
    start = time.time()
    solution, nodes = solve(variables, domains, variables_meta)
    elapsed = time.time() - start

    print_summary(courses, rooms, time_slots, elapsed, nodes, solution)

    if solution is None:
        print("[!] NO SOLUTION FOUND.")
        print("    Tip: Add more rooms or time slots in data.py to relax constraints.\n")
        return

    print("[*] Verifying solution against all constraints...")
    violations = verify_solution(solution, variables_meta)
    if violations:
        print(f"[!] {len(violations)} VIOLATION(S) DETECTED:")
        for v in violations:
            print(f"    - {v}")
    else:
        print("[✓] All constraints satisfied — schedule is conflict-free!\n")

    df = build_dataframe(solution, variables_meta)
    print_table(df)
    export_csv(df)

    print("[*] Generating visual timetable grid...")
    visualize_grid(solution, variables_meta, time_slots, rooms)


if __name__ == "__main__":
    main()
