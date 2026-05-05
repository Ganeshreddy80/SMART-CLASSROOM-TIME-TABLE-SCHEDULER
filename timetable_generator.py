"""
Timetable Generation Algorithm — v2 (Backtracking + Soft Constraints)

Improvements over v1:
  • Backtracking: if a course can't be placed, undo up to 3 previous
    placements for the same section and retry with different arrangements
  • Soft constraint scoring: penalizes back-to-back days for same subject,
    penalizes Easy courses in prime morning slots, rewards gaps
  • Structured conflict reports: explains *why* each course couldn't be placed
  • validate_timetable(): post-generation invariant checks
  • regenerate_partial(department_id): re-generate for one department only

Key hard constraints (never violated):
  • Faculty can only teach one section at a time
  • A room can only hold one class at a time
  • A section can only be in one class at a time
  • Maximum MAX_CLASSES_PER_DAY classes per section per day
"""
from models import db, TimetableEntry, Section, Course, Faculty, Classroom, University
from sqlalchemy import func
import json, copy

MAX_CLASSES_PER_DAY = 6   # per section (allows up to 30 classes per week with 6 slots/day)
MAX_BACKTRACK_DEPTH = 10  # increased to allow resolving complex conflicts
LUNCH_SLOT = "12:00-1:00"


# ═══════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════

def generate_timetable():
    """
    Main entry point.  Clears existing timetable and generates fresh.
    Returns dict with 'success', 'entries_created', 'conflicts' keys.
    """
    TimetableEntry.query.delete()
    db.session.commit()

    university = University.query.first()
    if not university:
        return _fail('University not configured')

    days = university.get_days()
    timeslots = university.get_timeslots()
    if not days or not timeslots:
        return _fail('No days or timeslots configured')

    sections = Section.query.all()
    if not sections:
        return _fail('No sections found. Generate sections first.')

    classrooms = Classroom.query.all()
    if not classrooms:
        return _fail('No classrooms found. Configure university first.')

    schedule = _empty_schedule(days, timeslots)
    entries_created, conflicts = _schedule_sections(sections, days, timeslots, classrooms, schedule)

    db.session.commit()

    return {
        'success': True,
        'message': f'Timetable generated successfully. {entries_created} entries created.',
        'entries_created': entries_created,
        'conflicts': conflicts,
    }


def regenerate_partial(department_id):
    """
    Re-generate timetable for a single department without touching others.
    Deletes only that department's entries, rebuilds schedule from survivors,
    then runs the algorithm for that department's sections.
    """
    university = University.query.first()
    if not university:
        return _fail('University not configured')

    days = university.get_days()
    timeslots = university.get_timeslots()
    classrooms = Classroom.query.all()

    # Delete entries for this department's sections
    dept_sections = Section.query.filter_by(department_id=department_id).all()
    dept_section_ids = [s.id for s in dept_sections]
    if not dept_section_ids:
        return _fail('No sections for this department')

    TimetableEntry.query.filter(TimetableEntry.section_id.in_(dept_section_ids)).delete()
    db.session.commit()

    # Rebuild schedule from surviving entries
    schedule = _empty_schedule(days, timeslots)
    for entry in TimetableEntry.query.all():
        key = (entry.day, entry.timeslot)
        if key in schedule['room']:
            schedule['room'][key].add(entry.classroom_id)
            schedule['faculty'][key].add(entry.faculty_id)
            schedule['section'][key].add(entry.section_id)

    entries_created, conflicts = _schedule_sections(
        dept_sections, days, timeslots, classrooms, schedule
    )
    db.session.commit()

    return {
        'success': True,
        'message': f'Partial regeneration done. {entries_created} entries created.',
        'entries_created': entries_created,
        'conflicts': conflicts,
    }


