import streamlit as st
import ollama
import json
import re
from json_repair import repair_json

st.title("Advanced Resume Tailor")
st.markdown("Generates a highly targeted resume, cover letter, and outreach email based on your Master Data.")

# ==========================================
# 1. LOAD MASTER DATA FROM FILE
# ==========================================
try:
    with open('my_data.json', 'r') as f: 
        master_data = json.load(f)
except FileNotFoundError:
    st.error("⚠️ 'my_data.json' file not found! Please make sure it is in the same folder as this script.")
    st.stop()

# ==========================================
# 2. UI: INPUTS & OPTIONS
# ==========================================
st.subheader("1. Job Details & Settings")

job_description = st.text_area("Paste the Job Description (JD)", height=200, placeholder="Paste the JD here...")

col1, col2 = st.columns(2)
with col1:
    generate_cover_letter = st.checkbox("Generate Cover Letter")
with col2:
    generate_email = st.checkbox("Generate Outreach Email")

# ==========================================
# 3. CORE LOGIC
# ==========================================
if st.button("Generate Tailored Application", type="primary"):
    if not job_description:
        st.warning("Please paste a Job Description first!")
    else:
        with st.spinner("Analyzing JD and filtering your Master Data (this may take a minute)..."):
            
            # --- YOUR NEW DETAILED PROMPT ---
            system_prompt = """
            You are an expert technical resume writer and recruiter with deep knowledge of software 
            engineering, AI/ML, and European tech hiring.

            You will receive two inputs:
            1. MASTER_DATA: A JSON file containing the candidate's complete profile (personal info, 
            all skills, full education, all work experience, all projects).
            2. JD: A job description for the role being applied to.

            Your task is to produce a tailored resume JSON that is highly relevant to the JD, 
            while following the strict rules below.

            ---

            SECTION A — PERSONAL
            Always include as-is from MASTER_DATA. Never modify name, email, phone, linkedin, 
            or github.

            ---

            SECTION B — SKILLS
            1. Read the JD carefully and identify every technical and non-technical skill it 
            mentions or implies.
            2. From MASTER_DATA skills (flat list), select ONLY skills that are relevant to the 
            JD — through direct keyword match OR semantic relevance (e.g. "Kotest" is relevant 
            if JD mentions "testing", "TDD", or "test coverage").
            3. Group the selected skills into 2 to 4 categories. Choose category names that best 
            fit the selected skills (e.g. "Languages", "Frameworks & Libraries", "Databases", 
            "Architecture & Practices", "Tools & Platforms", "ML & AI", etc.). Only create a 
            category if it has relevant skills — do not force all 4.
            4. Do NOT include skills that have no connection to the JD.

            ---

            SECTION C — EDUCATION
            Always include both degrees (BSc and MSc) exactly as in MASTER_DATA.
            - Include the MSc thesis title only if the JD is related to AI, ML, Computer Vision, 
            or research.
            - Always include degree name, institution, location, and period.

            ---

            SECTION D — EXPERIENCE
            Rules:
            1. ALWAYS include all 3 companies (Schwarz Digits, Benchmatrix, GoodCore). Never drop 
            a company entirely, even if the JD is not a perfect match — adapt the bullets instead.
            2. For each company/role, include ALL bullet points from MASTER_DATA that are relevant 
            or transferable to the JD. Target 4 to 6 bullets per role — do not artificially 
            limit to 2-3.
            3. Bullet writing rules (in order of preference):
            a. If a bullet directly matches the JD: include it, rephrase using JD keywords.
            b. If a bullet shows transferable skill: include and reword it using JD terminology.
            c. If an obvious and truthful detail can be inferred from context (e.g. they used 
                Hexagonal Architecture → they understand separation of concerns and maintainability; 
                they worked in a 3-engineer team → they practiced code reviews and collaborative 
                Git workflows): add it as a natural extension of the existing bullet. 
                Never fabricate specific metrics, tools, or outcomes that are not inferable.
            4. If a company has sub-projects (e.g. GoodCore: Project 1 and Project 2), include 
            both as sub-labels and select the most relevant bullets from each.
            5. Prioritize impact-driven language: use quantified details wherever they exist in 
            MASTER_DATA (e.g. "7 banks", "millions of users", "60 Fortune 500 companies", 
            "50,000 images", "95 percent accuracy").

            ---

            SECTION E — PROJECTS
            Rules:
            1. Always select the most relevant projects based on what the JD actually asks for. 
            Do not exclude AI/ML projects by default for SE roles — if the JD mentions anything 
            adjacent (LLMs, automation, CV, NLP, data pipelines, intelligent systems, 
            recommendation, search, etc.), include the matching AI/ML project(s).
            2. For purely technical SE JDs with no AI/ML angle at all: include 1-2 projects that 
            best demonstrate engineering skill (system design, scale, real-time performance, 
            accuracy metrics).
            3. For AI/ML or research-heavy JDs: include all relevant AI/ML projects.
            4. For each included project, write relevant_details that highlight the aspects most 
            aligned with the JD (e.g. if JD mentions "real-time systems", lead with the 
            3-second alert in the surveillance project; if JD mentions "recommendation", 
            lead with cosine similarity and top-N results).
            5. Always include the GitHub link if available.

            ---

            TONE & STYLE RULES
            - Use strong action verbs: Designed, Architected, Migrated, Drove, Owned, Engineered, 
            Built, Implemented, Led, Delivered.
            - Mirror terminology from the JD where truthful (e.g. if JD says "event-driven 
            architecture" and the candidate used microservices/REST, reference that using 
            JD language if accurate).
            - Every bullet must be specific and verifiable — no vague filler like "worked on" 
            or "helped with".
            - Keep bullets concise: 1-2 lines each. No paragraph-style bullets.
            - Do not use hedging language ("assisted", "contributed to", "involved in") unless 
            it is literally the only accurate description.

            ---

            OUTPUT FORMAT
            Return ONLY valid JSON. No explanation, no markdown, no preamble. 
            Use this exact structure:

            {
            "personal": {
                "name": "",
                "email": "",
                "phone": "",
                "location": "",
                "linkedin": "",
                "github": ""
            },
            "skills": {
                "Category Name 1": ["skill1", "skill2"],
                "Category Name 2": ["skill3", "skill4"]
            },
            "education": [
                {
                "degree": "",
                "institution": "",
                "location": "",
                "period": "",
                "thesis": ""
                }
            ],
            "experience": [
                {
                "company": "",
                "role": "",
                "location": "",
                "period": "",
                "projects": [
                    {
                    "name": "",
                    "bullets": [""]
                    }
                ]
                }
            ],
            "projects": [
                {
                "name": "",
                "technologies": [""],
                "github": "",
                "relevant_details": [""]
                }
            ]
            }

            Note: For experience entries with no sub-projects (like Schwarz Digits), use a single 
            project entry with name: "" and list all bullets there. For entries with multiple 
            sub-projects (like GoodCore), use one entry per sub-project with its name.
            """
            
            user_prompt = f"JOB DESCRIPTION:\n{job_description}\n\nMASTER DATA:\n{json.dumps(master_data)}"
            
            # --- CALL OLLAMA (No streaming) ---
            response = ollama.chat(
                model='llama3', 
                format='json',
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ],
                options={
                    'temperature': 0.1, 
                    'num_predict': 2500  # Forces the model to allow up to 2500 tokens for the response
                }
            )
            
            # ==========================================
            # 4. PARSE & DISPLAY RESULTS
            # ==========================================
            # ==========================================
            # 4. PARSE & DISPLAY RESULTS (Regex Powered)
            # ==========================================
            raw_string = response['message']['content']
            
            try:
                # 1. Aggressively hunt for the JSON object using Regex
                # This ignores any conversational text before or after the JSON
                match = re.search(r'\{.*\}', raw_string, re.DOTALL)
                
                if not match:
                    st.error("The model didn't output any recognizable JSON format.")
                    st.stop()
                    
                clean_json_string = match.group(0)
                
                # 2. Parse the clean string
                fixed_json_string = repair_json(clean_json_string)
                parsed_data = json.loads(fixed_json_string)
                
                st.success("Analysis Complete!")
                st.divider()
                
                st.header("📄 Tailored Resume")
                
                # --- Personal ---
                p_info = parsed_data.get('personal', {})
                st.markdown(f"**{p_info.get('name', '')}** | {p_info.get('email', '')} | {p_info.get('phone', '')} | {p_info.get('location', '')}")
                st.markdown(f"[LinkedIn]({p_info.get('linkedin', '')}) | [GitHub]({p_info.get('github', '')})")
                
                # --- Education ---
                st.subheader("Education")
                for edu in parsed_data.get('education', []):
                    thesis_str = f"  \n*Thesis: {edu.get('thesis')}*" if edu.get('thesis') else ""
                    st.markdown(f"- **{edu.get('degree')}** — {edu.get('institution')} ({edu.get('location')}, {edu.get('period')}){thesis_str}")
                
                # --- Skills ---
                # --- Skills ---
                st.subheader("Skills")
                skills_data = parsed_data.get('skills', {})

                # If the AI followed instructions and made a dictionary:
                if isinstance(skills_data, dict):
                    for category, skills_list in skills_data.items():
                        # Safety check in case the AI made the skills a string instead of a list
                        if isinstance(skills_list, list):
                            st.markdown(f"**{category}:** {', '.join(str(s) for s in skills_list)}")
                        else:
                            st.markdown(f"**{category}:** {skills_list}")

                # If the AI got lazy and just returned a flat list of skills:
                elif isinstance(skills_data, list):
                    st.markdown(f"**Relevant Skills:** {', '.join(str(s) for s in skills_data)}")
                
                # --- Experience ---
                st.subheader("Experience")
                for exp in parsed_data.get('experience', []):
                    st.markdown(f"**{exp.get('role')}** at {exp.get('company')} | *{exp.get('location')} ({exp.get('period')})*")
                    
                    for proj in exp.get('projects', []):
                        if proj.get('name'):
                            st.markdown(f"**Project: {proj.get('name')}**")
                        for bullet in proj.get('bullets', []):
                            st.markdown(f"- {bullet}")
                    st.write("") 
                
                # --- Projects ---
                st.subheader("Selected Projects")
                for proj in parsed_data.get('projects', []):
                    github_link = f" [GitHub]({proj.get('github')})" if proj.get('github') else ""
                    tech = f" | *{', '.join(proj.get('technologies', []))}*" if proj.get('technologies') else ""
                    
                    st.markdown(f"**{proj.get('name')}**{github_link}{tech}")
                    for detail in proj.get('relevant_details', []):
                        st.markdown(f"- {detail}")

                st.divider()

                # --- Downloads ---
                st.subheader("⬇️ Download Assets")
                export_data = json.dumps(parsed_data, indent=2)

                col_dl1, col_dl2 = st.columns(2)
                with col_dl1:
                    st.download_button(label="Download Resume JSON", data=export_data, file_name="tailored_resume.json", mime="application/json")
                
                with st.expander("View Raw JSON Model Output"):
                    st.json(parsed_data)

            except json.JSONDecodeError as e:
                # If it STILL fails, this prints the exact error and the raw text so you can see what the AI messed up
                st.error(f"Failed to parse JSON. Error: {e}")
                with st.expander("Click to see what the AI actually wrote (Debugging)"):
                    st.text(raw_string)