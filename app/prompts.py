import json


def get_jd_analysis_prompt(jd: str) -> str:
    return f"""
You are a technical recruiter. Extract structured facts from the job description.

Return ONLY valid JSON. No markdown, no comments, no preamble.

Rules:
- role_type must be exactly one of: "backend", "ai_ml", "hybrid".
- Use "hybrid" when the JD combines backend with Python, JVM/server-side, frontend, distributed systems, cloud, CI/CD, Docker/Kubernetes, or infrastructure.
- Use "backend" only when the JD is clearly server-side/backend without a mixed Python/JVM/frontend/cloud profile.
- must_have_skills must contain the top 5-8 concrete technical skills from the JD.
- domain should be a short lowercase business domain such as "fintech", "logistics", "saas", "ecommerce", "mobility", or "general".
- mentions_ai must be true only if the JD explicitly mentions AI, ML, data science, computer vision, NLP, LLMs, or intelligent systems.

Output shape:
{{
  "role_type": "backend",
  "must_have_skills": ["Java", "Kotlin", "REST APIs", "PostgreSQL", "Docker"],
  "domain": "logistics",
  "mentions_ai": false
}}

JD:
{jd}
"""


def get_skills_prompt(
    jd_analysis: dict,
    resume_rules: dict | list,
    tagged_skills: list[dict] | None = None,
    experience: list[dict] | None = None,
) -> str:
    if tagged_skills is None:
        tagged_skills = [
            {"skill": str(skill), "tags": []}
            for skill in (resume_rules if isinstance(resume_rules, list) else [])
        ]
        resume_rules = {"skill_category_schema": "hybrid"}
    if experience is None:
        experience = []
    return f"""
You are a resume writer. Select skills from TAGGED_SKILLS that are relevant to JD_ANALYSIS.

JD_ANALYSIS: {json.dumps(jd_analysis)}
RESUME_RULES: {json.dumps(resume_rules)}
TAGGED_SKILLS: {json.dumps(tagged_skills)}
EXPERIENCE_CONTEXT: {json.dumps(experience)}

STRICT RULES:
- Phase 1 exact match: select skills from TAGGED_SKILLS that directly match JD keywords or must_have_skills.
- Phase 2 inference: for each JD keyword, infer closely related skills only when strongly supported by EXPERIENCE_CONTEXT.
- Do NOT fabricate skills. Every selected skill must exist in TAGGED_SKILLS.
- Do NOT include JD-only skills that are absent from TAGGED_SKILLS. Example: if JD asks for COBOL or Oracle but they are not in TAGGED_SKILLS, exclude them.
- Use controlled equivalence only when the equivalent skill exists in TAGGED_SKILLS:
  Java/JVM/server-side -> Java, Kotlin, Spring Boot, REST APIs if present.
  SQL/relational database/Oracle -> PostgreSQL, MySQL, SQL if present; do not write Oracle unless present.
  cloud/infrastructure/CI/CD -> Docker, Kubernetes, Google Cloud Platform (GCP), GitHub Actions, Azure DevOps, Jenkins if present.
  API/documentation/agile/collaboration -> Swagger, Jira, Confluence if present.
- Do NOT write "(implied)" or any annotation next to any skill.
- Use RESUME_RULES.skill_category_schema to choose category names exactly:
  ai_ml: Languages, ML/DS Frameworks, Databases, MLOps
  backend: Languages, Backend, Databases, DevOps
  hybrid: Languages, Backend/Frameworks, Databases, Tools/DevOps
- Do not create categories outside the selected schema.
- Skip any category that has no relevant skills.
- Put REST APIs, Microservices, Spring Boot, architecture, and testing under Backend or Backend/Frameworks, never under DevOps.
- Put Docker, Kubernetes, CI/CD, Git, cloud, and deployment tools under DevOps or Tools/DevOps.
- Put PostgreSQL, MongoDB, MySQL, and SQL under Databases.
- If the JD mentions JVM/server-side, include supported Java/Kotlin/backend skills even when the job title emphasizes Python.
- Return ONLY valid JSON. No explanation, no markdown, no preamble.

OUTPUT JSON SHAPE:
{{
  "Languages": ["Python", "Java"],
  "Frameworks": ["Spring Boot"]
}}
"""


