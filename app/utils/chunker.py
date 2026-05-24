import json

from qdrant_client import QdrantClient


COLLECTION_NAME = "resume_portfolio"
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"

SKILL_CATEGORIES = {
    "Languages": {"Java", "Kotlin", "Python", "Golang", "TypeScript", "JavaScript", "PHP"},
    "Frameworks & Libraries": {
        "Spring Boot",
        "Spring MVC",
        "Laravel",
        "React",
        "Angular",
        "Redux",
        "Flask",
        "JPA/Hibernate",
    },
    "AI/ML": {
        "PyTorch",
        "OpenCV",
        "CNN",
        "YOLO",
        "Object Detection",
        "Image Classification",
        "Autoencoder",
        "Sklearn",
        "Pandas",
        "NumPy",
        "Deep Learning",
        "Vision Transformers",
        "VLMs",
        "Zero-Shot Learning",
        "Transformers",
        "CLIP",
        "BLIP",
        "LLaVA",
        "GANs",
        "Transfer Learning",
        "Reinforcement Learning",
        "LLMs",
    },
    "Databases": {"PostgreSQL", "MongoDB", "MySQL"},
    "Architecture & Practices": {
        "Hexagonal Architecture",
        "Microservices",
        "REST APIs",
        "Strategy Pattern",
        "Clean Code",
        "TDD",
        "Agile",
        "CI/CD",
    },
    "Testing": {"Kotest", "JUnit", "Mockito"},
    "Cloud & DevOps": {
        "Docker",
        "Kubernetes",
        "GitHub Actions",
        "Azure DevOps",
        "Google Cloud Platform (GCP)",
        "Jenkins",
    },
    "Tools & Platforms": {
        "Git",
        "SonarQube",
        "Liquibase",
        "Swagger",
        "Jira",
        "Confluence",
        "Jupyter",
        "Google Colab",
        "PuTTY",
        "Wildfly",
    },
}


def _skill_categories(skills: list[str]) -> dict[str, list[str]]:
    categorized = {category: [] for category in SKILL_CATEGORIES}
    uncategorized = []

    for skill in skills:
        matched = False
        for category, known_skills in SKILL_CATEGORIES.items():
            if skill in known_skills:
                categorized[category].append(skill)
                matched = True
                break
        if not matched:
            uncategorized.append(skill)

    if uncategorized:
        categorized["Tools & Platforms"].extend(uncategorized)

    return {category: values for category, values in categorized.items() if values}


def _project_technologies(project: dict) -> list[str]:
    return project.get("technologies") or []


def _project_domain(project: dict, fallback: str = "") -> str:
    return project.get("domain") or fallback or project.get("type") or ""


def _experience_chunks(job: dict) -> list[dict]:
    chunks = []
    base_metadata = {
        "type": "experience",
        "company": job.get("company"),
        "role": job.get("role"),
        "period": job.get("period"),
        "location": job.get("location"),
        "technologies": job.get("technologies", []),
        "domain": job.get("domain", ""),
    }

    for index, bullet in enumerate(job.get("highlights", []), start=1):
        metadata = {**base_metadata, "bullet_index": index, "project": ""}
        text = (
            f"Company: {job.get('company')}. Role: {job.get('role')}. "
            f"Period: {job.get('period')}. Domain: {metadata['domain']}. "
            f"Technologies: {', '.join(metadata['technologies'])}. "
            f"Raw bullet: {bullet}"
        )
        chunks.append({"page_content": text, "metadata": metadata})

    for project in job.get("projects", []):
        technologies = _project_technologies(project)
        domain = _project_domain(project, base_metadata["domain"])
        for index, bullet in enumerate(project.get("highlights", project.get("bullets", [])), start=1):
            metadata = {
                **base_metadata,
                "technologies": technologies,
                "domain": domain,
                "project": project.get("name", ""),
                "bullet_index": index,
            }
            text = (
                f"Company: {job.get('company')}. Role: {job.get('role')}. "
                f"Period: {job.get('period')}. Project: {project.get('name')}. "
                f"Domain: {domain}. Technologies: {', '.join(technologies)}. "
                f"Raw bullet: {bullet}"
            )
            chunks.append({"page_content": text, "metadata": metadata})

    return chunks


def create_chunks(json_filepath):
    with open(json_filepath, "r") as f:
        master_data = json.load(f)

    all_chunks = []

    skills = master_data.get("skills", [])
    if isinstance(skills, dict):
        category_map = skills
    else:
        category_map = _skill_categories(skills)

    for category, category_skills in category_map.items():
        all_chunks.append({
            "page_content": f"Skill category: {category}. Skills: {', '.join(category_skills)}",
            "metadata": {
                "type": "skills",
                "category": category,
                "skills": category_skills,
            },
        })

    for job in master_data.get("experience", []):
        all_chunks.extend(_experience_chunks(job))

    for proj in master_data.get("projects", []):
        proj_text = f"Project Name: {proj.get('name')}. "

        if "description" in proj:
            proj_text += f"Description: {proj['description']} "

        if "technologies" in proj:
            proj_text += f"Technologies used: {', '.join(proj['technologies'])}. "

        if "relevant_details" in proj:
            proj_text += f"Details: {' '.join(proj['relevant_details'])} "

        all_chunks.append({
            "page_content": proj_text.strip(),
            "metadata": {
                "type": "project",
                "name": proj.get("name"),
                "github": proj.get("github", ""),
                "technologies": proj.get("technologies", []),
            },
        })

    return all_chunks


if __name__ == "__main__":
    filepath = "data/my_data.json"

    print("1. Chunking data...")
    my_chunks = create_chunks(filepath)

    print("2. Connecting to fresh Qdrant Database...")
    client = QdrantClient(path="./data/qdrant_db")
    client.set_model(EMBEDDING_MODEL)

    if client.collection_exists(COLLECTION_NAME):
        print("3. Resetting existing collection...")
        client.delete_collection(COLLECTION_NAME)

    print("4. Uploading to Database...")
    client.add(
        collection_name=COLLECTION_NAME,
        documents=[chunk["page_content"] for chunk in my_chunks],
        metadata=[chunk["metadata"] for chunk in my_chunks],
    )
    client.close()

    print(f"✅ Successfully ingested {len(my_chunks)} chunks into Qdrant!")
