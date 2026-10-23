# BIT 4624 Canvas Incident Synthetic Data Dictionary

## Overview
This package contains synthetic, university-observable datasets designed for a senior-level undergraduate cybersecurity analytics project.

The scenario is a university incident response team analyzing the May 2026 Canvas incident using evidence a university could realistically see, rather than vendor-internal forensic logs.

These files are synthetic and are intended for teaching and analysis only.

## Included files

### 1. `canvas_usage_summary.csv`
Aggregated Canvas activity summaries by date, hour block, and user role.

**Purpose**
- Compare historical usage patterns across a prior semester and the Spring 2026 incident window
- Evaluate whether the incident occurred during a high-dependency period
- Estimate likely operational impact based on timing

**Columns**
- `date`: Calendar date
- `term`: Academic term (`Fall_2025`, `Spring_2026`)
- `week_of_term`: Approximate week number in the academic term
- `day_of_week`: Day name
- `hour_block`: Four-hour activity block
- `user_role`: `student`, `faculty`, or `staff_admin`
- `login_count`: Count of successful platform access events
- `assignment_submissions`: Count of assignment submissions
- `quiz_exam_attempts`: Count of quiz or exam attempts
- `file_accesses`: Count of file or course-material access events
- `active_courses`: Count of courses with observed activity in that block/role
- `incident_window_flag`: Indicates the May 7-8, 2026 incident/degradation window

### 2. `helpdesk_tickets_summary.csv`
Aggregated help desk ticket counts by date, hour block, user role, and issue type.

**Purpose**
- Measure user-facing impact
- Compare support burden during the incident window versus normal periods
- Connect technical disruption to user and business impact

**Columns**
- `date`: Calendar date
- `term`: Academic term
- `hour_block`: Four-hour activity block
- `user_role`: `student`, `faculty`, or `staff_admin`
- `issue_category`: Ticket topic
- `severity_level`: `low`, `medium`, `high`, or `critical`
- `ticket_count`: Number of tickets in that category/block
- `incident_related_flag`: Indicates incident-related outage or follow-on phishing activity

### 3. `academic_calendar_flags.csv`
Daily academic-calendar indicators for interpreting service criticality.

**Purpose**
- Identify high-dependency academic periods
- Connect operational data to the university calendar
- Support impact analysis near final exams

**Columns**
- `date`: Calendar date
- `term`: Academic term
- `week_of_term`: Approximate week number in the academic term
- `day_of_week`: Day name
- `term_phase`: `pre_finals`, `reading_review`, `finals_week`, or `grading_closeout`
- `days_to_final_exam_start`: Days until finals begin (negative values mean finals already started)
- `major_deadline_count`: Synthetic count of major due dates or assessments
- `finals_period_flag`: Indicates the formal finals period
- `high_dependency_flag`: Indicates likely high operational dependence on Canvas

### 4. `service_status_checks.csv`
Synthetic university-side service monitoring checks.

**Purpose**
- Represent what institutional IT monitoring might observe
- Compare baseline availability with the May 2026 disruption
- Correlate service degradation with help desk and usage effects

**Columns**
- `timestamp`: Check timestamp
- `term`: Academic term
- `service_component`: Monitored LMS-related component
- `check_result`: `ok`, `degraded`, or `failed`
- `response_time_ms`: Measured response time
- `error_rate`: Synthetic error rate for the check period
- `incident_flag`: Indicates the modeled May 2026 incident window

## Usage notes
These data are intentionally limited to what a university might realistically observe:
- historical usage summaries
- help desk volume
- academic calendar context
- service availability checks

They do **not** include vendor-internal cloud logs, attacker telemetry, or provider forensic artifacts.

## Suggested student questions
- Did the incident occur during an unusually critical period for LMS availability?
- Which user groups were likely most affected?
- How do service checks and help desk tickets align during the incident window?
- How does the Spring 2026 incident window compare to a prior semester finals period?
- What recommendations should university leadership make to reduce future academic disruption?