def get_projects_phase_a_prompt(jd_analysis: dict, retrieved_chunks: list[dict]) -> str:
    return f"""
You are a resume writer. Select the strongest project items from RETRIEVED_PROJECT_CHUNKS for JD_ANALYSIS.

Return ONLY valid JSON. No markdown, no explanation.

STRICT RULES:
- Use only facts present in the retrieved chunks.
- Select projects with direct overlap to role_type, must_have_skills, domain, or mentions_ai.
- For hybrid or Python-backend JDs, prefer one Python/engineering project if it strengthens the resume.
- Each selected project must have exactly one rewritten bullet.
- Rewrite every bullet in XYZ format: "Accomplished [X] as measured by [Y], by doing [Z]."
- If no project is relevant, return {{"projects": []}}.

OUTPUT JSON SHAPE:
{{
  "projects": [
    {{
      "name": "Project Name",
      "github": "GITHUB_URL",
      "technologies": ["Tech1", "Tech2", "Tech3"],
      "bullet": "Accomplished X as measured by Y, by doing Z."
    }}
  ]
}}

JD_ANALYSIS: {json.dumps(jd_analysis)}
RETRIEVED_PROJECT_CHUNKS: {json.dumps(retrieved_chunks)}
"""


def get_projects_phase_b_prompt(phase_a_json: dict) -> str:
    return f"""
Convert PROJECT_SELECTION_JSON into LaTeX.

Return ONLY LaTeX. No markdown, no explanation, no preamble.
If PROJECT_SELECTION_JSON.projects is empty, return an empty string.

OUTPUT FORMAT FOR EACH PROJECT:
\\begin{{twocolentry}}{{\\href{{GITHUB_URL}}{{\\underline{{GitHub}}}}}}
    \\textbf{{Project Name}} | \\textit{{Tech1, Tech2, Tech3}}
\\end{{twocolentry}}
\\vspace{{0.10cm}}
\\begin{{onecolentry}}
\\begin{{highlights}}
    \\item One line description with impact and key technologies.
\\end{{highlights}}
\\end{{onecolentry}}

\\vspace{{0.3cm}}

PROJECT_SELECTION_JSON: {json.dumps(phase_a_json)}
"""


def get_score_experiences_prompt(jd_analysis: dict, resume_rules: dict, experiences: list[dict]) -> str:
    return f"""
You are a resume relevance scorer. Score each experience entry for the JD.

Return ONLY valid JSON. No markdown, no explanation.

STRICT RULES:
- For each experience entry, reason privately step by step before choosing a score.
- Do NOT output chain-of-thought. Put only a short reason in the reason field.
- Score each entry 0-10 based on direct relevance plus transferable engineering value.
- Do NOT score low only because the programming language is different from the JD.
- Score different-language experience medium/high when it shows business logic, backend/product features, APIs, integrations, databases, testing, reliability, automation, production deployment, scale, users, clients, or business impact.
- For off-domain experience, score it higher if it shows architecture, scalability, API design, system design, reliability, automation, integrations, or production ownership.
- Add shrink: true only when an entry is useful but secondary for this JD.
- Add skip: true only when an entry is truly unrelated and lacks transferable engineering evidence.
- Prefer preserving all professional experience entries. For this candidate, entries with enterprise SaaS, 60+ clients, banking systems, APIs, automation, or production reliability should not be skipped.
- Return one object per experience entry.

OUTPUT JSON SHAPE:
[
  {{"id": "exp_01", "score": 8, "reason": "Strong backend overlap with APIs and reliability.", "shrink": false, "skip": false}}
]

JD_ANALYSIS: {json.dumps(jd_analysis)}
RESUME_RULES: {json.dumps(resume_rules)}
EXPERIENCES: {json.dumps(experiences)}
"""


