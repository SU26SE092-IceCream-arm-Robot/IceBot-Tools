import os
import time
import json
import re
import hashlib
from datetime import datetime
from pathlib import Path

# Design thresholds
DB_SLOW_QUERY_THRESHOLD_MS = 500
ROBOT_THREAD_BLOCK_THRESHOLD_MS = 1000
TOOL_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = TOOL_DIR.parent.parent
DEFAULT_MOCK_LOG_ROOT = TOOL_DIR.parent / "data" / "log-analyzer" / "mock_logs"
DEFAULT_RAG_LOG_ROOT = TOOL_DIR.parent / "logs" / "rag"
DEFAULT_VIOLATIONS_LOG_PATH = TOOL_DIR.parent / "logs" / "log-analyzer" / "violations.log"

class LogAnalyzer:
    def __init__(
        self,
        webapi_dir,
        robot_dir,
        rag_dir,
        violations_log_path,
        *,
        write_violations=True,
        verbose=True,
    ):
        self.webapi_dir = os.path.abspath(webapi_dir)
        self.robot_dir = os.path.abspath(robot_dir)
        self.rag_dir = os.path.abspath(rag_dir)
        self.write_violations = write_violations
        self.verbose = verbose
        
        # State for files being tailed
        self.webapi_file = None
        self.webapi_fp = None
        self.webapi_last_size = 0
        
        self.robot_file = None
        self.robot_fp = None
        self.robot_last_size = 0
        
        self.rag_file = None
        self.rag_fp = None
        self.rag_last_size = 0
        
        # Ingest timing tracking for slow RAG embedding warning
        self.last_rag_staged_time = None
        self.last_rag_staged_file = None
        
        # Aggregated Errors: key -> dict
        # key is hash of exception type + message + top frames
        self.errors = {}
        
        # Design Violations list
        self.violations = []
        
        # File to write violation alarms
        self.violations_log_path = os.path.abspath(violations_log_path)
        if self.write_violations:
            os.makedirs(os.path.dirname(self.violations_log_path), exist_ok=True)

    def log_violation(self, source, category, message, timestamp=None):
        ts = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        alarm_text = f"[{ts}] [{source.upper()}] [VIOLATION] [{category}] {message}"
        self.violations.append({
            "timestamp": ts,
            "source": source,
            "category": category,
            "message": message
        })
        # Keep violations list capped at 50 for display
        if len(self.violations) > 50:
            self.violations.pop(0)
            
        if self.write_violations:
            with open(self.violations_log_path, "a", encoding="utf-8") as f:
                f.write(alarm_text + "\n")

    def get_latest_file(self, directory, pattern):
        if not os.path.exists(directory):
            return None
        files = [os.path.join(directory, f) for f in os.listdir(directory) if re.match(pattern, f)]
        if not files:
            return None
        # Return the newest modified file
        return max(files, key=os.path.getmtime)

    def update_tail_file(self, directory, pattern, current_file, current_fp, *, seek_to_end=True):
        latest_file = self.get_latest_file(directory, pattern)
        if not latest_file:
            return None, None
            
        if latest_file != current_file:
            if current_fp:
                current_fp.close()
            if self.verbose:
                print(f"[*] Switching log file in {os.path.basename(directory)} to: {os.path.basename(latest_file)}")
            fp = open(latest_file, "r", encoding="utf-8", errors="ignore")
            if seek_to_end:
                # Seek to end of file on initial open to behave like tail -f.
                fp.seek(0, os.SEEK_END)
            return latest_file, fp
            
        # Check if file was truncated/recreated
        if current_fp:
            try:
                curr_pos = current_fp.tell()
                file_size = os.path.getsize(current_file)
                if file_size < curr_pos:
                    if self.verbose:
                        print(f"[*] Log file truncated: {os.path.basename(current_file)}")
                    current_fp.seek(0)
            except Exception:
                pass
                
        return current_file, current_fp

    def process_webapi_line(self, line):
        line = line.strip()
        if not line:
            return
            
        try:
            log_data = json.loads(line)
        except json.JSONDecodeError:
            # Fallback for plain text WebAPI logs if any
            self.process_text_line("webapi", line)
            return

        level = log_data.get("@l", "Information")
        message_template = log_data.get("@mt", "")
        timestamp = log_data.get("@t", datetime.now().isoformat())
        
        # Check Design Violation: Slow Database Queries
        if "Microsoft.EntityFrameworkCore.Database.Command" in log_data.get("SourceContext", ""):
            elapsed = log_data.get("Elapsed")
            if elapsed is not None:
                try:
                    elapsed_val = int(elapsed)
                    if elapsed_val > DB_SLOW_QUERY_THRESHOLD_MS:
                        sql = log_data.get("Sql", "Unknown SQL")
                        # Truncate sql for clean message
                        sql_short = sql[:60].replace("\n", " ").strip() + ("..." if len(sql) > 60 else "")
                        self.log_violation(
                            source="WebAPI",
                            category="SLOW_DATABASE_QUERY",
                            message=f"Query took {elapsed_val}ms (Threshold: {DB_SLOW_QUERY_THRESHOLD_MS}ms). SQL: {sql_short}",
                            timestamp=timestamp
                        )
                except ValueError:
                    pass

        # Check Errors
        if level in ["Error", "Fatal"]:
            exception_str = log_data.get("@x")
            message = log_data.get("@m") or message_template
            
            if exception_str:
                self.aggregate_error("WebAPI", exception_str, message, timestamp)
            else:
                self.aggregate_error("WebAPI", "Exception: unknown", message, timestamp)

    def process_text_line(self, source, line):
        normalized = line.strip()
        if not normalized:
            return

        if "ERROR" in normalized.upper() or "EXCEPTION" in normalized.upper():
            self.aggregate_error(source, normalized, normalized, datetime.now().isoformat())

    def process_robot_lines(self):
        if not self.robot_fp:
            return
            
        lines = self.robot_fp.readlines()
        if not lines:
            return
            
        # We need a buffer to accumulate stack traces
        buffer_lines = []
        in_exception = False
        exception_msg = ""
        exception_time = ""
        
        for line in lines:
            # Check if this line starts a new log entry
            # Format: [2026-06-11 22:52:00] [LEVEL] ...
            match = re.match(r"^\[(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})\]\s\[([A-Z]+)\]\s(.*)$", line)
            
            if match:
                # If we were gathering an exception, flush it first
                if in_exception and buffer_lines:
                    stack_trace = "".join(buffer_lines)
                    self.aggregate_error("Robot", stack_trace, exception_msg, exception_time)
                    buffer_lines = []
                    in_exception = False
                    
                timestamp_str, level, msg = match.groups()
                
                # Check Design Violation: Robot Controller Thread Blocked
                if "thread blocked for" in msg.lower():
                    # Extract blocking duration
                    ms_match = re.search(r"blocked for\s+(\d+)ms", msg, re.IGNORECASE)
                    if ms_match:
                        duration = int(ms_match.group(1))
                        if duration > ROBOT_THREAD_BLOCK_THRESHOLD_MS:
                            self.log_violation(
                                source="Robot",
                                category="THREAD_BLOCKED",
                                message=f"Robot control thread blocked for {duration}ms (Threshold: {ROBOT_THREAD_BLOCK_THRESHOLD_MS}ms)",
                                timestamp=timestamp_str
                            )
                            
                # Check for warnings/errors
                if level == "ERROR" or level == "FATAL":
                    in_exception = True
                    exception_msg = msg
                    exception_time = timestamp_str
                    buffer_lines.append(line)
            else:
                # Continuation of stack trace
                if in_exception:
                    buffer_lines.append(line)
                    
        # Flush any remaining exception
        if in_exception and buffer_lines:
            stack_trace = "".join(buffer_lines)
            self.aggregate_error("Robot", stack_trace, exception_msg, exception_time)

    def process_rag_lines(self):
        if not self.rag_fp:
            return
            
        lines = self.rag_fp.readlines()
        if not lines:
            return
            
        buffer_lines = []
        in_exception = False
        exception_msg = ""
        exception_time = ""
        
        for line in lines:
            # Format: 2026-06-11 21:11:29 INFO icebot.rag.ingest - Message
            match = re.match(r"^(\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}:\d{2})\s([A-Z]+)\s([a-zA-Z0-9\._\-]+)\s-\s(.*)$", line)
            
            if match:
                if in_exception and buffer_lines:
                    stack_trace = "".join(buffer_lines)
                    self.aggregate_error("RAG", stack_trace, exception_msg, exception_time)
                    buffer_lines = []
                    in_exception = False
                    
                timestamp_str, level, logger, msg = match.groups()
                
                # Check Design Violation: Qdrant Server Connection Fallback
                if "falling back to local storage" in msg.lower() or "failed to connect to qdrant" in msg.lower():
                    self.log_violation(
                        source="RAG",
                        category="QDRANT_FALLBACK",
                        message="Failed to connect to Qdrant server, falling back to local file database",
                        timestamp=timestamp_str
                    )
                
                # Check Design Violation: Missing Dependency
                if "hybrid retrieval is enabled but fastembed is not installed" in msg.lower():
                    self.log_violation(
                        source="RAG",
                        category="RAG_DEPENDENCY_MISSING",
                        message="Hybrid retrieval enabled but fastembed is not installed",
                        timestamp=timestamp_str
                    )
                
                # Check Design Violation: Slow Embedding (>5.0s per chunk)
                if "staged changed file" in msg.lower():
                    staged_match = re.search(r"staged changed file:\s*([^\s]+)\s+chunks=(\d+)", msg, re.IGNORECASE)
                    if staged_match:
                        file_name, chunks_str = staged_match.groups()
                        try:
                            chunks = int(chunks_str)
                            time_now = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                            if self.last_rag_staged_time and self.last_rag_staged_file:
                                duration = (time_now - self.last_rag_staged_time).total_seconds()
                                if chunks > 0:
                                    sec_per_chunk = duration / chunks
                                    if sec_per_chunk > 5.0:
                                        self.log_violation(
                                            source="RAG",
                                            category="SLOW_EMBEDDING",
                                            message=f"Embedding took {sec_per_chunk:.2f}s/chunk for {chunks} chunks in {self.last_rag_staged_file} (Slow CPU processing)",
                                            timestamp=timestamp_str
                                        )
                            self.last_rag_staged_time = time_now
                            self.last_rag_staged_file = file_name
                        except Exception:
                            pass
                            
                # Check for errors
                if level in ["ERROR", "CRITICAL", "FATAL"]:
                    in_exception = True
                    exception_msg = msg
                    exception_time = timestamp_str
                    buffer_lines.append(line)
            else:
                if in_exception:
                    buffer_lines.append(line)
                    
        if in_exception and buffer_lines:
            stack_trace = "".join(buffer_lines)
            self.aggregate_error("RAG", stack_trace, exception_msg, exception_time)

    def aggregate_error(self, source, stack_trace, message, timestamp):
        # Extract exception type
        # E.g. System.NullReferenceException or ValueError
        exc_type_match = re.match(r"^([a-zA-Z0-9\.]+Exception|[a-zA-Z0-9\.]+Error)", stack_trace.strip())
        exc_type = exc_type_match.group(1) if exc_type_match else "Exception"
        
        # Clean message to avoid variations in IDs
        clean_msg = re.sub(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}", "{GUID}", message)
        clean_msg = re.sub(r"\d+", "{NUMBER}", clean_msg)
        
        # Get top 2 stack frames for signature
        frames = []
        for line in stack_trace.split("\n"):
            if "at " in line or "File " in line:
                frames.append(line.strip())
            if len(frames) >= 2:
                break
        frames_str = "".join(frames)
        
        # Create hash signature
        sig_input = f"{source}:{exc_type}:{clean_msg}:{frames_str}"
        sig_hash = hashlib.md5(sig_input.encode("utf-8")).hexdigest()
        
        if sig_hash in self.errors:
            self.errors[sig_hash]["count"] += 1
            self.errors[sig_hash]["last_seen"] = timestamp
        else:
            self.errors[sig_hash] = {
                "source": source,
                "type": exc_type,
                "message": message[:80] + ("..." if len(message) > 80 else ""),
                "stack_sample": "\n".join(stack_trace.split("\n")[:4]),
                "count": 1,
                "first_seen": timestamp,
                "last_seen": timestamp
            }

    def print_dashboard(self):
        # Clear screen
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print("=" * 100)
        print("                     ICEBOT REAL-TIME LOG ANALYZER & ERROR AGGREGATOR")
        print("=" * 100)
        print(f"Monitoring directories:")
        print(f"  - WebAPI Logs:  {self.webapi_dir}")
        print(f"  - Robot Logs:   {self.robot_dir}")
        print(f"  - RAG Logs:     {self.rag_dir}")
        print(f"  - Alarm Log:    {self.violations_log_path}")
        print("-" * 100)
        
        # 1. Active Design Violations
        print("\n--- ACTIVE DESIGN VIOLATIONS (Last 10 Alarms) ---")
        if not self.violations:
            print("  [OK] No design violations detected.")
        else:
            # Show last 10
            for v in self.violations[-10:]:
                color_start = "\033[91m" if v["category"] == "THREAD_BLOCKED" else "\033[93m"
                color_end = "\033[0m"
                print(f"  {color_start}[{v['timestamp']}] [{v['source']}] [{v['category']}] {v['message']}{color_end}")
                
        # 2. Aggregated Error Summary Table
        print("\n--- AGGREGATED ERROR REPORT ---")
        if not self.errors:
            print("  [OK] No errors/exceptions captured in logs.")
        else:
            # Sort errors by count descending
            sorted_errors = sorted(self.errors.values(), key=lambda x: x["count"], reverse=True)
            print(f"  {'Source':<8} | {'Count':<5} | {'Exception Type':<30} | {'Message Summary'}")
            print(f"  {'-'*8} | {'-'*5} | {'-'*30} | {'-'*45}")
            for err in sorted_errors[:15]:
                print(f"  {err['source']:<8} | {err['count']:<5} | {err['type'][:30]:<30} | {err['message']}")
                
        print("\n" + "=" * 100)
        print("Press Ctrl+C to exit. Analyzing logs in real-time...")

    def build_summary(self, *, max_items=10):
        sorted_errors = sorted(self.errors.values(), key=lambda x: x["count"], reverse=True)
        violations = self.violations[-max_items:]
        errors = sorted_errors[:max_items]

        issue_count = len(self.violations) + len(self.errors)
        if issue_count == 0:
            return {
                "passed": True,
                "summary": "Log analyzer found no violations or error groups.",
            }

        return {
            "passed": False,
            "summary": (
                f"Log analyzer found {len(self.violations)} violation(s) "
                f"and {len(self.errors)} error group(s)."
            ),
            "violation_count": len(self.violations),
            "error_group_count": len(self.errors),
            "truncated": len(self.violations) > len(violations) or len(self.errors) > len(errors),
            "violations": [
                {
                    "timestamp": item["timestamp"],
                    "source": item["source"],
                    "category": item["category"],
                    "message": item["message"],
                }
                for item in violations
            ],
            "errors": [
                {
                    "source": item["source"],
                    "count": item["count"],
                    "type": item["type"],
                    "message": item["message"],
                    "first_seen": item["first_seen"],
                    "last_seen": item["last_seen"],
                }
                for item in errors
            ],
        }

    def print_once_summary(self, *, max_items=10):
        summary = self.build_summary(max_items=max_items)
        print("LOG ANALYZER ONE-SHOT SUMMARY")
        print(f"Violations: {summary.get('violation_count', 0)}")
        print(f"Error groups: {summary.get('error_group_count', 0)}")

        if summary.get("violations"):
            print("\nViolations:")
            for violation in summary["violations"]:
                print(
                    f"- [{violation['source']}] [{violation['category']}] {violation['message']}"
                )

        if summary.get("errors"):
            print("\nErrors:")
            for error in summary["errors"]:
                print(
                    f"- [{error['source']}] count={error['count']} type={error['type']} message={error['message']}"
                )

    def analyze_once(self, *, include_rag=True, max_items=10):
        self.webapi_file, self.webapi_fp = self.update_tail_file(
            self.webapi_dir,
            r"^log-\d{8}\.txt$",
            self.webapi_file,
            self.webapi_fp,
            seek_to_end=False,
        )
        self.robot_file, self.robot_fp = self.update_tail_file(
            self.robot_dir,
            r"^robot-.*\.log$",
            self.robot_file,
            self.robot_fp,
            seek_to_end=False,
        )
        if include_rag:
            self.rag_file, self.rag_fp = self.update_tail_file(
                self.rag_dir,
                r"^ingest\.log$",
                self.rag_file,
                self.rag_fp,
                seek_to_end=False,
            )

        if self.webapi_fp:
            for line in self.webapi_fp.readlines():
                self.process_webapi_line(line)

        if self.robot_fp:
            self.process_robot_lines()

        if include_rag and self.rag_fp:
            self.process_rag_lines()

        summary = self.build_summary(max_items=max_items)
        self.close_files()
        return summary

    def run_once(self, *, include_rag=True, max_items=10):
        self.analyze_once(include_rag=include_rag, max_items=max_items)
        self.print_once_summary(max_items=max_items)

    def close_files(self):
        if self.webapi_fp:
            self.webapi_fp.close()
            self.webapi_fp = None
        if self.robot_fp:
            self.robot_fp.close()
            self.robot_fp = None
        if self.rag_fp:
            self.rag_fp.close()
            self.rag_fp = None

    def run(self):
        print("[*] Log Analyzer started. Waiting for files...")
        
        try:
            while True:
                # 1. Update tailed files
                # WebAPI logs look like: log-YYYYMMDD.txt
                self.webapi_file, self.webapi_fp = self.update_tail_file(
                    self.webapi_dir, r"^log-\d{8}\.txt$", self.webapi_file, self.webapi_fp
                )
                # Robot logs look like: robot-YYYYMMDD.log or robot.log
                self.robot_file, self.robot_fp = self.update_tail_file(
                    self.robot_dir, r"^robot-.*\.log$", self.robot_file, self.robot_fp
                )
                # RAG logs look like: ingest.log
                self.rag_file, self.rag_fp = self.update_tail_file(
                    self.rag_dir, r"^ingest\.log$", self.rag_file, self.rag_fp
                )
                
                # 2. Read new lines from WebAPI (JSON format)
                if self.webapi_fp:
                    webapi_lines = self.webapi_fp.readlines()
                    for line in webapi_lines:
                        self.process_webapi_line(line)
                        
                # 3. Read new lines from Robot (Text format with multiline stack traces)
                if self.robot_fp:
                    self.process_robot_lines()
                    
                # 4. Read new lines from RAG (Text format with multiline stack traces)
                if self.rag_fp:
                    self.process_rag_lines()
                    
                # 5. Print Dashboard
                self.print_dashboard()
                
                time.sleep(2.0)
                
        except KeyboardInterrupt:
            print("\n[*] Exiting Log Analyzer.")
            self.close_files()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Real-time Log Analyzer for IceBot")
    parser.add_argument("--webapi-path", default=str(DEFAULT_MOCK_LOG_ROOT / "webapi"), help="Path to WebAPI logs folder")
    parser.add_argument("--robot-path", default=str(DEFAULT_MOCK_LOG_ROOT / "robot"), help="Path to robot logs folder")
    parser.add_argument("--rag-path", default=str(DEFAULT_RAG_LOG_ROOT), help="Path to RAG logs folder")
    parser.add_argument(
        "--violations-log-path",
        default=str(DEFAULT_VIOLATIONS_LOG_PATH),
        help="Path to write detected design violations",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Process current log files once from the beginning, print a summary, and exit.",
    )
    parser.add_argument(
        "--skip-rag",
        action="store_true",
        help="Do not include RAG ingest logs in one-shot analysis.",
    )
    parser.add_argument(
        "--max-items",
        type=int,
        default=10,
        help="Maximum violations/errors to print in one-shot mode.",
    )
    
    args = parser.parse_args()
    
    # Resolve relative paths from the current working directory.
    webapi_path = os.path.abspath(args.webapi_path)
    robot_path = os.path.abspath(args.robot_path)
    rag_path = os.path.abspath(args.rag_path)
    violations_log_path = os.path.abspath(args.violations_log_path)
    
    # Ensure directories exist
    os.makedirs(webapi_path, exist_ok=True)
    os.makedirs(robot_path, exist_ok=True)
    os.makedirs(rag_path, exist_ok=True)
    
    analyzer = LogAnalyzer(webapi_path, robot_path, rag_path, violations_log_path)
    if args.once:
        analyzer.run_once(include_rag=not args.skip_rag, max_items=args.max_items)
    else:
        analyzer.run()