def validate_timetable():
    """
    Post-generation sanity check.  Returns {'valid': bool, 'violations': [...]}.
    Checks:
      1. No faculty teaching two sections at the same time
      2. No room used by two sections simultaneously
      3. No section exceeds MAX_CLASSES_PER_DAY
    """
    violations = []

    # 1. Faculty double-booking
    rows = (
        db.session.query(
            TimetableEntry.day, TimetableEntry.timeslot, TimetableEntry.faculty_id,
            func.count(TimetableEntry.id).label('cnt')
        )
        .group_by(TimetableEntry.day, TimetableEntry.timeslot, TimetableEntry.faculty_id)
        .having(func.count(TimetableEntry.id) > 1)
        .all()
    )
    for row in rows:
        violations.append({
            'type': 'faculty_double_booked',
            'day': row.day, 'timeslot': row.timeslot,
            'faculty_id': row.faculty_id, 'count': row.cnt,
        })

    # 2. Room double-booking
    rows = (
        db.session.query(
            TimetableEntry.day, TimetableEntry.timeslot, TimetableEntry.classroom_id,
            func.count(TimetableEntry.id).label('cnt')
        )
        .group_by(TimetableEntry.day, TimetableEntry.timeslot, TimetableEntry.classroom_id)
        .having(func.count(TimetableEntry.id) > 1)
        .all()
    )
    for row in rows:
        violations.append({
            'type': 'room_double_booked',
            'day': row.day, 'timeslot': row.timeslot,
            'classroom_id': row.classroom_id, 'count': row.cnt,
        })

    # 3. Section over-scheduled
    rows = (
        db.session.query(
            TimetableEntry.section_id, TimetableEntry.day,
            func.count(TimetableEntry.id).label('cnt')
        )
        .group_by(TimetableEntry.section_id, TimetableEntry.day)
        .having(func.count(TimetableEntry.id) > MAX_CLASSES_PER_DAY)
        .all()
    )
    for row in rows:
        violations.append({
            'type': 'section_over_scheduled',
            'section_id': row.section_id, 'day': row.day, 'count': row.cnt,
        })

    # 4. Cross-section faculty conflict (same faculty, same day+slot, different sections)
    rows = (
        db.session.query(
            TimetableEntry.day, TimetableEntry.timeslot, TimetableEntry.faculty_id,
            func.count(TimetableEntry.id).label('cnt')
        )
        .group_by(TimetableEntry.day, TimetableEntry.timeslot, TimetableEntry.faculty_id)
        .having(func.count(TimetableEntry.id) > 1)
        .all()
    )
    for row in rows:
        violations.append({
            'type': 'cross_section_faculty_conflict',
            'day': row.day, 'timeslot': row.timeslot,
            'faculty_id': row.faculty_id, 'count': row.cnt,
        })

    # 5. Cross-section room conflict (same room, same day+slot, different sections)
    rows = (
        db.session.query(
            TimetableEntry.day, TimetableEntry.timeslot, TimetableEntry.classroom_id,
            func.count(TimetableEntry.id).label('cnt')
        )
        .group_by(TimetableEntry.day, TimetableEntry.timeslot, TimetableEntry.classroom_id)
        .having(func.count(TimetableEntry.id) > 1)
        .all()
    )
    for row in rows:
        violations.append({
            'type': 'cross_section_room_conflict',
            'day': row.day, 'timeslot': row.timeslot,
            'classroom_id': row.classroom_id, 'count': row.cnt,
        })

    return {'valid': len(violations) == 0, 'violations': violations}


# ═══════════════════════════════════════════════════════════════
# INTERNAL HELPERS
# ═══════════════════════════════════════════════════════════════

def _fail(msg):
    return {'success': False, 'message': msg, 'entries_created': 0, 'conflicts': []}


def _empty_schedule(days, timeslots):
    """Create empty schedule tracking dicts."""
    room, faculty, section = {}, {}, {}
    for day in days:
        for ts in timeslots:
            key = (day, ts)
            room[key] = set()
            faculty[key] = set()
            section[key] = set()
    return {'room': room, 'faculty': faculty, 'section': section}


