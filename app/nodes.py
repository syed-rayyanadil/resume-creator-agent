import json
import os
import re
from typing import Any, Dict

from app.database import retrieve_resume_chunks
from app.prompts import (
    get_jd_analysis_prompt,
    get_letter_prompt,
    get_projects_phase_a_prompt,
    get_rewrite_experience_prompt,
    get_score_experiences_prompt,
    get_skills_prompt,
)
from app.state import AgentState
from app.utils.OllamaConnection import generate_text
from app.utils.pdf_generator import latex_jinja_env, tex_escape


def load_master_data():
    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "my_data.json")
    with open(data_path, "r") as f:
        return json.load(f)


def extract_json(text: str) -> Any | None:
    text = (text or "").strip()

    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]

    text = text.strip()

    try:
        return json.loads(text, strict=False)
    except json.JSONDecodeError:
        pass

    try:
        match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", text)
        if match:
            return json.loads(match.group(0), strict=False)
    except Exception as e:
        print(f"❌ Regex JSON Parse Error: {e}")

    return None


def _analysis_query(jd_analysis: dict) -> str:
    skills = jd_analysis.get("must_have_skills", [])
    if not isinstance(skills, list):
        skills = []
    role_type = jd_analysis.get("role_type", "mixed")
    domain = jd_analysis.get("domain", "general")
    return f"role_type: {role_type}; domain: {domain}; skills: {', '.join(map(str, skills))}"


def _retrieve_for_section(state: AgentState, chunk_type: str) -> list[dict]:
    jd_analysis = state.get("jd_analysis", {})
    query = _analysis_query(jd_analysis)
    try:
        return retrieve_resume_chunks(query=query, chunk_type=chunk_type, top_k=5)
    except Exception as e:
        print(f"❌ Retrieval failed for {chunk_type}: {e}")
        return []


def _latex_has(text: str, required: list[str]) -> bool:
    clean = (text or "").strip()
    return bool(clean) and all(token in clean for token in required)


SKILL_CATEGORY_TAGS = {
    "Languages": {"language", "python", "java", "kotlin", "golang", "typescript", "javascript", "php"},
    "Backend": {"backend", "framework", "architecture", "testing"},
    "Backend/Frameworks": {"backend", "framework", "architecture", "testing", "frontend"},
    "Frameworks": {"framework", "backend", "frontend"},
    "ML/DS Frameworks": {"ai", "ml", "data"},
    "ML Libraries": {"ai", "ml", "data"},
    "Databases": {"database"},
    "MLOps": {"devops", "cloud", "mlops"},
    "DevOps": {"devops", "cloud", "tool"}, 
    "Tools": {"tool", "devops", "cloud"},
}

SKILL_ALIASES = {
    "gcp": "Google Cloud Platform (GCP)",
    "google cloud": "Google Cloud Platform (GCP)",
    "google cloud platform": "Google Cloud Platform (GCP)",
    "rest api": "REST APIs",
    "rest apis": "REST APIs",
    "api": "REST APIs",
    "sql": "SQL",
    "ci/cd": "CI/CD",
    "cicd": "CI/CD",
    "github actions": "GitHub Actions",
    "azure devops": "Azure DevOps",
}

SKILL_CATEGORY_BY_SCHEMA = {
    "backend": {
        "Languages": {"language"},
        "Backend": {"backend", "framework", "architecture", "testing"},
        "Databases": {"database"},
        "DevOps": {"devops", "cloud", "tool"},
    },
    "hybrid": {
        "Languages": {"language"},
        "Backend/Frameworks": {"backend", "framework", "architecture", "testing", "frontend"},
        "Databases": {"database"},
        "Tools/DevOps": {"devops", "cloud", "tool"},
    },
    "ai_ml": {
        "Languages": {"language"},
        "ML/DS Frameworks": {"ai", "ml", "data"},
        "Databases": {"database"},
        "MLOps": {"devops", "cloud", "tool"},
    },
}

