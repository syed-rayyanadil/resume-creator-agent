import streamlit as st
import requests
import base64
import urllib.parse
import os
import streamlit.components.v1 as components

st.set_page_config(page_title="Agentic Resume Tailor", layout="wide")

def display_pdf(file_path):
    with open(file_path, "rb") as f:
        base64_pdf = base64.b64encode(f.read()).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

st.title("📄 AI Resume Architect")

with st.sidebar:
    st.header("🛠️ Selection")
    gen_resume = st.checkbox("Generate Resume", value=True)
    # Cover letter and email are disabled for the resume-only flow.
    # gen_cover_letter = st.checkbox("Generate Cover Letter", value=True)
    # gen_email = st.checkbox("Generate Email Draft", value=True)
    gen_cover_letter = False
    gen_email = False
    st.header("⚙️ Model Settings")
    # 1. Create the UI Dropdown in the sidebar
    selected_model_label = st.selectbox(
        "Choose your AI Model:",
        [
            "70B Model (Highest Quality) - llama-3.3-70b-versatile",
            "17B Model (Smart & High Limits) - meta-llama/llama-4-scout-17b-16e-instruct",
            "8B Model (Fastest) - llama-3.1-8b-instant"
        ]
    )
    # 2. Extract the actual Groq ID
    actual_model_id = selected_model_label.split(" - ")[-1]
    
    st.divider() # Adds a nice visual line to separate sections
    
    # st.header("📧 Email Settings")
    # send_email = st.checkbox("Prepare Email Draft")
    # if send_email:
    #     target_email = st.text_input("Recipient Email", placeholder="hiring@company.com")
    #     subject = st.text_input("Subject Line", value="Job Application - Software Engineer")

default_jd = "About the job\nAt Flix11, we offer a tech-driven environment where innovation meets real-world impact, with competitive pay, strong growth opportunities, and a culture of collaboration and ownership.\n\nWe are looking for a motivated and curious Junior python Engineer (m/f/d) to join our team in Supply Division and drive customer station experience to the next level!\n\nIn an ever growing network, Flix customers worldwide expect a comfortable and seamless experience at our stations as part of their travel experience. Our self-organized, cross-functional and distributed team builds products to enable Flix station managers to scale management of the station inventory, which a wide range of internal tech teams across Flix depend on, and overall serves to improve the experience at our stations for millions of passengers.\n\nIn this role, you will continue to shape the product by driving innovation, solving complex challenges, and creating a lasting impact on our organization.\n\nAbout The Role\n\nYou will join a mature environment where members support you in growing your technical and soft skills.\nYou and your team will work closely with the Business Stakeholders on continuously developing and improving the product vision.\nYou always keep the business value in mind when making decisions.\nYou drive the development process using an agile environment.\nAs part of your daily work, you will work closely with your fellow team members, for example in pair and ensemble programming, doing code reviews, testing, and operations.\nYou frequently deliver new versions of the product, using continuous integration and delivery.\nYou work confidently with or learn how to use cutting-edge technologies and tools including but not limited to:\npython across server and browser \nJVM on server-side (Ktor, Axon Framework)\nComponent-based Frontend (Compose HTML, but we valuable experience with similar libraries and frameworks)\nDistributed system architecture (Apache Kafka, HTTP/REST)\nInfrastructure with CI/CD (AWS, Docker, Kubernetes, Terraform, Datadog, Gitlab)\n\nAbout You\n\nA completed Bachelor's or Master's degree in Computer Science, Information Systems, or equivalent industry experience\nYou have experience in backend engineering using python\nYou possess an understanding of testing principles\nYou have knowledge of SQL and relational databases\nYou use Docker to run your application\nYou use Git to version your source code\nExperience in frontend engineering is a plus\nYou are passionate about learning new tools and keeping yourself up-to-date\nYou are willing to take responsibility for the product and technical decisions\nYou value a collaborative mindset, honest communication, experimenting, sharing knowledge and regular feedback\nClear written and spoken English communication skills\n\nWe recognize that everyone carries a unique set of valuable skills and experiences. If you think you could have an impact even though you don't meet 100% of the requirements, we still encourage you to apply. We want to hear from you!\n\nWhat We Offer\n\nTravel perks: 12 free Flix vouchers + 12 discount vouchers for friends & family.\nWork from (M)Anywhere: Depending on your role, work from another location for up to 60 days per year.\nHybrid work model: We are an office-first company, but we offer flexibility to balance work and life.\nWellbeing support: Access confidential 1:1 counselling, courses, and stress management for yourself and up to four family members.\nLearning & Development: Take advantage of language classes, training courses, and expert-led sessions to grow your skills.\nMentoring Program: Connect with experienced colleagues to gain insights and accelerate your career.\n\nTo view more local benefits specific to each office location, please check out this link: Locations - Flix Career\n\nWhy Join Flix?\n\nAt Flix, we empower our teams to push boundaries and shape the future of mobility. As we continue to scale globally, we harness cutting-edge technology to make mobility smarter, more sustainable, and more affordable.\n\nIf you’re looking for a place where you can drive change and redefine how millions of people travel, Flix is the place where you can lead your journey!"
jd_input = st.text_area("Paste Job Description", value=default_jd, height=250)


