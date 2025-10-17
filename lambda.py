import json
import requests
from datetime import datetime
from io import StringIO
import traceback

CANVAS_BASE_URL = "[YOUR_SCHOOL.instructure.com]"
CANVAS_ACCESS_TOKEN = "[]" #Go to canvas -> calendar -> calendar feed to make a new token (only valid for 120 days)


def lambda_handler(event, context):
    """
    AWS Lambda entry point — fetches all courses and all assignments (with pagination).
    Logs everything it receives and does.
    """
    print("=== Lambda invoked ===")
    print("Full event payload:")
    print(json.dumps(event, indent=2))

    # Context logging (safe subset)
    if context:
        print("Context info:")
        print({
            "function_name": context.function_name,
            "function_version": context.function_version,
            "invoked_function_arn": context.invoked_function_arn,
            "memory_limit_in_mb": context.memory_limit_in_mb,
            "aws_request_id": context.aws_request_id,
            "log_group_name": context.log_group_name,
            "log_stream_name": context.log_stream_name
        })

    try:
        headers = {"Authorization": f"Bearer {CANVAS_ACCESS_TOKEN}"}

        # Get all active courses (with pagination)
        print("=== Fetching all active courses ===")
        courses_url = f"{CANVAS_BASE_URL}/api/v1/courses?enrollment_state=active&per_page=100"
        courses = get_all_pages(courses_url, headers)
        print(f"Total courses received: {len(courses)}")

        all_assignments = []

        # Get assignments from each course (with pagination)
        for course in courses:
            course_id = course.get("id")
            course_name = course.get("name", "Unnamed Course")
            print(f"\n=== Fetching assignments for course: {course_name} (ID: {course_id}) ===")

            if not course_id:
                print("Skipping course without ID.")
                continue

            assignments_url = f"{CANVAS_BASE_URL}/api/v1/courses/{course_id}/assignments?per_page=100"
            assignments = get_all_pages(assignments_url, headers)
            print(f"Total assignments received for '{course_name}': {len(assignments)}")

            # Log sample data (first assignment)
            if assignments:
                print("Sample assignment (truncated):")
                print(json.dumps(assignments[0], indent=2)[:500])

            #  Filter and store assignments
            for a in assignments:
                if a.get("due_at") or "assignment" in (a.get("UID", "") or "") or "quiz" in (a.get("UID", "") or ""):
                    all_assignments.append({
                        "name": a.get("name"),
                        "due_at": a.get("due_at"),
                        "html_url": a.get("html_url"),
                        "course_name": course_name
                    })

        print(f"\n=== Total assignments collected across all courses: {len(all_assignments)} ===")

        # Generate ICS calendar content
        ics_data = generate_ics(all_assignments)
        print("ICS generation completed. Sample output (first 500 chars):")
        print(ics_data[:500])

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "text/calendar",
                "Content-Disposition": "inline; filename=assignments.ics"
            },
            "body": ics_data
        }

    except Exception as e:
        print("=== ERROR ===")
        traceback.print_exc()
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }


def get_all_pages(url, headers):
    """
    Fetch all pages of a paginated Canvas API endpoint.
    """
    all_results = []
    next_url = url
    page = 1

    while next_url:
        print(f"Requesting page {page}: {next_url}")
        response = requests.get(next_url, headers=headers)
        print(f"Response status: {response.status_code}")

        if response.status_code != 200:
            print(f"Error response: {response.text[:500]}")
            break

        data = response.json()
        print(f"Received {len(data)} items on page {page}")
        all_results.extend(data)

        # Parse the Link header to find the next page URL
        link_header = response.headers.get("Link", "")
        next_url = None
        if 'rel="next"' in link_header:
            parts = link_header.split(",")
            for part in parts:
                if 'rel="next"' in part:
                    next_url = part[part.find("<") + 1: part.find(">")]
                    break
        page += 1

    print(f"Total items fetched: {len(all_results)}")
    return all_results


def generate_ics(assignments):
    """
    Convert assignment list to ICS calendar format.
    """
    print("Generating ICS data...")
    output = StringIO()
    output.write("BEGIN:VCALENDAR\n")
    output.write("VERSION:2.0\n")
    output.write("PRODID:-//Canvas Assignment Feed//EN\n")

    for a in assignments:
        try:
            if not a.get("due_at"):
                continue
            due = datetime.fromisoformat(a["due_at"].replace("Z", "+00:00"))
            uid = f"{hash(a['html_url'])}@canvas"
            output.write("BEGIN:VEVENT\n")
            output.write(f"UID:{uid}\n")
            output.write(f"DTSTAMP:{due.strftime('%Y%m%dT%H%M%SZ')}\n")
            output.write(f"DTSTART:{due.strftime('%Y%m%dT%H%M%SZ')}\n")
            output.write(f"SUMMARY:{a['name']}\n")
            output.write(f"DESCRIPTION:{a['course_name']}\n")
            output.write(f"URL:{a['html_url']}\n")
            output.write("END:VEVENT\n")
        except Exception as e:
            print(f"Error writing ICS event for {a.get('name', 'Unknown')} ({a.get('course_name', 'Unknown Course')}): {e}")

    output.write("END:VCALENDAR\n")
    return output.getvalue()