CONTROLLED_SKILL_INFERENCES = {
    "java": ["Java", "Kotlin", "Spring Boot", "Spring MVC", "JPA/Hibernate", "REST APIs"],
    "jvm": ["Java", "Kotlin", "Spring Boot", "Spring MVC", "JPA/Hibernate", "REST APIs"],
    "server-side": ["Java", "Kotlin", "Spring Boot", "REST APIs", "Microservices"],
    "backend": ["Java", "Kotlin", "Python", "Spring Boot", "REST APIs", "Microservices"],
    "sql": ["SQL", "PostgreSQL", "MySQL"],
    "relational": ["SQL", "PostgreSQL", "MySQL"],
    "database": ["PostgreSQL", "MongoDB", "MySQL", "SQL"],
    "oracle": ["PostgreSQL", "MySQL", "SQL"],
    "cloud": ["Google Cloud Platform (GCP)", "Docker", "Kubernetes", "CI/CD", "GitHub Actions", "Azure DevOps", "Jenkins"],
    "infrastructure": ["Google Cloud Platform (GCP)", "Docker", "Kubernetes", "CI/CD", "GitHub Actions", "Azure DevOps", "Jenkins"],
    "ci/cd": ["CI/CD", "GitHub Actions", "Azure DevOps", "Jenkins", "Docker", "Kubernetes"],
    "docker": ["Docker", "Kubernetes"],
    "kubernetes": ["Kubernetes", "Docker"],
    "api": ["REST APIs", "Swagger"],
    "documentation": ["Swagger", "Confluence"],
    "agile": ["Agile", "Jira", "Confluence"],
    "testing": ["TDD", "JUnit", "Mockito", "Kotest"],
}


def _tagged_skills(master: dict) -> list[dict]:
    tagged = []
    skill_names = list(master.get("skills", []))
    for experience in master.get("experience", []) or []:
        skill_names.extend(experience.get("technologies", []) or [])
        for project in experience.get("projects", []) or []:
            skill_names.extend(project.get("technologies", []) or [])
    for project in master.get("projects", []) or []:
        skill_names.extend(project.get("technologies", []) or [])

    seen = set()
    for skill in skill_names:
        name = str(skill)
        if name.lower() in seen:
            continue
        seen.add(name.lower())
        lower = name.lower()
        tags = set()
        if lower in {"java", "kotlin", "python", "golang", "typescript", "javascript", "php"}:
            tags.add("language")
        if any(token in lower for token in ["spring", "laravel", "react", "angular", "redux", "flask", "hibernate"]):
            tags.update({"framework", "backend"})
        if any(token in lower for token in ["rest", "microservices", "architecture", "strategy pattern", "clean code"]):
            tags.update({"backend", "architecture"})
        if any(token in lower for token in ["tdd", "junit", "mockito", "kotest", "testing"]):
            tags.update({"backend", "testing"})
        if any(token in lower for token in ["pytorch", "opencv", "cnn", "yolo", "transformer", "clip", "llm", "sklearn", "pandas", "numpy", "learning", "vision", "gan"]):
            tags.update({"ai", "ml"})
        if any(token in lower for token in ["postgres", "mongo", "mysql", "sql"]):
            tags.add("database")
        if any(token in lower for token in ["docker", "kubernetes", "devops", "github actions", "gcp", "jenkins", "ci/cd"]):
            tags.update({"devops", "cloud"})
        if not tags:
            tags.add("tool")
        tagged.append({"skill": name, "tags": sorted(tags)})
    return tagged


def _skill_lookup(tagged_skills: list[dict]) -> dict[str, dict]:
    lookup = {}
    for item in tagged_skills:
        skill = item.get("skill")
        if not skill:
            continue
        lookup[str(skill).lower()] = item
        alias = SKILL_ALIASES.get(str(skill).lower())
        if alias:
            lookup[alias.lower()] = item
    return lookup


def _canonical_skill_name(skill: str, lookup: dict[str, dict]) -> str | None:
    key = str(skill).strip().lower()
    if key in lookup:
        return lookup[key]["skill"]
    alias = SKILL_ALIASES.get(key)
    if alias and alias.lower() in lookup:
        return lookup[alias.lower()]["skill"]
    return None


def _jd_skill_candidates(jd_analysis: dict, tagged_skills: list[dict]) -> set[str]:
    lookup = _skill_lookup(tagged_skills)
    jd_terms = " ".join(str(term) for term in jd_analysis.get("must_have_skills", []))
    jd_terms = f"{jd_terms} {jd_analysis.get('domain', '')} {jd_analysis.get('role_type', '')}".lower()
    selected = set()

    for item in tagged_skills:
        skill = item.get("skill", "")
        if skill and skill.lower() in jd_terms:
            selected.add(skill)

    for trigger, inferred_skills in CONTROLLED_SKILL_INFERENCES.items():
        if trigger in jd_terms:
            for skill in inferred_skills:
                canonical = _canonical_skill_name(skill, lookup)
                if canonical:
                    selected.add(canonical)

    return selected