def get_rewrite_experience_prompt(jd_analysis: dict, resume_rules: dict, experience: dict, score: dict, tailored_skills: dict = None) -> str:
    if tailored_skills is None:
        tailored_skills = {}
    return f"""
You are a resume writer. Rewrite exactly one experience entry for the JD.

Return ONLY valid JSON or null. No markdown, no explanation, no preamble.

STRICT RULES:
- If SCORE.skip is true, return null.
- "Shrink" means compress wording to maximum {resume_rules.get('exp_bullet_limit_secondary', 3)} bullets per project group, without deleting core engineering evidence.
- If SCORE.shrink is false, rewrite to maximum {resume_rules.get('exp_bullet_limit_main', 5)} bullets across entries.
- Frame different-language work around transferable engineering value (APIs, scale, testing, etc.) instead of deleting it.
- Weave in relevant keywords from TAILORED_SKILLS naturally.
- Do not fabricate information. Preserve company, role, period, location, and project labels.
- Output your reasoning in the "thought_process" field before "projects" to plan the best bullet points.

EXAMPLE OUTPUT JSON:
{{
  "id": "exp_01",
  "company": "Tech Corp",
  "role": "Software Engineer",
  "period": "2021-2023",
  "location": "Remote",
  "thought_process": "JD needs scalable backend & APIs. Original mentions Java API and saving time. I will emphasize the API creation, scale, and time saved using tailored skills.",
  "projects": [
    {{"name": "Backend API", "bullets": ["Engineered scalable Java API to automate data processing, reducing manual effort by 20%"], "technologies": ["Java", "API"]}}
  ]
}}

JD_ANALYSIS: {json.dumps(jd_analysis)}
RESUME_RULES: {json.dumps(resume_rules)}
TAILORED_SKILLS: {json.dumps(tailored_skills)}
EXPERIENCE_ENTRY: {json.dumps(experience)}
SCORE: {json.dumps(score)}
"""


def get_letter_prompt(jd_analysis: dict, tailored_experience: str, personal: dict) -> str:
    return f"""
SYSTEM INSTRUCTION:
- You are a professional cover letter writer with 10 years of recruiting experience.
- Write in first person, confident but not arrogant tone.
- Never use filler phrases like "I am excited to apply" or "I am passionate about".
- Never repeat the job title more than once.
- Mirror keywords from jd_analysis naturally, do not stuff them.

USER DATA:
- jd_analysis dict (role_type, must_have_skills, domain, mentions_ai): {json.dumps(jd_analysis)}
- tailored_experience string (the rewritten XYZ bullets from resume): {tailored_experience}
- personal data: name: {personal.get("name", "")}, current role context: MSc AI student + working student background

COVER LETTER must have exactly 4 paragraphs:
Paragraph 1 — Hook: one strong opening sentence about why this specific role and company, no generic opener.
Paragraph 2 — Relevant experience: pull 2-3 specific achievements from tailored_experience using actual numbers and tech from the XYZ bullets.
Paragraph 3 — Value add: connect MSc AI thesis and any AI/CV background IF jd_analysis mentions_ai is true, otherwise connect to backend depth and architecture experience.
Paragraph 4 — Close: one confident closing line + call to action. No "thank you for your consideration" cliche.

EMAIL must be:
- Max 5 lines
- Subject line included as a field
- Purpose: applying via email when company says to apply by email
- Reference the role and one specific achievement only
- Professional but direct tone

OUTPUT FORMAT MUST BE EXACTLY:
{{
  "cover_letter": "Paragraph1\\n\\nParagraph2\\n\\nParagraph3\\n\\nParagraph4",
  "email_draft": {{
    "subject": "Subject line here",
    "body": "Email body here"
  }}
}}
"""


# Backwards-compatible names for old ad-hoc test scripts.
def get_projects_prompt(jd_analysis: dict, retrieved_chunks: list[dict]) -> str:
    return get_projects_phase_a_prompt(jd_analysis, retrieved_chunks)


def get_experience_prompt(jd_analysis: dict, retrieved_chunks: list[dict]) -> str:
    return get_score_experiences_prompt(jd_analysis, {}, retrieved_chunks)
