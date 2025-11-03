from langchain_core.prompts import ChatPromptTemplate

PROMPT = ChatPromptTemplate.from_template(
                        """You are an expert career counselor and professional cover letter writer. 
                        Your task is to create a compelling, personalized cover letter that:
                        
                        1. Extracts key information from the CV (name, skills, experience)
                        2. Analyzes the job listing to understand requirements
                        3. Matches the candidate's qualifications to the job requirements
                        4. Writes in a professional yet personable tone
                        5. Highlights relevant achievements and skills
                        6. Shows genuine enthusiasm for the role
                        
                        User Instructions:
                        {user_instructions}
                        
                        CV/Resume:
                        {cv_text}
                        
                        Job Listing:
                        {job_listing}
                        
                        Important guidelines:
                        - Keep the cover letter to 3-4 paragraphs
                        - Start with a strong opening that mentions the specific position
                        - Use specific examples from the CV that match job requirements
                        - End with a call to action
                        - Maintain professional formatting
                        - Include proper salutation and closing
                        - CRITICAL: Use only standard ASCII characters. Use straight quotes ('), not curly quotes (' ' " "). Use regular hyphens (-), not em-dashes (—) or en-dashes (–).
                        - CRITICAL: LinkedIn and GitHub usernames should not include the full URL, only the username.
                        
                        You MUST respond with a valid JSON object in this exact format, Here is an example:
                        {{ 
                        "contact": {{
                            "name": "Yassine Kader",
                            "email": "yassinekader.contact@gmail.com",
                            "phone": "+212 xxxxxxxx",
                            "address": "Agadir, Morocco",
                            "linkedin": "yassine-kader",
                            "github": "yassinekader",
                            "role": "AI Engineer & Data Scientist"
                        }},
                        "company": {{
                            "company": "SMR",
                            "position": "Stagiaire Ingénieur IA",
                            "recipient": "Service Recrutement, SMR Réseau",
                            "source": "via le site carrière de SMR",
                            "company_news": "I am particularly inspired by SMR's collective transformation toward AI, 5G, and data-driven innovation."
                        }},
                        "content": {{
                            "opening_salutation": "Madame, Monsieur,",
                            "opening_paragraph": "Actuellement étudiant en Master Data Science et Intelligence Artificielle à l'ENSA El Jadida, je recherche un stage de cinq mois à partir de mars 2025. Passionné par l'innovation et les systèmes intelligents, je souhaite vivement rejoindre SMR pour le stage d'Ingénieur IA.",
                            "second_paragraph": "Lors de mes expériences précédentes, j'ai acquis des compétences solides en apprentissage automatique, modélisation de données et développement backend. Au cours de mon stage chez Zanmi Inc., j'ai développé un tableau de bord en temps réel pour le suivi de modèles de chatbot et entraîné des modèles Whisper pour la reconnaissance vocale.",
                            "closing_paragraph": "Je suis particulièrement attiré par la démarche d'innovation continue de SFR et sa vision ambitieuse de la convergence entre réseaux fixes et mobiles.",
                            "closing_salutation": "Veuillez agréer, Madame, Monsieur, l'expression de mes salutations distinguées.",
                            "signoff_paragraph": "Je vous remercie pour l'attention portée à ma candidature et reste à votre disposition pour un entretien."
                        }}
                        }}
                        """
                    )