def _normalize_tailored_skills(skills: Any, jd_analysis: dict, resume_rules: dict, tagged_skills: list[dict]) -> dict:
    lookup = _skill_lookup(tagged_skills)
    allowed_names = {item["skill"] for item in tagged_skills if item.get("skill")}
    selected = _jd_skill_candidates(jd_analysis, tagged_skills)

    if isinstance(skills, dict):
        for values in skills.values():
            if not isinstance(values, list):
                continue
            for value in values:
                canonical = _canonical_skill_name(str(value), lookup)
                if canonical in allowed_names:
                    selected.add(canonical)

    schema = resume_rules.get("skill_category_schema", "hybrid")
    category_schema = SKILL_CATEGORY_BY_SCHEMA.get(schema, SKILL_CATEGORY_BY_SCHEMA["hybrid"])
    categorized = {category: [] for category in category_schema}

    for skill in sorted(selected):
        item = lookup.get(skill.lower())
        if not item:
            continue
        tags = set(item.get("tags", []))
        for category, category_tags in category_schema.items():
            if tags & category_tags:
                categorized[category].append(skill)
                break

    return {category: values for category, values in categorized.items() if values}


def _normalize_projects(data: Any) -> list[dict]:
    if isinstance(data, dict):
        projects = data.get("projects", [])
        return projects if isinstance(projects, list) else []
    return data if isinstance(data, list) else []


def _normalize_experience_scores(data: Any) -> list[dict]:
    if isinstance(data, dict):
        data = data.get("scores", data.get("experience", []))
    return data if isinstance(data, list) else []


def _experience_has_transferable_value(experience: dict) -> bool:
    text_parts = [
        experience.get("domain", ""),
        " ".join(experience.get("highlights", [])),
    ]
    for project in experience.get("projects", []) or []:
        text_parts.extend([
            project.get("name", ""),
            project.get("domain", ""),
            " ".join(project.get("highlights", project.get("bullets", []))),
        ])
    text = " ".join(str(part).lower() for part in text_parts)
    preservation_signals = [
        "api",
        "microservice",
        "architecture",
        "testing",
        "reliability",
        "automation",
        "integration",
        "database",
        "deployment",
        "ci/cd",
        "docker",
        "kubernetes",
        "users",
        "clients",
        "fortune 500",
        "business logic",
        "production",
        "scale",
        "stability",
    ]
    return any(signal in text for signal in preservation_signals)


def _guard_experience_scores(scores: list[dict], experiences: list[dict]) -> list[dict]:
    by_id = {entry.get("id"): entry for entry in experiences}
    guarded = []
    seen_ids = set()
    for score in scores:
        if not isinstance(score, dict):
            continue
        exp_id = score.get("id")
        exp = by_id.get(exp_id)
        if not exp:
            continue
        score = {**score}
        score_value = int(score.get("score", 0) or 0)
        if score.get("skip") is True and _experience_has_transferable_value(exp):
            score["skip"] = False
            score["shrink"] = True
            score["score"] = max(score_value, 4)
            score["reason"] = "Kept as transferable engineering experience with production, scale, API, automation, or reliability evidence."
        guarded.append(score)
        seen_ids.add(exp_id)

    for exp in experiences:
        exp_id = exp.get("id")
        if exp_id and exp_id not in seen_ids and _experience_has_transferable_value(exp):
            guarded.append({
                "id": exp_id,
                "score": 4,
                "reason": "Added as compressed transferable engineering experience.",
                "shrink": True,
                "skip": False,
            })
    return guarded


def _escape(value: Any) -> str:
    return str(tex_escape(value or ""))


def _render_skills_latex(skills: dict) -> str:
    if not isinstance(skills, dict) or not skills:
        return ""
    blocks = []
    for category, values in skills.items():
        if not values:
            continue
        skill_text = ", ".join(_escape(skill) for skill in values)
        blocks.append(
            "\\begin{onecolentry}\n"
            f"    \\textbf{{{_escape(category)}:}} {skill_text}\n"
            "\\end{onecolentry}"
        )
    return "\n\n\\vspace{0.1cm}\n\n".join(blocks)


