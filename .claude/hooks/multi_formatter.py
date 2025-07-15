#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "black",
#     "isort",
# ]
# ///

import json
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime
import shutil

def check_tool_installed(tool_name):
    """Check if a formatting tool is installed."""
    return shutil.which(tool_name) is not None

def format_file(file_path, file_type):
    """Format a file based on its type."""
    results = []
    
    if file_type == "python":
        # First run isort for import sorting
        if check_tool_installed("isort"):
            try:
                subprocess.run(['isort', file_path], check=True, capture_output=True, text=True)
                results.append({"tool": "isort", "status": "success"})
            except subprocess.CalledProcessError as e:
                results.append({"tool": "isort", "status": "failed", "error": e.stderr})
        
        # Then run black for formatting
        if check_tool_installed("black"):
            try:
                subprocess.run(['black', '--quiet', file_path], check=True, capture_output=True, text=True)
                results.append({"tool": "black", "status": "success"})
            except subprocess.CalledProcessError as e:
                results.append({"tool": "black", "status": "failed", "error": e.stderr})
    
    elif file_type == "go":
        # Run gofmt
        if check_tool_installed("gofmt"):
            try:
                subprocess.run(['gofmt', '-w', file_path], check=True, capture_output=True, text=True)
                results.append({"tool": "gofmt", "status": "success"})
            except subprocess.CalledProcessError as e:
                results.append({"tool": "gofmt", "status": "failed", "error": e.stderr})
        else:
            results.append({"tool": "gofmt", "status": "not_installed"})
    
    elif file_type == "rust":
        # Run rustfmt
        if check_tool_installed("rustfmt"):
            try:
                subprocess.run(['rustfmt', '--edition', '2021', file_path], check=True, capture_output=True, text=True)
                results.append({"tool": "rustfmt", "status": "success"})
            except subprocess.CalledProcessError as e:
                results.append({"tool": "rustfmt", "status": "failed", "error": e.stderr})
        else:
            results.append({"tool": "rustfmt", "status": "not_installed"})
    
    elif file_type in ["javascript", "typescript", "json"]:
        # Try prettier first
        if check_tool_installed("prettier"):
            try:
                subprocess.run(['prettier', '--write', file_path], check=True, capture_output=True, text=True)
                results.append({"tool": "prettier", "status": "success"})
            except subprocess.CalledProcessError as e:
                results.append({"tool": "prettier", "status": "failed", "error": e.stderr})
        # If prettier not available and it's JavaScript/TypeScript, try deno fmt
        elif file_type != "json" and check_tool_installed("deno"):
            try:
                subprocess.run(['deno', 'fmt', file_path], check=True, capture_output=True, text=True)
                results.append({"tool": "deno", "status": "success"})
            except subprocess.CalledProcessError as e:
                results.append({"tool": "deno", "status": "failed", "error": e.stderr})
        else:
            results.append({"tool": "prettier/deno", "status": "not_installed"})
    
    return results

def get_file_type(file_path):
    """Determine the file type based on extension."""
    ext = Path(file_path).suffix.lower()
    
    if ext == '.py':
        return 'python'
    elif ext == '.go':
        return 'go'
    elif ext == '.rs':
        return 'rust'
    elif ext in ['.js', '.jsx', '.mjs']:
        return 'javascript'
    elif ext in ['.ts', '.tsx']:
        return 'typescript'
    elif ext == '.json':
        return 'json'
    else:
        return None

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
        
        # Filter for supported file types
        files_to_format = []
        for fp in file_paths:
            file_type = get_file_type(fp)
            if file_type and os.path.exists(fp):
                files_to_format.append((fp, file_type))
        
        if not files_to_format:
            sys.exit(0)
        
        # Ensure log directory exists
        log_dir = Path.cwd() / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / 'multi_formatter.json'
        
        # Read existing log data or initialize empty list
        if log_path.exists():
            with open(log_path, 'r') as f:
                try:
                    log_data = json.load(f)
                except (json.JSONDecodeError, ValueError):
                    log_data = []
        else:
            log_data = []
        
        # Format each file
        all_results = []
        for file_path, file_type in files_to_format:
            format_results = format_file(file_path, file_type)
            
            result = {
                'file': file_path,
                'file_type': file_type,
                'timestamp': datetime.now().isoformat(),
                'results': format_results,
                'tool_name': tool_name,
                'session_id': input_data.get('session_id', 'unknown')
            }
            
            all_results.append(result)
        
        # Log results
        if all_results:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'formatted_files': all_results
            }
            log_data.append(log_entry)
            
            # Keep only last 100 entries to prevent log from growing too large
            if len(log_data) > 100:
                log_data = log_data[-100:]
            
            with open(log_path, 'w') as f:
                json.dump(log_data, f, indent=2)
        
        sys.exit(0)
        
    except json.JSONDecodeError:
        # Handle JSON decode errors gracefully
        sys.exit(0)
    except Exception:
        # Exit cleanly on any other error
        sys.exit(0)

if __name__ == '__main__':
    main()