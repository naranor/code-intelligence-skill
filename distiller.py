import re
import sys
import subprocess
import os

class OutputDistiller:
    @staticmethod
    def clean_ansi(text: str) -> str:
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)

    @staticmethod
    def distill(tool_name: str, exit_code: int, stdout: str, stderr: str) -> str:
        combined = (stdout + "\n" + stderr).strip()
        clean_text = OutputDistiller.clean_ansi(combined)
        
        if exit_code == 0:
            if "pytest" in tool_name.lower():
                match = re.search(r'==.* passed.* in .*==', clean_text)
                summary = match.group(0).strip('= ') if match else "All tests passed."
                return f"SUCCESS (distilled): {summary}"
            return f"SUCCESS (distilled): {tool_name} completed."
        else:
            lines = clean_text.splitlines()
            error_content = []
            if "pytest" in tool_name.lower():
                capture = False
                for line in lines:
                    if any(m in line for m in ["FAILURES", "SHORT TEST SUMMARY", "ERRORS", "ERROR collecting"]):
                        capture = True
                    if capture:
                        error_content.append(line)
                if not error_content: error_content = lines[-100:] # More context for fallback
            elif "ruff" in tool_name.lower():
                # Capture all linting errors
                error_content = [l for l in lines if re.search(r'.*\.py:\d+:\d+: [A-Z]\d+', l)]
                if not error_content: error_content = lines
            else:
                error_content = lines # No truncation for generic errors
            
            # ABSOLUTELY NO TRUNCATION in v5.7
            return f"FAILURE in {tool_name}:\n" + "\n".join(error_content)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python distiller_wrapper.py <tool_name> <command...>")
        sys.exit(1)
    tool_name = sys.argv[1]
    command = sys.argv[2:]
    try:
        proc = subprocess.run(command, capture_output=True, text=True, check=False)
        print(OutputDistiller.distill(tool_name, proc.returncode, proc.stdout, proc.stderr))
        sys.exit(proc.returncode)
    except Exception as e:
        print(f"Distiller execution failed: {e}")
        sys.exit(1)