def _render_projects_latex(projects: list[dict]) -> str:
    blocks = []
    for project in projects or []:
        technologies = project.get("technologies", [])
        tech_text = ", ".join(_escape(tech) for tech in technologies)
        bullet = project.get("bullet") or project.get("description") or ""
        github = _escape(project.get("github", ""))
        blocks.append(
            f"\\begin{{twocolentry}}{{\\href{{{github}}}{{\\underline{{GitHub}}}}}}\n"
            f"    \\textbf{{{_escape(project.get('name'))}}} | \\textit{{{tech_text}}}\n"
            "\\end{twocolentry}\n"
            "\\vspace{0.10cm}\n"
            "\\begin{onecolentry}\n"
            "\\begin{highlights}\n"
            f"    \\item {_escape(bullet)}\n"
            "\\end{highlights}\n"
            "\\end{onecolentry}"
        )
    return "\n\n\\vspace{0.3cm}\n\n".join(blocks)


def _render_experience_latex(experiences: list[dict]) -> str:
    blocks = []
    for exp in experiences or []:
        exp_block = [
            f"\\begin{{twocolentry}}{{{_escape(exp.get('period'))}}}",
            f"    \\textbf{{{_escape(exp.get('role'))}}}, {_escape(exp.get('company'))} -- {_escape(exp.get('location'))}",
            "\\end{twocolentry}",
            "\\vspace{0.10cm}",
        ]
        for project in exp.get("projects", []) or []:
            name = project.get("name", "")
            if name:
                exp_block.extend([
                    "\\begin{onecolentry}",
                    f"\\textit{{{_escape(name)}}}",
                    "\\end{onecolentry}",
                    "\\vspace{0.05cm}",
                ])
            bullets = project.get("bullets", []) or []
            if bullets:
                exp_block.extend(["\\begin{onecolentry}", "\\begin{highlights}"])
                exp_block.extend(f"    \\item {_escape(bullet)}" for bullet in bullets)
                exp_block.extend(["\\end{highlights}", "\\end{onecolentry}"])
        blocks.append("\n".join(exp_block))
    return "\n\n\\vspace{0.3cm}\n\n".join(blocks)


def analyze_jd_node(state: AgentState) -> Dict[str, Any]:
    print("⚙️ [Node 0] Analyzing JD...")
    prompt = get_jd_analysis_prompt(state["job_description"])
    output = generate_text(prompt, model_name=state.get("model_name"))
    analysis = extract_json(output) or {}

    role_type = analysis.get("role_type")
    if role_type in {"fullstack", "mixed"}:
        role_type = "hybrid"
    if role_type not in {"backend", "ai_ml", "hybrid"}:
        role_type = "hybrid"

    skills = analysis.get("must_have_skills", [])
    if not isinstance(skills, list):
        skills = []

    jd_text = state.get("job_description", "").lower()
    hybrid_signals = [
        "python",
        "jvm",
        "frontend",
        "browser",
        "distributed",
        "kafka",
        "docker",
        "kubernetes",
        "terraform",
        "aws",
        "gitlab",
        "ci/cd",
        "infrastructure",
        "server and browser",
    ]
    if role_type == "backend" and sum(signal in jd_text for signal in hybrid_signals) >= 2:
        role_type = "hybrid"

    normalized = {
        "role_type": role_type,
        "must_have_skills": [str(skill) for skill in skills[:8]],
        "domain": str(analysis.get("domain") or "general").lower(),
        "mentions_ai": bool(analysis.get("mentions_ai", False)),
    }
    print("JD ANALYSIS:", normalized)
    return {
        "jd_analysis": normalized,
        "skills_retries": state.get("skills_retries", 0),
        "experience_retries": state.get("experience_retries", 0),
        "projects_retries": state.get("projects_retries", 0),
    }


