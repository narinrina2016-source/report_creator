import os
import re

frontend_src = r"d:\Project System\ARMS\frontend\src"

def replace_localhost():
    for root, dirs, files in os.walk(frontend_src):
        for file in files:
            if file.endswith(".tsx") or file.endswith(".ts"):
                filepath = os.path.join(root, file)
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Replace exact string fetches
                # E.g. fetch("http://localhost:8000/api/v1/...") -> fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/...`)
                new_content = re.sub(r'"http://localhost:8000(/api/v1/[^"]*)"', r'`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}\1`', content)
                
                # Replace template literal fetches
                # E.g. fetch(`http://localhost:8000/api/v1/...`) -> fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/...`)
                new_content = new_content.replace("`http://localhost:8000/api/v1/", "`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/")
                
                if new_content != content:
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    print(f"Updated {filepath}")

if __name__ == "__main__":
    replace_localhost()
    print("Done")
