from langgraph.graph import END, StateGraph

from app.nodes import (
    aggregate_outputs_node,
    analyze_jd_node,
    build_resume_rules_node,
    draft_letter_node,
    experience_done_node,
    experience_output_valid,
    inject_static_node,
    projects_done_node,
    projects_output_valid,
    render_latex_node,
    retry_experience_node,
    retry_projects_node,
    retry_skills_node,
    rewrite_experiences_node,
    score_experiences_node,
    skills_done_node,
    skills_output_valid,
    tailor_projects_node,
    tailor_skills_node,
    validate_experience_node,
    validate_projects_node,
    validate_skills_node,
)
from app.state import AgentState


def route_after_jd_analysis(state: AgentState) -> list[str]:
    return ["InjectStatic", "TailorSkills", "ScoreExperiences", "TailorProjects"]


def route_skills_validation(state: AgentState) -> str:
    if not state.get("generate_resume", True):
        return "SkillsDone"
    if skills_output_valid(state):
        return "SkillsDone"
    if state.get("skills_retries", 0) < 2:
        return "RetrySkills"
    return "SkillsDone"


def route_projects_validation(state: AgentState) -> str:
    if not state.get("generate_resume", True):
        return "ProjectsDone"
    if projects_output_valid(state):
        return "ProjectsDone"
    if state.get("projects_retries", 0) < 2:
        return "RetryProjects"
    return "ProjectsDone"


def route_experience_validation(state: AgentState) -> str:
    if not state.get("generate_resume", True):
        return "ExperienceDone"
    if experience_output_valid(state):
        return "ExperienceDone"
    if state.get("experience_retries", 0) < 2:
        return "RetryExperience"
    return "ExperienceDone"


def build_graph():
    print("🏗️ Building Parallel JD-Aware LangGraph Workflow...")

    workflow = StateGraph(AgentState)

    workflow.add_node("AnalyzeJD", analyze_jd_node)
    workflow.add_node("BuildResumeRules", build_resume_rules_node)
    workflow.add_node("InjectStatic", inject_static_node)
    workflow.add_node("TailorSkills", tailor_skills_node)
    workflow.add_node("TailorProjects", tailor_projects_node)
    workflow.add_node("ScoreExperiences", score_experiences_node)
    workflow.add_node("RewriteExperiences", rewrite_experiences_node)
    workflow.add_node("ValidateSkills", validate_skills_node)
    workflow.add_node("ValidateProjects", validate_projects_node)
    workflow.add_node("ValidateExperience", validate_experience_node)
    workflow.add_node("RetrySkills", retry_skills_node)
    workflow.add_node("RetryProjects", retry_projects_node)
    workflow.add_node("RetryExperience", retry_experience_node)
    workflow.add_node("SkillsDone", skills_done_node)
    workflow.add_node("ProjectsDone", projects_done_node)
    workflow.add_node("ExperienceDone", experience_done_node)
    workflow.add_node("Aggregate", aggregate_outputs_node)
    workflow.add_node("RenderLatex", render_latex_node)
    workflow.add_node("DraftLetter", draft_letter_node)

    workflow.set_entry_point("AnalyzeJD")
    workflow.add_edge("AnalyzeJD", "BuildResumeRules")

    workflow.add_conditional_edges(
        "BuildResumeRules",
        route_after_jd_analysis,
        {
            "InjectStatic": "InjectStatic",
            "TailorSkills": "TailorSkills",
            "ScoreExperiences": "ScoreExperiences",
            "TailorProjects": "TailorProjects",
        },
    )

    workflow.add_edge("TailorSkills", "ValidateSkills")
    workflow.add_conditional_edges(
        "ValidateSkills",
        route_skills_validation,
        {"RetrySkills": "RetrySkills", "SkillsDone": "SkillsDone"},
    )
    workflow.add_edge("RetrySkills", "TailorSkills")

    workflow.add_edge("TailorProjects", "ValidateProjects")
    workflow.add_conditional_edges(
        "ValidateProjects",
        route_projects_validation,
        {"RetryProjects": "RetryProjects", "ProjectsDone": "ProjectsDone"},
    )
    workflow.add_edge("RetryProjects", "TailorProjects")
    workflow.add_edge("ScoreExperiences", "RewriteExperiences")
    workflow.add_edge("RewriteExperiences", "ValidateExperience")
    workflow.add_conditional_edges(
        "ValidateExperience",
        route_experience_validation,
        {"RetryExperience": "RetryExperience", "ExperienceDone": "ExperienceDone"},
    )
    workflow.add_edge("RetryExperience", "RewriteExperiences")

    workflow.add_edge(
        ["InjectStatic", "SkillsDone", "ProjectsDone", "ExperienceDone"],
        "Aggregate",
    )
    workflow.add_edge("Aggregate", "RenderLatex")
    # Cover letter and email generation are intentionally not connected for the resume-only flow.
    # workflow.add_edge("RenderLatex", "DraftLetter")
    # workflow.add_edge("DraftLetter", END)
    workflow.add_edge("RenderLatex", END)

    return workflow.compile()


agent_workflow = build_graph()