def build_resume_rules_node(state: AgentState) -> Dict[str, Any]:
    print("⚙️ [Rules] Building resume rules...")
    jd_analysis = state.get("jd_analysis", {})
    role_type = jd_analysis.get("role_type", "hybrid")
    mentions_ai = bool(jd_analysis.get("mentions_ai", False))
    jd_text = state.get("job_description", "").lower()
    is_python_backend = "python" in jd_text and any(
        signal in jd_text
        for signal in ["backend", "server", "jvm", "distributed", "docker", "kubernetes", "ci/cd"]
    )

    if role_type == "ai_ml":
        schema = "ai_ml"
        max_projects = 2
    elif role_type == "backend":
        schema = "backend"
        max_projects = 1 if (mentions_ai or is_python_backend) else 0
    else:
        schema = "hybrid"
        max_projects = 1

    rules = {
        "include_ai_projects": not (role_type == "backend" and not mentions_ai and not is_python_backend),
        "shrink_non_domain_exp": role_type == "ai_ml",
        "skill_category_schema": schema,
        "max_projects": max_projects,
        "exp_bullet_limit_main": 5,
        "exp_bullet_limit_secondary": 3,
    }
    print("RESUME RULES:", rules)
    return {"resume_rules": rules}


def inject_static_node(state: AgentState) -> Dict[str, Any]:
    print("⚙️ [Static] Injecting Static Data...")
    if not state.get("generate_resume", True):
        return {}
    master = load_master_data()
    return {"personal": master.get("personal", {}), "education": master.get("education", [])}


def tailor_skills_node(state: AgentState) -> Dict[str, Any]:
    print("⚙️ [Skills] Tailoring Skills...")
    if not state.get("generate_resume", True):
        return {"tailored_skills": {}}
    master = load_master_data()
    tagged_skills = _tagged_skills(master)
    prompt = get_skills_prompt(
        state.get("jd_analysis", {}),
        state.get("resume_rules", {}),
        tagged_skills,
        master.get("experience", []),
    )
    output = generate_text(prompt, model_name=state.get("model_name"))
    print("SKILLS OUTPUT:", output)
    skills = extract_json(output) or {}
    normalized_skills = _normalize_tailored_skills(
        skills,
        state.get("jd_analysis", {}),
        state.get("resume_rules", {}),
        tagged_skills,
    )
    print("NORMALIZED SKILLS:", normalized_skills)
    return {"tailored_skills": normalized_skills}


def tailor_projects_node(state: AgentState) -> Dict[str, Any]:
    print("⚙️ [Projects] Tailoring Projects...")
    if not state.get("generate_resume", True):
        return {"tailored_projects": []}
    rules = state.get("resume_rules", {})
    if not rules.get("include_ai_projects", True):
        print("⏭️ [Projects] Skipping projects from resume rules.")
        return {"tailored_projects": []}
    chunks = _retrieve_for_section(state, "project")
    phase_a_prompt = get_projects_phase_a_prompt(state.get("jd_analysis", {}), chunks)
    phase_a_output = generate_text(phase_a_prompt, model_name=state.get("model_name"))
    projects = _normalize_projects(extract_json(phase_a_output))
    max_projects = int(rules.get("max_projects", 2))
    print("PROJECTS OUTPUT:", projects)
    return {"tailored_projects": projects[:max_projects]}


def skip_projects_node(state: AgentState) -> Dict[str, Any]:
    print("⏭️ [Projects] Skipping projects for pure backend JD with no AI mention.")
    return {"tailored_projects": []}


def score_experiences_node(state: AgentState) -> Dict[str, Any]:
    print("⚙️ [Experience] Scoring Experiences...")
    if not state.get("generate_resume", True):
        return {"experience_scores": []}
    master = load_master_data()
    prompt = get_score_experiences_prompt(
        state.get("jd_analysis", {}),
        state.get("resume_rules", {}),
        master.get("experience", []),
    )
    output = generate_text(prompt, model_name=state.get("model_name"))
    scores = _guard_experience_scores(
        _normalize_experience_scores(extract_json(output)),
        master.get("experience", []),
    )
    print("EXPERIENCE SCORES:", scores)
    return {"experience_scores": scores}


def rewrite_experiences_node(state: AgentState) -> Dict[str, Any]:
    print("⚙️ [Experience] Rewriting Experiences...")
    if not state.get("generate_resume", True):
        return {"tailored_experience": []}
    master = load_master_data()
    experiences_by_id = {entry.get("id"): entry for entry in master.get("experience", [])}
    tailored = []
    for score in state.get("experience_scores", []):
        exp = experiences_by_id.get(score.get("id"))
        if not exp:
            continue
        prompt = get_rewrite_experience_prompt(
            state.get("jd_analysis", {}),
            state.get("resume_rules", {}),
            exp,
            score,
            state.get("tailored_skills", {})
        )
        output = generate_text(prompt, model_name=state.get("model_name"))
        rewritten = extract_json(output)
        if isinstance(rewritten, dict):
            tailored.append(rewritten)
    print("EXPERIENCE OUTPUT:", tailored)
    return {"tailored_experience": tailored}


