
import re
with open('/Users/a.ganeshkumarreddy12/Downloads/pppp 2/templates/student_dashboard.html', 'r') as f:
    content = f.read()

scripts = re.findall(r'<script>(.*?)</script>', content, re.DOTALL)
with open('/Users/a.ganeshkumarreddy12/Downloads/pppp 2/scratch/check_syntax.js', 'w') as f:
    for s in scripts:
        f.write(s)
        f.write("\n\n")
