import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.nodes import load_master_data, extract_json, tailor_skills_node, tailor_projects_node, rewrite_experience_node
from app.prompts import get_skills_prompt, get_projects_prompt, get_experience_prompt
from app.utils.OllamaConnection import generate_text

# ==========================================
# HARDCODED JD FOR TESTING
# ==========================================
JD = """
About the job\nAt Flix1, we offer a tech-driven environment where innovation meets real-world impact, with competitive pay, strong growth opportunities, and a culture of collaboration and ownership.\n\nWe are looking for a motivated and curious Junior Java/Kotlin Engineer (m/f/d) to join our team in Supply Division and drive customer station experience to the next level!\n\nIn an ever growing network, Flix customers worldwide expect a comfortable and seamless experience at our stations as part of their travel experience. Our self-organized, cross-functional and distributed team builds products to enable Flix station managers to scale management of the station inventory, which a wide range of internal tech teams across Flix depend on, and overall serves to improve the experience at our stations for millions of passengers.\n\nIn this role, you will continue to shape the product by driving innovation, solving complex challenges, and creating a lasting impact on our organization.\n\nAbout The Role\n\nYou will join a mature environment where members support you in growing your technical and soft skills.\nYou and your team will work closely with the Business Stakeholders on continuously developing and improving the product vision.\nYou always keep the business value in mind when making decisions.\nYou drive the development process using an agile environment.\nAs part of your daily work, you will work closely with your fellow team members, for example in pair and ensemble programming, doing code reviews, testing, and operations.\nYou frequently deliver new versions of the product, using continuous integration and delivery.\nYou work confidently with or learn how to use cutting-edge technologies and tools including but not limited to:\nKotlin across server and browser (we use Kotlin a lot!)\nJVM on server-side (Ktor, Axon Framework)\nComponent-based Frontend (Compose HTML, but we valuable experience with similar libraries and frameworks)\nDistributed system architecture (Apache Kafka, HTTP/REST)\nInfrastructure with CI/CD (AWS, Docker, Kubernetes, Terraform, Datadog, Gitlab)\n\nAbout You\n\nA completed Bachelor's or Master's degree in Computer Science, Information Systems, or equivalent industry experience\nYou have experience in backend engineering using any JVM language (Kotlin is a plus)\nYou possess an understanding of testing principles\nYou have knowledge of SQL and relational databases\nYou use Docker to run your application\nYou use Git to version your source code\nExperience in frontend engineering is a plus\nYou are passionate about learning new tools and keeping yourself up-to-date\nYou are willing to take responsibility for the product and technical decisions\nYou value a collaborative mindset, honest communication, experimenting, sharing knowledge and regular feedback\nClear written and spoken English communication skills\n\nWe recognize that everyone carries a unique set of valuable skills and experiences. If you think you could have an impact even though you don't meet 100% of the requirements, we still encourage you to apply. We want to hear from you!\n\nWhat We Offer\n\nTravel perks: 12 free Flix vouchers + 12 discount vouchers for friends & family.\nWork from (M)Anywhere: Depending on your role, work from another location for up to 60 days per year.\nHybrid work model: We are an office-first company, but we offer flexibility to balance work and life.\nWellbeing support: Access confidential 1:1 counselling, courses, and stress management for yourself and up to four family members.\nLearning & Development: Take advantage of language classes, training courses, and expert-led sessions to grow your skills.\nMentoring Program: Connect with experienced colleagues to gain insights and accelerate your career.\n\nTo view more local benefits specific to each office location, please check out this link: Locations - Flix Career\n\nWhy Join Flix?\n\nAt Flix, we empower our teams to push boundaries and shape the future of mobility. As we continue to scale globally, we harness cutting-edge technology to make mobility smarter, more sustainable, and more affordable.\n\nIf you’re looking for a place where you can drive change and redefine how millions of people travel, Flix is the place where you can lead your journey!
"""

MODEL = "llama-3.1-8b-instant"

master = load_master_data()

# ==========================================
# TEST 1: SKILLS
# comment out TEST 2 and TEST 3 to run this alone
# ==========================================
print("\n" + "="*50)
print("TEST 1: SKILLS")
print("="*50)

prompt = get_skills_prompt(JD, master['skills'])
raw = generate_text(prompt, model_name=MODEL)
print("RAW OUTPUT:\n", raw)
data = extract_json(raw)
print("\nPARSED OUTPUT:", data)


# # ==========================================
# # TEST 2: PROJECTS
# # comment out TEST 1 and TEST 3 to run this alone
# # ==========================================
# print("\n" + "="*50)
# print("TEST 2: PROJECTS")
# print("="*50)

# prompt = get_projects_prompt(JD, master['projects'])
# raw = generate_text(prompt, model_name=MODEL)
# print("RAW OUTPUT:\n", raw)
# data = extract_json(raw)
# print("\nPARSED OUTPUT:", data)


# # ==========================================
# # TEST 3: EXPERIENCE
# # comment out TEST 1 and TEST 2 to run this alone
# # ==========================================
# print("\n" + "="*50)
# print("TEST 3: EXPERIENCE")
# print("="*50)

# prompt = get_experience_prompt(JD, master['experience'])
# raw = generate_text(prompt, model_name=MODEL)
# print("RAW OUTPUT:\n", raw)
# data = extract_json(raw)
# print("\nPARSED OUTPUT:", data)