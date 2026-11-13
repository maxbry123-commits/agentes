from bs4 import BeautifulSoup
from typing import List, Dict, Any
from urllib.parse import urljoin

class WebAnalyzer:
    def __init__(self, executor):
        self.executor = executor

    def inspect_page(self, url: str) -> Dict[str, Any]:
        """
        Fetch a page using curl on the remote Kali box and extract interesting elements.
        """
        try:
            # Use curl to fetch the page from the Kali box
            # -s: Silent, -k: Insecure (skip SSL cert), -L: Follow redirects
            cmd = f"curl -s -k -L {url}"
            stdout, stderr, code = self.executor.run_command(cmd)
            
            if code != 0:
                return {"error": f"Curl failed: {stderr}"}
            
            html_content = stdout
            soup = BeautifulSoup(html_content, 'html.parser')
            
            title = soup.title.string if soup.title else "No Title"
            forms = []
            for form in soup.find_all('form'):
                action = form.get('action') 
                method = form.get('method', 'get').upper()
                inputs = []
                for inp in form.find_all('input'):
                    input_name = inp.get('name')
                    # Only record inputs with names (interaction points)
                    if input_name:
                        inputs.append({
                            "name": input_name,
                            "type": inp.get('type', 'text')
                        })
                forms.append({
                    "action": urljoin(url, action) if action else url,
                    "method": method,
                    "inputs": inputs
                })
            
            return {
                "status_code": 200, # Assuming success if curl 0
                "title": title,
                "forms_found": len(forms),
                "forms_details": forms,
                "raw_length": len(html_content)
            }
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def format_for_llm(data: Dict) -> str:
        """Compact summary for the Brain."""
        if "error" in data:
            return f"Web Check Failed: {data['error']}"
            
        summary = f"Page: {data.get('title')}\n"
        if data.get('forms_found', 0) > 0:
            summary += f"Found {data['forms_found']} Forms:\n"
            for form in data['forms_details']:
                summary += f" - Form ({form['method']}) to {form['action']}: Inputs={[i['name'] for i in form['inputs']]}\n"
        else:
            summary += "No interactive forms found.\n"
        return summary
