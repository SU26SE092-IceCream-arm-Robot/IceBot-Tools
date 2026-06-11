import os
import time
import json
import random
import argparse
from datetime import datetime, timezone
from pathlib import Path

TOOL_DIR = Path(__file__).resolve().parent
TOOLS_ROOT = TOOL_DIR.parent
DEFAULT_MOCK_LOG_ROOT = TOOLS_ROOT / "data" / "log-analyzer" / "mock_logs"

# Sample stack traces
NULL_REF_STACK = """System.NullReferenceException: Object reference not set to an instance of an object.
   at IceBot.Application.Services.InventoryService.GetStockAsync(Guid itemId) in /workspace/IceBot-Backend/src/Application/Services/InventoryService.cs:line 42
   at IceBot.WebAPI.GraphQL.Inventory.InventoryQueries.GetInventoryStock(InventoryService service, Guid itemId) in /workspace/IceBot-Backend/src/WebAPI/GraphQL/Inventory/InventoryQueries.cs:line 18
   at Microsoft.AspNetCore.Mvc.Infrastructure.ActionMethodExecutor.TaskOfMethodExecutor.Execute(ActionContext actionContext, ObjectMethodExecutor executor, Object controller, Object[] arguments)"""

DB_CONN_STACK = """Npgsql.NpgsqlException (0x80004005): Failed to connect to localhost:5432
   at Npgsql.Internal.NpgsqlConnector.Connect(NpgsqlTimeout timeout)
   at Npgsql.NpgsqlConnection.Open()
   at IceBot.Infrastructure.Persistence.IceBotDbContext.SaveChangesAsync(CancellationToken cancellationToken) in /workspace/IceBot-Backend/src/Infrastructure/Persistence/IceBotDbContext.cs:line 85"""

ROBOT_FAULT_STACK = """ValueError: Joint 3 angle 185.2 exceeds physical limit of 180.0 degrees.
  File "robot_runtime/controllers/arm.py", line 124, in set_joint_angle
    raise ValueError(f"Joint {joint} angle {angle} exceeds physical limit...")
  File "robot_runtime/worker.py", line 54, in process_command
    self.controller.set_joint_angle(cmd.joint, cmd.angle)
  File "robot_runtime/main.py", line 32, in run_loop
    self.worker.process_command(cmd)"""

def generate_webapi_log(webapi_file_path):
    timestamp = datetime.now(timezone.utc).isoformat()
    log_type = random.choices(["info", "slow_query", "error"], weights=[0.7, 0.2, 0.1])[0]

    if log_type == "info":
        log_entry = {
            "@t": timestamp,
            "@mt": "Request finished in {ElapsedMilliseconds}ms with status code {StatusCode}",
            "@l": "Information",
            "ElapsedMilliseconds": random.uniform(5.0, 150.0),
            "StatusCode": 200,
            "SourceContext": "Microsoft.AspNetCore.Hosting.Diagnostics"
        }
    elif log_type == "slow_query":
        elapsed = random.choice([120, 580, 890, 1200]) # some are slow (>500ms)
        sql = random.choice([
            "SELECT * FROM \"InventoryItems\" WHERE \"TenantId\" = @p0",
            "UPDATE \"Orders\" SET \"Status\" = @p0, \"UpdatedAt\" = @p1 WHERE \"Id\" = @p2",
            "SELECT \"t\".\"Id\", \"t\".\"Name\" FROM \"Tenants\" AS \"t\""
        ])
        log_entry = {
            "@t": timestamp,
            "@mt": "Executed DbCommand ({Elapsed}ms) [Parameters=[@p0='...'], CommandType='Text', CommandTimeout='30']\n{Sql}",
            "@l": "Warning" if elapsed > 500 else "Information",
            "Elapsed": elapsed,
            "Sql": sql,
            "SourceContext": "Microsoft.EntityFrameworkCore.Database.Command"
        }
    else:  # Error
        err_type = random.choice(["null_ref", "db_conn"])
        if err_type == "null_ref":
            log_entry = {
                "@t": timestamp,
                "@mt": "An unhandled exception has occurred while executing the request.",
                "@l": "Error",
                "@x": NULL_REF_STACK,
                "SourceContext": "Microsoft.AspNetCore.Diagnostics.ExceptionHandlerMiddleware"
            }
        else:
            log_entry = {
                "@t": timestamp,
                "@mt": "Database connection failed for query execution.",
                "@l": "Fatal",
                "@x": DB_CONN_STACK,
                "SourceContext": "IceBot.Infrastructure.Persistence.IceBotDbContext"
            }
            
    with open(webapi_file_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry) + "\n")

def generate_robot_log(robot_file_path):
    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_type = random.choices(["info", "warning", "thread_block", "exception"], weights=[0.6, 0.2, 0.1, 0.1])[0]

    with open(robot_file_path, "a", encoding="utf-8") as f:
        if log_type == "info":
            f.write(f"[{timestamp_str}] [INFO] RobotController: Heartbeat sent successfully. Ping: 12ms\n")
        elif log_type == "warning":
            f.write(f"[{timestamp_str}] [WARNING] RobotController: Command queue delay detected. queue_len={random.randint(3, 8)}\n")
        elif log_type == "thread_block":
            block_ms = random.choice([200, 1500, 3200]) # > 1000ms is a violation
            f.write(f"[{timestamp_str}] [FATAL] RobotController: Robot controller thread blocked for {block_ms}ms\n")
        else: # Exception
            f.write(f"[{timestamp_str}] [ERROR] RobotController: Failed to execute arm movement.\n{ROBOT_FAULT_STACK}\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate mock WebAPI and robot logs for the IceBot log analyzer")
    parser.add_argument(
        "--output-root",
        default=str(DEFAULT_MOCK_LOG_ROOT),
        help="Root folder for generated mock logs",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=0,
        help="Number of log-generation iterations to run. Default 0 means run until Ctrl+C.",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=1.0,
        help="Seconds to sleep between iterations when --count is 0.",
    )
    args = parser.parse_args()

    output_root = Path(args.output_root).resolve()
    webapi_dir = output_root / "webapi"
    robot_dir = output_root / "robot"
    webapi_dir.mkdir(parents=True, exist_ok=True)
    robot_dir.mkdir(parents=True, exist_ok=True)

    today_str = datetime.now().strftime("%Y%m%d")
    webapi_file_path = webapi_dir / f"log-{today_str}.txt"
    robot_file_path = robot_dir / f"robot-{today_str}.log"

    print(f"Generating mock logs into:\n  WebAPI: {webapi_file_path}\n  Robot:  {robot_file_path}")
    if args.count <= 0:
        print("Press Ctrl+C to stop.")
    
    try:
        iterations = 0
        while args.count <= 0 or iterations < args.count:
            generate_webapi_log(webapi_file_path)
            if random.random() > 0.3:
                generate_robot_log(robot_file_path)
            iterations += 1
            if args.count <= 0:
                time.sleep(max(args.sleep, 0.0))
    except KeyboardInterrupt:
        print("\nMock log generation stopped.")