def _schedule_sections(sections, days, timeslots, classrooms, schedule):
    """Schedule a list of sections.  Returns (entries_created, conflicts)."""
    entries_created = 0
    conflicts = []

    for section in sections:
        dept = section.department
        # YEAR-WISE: Only courses from the section's own department are scheduled here.
        courses = Course.query.filter_by(department_id=dept.id).all()
        if not courses:
            continue

        # Sort: Hard > Medium > Easy, then credits descending
        difficulty_order = {'Hard': 0, 'Medium': 1, 'Easy': 2}
        courses_sorted = sorted(
            courses,
            key=lambda c: (difficulty_order.get(c.difficulty, 1), -c.credits)
        )

        # Per-section state
        state = _SectionState(days)

        # Track assignments as a stack for backtracking
        assignment_stack = []  # list of (entry_obj, course_id, day, ts, faculty_id, room_id)

        for course_idx, course in enumerate(courses_sorted):
            classes_needed = course.classes_per_week
            available_faculty = list(course.faculty_members)

            if not available_faculty:
                conflicts.append(_build_conflict(
                    course, dept, section, 0, classes_needed,
                    'no_faculty', 'No faculty assigned to teach this course'
                ))
                continue

            classes_assigned = 0

            for _ in range(classes_needed):
                if classes_assigned >= classes_needed:
                    break

                placed = _try_place_class(
                    section, course, days, timeslots, classrooms,
                    available_faculty, schedule, state
                )

                if placed:
                    day, ts, fac_id, room_id = placed
                    entry_obj = _commit_placement(section, course, day, ts, fac_id, room_id, schedule, state)
                    assignment_stack.append((entry_obj, course.id, day, ts, fac_id, room_id))
                    classes_assigned += 1
                    entries_created += 1
                else:
                    # ── Backtracking ──────────────────────────────
                    bt_success = _backtrack_and_place(
                        section, course, courses_sorted[:course_idx],
                        days, timeslots, classrooms, schedule, state,
                        assignment_stack
                    )
                    if bt_success:
                        classes_assigned += 1
                        entries_created += 1  # net +1 (undo then redo keeps count)
                    # else: will be reported as conflict below

            if classes_assigned < classes_needed:
                # Build detailed reason
                reason_counts = _diagnose_failure(
                    section, course, days, timeslots, classrooms,
                    available_faculty, schedule, state
                )
                conflicts.append(_build_conflict(
                    course, dept, section, classes_assigned, classes_needed,
                    'partially_scheduled', reason_counts=reason_counts
                ))

    return entries_created, conflicts


# ═══════════════════════════════════════════════════════════════
# PLACEMENT LOGIC
# ═══════════════════════════════════════════════════════════════

class _SectionState:
    """Per-section mutable state for the scheduling loop."""
    def __init__(self, days):
        self.day_load = {d: 0 for d in days}
        self.course_on_day = {d: set() for d in days}
        self.course_days = {}  # course_id -> set of days assigned
        self.slot_indices = {d: set() for d in days}  # ts indices used per day

    def copy(self):
        s = _SectionState.__new__(_SectionState)
        s.day_load = dict(self.day_load)
        s.course_on_day = {d: set(v) for d, v in self.course_on_day.items()}
        s.course_days = {k: set(v) for k, v in self.course_days.items()}
        s.slot_indices = {d: set(v) for d, v in self.slot_indices.items()}
        return s


def _try_place_class(section, course, days, timeslots, classrooms,
                     available_faculty, schedule, state):
    """
    Try to find the best (day, slot, faculty, room) for one class of a course.
    Returns (day, ts, faculty_id, room_id) or None.
    """
    # Candidate days: least-loaded first, skip if course already on that day or day full
    candidate_days = sorted(
        [d for d in days
         if course.id not in state.course_on_day[d]
         and state.day_load[d] < MAX_CLASSES_PER_DAY],
        key=lambda d: state.day_load[d]
    )

    best = _find_best_slot(section, course, candidate_days, timeslots,
                           classrooms, available_faculty, schedule, state)
    if best:
        return best

    # Fallback: relax one-course-per-day rule
    fallback_days = sorted(
        [d for d in days if state.day_load[d] < MAX_CLASSES_PER_DAY],
        key=lambda d: state.day_load[d]
    )
    return _find_best_slot(section, course, fallback_days, timeslots,
                           classrooms, available_faculty, schedule, state)


