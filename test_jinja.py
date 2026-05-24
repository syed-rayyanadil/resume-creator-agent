import jinja2

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
)

template_str = """
\BLOCK{ if tailored_projects and tailored_projects|trim != '' }
\section{Projects}
\VAR{tailored_projects}
\BLOCK{ endif }
"""

template = latex_jinja_env.from_string(template_str)
print("Empty string:", repr(template.render(tailored_projects="")))
print("Spaces:", repr(template.render(tailored_projects="   ")))