if st.button("Generate Resume"):
    if not jd_input.strip():
        st.error("Please paste a job description first.")
    else:
        # Display which model is being used in the spinner
        with st.spinner(f"Generating assets using the {actual_model_id.split('-')[1]} model..."):
            
            # Updated payload to include the model choice
            payload = {
                "job_description": jd_input,
                "model_name": actual_model_id,
                "generate_resume": gen_resume,
                "generate_cover_letter": gen_cover_letter,
                "generate_email": gen_email
            }
                
            try:
                # 1. Call Backend
                response = requests.post("http://127.0.0.1:8000/generate", json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    st.success("✨ Generation Complete!")
                    
                    import time
                    time.sleep(0.5)

                    # --- CONDITIONAL UI DISPLAY ---
                    # Create a list of what we actually want to show
                    views = []
                    if gen_resume: views.append("Resume")
                    # if gen_cover_letter: views.append("Cover Letter")

                    if len(views) > 0:
                        # Create dynamic columns based on selection
                        cols = st.columns(len(views))
                        
                        for i, view_type in enumerate(views):
                            with cols[i]:
                                if view_type == "Resume":
                                    st.subheader("🎯 Tailored Resume")
                                    if os.path.exists("tailored_resume.pdf"):
                                        display_pdf("tailored_resume.pdf")
                                    else:
                                        st.error("Resume PDF missing.")

                                # elif view_type == "Cover Letter":
                                #     st.subheader("✉️ Cover Letter")
                                #     if os.path.exists("cover_letter.pdf"):
                                #         display_pdf("cover_letter.pdf")
                                #     else:
                                #         st.error("Cover Letter PDF failed to generate.")
                                #         if not data.get("cover_letter"):
                                #             st.warning("Reason: AI returned empty text for the letter.")

                    # Email draft display is disabled for the resume-only flow.
                    # if gen_email:
                    #     st.divider()
                    #     st.subheader("📧 Networking Email")
                    #     email_text = data.get("email_draft", "No email draft generated.")
                    #     st.text_area("Draft Copy", value=email_text, height=150)
                    #     gmail_url = f"https://mail.google.com/mail/?view=cm&fs=1&to={target_email}&su={urllib.parse.quote(subject)}&body={urllib.parse.quote(email_text)}"
                    #     st.link_button("🚀 Open in Gmail", gmail_url)
                
                else:
                    # Handles cases where FastAPI returns an error (400, 500, etc.)
                    error_detail = response.json().get("detail", "Unknown Backend Error")
                    st.error(f"❌ Backend Error {response.status_code}: {error_detail}")

            except requests.exceptions.ConnectionError:
                st.error("🚨 Connection Failed! Is your FastAPI backend running? Run `sh run.sh` in your terminal.")
            
            except Exception as e:
                st.error(f"🚨 An unexpected error occurred: {e}")