def _find_best_slot(section, course, candidate_days, timeslots,
                    classrooms, available_faculty, schedule, state):
    """Score all (day, slot) combos across candidate_days and return the best."""
    scored = []

    for chosen_day in candidate_days:
        used_indices = state.slot_indices[chosen_day]

        for ts_idx, ts in enumerate(timeslots):
            if ts == LUNCH_SLOT:
                continue
            key = (chosen_day, ts)

            # Hard constraint: section slot must be free
            if section.id in schedule['section'][key]:
                continue

            score = _compute_slot_score(
                course, ts_idx, timeslots, used_indices, state, chosen_day
            )

            # Find available faculty
            fac = _find_faculty(available_faculty, schedule, key, chosen_day, ts)
            if fac is None:
                continue

            # Find available room
            room = _find_room(classrooms, schedule['room'], key,
                              section.student_count, course.course_type)
            if room is None:
                continue

            scored.append((score, chosen_day, ts, ts_idx, fac.id, room.id))

    if not scored:
        return None

    scored.sort(key=lambda x: x[0])
    best = scored[0]
    return (best[1], best[2], best[4], best[5])  # day, ts, fac_id, room_id


def _compute_slot_score(course, ts_idx, timeslots, used_indices, state, day):
    """
    Soft constraint scoring.  Lower = better.
    """
    score = 0
    n_slots = len(timeslots)

    # ── Difficulty-based slot preference ──
    if course.difficulty == 'Hard':
        score += ts_idx                       # prefer early
    elif course.difficulty == 'Easy':
        score += n_slots - ts_idx             # prefer late
    else:
        score += abs(ts_idx - n_slots // 2)   # prefer middle

    # ── Penalty: Easy course in prime morning slots (idx 0 or 1) ──
    if course.difficulty == 'Easy' and ts_idx < 2:
        score += 2

    # ── Penalty: discourage filling the very first slot unless necessary ──
    if ts_idx == 0 and state.day_load[day] == 0:
        score += 3

    # ── Penalty: adjacent to an existing class (encourages gaps) ──
    if (ts_idx - 1) in used_indices:
        score += 2
    if (ts_idx + 1) in used_indices:
        score += 2

    # ── Bonus: far from existing classes ──
    if used_indices:
        min_dist = min(abs(ts_idx - ui) for ui in used_indices)
        if min_dist >= 2:
            score -= 1

    # ── Penalty: same course on back-to-back days ──
    prev_days = state.course_days.get(course.id, set())
    if prev_days:
        day_names = list(state.day_load.keys())
        try:
            day_idx = day_names.index(day)
            for pd in prev_days:
                try:
                    pd_idx = day_names.index(pd)
                    if abs(day_idx - pd_idx) == 1:
                        score += 3
                except ValueError:
                    pass
        except ValueError:
            pass

    return score


def _find_faculty(available_faculty, schedule, key, day, ts):
    """Return the first available faculty for a slot, or None."""
    for fac in available_faculty:
        if fac.id in schedule['faculty'][key]:
            continue
        avail = fac.get_available_slots()
        if avail:
            day_slots = avail.get(day, [])
            if day_slots and ts not in day_slots:
                continue
        return fac
    return None


def _find_room(classrooms, room_schedule, key, student_count, course_type):
    """Find a suitable free classroom.  Prefers matching room type."""
    # First pass: match room type
    for room in classrooms:
        if room.id in room_schedule[key]:
            continue
        if room.capacity >= student_count:
            if course_type == 'Lab' and room.room_type == 'Lab':
                return room
            elif course_type == 'Theory' and room.room_type == 'Theory':
                return room

    # Second pass: any room with capacity
    for room in classrooms:
        if room.id not in room_schedule[key] and room.capacity >= student_count:
            return room

    return None


def _commit_placement(section, course, day, ts, faculty_id, room_id,
                      schedule, state):
    """Write a placement to the DB and update all trackers."""
    entry = TimetableEntry(
        section_id=section.id, day=day, timeslot=ts,
        course_id=course.id, faculty_id=faculty_id, classroom_id=room_id
    )
    db.session.add(entry)
    db.session.flush() # Ensure object is persisted for potential deletion during backtracking

    key = (day, ts)
    schedule['room'][key].add(room_id)
    schedule['faculty'][key].add(faculty_id)
    schedule['section'][key].add(section.id)

    state.day_load[day] += 1
    state.course_on_day[day].add(course.id)
    state.course_days.setdefault(course.id, set()).add(day)

    timeslots_keys = [k for k in schedule['section'] if k[0] == day]
    all_ts = sorted(set(k[1] for k in timeslots_keys))
    if ts in all_ts:
        state.slot_indices[day].add(all_ts.index(ts))
    
    return entry


def _undo_placement(section, entry_obj, course_id, day, ts, faculty_id, room_id,
                    schedule, state):
    """Reverse a placement from trackers and delete from DB."""
    key = (day, ts)
    schedule['room'][key].discard(room_id)
    schedule['faculty'][key].discard(faculty_id)
    schedule['section'][key].discard(section.id)

    state.day_load[day] = max(0, state.day_load[day] - 1)
    state.course_on_day[day].discard(course_id)
    if course_id in state.course_days:
        state.course_days[course_id].discard(day)

    if entry_obj:
        if entry_obj in db.session:
            db.session.delete(entry_obj)
            db.session.flush()
        else:
            # Fallback for re-placed items that might have been lost
            entry = TimetableEntry.query.filter_by(
                section_id=section.id, day=day, timeslot=ts,
                course_id=course_id, faculty_id=faculty_id, classroom_id=room_id
            ).first()
            if entry:
                db.session.delete(entry)
                db.session.flush()


# ═══════════════════════════════════════════════════════════════
# BACKTRACKING
# ═══════════════════════════════════════════════════════════════

def _backtrack_and_place(section, stuck_course, earlier_courses,
                         days, timeslots, classrooms, schedule, state,
                         assignment_stack):
    """
    When `stuck_course` can't be placed, try undoing up to MAX_BACKTRACK_DEPTH
    recent assignments for this section and re-arranging them.
    Returns True if successful.
    """
    # Only backtrack over this section's assignments
    section_assignments = [
        (i, a) for i, a in enumerate(assignment_stack)
    ]

    depth = min(MAX_BACKTRACK_DEPTH, len(section_assignments))
    if depth == 0:
        return False

    for n_undo in range(1, depth + 1):
        # Take the last n_undo assignments
        to_undo = section_assignments[-n_undo:]
        undo_indices = [i for i, _ in to_undo]
        undo_data = [a for _, a in to_undo]

        # Save state snapshot
        saved_stack = list(assignment_stack)
        saved_state = state.copy()
        saved_schedule_room = {k: set(v) for k, v in schedule['room'].items()}
        saved_schedule_faculty = {k: set(v) for k, v in schedule['faculty'].items()}
        saved_schedule_section = {k: set(v) for k, v in schedule['section'].items()}

        # Undo them
        for entry_obj, course_id, d, t, fid, rid in reversed(undo_data):
            _undo_placement(section, entry_obj, course_id, d, t, fid, rid, schedule, state)

        # Remove from stack
        for idx in sorted(undo_indices, reverse=True):
            assignment_stack.pop(idx)

        # Try to place stuck_course first
        stuck_faculty = list(stuck_course.faculty_members)
        placed_stuck = _try_place_class(
            section, stuck_course, days, timeslots, classrooms,
            stuck_faculty, schedule, state
        )

        if placed_stuck:
            d, t, fid, rid = placed_stuck
            entry_obj = _commit_placement(section, stuck_course, d, t, fid, rid, schedule, state)
            assignment_stack.append((entry_obj, stuck_course.id, d, t, fid, rid))

            # Now re-place the undone courses
            all_replaced = True
            for _, course_id, _, _, _, _ in undo_data:
                course_obj = Course.query.get(course_id)
                if not course_obj:
                    all_replaced = False
                    break
                facs = list(course_obj.faculty_members)
                re_placed = _try_place_class(
                    section, course_obj, days, timeslots, classrooms,
                    facs, schedule, state
                )
                if re_placed:
                    rd, rt, rfid, rrid = re_placed
                    rentry = _commit_placement(section, course_obj, rd, rt, rfid, rrid, schedule, state)
                    assignment_stack.append((rentry, course_id, rd, rt, rfid, rrid))
                else:
                    all_replaced = False
                    break

            if all_replaced:
                return True

            # Failed attempt — undo everything added during this attempt
            while len(assignment_stack) > len(saved_stack) - n_undo:
                eo2, cid2, d2, t2, fid2, rid2 = assignment_stack.pop()
                _undo_placement(section, eo2, cid2, d2, t2, fid2, rid2, schedule, state)

        # Hard restore state and schedule from snapshots
        state.day_load = dict(saved_state.day_load)
        state.course_on_day = {d: set(v) for d, v in saved_state.course_on_day.items()}
        state.course_days = {k: set(v) for k, v in saved_state.course_days.items()}
        state.slot_indices = {d: set(v) for d, v in saved_state.slot_indices.items()}

        schedule['room'] = saved_schedule_room
        schedule['faculty'] = saved_schedule_faculty
        schedule['section'] = saved_schedule_section

        # Restore assignment stack and re-add entries to session
        assignment_stack.clear()
        assignment_stack.extend(saved_stack)
        for entry_obj, course_id, d, t, fid, rid in undo_data:
            new_entry = TimetableEntry(
                section_id=section.id, course_id=course_id,
                day=d, timeslot=t, faculty_id=fid, classroom_id=rid
            )
            db.session.add(new_entry)
            # Update the entry object in the stack to the new one
            for i, item in enumerate(assignment_stack):
                if item[1:] == (course_id, d, t, fid, rid):
                    assignment_stack[i] = (new_entry, course_id, d, t, fid, rid)
                    break
        db.session.flush()

    return False


# ═══════════════════════════════════════════════════════════════
# CONFLICT DIAGNOSIS
# ═══════════════════════════════════════════════════════════════

def _diagnose_failure(section, course, days, timeslots, classrooms,
                      available_faculty, schedule, state):
    """
    When a course can't be placed, iterate every (day, slot) and record
    which hard constraint blocked it.  Returns dict of reason -> count.
    """
    reasons = {'no_room': 0, 'faculty_busy': 0, 'section_full': 0}

    for day in days:
        for ts_idx, ts in enumerate(timeslots):
            if ts == LUNCH_SLOT:
                continue
            key = (day, ts)

            # Section slot taken or day full
            if section.id in schedule['section'][key]:
                reasons['section_full'] += 1
                continue
            if state.day_load[day] >= MAX_CLASSES_PER_DAY:
                reasons['section_full'] += 1
                continue

            # Faculty check
            fac = _find_faculty(available_faculty, schedule, key, day, ts)
            if fac is None:
                reasons['faculty_busy'] += 1
                continue

            # Room check
            room = _find_room(classrooms, schedule['room'], key,
                              section.student_count, course.course_type)
            if room is None:
                reasons['no_room'] += 1
                continue

    return reasons


def _build_conflict(course, dept, section, assigned, needed,
                    reason_type, reason_text=None, reason_counts=None):
    """Build a structured conflict dict."""
    conflict = {
        'course_code': course.code,
        'course_name': course.name,
        'section': f'{dept.code}-{section.name}',
        'assigned': assigned,
        'needed': needed,
        'reason': reason_type,
    }
    if reason_text:
        conflict['detail'] = reason_text
    if reason_counts:
        conflict['reasons'] = reason_counts
    return conflict