def validate_skills_node(state: AgentState) -> Dict[str, Any]:
    return {}


def validate_projects_node(state: AgentState) -> Dict[str, Any]:
    return {}


def validate_experience_node(state: AgentState) -> Dict[str, Any]:
    return {}


def skills_output_valid(state: AgentState) -> bool:
    skills = state.get("tailored_skills", {})
    return isinstance(skills, dict) and any(isinstance(v, list) and v for v in skills.values())


def projects_output_valid(state: AgentState) -> bool:
    projects = state.get("tailored_projects", [])
    if projects == []:
        return True
    return isinstance(projects, list) and all(
        isinstance(project, dict) and project.get("name") and project.get("bullet")
        for project in projects
    )


def experience_output_valid(state: AgentState) -> bool:
    experiences = state.get("tailored_experience", [])
    return isinstance(experiences, list) and bool(experiences) and all(
        isinstance(exp, dict)
        and exp.get("company")
        and isinstance(exp.get("projects"), list)
        and any(project.get("bullets") for project in exp.get("projects", []) if isinstance(project, dict))
        for exp in experiences
    )


def retry_skills_node(state: AgentState) -> Dict[str, Any]:
    return {"skills_retries": state.get("skills_retries", 0) + 1}


def retry_projects_node(state: AgentState) -> Dict[str, Any]:
    return {"projects_retries": state.get("projects_retries", 0) + 1}


def retry_experience_node(state: AgentState) -> Dict[str, Any]:
    return {"experience_retries": state.get("experience_retries", 0) + 1}


def skills_done_node(state: AgentState) -> Dict[str, Any]:
    return {}


def projects_done_node(state: AgentState) -> Dict[str, Any]:
    if not projects_output_valid(state):
        print("⚠️ [Projects] Output invalid after retries, clearing.")
        return {"tailored_projects": []}
    return {}


def experience_done_node(state: AgentState) -> Dict[str, Any]:
    return {}


def aggregate_outputs_node(state: AgentState) -> Dict[str, Any]:
    print("🧩 [Aggregate] Section branches complete.")
    return {}


def render_latex_node(state: AgentState) -> Dict[str, Any]:
    print("⚙️ [Render] Rendering complete resume LaTeX...")
    if not state.get("generate_resume", True):
        return {"resume_tex": ""}
    resume_data = {
        "personal": state.get("personal", {}),
        "education": state.get("education", []),
        "tailored_skills": _render_skills_latex(state.get("tailored_skills", {})),
        "tailored_experience": _render_experience_latex(state.get("tailored_experience", [])),
        "tailored_projects": _render_projects_latex(state.get("tailored_projects", [])),
    }
    template = latex_jinja_env.get_template("app/templates/resume_template.tex")
    return {"resume_tex": template.render(**resume_data)}


def draft_letter_node(state: AgentState) -> Dict[str, Any]:
    print("⚙️ [Letter] Drafting Cover Letter & Email...")
    do_cl = state.get("generate_cover_letter", True)
    do_email = state.get("generate_email", True)
    if not do_cl and not do_email:
        return {
            "cover_letter": "",
            "email_draft": "",
            "email_subject": "",
            "email_body": "",
            "recipient": "Dear Hiring Manager,"
        }

    prompt = get_letter_prompt(
        state.get("jd_analysis", {}),
        state.get("tailored_experience", ""),
        state.get("personal", {})
    )

    output = generate_text(prompt, model_name=state.get("model_name"))
    data = extract_json(output)
    if data:
        email_draft_obj = data.get("email_draft", {})
        email_subject = ""
        email_body = ""
        if isinstance(email_draft_obj, dict):
            email_subject = email_draft_obj.get("subject", "")
            email_body = email_draft_obj.get("body", "")
        
        return {
            "cover_letter": data.get("cover_letter", ""),
            "email_draft": str(email_draft_obj),
            "email_subject": email_subject,
            "email_body": email_body,
            "recipient": "Dear Hiring Manager,"
        }
    return {
        "cover_letter": "Error formatting letter.",
        "email_draft": "Error formatting email.",
        "email_subject": "",
        "email_body": "",
        "recipient": "Dear Hiring Manager,"
    }
