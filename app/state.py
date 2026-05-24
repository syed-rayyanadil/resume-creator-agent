from typing import TypedDict, List, Dict, Any

class AgentState(TypedDict):
    job_description: str
    model_name: str  # <--- ADD THIS LINE HERE!
    jd_analysis: Dict[str, Any]
    resume_rules: Dict[str, Any]
    personal: Dict[str, Any]
    education: List[Dict[str, Any]]
    retrieved_projects: List[Dict[str, Any]]
    tailored_skills: Dict[str, Any]
    experience_scores: List[Dict[str, Any]]
    tailored_experience: List[Dict[str, Any]]
    tailored_projects: List[Dict[str, Any]]
    resume_tex: str
    cover_letter: str
    email_draft: str
    email_subject: str
    email_body: str
    recipient: str
    generate_resume: bool
    generate_cover_letter: bool
    generate_email: bool
    skills_retries: int
    experience_retries: int
    projects_retries: int
