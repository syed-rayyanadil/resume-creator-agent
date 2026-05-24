import os
import subprocess
import jinja2
import re

# LaTeX special characters that need escaping (prevents crashes with & % $ # _ { })
def tex_escape(text):
    if not isinstance(text, str):
        return text
    regex = re.compile(r'([{}])'.format(re.escape(r'&%$#_{}~^\\')))
    return regex.sub(r'\\\1', text)

# Configure Jinja2 to use tags that don't clash with LaTeX brackets
latex_jinja_env = jinja2.Environment(
    block_start_string='\BLOCK{',
    block_end_string='}',
    variable_start_string='\VAR{',
    variable_end_string='}',
    comment_start_string='\#{',
    comment_end_string='}',
    line_statement_prefix='%%',
    line_comment_prefix='%#',
    trim_blocks=True,
    autoescape=False,
    loader=jinja2.FileSystemLoader(os.path.abspath('.'))
)
latex_jinja_env.filters['e'] = tex_escape

TEX_FIELDS = {"tailored_skills", "tailored_experience", "tailored_projects"}

def generate_pdf(data, template_path, output_filename):
    def escape_dict(d, key=None):
        if key in TEX_FIELDS:
            return d  # don't escape raw LaTeX snippets
        if isinstance(d, dict):
            return {k: escape_dict(v, key=k) for k, v in d.items()}
        elif isinstance(d, list):
            return [escape_dict(i) for i in d]
        return tex_escape(d)

    clean_data = escape_dict(data)
    template = latex_jinja_env.get_template(template_path)
    rendered_tex = template.render(**clean_data)
    
    tex_file = f"{output_filename}.tex"
    with open(tex_file, "w") as f:
        f.write(rendered_tex)
    
    try:
        latex_path = "/Library/TeX/texbin/pdflatex"
        cmd = [latex_path, "-interaction=nonstopmode", tex_file]
        
        # Notice we removed check=True so Python doesn't panic on minor warnings
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        pdf_file = f"{output_filename}.pdf"
        
        # The ultimate test: did it actually make the PDF?
        if os.path.exists(pdf_file):
            # Cleanup LaTeX junk files
            for ext in [".aux", ".log", ".out"]:
                if os.path.exists(output_filename + ext):
                    os.remove(output_filename + ext)
            return pdf_file
        else:
            print("❌ LaTeX Compilation Failed!")
            print("--- LATEX ERROR LOG ---")
            print(result.stdout[-1000:])
            return None
            
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return None