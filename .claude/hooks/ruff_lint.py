#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "ruff",
# ]
# ///

import json
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime

def main():
    try:
        # Read JSON input from stdin
        input_data = json.load(sys.stdin)
        
        # Check if this is a relevant tool
        tool_name = input_data.get('tool_name', '')
        if tool_name not in ['Write', 'Edit', 'MultiEdit']:
            sys.exit(0)
        
        # Extract file path(s)
        tool_input = input_data.get('tool_input', {})
        file_paths = []
        
        if tool_name in ['Write', 'Edit']:
            file_path = tool_input.get('file_path')
            if file_path:
                file_paths.append(file_path)
        elif tool_name == 'MultiEdit':
            file_path = tool_input.get('file_path')
            if file_path:
                file_paths.append(file_path)
        
        # Filter for Python files
        python_files = [fp for fp in file_paths if fp.endswith('.py')]
        
        if not python_files:
            sys.exit(0)
        
        # Ensure log directory exists
        log_dir = Path.cwd() / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / 'ruff_lint.json'
        
        # Read existing log data or initialize empty list
        if log_path.exists():
            with open(log_path, 'r') as f:
                try:
                    log_data = json.load(f)
                except (json.JSONDecodeError, ValueError):
                    log_data = []
        else:
            log_data = []
        
        # Run ruff on each Python file
        results = []
        for file_path in python_files:
            if os.path.exists(file_path):
                # Run ruff check with auto-fix
                try:
                    # First, try to fix what can be fixed automatically
                    fix_result = subprocess.run(
                        ['ruff', 'check', '--fix', file_path],
                        capture_output=True,
                        text=True
                    )
                    
                    # Then run check to see what issues remain
                    check_result = subprocess.run(
                        ['ruff', 'check', file_path],
                        capture_output=True,
                        text=True
                    )
                    
                    result = {
                        'file': file_path,
                        'timestamp': datetime.now().isoformat(),
                        'fixed': fix_result.returncode == 0,
                        'has_issues': check_result.returncode != 0,
                        'output': check_result.stdout + check_result.stderr,
                        'tool_name': tool_name,
                        'session_id': input_data.get('session_id', 'unknown')
                    }
                    
                    results.append(result)
                    
                except Exception as e:
                    result = {
                        'file': file_path,
                        'timestamp': datetime.now().isoformat(),
                        'error': str(e),
                        'tool_name': tool_name,
                        'session_id': input_data.get('session_id', 'unknown')
                    }
                    results.append(result)
        
        # Log results
        if results:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'results': results
            }
            log_data.append(log_entry)
            
            # Keep only last 100 entries to prevent log from growing too large
            if len(log_data) > 100:
                log_data = log_data[-100:]
            
            with open(log_path, 'w') as f:
                json.dump(log_data, f, indent=2)
            
            # If there are linting issues, we could optionally return a notification
            # For now, we'll just exit cleanly to avoid disrupting the workflow
            issues_found = any(r.get('has_issues', False) for r in results)
            if issues_found:
                # You could return a JSON response here to notify Claude Code
                # For example:
                # response = {
                #     "type": "notification",
                #     "message": f"Ruff found issues in {sum(1 for r in results if r.get('has_issues'))}"
                # }
                # print(json.dumps(response))
                pass
        
        sys.exit(0)
        
    except json.JSONDecodeError:
        # Handle JSON decode errors gracefully
        sys.exit(0)
    except Exception:
        # Exit cleanly on any other error
        sys.exit(0)

if __name__ == '__main__':
    main()