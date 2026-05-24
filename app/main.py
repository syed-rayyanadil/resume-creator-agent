from fastapi import FastAPI, HTTPException
import os
import subprocess
from app.graph import agent_workflow
from app.state import AgentState
from app.nodes import load_master_data  # Import the master data loader

app = FastAPI()


def compile_resume_tex(tex_content: str, output_filename: str = "tailored_resume"):
    tex_file = f"{output_filename}.tex"
    with open(tex_file, "w") as f:
        f.write(tex_content)

    latex_path = "/Library/TeX/texbin/pdflatex"
    result = subprocess.run(
        [latex_path, "-interaction=nonstopmode", tex_file],
        capture_output=True,
        text=True,
    )

    pdf_file = f"{output_filename}.pdf"
    if os.path.exists(pdf_file):
        for ext in [".aux", ".log", ".out"]:
            if os.path.exists(output_filename + ext):
                os.remove(output_filename + ext)
        return pdf_file

    print("❌ LaTeX Compilation Failed!")
    print(result.stdout[-1000:])
    return None

@app.post("/generate")
async def generate_resume(request: dict):
    # Grab the JD from the frontend
    jd = request.get("job_description")
    
    # Grab the model choice from the frontend! 
    # (We provide the 17B model as a safe default just in case)
    model_choice = request.get("model_name", "meta-llama/llama-4-scout-17b-16e-instruct")

    if not jd:
        raise HTTPException(status_code=400, detail="Job description is required")
    
    do_resume = request.get("generate_resume", True)
    # Cover letter and email are disabled for the resume-only flow.
    # do_cl = request.get("generate_cover_letter", True)
    # do_email = request.get("generate_email", True)

    # 1. Run the Agent Workflow
    initial_state = AgentState(
        job_description=jd,
        model_name=model_choice, # Pass the chosen model into LangGraph!
        jd_analysis={},
        resume_rules={},
        personal={},
        education=[],
        retrieved_projects=[],
        tailored_skills={},
        experience_scores=[],
        tailored_experience=[],
        tailored_projects=[],
        resume_tex="",
        cover_letter="",
        email_draft="",
        email_subject="",
        email_body="",
        recipient="",
        generate_resume=do_resume,
        generate_cover_letter=False,
        generate_email=False,
        skills_retries=0,
        experience_retries=0,
        projects_retries=0,
    )
    
    final_output = agent_workflow.invoke(initial_state)

    print("FINAL OUTPUT KEYS:", list(final_output.keys()))
    print("TAILORED EXPERIENCE:", final_output.get("tailored_experience"))
    print("TAILORED PROJECTS:", final_output.get("tailored_projects"))

    print("🚀 Compiling Resume PDF...")
    resume_tex = final_output.get("resume_tex", "")
    if resume_tex:
        compile_resume_tex(resume_tex, "tailored_resume")

    # Cover letter and email PDF generation are disabled for the resume-only flow.
    # cover_letter_content = final_output.get("cover_letter")
    # if do_cl and cover_letter_content:
    #     ...

    return final_output
