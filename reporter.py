from typing import List
from base_checker import CheckResult


class ConsoleReporter:
    def __init__(self):
        self.colors = {
            'PASS': '\033[92m',    # Green
            'FAIL': '\033[91m',    # Red  
            'WARN': '\033[93m',    # Yellow
            'ERROR': '\033[91m',   # Red
            'RESET': '\033[0m'     # Reset
        }
    
    def print_results(self, results: List[CheckResult]):
        """Print formatted results to console"""
        print("\n" + "="*60)
        print("ALPHA ANALYZER RESULTS")
        print("="*60)
        
        # Summary stats
        total = len(results)
        passed = sum(1 for r in results if r.status == 'PASS')
        failed = sum(1 for r in results if r.status == 'FAIL')
        warned = sum(1 for r in results if r.status == 'WARN')
        errors = sum(1 for r in results if r.status == 'ERROR')
        
        print(f"Total Checks: {total}")
        print(f"Passed: {self._colorize('PASS', str(passed))}")
        print(f"Failed: {self._colorize('FAIL', str(failed))}")
        print(f"Warnings: {self._colorize('WARN', str(warned))}")
        print(f"Errors: {self._colorize('ERROR', str(errors))}")
        print()
        
        # Individual results
        for result in results:
            status_colored = self._colorize(result.status, result.status)
            print(f"[{status_colored}] {result.checker_name}")
            print(f"    {result.message}")
            
            if result.details:
                print(f"    Details:")
                for line in result.details.split('\n'):
                    if line.strip():  # Skip empty lines
                        print(f"      {line}")
            print()
        
        # Final summary
        if failed > 0 or errors > 0:
            print(self._colorize('FAIL', f"❌ ANALYSIS FAILED - {failed + errors} critical issues"))
        elif warned > 0:
            print(self._colorize('WARN', f"⚠️  ANALYSIS COMPLETED WITH WARNINGS - {warned} warnings"))
        else:
            print(self._colorize('PASS', "✅ ALL CHECKS PASSED"))
        print()
    
    def _colorize(self, status: str, text: str) -> str:
        """Add color to text based on status"""
        color = self.colors.get(status, '')
        reset = self.colors['RESET']
        return f"{color}{text}{reset}"