#!/usr/bin/env python3
"""
Real-time log monitoring for GrowFolio CMS
Monitors server logs and displays errors/warnings
"""
import subprocess
import sys
import re
from datetime import datetime
import signal

# Colors for terminal output
class Colors:
    RED = '\033[91m'
    YELLOW = '\033[93m'
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_colored(message, color):
    """Print colored message"""
    print(f"{color}{message}{Colors.RESET}")

def print_header():
    """Print monitoring header"""
    print_colored("\n" + "="*80, Colors.CYAN)
    print_colored("🔍 GrowFolio CMS - Real-time Log Monitor", Colors.BOLD + Colors.CYAN)
    print_colored("="*80, Colors.CYAN)
    print_colored(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", Colors.WHITE)
    print_colored("="*80 + "\n", Colors.CYAN)

def categorize_log_line(line):
    """Categorize log line and return color"""
    line_upper = line.upper()

    if 'ERROR' in line_upper or 'EXCEPTION' in line_upper or 'TRACEBACK' in line_upper:
        return Colors.RED, '❌ ERROR'
    elif 'WARNING' in line_upper or 'WARN' in line_upper:
        return Colors.YELLOW, '⚠️  WARN'
    elif '200 OK' in line or '201 Created' in line:
        return Colors.GREEN, '✅ SUCCESS'
    elif '404' in line or '422' in line or '500' in line or '403' in line:
        return Colors.RED, '❌ ERROR'
    elif 'INFO' in line_upper or 'POST' in line or 'GET' in line or 'PUT' in line or 'DELETE' in line:
        return Colors.BLUE, 'ℹ️  INFO'
    else:
        return Colors.WHITE, '📝 LOG'

def extract_important_info(line):
    """Extract important information from log line"""
    # Extract HTTP method and endpoint
    http_match = re.search(r'(GET|POST|PUT|DELETE|PATCH)\s+([^\s]+)', line)
    if http_match:
        method, endpoint = http_match.groups()
        return f"{method} {endpoint}"

    # Extract error messages
    error_match = re.search(r'(Error|Exception):\s+(.+)', line)
    if error_match:
        return error_match.group(2)

    return None

def monitor_logs():
    """Monitor server logs in real-time"""
    print_header()

    # Statistics
    stats = {
        'requests': 0,
        'errors': 0,
        'warnings': 0,
        'success': 0
    }

    try:
        # Find uvicorn process
        ps_output = subprocess.check_output(['ps', 'aux'], universal_newlines=True)
        uvicorn_lines = [line for line in ps_output.split('\n') if 'uvicorn main:app' in line and 'grep' not in line]

        if not uvicorn_lines:
            print_colored("❌ No uvicorn server found running!", Colors.RED)
            print_colored("Please start the server with: python -m uvicorn main:app --reload", Colors.YELLOW)
            sys.exit(1)

        pid = uvicorn_lines[0].split()[1]
        print_colored(f"✅ Found uvicorn server (PID: {pid})", Colors.GREEN)
        print_colored("Monitoring logs... Press Ctrl+C to stop\n", Colors.WHITE)

        # Tail the logs
        process = subprocess.Popen(
            ['tail', '-f', '/dev/null'],  # Placeholder, we'll read from stderr
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )

        # Monitor using ps output
        log_cmd = f"tail -f /proc/{pid}/fd/1 /proc/{pid}/fd/2 2>/dev/null || tail -f /dev/null"
        process = subprocess.Popen(
            log_cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )

        print_colored("📊 Live Statistics:", Colors.MAGENTA)
        print_colored("-" * 80 + "\n", Colors.WHITE)

        for line in process.stdout:
            line = line.strip()
            if not line:
                continue

            # Categorize and color
            color, category = categorize_log_line(line)

            # Update stats
            if '200 OK' in line or '201 Created' in line:
                stats['success'] += 1
                stats['requests'] += 1
            elif 'ERROR' in line.upper() or '404' in line or '500' in line or '422' in line or '403' in line:
                stats['errors'] += 1
                stats['requests'] += 1
            elif 'WARNING' in line.upper():
                stats['warnings'] += 1
            elif any(method in line for method in ['GET', 'POST', 'PUT', 'DELETE']):
                stats['requests'] += 1

            # Extract important info
            important = extract_important_info(line)

            # Print log line
            timestamp = datetime.now().strftime('%H:%M:%S')
            if important:
                print_colored(f"[{timestamp}] {category} | {important}", color)
            else:
                # Only print errors/warnings fully
                if color in [Colors.RED, Colors.YELLOW]:
                    print_colored(f"[{timestamp}] {category} | {line[:100]}", color)

            # Print stats every 10 requests
            if stats['requests'] > 0 and stats['requests'] % 10 == 0:
                print_colored(f"\n📊 Stats: {stats['requests']} requests | {stats['success']} success | {stats['errors']} errors | {stats['warnings']} warnings\n", Colors.MAGENTA)

    except KeyboardInterrupt:
        print_colored("\n\n" + "="*80, Colors.CYAN)
        print_colored("📊 Final Statistics:", Colors.BOLD + Colors.CYAN)
        print_colored("="*80, Colors.CYAN)
        print_colored(f"Total Requests: {stats['requests']}", Colors.WHITE)
        print_colored(f"Successful: {stats['success']}", Colors.GREEN)
        print_colored(f"Errors: {stats['errors']}", Colors.RED)
        print_colored(f"Warnings: {stats['warnings']}", Colors.YELLOW)
        print_colored("="*80 + "\n", Colors.CYAN)
        print_colored("✅ Log monitoring stopped", Colors.GREEN)
    except Exception as e:
        print_colored(f"\n❌ Error monitoring logs: {e}", Colors.RED)
        sys.exit(1)

if __name__ == "__main__":
    monitor_logs()
