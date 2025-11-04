"""
Comprehensive Flask Routing Analysis Tool
Detects all routing inconsistencies and generates fixes
"""
import os
import re
from collections import defaultdict
import json

class RoutingAnalyzer:
    def __init__(self):
        self.registered_endpoints = {}  # endpoint -> (file, line, route_pattern)
        self.url_for_calls = []  # [(file, line, endpoint, context)]
        self.issues = defaultdict(list)
        self.fixes = []
        
    def extract_routes_from_app(self, filepath='app.py'):
        """Extract all registered routes from app.py"""
        print(f"[1/5] Analyzing route definitions in {filepath}...")
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for i, line in enumerate(lines, 1):
                # Match @app.route(..., endpoint='...')
                route_match = re.search(r"@app\.route\(['\"]([^'\"]+)['\"].*?endpoint=['\"]([^'\"]+)['\"]", line)
                if route_match:
                    route_pattern, endpoint = route_match.groups()
                    self.registered_endpoints[endpoint] = (filepath, i, route_pattern)
                    
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
    
    def extract_url_for_calls(self, directory='templates'):
        """Extract all url_for() calls from templates"""
        print(f"[2/5] Scanning url_for() calls in {directory}...")
        count = 0
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.html'):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                        
                        for i, line in enumerate(lines, 1):
                            # Match url_for('endpoint') or url_for("endpoint")
                            matches = re.finditer(r"url_for\(['\"]([^'\"]+)['\"]", line)
                            for match in matches:
                                endpoint = match.group(1)
                                context = line.strip()[:100]
                                self.url_for_calls.append((filepath, i, endpoint, context))
                                count += 1
                    except Exception as e:
                        print(f"  Error reading {filepath}: {e}")
        
        print(f"  Found {count} url_for() calls")
    
    def extract_url_for_from_python(self, filepath='app.py'):
        """Extract url_for() calls from Python files"""
        print(f"[3/5] Scanning url_for() calls in {filepath}...")
        count = 0
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for i, line in enumerate(lines, 1):
                # Match url_for('endpoint') or url_for("endpoint") in Python
                matches = re.finditer(r"url_for\(['\"]([^'\"]+)['\"]", line)
                for match in matches:
                    endpoint = match.group(1)
                    context = line.strip()[:100]
                    self.url_for_calls.append((filepath, i, endpoint, context))
                    count += 1
        except Exception as e:
            print(f"  Error reading {filepath}: {e}")
        
        print(f"  Found {count} url_for() calls in Python")
    
    def analyze_inconsistencies(self):
        """Detect all routing inconsistencies"""
        print("[4/5] Analyzing inconsistencies...")
        
        # Group url_for calls by endpoint
        endpoint_usage = defaultdict(list)
        for call in self.url_for_calls:
            filepath, line, endpoint, context = call
            endpoint_usage[endpoint].append((filepath, line, context))
        
        # Check each url_for call
        for endpoint, usages in endpoint_usage.items():
            if endpoint not in self.registered_endpoints:
                # Endpoint not registered - try to find close matches
                self.issues['missing_endpoint'].append({
                    'endpoint': endpoint,
                    'usages': usages,
                    'suggestions': self._find_similar_endpoints(endpoint)
                })
        
        # Check for potential naming issues
        self._check_naming_patterns()
        
        print(f"  Found {len(self.issues['missing_endpoint'])} missing endpoints")
    
    def _find_similar_endpoints(self, target):
        """Find similar endpoint names using fuzzy matching"""
        suggestions = []
        target_lower = target.lower()
        target_parts = target.split('.')
        
        for registered in self.registered_endpoints.keys():
            # Exact match without prefix
            if target_parts[-1] == registered.split('.')[-1]:
                suggestions.append(registered)
            # Contains target as substring
            elif target_lower in registered.lower() or registered.lower() in target_lower:
                suggestions.append(registered)
        
        return suggestions[:5]  # Return top 5
    
    def _check_naming_patterns(self):
        """Check for common naming pattern issues"""
        # Check for endpoints without blueprint prefix
        for call_file, call_line, endpoint, context in self.url_for_calls:
            if '.' not in endpoint and endpoint not in ['logout', 'login', 'signup', 'main_home']:
                # Might be missing blueprint prefix
                potential_prefixes = ['project', 'admin', 'hr', 'finance', 'procurement', 'quarry', 'files', 'dashboard']
                for prefix in potential_prefixes:
                    full_endpoint = f"{prefix}.{endpoint}"
                    if full_endpoint in self.registered_endpoints:
                        self.issues['missing_prefix'].append({
                            'file': call_file,
                            'line': call_line,
                            'current': endpoint,
                            'suggested': full_endpoint,
                            'context': context
                        })
                        break
    
    def generate_fixes(self):
        """Generate automated fixes"""
        print("[5/5] Generating fixes...")
        
        # Generate fixes for missing endpoints
        for issue in self.issues['missing_endpoint']:
            endpoint = issue['endpoint']
            suggestions = issue['suggestions']
            usages = issue['usages']
            
            if suggestions:
                # Use the first suggestion
                fix_endpoint = suggestions[0]
                for filepath, line, context in usages:
                    self.fixes.append({
                        'type': 'replace_endpoint',
                        'file': filepath,
                        'line': line,
                        'old': f"url_for('{endpoint}')",
                        'new': f"url_for('{fix_endpoint}')",
                        'context': context
                    })
        
        # Generate fixes for missing prefixes
        for issue in self.issues['missing_prefix']:
            self.fixes.append({
                'type': 'add_prefix',
                'file': issue['file'],
                'line': issue['line'],
                'old': f"url_for('{issue['current']}')",
                'new': f"url_for('{issue['suggested']}')",
                'context': issue['context']
            })
        
        print(f"  Generated {len(self.fixes)} fixes")
    
    def print_report(self):
        """Print comprehensive report"""
        print("\n" + "="*80)
        print("ROUTING ANALYSIS REPORT")
        print("="*80)
        
        print(f"\n✓ Total registered endpoints: {len(self.registered_endpoints)}")
        print(f"✓ Total url_for() calls: {len(self.url_for_calls)}")
        
        if self.issues['missing_endpoint']:
            print(f"\n⚠ MISSING ENDPOINTS ({len(self.issues['missing_endpoint'])})")
            print("-" * 80)
            for issue in self.issues['missing_endpoint'][:10]:  # Show first 10
                endpoint = issue['endpoint']
                suggestions = issue['suggestions']
                usages = issue['usages']
                
                print(f"\n  Endpoint: '{endpoint}' (used in {len(usages)} places)")
                if suggestions:
                    print(f"  Suggestions: {', '.join(suggestions)}")
                
                # Show first 3 usages
                for filepath, line, context in usages[:3]:
                    print(f"    {filepath}:{line}")
                    print(f"      {context}")
        
        if self.issues['missing_prefix']:
            print(f"\n⚠ MISSING PREFIXES ({len(self.issues['missing_prefix'])})")
            print("-" * 80)
            for issue in self.issues['missing_prefix'][:10]:
                print(f"\n  {issue['file']}:{issue['line']}")
                print(f"    Current:   {issue['current']}")
                print(f"    Suggested: {issue['suggested']}")
        
        if self.fixes:
            print(f"\n🔧 AUTOMATED FIXES ({len(self.fixes)})")
            print("-" * 80)
            print("  Run apply_fixes() to automatically fix all issues")
        
        print("\n" + "="*80)
    
    def export_report(self, filename='routing_analysis.json'):
        """Export detailed report to JSON"""
        report = {
            'registered_endpoints': {
                ep: {'file': f, 'line': l, 'route': r}
                for ep, (f, l, r) in self.registered_endpoints.items()
            },
            'issues': dict(self.issues),
            'fixes': self.fixes,
            'summary': {
                'total_endpoints': len(self.registered_endpoints),
                'total_url_for_calls': len(self.url_for_calls),
                'missing_endpoints': len(self.issues['missing_endpoint']),
                'missing_prefixes': len(self.issues['missing_prefix']),
                'total_fixes': len(self.fixes)
            }
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Detailed report exported to: {filename}")
    
    def apply_fixes(self):
        """Apply all automated fixes"""
        print("\n🔧 Applying fixes...")
        
        # Group fixes by file
        fixes_by_file = defaultdict(list)
        for fix in self.fixes:
            fixes_by_file[fix['file']].append(fix)
        
        fixed_count = 0
        for filepath, file_fixes in fixes_by_file.items():
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                # Apply each fix
                for fix in file_fixes:
                    old = fix['old']
                    new = fix['new']
                    if old in content:
                        content = content.replace(old, new)
                        fixed_count += 1
                
                # Write back if changes were made
                if content != original_content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"  ✓ Fixed {len(file_fixes)} issues in {filepath}")
            
            except Exception as e:
                print(f"  ✗ Error fixing {filepath}: {e}")
        
        print(f"\n✓ Applied {fixed_count} fixes across {len(fixes_by_file)} files")


def main():
    analyzer = RoutingAnalyzer()
    
    # Step 1: Extract all registered routes
    analyzer.extract_routes_from_app('app.py')
    
    # Step 2: Extract all url_for calls from templates
    analyzer.extract_url_for_calls('templates')
    
    # Step 3: Extract url_for calls from Python files
    analyzer.extract_url_for_from_python('app.py')
    
    # Step 4: Analyze inconsistencies
    analyzer.analyze_inconsistencies()
    
    # Step 5: Generate fixes
    analyzer.generate_fixes()
    
    # Print report
    analyzer.print_report()
    
    # Export detailed report
    analyzer.export_report()
    
    # Ask user if they want to apply fixes
    print("\n" + "="*80)
    response = input("Apply all automated fixes? (yes/no): ").strip().lower()
    if response == 'yes':
        analyzer.apply_fixes()
        print("\n✓ All fixes applied! Please restart your Flask app to test.")
    else:
        print("\n✗ Fixes not applied. Review routing_analysis.json for details.")


if __name__ == '__main__':
    main()
